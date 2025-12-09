import pandas as pd
import numpy as np
import unicodedata

# --- 1. DATOS DE REFERENCIA ---

# Municipios con Hospital (Listado oficial Sacyl/Ministerio)
municipios_con_hospital = [
    "AVILA", "AREVALO", 
    "BURGOS", "ARANDA DE DUERO", "MIRANDA DE EBRO", 
    "LEON", "PONFERRADA", "VILLABLINO", 
    "PALENCIA", 
    "SALAMANCA", 
    "SEGOVIA", 
    "SORIA", 
    "VALLADOLID", "MEDINA DEL CAMPO", 
    "ZAMORA", "BENAVENTE"
]

# Municipios con Unidad de Trasplantes
municipios_con_transplante = ["VALLADOLID", "SALAMANCA"]

# Coordenadas de Capitales (Para medir aislamiento)
capitales = {
    "AVILA": (40.65, -4.70), "BURGOS": (42.34, -3.70), "LEON": (42.60, -5.57),
    "PALENCIA": (42.01, -4.53), "SALAMANCA": (40.96, -5.66), "SEGOVIA": (40.94, -4.12),
    "SORIA": (41.76, -2.47), "VALLADOLID": (41.65, -4.72), "ZAMORA": (41.50, -5.75)
}

# --- 2. FUNCIONES AUXILIARES ---

def normalize_text(text):
    """Limpia tildes y mayúsculas para comparar nombres."""
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFD', text.upper()).encode('ascii', 'ignore').decode("utf-8").strip()

def haversine(lat1, lon1, lat2, lon2):
    """Calcula distancia en km (Fórmula Haversine)."""
    R = 6371 
    dlat, dlon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def get_geo_difficulty(row):
    """Devuelve un score de montaña (0.1 a 1.0) según coordenadas (Geofencing)."""
    lat, lon = row['Latitud'], row['Longitud']
    
    # Norte (Cordillera Cantábrica)
    if lat > 42.8: return 1.0
    # Oeste (Bierzo / Ancares)
    if lon < -6.2 and lat > 42.2: return 1.0
    # Noroeste Zamora (Sanabria)
    if lon < -6.2 and 41.8 < lat <= 42.2: return 0.9
    # Sur (Sistema Central: Gredos / Francia)
    if lat < 40.6: return 1.0
    # Este (Sistema Ibérico: Urbión / Demanda)
    if lon > -3.0 and lat > 41.7: return 0.9
    # Oeste (Arribes)
    if lon < -6.5: return 0.8
        
    return 0.1 # Meseta / Llano

def get_dist_score(row):
    """Calcula score de aislamiento (0 a 1) por distancia a capital."""
    prov = normalize_text(row['Provincia'])
    if prov in capitales:
        d = haversine(row['Latitud'], row['Longitud'], *capitales[prov])
        return min(d / 120.0, 1.0) # 120km es el tope para score máximo
    return 0

# --- 3. EJECUCIÓN PRINCIPAL ---

# Cargar
try:
    df = pd.read_csv("registro-de-municipios-de-castilla-y-leon.csv", sep=";", encoding="utf-8")
except:
    df = pd.read_csv("registro-de-municipios-de-castilla-y-leon.csv", sep=";", encoding="latin-1")

# Limpiar Coordenadas
df['Latitud'] = df['Latitud'].apply(lambda x: float(str(x).replace(',', '.')))
df['Longitud'] = df['Longitud'].apply(lambda x: float(str(x).replace(',', '.')))

# Crear Columnas Lógicas
df['Municipio_Norm'] = df['Municipio'].apply(normalize_text)
df['Tiene_Hospital'] = df['Municipio_Norm'].apply(lambda x: 1 if x in municipios_con_hospital else 0)
df['Transplantes'] = df['Municipio_Norm'].apply(lambda x: 1 if x in municipios_con_transplante else 0)
df.drop(columns=['Municipio_Norm'], inplace=True)

# Crear Columnas de Dificultad
# Fórmula: 70% Orografía + 30% Distancia Capital
df['Dificultad_Acceso'] = (df.apply(get_geo_difficulty, axis=1) * 0.7) + \
                          (df.apply(get_dist_score, axis=1) * 0.3)
df['Dificultad_Acceso'] = df['Dificultad_Acceso'].round(2)

# Guardar
output_file = "registro-de-municipios-de-castilla-y-leon.csv"
df.to_csv(output_file, sep=";", index=False, encoding="utf-8")

print(f"Proceso finalizado. Archivo guardado: {output_file}")