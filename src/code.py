import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium


ARCHIVO_CSV = 'registro_municipios_completo.csv'

#PARÁMETROS DE LOS HELICOPTEROS:

#La velocidad crucero de un helicoptero es de 240 km/h
VELOCIDAD_HELICOPTERO = 240
#El tiempo de cobertura minimo regional es de 30 min
TIEMPO_COBERTURA_MAX = 30
#El tiempo de acción rápida ideal 15 min
TIEMPO_ACCION_IDEAL = 15

# Radio operativo en Km (para validación de hospitales cercanos)
RADIO_OPERATIVO_KM = (VELOCIDAD_HELICOPTERO * TIEMPO_COBERTURA_MAX) / 60

#PESOS DEL MODELO PARA LA PRIORIDAD
W_ACCIDENTES_CTRA = 0.2  #prioridad media: Zonas de siniestralidad
W_DIFICULTAD = 0.43      #Alta prioridad: A zonas montañosas(debido a la deficultad de los vehiculos terrestres) y lejanaas a ciudades principales
W_DENSIDAD = 0.15     #Prioridad media: Cubrir al mayor número de personas
W_TIENE_CENTRO = 0.15    #Prioridad media: Puntos de transferencia médica
W_TRANSPLANTES = 0.02   #Prioridad Baja: Especialización: Capacidad crítica
W_4G = 0.05              #Prioridad baja: Cobertura movil 

#Como hay que añadir uno en el bierzo hacemos un listado de los municipios pertenecientes a el
MUNICIPIOS_BIERZO = [
    "ARGANZA", "BALBOA", "BARJAS", "BEMBIBRE", "BENUZA", "BERLANGA DEL BIERZO",
    "BORRENES", "CABAÑAS RARAS", "CACABELOS", "CAMPONARAYA", "CANDÍN",
    "CARRACEDELO", "CARUCEDO", "CASTROPODAME", "CONGOSTO", "CORULLÓN",
    "CUBILLOS DEL SIL", "FABERO", "FOLGOSO DE LA RIBERA", "IGÜEÑA",
    "MOLINASECA", "NOCEDA DEL BIERZO", "OENCIA", "PALACIOS DEL SIL",
    "PÁRAMO DEL SIL", "PERANZANES", "PONFERRADA", "PRIARANZA DEL BIERZO",
    "PUENTE DE DOMINGO FLÓREZ", "SANCEDO", "SOBRADO", "TORAL DE LOS VADOS",
    "TORENO", "TORRE DEL BIERZO", "TRABADELO", "VEGA DE ESPINAREDA",
    "VEGA DE VALCARCE", "VILLAFRANCA DEL BIERZO"
]

# FUNCIONES Y CARGA DE DATOS
def haversine_vectorizado(lon1, lat1, lon2, lat2):
    """Calcula la distancia geodésica en km entre coordenadas."""
    # Los datos vienen en grados, por lo que usamos map() para convertir las 4 variables a radianes.
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    #calculo de diferencias
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    #Calculamos a que representa el cuadrado de la mitad de la longitud de la cuerda recta entre los puntos.
    #Fórmula matemática: a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    #c es la distancia angular en radianes sobre la superficie de la esfera.
    #Fórmula: c = 2 * arcsin(√a)
    c = 2 * np.arcsin(np.sqrt(a))
    #Multiplicamos la distancia angular c por el radio medio de la tierra.
    #Para asi convertir los radianes a kilómetros.
    return 6371 * c

print("--- Iniciando proceso de optimización ---")
df = pd.read_csv(ARCHIVO_CSV)

#Extraemos las columnas necesarias del csv
cols_necesarias = ['DENSIDADMM', 'Accidentes_Por_Carretera', 'Dificultad_Acceso', 
                   '4G', 'tiene_centro', 'Transplantes', 'Población', 'Tiene_Hospital']
#recorre las columnas extraidas del csv
for col in cols_necesarias:
    if col not in df.columns: #aseguramos que no falle en caso de que una columna no exista
        df[col] = 0
    df[col] = df[col].fillna(0)#rellenamos los datos nulos a 0 en caso que haya
#estas son las columnas a normalizar
cols_a_normalizar = ['DENSIDADMM', 'Accidentes_Por_Carretera', 'Dificultad_Acceso', 
                     '4G', 'tiene_centro', 'Transplantes']
