import sys

# Aumentamos el límite de recursión por si acaso (el backtracking usa recursividad profunda)
sys.setrecursionlimit(3000)

class GeneradorAutomatico:
    def __init__(self, db):
        self.db = db
        self.errores = []
        self.avisos = []
        
        # Estructuras de datos globales para el proceso recursivo
        self.horario = []       # Matriz 5x6
        self.ocupacion_L1 = {}  # {id_profe: set((dia, hora))} - Restricciones duras
        self.preferencias_L2 = {} # {id_profe: set((dia, hora))} - Preferencias blandas
        self.lista_items_a_colocar = [] # Lista plana de horas individuales a asignar

    def generar_horario(self, nombre_ciclo):
        """
        Algoritmo Backtracking (Vuelta Atrás).
        Prueba combinaciones recursivamente hasta encontrar una válida.
        """
        print(f"Generando para: {nombre_ciclo} (Modo: Backtracking)")
        
        # 1. Obtener datos
        modulos_datos = self.db.obtener_datos_generacion(nombre_ciclo)
        
        if not modulos_datos:
            return False, "No se encontraron módulos para este ciclo."

        # 2. Cargar restricciones iniciales (Profesores)
        ids_profesores = [m['id_profesor'] for m in modulos_datos if m['id_profesor']]
        ocupacion_existente = self.db.obtener_ocupacion_horario_profesores(ids_profesores)
        
        self.ocupacion_L1 = {}
        self.preferencias_L2 = {}
        
        for m in modulos_datos:
            pid = m['id_profesor']
            if pid:
                if pid not in self.ocupacion_L1:
                    bloqueos = self._cargar_restricciones(pid, nivel=1)
                    # Añadir clases ya asignadas en otros grupos (Multiverso)
                    clases_ya = ocupacion_existente.get(pid, set())
                    dias_map = {"LUNES":0, "MARTES":1, "MIERCOLES":2, "MIÉRCOLES":2, "JUEVES":3, "VIERNES":4}
                    for d_nom, h_num in clases_ya:
                        d_idx = dias_map.get(d_nom.upper().replace("É", "E"))
                        if d_idx is not None: 
                            bloqueos.add((d_idx, h_num - 1)) # Restar 1 porque array es 0-5
                    
                    self.ocupacion_L1[pid] = bloqueos

                if pid not in self.preferencias_L2:
                    self.preferencias_L2[pid] = self._cargar_restricciones(pid, nivel=2)

        # 3. Inicializar Matriz y Lista de Tareas
        self.horario = [[None for _ in range(6)] for _ in range(5)] # 5 días x 6 horas
        
        # Aplanar los módulos en horas individuales para el backtracking.
        # Ordenamos por dificultad: los que tienen más horas totales primero.
        modulos_datos.sort(key=lambda x: x['horas'], reverse=True)
        
        self.lista_items_a_colocar = []
        for m in modulos_datos:
            # Añadimos una entrada por cada hora que tenga la asignatura
            for _ in range(m['horas']):
                self.lista_items_a_colocar.append({
                    'mid': m['id_modulo'],
                    'pid': m['id_profesor'],
                    'nom': m['nombre_modulo']
                })

        # 4. EJECUTAR BACKTRACKING
        # Empezamos intentando colocar el primer item (índice 0)
        exito = self._backtrack(index=0)

        # 5. RESULTADO
        if exito:
            self._guardar(self.horario, modulos_datos, nombre_ciclo)
            msg = "Horario generado con éxito."
            if self.avisos: 
                # Filtramos avisos únicos para no saturar
                avisos_unicos = list(set(self.avisos))
                msg += f"\n\nSe ignoraron preferencias (Nivel 2) en {len(avisos_unicos)} casos."
            return True, msg
        else:
            return False, "No se encontró ninguna combinación válida.\nRevisa los bloqueos (Nivel 1) de los profesores o la carga horaria."

    # --- NÚCLEO DEL BACKTRACKING ---

    def _backtrack(self, index):
        """
        Función recursiva: Intenta colocar el item de la posición 'index'.
        Si lo logra, se llama a sí misma para el siguiente (index+1).
        Si el siguiente falla, esta función "deshace" su cambio y prueba otro hueco.
        """
        # CASO BASE: Si hemos llegado al final de la lista, ¡hemos terminado!
        if index == len(self.lista_items_a_colocar):
            return True

        item = self.lista_items_a_colocar[index]
        mid, pid, nom = item['mid'], item['pid'], item['nom']

        # Probamos todos los huecos posibles (Día x Hora)
        # Se recorre Lunes -> Viernes, Hora 1 -> 6
        for d in range(5):
            # RESTRICCIÓN PEDAGÓGICA: No más de 2 horas seguidas del mismo módulo al día
            if self._contar_horas_dia(self.horario, d, mid) >= 2:
                continue

            for h in range(6):
                if self.horario[d][h] is None: # Hueco libre en el aula
                    
                    # Verificamos Nivel 1 (OBLIGATORIO: Profe libre y sin bloqueo)
                    if self._profe_cumple_L1(pid, d, h):
                        
                        # --- INTENTO: COLOCAR ---
                        self.horario[d][h] = mid
                        # Marcamos ocupación temporal para que en la recursión se sepa que está ocupado
                        if pid: self.ocupacion_L1[pid].add((d, h))
                        
                        # Gestión de Avisos Nivel 2 (Preferencia)
                        aviso_generado = None
                        if not self._profe_cumple_L2(pid, d, h):
                            dias_txt = ["L", "M", "X", "J", "V"]
                            aviso_generado = f"{nom} ({dias_txt[d]}-{h+1})"
                            self.avisos.append(aviso_generado)

                        # --- PASO RECURSIVO (LLAMADA MÁGICA) ---
                        if self._backtrack(index + 1):
                            return True # Si el camino siguió con éxito, retornamos éxito hacia arriba

                        # --- BACKTRACK (DESHACER / VOLVER ATRÁS) ---
                        # Si llegamos aquí, es que el camino futuro falló.
                        # Deshacemos los cambios de este paso y probamos el siguiente hueco del bucle.
                        self.horario[d][h] = None
                        if pid: self.ocupacion_L1[pid].remove((d, h))
                        if aviso_generado: self.avisos.pop()

        # Si probamos todos los días y horas y no encaja en ninguno, devolvemos False
        # Esto hará que el paso anterior (index-1) mueva su ficha a otro sitio.
        return False

    # --- FUNCIONES DE APOYO ---

    def _cargar_restricciones(self, pid, nivel):
        ocupadas = set()
        prefs = self.db.obtener_preferencias(pid)
        dias = {"LUNES":0, "MARTES":1, "MIERCOLES":2, "MIÉRCOLES":2, "JUEVES":3, "VIERNES":4}
        for p in prefs:
            if p['nivel_prioridad'] == nivel:
                d_str = p['dia_semana'].upper().replace("É", "E")
                d = dias.get(d_str)
                h = p['franja_horaria'] - 1
                if d is not None: ocupadas.add((d, h))
        return ocupadas

    def _profe_cumple_L1(self, pid, d, h):
        """Verifica restricciones duras (ocupación en otros grupos o bloqueo usuario)"""
        if not pid: return True
        return (d, h) not in self.ocupacion_L1.get(pid, set())

    def _profe_cumple_L2(self, pid, d, h):
        """Verifica preferencias blandas"""
        if not pid: return True
        return (d, h) not in self.preferencias_L2.get(pid, set())

    def _contar_horas_dia(self, horario, d, mid):
        """Cuenta cuántas horas de este módulo hay ya en este día"""
        return sum(1 for h in range(6) if horario[d][h] == mid)

    def _guardar(self, matriz, datos, nombre_ciclo):
        filas = []
        dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
        for d in range(5):
            for h in range(6):
                mid = matriz[d][h]
                if mid:
                    dato = next((x for x in datos if x['id_modulo'] == mid), None)
                    pid = dato['id_profesor'] if dato else None
                    filas.append({
                        "id_modulo": mid, 
                        "id_trabajador": pid, 
                        "dia_semana": dias[d], 
                        "franja_horaria": h+1,
                        "ciclo": nombre_ciclo 
                    })
        if filas: self.db.guardar_horario_generado(filas, nombre_ciclo)