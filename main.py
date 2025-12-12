import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QFileDialog
from PyQt5 import uic

try:
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill
except ImportError:
    class Workbook: pass
    class PatternFill:
        def __init__(self, *args, **kwargs): pass
    print("ADVERTENCIA: La librería 'openpyxl' no está instalada. El exportador XLSX no funcionará.")

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
        
        # 1. Cargar la parte de la Izquierda que siempre se mantiene.  Los botones principales(VISTA GENERAL, GENERAR HORARIO, AJUSTAR PROFESORES Y MODULOS, EXPORTAR CSV)
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'main_shell.ui')
        uic.loadUi(ui_path, self)
        
        # 2. Iniciar Base de Datos
        print("Iniciando sistema...")
        self.db = DatabaseManager()
        
        # 3. Conectar Botones del Menú Lateral
        self.btnVistaHorario.clicked.connect(self.cargar_vista_horario)
        self.btnGestionDatos.clicked.connect(self.cargar_gestion_datos)
        self.btnGenerarHorario.clicked.connect(self.cargar_generador)
        self.btnExportar.clicked.connect(self.exportar_xlsx)
        
        self.cargar_vista_horario()
        
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

# Metodo para cargar el ui dentro de la pagina
    def cargar_ui_pagina(self, nombre_archivo):
        
        self.limpiar_contenedor()
        
        path = os.path.join(os.path.dirname(__file__), 'ui', 'pages', nombre_archivo)
        try:
            nuevo_widget = uic.loadUi(path)
            self.layout_contenedor.addWidget(nuevo_widget)
            return nuevo_widget
        except FileNotFoundError:
            print(f"No se pudo encontrar el archivo: {nombre_archivo}")
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

        # Metodo para exportae datos al csv.
    # main.py (dentro de la clase MainApp)

    def exportar_xlsx(self):
        """
        Exporta los datos de gestión (profesores, módulos, preferencias) y 
        el horario completo a un único archivo XLSX, en hojas separadas, con colores.
        """
        if not self.db:
            QMessageBox.critical(self, "Error", "La conexión a la base de datos no está disponible.")
            return
            
        if 'Workbook' not in globals() or not isinstance(Workbook, type):
            QMessageBox.critical(self, "Error", "No se encontró la librería 'openpyxl'. Por favor, instálala con: pip install openpyxl")
            return

        # 1. Solicitar la ruta de guardado
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Horario", "datos_horario", "Archivos Excel (*.xlsx)")
        if not path:
            return
        
        if not path.lower().endswith('.xlsx'):
            path += '.xlsx'

        try:
            # Crear un nuevo libro de trabajo de OpenPyXL
            wb = Workbook()
            
            # --- HOJA 1: DATOS DE GESTIÓN (Generar Horario) ---
            ws_gestion = wb.active 
            ws_gestion.title = "Datos de Gestion"

            profes = self.db.obtener_profesores()
            modulos = self.db.obtener_modulos()
            prefs = self.db.obtener_todas_preferencias()
            
            # --- PROFESORES Y COLORES ---
            ws_gestion.append(["--- PROFESORES Y COLORES (GENERAR HORARIO) ---"])
            if profes:
                # Cabeceras
                keys = list(profes[0].keys())
                ws_gestion.append([k.replace('_', ' ').title() for k in keys])
                
                for p in profes:
                    row_data = [p.get(k) for k in keys]
                    ws_gestion.append(row_data)
                    
                    # Colorear la fila
                    color_hex = p.get('color_asignado')
                    if color_hex and len(color_hex) == 7 and color_hex.startswith('#'):
                        try:
                            # Creamos un relleno con el color del profesor
                            fill = PatternFill(start_color=color_hex[1:], end_color=color_hex[1:], fill_type="solid")
                            # Coloreamos las celdas de la fila recién añadida
                            for cell in ws_gestion[ws_gestion.max_row]:
                                cell.fill = fill
                        except Exception as e:
                            # Ignorar si hay un color inválido
                            pass
                            
            # --- MÓDULOS ---
            ws_gestion.append([])
            ws_gestion.append(["--- MÓDULOS ---"])
            if modulos:
                keys = list(modulos[0].keys())
                ws_gestion.append([k.replace('_', ' ').title() for k in keys])
                for m in modulos:
                    ws_gestion.append([m.get(k) for k in keys])

            # --- PREFERENCIAS ---
            ws_gestion.append([])
            ws_gestion.append(["--- PREFERENCIAS Y BLOQUEOS ---"])
            if prefs:
                keys = list(prefs[0].keys())
                ws_gestion.append([k.replace('_', ' ').title() for k in keys])
                for pr in prefs:
                    ws_gestion.append([pr.get(k) for k in keys])
                    
            # --- HOJA 2: VISTA HORARIO COMPLETO ---
            ws_horario = wb.create_sheet(title="Horario Completo")
            horario_datos = self.db.obtener_horario_completo_para_exportar()
            
            if horario_datos:
                # Usamos las claves del diccionario como encabezados
                keys = list(horario_datos[0].keys())
                ws_horario.append(keys)
                
                # Obtener el índice de la columna 'Nombre Módulo' para colorear
                nombre_modulo_col_idx = keys.index('Nombre Módulo') + 1 
                
                for h in horario_datos:
                    row_data = [h.get(k) for k in keys]
                    ws_horario.append(row_data)
                    
                    # Colorear la celda del Módulo/Profesor con el color asignado
                    color_hex = h.get('Color Asignado')
                    
                    if color_hex and len(color_hex) == 7 and color_hex.startswith('#'):
                        try:
                            fill = PatternFill(start_color=color_hex[1:], end_color=color_hex[1:], fill_type="solid")
                            # Coloreamos la columna 'Nombre Módulo' de la fila actual
                            ws_horario.cell(row=ws_horario.max_row, column=nombre_modulo_col_idx).fill = fill
                        except Exception as e:
                            # Ignorar si hay un color inválido
                            pass
            
            # Eliminar la hoja de trabajo por defecto (Sheet) si se creó
            if 'Sheet' in wb.sheetnames:
                del wb['Sheet']
                
            # Guardar el archivo
            wb.save(path)

            QMessageBox.information(self, "Exportar", f"Datos guardados correctamente en:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al exportar: {e}.\n¡Asegúrate de haber instalado 'openpyxl'!")

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