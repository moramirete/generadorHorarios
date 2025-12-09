import os
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QColorDialog, QAbstractItemView
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5 import uic

class GestionDatosController:
    def __init__(self, ui, db):
        self.ui = ui
        self.db = db
        self.datos_cargados = False

        # --- CONEXIONES BOTONES TABLA ---
        self.ui.btnAddProfe.clicked.connect(self.abrir_crear_profesor)
        self.ui.btnEditProfe.clicked.connect(self.abrir_editar_profesor)
        self.ui.btnDelProfe.clicked.connect(self.eliminar_profesor)

    def cargar_datos_iniciales(self):
        """Se llama al entrar en la pestaña"""
        print("📥 Recargando lista de profesores...")
        profesores = self.db.obtener_profesores()
        self.llenar_tabla_profesores(profesores)
        self.datos_cargados = True

    def llenar_tabla_profesores(self, datos):
        tabla = self.ui.tablaProfesores
        
        # Configurar columnas
        headers = ["ID", "Nombre", "Apellidos", "Horas", "Color"]
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Color

        tabla.setRowCount(len(datos))
        
        for row, p in enumerate(datos):
            tabla.setItem(row, 0, QTableWidgetItem(str(p.get('id_trabajador'))))
            tabla.setItem(row, 1, QTableWidgetItem(p.get('nombre', '')))
            tabla.setItem(row, 2, QTableWidgetItem(p.get('apellidos', '')))
            
            # Horas centradas
            item_horas = QTableWidgetItem(str(p.get('horas_max_semana', 0)))
            item_horas.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(row, 3, item_horas)
            
            # Color visual
            color_hex = p.get('color_asignado', '#ffffff')
            item_color = QTableWidgetItem("")
            item_color.setBackground(QColor(color_hex))
            tabla.setItem(row, 4, item_color)

    # --- GESTIÓN DEL FORMULARIO ---

    def abrir_crear_profesor(self):
        self.mostrar_formulario(modo_edicion=False)

    def abrir_editar_profesor(self):
        filas = self.ui.tablaProfesores.selectionModel().selectedRows()
        if not filas:
            QMessageBox.warning(self.ui, "Aviso", "Selecciona un profesor para editar.")
            return
            
        # Obtener datos de la fila
        idx = filas[0].row()
        id_profesor = self.ui.tablaProfesores.item(idx, 0).text()
        nombre = self.ui.tablaProfesores.item(idx, 1).text()
        apellidos = self.ui.tablaProfesores.item(idx, 2).text()
        horas = self.ui.tablaProfesores.item(idx, 3).text()
        color = self.ui.tablaProfesores.item(idx, 4).background().color().name()

        datos_actuales = {
            "id": id_profesor, "nombre": nombre, "apellidos": apellidos, 
            "horas": int(horas), "color": color
        }
        
        self.mostrar_formulario(modo_edicion=True, datos=datos_actuales)

    def mostrar_formulario(self, modo_edicion, datos=None):
        dialog = QDialog()
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'form_profesor.ui')
        uic.loadUi(ui_path, dialog)
        
        # 1. Cargar Módulos en el ComboBox
        modulos = self.db.obtener_modulos()
        dialog.comboModulos.addItem("Ninguno", None)
        for m in modulos:
            texto = f"{m['nombre_modulo']} ({m['ciclo']})"
            dialog.comboModulos.addItem(texto, m['id_modulo'])

        # 2. Configurar Estado Inicial
        self.color_temporal = datos['color'] if datos else "#3388ff"
        self.preferencias_temporales = []

        if modo_edicion and datos:
            dialog.setWindowTitle(f"Editar: {datos['nombre']}")
            dialog.inputNombre.setText(datos['nombre'])
            dialog.inputApellidos.setText(datos['apellidos'])
            dialog.inputHoras.setValue(datos['horas'])
            
            # Cargar módulo asignado
            id_modulo_actual = self.db.obtener_id_modulo_asignado(datos['id'])
            if id_modulo_actual:
                idx = dialog.comboModulos.findData(id_modulo_actual)
                if idx >= 0: dialog.comboModulos.setCurrentIndex(idx)

            # Cargar preferencias
            self.preferencias_temporales = self.db.obtener_preferencias(datos['id'])
        
        def actualizar_preview_color():
            dialog.frameColorPreview.setStyleSheet(f"background-color: {self.color_temporal}; border: 1px solid white; border-radius: 5px;")
        
        actualizar_preview_color()

        # --- EVENTOS INTERNOS DEL DIÁLOGO ---

        def abrir_paleta():
            color = QColorDialog.getColor(QColor(self.color_temporal), dialog, "Selecciona color")
            if color.isValid():
                self.color_temporal = color.name()
                actualizar_preview_color()

        def abrir_grid_preferencias():
            grid_dialog = QDialog(dialog)
            grid_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'grid_preferencias.ui')
            uic.loadUi(grid_path, grid_dialog)
            
            tabla = grid_dialog.tablaGrid
            dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
            horas = ["08:30", "09:25", "10:20", "11:45", "12:40", "13:35", "14:30"] # Ajusta según tus horas reales
            
            tabla.setColumnCount(len(dias))
            tabla.setRowCount(len(horas))
            tabla.setHorizontalHeaderLabels(dias)
            tabla.setVerticalHeaderLabels(horas)
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tabla.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            # Aquí usamos la corrección del import
            tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)

            # Cargar visualmente
            matriz_estados = {} 
            for pref in self.preferencias_temporales:
                try:
                    dia_limpio = pref['dia_semana'].replace("MIERCOLES", "MIÉRCOLES")
                    if dia_limpio in dias:
                        c = dias.index(dia_limpio)
                        r = pref['franja_horaria'] - 1
                        key = f"{r}_{c}"
                        nivel = pref['nivel_prioridad']
                        matriz_estados[key] = nivel
                        
                        color = QColor("#f87171") if nivel == 1 else QColor("#facc15")
                        item = QTableWidgetItem("")
                        item.setBackground(color)
                        tabla.setItem(r, c, item)
                except Exception: pass

            def celda_clicada(row, col):
                key = f"{row}_{col}"
                estado = matriz_estados.get(key, 0)
                # 0->2->1->0
                nuevo = 2 if estado == 0 else (1 if estado == 2 else 0)
                matriz_estados[key] = nuevo
                
                color = QColor(0,0,0,0)
                if nuevo == 2: color = QColor("#facc15")
                elif nuevo == 1: color = QColor("#f87171")
                
                if tabla.item(row, col) is None: tabla.setItem(row, col, QTableWidgetItem(""))
                tabla.item(row, col).setBackground(color)
                tabla.clearSelection()

            tabla.cellClicked.connect(celda_clicada)

            def guardar_grid():
                self.preferencias_temporales = []
                for key, nivel in matriz_estados.items():
                    if nivel == 0: continue
                    r, c = map(int, key.split('_'))
                    dia_bd = dias[c].replace("MIÉRCOLES", "MIERCOLES")
                    self.preferencias_temporales.append({
                        "dia_semana": dia_bd,
                        "franja_horaria": r + 1,
                        "nivel_prioridad": nivel,
                        "tipo_restriccion": "BLOQUEO" if nivel == 1 else "PREFERENCIA"
                    })
                grid_dialog.accept()

            grid_dialog.btnAceptar.clicked.connect(guardar_grid)
            grid_dialog.exec_()

        def guardar_todo():
            nombre = dialog.inputNombre.text()
            if not nombre:
                QMessageBox.warning(dialog, "Error", "Nombre obligatorio")
                return

            payload = {
                "nombre": nombre,
                "apellidos": dialog.inputApellidos.text(),
                "horas_max_semana": dialog.inputHoras.value(),
                "color_asignado": self.color_temporal
            }

            profe_guardado = None
            if modo_edicion:
                if self.db.actualizar_profesor(datos['id'], payload):
                    profe_guardado = {'id_trabajador': datos['id']}
            else:
                profe_guardado = self.db.crear_profesor(payload)

            if profe_guardado:
                id_profe = profe_guardado.get('id_trabajador')
                
                # Guardar Módulo Asignado
                id_modulo = dialog.comboModulos.currentData()
                self.db.guardar_asignacion_modulo(id_profe, id_modulo)

                # Guardar Preferencias
                for p in self.preferencias_temporales:
                    p['id_trabajador'] = id_profe
                self.db.guardar_preferencias(id_profe, self.preferencias_temporales)
                
                dialog.accept()
                self.cargar_datos_iniciales()
            else:
                QMessageBox.critical(dialog, "Error", "Error al guardar en BD")

        # Conectar botones
        dialog.btnColorPicker.clicked.connect(abrir_paleta)
        dialog.btnPreferencias.clicked.connect(abrir_grid_preferencias)
        dialog.btnGuardar.clicked.connect(guardar_todo)
        dialog.btnCancelar.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def eliminar_profesor(self):
        filas = self.ui.tablaProfesores.selectionModel().selectedRows()
        if not filas:
            return
        idx = filas[0].row()
        id_p = self.ui.tablaProfesores.item(idx, 0).text()
        nombre = self.ui.tablaProfesores.item(idx, 1).text()

        if QMessageBox.question(self.ui, "Confirmar", f"¿Eliminar a {nombre}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            if self.db.eliminar_profesor(id_p):
                self.cargar_datos_iniciales()