import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

"""
INFORME SOBRE EL PROCESADO DE LA COLUMNA ACCIDENTES:

Hemos sacado el dataset de accidentalidad-por-carreteras de
https://datosabiertos.jcyl.es/web/jcyl/set/es/transporte/accidentalidad-carreteras/1284967604431
Para cada accidente registrado, el programa analiza la descripción textual del tramo 
(por ejemplo, "DE BU-550 A MEDINA DE POMAR (N-629)") y busca coincidencias con los nombres 
de municipios mediante comparación de cadenas de texto en mayúsculas.

Cuando encuentra uno o varios municipios mencionados en la descripción del accidente, 
calcula un "peso de gravedad" basado en una fórmula que pondera diferentes variables: 
asigna mayor valor a los fallecidos (coeficiente 1.0), seguido de heridos (0.5) y accidentes con 
víctimas (0.3), garantizando que incluso accidentes sin víctimas reciban un peso mínimo (0.1) 
para mantenerlos en el análisis. Este peso total se distribuye equitativamente entre todos 
los municipios identificados en ese tramo.

Para los casos donde ningún municipio aparece explícitamente en la descripción, el script 
implementa un mecanismo de fallback: extrae el código provincial de la carretera 
(como "BU" de "BU-551"), lo mapea a una provincia completa ("Burgos") y distribuye el peso entre 
todos los municipios de esa provincia, asegurando que ningún accidente quede sin asignación.

Finalmente, una vez acumulados todos los pesos brutos por municipio, el script normaliza 
los valores a un rango entre 0 y 1 usando MinMaxScaler, donde 0 representa el municipio con 
menor exposición a accidentes y 1 el de mayor exposición, añadiendo esta nueva métrica como 
columna "Accidentes_Por_Carretera" al dataset original de municipios, listo para ser 
integrado en modelos predictivos de demanda hospitalaria

"""

def cargar_datos():
    """Carga los archivos CSV"""
    try:
        municipios = pd.read_csv(
            'registro-de-municipios-de-castilla-y-leon.csv', 
            sep=';'
        )
        accidentes = pd.read_csv(
            'data/accidentalidad-por-carreteras.csv', 
            sep=';',
            decimal=','
        )
        return municipios, accidentes
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Asegúrate de que los archivos están en la carpeta 'data/'")
        return None, None

def asignar_accidentes_a_municipios(municipios_df, accidentes_df):
    """
    Asigna accidentes a municipios basándose en coincidencias de nombres
    y normaliza el resultado entre 0 y 1
    """
    # Hacer copia para no modificar el original
    municipios = municipios_df.copy()
    
    # Inicializar la columna de accidentes
    municipios['Accidentes_Raw'] = 0.0
    
    # Crear diccionario de búsqueda (municipio en mayúsculas)
    municipios_upper = {muni.upper(): idx 
                       for idx, muni in enumerate(municipios['Municipio'])}
    
    # Procesar cada accidente
    for _, acc in accidentes_df.iterrows():
        descripcion = str(acc['DESCRIPCIÓN']).upper()
        
        # Calcular peso del accidente
        heridos = float(acc['HERIDOS']) if pd.notna(acc['HERIDOS']) else 0
        muertos = float(acc['MUERTOS']) if pd.notna(acc['MUERTOS']) else 0
        acv = float(acc['ACV']) if pd.notna(acc['ACV']) else 0
        
        peso_accidente = (heridos * 0.5 + muertos * 1.0 + acv * 0.3)
        if peso_accidente == 0:
            peso_accidente = 0.1  # Valor mínimo
        
        # Buscar municipios en la descripción
        municipios_encontrados = []
        
        for muni_nombre, muni_idx in municipios_upper.items():
            if muni_nombre in descripcion:
                municipios_encontrados.append(muni_idx)
        
        # Si encontramos municipios, distribuir el peso
        if municipios_encontrados:
            peso_por_municipio = peso_accidente / len(municipios_encontrados)
            for idx in municipios_encontrados:
                municipios.at[idx, 'Accidentes_Raw'] += peso_por_municipio
        else:
            # Si no encontramos, intentar por código de provincia
            codigo_carretera = str(acc['NOMBRE'])
            if '-' in codigo_carretera:
                cod_prov = codigo_carretera.split('-')[0]
                
                # Mapeo de códigos a provincias
                codigo_a_provincia = {
                    'BU': 'BURGOS', 'LE': 'LEÓN', 'SA': 'SALAMANCA',
                    'ZA': 'ZAMORA', 'VA': 'VALLADOLID', 'SO': 'SORIA',
                    'SG': 'SEGOVIA', 'AV': 'ÁVILA', 'P': 'PALENCIA'
                }
                
                if cod_prov in codigo_a_provincia:
                    provincia_nombre = codigo_a_provincia[cod_prov]
                    # Obtener índices de municipios de esa provincia
                    idxs_provincia = municipios[
                        municipios['Provincia'] == provincia_nombre
                    ].index.tolist()
                    
                    if idxs_provincia:
                        peso_por_municipio = peso_accidente / len(idxs_provincia)
                        for idx in idxs_provincia:
                            municipios.at[idx, 'Accidentes_Raw'] += peso_por_municipio
    
    # Normalizar a rango 0-1
    scaler = MinMaxScaler()
    valores_accidentes = municipios['Accidentes_Raw'].values.reshape(-1, 1)
    
    # Añadir columna normalizada
    municipios['Accidentes_Por_Carretera'] = scaler.fit_transform(valores_accidentes).flatten()
    
    # Redondear a 4 decimales para claridad
    municipios['Accidentes_Por_Carretera'] = municipios['Accidentes_Por_Carretera'].round(4)
    
    return municipios

def main():
    """Función principal"""
    print("Cargando datos...")
    municipios, accidentes = cargar_datos()
    
    if municipios is None or accidentes is None:
        return
    
    print(f"Municipios cargados: {len(municipios)}")
    print(f"Registros de accidentes: {len(accidentes)}")
    
    print("\nProcesando asignación de accidentes...")
    municipios_con_accidentes = asignar_accidentes_a_municipios(municipios, accidentes)
    
    # Mostrar algunos resultados
    print("\nPrimeros 10 municipios con índice de accidentes:")
    resultados = municipios_con_accidentes[
        ['Municipio', 'Provincia', 'Accidentes_Por_Carretera']
    ].sort_values('Accidentes_Por_Carretera', ascending=False).head(10)
    
    print(resultados.to_string(index=False))
    
    # Guardar el archivo actualizado
    output_path = 'registro-de-municipios-de-castilla-y-leon.csv'
    municipios_con_accidentes.to_csv(output_path, sep=';', index=False, encoding='utf-8')
    
    print(f"\nArchivo guardado en: {output_path}")
    print(f"Columna 'Accidentes_Por_Carretera' añadida con {len(municipios_con_accidentes)} registros")
    
    # Estadísticas
    print("\nEstadísticas del índice de accidentes:")
    print(f"Mínimo: {municipios_con_accidentes['Accidentes_Por_Carretera'].min():.4f}")
    print(f"Máximo: {municipios_con_accidentes['Accidentes_Por_Carretera'].max():.4f}")
    print(f"Promedio: {municipios_con_accidentes['Accidentes_Por_Carretera'].mean():.4f}")

if __name__ == "__main__":
    main()
