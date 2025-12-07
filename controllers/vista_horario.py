from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QColor

class VistaHorarioController:
    def __init__(self, ui, db, main_window):
        self.ui = ui
        self.db = db
        self.main_window = main_window  # Guardamos la referencia a la ventana principal
        
        # Conectamos el botón de "Crear Horario" (del aviso de lista vacía)
        # Usamos try/except por si el botón aún no existe en el UI para que no falle
        try:
            self.ui.btnIrAGenerador.clicked.connect(self.ir_a_generador)
        except AttributeError:
            print("Aviso: El botón 'btnIrAGenerador' no se encontró en el UI.")

        # Comprobamos si hay datos para decidir qué mostrar
        self.actualizar_vista()

    def actualizar_vista(self):
        """Decide si muestra la tabla o el mensaje de 'No hay datos'"""
        # Asegúrate de haber añadido 'hay_horarios_generados()' en tu db_conexion.py
        try:
            hay_datos = self.db.hay_horarios_generados()
        except AttributeError:
            print("Error: Falta el método 'hay_horarios_generados' en db_conexion.py")
            hay_datos = False
        
        if hay_datos:
            # CASO A: Hay horarios -> Ocultar aviso, Mostrar tabla y cargarla
            try:
                self.ui.frameSinHorario.hide()
                self.ui.tablaHorarioGeneral.show()
                self.cargar_tabla() 
            except AttributeError:
                pass
        else:
            # CASO B: No hay horarios -> Mostrar aviso, Ocultar tabla
            try:
                self.ui.frameSinHorario.show()
                self.ui.tablaHorarioGeneral.hide()
            except AttributeError:
                pass

    def ir_a_generador(self):
        """Redirige a la página del generador (Índice 2 del Stack)"""
        # Simulamos un clic en el botón del menú lateral para cambiar de pestaña
        self.ui.btnGenerarHorario.click()

    def cargar_tabla(self):
        """Configura y rellena la tabla de horarios"""
        tabla = self.ui.tablaHorarioGeneral
        
        # Configurar columnas (Ejemplo básico)
        dias = ["Hora", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        tabla.setColumnCount(len(dias))
        tabla.setHorizontalHeaderLabels(dias)
        
        # Ajustar cabeceras para que se vean bien
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        
        # Rellenar filas con las horas (Ejemplo estático)
        horas = ["08:30", "09:25", "10:20", "11:15 (R)", "11:45", "12:40", "13:35"]
        tabla.setRowCount(len(horas))
        
        for i, hora in enumerate(horas):
            item = QTableWidgetItem(hora)
            item.setBackground(QColor("#151521")) # Color oscuro para la columna de horas
            tabla.setItem(i, 0, item)

        # AQUÍ IRÍA LA LÓGICA FUTURA PARA PINTAR LAS CELDAS CON DATOS DE LA DB
        print("Tabla de horarios configurada.")