#realizamos el proceso de normalizacion conocido como minmax para normalizar las columnas
#A pesar que ya han sido normalizadas en el csv las normalizamos otra vez por si acaso ha habido algun problema o fallo
#esta fomula es la normalizacion minmax hecha a mano se podria haber usado la funcion minmax de sklearn para hacerlo en una  linea.
for col in cols_a_normalizar:
    col_norm = col + '_Norm'
    min_val = df[col].min()
    max_val = df[col].max()
    if max_val - min_val == 0:
        df[col_norm] = 0
    else:
        df[col_norm] = (df[col] - min_val) / (max_val - min_val)

#Multiplicamos los valores por sus pesos correspondientes
df['Score_Prioridad'] = (
    df['Accidentes_Por_Carretera_Norm'] * W_ACCIDENTES_CTRA +
    df['Dificultad_Acceso_Norm'] * W_DIFICULTAD +
    df['DENSIDADMM_Norm'] * W_DENSIDAD +
    df['tiene_centro_Norm'] * W_TIENE_CENTRO +
    df['Transplantes_Norm'] * W_TRANSPLANTES +
    (1 - df['4G_Norm']) * W_4G #este es un caso especial ya que necesitamos aplicar el peso al valor inverso de la cobertura
    #debido a que es prioridad donde menos haya cobertura
)

#Convertimos los nombres de municipios a MAYÚSCULAS .upper() y eliminamos espacios en blanco al principio/final .strip()
df['Municipio_Norm'] = df['Municipio'].str.upper().str.strip()
#Usamos .isin() para saber si un municipio pertenece a la lista de municipios del bierzo.
#Devuelve True/False y con .astype(int) lo convertimos a 1 o 0.
#Esto lo hacemos para identificar la comarca.
df['Es_Bierzo'] = df['Municipio_Norm'].isin(MUNICIPIOS_BIERZO).astype(int)
#Esta función sirve para agrupar los territorios.
def asignar_region(row):
    #Nos indica si es del Bierzo, independiente de León. 
    if row['Es_Bierzo'] == 1: return 'EL BIERZO'
    #Si no es Bierzo, pero es provincia de León, es LEÓN(RESTO).
    #Esto es para evitar que poniendo un helicoptero en el bierzo diga que en leon ya lo ha puesto.
    elif row['Provincia'] == 'LEÓN': return 'LEÓN (RESTO)'
    #Las otras provincias no las modificamos
    else: return row['Provincia']
#.apply(..., axis=1) ejecuta la función 'asignar_region' para asegurar que hay 1 base en cada uno de estos 10 grupos.
df['Region_Logica'] = df.apply(asignar_region, axis=1)


#SELECCIÓN DE CANDIDATOS VIABLES
print("--- Evaluando viabilidad de candidatos ---")


# Creamos una columna donde se va a guardar la distancia al hospital más cercano
df['Distancia_Hospital_Min'] = 9999.0

# Guardamos que municipios ya tienen un hospital
hospitales = df[df['Tiene_Hospital'] == 1]

#comprobamos que existen hospitales
#guardamos las coordenadas de los hospitales
coords_hosp = hospitales[['Latitud', 'Longitud']].values
lat_hosp = coords_hosp[:, 0][np.newaxis, :]
lon_hosp = coords_hosp[:, 1][np.newaxis, :]

#guardamos las coordenadas de todos los municipios candidatos
lat_cand_raw = df['Latitud'].values[:, np.newaxis]
lon_cand_raw = df['Longitud'].values[:, np.newaxis]

# Calcula una matriz de distancia de cada municipio a cada hospital con la funcion que creamos antes
dists_hosp = haversine_vectorizado(lon_cand_raw, lat_cand_raw, lon_hosp, lat_hosp)

#nos quedamos con la distancia minima de cada municipio
min_dist_hosp = np.min(dists_hosp, axis=1)

# Guardamos cada uno de los minimos en el DataFrame 
df['Distancia_Hospital_Min'] = min_dist_hosp

#Un candidato es viable si tiene hospital en el radio o en el mismo municipio
df['Hospital_Cercano_OK'] = (min_dist_hosp <= RADIO_OPERATIVO_KM) | (df['Tiene_Hospital'] == 1)

