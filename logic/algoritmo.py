import random

class GeneradorAutomatico:
    def __init__(self, db):
        self.db = db
        self.errores = []
        self.avisos = []

    def generar_horario(self, nombre_ciclo):
        """Genera el horario y lo guarda con la etiqueta del ciclo"""
        print(f"Generando para: {nombre_ciclo}")
        
        modulos_datos = self.db.obtener_datos_generacion(nombre_ciclo)
        
        # 1. Cargar restricciones (Profesores de este grupo + sus otras clases)
        ids_profesores = [m['id_profesor'] for m in modulos_datos if m['id_profesor']]
        ocupacion_existente = self.db.obtener_ocupacion_horario_profesores(ids_profesores)
        
        restricciones_L1 = {}
        preferencias_L2 = {}
        
        for m in modulos_datos:
            pid = m['id_profesor']
            if pid:
                if pid not in restricciones_L1:
                    bloqueos = self._cargar_restricciones(pid, nivel=1)
                    # Añadir clases que ya tiene en OTROS grupos
                    clases_ya = ocupacion_existente.get(pid, set())
                    dias_map = {"LUNES":0, "MARTES":1, "MIERCOLES":2, "MIÉRCOLES":2, "JUEVES":3, "VIERNES":4}
                    for d_nom, h_num in clases_ya:
                        d_idx = dias_map.get(d_nom.upper().replace("É", "E"))
                        if d_idx is not None: bloqueos.add((d_idx, h_num - 1))
                    
                    restricciones_L1[pid] = bloqueos

                if pid not in preferencias_L2:
                    preferencias_L2[pid] = self._cargar_restricciones(pid, nivel=2)
        
        # Copiar restricciones para rastrear ocupación durante asignación
        ocupacion_L1 = {pid: set(rest) for pid, rest in restricciones_L1.items()}

        # 2. Matriz y Ordenación inteligente
        horario = [[None for _ in range(6)] for _ in range(5)]
        
        # Ordenar: primero por horas (descendentes), luego por número de restricciones (ascendentes)
        def prioridad_modulo(m):
            pid = m['id_profesor']
            num_restricciones = len(restricciones_L1.get(pid, set()))
            # Mayor peso a horas, menor peso a restricciones
            return (-m['horas'], num_restricciones)
        
        modulos_datos.sort(key=prioridad_modulo)

        # 3. Asignación inteligente
        for m in modulos_datos:
            horas_pendientes = m['horas']
            mid = m['id_modulo']
            pid = m['id_profesor']
            nom = m['nombre_modulo']
            
            for hora_idx in range(horas_pendientes):
                colocado = False
                
                # Intentar pasadas progresivas
                for pasada in range(1, 4):
                    if colocado:
                        break
                    
                    # Seleccionar días menos cargados
                    dias_intento = self._ordenar_dias_por_carga(horario, mid)
                    
                    for d in dias_intento:
                        if colocado:
                            break
                        
                        # Límite de 2 horas por día (solo pasada 1 y 2)
                        if pasada <= 2 and self._contar_horas_dia(horario, d, mid) >= 2:
                            continue
                        
                        # Seleccionar franjas en orden inteligente
                        franjas = self._ordenar_franjas_por_disponibilidad(horario, d, pid, ocupacion_L1, preferencias_L2 if pasada == 1 else None)
                        
                        for h in franjas:
                            if horario[d][h] is None:
                                se_asigna = False
                                aviso = None
                                
                                if pasada == 1:
                                    # Ideal: L1 + L2
                                    if self._profe_cumple_L1(pid, d, h, ocupacion_L1) and \
                                       self._profe_cumple_L2(pid, d, h, preferencias_L2):
                                        se_asigna = True
                                
                                elif pasada == 2:
                                    # Flexible: Solo L1
                                    if self._profe_cumple_L1(pid, d, h, ocupacion_L1):
                                        se_asigna = True
                                        aviso = f"⚠️ {nom}: Preferencia L2 ignorada"
                                
                                elif pasada == 3:
                                    # Última oportunidad: sin restricciones
                                    se_asigna = True
                                    aviso = f"⚠️ {nom}: Restricciones ignoradas"
                                
                                if se_asigna:
                                    self._asignar(horario, d, h, mid, pid, ocupacion_L1)
                                    colocado = True
                                    if aviso:
                                        self.avisos.append(aviso)
                                    break

                if not colocado:
                    self.errores.append(f"❌ No cabe: {nom}")

        # 4. Guardado
        if not self.errores:
            # Éxito: el horario se generó completamente
            msg = "Horario generado correctamente."
            self._guardar(horario, modulos_datos, nombre_ciclo)
            return True, msg
        else:
            # Error: hay módulos que no caben
            return False, "\n".join(self.errores)

    # --- AUXILIARES ---
    def _ordenar_dias_por_carga(self, horario, mid):
        """Ordena los días por carga de trabajo (menos cargados primero)"""
        carga = []
        for d in range(5):
            horas_ocupadas = sum(1 for h in range(6) if horario[d][h] is not None)
            carga.append((horas_ocupadas, d))
        carga.sort()  # Ordena por carga
        return [d for _, d in carga]
    
    def _ordenar_franjas_por_disponibilidad(self, horario, d, pid, ocupacion_L1, preferencias_L2):
        """Ordena las franjas horarias de forma inteligente"""
        franjas = []
        for h in range(6):
            if horario[d][h] is None:
                # Puntuación: 0 es mejor
                puntuacion = 0
                
                # Si cumple L1, mejor puntuación
                if not (pid and (d, h) in ocupacion_L1.get(pid, set())):
                    puntuacion += 0
                else:
                    puntuacion += 10
                
                # Si cumple L2, mejor puntuación
                if preferencias_L2 and not (pid and (d, h) in preferencias_L2.get(pid, set())):
                    puntuacion += 0
                else:
                    puntuacion += 5
                
                franjas.append((puntuacion, h))
        
        # Ordenar por puntuación
        franjas.sort()
        return [h for _, h in franjas]
    
    def _cargar_restricciones(self, pid, nivel):
        ocupadas = set()
        prefs = self.db.obtener_preferencias(pid)
        dias = {"LUNES":0, "MARTES":1, "MIERCOLES":2, "MIÉRCOLES":2, "JUEVES":3, "VIERNES":4}
        for p in prefs:
            if p['nivel_prioridad'] == nivel:
                d = dias.get(p['dia_semana'].upper().replace("É", "E"))
                h = p['franja_horaria'] - 1
                if d is not None: ocupadas.add((d, h))
        return ocupadas

    def _profe_cumple_L1(self, pid, d, h, oc):
        if not pid: return True
        return (d, h) not in oc.get(pid, set())

    def _profe_cumple_L2(self, pid, d, h, pr):
        if not pid: return True
        return (d, h) not in pr.get(pid, set())

    def _asignar(self, hor, d, h, mid, pid, oc):
        hor[d][h] = mid
        if pid: oc[pid].add((d, h))

    def _contar_horas_dia(self, hor, d, mid):
        return sum(1 for h in range(6) if hor[d][h] == mid)

    def _guardar(self, matriz, datos, nombre_ciclo):
        filas = []
        dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
        for d in range(5):
            for h in range(6):
                mid = matriz[d][h]
                if mid:
                    dato = next((x for x in datos if x['id_modulo'] == mid), None)
                    pid = dato['id_profesor'] if dato else None
                    # AÑADIMOS EL CAMPO 'ciclo'
                    filas.append({
                        "id_modulo": mid, 
                        "id_trabajador": pid, 
                        "dia_semana": dias[d], 
                        "franja_horaria": h+1,
                        "ciclo": nombre_ciclo 
                    })
        if filas: self.db.guardar_horario_generado(filas, nombre_ciclo)