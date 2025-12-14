# Ubicación Óptima de Helipuertos Sanitarios en Castilla y León

Proyecto desarrollado para la asignatura **Modelización Matemática I** del  
**Grado en Ingeniería de Datos e Inteligencia Artificial** (Universidad de León).

El objetivo es determinar la ubicación óptima de **10 helipuertos sanitarios** (uno por provincia y uno adicional para El Bierzo), maximizando la cobertura sanitaria prioritaria bajo restricciones operativas de tiempo y equidad territorial.

---

## Descripción del modelo

El problema se formula como un **Problema de Localización con Cobertura Máxima (MCLP)**, donde se busca maximizar la prioridad sanitaria total cubierta en un tiempo máximo de respuesta de **30 minutos**, considerando:

- Densidad de población  
- Accidentes de tráfico  
- Dificultad de acceso (zonas montañosas y alejadas)  
- Presencia de centros sanitarios  
- Disponibilidad de trasplantes  
- Cobertura 4G  

El modelo utiliza un **índice de prioridad multicriterio** y se resuelve mediante un **algoritmo heurístico de mejora iterativa por región**.

---

## Estructura del proyecto

```text
C:.
│   environment.yml
│   README.md
│
├── data
│   ├── accidentalidad-por-carreteras.csv
│   ├── datos_demanda_final_densidad_4g_scaled.csv
│   ├── densidad-obsoleto.xlsx
│   ├── registro-de-municipios-de-castilla-y-leon.csv
│   ├── registro-de-municipios_sin-limpiar.csv
│   └── solucion_prioridad_optima.csv
│
├── docs
│   ├── hoja_de_control.md
│   └── Selección de datos.docx
│
├── figures
│   ├── cobertura.png
│   ├── mapa_cobertura_helicopteros.html
│   ├── mapa_cobertura_helicopteros_15.html
│   ├── mapa_cobertura_helicopteros_municipios.html
│   ├── mapa_cobertura_helicopteros_municipios_difi_acceso.html
│   └── pesos_modelo_multicriterio.png
│
└── src
    ├── code.py
    ├── codigo_a_entregar.py
    ├── juntar_densidad_cobertura_al_csv_global.py
    ├── procesar_accidentes.py
    ├── procesar_cp_centros_sanitarios.py
    └── procesar_transplates_hospitales_dificil_acceso.py
```

## Descripción de carpetas

### `data/`
Contiene todos los datasets utilizados en el proyecto, tanto en bruto como procesados.

- `registro-de-municipios-de-castilla-y-leon.csv`: dataset principal ya limpio
- `registro-de-municipios_sin-limpiar.csv`: dataset original con todas las variables, sin procesar ni ajustadas al modelo
- `accidentalidad-por-carreteras.csv`: dataset de siniestralidad vial
- `datos_demanda_final_densidad_4g_scaled.csv`: dataset normalizado de densidad de población y cobertura 4g
- `solucion_prioridad_optima.csv`: resultado final del modelo

### `docs/`
Documentación auxiliar del proyecto:

- `Selección de datos.docx`: informe pequeño sobre el procesamiento de las variables dificultad de acceso y hospitales
- `hoja_de_control.md`: control de utilización de git

### `figures/`
Visualizaciones y mapas generados:

- Mapas de cobertura a 15 y 30 minutos
- Mapas interactivos en HTML
- Gráficos de ponderación del modelo multicriterio

### `src/`
Código fuente del proyecto.

#### `codigo_a_entregar.py`
Archivo principal del proyecto.

- Implementa el modelo matemático completo
- Calcula el índice de prioridad
- Evalúa candidatos viables
- Ejecuta la optimización heurística
- Calcula métricas de cobertura
- Genera el CSV final con las ubicaciones óptimas

**Este es el archivo que debe ejecutarse para reproducir los resultados del informe.**

#### `code.py`
Versión extendida orientada a la visualización geográfica.

- Utiliza la biblioteca Folium
- Dibuja círculos de cobertura cuyos centros vienen indicados por las coordenadas de los municipios seleccionados
- Permite configurar parámetros adicionales como radio, color u opacidad

**Este archivo no es necesario para la optimización**, sino para la visualización y análisis espacial.

#### Scripts de preprocesamiento
- `procesar_accidentes.py`: tratamiento y ponderación de accidentes
- `procesar_cp_centros_sanitarios.py`: integración de centros sanitarios
- `procesar_transplates_hospitales_dificil_acceso.py`: hospitales, trasplantes y dificultad de acceso
- `juntar_densidad_cobertura_al_csv_global.py`: integración final de variables

---

## Ejecución del proyecto

### 1) Crear el entorno (opcional)

```bash
conda env create -f environment.yml
conda activate mmi-helipuertos
```
### 2) Ejecutar el modelo principal

```bash
python src/codigo_a_entregar.py
```
Esto generará:

- Salida por consola con métricas de cobertura
- El archivo `solucion_prioridad_optima.csv` en la carpeta `data/`

---

## Resultados principales

**Cobertura 30 minutos**

- 100% de la población
- 100% del score de prioridad

**Cobertura 15 minutos**

- 62.42% de la población
- 73.08% del score de prioridad

El modelo prioriza correctamente zonas de alta criticidad sanitaria, aunque no concentren grandes volúmenes de población.

---

## Tecnologías utilizadas

- Python 3.9
- pandas, numpy
- scikit-learn
- folium (visualización)
- LaTeX (documentación)
- GitHub (control de versiones)

---

## Autores

Proyecto realizado por el **Grupo C**:

- María Batlles Aguilera
- Sofía Fuentes Crespo
- Iván Tejada Mardones
- Marcos López Caldito
- Álvaro Luis Alonso
- Guillén Menéndez Pellitero
