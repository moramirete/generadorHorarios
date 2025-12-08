import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic

from database.db_conexion import DatabaseManager

from controllers.vista_horario import VistaHorarioController
from controllers.gestion_datos import GestionDatosController

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'dashboard.ui')
        uic.loadUi(ui_path, self)
        
        self.db = DatabaseManager()
        
        self.ctrl_vista = VistaHorarioController(self, self.db, self)
        self.ctrl_gestion = GestionDatosController(self, self.db)
        
        self.conectar_menu()

    # Metodo para que funcionen los botones en la vista
    def conectar_menu(self):
        
        self.btnVistaHorario.clicked.connect(lambda: self.cambiar_pagina(0, self.btnVistaHorario))
        
        self.btnGestionDatos.clicked.connect(lambda: self.cambiar_pagina(1, self.btnGestionDatos))
        self.btnGestionDatos.clicked.connect(self.ctrl_gestion.cargar_datos_iniciales)
        
        self.btnGenerarHorario.clicked.connect(lambda: self.cambiar_pagina(2, self.btnGenerarHorario))

    # Metodo para cambiar de pestaña cuando hacemos click en los botones.
    def cambiar_pagina(self, indice, boton_emisor):
        
        self.stackedWidget.setCurrentIndex(indice)
        
        self.btnVistaHorario.setChecked(False)
        self.btnGestionDatos.setChecked(False)
        self.btnGenerarHorario.setChecked(False)
        self.btnConflictos.setChecked(False)
        
        boton_emisor.setChecked(True)
# Para que inicie la pantalla
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainApp()
    ventana.show()
    sys.exit(app.exec_())