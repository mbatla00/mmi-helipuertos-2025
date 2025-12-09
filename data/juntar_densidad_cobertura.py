import pandas as pd

# Cargar los archivos
df_municipios = pd.read_csv('new_municipios.csv')
df_demanda = pd.read_csv('datos_demanda_final_scaled.csv')

# Normalizar nombres para asegurar el cruce (mayúsculas y espacios)
df_municipios['Municipio_join'] = df_municipios['Municipio'].str.upper().str.strip()
df_municipios['Provincia_join'] = df_municipios['Provincia'].str.upper().str.strip()

df_demanda['Municipio_join'] = df_demanda['NOMBRE_ACTUAL'].str.upper().str.strip()
df_demanda['Provincia_join'] = df_demanda['PROVINCIA'].str.upper().str.strip()

# Convertir DENSIDADMM a numérico si es necesario (parece tener coma decimal)
df_demanda['DENSIDADMM'] = df_demanda['DENSIDADMM'].astype(str).str.replace(',', '.').astype(float)

# Realizar el merge (unión)
# Usamos left join para mantener todos los registros de new_municipios
df_final = pd.merge(
    df_municipios,
    df_demanda[['Municipio_join', 'Provincia_join', 'DENSIDADMM', '4G']],
    on=['Municipio_join', 'Provincia_join'],
    how='left'
)

# Eliminar columnas auxiliares usadas para el join
df_final = df_final.drop(columns=['Municipio_join', 'Provincia_join'])

# Guardar el resultado
df_final.to_csv('new_municipios_completo.csv', index=False)

# Mostrar las primeras filas para verificar
print(df_final.head())
print(df_final.info())