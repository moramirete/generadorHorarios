from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView, QApplication, QAbstractItemView
from PyQt5.QtGui import QColor, QCursor
from PyQt5.QtCore import Qt
from logic.algoritmo import GeneradorAutomatico

class GeneradorController:
    def __init__(self, ui, db, main_window=None):
        self.ui = ui
        self.db = db
        self.main_window = main_window 
        
        try:
            self.ui.btnLanzarGenerador.clicked.connect(self.iniciar_algoritmo)
            self.ui.comboCiclos.currentIndexChanged.connect(self.cargar_datos_ciclo)
            self.cargar_ciclos()
        except AttributeError:
            pass

    def cargar_ciclos(self):
        self.ui.comboCiclos.clear()
        self.ui.comboCiclos.addItem("- Seleccionar -")
        ciclos = self.db.obtener_ciclos_unicos()
        for c in ciclos:
            self.ui.comboCiclos.addItem(c)

    def cargar_datos_ciclo(self):
        ciclo = self.ui.comboCiclos.currentText()
        if ciclo == "- Seleccionar -":
            self.ui.tablaResumen.setRowCount(0)
            self.actualizar_validacion(False, False, 0)
            return

        datos = self.db.obtener_datos_generacion(ciclo)
        self.llenar_tabla(datos)
        
        # Validaciones (Flexible para pruebas: acepta entre 20 y 35 horas)
        total = sum(d['horas'] for d in datos)
        horas_ok = (30 <= total <= 35) 
        profes_ok = all(d['id_profesor'] is not None for d in datos)
        
        self.actualizar_validacion(horas_ok, profes_ok, total)

    def llenar_tabla(self, datos):
        t = self.ui.tablaResumen
        
        
        
        # 1. Ocultar números de fila y poner en blanco una cosa de la tabla que salia en blanco
        t.verticalHeader().setVisible(False)
        
        # 2. Bloquear edición y selección
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)   
        t.setSelectionMode(QAbstractItemView.NoSelection)     
        t.setFocusPolicy(Qt.NoFocus)                         
        
        # Configuración de columnas
        cols = ["Módulo", "Profesor Asignado", "Horas"]
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Rellenar datos
        t.setRowCount(len(datos))
        for r, d in enumerate(datos):
            # Módulo
            t.setItem(r, 0, QTableWidgetItem(d['nombre_modulo']))
            
            # Profesor (Con color rojo si falta)
            p_item = QTableWidgetItem(d['nombre_profesor'])
            if d['id_profesor'] is None:
                p_item.setForeground(QColor("#ef4444")) # Rojo
                p_item.setText(" SIN ASIGNAR")
            else:
                p_item.setForeground(QColor("#4ade80")) # Verde
            t.setItem(r, 1, p_item)
            
            # Horas (Centradas)
            h_item = QTableWidgetItem(str(d['horas']))
            h_item.setTextAlignment(Qt.AlignCenter)
            t.setItem(r, 2, h_item)

    def actualizar_validacion(self, h_ok, p_ok, total):
        lbl_h = self.ui.lblCheckHoras
        # Mensajes de validación
        if h_ok:
            lbl_h.setText(f"Total Horas: {total} / 30")
            lbl_h.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 14px;")
        else:
            lbl_h.setText(f"Total Horas: {total} / 30")
            lbl_h.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")

        lbl_p = self.ui.lblCheckProfes
        if p_ok:
            lbl_p.setText("Profesores asignados")
            lbl_p.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 14px;")
        else:
            lbl_p.setText("Faltan profesores")
            lbl_p.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")

        # Estado del botón
        btn = self.ui.btnLanzarGenerador
        # Nota: Permitimos generar si hay profes, aunque las horas no sean exactas para facilitar pruebas
        if p_ok: 
            btn.setEnabled(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setText(" GENERAR HORARIO AHORA")
            btn.setStyleSheet("""
                QPushButton { background-color: #38bdf8; color: #0f172a; font-weight: bold; padding: 20px; border-radius: 8px; font-size: 16px; }
                QPushButton:hover { background-color: #7dd3fc; }
            """)
        else:
            btn.setEnabled(False)
            btn.setCursor(Qt.ForbiddenCursor)
            btn.setText("REVISA LOS ERRORES ARRIBA")
            btn.setStyleSheet("""
                QPushButton { background-color: #334155; color: #94a3b8; font-weight: bold; padding: 20px; border-radius: 8px; font-size: 16px; }
            """)

    def iniciar_algoritmo(self):
        ciclo = self.ui.comboCiclos.currentText()
        
        self.ui.btnLanzarGenerador.setText(" Generando...")
        self.ui.btnLanzarGenerador.setEnabled(False)
        QApplication.processEvents()
        
        motor = GeneradorAutomatico(self.db)
        ok, msg = motor.generar_horario(ciclo)
        
        self.ui.btnLanzarGenerador.setText("GENERAR HORARIO AHORA")
        self.ui.btnLanzarGenerador.setEnabled(True)

        if ok:
            tipo = QMessageBox.Warning if "IGNORADO" in msg else QMessageBox.Information
            QMessageBox.information(self.ui, "Resultado Generación", msg)
            # Navegar a la vista de horario
            if self.main_window:
                self.main_window.btnVistaHorario.click()
                if hasattr(self.main_window, 'ctrl_vista'):
                    # Actualizar vista y cargar ciclos
                    self.main_window.ctrl_vista.cargar_ciclos()
                    self.main_window.ctrl_vista.actualizar_vista()
                    # Seleccionar automáticamente el ciclo generado
                    try:
                        combo = self.main_window.ctrl_vista.ui.comboFiltro
                        for i in range(combo.count()):
                            if combo.itemText(i) == ciclo:
                                combo.setCurrentIndex(i)
                                # Forzar el llenado
                                self.main_window.ctrl_vista.on_cambiar_ciclo()
                                break
                    except:
                        pass
        else:
            QMessageBox.critical(self.ui, "Error Crítico", msg)