from PyQt5.QtWidgets import QMessageBox

class GeneradorController:
    def __init__(self, ui, db):
        self.ui = ui
        self.db = db
        try:
            self.ui.btnLanzarGenerador.clicked.connect(self.iniciar_generacion)
        except AttributeError:
            pass

    def iniciar_generacion(self):
        QMessageBox.information(self.ui, "Generador", "¡Algoritmo iniciado! (Lógica pendiente)")