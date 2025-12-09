import sys
import os
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QFileDialog
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

        # Conectar exportar CSV si existe el botón
        if hasattr(self, 'btnExportar'):
            try:
                self.btnExportar.clicked.connect(self.exportar_datos_csv)
            except Exception as e:
                print(f"Aviso: no se pudo conectar 'btnExportar': {e}")

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
        QMessageBox.information(
            self, 
            "Exportar Datos", 
            "¡Exportación a CSV iniciada!\n\nSe generará un archivo con los datos actuales."
        )

    def exportar_datos_csv(self):
        """Exporta profesores, módulos y preferencias a un único CSV con secciones."""
        default = os.path.join(os.path.expanduser('~'), 'exportar_datos.csv')
        path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", default, "CSV Files (*.csv)")
        if not path:
            return

        try:
            profes = self.db.obtener_profesores()
        except Exception:
            profes = []

        try:
            modulos = self.db.obtener_modulos()
        except Exception:
            modulos = []

        try:
            prefs = self.db.obtener_preferencias()
        except Exception:
            prefs = []

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Profesores
                writer.writerow(['# Profesores'])
                if profes:
                    keys = sorted({k for d in profes for k in d.keys()})
                    writer.writerow(['tipo'] + keys)
                    for p in profes:
                        row = ['profesor'] + [p.get(k, '') for k in keys]
                        writer.writerow(row)
                else:
                    writer.writerow(['(sin datos)'])

                writer.writerow([])

                # Módulos
                writer.writerow(['# Modulos'])
                if modulos:
                    keys = sorted({k for d in modulos for k in d.keys()})
                    writer.writerow(['tipo'] + keys)
                    for m in modulos:
                        row = ['modulo'] + [m.get(k, '') for k in keys]
                        writer.writerow(row)
                else:
                    writer.writerow(['(sin datos)'])

                writer.writerow([])

                # Preferencias: por profesor -> filas con Nombre,Apellidos,Dia,Hora,Nivel,Color
                writer.writerow(['# Preferencias'])
                horas = ["08:30", "09:25", "10:20", "11:45", "12:40", "13:35", "14:30"]
                dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
                writer.writerow(['Profesor', 'Apellidos', 'Dia', 'Hora', 'Nivel', 'Color'])
                any_pref = False
                for p in profes:
                    pid = p.get('id_trabajador') or p.get('id')
                    nombre = p.get('nombre', '')
                    apellidos = p.get('apellidos', '')
                    if not pid:
                        continue
                    try:
                        pref_list = self.db.obtener_preferencias(pid)
                    except Exception:
                        pref_list = []

                    for pref in pref_list:
                        try:
                            d = pref.get('dia_semana', '').replace('MIÉRCOLES', 'MIERCOLES')
                            fr = int(pref.get('franja_horaria', 0)) - 1
                            nivel = int(pref.get('nivel_prioridad', 0))
                            if d not in dias or fr < 0 or fr >= len(horas):
                                continue
                            hora_txt = horas[fr]
                            color = '#f87171' if nivel == 1 else ('#facc15' if nivel == 2 else '')
                            writer.writerow([nombre, apellidos, d, hora_txt, nivel, color])
                            any_pref = True
                        except Exception:
                            continue

                if not any_pref:
                    writer.writerow(['(sin preferencias guardadas)'])

            QMessageBox.information(self, 'Exportar CSV', f'Datos exportados en:\n{path}')
        except Exception as e:
            QMessageBox.critical(self, 'Exportar CSV', f'Error al exportar CSV:\n{e}')

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