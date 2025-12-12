import os
from supabase import create_client, Client

class DatabaseManager:
    def __init__(self):
        # --- TUS CREDENCIALES ---
        self.url: str = "https://vprdputyefmobtjajucw.supabase.co"
        self.key: str = "sb_publishable_qGU8m8neFbPiKS2HefNinQ_nxLwUQFa"
        
        try:
            self.client: Client = create_client(self.url, self.key)
            print("Supabase se ha conectado con exito.")
        except Exception as e:
            print(f"Ha ocurrido un erros y no se ha podido conectar a la base de datos de SUPABASE: {e}")

    # --- LECTURA ---
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
        try:
            return self.client.table('preferencias').select("*").execute().data or []
        except:
            return []

    # --- ESCRITURA CRUD ---
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

    # --- MULTI-ASIGNACIÓN ---
    def obtener_modulos_disponibles(self, id_p=None):
        try:
            todos = self.obtener_modulos()
            ocupados = set()
            asig = self.client.table('asignacion_modulo_trabajador').select("*").execute().data or []
            for a in asig:
                if str(a['id_trabajador']) != str(id_p): ocupados.add(a['id_modulo'])
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

    # --- GENERADOR Y VISTA MEJORADA ---

    def obtener_ciclos_unicos(self):
        """Para el desplegable del Generador (antes de generar)"""
        try:
            res = self.client.table('modulos').select('ciclo, curso').execute()
            if res.data: return sorted(list(set(f"{x['ciclo']} {x['curso']}" for x in res.data)))
            return []
        except: return []

    def obtener_datos_generacion(self, etiqueta):
        try:
            parts = etiqueta.rsplit(' ', 1)
            if len(parts)!=2: return []
            cic, cur = parts[0], int(parts[1])
            modulos = self.client.table('modulos').select("*").eq('ciclo', cic).eq('curso', cur).execute().data or []
            
            res = []
            for m in modulos:
                item = {"id_modulo": m['id_modulo'], "nombre_modulo": m['nombre_modulo'], "horas": m['horas_totales_semanales'], 
                        "nombre_profesor": "SIN ASIGNAR", "id_profesor": None, "color": "#333"}
                
                asig = self.client.table('asignacion_modulo_trabajador').select("id_trabajador").eq('id_modulo', m['id_modulo']).execute()
                if asig.data:
                    pid = asig.data[0]['id_trabajador']
                    prof = self.client.table('trabajadores').select("nombre, apellidos, color_asignado").eq('id_trabajador', pid).execute()
                    if prof.data:
                        pd = prof.data[0]
                        item["nombre_profesor"] = f"{pd['nombre']} {pd['apellidos']}"
                        item["id_profesor"] = pid
                        item["color"] = pd['color_asignado']
                res.append(item)
            return res
        except: return []

    def guardar_horario_generado(self, lista_datos, ciclo_etiqueta):
        
        try:
            # 1. Borrar solo lo viejo de este ciclo
            self.client.table('horario_generado').delete().eq('ciclo', ciclo_etiqueta).execute()
            
            # 2. Insertar lo nuevo
            self.client.table('horario_generado').insert(lista_datos).execute()
            return True
        except Exception as e:
            print(f"Error guardando horario: {e}")
            return False

    def obtener_listados_vista(self):
       
        try:
            # Ciclos disponibles (Directo de la nueva columna)
            res_ciclos = self.client.table('horario_generado').select('ciclo').execute()
            ciclos = sorted(list(set(x['ciclo'] for x in res_ciclos.data))) if res_ciclos.data else []
            
            # Profesores disponibles en el horario
            res_prof = self.client.table('horario_generado').select('id_trabajador').execute()
            profes = []
            if res_prof.data:
                ids = set(x['id_trabajador'] for x in res_prof.data if x['id_trabajador'])
                if ids:
                    all_p = self.obtener_profesores()
                    for p in all_p:
                        if p['id_trabajador'] in ids:
                            profes.append(f"{p['nombre']} {p['apellidos']}")
            
            return ciclos, sorted(profes)
        except Exception as e:
            print(f"Error listados vista: {e}")
            return [], []

    def obtener_horario_filtrado(self, modo, filtro):
        """
        Filtra usando la nueva columna 'ciclo' si el modo es CLASE.
        """
        try:
            raw = self.client.table('horario_generado').select("*").execute().data or []
            # Traemos info extra para pintar bonito
            all_mods = {m['id_modulo']: m for m in self.obtener_modulos()}
            all_profs = {p['id_trabajador']: p for p in self.obtener_profesores()}
            
            resultado = []
            
            for h in raw:
                mod = all_mods.get(h['id_modulo'])
                prof = all_profs.get(h['id_trabajador'])
                
                match = False
                texto_prin, texto_sec, color = "", "", "#333"
                
                # MODO CLASE: Usamos la columna 'ciclo' directamente
                if modo == 'CLASE':
                    if h.get('ciclo') == filtro:
                        match = True
                        texto_prin = mod['nombre_modulo'] if mod else "Módulo desconocido"
                        texto_sec = f"{prof['nombre']} {prof['apellidos']}" if prof else "Sin Profe"
                        color = prof['color_asignado'] if prof else "#666"

                # MODO PROFESOR
                elif modo == 'PROFESOR' and prof:
                    nombre_completo = f"{prof['nombre']} {prof['apellidos']}"
                    if nombre_completo == filtro:
                        match = True
                        texto_prin = f"{mod['nombre_modulo']} ({h.get('ciclo', '?')})" if mod else "?"
                        texto_sec = f"Aula: {mod.get('clases_asociadas') or '?'}" if mod else ""
                        color = prof['color_asignado']

                if match:
                    resultado.append({
                        "dia": h['dia_semana'],
                        "hora": h['franja_horaria'],
                        "texto1": texto_prin,
                        "texto2": texto_sec,
                        "color": color
                    })
            return resultado
        except Exception as e:
            print(e)
            return []

    def borrar_horario_por_ciclo(self, ciclo_nombre):
        """Borrado rápido usando la nueva columna"""
        try:
            self.client.table('horario_generado').delete().eq('ciclo', ciclo_nombre).execute()
            return True
        except: return False

    def obtener_ocupacion_horario_profesores(self, lista_ids):
        # Igual que antes, útil para el generador
        if not lista_ids: return {}
        try:
            res = self.client.table('horario_generado').select("*").execute()
            ocup = {}
            for r in res.data or []:
                pid = r['id_trabajador']
                if pid in lista_ids:
                    if pid not in ocup: ocup[pid] = set()
                    ocup[pid].add((r['dia_semana'], r['franja_horaria']))
            return ocup
        except: return {}

    def hay_horarios_generados(self):
        """Verifica si hay horarios generados en la BD"""
        try:
            res = self.client.table('horario_generado').select("id").limit(1).execute()
            return bool(res.data)
        except:
            return False
