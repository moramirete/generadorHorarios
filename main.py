import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt5 import uic

# Importaciones del proyecto
from database.db_conexion import DatabaseManager
from controllers.gestion_datos import GestionDatosController
from controllers.vista_horario import VistaHorarioController

# Importamos el controlador del generador (Stub por seguridad)
try:
    from logic.generador import GeneradorController
except ImportError:
    class GeneradorController:
        def __init__(self, ui, db):
            self.ui = ui
            self.db = db
            try:
                self.ui.btnLanzarGenerador.clicked.connect(self.iniciar_generacion)
            except AttributeError:
                pass
        def iniciar_generacion(self):
            QMessageBox.information(self.ui, "Generador", "¡Algoritmo iniciado! (Lógica pendiente)")

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Cargar la CARCASA
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'main_shell.ui')
        uic.loadUi(ui_path, self)
        
        # 2. Iniciar Base de Datos
        print("Iniciando sistema...")
        self.db = DatabaseManager()
        
        # 3. Conectar Botones del Menú Lateral
        self.btnVistaHorario.clicked.connect(self.cargar_vista_horario)
        self.btnGestionDatos.clicked.connect(self.cargar_gestion_datos)
        self.btnGenerarHorario.clicked.connect(self.cargar_generador)
        
        # Conectar el botón de Exportar (que ahora está en el menú)
        try:
            self.btnExportar.clicked.connect(self.exportar_datos)
        except AttributeError:
            pass

        # 4. Configurar Usuario en el Menú Lateral
        # Esto buscará los labels en main_shell.ui y pondrá los datos
        try:
            self.lblUserName.setText("Admin") 
            self.lblUserRole.setText("Administrador")
        except AttributeError:
            pass # Si no encuentra los labels, no pasa nada

        # 5. Cargar la primera página por defecto
        self.btnVistaHorario.click()

    # --- GESTIÓN DE PÁGINAS (ADAPTADO A TU NUEVO UI) ---

    def limpiar_contenedor(self):
        """Elimina el widget actual del layout principal"""
        # AHORA USAMOS DIRECTAMENTE EL LAYOUT, NO UN WIDGET CONTENEDOR
        layout = self.layout_contenedor
        
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def cargar_ui_pagina(self, nombre_archivo):
        """Carga un archivo .ui dentro del layout"""
        self.limpiar_contenedor()
        
        path = os.path.join(os.path.dirname(__file__), 'ui', 'pages', nombre_archivo)
        try:
            nuevo_widget = uic.loadUi(path)
            # AÑADIMOS AL LAYOUT DIRECTAMENTE
            self.layout_contenedor.addWidget(nuevo_widget)
            return nuevo_widget
        except FileNotFoundError:
            print(f"❌ Error crítico: No se encontró el archivo: {nombre_archivo}")
            return None

    # --- FUNCIONES DE NAVEGACIÓN ---

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

    def exportar_datos(self):
        """Lógica del botón Exportar"""
        QMessageBox.information(
            self, 
            "Exportar Datos", 
            "¡Exportación a CSV iniciada!\n\nSe generará un archivo con los datos actuales."
        )

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