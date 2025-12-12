import os
from supabase import create_client, Client

class DatabaseManager:
    def __init__(self):
        # --- TUS CREDENCIALES ---
        self.url: str = "https://vprdputyefmobtjajucw.supabase.co"
        self.key: str = "sb_publishable_qGU8m8neFbPiKS2HefNinQ_nxLwUQFa"
        
        try:
            self.client: Client = create_client(self.url, self.key)
            print("✅ Supabase conectado correctamente.")
        except Exception as e:
            print(f"❌ Error al conectar con Supabase: {e}")

    # --- MÉTODOS DE LECTURA BÁSICOS (OPTIMIZADOS) ---
    def obtener_profesores(self):
        try: return self.client.table('trabajadores').select("*").execute().data or []
        except: return []

    def obtener_modulos(self):
        try: return self.client.table('modulos').select("*").execute().data or []
        except: return []

    def obtener_preferencias(self, id_profesor):
        try: return self.client.table('preferencias').select("*").eq('id_trabajador', id_profesor).execute().data or []
        except: return []

    def obtener_todas_preferencias(self):
        """Descarga TODAS las preferencias para el exportar CSV"""
        try: 
            return self.client.table('preferencias').select("*").execute().data or []
        except: 
            return []

    def hay_horarios_generados(self):
        try:
            # count='exact', head=True es más ligero, solo devuelve el número
            res = self.client.table('horario_generado').select("id_horario", count="exact").limit(1).execute()
            return res.count > 0
        except: return False

    # --- CRUD BÁSICO ---
    def crear_profesor(self, d):
        try: return self.client.table('trabajadores').insert(d).execute().data[0]
        except: return None
    def actualizar_profesor(self, i, d):
        try: return bool(self.client.table('trabajadores').update(d).eq('id_trabajador', i).execute().data)
        except: return False
    def eliminar_profesor(self, i):
        try: return bool(self.client.table('trabajadores').delete().eq('id_trabajador', i).execute().data)
        except: return False
    
    def crear_modulo(self, d):
        try: return bool(self.client.table('modulos').insert(d).execute().data)
        except: return False
    def actualizar_modulo(self, i, d):
        try: return bool(self.client.table('modulos').update(d).eq('id_modulo', i).execute().data)
        except: return False
    def eliminar_modulo(self, i):
        try: return bool(self.client.table('modulos').delete().eq('id_modulo', i).execute().data)
        except: return False

    # --- ASIGNACIONES OPTIMIZADAS ---
    def obtener_modulos_disponibles(self, id_p=None):
        try:
            # 1. Traemos todo de golpe (2 peticiones en total)
            todos = self.obtener_modulos()
            asig = self.client.table('asignacion_modulo_trabajador').select("id_modulo, id_trabajador").execute().data or []
            
            # 2. Procesamos en local (Instantáneo)
            ocupados = set()
            for a in asig:
                if str(a['id_trabajador']) != str(id_p): 
                    ocupados.add(a['id_modulo'])
            
            return [m for m in todos if m['id_modulo'] not in ocupados]
        except: return []

    def obtener_ids_modulos_profesor(self, id_p):
        try:
            res = self.client.table('asignacion_modulo_trabajador').select("id_modulo").eq('id_trabajador', id_p).execute()
            return [x['id_modulo'] for x in res.data] if res.data else []
        except: return []

    def guardar_asignaciones_profesor(self, id_p, lista_ids):
        try:
            self.client.table('asignacion_modulo_trabajador').delete().eq('id_trabajador', id_p).execute()
            if lista_ids:
                data = [{"id_trabajador": id_p, "id_modulo": mid} for mid in lista_ids]
                self.client.table('asignacion_modulo_trabajador').insert(data).execute()
            return True
        except: return False

    def guardar_preferencias(self, id_p, lista):
        try:
            self.client.table('preferencias').delete().eq('id_trabajador', id_p).execute()
            if lista: self.client.table('preferencias').insert(lista).execute()
            return True
        except: return False

    def obtener_ocupacion_horario_profesores(self, lista_ids):
        if not lista_ids: return {}
        try:
            # Usamos filtro .in_ para traer solo lo necesario
            res = self.client.table('horario_generado').select("*").in_('id_trabajador', lista_ids).execute()
            ocup = {}
            for r in res.data or []:
                pid = r['id_trabajador']
                if pid not in ocup: ocup[pid] = set()
                ocup[pid].add((r['dia_semana'], r['franja_horaria']))
            return ocup
        except: return {}

    # GENERADOR OPTIMIZADO 

    def obtener_ciclos_unicos(self):
        try:
            res = self.client.table('modulos').select('ciclo, curso').execute()
            if res.data:
                return sorted(list(set(f"{x['ciclo']} {x['curso']}" for x in res.data)))
            return []
        except: return []

    def obtener_datos_generacion(self, etiqueta):
        """
        Versión OPTIMIZADA: Realiza solo 3 peticiones en lugar de 20+.
        Cruza los datos en memoria.
        """
        try:
            parts = etiqueta.rsplit(' ', 1)
            if len(parts)!=2: return []
            cic, cur = parts[0], int(parts[1])
            
            
            modulos = self.client.table('modulos').select("*").eq('ciclo', cic).eq('curso', cur).execute().data or []
            if not modulos: return []
            
            ids_modulos = [m['id_modulo'] for m in modulos]
            
             
            asignaciones = self.client.table('asignacion_modulo_trabajador').select("*").in_('id_modulo', ids_modulos).execute().data or []
            
            
            map_mod_prof = {a['id_modulo']: a['id_trabajador'] for a in asignaciones}
            
            ids_profesores = list(set(map_mod_prof.values()))
            
             
            map_prof_datos = {}
            if ids_profesores:
                profes = self.client.table('trabajadores').select("*").in_('id_trabajador', ids_profesores).execute().data or []
                # 
                map_prof_datos = {p['id_trabajador']: p for p in profes}
            
            # 4. Cruzar datos en local
            res = []
            for m in modulos:
                item = {
                    "id_modulo": m['id_modulo'], 
                    "nombre_modulo": m['nombre_modulo'], 
                    "horas": m['horas_totales_semanales'], 
                    "nombre_profesor": "⚠️ SIN ASIGNAR", 
                    "id_profesor": None, 
                    "color": "#333"
                }
                
                pid = map_mod_prof.get(m['id_modulo'])
                if pid:
                    prof_data = map_prof_datos.get(pid)
                    if prof_data:
                        item["nombre_profesor"] = f"{prof_data['nombre']} {prof_data['apellidos']}"
                        item["id_profesor"] = pid
                        item["color"] = prof_data['color_asignado']
                
                res.append(item)
            return res
            
        except Exception as e:
            print(f"Error optimizado: {e}")
            return []

    def guardar_horario_generado(self, lista, ciclo):
        try:
            self.client.table('horario_generado').delete().eq('ciclo', ciclo).execute()
            self.client.table('horario_generado').insert(lista).execute()
            return True
        except: return False

    # --- VISTA OPTIMIZADA ---

    def obtener_listados_vista(self):
        try:
            # Traer solo columnas necesarias para filtrar
            h_data = self.client.table('horario_generado').select('ciclo, id_trabajador').execute().data or []
            
            ciclos = sorted(list(set(x['ciclo'] for x in h_data if x['ciclo'])))
            ids_profs = list(set(x['id_trabajador'] for x in h_data if x['id_trabajador']))
            
            profes = []
            if ids_profs:
                # Petición masiva de nombres
                p_data = self.client.table('trabajadores').select("nombre, apellidos").in_('id_trabajador', ids_profs).execute().data or []
                profes = sorted([f"{p['nombre']} {p['apellidos']}" for p in p_data])
            
            return ciclos, profes
        except: return [], []

    def obtener_horario_filtrado(self, modo, filtro):
        try:
            # Traemos todo el horario (suele ser ligero, texto plano)
            raw = self.client.table('horario_generado').select("*").execute().data or []
            
            # Carga Eager de catálogos
            all_mods = {m['id_modulo']: m for m in self.obtener_modulos()}
            all_profs = {p['id_trabajador']: p for p in self.obtener_profesores()}
            
            resultado = []
            for h in raw:
                mod = all_mods.get(h['id_modulo'])
                prof = all_profs.get(h['id_trabajador'])
                
                match = False
                if modo == 'CLASE' and h.get('ciclo') == filtro:
                    match = True
                    t1 = mod['nombre_modulo'] if mod else "?"
                    t2 = f"{prof['nombre']} {prof['apellidos']}" if prof else "Sin Profe"
                    col = prof['color_asignado'] if prof else "#666"
                
                elif modo == 'PROFESOR' and prof:
                    if f"{prof['nombre']} {prof['apellidos']}" == filtro:
                        match = True
                        t1 = f"{mod['nombre_modulo']}" if mod else "?"
                        t2 = f"Aula: {mod.get('ciclo')} {mod.get('curso')}" if mod else "?"
                        col = prof['color_asignado']

                if match:
                    resultado.append({
                        "dia": h['dia_semana'], "hora": h['franja_horaria'],
                        "texto1": t1, "texto2": t2, "color": col
                    })
            return resultado
        except: return []

    def borrar_horario_por_ciclo(self, ciclo):
        try:
            self.client.table('horario_generado').delete().eq('ciclo', ciclo).execute()
            return True
        except: return False



   

   
    def obtener_horario_completo_para_exportar(self):
        """Obtiene la tabla de horario completa con detalles (ciclo, modulo, profe, color)."""
        try: 
            
            raw = self.client.table('horario_generado').select("*").execute().data or []
            all_mods = {m['id_modulo']: m for m in self.obtener_modulos()}
            all_profs = {p['id_trabajador']: p for p in self.obtener_profesores()}

            resultado = []
            for h in raw:
                mod = all_mods.get(h['id_modulo'])
                prof = all_profs.get(h['id_trabajador'])
                
                # Formato detallado para exportación
                resultado.append({
                    "Ciclo": h.get('ciclo'),
                    "Curso": mod.get('curso') if mod else None,
                    "Día": h['dia_semana'], 
                    "Franja Horaria": h['franja_horaria'],
                    "Módulo ID": h['id_modulo'],
                    "Nombre Módulo": mod['nombre_modulo'] if mod else "Módulo Desconocido",
                    "Profesor ID": h['id_trabajador'],
                    "Nombre Profesor": f"{prof['nombre']} {prof['apellidos']}" if prof else "Sin Asignar",
                    "Color Asignado": prof['color_asignado'] if prof else "#CCCCCC"
                })
            return resultado
        except Exception as e: 
            print(f"Error al obtener horario completo para exportar: {e}")
            return []