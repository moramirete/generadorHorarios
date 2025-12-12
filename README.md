# Gestor y Generador de Horarios Escolar

> **Versión:** 1.0.0  
> **Estado:** Producción / Estable  
> **Tecnología:** Python 3 + PyQt5 + Supabase

## Descripción del Proyecto

**GeneradorHorarios** es una aplicación de escritorio robusta diseñada para automatizar y gestionar la creación de horarios escolares, específicamente orientada a ciclos de Formación Profesional (FP). 

El sistema resuelve la compleja problemática de la asignación de horarios mediante un **algoritmo de Backtracking (Vuelta Atrás)**, capaz de respetar restricciones duras (bloqueos horarios, asignaciones previas) y preferencias blandas de los docentes, garantizando una distribución equitativa y pedagógicamente válida.

La interfaz gráfica ha sido construida con **PyQt5**, implementando un diseño moderno (Dark Mode) y una arquitectura modular que separa la lógica de negocio de la vista.

## Autores (Nombres - GitHub)
- Sergio Mora Mirete - moramirete
- Marcos Antonio Monreal Martinez - monrealmartinez
- Zeus Lopez Prior - zeuslpzz


## Características Principales

### Gestión Integral (CRUD)
- **Profesores:** Gestión completa de docentes, incluyendo asignación de colores identificativos y carga horaria máxima semanal.
- **Módulos:** Administración de asignaturas/módulos, vinculación a ciclos formativos, cursos y carga horaria (semanal y diaria).
- **Asignación Inteligente:** Vinculación dinámica de módulos a profesores basada en disponibilidad.

### Motor de Algoritmo
- **Backtracking Recursivo:** Algoritmo personalizado (`logic/algoritmo.py`) que explora el árbol de soluciones para encontrar un horario sin conflictos.
- **Gestión de Conflictos:**
  - **Nivel 1 (Restricción Dura):** Bloqueos absolutos (ej. el profesor no trabaja los viernes).
  - **Nivel 2 (Preferencia):** El algoritmo intenta evitar estas franjas, pero las usa si es estrictamente necesario (generando avisos).
- **Control de Carga:** Evita que un módulo tenga más de 2 horas seguidas en el mismo día.

### Visualización y Exportación
- **Vista Dual:** Visualización de horarios filtrada por **Grupo/Clase** o por **Profesor**.
- **Grid de Preferencias:** Interfaz visual interactiva para que los profesores marquen su disponibilidad.
- **Exportación XLSX:** Generación de reportes en Excel utilizando `openpyxl`, con hojas separadas para datos de gestión y horarios visuales con código de colores.

### Persistencia en la Nube
- Integración nativa con **Supabase** (PostgreSQL) para la persistencia de datos en tiempo real.
- Operaciones optimizadas para reducir la latencia en la carga de datos masivos.

## Arquitectura del Software

El proyecto sigue un patrón de diseño **MVC (Modelo-Vista-Controlador)** adaptado a aplicaciones de escritorio:

- **Vistas (`ui/`):** Archivos `.ui` generados con Qt Designer. Se cargan dinámicamente con `uic`, lo que facilita la iteración rápida de diseño sin recompilar código.
- **Controladores (`controllers/`):** Gestionan la lógica de la interfaz, las señales de Qt y la comunicación con la base de datos.
  - `generador.py`: Orquesta el algoritmo de generación.
  - `gestion_datos.py`: Maneja los formularios CRUD.
  - `vista_horario.py`: Renderiza la tabla visual del horario.
- **Modelo/Lógica (`database/` y `logic/`):** 
    - `db_conexion.py`: Capa de abstracción para las consultas a Supabase.
  - `algoritmo.py`: Núcleo lógico puro de la generación de horarios.

## Requisitos Previos

Para ejecutar este proyecto, necesitas tener instalado:

* **Python 3.8** o superior.
* Conexión a Internet (para acceder a Supabase).

### Dependencias


Las librerías principales se encuentran listadas a continuación. Se recomienda usar un entorno virtual.

```bash
pip install PyQt5 supabase openpyxl




