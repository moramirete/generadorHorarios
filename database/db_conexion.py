import os
from supabase import create_client, Client

#--- CLASE DE GESTIÓN DE LA BASE DE DATOS ---
# Codigo de prueba para la conexión a Supabase

class DatabaseManager:
    def __init__(self):
        # SUSTITUYE ESTO CON TUS DATOS DE SUPABASE (Settings -> API)
        self.url: str = "https://vprdputyefmobtjajucw.supabase.co"
        self.key: str = "sb_publishable_qGU8m8neFbPiKS2HefNinQ_nxLwUQFa"
        
        try:
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            print(f"Error al conectar con Supabase: {e}")

    # --- MÉTODOS DE LECTURA ---
    
    def obtener_profesores(self):
        """Devuelve la lista de diccionarios de profesores"""
        try:
            response = self.client.table('trabajadores').select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error obteniendo profesores: {e}")
            return []

    def obtener_modulos(self):
        """Devuelve todos los módulos"""
        try:
            response = self.client.table('modulos').select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error obteniendo módulos: {e}")
            return []

    def obtener_preferencias(self):
        """Devuelve todas las preferencias"""
        try:
            response = self.client.table('preferencias').select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error obteniendo preferencias: {e}")
            return []
        
    # --- Añadir esto en db_conexion.py ---
    def hay_horarios_generados(self):
        """Verifica si existe algún registro en la tabla de horarios"""
        try:
            # Hacemos una consulta ligera, solo pedimos 1 registro para ver si existe
            response = self.client.table('horario_generado').select("id_horario", count="exact").limit(1).execute()
            # Si count es mayor que 0, es que hay horarios
            return response.count > 0
        except Exception as e:
            print(f"Error verificando horarios: {e}")
            return False

    # --- MÉTODO PARA PROBAR LA CONEXIÓN ---
if __name__ == "__main__":
    db = DatabaseManager()
    profes = db.obtener_profesores()