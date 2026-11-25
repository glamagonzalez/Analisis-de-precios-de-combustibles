# Analisis de precios de combustibles

Proyecto de practica profesionalizante basado en datos oficiales de precios en surtidor de Argentina. Aplica la metodologia CRISP-DM para analizar el mercado, desarrollar modelos de regresion y clasificacion, evaluar los resultados y presentar un dashboard interactivo.

## Objetivos

- Analizar la evolucion de precios por producto, bandera, provincia y region.
- Comparar la participacion observada por estaciones unicas.
- Estimar el precio mediante un modelo de regresion.
- Clasificar estaciones como Cara o Barata.
- Generar una proyeccion de 2027 claramente identificada como estimacion.

## Particion temporal

| Periodo | Uso |
|---|---|
| 2024-2025 | Entrenamiento |
| 2025 | Validacion temporal |
| 2026 | Evaluacion con datos disponibles |
| 2027 | Pronostico, sin precios reales |

La cobertura de 2026 es incompleta y desigual. Las cifras de participacion no deben presentarse como participacion real del mercado argentino.

## Metodologia

El trabajo sigue las seis fases de CRISP-DM:

1. Comprension del negocio.
2. Comprension de los datos.
3. Preparacion de los datos.
4. Modelado.
5. Evaluacion.
6. Implementacion y monitoreo.

## Modelos

- Random Forest Regressor para estimar `precio`.
- Random Forest Classifier para clasificar `Cara` o `Barata`.
- Baseline de mediana para regresion.
- Baseline de clase mas frecuente para clasificacion.

Las metricas y predicciones se generan de forma temporal para evitar mezclar datos futuros en el entrenamiento.

## Resultados principales

- Validacion 2025: MAE del Random Forest de 236,11 frente a 330,97 del baseline.
- Evaluacion 2026: MAE del Random Forest de 712 frente a 844,82 del baseline.
- Exactitud de clasificacion en 2026: 61,38 %.
- F1 de la clase Cara: 75,46 %.
- AUC: 82,67 %.
- R2 de la regresion en 2026: -0,7165. Un R2 negativo indica que el modelo de
  regresion no supera una prediccion simple basada en el promedio.

Estos resultados deben interpretarse junto con las limitaciones de cobertura de 2026.

## Pruebas

```powershell
python -m pytest -q
```

## Dashboard

Instalar las dependencias:

```powershell
python -m pip install -r requirements_dashboard.txt
```

Ejecutar:

```powershell
streamlit run dashboard_ypf.py
```

Abrir `http://localhost:8501`.

## Archivos principales

- `generar_datasets_modelos.py`: limpieza, datasets y modelos.
- `dashboard_ypf.py`: dashboard interactivo.
- `Informe_entrega_PRP.md`: informe organizado segun CRISP-DM.
- `precios-en-surtidor-resolucin-3142016.csv`: archivo fuente.
- `modelos_y_datos/`: datasets, modelos y resultados.
- `Analisis_Combustibles.ipynb`: analisis exploratorio original.
- `Analisis_Combustibles (2).ipynb`: copia equivalente del analisis.

## Limitaciones

- 2026 no esta completo.
- La proyeccion 2027 no contiene precios observados.
- El modelo no incorpora inflacion, impuestos, subsidios, devaluacion ni regulaciones oficiales.
- Las participaciones se calculan sobre estaciones unicas de la muestra.
- YPF se destaca como actor estatal estrategico dentro del analisis, pero el proyecto no demuestra por si solo su liderazgo nacional sin datos completos y representativos.