#analizamos todo el csv y buscamos los municipios con poblacion entre 300 y 10000 y con un hospital cercano calculado antes
condicion_poblacion = (df['Población'].between(300, 10000, inclusive='neither') & df['Hospital_Cercano_OK'])

#copiamos los candidatos a una nueva lista
candidates = df[condicion_poblacion].copy().reset_index(drop=True)

#comprobamos region por region si alguna ha quedado sin candidatos por condiciones muy estrictas
for reg in df['Region_Logica'].unique():
    #si ha quedado vacio:
    if len(candidates[candidates['Region_Logica'] == reg]) == 0:
        #añadimos a esa region el municipio con mayor score
        top_muni = df[df['Region_Logica'] == reg].sort_values('Score_Prioridad', ascending=False).iloc[0]
        #añadimos todo a la lista de candidatos
        candidates = pd.concat([candidates, top_muni.to_frame().T])

#limpiamos los indices para evitar errores
candidates = candidates.reset_index(drop=True)
demand = df.copy()
#imprimimos la cantidad total de municipios candidatos
print(f"Total Candidatos Viables: {len(candidates)}")



#Optimización (Maximizar Cobertura Prioritaria)

# El objetivo es seleccionar un helipuerto por que maximice la prioridad de todos los puntos de demanda cubiertos dentro del tiempo máximo.

print("--- Optimizando ubicaciones (Base 30 min) ---")

#Preparamos la matriz de cobertura
#Extraemos las coordenadas de la demanda y los candidatos.
lat_dem = demand['Latitud'].values[:, np.newaxis]
lon_dem = demand['Longitud'].values[:, np.newaxis]
lat_cand = candidates['Latitud'].values[np.newaxis, :]
lon_cand = candidates['Longitud'].values[np.newaxis, :]

#Calcula la matriz de distancias en kilómetros.
dists_km = haversine_vectorizado(lon_dem, lat_dem, lon_cand, lat_cand)
#Convertimos la distancia a tiempo de vuelo en minutos.
tiempos_min = (dists_km / VELOCIDAD_HELICOPTERO) * 60

#Crea la matriz: 1 si el tiempo es menor o igual al máximo tiempo de cobertura o 0 si no
matriz_cobertura_30 = (tiempos_min <= TIEMPO_COBERTURA_MAX).astype(int)
#Extrae los scores de prioridad de cada punto de demanda para maximizarlo
scores_demanda = demand['Score_Prioridad'].values

solucion_indices = [] # Lista para almacenar los índices globales de los helipuertos seleccionados.
regiones = df['Region_Logica'].unique() # Identifica todas las regiones lógicas.

#Definición de la Función Objetivo
def calcular_score_total_cubierto(indices_solucion):
    """Calcula el score total sumando las prioridades de los puntos de demanda cubiertos."""
    #Verifica si cada pueblo es cubierto por alguna base elegida.
    cubierto_bool = np.any(matriz_cobertura_30[:, indices_solucion] == 1, axis=1)
    #Suma los puntos de prioridad solo de los pueblos cubiertos.
    return np.sum(scores_demanda[cubierto_bool])


# Paso 1: Solución Inicial
# Selecciona el candidato con la mayor 'Score_Prioridad' de cada region
for reg in regiones:
    cands_reg = candidates[candidates['Region_Logica'] == reg]
    # Encuentra el candidato con la mayor prioridad interna en esa región.
    mejor_cand = cands_reg.loc[cands_reg['Score_Prioridad'].idxmax()]
    #Obtenemos el índice de ese candidato del DataFrame.
    idx_global = candidates.index[candidates['Municipio'] == mejor_cand['Municipio']].tolist()[0]
    #añadimos el indice a la lista de soluciones.
    solucion_indices.append(idx_global)

#Calcula el score inicial de la solución base.
score_actual = calcular_score_total_cubierto(solucion_indices)

