import random

class GeneradorAutomatico:
    def __init__(self, db):
        self.db = db
        self.errores = []
        self.avisos = []

    def generar_horario(self, nombre_ciclo):
        """Genera el horario y lo guarda con la etiqueta del ciclo"""
        print(f"🚀 Generando para: {nombre_ciclo}")
        
        modulos_datos = self.db.obtener_datos_generacion(nombre_ciclo)
        
        # 1. Cargar restricciones (Profesores de este grupo + sus otras clases)
        ids_profesores = [m['id_profesor'] for m in modulos_datos if m['id_profesor']]
        ocupacion_existente = self.db.obtener_ocupacion_horario_profesores(ids_profesores)
        
        ocupacion_L1 = {}
        preferencias_L2 = {}
        
        for m in modulos_datos:
            pid = m['id_profesor']
            if pid:
                if pid not in ocupacion_L1:
                    bloqueos = self._cargar_restricciones(pid, nivel=1)
                    # Añadir clases que ya tiene en OTROS grupos
                    clases_ya = ocupacion_existente.get(pid, set())
                    dias_map = {"LUNES":0, "MARTES":1, "MIERCOLES":2, "MIÉRCOLES":2, "JUEVES":3, "VIERNES":4}
                    for d_nom, h_num in clases_ya:
                        d_idx = dias_map.get(d_nom.upper().replace("É", "E"))
                        if d_idx is not None: bloqueos.add((d_idx, h_num - 1))
                    
                    ocupacion_L1[pid] = bloqueos

                if pid not in preferencias_L2:
                    preferencias_L2[pid] = self._cargar_restricciones(pid, nivel=2)

        # 2. Matriz y Ordenación
        horario = [[None for _ in range(6)] for _ in range(5)]
        modulos_datos.sort(key=lambda x: x['horas'], reverse=True)

        # 3. Asignación
        for m in modulos_datos:
            horas_pendientes = m['horas']
            mid = m['id_modulo']
            pid = m['id_profesor']
            nom = m['nombre_modulo']
            
            for _ in range(horas_pendientes):
                colocado = False
                
                # Pasada 1 (Ideal)
                for d in range(5):
                    if self._contar_horas_dia(horario, d, mid) >= 2: continue
                    for h in range(6):
                        if horario[d][h] is None:
                            if self._profe_cumple_L1(pid, d, h, ocupacion_L1) and \
                               self._profe_cumple_L2(pid, d, h, preferencias_L2):
                                self._asignar(horario, d, h, mid, pid, ocupacion_L1)
                                colocado = True; break
                    if colocado: break
                
                # Pasada 2 (Forzosa)
                if not colocado:
                    for d in range(5):
                        if self._contar_horas_dia(horario, d, mid) >= 2: continue
                        for h in range(6):
                            if horario[d][h] is None:
                                if self._profe_cumple_L1(pid, d, h, ocupacion_L1):
                                    self._asignar(horario, d, h, mid, pid, ocupacion_L1)
                                    colocado = True
                                    self.avisos.append(f"⚠️ {nom}: Preferencia ignorada ({d+1}, {h+1})")
                                    break
                        if colocado: break

                if not colocado:
                    self.errores.append(f"❌ No cabe: {nom}")

        # 4. Guardado
        msg = "Horario generado."
        if self.avisos: msg += f"\n\n{len(self.avisos)} avisos de preferencia."
        
        if not self.errores:
            # AQUÍ ESTÁ EL CAMBIO: Pasamos el nombre del ciclo al guardar
            self._guardar(horario, modulos_datos, nombre_ciclo)
            return True, msg
        else:
            return False, "\n".join(self.errores)

    # --- AUXILIARES ---
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