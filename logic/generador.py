from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class GeneradorController:
    def __init__(self, ui, db, main_window=None):
        self.ui = ui
        self.db = db
        self.main = main_window
        try:
            self.ui.btnLanzarGenerador.clicked.connect(self.iniciar_generacion)
        except AttributeError:
            pass

    def iniciar_generacion(self):
        """Genera un horario sencillo: asigna cada profesor a una franja horaria.
        - Respeta bloqueos (nivel 1) evitando asignar allí.
        - Prefiere franjas nivel 2 cuando sea posible.
        - Colorea las celdas con `color_asignado` del profesor.
        - Si detecta una incompatibilidad (dos asignaciones en la misma casilla)
          muestra una ventana emergente describiendo el conflicto, pero no cierra la página.
        """
        # Obtener referencia a la tabla de la vista de horario
        if not self.main:
            QMessageBox.critical(self.ui, "Generador", "No se encontró la ventana principal para mostrar el horario.")
            return

        # Asegurarnos de que la vista de horario esté cargada
        try:
            self.main.cargar_vista_horario()
        except Exception:
            pass

        try:
            tabla = self.main.ctrl_vista.ui.tablaHorarioGeneral
        except Exception:
            QMessageBox.critical(self.ui, "Generador", "No se pudo acceder a la tabla del horario.")
            return

        dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
        horas = ["08:30", "09:25", "10:20", "11:45", "12:40", "13:35", "14:30"]

        # Preparar tabla
        columnas = ["HORA"] + dias
        tabla.setColumnCount(len(columnas))
        tabla.setRowCount(len(horas))
        tabla.setHorizontalHeaderLabels(columnas)
        for r, h in enumerate(horas):
            item = QTableWidgetItem(h)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            tabla.setItem(r, 0, item)

        # mapa de módulos por id
        modulos = self.db.obtener_modulos() or []
        mod_map = {m.get('id_modulo'): m.get('nombre_modulo', '') for m in modulos}

        profesores = self.db.obtener_profesores() or []

        # occupancy: (r,c) -> (prof_id, prof_nombre, modulo)
        occupancy = {}
        conflicts = []

        for prof in profesores:
            pid = prof.get('id_trabajador') or prof.get('id')
            if not pid:
                continue
            nombre = prof.get('nombre', '')
            apellidos = prof.get('apellidos', '')
            color = prof.get('color_asignado', '#ffffff')

            # módulo asignado (si existe)
            mid = None
            try:
                mid = self.db.obtener_id_modulo_asignado(pid)
            except Exception:
                mid = None
            mod_obj = None
            for m in modulos:
                if m.get('id_modulo') == mid:
                    mod_obj = m
                    break
            mod_name = mod_obj.get('nombre_modulo', f"Módulo {mid}") if mod_obj else (f"Módulo {mid}" if mid else "(Sin módulo)")
            horas_req = int(mod_obj.get('horas_totales_semanales', 1)) if mod_obj else 1

            # preferencias y bloqueos
            prefs = []
            try:
                prefs = self.db.obtener_preferencias(pid) or []
            except Exception:
                prefs = []

            preferred_slots = []
            blocked_slots = set()
            for p in prefs:
                try:
                    dia = p.get('dia_semana', '').replace('MIÉRCOLES', 'MIERCOLES')
                    fr = int(p.get('franja_horaria', 0)) - 1
                    nivel = int(p.get('nivel_prioridad', 0))
                    if dia in dias and 0 <= fr < len(horas):
                        c = dias.index(dia) + 1
                        r = fr
                        if nivel == 1:
                            blocked_slots.add((r, c))
                        elif nivel == 2:
                            preferred_slots.append((r, c))
                except Exception:
                    continue

            # We need to assign `horas_req` slots for this professor/module
            assigned_count = 0
            # order candidate slots: preferred first, then all other non-blocked slots
            candidates = []
            # keep unique while preserving order
            seen = set()
            for slot in preferred_slots:
                if slot in seen: continue
                seen.add(slot)
                candidates.append(slot)

            for r in range(len(horas)):
                for c in range(1, len(dias) + 1):
                    if (r, c) in seen:
                        continue
                    if (r, c) in blocked_slots:
                        continue
                    seen.add((r, c))
                    candidates.append((r, c))

            for (r, c) in candidates:
                if assigned_count >= horas_req:
                    break
                if (r, c) in blocked_slots:
                    continue
                if (r, c) in occupancy:
                    # conflicto: ya hay alguien asignado -> recordar y seguir
                    other = occupancy[(r, c)]
                    conflicts.append(f"Conflicto: {nombre} {apellidos} ({mod_name}) vs {other[1]} ({other[2]}) — {dias[c-1]} {horas[r]}")
                    continue
                # asignar
                occupancy[(r, c)] = (pid, f"{nombre} {apellidos}", mod_name, color)
                assigned_count += 1

            if assigned_count < horas_req:
                conflicts.append(f"No hay hueco suficiente para {nombre} {apellidos} ({mod_name}): requiere {horas_req}, asignadas {assigned_count}")

        # Rellenar tabla con occupancy
        for (r, c), val in occupancy.items():
            pid, prof_nom, mod_name, color = val
            txt = f"{mod_name}\n{prof_nom}"
            item = QTableWidgetItem(txt)
            item.setBackground(QColor(color))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            tabla.setItem(r, c, item)

        # Mostrar resumen de conflictos si los hay
        if conflicts:
            text = "Se han detectado las siguientes incompatibilidades:\n\n" + "\n".join(conflicts)
            # Mostrar en un diálogo informativo que no cierra la página
            QMessageBox.warning(self.ui, "Conflictos detectados", text)

        QMessageBox.information(self.ui, "Generador", "Generación finalizada.")