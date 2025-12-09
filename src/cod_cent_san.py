# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 17:06:16 2025

@author: Usuario
"""

import pandas as pd

centros = pd.read_csv("centros-sanitarios-cyl.csv", sep=";")
municipios = pd.read_csv("registro-de-municipios.csv", sep=";")
CP = pd.read_csv("codigos_postales_municipales.csv")


centros_por_cp = centros.groupby("Código postal").size().reset_index(name="num_centros_cp")
#print(centros_por_cp)

centros_por_cp = centros_por_cp.rename(columns={"Código postal": "codigo_postal"})

# En la tabla de centros
centros_por_cp["codigo_postal"] = (
    centros_por_cp["codigo_postal"]
    .astype(float)      # por si viene mezclado
    .astype(int)        # quita los decimales
    .astype(str)        # lo pasa a texto
    .str.zfill(5)       # asegura formato 5 dígitos (opcional pero recomendado)
)

CP["codigo_postal"] = (
    CP["codigo_postal"]
    .astype(str)
    .str.strip()
    .str.zfill(5)
)


centros_cp_muni = centros_por_cp.merge(CP, on="codigo_postal", how="left")

#print(centros_cp_muni)

centros_cp_muni = centros_cp_muni.dropna(subset=["nombre"])

#centros_por_muni = centros_cp_muni.groupby("nombre")["num_centros_cp"].sum().reset_index()

centros_por_muni = centros_cp_muni[["nombre", "num_centros_cp"]].copy()

centros_por_muni = (
    centros_por_muni
    .groupby("nombre", as_index=False)["num_centros_cp"]
    .sum()
)

#print(centros_por_muni.head())

import unidecode

def normalizar(nombre):
    if pd.isna(nombre):
        return ""
    nombre = nombre.lower()                 # minúsculas
    nombre = unidecode.unidecode(nombre)    # quitar acentos
    nombre = nombre.replace(",", " ")       # quitar comas
    nombre = nombre.replace(".", " ")
    nombre = nombre.replace("(", "").replace(")", "")
    nombre = " ".join(nombre.split())       # quitar dobles espacios
    return nombre

centros_por_muni["muni_norm"] = centros_por_muni["nombre"].apply(normalizar)
municipios["muni_norm"] = municipios["Municipio"].apply(normalizar)

municipios_merge = municipios.merge(
    centros_por_muni[["muni_norm", "num_centros_cp"]],
    on="muni_norm",
    how="left"
)

municipios_merge["num_centros_cp"] = municipios_merge["num_centros_cp"].fillna(0).astype(int)

municipios_merge["tiene_centro"] = (municipios_merge["num_centros_cp"] > 0).astype(int)

municipios_merge = municipios_merge.drop(columns=["Cod_INE", "Mancomunidades", "Entidades_Locales_Menores", "Comarca", "num_centros_cp", "muni_norm"])

municipios_merge.to_csv("new_municipios.csv", index=False)
