from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView

class GestionDatosController:
    def __init__(self, ui, db):
        self.ui = ui
        self.db = db
        self.datos_cargados = False

    def cargar_datos_iniciales(self):
        if self.datos_cargados:
            return
            
        profesores = self.db.obtener_profesores()
        self.llenar_tabla_profesores(profesores)
        self.datos_cargados = True

    def llenar_tabla_profesores(self, datos):
        tabla = self.ui.tablaProfesores
        headers = ["Nombre", "Apellidos", "Horas Max", "Color"]
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabla.setRowCount(len(datos))
        
        for row, p in enumerate(datos):
            tabla.setItem(row, 0, QTableWidgetItem(p.get('nombre', '')))
            tabla.setItem(row, 1, QTableWidgetItem(p.get('apellidos', '')))
            tabla.setItem(row, 2, QTableWidgetItem(str(p.get('horas_max_semana', ''))))
            tabla.setItem(row, 3, QTableWidgetItem(p.get('color_asignado', '')))