#Mejora Iterativa
mejora = True
while mejora:
    #Asume que no hay mejora en esta iteración
    mejora = False
    # Itera sobre cada posición.
    for i in range(len(solucion_indices)):
        #Extraemos el indice y candidato de la region actual.
        idx_actual = solucion_indices[i]
        region_actual = candidates.iloc[idx_actual]['Region_Logica']
        #Obtiene todos los candidatos alternativos dentro de la región actual.
        alternativas = candidates[candidates['Region_Logica'] == region_actual].index
        #actualizamos los indices y puntuacion en caso de encontrar una mejor
        mejor_idx_local = idx_actual
        mejor_score_local = score_actual
        
        #Prueba cada alternativo de la región.
        for alt in alternativas:
            if alt == idx_actual: 
                continue #Evita compararse consigo mismo.
                
            #Crea una solución temporal reemplazando el candidato actual.
            solucion_temp = solucion_indices.copy()
            solucion_temp[i] = alt
            
            #Evalúa el score de la solución temporal.
            nuevo_score = calcular_score_total_cubierto(solucion_temp)
    
            #Si el alternativo mejora el score, lo guarda como el mejor local.
            if nuevo_score > mejor_score_local:
                mejor_score_local = nuevo_score
                mejor_idx_local = alt
        
        #Si se encontró un mejor candidato para esta posición.
        if mejor_idx_local != idx_actual:
            #Actualiza la solución global.
            solucion_indices[i] = mejor_idx_local
            #Actualiza el score global.
            score_actual = mejor_score_local
            #Indica que hubo una mejora.
            mejora = True
#'solucion_indices' contiene los índices de los helipuertos seleccionados

# ==========================================
# 5. ANÁLISIS DE RESULTADOS
# ==========================================
#guardo los candidatos con mejor score de cada region y los guardo
bases_finales = candidates.iloc[solucion_indices].copy().sort_values('Region_Logica')

#guarda los tiempos a las bases seleccionadas
tiempos_elegidos = tiempos_min[:, solucion_indices]
#calculamos el tiempo minimo de cada municipio a su base mas cercana
min_tiempos = np.min(tiempos_elegidos, axis=1)

# crea una lista de true o false de todos los municipios si quedan en el radio de cobertura de 30m
cubiertos_30_bool = min_tiempos <= TIEMPO_COBERTURA_MAX

#suma la score de prioridad de todos los municipios en el rango
score_cubierto_30 = demand.loc[cubiertos_30_bool, 'Score_Prioridad'].sum()
#suma la poblacion que vive en el radio
pop_cubierta_30 = demand.loc[cubiertos_30_bool, 'Población'].sum()

#hace lo mismo con 15minutos
cubiertos_15_bool = min_tiempos <= TIEMPO_ACCION_IDEAL
score_cubierto_15 = demand.loc[cubiertos_15_bool, 'Score_Prioridad'].sum()
pop_cubierta_15 = demand.loc[cubiertos_15_bool, 'Población'].sum()

#suma el score de todos los municipios de cyl
total_score = demand['Score_Prioridad'].sum()

#suma la poblacion de toda cyl
total_pop = demand['Población'].sum()


print(f"UBICACIÓN ÓPTIMA DE BASES ")

# junto todas las columnas que me interesan
cols_mostrar = ['Municipio', 'Provincia', 'Region_Logica', 'Población', 'Score_Prioridad', 'Distancia_Hospital_Min']

print(bases_finales[cols_mostrar].round(3).to_string(index=False))
print(f"Métricas Globales (Total Score Prioridad: {total_score:.2f})")
print(f" > Cobertura Operativa (30 min):")
print(f"   - Score Prioridad Cubierto: {score_cubierto_30:.2f} ({score_cubierto_30/total_score:.2%}) ")
print(f"   - Población Cubierta:       {pop_cubierta_30:,.0f} ({pop_cubierta_30/total_pop:.2%})")
print(f"\n > Cobertura Excelencia (15 min):")
print(f"   - Score Prioridad Cubierto: {score_cubierto_15:.2f} ({score_cubierto_15/total_score:.2%})")
print(f"   - Población Cubierta:       {pop_cubierta_15:,.0f} ({pop_cubierta_15/total_pop:.2%})")

#exporto los datos de las bases a un csv final
bases_finales.to_csv('solucion_prioridad_optima.csv', index=False)
print("csv final 'solucion_prioridad_optima.csv' guardado.")


