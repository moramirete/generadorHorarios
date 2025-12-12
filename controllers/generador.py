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
        self.ui.comboCiclos.addItem("Seleccionar")
        ciclos = self.db.obtener_ciclos_unicos()
        for c in ciclos:
            self.ui.comboCiclos.addItem(c)

    def cargar_datos_ciclo(self):
        ciclo = self.ui.comboCiclos.currentText()
        if ciclo == "Seleccionar":
            self.ui.tablaResumen.setRowCount(0)
            self.actualizar_validacion(False, False, 0)
            return

        datos = self.db.obtener_datos_generacion(ciclo)
        self.llenar_tabla(datos)
        
       
        total = sum(d['horas'] for d in datos)
        
        
        horas_ok = (total == 30) 
        
        profes_ok = all(d['id_profesor'] is not None for d in datos)
        
        self.actualizar_validacion(horas_ok, profes_ok, total)

    def llenar_tabla(self, datos):
        t = self.ui.tablaResumen
        
        # Visual
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)   
        t.setSelectionMode(QAbstractItemView.NoSelection)     
        t.setFocusPolicy(Qt.NoFocus)                         
        
        cols = ["Módulo", "Profesor Asignado", "Horas"]
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        t.setRowCount(len(datos))
        for r, d in enumerate(datos):
            t.setItem(r, 0, QTableWidgetItem(d['nombre_modulo']))
            
            p_item = QTableWidgetItem(d['nombre_profesor'])
            if d['id_profesor'] is None:
                p_item.setForeground(QColor("#ef4444"))
                p_item.setText("SIN ASIGNAR")
            else:
                p_item.setForeground(QColor("#4ade80"))
            t.setItem(r, 1, p_item)
            
            h_item = QTableWidgetItem(str(d['horas']))
            h_item.setTextAlignment(Qt.AlignCenter)
            t.setItem(r, 2, h_item)

    def actualizar_validacion(self, h_ok, p_ok, total):
        lbl_h = self.ui.lblCheckHoras
        
        if h_ok:
            lbl_h.setText(f"Total Horas: {total} / 30")
            lbl_h.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 14px;")
        else:
            lbl_h.setText(f"Total Horas: {total} / 30 (Debe sumar 30 exactas)")
            lbl_h.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")

        lbl_p = self.ui.lblCheckProfes
        if p_ok:
            lbl_p.setText("Profesores asignados")
            lbl_p.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 14px;")
        else:
            lbl_p.setText("Faltan profesores")
            lbl_p.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")

        btn = self.ui.btnLanzarGenerador
        
    # Cuando existe 30 horas de 30 el cursor del raton se pone con una mano para que quede bonito, si no llega al maximo de horas o se pasa, no sale el cursor

        if p_ok and h_ok:
            btn.setEnabled(True)
            btn.setCursor(Qt.PointingHandCursor) 
        else:
            btn.setEnabled(False)
            btn.setCursor(Qt.ForbiddenCursor)
        
        errores = []
        if not h_ok: errores.append("HORAS INCORRECTAS")
        if not p_ok: errores.append("FALTAN PROFESORES")
        
        if errores:
             btn.setText(f"REVISA: {' Y '.join(errores)}")
             btn.setStyleSheet("""
                QPushButton { background-color: #334155; color: #94a3b8; font-weight: bold; padding: 20px; border-radius: 8px; font-size: 16px; }
            """)
        else:
             btn.setText("GENERAR HORARIO AHORA") 
             btn.setStyleSheet("""
                QPushButton { background-color: #38BDF8; color: #0f172a; font-weight: bold; padding: 20px; border-radius: 8px; font-size: 16px; }
                QPushButton:hover { background-color: #7dd3fc; }""")


    def iniciar_algoritmo(self):
        ciclo = self.ui.comboCiclos.currentText()
        
        self.ui.btnLanzarGenerador.setText("Generando...")
        self.ui.btnLanzarGenerador.setEnabled(False)
        self.ui.btnLanzarGenerador.setCursor(Qt.WaitCursor) 
        QApplication.processEvents()
        
        motor = GeneradorAutomatico(self.db)
        ok, msg = motor.generar_horario(ciclo)
        
        self.ui.btnLanzarGenerador.setText("Generar horario ahora")
        

        if ok:
            tipo = QMessageBox.Warning if "Ignorado" in msg else QMessageBox.Information
            QMessageBox.information(self.ui, "Resultado Generación", msg)
            if self.main_window:
                self.main_window.btnVistaHorario.click()
                if hasattr(self.main_window, 'ctrl_vista'):
                    self.main_window.ctrl_vista.actualizar_vista()
        else:
            QMessageBox.critical(self.ui, "Error Crítico", msg)
            self.ui.btnLanzarGenerador.setEnabled(True)
            self.ui.btnLanzarGenerador.setCursor(Qt.PointingHandCursor)