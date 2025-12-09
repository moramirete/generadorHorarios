from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QColor

class VistaHorarioController:
    def __init__(self, ui, db, main_window):
        self.ui = ui
        self.db = db
        self.main_window = main_window

        self.configurar_tabla()
        
        # Conectar botón del aviso
        try:
            self.ui.btnIrAGenerador.clicked.connect(self.ir_a_generador)
        except AttributeError:
            pass

        self.actualizar_vista()

    def actualizar_vista(self):
        try:
            hay_datos = self.db.hay_horarios_generados()
            # hay_datos = True  # <--- DESCOMENTAR PARA VER LA TABLA SIEMPRE
        except AttributeError:
            hay_datos = False

        if hay_datos:
            self.ui.stackContenido.setCurrentIndex(1) # Página Tabla
        else:
            self.ui.stackContenido.setCurrentIndex(0) # Página Aviso

    def ir_a_generador(self):
        self.main_window.cargar_generador()

    def configurar_tabla(self):
        tabla = self.ui.tablaHorarioGeneral
        columnas = ["HORA", "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        filas = ["08:30", "09:25", "10:20", "11:15 (R)", "11:45", "12:40", "13:35"]
        
        tabla.setColumnCount(len(columnas))
        tabla.setRowCount(len(filas))
        tabla.setHorizontalHeaderLabels(columnas)
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        for i, hora in enumerate(filas):
            item = QTableWidgetItem(hora)
            item.setBackground(QColor("#0f172a"))
            item.setForeground(QColor("#94a3b8"))
            item.setTextAlignment(0x0084)
            tabla.setItem(i, 0, item)