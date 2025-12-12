from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QColor

class VistaHorarioController:
    def __init__(self, ui, db, main_window):
        self.ui = ui
        self.db = db
        self.main_window = main_window
        self.ciclo_actual = None

        self.configurar_tabla()
        self.cargar_ciclos()
        
        # Conectar botón del aviso
        try:
            self.ui.btnIrAGenerador.clicked.connect(self.ir_a_generador)
        except AttributeError:
            pass
        
        # Conectar botón borrar horario
        try:
            self.ui.btnBorrarHorario.clicked.connect(self.borrar_horario_actual)
        except AttributeError:
            pass
        
        # Conectar combo de filtro y modo
        try:
            self.ui.comboFiltro.currentTextChanged.connect(self.on_cambiar_filtro)
        except AttributeError:
            pass
        try:
            self.ui.comboModo.currentIndexChanged.connect(self.on_cambiar_modo)
        except AttributeError:
            pass

        self.actualizar_vista()

        
    def cargar_ciclos(self):
        """Carga los ciclos disponibles en el combobox"""
        try:
            combo = self.ui.comboFiltro
            ciclos, _ = self.db.obtener_listados_vista()
            combo.clear()
            combo.addItem("- Seleccionar -")
            for c in ciclos:
                combo.addItem(c)
        except AttributeError:
            pass

    def on_cambiar_ciclo(self):
        """Se ejecuta cuando se cambia el ciclo seleccionado"""
        try:
            ciclo = self.ui.comboFiltro.currentText()
            if ciclo and ciclo != "- Seleccionar -":
                self.ciclo_actual = ciclo
                self.rellenar_horario(ciclo)
            else:
                self.limpiar_tabla()
        except Exception as e:
            print(f"Error al cambiar ciclo: {e}")

    def on_cambiar_filtro(self, *args):
        # Alias para compatibilidad con nombre anterior
        self.on_cambiar_ciclo()

    def on_cambiar_modo(self, idx):
        # Ajustar etiqueta del filtro según el modo (CLASE/PROFESOR)
        try:
            if idx == 0:  # Clase
                # rellenar ciclos
                self.cargar_ciclos()
            else:
                # Modo Profesor: cargar lista de profesores en comboFiltro
                combo = self.ui.comboFiltro
                _, profes = self.db.obtener_listados_vista()
                combo.clear()
                combo.addItem("- Seleccionar -")
                for p in profes:
                    combo.addItem(p)
            # limpiar vista al cambiar modo
            self.limpiar_tabla()
        except Exception as e:
            print(f"Error al cambiar modo: {e}")

    def actualizar_vista(self):
        try:
            hay_datos = self.db.hay_horarios_generados()
        except AttributeError:
            hay_datos = False

        if hay_datos:
            self.ui.stackContenido.setCurrentIndex(1)  # Página Tabla
        else:
            self.ui.stackContenido.setCurrentIndex(0)  # Página Aviso

    def ir_a_generador(self):
        self.main_window.cargar_generador()

    def configurar_tabla(self):
        tabla = self.ui.tablaHorarioGeneral
        columnas = ["HORA", "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        filas = ["08:30 - 09:25", "09:25 - 10:20", "10:20 - 11:15", "11:15 - 11:45 (R)", "11:45 - 12:40", "12:40 - 13:35"]
        
        tabla.setColumnCount(len(columnas))
        tabla.setRowCount(len(filas))
        tabla.setHorizontalHeaderLabels(columnas)
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Columna de horas
        
        # Inicializar todas las celdas vacías
        for i in range(len(filas)):
            # Columna de horas
            item = QTableWidgetItem(filas[i])
            item.setBackground(QColor("#0f172a"))
            item.setForeground(QColor("#94a3b8"))
            item.setTextAlignment(0x0084)
            tabla.setItem(i, 0, item)
            
            # Celdas de horario
            for j in range(1, len(columnas)):
                celda = QTableWidgetItem("")
                celda.setBackground(QColor("#1e293b"))
                tabla.setItem(i, j, celda)

    # Metodo para rellenar el horario cunado seleccionamos el modulo o los profesores
    def rellenar_horario(self, ciclo):
        
        try:
            tabla = self.ui.tablaHorarioGeneral
            
            # Mapeo de días a columnas
            dias_map = {
                "LUNES": 1,
                "MARTES": 2,
                "MIERCOLES": 3,
                "MIÉRCOLES": 3,
                "JUEVES": 4,
                "VIERNES": 5
            }
            
            # Determinar el modo (CLASE o PROFESOR)
            modo = "PROFESOR" if self.ui.comboModo.currentIndex() == 1 else "CLASE"
            
            # Obtener datos del horario
            datos = self.db.obtener_horario_filtrado(modo, ciclo)
            
            # Limpiar primero
            self.limpiar_tabla()
            
            # Rellenar celdas con los datos
            for d in datos:
                col = dias_map.get(d['dia'].upper().replace("É", "E"))
                fila = d['hora'] - 1  # Las franjas son 1-6, las filas son 0-5
                
                if col and 0 <= fila < tabla.rowCount():
                    celda = tabla.item(fila, col)
                    if celda is None:
                        celda = QTableWidgetItem()
                        tabla.setItem(fila, col, celda)
                    
                    # Establecer contenido
                    celda.setText(f"{d['texto1']}\n{d['texto2']}")
                    
                    # Aplicar color
                    color_hex = d['color'] if d['color'].startswith('#') else '#333'
                    celda.setBackground(QColor(color_hex))
                    celda.setForeground(QColor("#ffffff"))
                    
                    # Alineación
                    celda.setTextAlignment(0x0084)  # Centro
                    
            # Si hay datos, mostrar la página de la tabla, si no, mostrar aviso
            if datos:
                self.ui.stackContenido.setCurrentIndex(1)
            else:
                self.ui.stackContenido.setCurrentIndex(0)
                
        except Exception as e:
            print(f"Error rellenando horario: {e}")

    # Metodo para pintar las celdas de los profesores con sus colores asignados
    def pintar_leyenda_profesores(self, datos):
        """Pinta una leyenda de profesores con sus colores debajo de la tabla"""
        try:
            # Obtener profesores únicos de los datos
            profesores_unicos = {}
            for d in datos:
                nombre = d['texto2']  # "Nombre Profesor"
                color = d['color']
                if nombre and nombre not in profesores_unicos:
                    profesores_unicos[nombre] = color
            
            # Buscar o crear el layout de leyenda
            layout_padre = self.ui.lTabla if hasattr(self.ui, 'lTabla') else None
            if not layout_padre:
                print("Error: no se encontró lTabla")
                return
            
            # Buscar si existe frame de leyenda
            frame_leyenda = None
            for i in range(layout_padre.count()):
                item = layout_padre.itemAt(i)
                if item and hasattr(item, 'widget'):
                    w = item.widget()
                    if hasattr(w, 'objectName') and w.objectName() == 'frameLeyenda':
                        frame_leyenda = w
                        break
            
            # Si no existe, crearlo
            if not frame_leyenda:
                from PyQt5.QtWidgets import QFrame, QHBoxLayout
                frame_leyenda = QFrame()
                frame_leyenda.setObjectName('frameLeyenda')
                frame_leyenda.setStyleSheet("background-color: #334155; border-radius: 8px; padding: 15px; margin: 15px;")
                frame_leyenda.setMaximumHeight(70)
                h_layout = QHBoxLayout()
                h_layout.setContentsMargins(15, 10, 15, 10)
                frame_leyenda.setLayout(h_layout)
                layout_padre.addStretch()
                layout_padre.addWidget(frame_leyenda)
            else:
                # Limpiar widgets anteriores
                layout_leyenda = frame_leyenda.layout()
                while layout_leyenda.count():
                    item = layout_leyenda.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            
            # Obtener layout y agregar etiqueta "Profesores:"
            from PyQt5.QtWidgets import QLabel, QSpacerItem, QSizePolicy
            layout_leyenda = frame_leyenda.layout()
            lbl_titulo = QLabel("Profesores:")
            lbl_titulo.setStyleSheet("font-weight: bold; color: #cbd5e1; margin-right: 20px;")
            layout_leyenda.addWidget(lbl_titulo)
            
            # Agregar profesores con sus colores
            for nombre, color in profesores_unicos.items():
                lbl = QLabel(f"■ {nombre}")
                color_hex = color if color.startswith('#') else '#333'
                lbl.setStyleSheet(f"color: {color_hex}; font-weight: bold; margin-right: 15px;")
                layout_leyenda.addWidget(lbl)
            
            # Espaciador al final
            spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            layout_leyenda.addItem(spacer)
            
        except Exception as e:
            print(f"Error pintando leyenda: {e}")

    # Metodo para limpiar la tabla
    def limpiar_tabla(self):
        """Limpia el contenido de la tabla (excepto la columna de horas)"""
        tabla = self.ui.tablaHorarioGeneral
        for i in range(tabla.rowCount()):
            for j in range(1, tabla.columnCount()):
                celda = tabla.item(i, j)
                if celda:
                    celda.setText("")
                    celda.setBackground(QColor("#1e293b"))

    # Se elimina el horario de la base de datos y se limpia la tabla
    def borrar_horario_actual(self):
        """Elimina el horario de la base de datos y limpia la tabla"""
        if self.ciclo_actual:
            self.db.borrar_horario_por_ciclo(self.ciclo_actual)
            self.limpiar_tabla()
