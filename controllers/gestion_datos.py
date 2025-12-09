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

        # --- CONEXIONES PROFESORES ---
        self.ui.btnAddProfe.clicked.connect(self.abrir_crear_profesor)
        self.ui.btnEditProfe.clicked.connect(self.abrir_editar_profesor)
        self.ui.btnDelProfe.clicked.connect(self.eliminar_profesor)

        # --- CONEXIONES MÓDULOS (NUEVO) ---
        self.ui.btnAddModulo.clicked.connect(self.abrir_crear_modulo)
        self.ui.btnEditModulo.clicked.connect(self.abrir_editar_modulo)
        self.ui.btnDelModulo.clicked.connect(self.eliminar_modulo)

    def cargar_datos_iniciales(self):
        """Carga ambas tablas al entrar"""
        print("📥 Recargando datos...")
        
        # 1. Cargar Profesores
        profesores = self.db.obtener_profesores()
        self.llenar_tabla_profesores(profesores)
        
        # 2. Cargar Módulos (NUEVO)
        modulos = self.db.obtener_modulos()
        self.llenar_tabla_modulos(modulos)
        
        self.datos_cargados = True

    # ==========================
    # SECCIÓN PROFESORES
    # ==========================
    def llenar_tabla_profesores(self, datos):
        tabla = self.ui.tablaProfesores
        headers = ["ID", "Nombre", "Apellidos", "Horas", "Color"]
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        tabla.setRowCount(len(datos))
        for row, p in enumerate(datos):
            tabla.setItem(row, 0, QTableWidgetItem(str(p.get('id_trabajador'))))
            tabla.setItem(row, 1, QTableWidgetItem(p.get('nombre', '')))
            tabla.setItem(row, 2, QTableWidgetItem(p.get('apellidos', '')))
            item_h = QTableWidgetItem(str(p.get('horas_max_semana', 0)))
            item_h.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(row, 3, item_h)
            
            color_hex = p.get('color_asignado', '#ffffff')
            item_c = QTableWidgetItem("")
            item_c.setBackground(QColor(color_hex))
            tabla.setItem(row, 4, item_c)

    def abrir_crear_profesor(self):
        self.mostrar_formulario_profe(False)

    def abrir_editar_profesor(self):
        filas = self.ui.tablaProfesores.selectionModel().selectedRows()
        if not filas:
            QMessageBox.warning(self.ui, "Aviso", "Selecciona un profesor.")
            return
        
        idx = filas[0].row()
        # Recuperamos datos de la tabla (o idealmente de la DB)
        id_p = self.ui.tablaProfesores.item(idx, 0).text()
        nom = self.ui.tablaProfesores.item(idx, 1).text()
        ape = self.ui.tablaProfesores.item(idx, 2).text()
        hrs = self.ui.tablaProfesores.item(idx, 3).text()
        col = self.ui.tablaProfesores.item(idx, 4).background().color().name()
        
        datos = {"id": id_p, "nombre": nom, "apellidos": ape, "horas": int(hrs), "color": col}
        self.mostrar_formulario_profe(True, datos)

    def mostrar_formulario_profe(self, modo_edicion, datos=None):
        dialog = QDialog()
        uic.loadUi(os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'form_profesor.ui'), dialog)
        
        # Cargar Combo Módulos
        modulos = self.db.obtener_modulos()
        dialog.comboModulos.addItem("Ninguno", None)
        for m in modulos:
            dialog.comboModulos.addItem(f"{m['nombre_modulo']} ({m['ciclo']})", m['id_modulo'])

        self.color_temporal = datos['color'] if datos else "#3388ff"
        self.preferencias_temporales = []

        if modo_edicion and datos:
            dialog.setWindowTitle(f"Editar: {datos['nombre']}")
            dialog.inputNombre.setText(datos['nombre'])
            dialog.inputApellidos.setText(datos['apellidos'])
            dialog.inputHoras.setValue(datos['horas'])
            
            id_mod_actual = self.db.obtener_id_modulo_asignado(datos['id'])
            if id_mod_actual:
                idx = dialog.comboModulos.findData(id_mod_actual)
                if idx >= 0: dialog.comboModulos.setCurrentIndex(idx)
            
            self.preferencias_temporales = self.db.obtener_preferencias(datos['id'])

        def update_preview():
            dialog.frameColorPreview.setStyleSheet(f"background-color: {self.color_temporal}; border: 1px solid white; border-radius: 5px;")
        update_preview()

        def abrir_paleta():
            c = QColorDialog.getColor(QColor(self.color_temporal), dialog)
            if c.isValid():
                self.color_temporal = c.name()
                update_preview()

        def abrir_grid():
            grid = QDialog(dialog)
            uic.loadUi(os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'grid_preferencias.ui'), grid)
            
            dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
            horas = ["08:30", "09:25", "10:20", "11:45", "12:40", "13:35", "14:30"]
            
            grid.tablaGrid.setColumnCount(len(dias))
            grid.tablaGrid.setRowCount(len(horas))
            grid.tablaGrid.setHorizontalHeaderLabels(dias)
            grid.tablaGrid.setVerticalHeaderLabels(horas)
            grid.tablaGrid.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            grid.tablaGrid.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            grid.tablaGrid.setEditTriggers(QAbstractItemView.NoEditTriggers)

            matriz = {}
            for p in self.preferencias_temporales:
                try:
                    d_bd = p['dia_semana'].replace("MIÉRCOLES", "MIERCOLES")
                    if d_bd in dias:
                        c, r = dias.index(d_bd), p['franja_horaria'] - 1
                        nivel = p['nivel_prioridad']
                        matriz[f"{r}_{c}"] = nivel
                        col = QColor("#f87171") if nivel==1 else QColor("#facc15")
                        item = QTableWidgetItem("")
                        item.setBackground(col)
                        grid.tablaGrid.setItem(r, c, item)
                except: pass

            def celda_clic(r, c):
                k = f"{r}_{c}"
                st = matriz.get(k, 0)
                nxt = 2 if st==0 else (1 if st==2 else 0)
                matriz[k] = nxt
                col = QColor(0,0,0,0)
                if nxt==2: col = QColor("#facc15")
                elif nxt==1: col = QColor("#f87171")
                
                if not grid.tablaGrid.item(r, c): grid.tablaGrid.setItem(r, c, QTableWidgetItem(""))
                grid.tablaGrid.item(r, c).setBackground(col)
                grid.tablaGrid.clearSelection()

            grid.tablaGrid.cellClicked.connect(celda_clic)

            def save_grid():
                self.preferencias_temporales = []
                for k, v in matriz.items():
                    if v==0: continue
                    r, c = map(int, k.split('_'))
                    self.preferencias_temporales.append({
                        "dia_semana": dias[c], "franja_horaria": r+1,
                        "nivel_prioridad": v, "tipo_restriccion": "BLOQUEO" if v==1 else "PREFERENCIA"
                    })
                grid.accept()
            
            grid.btnAceptar.clicked.connect(save_grid)
            grid.exec_()

        def guardar():
            nom = dialog.inputNombre.text()
            if not nom: return QMessageBox.warning(dialog, "Error", "Nombre obligatorio")
            
            payload = {
                "nombre": nom, "apellidos": dialog.inputApellidos.text(),
                "horas_max_semana": dialog.inputHoras.value(), "color_asignado": self.color_temporal
            }
            
            res = None
            if modo_edicion:
                if self.db.actualizar_profesor(datos['id'], payload): res = {'id_trabajador': datos['id']}
            else:
                res = self.db.crear_profesor(payload)
            
            if res:
                pid = res.get('id_trabajador')
                self.db.guardar_asignacion_modulo(pid, dialog.comboModulos.currentData())
                for p in self.preferencias_temporales: p['id_trabajador'] = pid
                self.db.guardar_preferencias(pid, self.preferencias_temporales)
                dialog.accept()
                self.cargar_datos_iniciales()
            else:
                QMessageBox.critical(dialog, "Error", "Error BD")

        dialog.btnColorPicker.clicked.connect(abrir_paleta)
        dialog.btnPreferencias.clicked.connect(abrir_grid)
        dialog.btnGuardar.clicked.connect(guardar)
        dialog.btnCancelar.clicked.connect(dialog.reject)
        dialog.exec_()

    def eliminar_profesor(self):
        filas = self.ui.tablaProfesores.selectionModel().selectedRows()
        if not filas: return
        idx = filas[0].row()
        id_p = self.ui.tablaProfesores.item(idx, 0).text()
        if QMessageBox.question(self.ui, "Borrar", "¿Eliminar profesor?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.db.eliminar_profesor(id_p)
            self.cargar_datos_iniciales()

    # ==========================
    # SECCIÓN MÓDULOS (NUEVO)
    # ==========================

    def llenar_tabla_modulos(self, datos):
        tabla = self.ui.tablaModulos
        # Columnas: ID, Nombre, Ciclo, Curso, Horas S/D
        headers = ["ID", "Módulo", "Ciclo", "Curso", "Horas (Sem/Día)"]
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID peq

        tabla.setRowCount(len(datos))
        for row, m in enumerate(datos):
            tabla.setItem(row, 0, QTableWidgetItem(str(m.get('id_modulo'))))
            tabla.setItem(row, 1, QTableWidgetItem(m.get('nombre_modulo', '')))
            tabla.setItem(row, 2, QTableWidgetItem(m.get('ciclo', '')))
            
            item_curso = QTableWidgetItem(str(m.get('curso', 1)))
            item_curso.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(row, 3, item_curso)
            
            # Formato "4 / 2" (Semana / Dia)
            txt_horas = f"{m.get('horas_totales_semanales', 0)} / {m.get('horas_max_dia', 0)}"
            item_h = QTableWidgetItem(txt_horas)
            item_h.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(row, 4, item_h)

    def abrir_crear_modulo(self):
        self.mostrar_formulario_modulo(False)

    def abrir_editar_modulo(self):
        filas = self.ui.tablaModulos.selectionModel().selectedRows()
        if not filas:
            QMessageBox.warning(self.ui, "Aviso", "Selecciona un módulo.")
            return
        
        idx = filas[0].row()
        id_m = self.ui.tablaModulos.item(idx, 0).text()
        nom = self.ui.tablaModulos.item(idx, 1).text()
        ciclo = self.ui.tablaModulos.item(idx, 2).text()
        curso = self.ui.tablaModulos.item(idx, 3).text()
        
        # Las horas están combinadas "4 / 2", hay que separarlas
        horas_txt = self.ui.tablaModulos.item(idx, 4).text()
        h_sem, h_dia = map(int, horas_txt.split(' / '))

        datos = {
            "id": id_m, "nombre": nom, "ciclo": ciclo, 
            "curso": int(curso), "h_sem": h_sem, "h_dia": h_dia
        }
        self.mostrar_formulario_modulo(True, datos)

    def mostrar_formulario_modulo(self, modo_edicion, datos=None):
        dialog = QDialog()
        uic.loadUi(os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'form_modulo.ui'), dialog)
        
        if modo_edicion and datos:
            dialog.setWindowTitle(f"Editar: {datos['nombre']}")
            dialog.inputNombreModulo.setText(datos['nombre'])
            dialog.inputCiclo.setText(datos['ciclo'])
            dialog.inputCurso.setValue(datos['curso'])
            dialog.inputHorasSem.setValue(datos['h_sem'])
            dialog.inputHorasDia.setValue(datos['h_dia'])

        def guardar():
            nom = dialog.inputNombreModulo.text()
            cic = dialog.inputCiclo.text()
            if not nom or not cic:
                return QMessageBox.warning(dialog, "Error", "Nombre y Ciclo son obligatorios")

            payload = {
                "nombre_modulo": nom,
                "ciclo": cic,
                "curso": dialog.inputCurso.value(),
                "horas_totales_semanales": dialog.inputHorasSem.value(),
                "horas_max_dia": dialog.inputHorasDia.value()
            }

            ok = False
            if modo_edicion:
                ok = self.db.actualizar_modulo(datos['id'], payload)
            else:
                ok = self.db.crear_modulo(payload)

            if ok:
                dialog.accept()
                self.cargar_datos_iniciales()
            else:
                QMessageBox.critical(dialog, "Error", "Error al guardar módulo en BD")

        dialog.btnGuardar.clicked.connect(guardar)
        dialog.btnCancelar.clicked.connect(dialog.reject)
        dialog.exec_()

    def eliminar_modulo(self):
        filas = self.ui.tablaModulos.selectionModel().selectedRows()
        if not filas: return
        idx = filas[0].row()
        id_m = self.ui.tablaModulos.item(idx, 0).text()
        
        if QMessageBox.question(self.ui, "Borrar", "¿Eliminar módulo?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            if self.db.eliminar_modulo(id_m):
                self.cargar_datos_iniciales()