import os
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QColorDialog, QAbstractItemView, QListWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5 import uic

class GestionDatosController:
    def __init__(self, ui, db):
        self.ui = ui
        self.db = db
        self.datos_cargados = False

        # --- CONEXIONES DE BOTONES (PROFESORES) ---
        self.ui.btnAddProfe.clicked.connect(self.abrir_crear_profesor)
        self.ui.btnEditProfe.clicked.connect(self.abrir_editar_profesor)
        self.ui.btnDelProfe.clicked.connect(self.eliminar_profesor)

        # --- CONEXIONES DE BOTONES (MÓDULOS) ---
        self.ui.btnAddModulo.clicked.connect(self.abrir_crear_modulo)
        self.ui.btnEditModulo.clicked.connect(self.abrir_editar_modulo)
        self.ui.btnDelModulo.clicked.connect(self.eliminar_modulo)

    def cargar_datos_iniciales(self):
        """Carga ambas tablas al entrar en la pestaña"""
        print("📥 Recargando datos de gestión...")
        
        # 1. Cargar Profesores
        profesores = self.db.obtener_profesores()
        self.llenar_tabla_profesores(profesores)
        
        # 2. Cargar Módulos
        modulos = self.db.obtener_modulos()
        self.llenar_tabla_modulos(modulos)
        
        self.datos_cargados = True

    # =======================================================
    #                   SECCIÓN PROFESORES
    # =======================================================

    def llenar_tabla_profesores(self, datos):
        t = self.ui.tablaProfesores
        headers = ["ID", "Nombre", "Apellidos", "Horas", "Color"]
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        
        header = t.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID ajustado
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Color ajustado

        t.setRowCount(len(datos))
        
        for row, p in enumerate(datos):
            t.setItem(row, 0, QTableWidgetItem(str(p.get('id_trabajador'))))
            t.setItem(row, 1, QTableWidgetItem(p.get('nombre', '')))
            t.setItem(row, 2, QTableWidgetItem(p.get('apellidos', '')))
            
            # Horas centradas
            item_h = QTableWidgetItem(str(p.get('horas_max_semana', 0)))
            item_h.setTextAlignment(Qt.AlignCenter)
            t.setItem(row, 3, item_h)
            
            # Color visual
            color_hex = p.get('color_asignado', '#ffffff')
            item_c = QTableWidgetItem("")
            item_c.setBackground(QColor(color_hex))
            t.setItem(row, 4, item_c)

    def abrir_crear_profesor(self):
        self.mostrar_formulario_profe(False)

    def abrir_editar_profesor(self):
        filas = self.ui.tablaProfesores.selectionModel().selectedRows()
        if not filas:
            QMessageBox.warning(self.ui, "Aviso", "Selecciona un profesor para editar.")
            return
        
        idx = filas[0].row()
        # Recuperamos datos de la tabla visualmente
        id_p = self.ui.tablaProfesores.item(idx, 0).text()
        nom = self.ui.tablaProfesores.item(idx, 1).text()
        ape = self.ui.tablaProfesores.item(idx, 2).text()
        hrs = self.ui.tablaProfesores.item(idx, 3).text()
        col = self.ui.tablaProfesores.item(idx, 4).background().color().name()
        
        datos = {"id": id_p, "nombre": nom, "apellidos": ape, "horas": int(hrs), "color": col}
        self.mostrar_formulario_profe(True, datos)

    def mostrar_formulario_profe(self, modo_edicion, datos=None):
        """Muestra el diálogo de profesor (Crear o Editar)"""
        dialog = QDialog()
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'form_profesor.ui')
        uic.loadUi(ui_path, dialog)
        
        # 1. CARGAR MÓDULOS LIBRES Y PROPIOS (MULTISELECCIÓN)
        id_actual = datos['id'] if modo_edicion else None
        
        # Obtenemos módulos que no tiene nadie más + los míos
        modulos_disponibles = self.db.obtener_modulos_disponibles(id_actual)
        
        # Recuperar asignaciones previas si editamos
        ids_asignados = []
        if modo_edicion:
            ids_asignados = self.db.obtener_ids_modulos_profesor(id_actual)

        dialog.listModulos.clear()
        
        for m in modulos_disponibles:
            # Formato claro: "Programación (DAM 1)"
            texto_modulo = f"{m['nombre_modulo']} ({m['ciclo']} {m.get('curso', '')})"
            
            item = QListWidgetItem(texto_modulo)
            item.setData(Qt.UserRole, m['id_modulo']) # Guardamos el ID invisible
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable) # Activamos CheckBox
            
            # Marcar si ya lo tiene asignado
            if m['id_modulo'] in ids_asignados:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
            dialog.listModulos.addItem(item)

        # 2. Configurar Estado Inicial
        self.color_temporal = datos['color'] if datos else "#3388ff"
        self.preferencias_temporales = []

        if modo_edicion and datos:
            dialog.setWindowTitle(f"Editar: {datos['nombre']}")
            dialog.inputNombre.setText(datos['nombre'])
            dialog.inputApellidos.setText(datos['apellidos'])
            dialog.inputHoras.setValue(datos['horas'])
            
            # Cargar preferencias guardadas
            self.preferencias_temporales = self.db.obtener_preferencias(datos['id'])
        
        def update_preview():
            dialog.frameColorPreview.setStyleSheet(f"background-color: {self.color_temporal}; border: 1px solid white; border-radius: 5px;")
        
        update_preview()

        # --- LÓGICA DE LA PALETA DE COLOR ---
        def abrir_paleta():
            color = QColorDialog.getColor(QColor(self.color_temporal), dialog, "Selecciona color")
            if color.isValid():
                self.color_temporal = color.name()
                update_preview()

        # --- LÓGICA DE LA REJILLA DE PREFERENCIAS ---
        def abrir_grid_preferencias():
            grid_dialog = QDialog(dialog)
            grid_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'grid_preferencias.ui')
            uic.loadUi(grid_path, grid_dialog)
            
            t = grid_dialog.tablaGrid
            dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
            horas = ["08:30", "09:25", "10:20", "11:45", "12:40", "13:35", "14:30"]
            
            t.setColumnCount(len(dias))
            t.setRowCount(len(horas))
            t.setHorizontalHeaderLabels(dias)
            t.setVerticalHeaderLabels(horas)
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            t.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            # --- CORRECCIÓN CLAVE AQUÍ: QAbstractItemView ---
            t.setEditTriggers(QAbstractItemView.NoEditTriggers)

            matriz_estados = {} 
            bloqueados = set()

            # A. Cargar Preferencias
            for pref in self.preferencias_temporales:
                try:
                    d_bd = pref['dia_semana'].replace("MIÉRCOLES", "MIERCOLES")
                    if d_bd in dias:
                        c = dias.index(d_bd)
                        r = pref['franja_horaria'] - 1
                        matriz_estados[f"{r}_{c}"] = pref['nivel_prioridad']
                        
                        col = QColor("#f87171") if pref['nivel_prioridad'] == 1 else QColor("#facc15")
                        item = QTableWidgetItem("")
                        item.setBackground(col)
                        t.setItem(r, c, item)
                except: pass

            # B. Bloquear si ya tiene clase en OTRO horario generado
            if modo_edicion:
                ocupacion = self.db.obtener_ocupacion_horario_profesores([int(datos['id'])])
                mis_clases = ocupacion.get(int(datos['id']), set())
                
                for d_nom, h_num in mis_clases:
                    d_lim = d_nom.replace("MIÉRCOLES", "MIERCOLES")
                    if d_lim in dias:
                        c = dias.index(d_lim)
                        r = h_num - 1
                        
                        bloqueados.add(f"{r}_{c}")
                        it = QTableWidgetItem("CLASE")
                        it.setTextAlignment(Qt.AlignCenter)
                        it.setBackground(QColor("#3b82f6")) # Azul ocupado
                        it.setForeground(QColor("white"))
                        it.setFlags(Qt.ItemIsEnabled) # Bloqueado
                        t.setItem(r, c, it)

            # Clic en celda
            def celda_clicada(row, col):
                k = f"{row}_{col}"
                if k in bloqueados: return # No tocar si está bloqueado por horario real
                
                st = matriz_estados.get(k, 0)
                # Ciclo: 0 -> 2 (Amarillo) -> 1 (Rojo) -> 0
                nuevo = 2 if st == 0 else (1 if st == 2 else 0)
                matriz_estados[k] = nuevo
                
                col_obj = QColor(0,0,0,0)
                if nuevo == 2: col_obj = QColor("#facc15")
                elif nuevo == 1: col_obj = QColor("#f87171")
                
                if not t.item(row, col): t.setItem(row, col, QTableWidgetItem(""))
                t.item(row, col).setBackground(col_obj)
                t.clearSelection()

            t.cellClicked.connect(celda_clicada)

            def guardar_grid():
                self.preferencias_temporales = []
                for k, v in matriz_estados.items():
                    if v == 0: continue
                    r, c = map(int, k.split('_'))
                    d_bd = dias[c].replace("MIERCOLES", "MIÉRCOLES")
                    self.preferencias_temporales.append({
                        "dia_semana": d_bd, "franja_horaria": r+1,
                        "nivel_prioridad": v, "tipo_restriccion": "BLOQUEO" if v==1 else "PREFERENCIA"
                    })
                grid_dialog.accept()

            grid_dialog.btnAceptar.clicked.connect(guardar_grid)
            grid_dialog.exec_()

        # --- GUARDAR TODO ---
        def guardar_todo():
            nom = dialog.inputNombre.text()
            if not nom: return QMessageBox.warning(dialog, "Error", "El nombre es obligatorio")

            payload = {
                "nombre": nom, "apellidos": dialog.inputApellidos.text(),
                "horas_max_semana": dialog.inputHoras.value(), "color_asignado": self.color_temporal
            }

            res = None
            if modo_edicion:
                if self.db.actualizar_profesor(datos['id'], payload): res = {'id_trabajador': datos['id']}
            else: res = self.db.crear_profesor(payload)

            if res:
                pid = res.get('id_trabajador')
                
                # RECOGER MULTI-SELECCIÓN DE LA LISTA
                ids_seleccionados = []
                for i in range(dialog.listModulos.count()):
                    item = dialog.listModulos.item(i)
                    if item.checkState() == Qt.Checked:
                        ids_seleccionados.append(item.data(Qt.UserRole))
                
                self.db.guardar_asignaciones_profesor(pid, ids_seleccionados)
                
                # Guardar preferencias
                for p in self.preferencias_temporales: p['id_trabajador'] = pid
                self.db.guardar_preferencias(pid, self.preferencias_temporales)
                
                dialog.accept()
                self.cargar_datos_iniciales()
            else:
                QMessageBox.critical(dialog, "Error", "Error al guardar en BD")

        # Conexiones
        dialog.btnColorPicker.clicked.connect(abrir_paleta)
        dialog.btnPreferencias.clicked.connect(abrir_grid_preferencias)
        dialog.btnGuardar.clicked.connect(guardar_todo)
        dialog.btnCancelar.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def eliminar_profesor(self):
        filas = self.ui.tablaProfesores.selectionModel().selectedRows()
        if not filas: return
        
        idx = filas[0].row()
        pid = self.ui.tablaProfesores.item(idx, 0).text()
        nom = self.ui.tablaProfesores.item(idx, 1).text()

        if QMessageBox.question(self.ui, "Confirmar", f"¿Eliminar a {nom}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            if self.db.eliminar_profesor(pid): self.cargar_datos_iniciales()

    # =======================================================
    #                   SECCIÓN MÓDULOS
    # =======================================================

    def llenar_tabla_modulos(self, datos):
        t = self.ui.tablaModulos
        h = ["ID", "Módulo", "Ciclo", "Curso", "Horas (Sem/Día)"]
        t.setColumnCount(len(h)); t.setHorizontalHeaderLabels(h)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setRowCount(len(datos))
        
        for r, m in enumerate(datos):
            t.setItem(r, 0, QTableWidgetItem(str(m.get('id_modulo'))))
            t.setItem(r, 1, QTableWidgetItem(m.get('nombre_modulo', '')))
            t.setItem(r, 2, QTableWidgetItem(m.get('ciclo', '')))
            
            c_it = QTableWidgetItem(str(m.get('curso', 1)))
            c_it.setTextAlignment(Qt.AlignCenter)
            t.setItem(r, 3, c_it)
            
            h_it = QTableWidgetItem(f"{m.get('horas_totales_semanales')}/{m.get('horas_max_dia')}")
            h_it.setTextAlignment(Qt.AlignCenter)
            t.setItem(r, 4, h_it)

    def abrir_crear_modulo(self): self.mostrar_form_mod(False)
    def abrir_editar_modulo(self):
        rows = self.ui.tablaModulos.selectionModel().selectedRows()
        if not rows: return QMessageBox.warning(self.ui, "Aviso", "Selecciona un módulo")
        
        idx = rows[0].row()
        t = self.ui.tablaModulos
        hs, hd = map(int, t.item(idx, 4).text().split('/'))
        d = {"id": t.item(idx,0).text(), "nombre": t.item(idx,1).text(), "ciclo": t.item(idx,2).text(),
             "curso": int(t.item(idx,3).text()), "h_sem": hs, "h_dia": hd}
        self.mostrar_form_mod(True, d)

    def mostrar_form_mod(self, edit, d=None):
        dlg = QDialog()
        uic.loadUi(os.path.join(os.path.dirname(__file__), '..', 'ui', 'dialogs', 'form_modulo.ui'), dlg)
        
        if edit:
            dlg.setWindowTitle(f"Editar {d['nombre']}")
            dlg.inputNombreModulo.setText(d['nombre'])
            dlg.inputCiclo.setText(d['ciclo'])
            dlg.inputCurso.setValue(d['curso'])
            dlg.inputHorasSem.setValue(d['h_sem'])
            dlg.inputHorasDia.setValue(d['h_dia'])

        def save():
            pay = {
                "nombre_modulo": dlg.inputNombreModulo.text(),
                "ciclo": dlg.inputCiclo.text(),
                "curso": dlg.inputCurso.value(),
                "horas_totales_semanales": dlg.inputHorasSem.value(),
                "horas_max_dia": dlg.inputHorasDia.value()
            }
            ok = False
            if edit: ok = self.db.actualizar_modulo(d['id'], pay)
            else: ok = self.db.crear_modulo(pay)
            
            if ok: dlg.accept(); self.cargar_datos_iniciales()
            else: QMessageBox.critical(dlg, "Error", "Error BD")

        dlg.btnGuardar.clicked.connect(save)
        dlg.btnCancelar.clicked.connect(dlg.reject)
        dlg.exec_()

    def eliminar_modulo(self):
        rows = self.ui.tablaModulos.selectionModel().selectedRows()
        if rows and QMessageBox.question(self.ui, "Borrar", "¿Eliminar?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.db.eliminar_modulo(self.ui.tablaModulos.item(rows[0].row(),0).text())
            self.cargar_datos_iniciales()