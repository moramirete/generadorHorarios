import sys
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QFileDialog
from PyQt5 import uic

# Importaciones del proyecto
from database.db_conexion import DatabaseManager
from controllers.gestion_datos import GestionDatosController
from controllers.vista_horario import VistaHorarioController

# Importamos el controlador del generador
try:
    from controllers.generador import GeneradorController
except ImportError:
    class GeneradorController:
        def __init__(self, ui, db, main_window=None): pass

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Cargar la CARCASA
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'main_shell.ui')
        uic.loadUi(ui_path, self)
        
        # 2.         Iniciar Base de Datos
        print("Iniciando sistema...")
        self.db = DatabaseManager()
        
        # 3. Conectar Botones del Menú Lateral
        self.btnVistaHorario.clicked.connect(self.cargar_vista_horario)
        self.btnGestionDatos.clicked.connect(self.cargar_gestion_datos)
        self.btnGenerarHorario.clicked.connect(self.cargar_generador)
        
        # Conectar el botón de Exportar
        try:
            self.btnExportar.clicked.connect(self.exportar_datos_csv)
        except AttributeError:
            pass

        # Configurar Usuario
        try:
            self.lblUserName.setText("Admin") 
            self.lblUserRole.setText("Administrador")
        except AttributeError:
            pass 

        # Cargar primera página
        self.btnVistaHorario.click()

    # --- GESTIÓN DE PÁGINAS ---

    def limpiar_contenedor(self):
        """Elimina el widget actual del layout principal"""
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
            self.ctrl_gen = GeneradorController(widget, self.db, self)
            self.resaltar_boton(self.btnGenerarHorario)

    def exportar_datos_csv(self):
        """Exporta los datos a CSV"""
        default = os.path.join(os.path.expanduser('~'), 'export_datos.csv')
        path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", default, "CSV Files (*.csv)")
        if not path: return

        try:
            profes = self.db.obtener_profesores()
            modulos = self.db.obtener_modulos()
            prefs = self.db.obtener_preferencias() # Requiere ajustar en db_conexion si no existe sin argumentos
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                writer.writerow(['--- PROFESORES ---'])
                if profes:
                    keys = list(profes[0].keys())
                    writer.writerow(keys)
                    for p in profes: writer.writerow([p.get(k) for k in keys])
                
                writer.writerow([])
                writer.writerow(['--- MODULOS ---'])
                if modulos:
                    keys = list(modulos[0].keys())
                    writer.writerow(keys)
                    for m in modulos: writer.writerow([m.get(k) for k in keys])

            QMessageBox.information(self, 'Exportar', f'Datos guardados en:\n{path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Fallo al exportar:\n{e}')

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