# ==========================================
# 6. funciones generacion de graficos
# ==========================================
def generar_grafico_pesos():
    """
    Genera y guarda un gráfico circular (pie chart) visualizando 
    la distribución de pesos de las variables del modelo.
    """
    # Definición de etiquetas y pesos (basado en tu configuración)
    labels = [
        'Accidentes Ctra.', 
        'Dificultad Acceso', 
        'Densidad Pob.', 
        'Centro Salud', 
        'Transplantes', 
        'Cobertura 4G'
    ]
    sizes = [0.20, 0.43, 0.15, 0.15, 0.02, 0.05] # Deben sumar 1.0     
    
    # Colores para diferenciar categorías
    colors = ['#ff6666', '#ffcc99', '#99ff99', '#66b3ff', '#c2c2f0', '#ffb3e6']
    explode = (0.05, 0.05, 0, 0, 0, 0)  # Destacar ligeramente las dos más importantes

    plt.figure(figsize=(10, 7))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=140)
    
    plt.title('Ponderación de Variables en el Índice de Prioridad (IP)', fontsize=14, fontweight='bold')
    plt.axis('equal')  # Asegura que el pastel sea un círculo perfecto

    # Guardar gráfico
    nombre_archivo = 'pesos_modelo_multicriterio.png'
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    print(f"Gráfico de pesos generado correctamente: {nombre_archivo}")
    plt.close()
generar_grafico_pesos()

# ==========================================
# 7. grafico de radio 30km
# ==========================================

# 1. Crear el mapa base centrado en Castilla y León
# Coordenadas aprox del centro de CyL (Tordesillas/Valladolid)
mapa_cyl = folium.Map(location=[41.65, -4.72], zoom_start=8, tiles='CartoDB positron')

# 2. Capa de Municipios (Puntos pequeños de fondo)
# Iteramos sobre todo el dataframe 'demand'
for index, row in demand.iterrows():
    # Solo pintamos si tenemos coordenadas válidas
    if pd.notnull(row['Latitud']) and pd.notnull(row['Longitud']):
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=2, # Puntos pequeños
            color='blue', # Azul claro
            fill=True,
            fill_color='blue',
            popup=f"{row['Municipio']} (Pob: {row['Población']})",
            fill_opacity=0.4
        ).add_to(mapa_cyl)

# 3. Capa de BASES SELECCIONADAS (Marcadores grandes Rojos)
for index, row in bases_finales.iterrows():
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=folium.Popup(f"<b>BASE: {row['Municipio']}</b><br>Provincia: {row['Provincia']}", max_width=300),
        tooltip=f"Base {row['Municipio']}",
        icon=folium.Icon(color='red', icon='info-sign', prefix='glyphicon')
    ).add_to(mapa_cyl)
    
    # OPCIONAL: Dibujar el radio de cobertura (30 min ~ 110km aprox a 220km/h)
    # Ajusta el radio en metros según tu velocidad real. 
    # Ejemplo: 30 min a 220km/h = 110 km = 110,000 metros
    radio_metros = (VELOCIDAD_HELICOPTERO * (TIEMPO_COBERTURA_MAX/60)) * 1000
    
    folium.Circle(
        location=[row['Latitud'], row['Longitud']],
        radius=radio_metros,
        color='red',
        fill=True,
        fill_opacity=0.1
    ).add_to(mapa_cyl)

# 4. Guardar el mapa
archivo_mapa = 'mapa_cobertura_helicopteros.html'
mapa_cyl.save(archivo_mapa)
print(f"Mapa guardado correctamente como: '{archivo_mapa}'")

# ==========================================
# 7. grafico de radio 15km
# ==========================================

# 1. Crear el mapa base centrado en Castilla y León
# Coordenadas aprox del centro de CyL (Tordesillas/Valladolid)
mapa_cyl = folium.Map(location=[41.65, -4.72], zoom_start=8, tiles='CartoDB positron')

# 2. Capa de Municipios (Puntos pequeños de fondo)
# Iteramos sobre todo el dataframe 'demand'
for index, row in demand.iterrows():
    # Solo pintamos si tenemos coordenadas válidas
    if pd.notnull(row['Latitud']) and pd.notnull(row['Longitud']):
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=2, # Puntos pequeños
            color='blue', # Azul claro
            fill=True,
            fill_color='blue',
            popup=f"{row['Municipio']} (Pob: {row['Población']})",
            fill_opacity=0.4
        ).add_to(mapa_cyl)

