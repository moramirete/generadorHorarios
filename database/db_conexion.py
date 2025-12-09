import os
from supabase import create_client, Client

class DatabaseManager:
    def __init__(self):
        # --- TUS CREDENCIALES ---
        # Asegúrate de poner aquí tus claves reales si no usas variables de entorno
        self.url: str = "https://vprdputyefmobtjajucw.supabase.co"
        self.key: str = "sb_publishable_qGU8m8neFbPiKS2HefNinQ_nxLwUQFa"
        
        try:
            self.client: Client = create_client(self.url, self.key)
            print("✅ Supabase conectado correctamente.")
        except Exception as e:
            print(f"❌ Error al conectar con Supabase: {e}")

    # --- MÉTODOS DE LECTURA ---
    
    def obtener_profesores(self):
        try:
            response = self.client.table('trabajadores').select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error obteniendo profesores: {e}")
            return []

    def obtener_modulos(self):
        try:
            response = self.client.table('modulos').select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error obteniendo módulos: {e}")
            return []

    def obtener_preferencias(self, id_profesor):
        try:
            response = self.client.table('preferencias').select("*").eq('id_trabajador', id_profesor).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error obteniendo preferencias: {e}")
            return []

    def hay_horarios_generados(self):
        try:
            response = self.client.table('horario_generado').select("id_horario", count="exact").limit(1).execute()
            return response.count > 0
        except Exception:
            return False

    # --- MÉTODOS DE ESCRITURA (CRUD PROFESORES) ---

    def crear_profesor(self, datos):
        try:
            response = self.client.table('trabajadores').insert(datos).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creando profesor: {e}")
            return None

    def actualizar_profesor(self, id_profesor, datos):
        try:
            self.client.table('trabajadores').update(datos).eq('id_trabajador', id_profesor).execute()
            return True
        except Exception as e:
            print(f"Error actualizando profesor: {e}")
            return False

    def eliminar_profesor(self, id_profesor):
        try:
            self.client.table('trabajadores').delete().eq('id_trabajador', id_profesor).execute()
            return True
        except Exception as e:
            print(f"Error eliminando profesor: {e}")
            return False

    def guardar_preferencias(self, id_profesor, lista_nuevas):
        try:
            # 1. Borrar antiguas
            self.client.table('preferencias').delete().eq('id_trabajador', id_profesor).execute()
            # 2. Insertar nuevas
            if lista_nuevas:
                self.client.table('preferencias').insert(lista_nuevas).execute()
            return True
        except Exception as e:
            print(f"Error guardando preferencias: {e}")
            return False

    # --- NUEVOS MÉTODOS PARA ASIGNACIÓN DE MÓDULO PRINCIPAL ---

    def obtener_id_modulo_asignado(self, id_profesor):
        """Busca el módulo asignado al profesor en la tabla intermedia"""
        try:
            response = self.client.table('asignacion_modulo_trabajador')\
                .select("id_modulo")\
                .eq('id_trabajador', id_profesor)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['id_modulo']
            return None
        except Exception as e:
            print(f"Error buscando asignación: {e}")
            return None

    def guardar_asignacion_modulo(self, id_profesor, id_modulo):
        """Guarda la relación (Borra anteriores para mantener uno solo principal)"""
        try:
            # 1. Borrar anteriores
            self.client.table('asignacion_modulo_trabajador')\
                .delete()\
                .eq('id_trabajador', id_profesor)\
                .execute()

            # 2. Insertar nuevo si no es None
            if id_modulo is not None:
                self.client.table('asignacion_modulo_trabajador').insert({
                    "id_trabajador": id_profesor,
                    "id_modulo": id_modulo
                }).execute()
            return True
        except Exception as e:
            print(f"Error guardando asignación: {e}")
            return False

if __name__ == "__main__":
    # Prueba rápida
    db = DatabaseManager()
    print(f"Profesores encontrados: {len(db.obtener_profesores())}")