import sys

# Aumentamos límite recursión
sys.setrecursionlimit(3000)

class GeneradorAutomatico:
    def __init__(self, db):
        self.db = db
        self.errores = []
        self.avisos = []
        self.horario = []
        self.ocupacion_L1 = {}
        self.preferencias_L2 = {}
        self.lista_items_a_colocar = []

    def generar_horario(self, nombre_ciclo):
        print(f"Generando para: {nombre_ciclo}")
        
        modulos_datos = self.db.obtener_datos_generacion(nombre_ciclo)
        if not modulos_datos:
            return False, "No se encontraron módulos."

        # Cargar restricciones
        ids_profesores = [m['id_profesor'] for m in modulos_datos if m['id_profesor']]
        ocupacion_existente = self.db.obtener_ocupacion_horario_profesores(ids_profesores)
        
        self.ocupacion_L1 = {}
        self.preferencias_L2 = {}
        
        for m in modulos_datos:
            pid = m['id_profesor']
            if pid:
                if pid not in self.ocupacion_L1:
                    bloqueos = self._cargar_restricciones(pid, nivel=1)
                    clases_ya = ocupacion_existente.get(pid, set())
                    dias_map = {"LUNES":0, "MARTES":1, "MIERCOLES":2, "MIÉRCOLES":2, "JUEVES":3, "VIERNES":4}
                    for d_nom, h_num in clases_ya:
                        d_idx = dias_map.get(d_nom.upper().replace("É", "E"))
                        if d_idx is not None: bloqueos.add((d_idx, h_num - 1))
                    self.ocupacion_L1[pid] = bloqueos

                if pid not in self.preferencias_L2:
                    self.preferencias_L2[pid] = self._cargar_restricciones(pid, nivel=2)

        # Inicializar
        self.horario = [[None for _ in range(6)] for _ in range(5)]
        
        # Ordenar (más horas primero)
        modulos_datos.sort(key=lambda x: x['horas'], reverse=True)
        
        self.lista_items_a_colocar = []
        for m in modulos_datos:
            for _ in range(m['horas']):
                self.lista_items_a_colocar.append({
                    'mid': m['id_modulo'],
                    'pid': m['id_profesor'],
                    'nom': m['nombre_modulo'],
                    'max_dia': m['max_diarias']
                })

        # Ejecutar Backtracking
        exito = self._backtrack(index=0)

        if exito:
            self._guardar(self.horario, modulos_datos, nombre_ciclo)
            msg = "Horario generado con éxito."
            if self.avisos: 
                msg += f"\n\nSe ignoraron preferencias (Nivel 2) en {len(set(self.avisos))} casos."
            return True, msg
        else:
            return False, "No se encontró solución válida."

    def _backtrack(self, index):
        if index == len(self.lista_items_a_colocar):
            return True

        item = self.lista_items_a_colocar[index]
        mid, pid, nom = item['mid'], item['pid'], item['nom']
        max_h = item['max_dia'] # <--- LEEMOS EL LÍMITE ESPECÍFICO

        # Probar huecos
        for d in range(5):
            
            if self._contar_horas_dia(self.horario, d, mid) >= max_h:
                continue

            for h in range(6):
                if self.horario[d][h] is None:
                    if self._profe_cumple_L1(pid, d, h):
                        
                        # Colocar
                        self.horario[d][h] = mid
                        if pid: self.ocupacion_L1[pid].add((d, h))
                        
                        aviso = None
                        if not self._profe_cumple_L2(pid, d, h):
                            dias_txt = ["L", "M", "X", "J", "V"]
                            aviso = f"{nom} ({dias_txt[d]}-{h+1})"
                            self.avisos.append(aviso)

                        # Recursión
                        if self._backtrack(index + 1):
                            return True

                        # Backtrack
                        self.horario[d][h] = None
                        if pid: self.ocupacion_L1[pid].remove((d, h))
                        if aviso: self.avisos.pop()
        return False

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

    def _profe_cumple_L1(self, pid, d, h):
        if not pid: return True
        return (d, h) not in self.ocupacion_L1.get(pid, set())

    def _profe_cumple_L2(self, pid, d, h):
        if not pid: return True
        return (d, h) not in self.preferencias_L2.get(pid, set())

    def _contar_horas_dia(self, horario, d, mid):
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
                        "id_modulo": mid, "id_trabajador": pid, 
                        "dia_semana": dias[d], "franja_horaria": h+1,
                        "ciclo": nombre_ciclo 
                    })
        if filas: self.db.guardar_horario_generado(filas, nombre_ciclo)