# 3. Capa de BASES SELECCIONADAS (Marcadores grandes Rojos)
for index, row in bases_finales.iterrows():
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=folium.Popup(f"<b>BASE: {row['Municipio']}</b><br>Provincia: {row['Provincia']}", max_width=300),
        tooltip=f"Base {row['Municipio']}",
        icon=folium.Icon(color='red', icon='info-sign', prefix='glyphicon')
    ).add_to(mapa_cyl)
    
    # OPCIONAL: Dibujar el radio de cobertura (30 min ~ 110km aprox a 220km/h)
    # Ajusta el radio en metros según tu velocidad real. 
    # Ejemplo: 30 min a 220km/h = 110 km = 110,000 metros
    radio_metros = (VELOCIDAD_HELICOPTERO * (TIEMPO_ACCION_IDEAL/60)) * 1000
    
    folium.Circle(
        location=[row['Latitud'], row['Longitud']],
        radius=radio_metros,
        color='yellow',
        fill=True,
        fill_opacity=0.2
    ).add_to(mapa_cyl)
    radio_metros = (VELOCIDAD_HELICOPTERO * (TIEMPO_COBERTURA_MAX/60)) * 1000
    folium.Circle(
        location=[row['Latitud'], row['Longitud']],
        radius=radio_metros,
        color='red',
        fill=True,
        fill_opacity=0.05
    ).add_to(mapa_cyl)

# 4. Guardar el mapa
archivo_mapa = 'mapa_cobertura_helicopteros_15.html'
mapa_cyl.save(archivo_mapa)
print(f"Mapa guardado correctamente como: '{archivo_mapa}'")


# ==========================================
# 8. grafico de municipios
# ==========================================


# 1. Crear el mapa base centrado en Castilla y León
# Coordenadas aprox del centro de CyL (Tordesillas/Valladolid)
mapa_cyl = folium.Map(location=[41.65, -4.72], zoom_start=8, tiles='CartoDB positron')

# 2. Capa de Municipios (Puntos pequeños de fondo)
# Iteramos sobre todo el dataframe 'demand'
for index, row in demand.iterrows():
    # Solo pintamos si tenemos coordenadas válidas
    if pd.notnull(row['Latitud']) and pd.notnull(row['Longitud']):
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=2, # Puntos pequeños
            color='blue', # Azul claro
            fill=True,
            fill_color='blue',
            popup=f"{row['Municipio']} (Pob: {row['Población']}) Longitud:{row['Longitud']} Latitud:{row['Latitud']}",
            fill_opacity=0.4
        ).add_to(mapa_cyl)



# 4. Guardar el mapa
archivo_mapa = 'mapa_cobertura_helicopteros_municipios.html'
mapa_cyl.save(archivo_mapa)
print(f"Mapa guardado correctamente como: '{archivo_mapa}'")


# ===========================================================
# 9. grafico de radio municipios con dificultad de acceso>0.5
# ============================================================



# 1. Crear el mapa base centrado en Castilla y León
# Coordenadas aprox del centro de CyL (Tordesillas/Valladolid)
mapa_cyl = folium.Map(location=[41.65, -4.72], zoom_start=8, tiles='CartoDB positron')

# 2. Capa de Municipios (Puntos pequeños de fondo)
# Iteramos sobre todo el dataframe 'demand'
for index, row in demand.iterrows():
    # Solo pintamos si tenemos coordenadas válidas
    if pd.notnull(row['Latitud']) and pd.notnull(row['Longitud']) and (row['Dificultad_Acceso_Norm'])>0.5:
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=2, # Puntos pequeños
            color='blue', # Azul claro
            fill=True,
            fill_color='blue',
            popup=f"{row['Municipio']} (Pob: {row['Población']}) Longitud:{row['Longitud']} Latitud:{row['Latitud']}",
            fill_opacity=0.4
        ).add_to(mapa_cyl)



# 4. Guardar el mapa
archivo_mapa = 'mapa_cobertura_helicopteros_municipios_difi_acceso.html'
mapa_cyl.save(archivo_mapa)
print(f"Mapa guardado correctamente como: '{archivo_mapa}'")










"""
NOTAS: 
Bierzo, Villafranca del bierzo, puebla de sanabria,cuellar se repite en multiples experimentos

#Villablino tiene helipuerto
"""