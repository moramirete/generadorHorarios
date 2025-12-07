import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

# IMPORTANTE: Fíjate cómo importamos ahora gracias a las carpetas
# from [nombre_carpeta].[nombre_archivo] import [NombreClase]
from database.db_conexion import DatabaseManager

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Horarios - AutoHorarios")
        self.resize(800, 600)
        
        # 1. Inicializamos la base de datos
        print("Iniciando conexión a base de datos...")
        self.db = DatabaseManager()
        
        # 2. Probamos que funciona trayendo datos (solo para ver en consola)
        profesores = self.db.obtener_profesores()
        print(f"Conexión exitosa desde main.py. Profesores cargados: {len(profesores)}")

def main():
    app = QApplication(sys.argv)
    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()