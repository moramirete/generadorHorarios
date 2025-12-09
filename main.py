import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5 import uic

# Importaciones del proyecto
from database.db_conexion import DatabaseManager
from controllers.gestion_datos import GestionDatosController
from controllers.vista_horario import VistaHorarioController
from logic.generador import GeneradorController

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Cargar la CARCASA (Solo menú y hueco vacío)
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'main_shell.ui')
        uic.loadUi(ui_path, self)
        
        # 2. Iniciar Base de Datos
        self.db = DatabaseManager()
        
        # 3. Conectar menú lateral
        self.btnVistaHorario.clicked.connect(self.cargar_vista_horario)
        self.btnGestionDatos.clicked.connect(self.cargar_gestion_datos)
        self.btnGenerarHorario.clicked.connect(self.cargar_generador)
        
        # 4. Cargar la primera página por defecto
        self.btnVistaHorario.click()

    def limpiar_contenedor(self):
        """Elimina el widget actual del hueco principal"""
        layout = self.contenedor_principal.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def cargar_ui_pagina(self, nombre_archivo):
        """Carga un archivo .ui dentro del contenedor"""
        self.limpiar_contenedor()
        path = os.path.join(os.path.dirname(__file__), 'ui', 'pages', nombre_archivo)
        try:
            nuevo_widget = uic.loadUi(path)
            self.contenedor_principal.layout().addWidget(nuevo_widget)
            return nuevo_widget
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {nombre_archivo}")
            return None

    # --- NAVEGACIÓN ---

    def cargar_vista_horario(self):
        widget = self.cargar_ui_pagina('pagina_horario.ui')
        if widget:
            self.ctrl_vista = VistaHorarioController(widget, self.db, self)
            self.resaltar_boton(self.btnVistaHorario)

    def cargar_gestion_datos(self):
        widget = self.cargar_ui_pagina('pagina_gestion.ui')
        if widget:
            self.ctrl_gestion = GestionDatosController(widget, self.db)
            self.ctrl_gestion.cargar_datos_iniciales()
            self.resaltar_boton(self.btnGestionDatos)

    def cargar_generador(self):
        widget = self.cargar_ui_pagina('pagina_generador.ui')
        if widget:
            self.ctrl_gen = GeneradorController(widget, self.db)
            self.resaltar_boton(self.btnGenerarHorario)

    def resaltar_boton(self, boton_activo):
        self.btnVistaHorario.setChecked(False)
        self.btnGestionDatos.setChecked(False)
        self.btnGenerarHorario.setChecked(False)
        boton_activo.setChecked(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec_())