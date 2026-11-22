# Proyecto de Analisis y Exploracion de Datos

## 1. Comprension del negocio

El objetivo es analizar precios minoristas de combustibles en Argentina y estimar si una estacion comercializa un producto a precio Cara o Barata. El proyecto puede apoyar comparaciones entre banderas, regiones y productos.

Objetivos tecnicos:

- Estimar el precio futuro de una estacion.
- Clasificar una observacion como Cara o Barata.
- Comparar los modelos con referencias simples.
- Diferenciar datos observados de pronosticos.

Criterios de exito:

- El modelo supera al baseline.
- Las metricas se calculan con particion temporal.
- Las limitaciones y la cobertura se documentan.
- Los resultados pueden reproducirse ejecutando un script.

## 2. Comprension de los datos

La fuente es el CSV oficial de precios en surtidor. El proyecto utiliza bandera, direccion, localidad, provincia, region, producto, horario, fecha y precio.

Se verificaron:

- Precios no numericos.
- Valores faltantes.
- Fechas incompletas.
- Bandera SIN EMPRESA BANDERA.
- Posibles duplicados.
- Cobertura mensual desigual.

2026 tiene nueve meses disponibles y cobertura irregular. Por esa razon no representa una medicion completa del mercado.

## 3. Preparacion

Se realizaron las siguientes transformaciones:

- Conversion del precio a numero.
- Conversion de `indice_tiempo` a fecha.
- Creacion de `anio` y `mes`.
- Eliminacion de precios menores a 50 o mayores a 10000.
- Eliminacion de registros sin variables esenciales.
- Eliminacion de duplicados por estacion, producto, horario y fecha.
- Codificacion one-hot de variables categoricas.

Los archivos finales quedan en `modelos_y_datos`.

## 4. Modelado

Se utilizo Random Forest por su capacidad de representar relaciones no lineales y manejar variables categoricas codificadas.

Regresion:

- Objetivo: `precio`.
- Baseline: mediana del conjunto de entrenamiento.
- Modelo: Random Forest Regressor.
- Metricas: MAE, RMSE y R2.

Clasificacion:

- Objetivo: `clase`.
- Cara: precio superior a la mediana de referencia.
- Baseline: clase mas frecuente.
- Modelo: Random Forest Classifier.
- Metricas: Accuracy, Precision, Recall, F1 y AUC.

## 5. Evaluacion

La particion es temporal:

- Entrenamiento: 2024-2025.
- Evaluacion: datos reales disponibles de 2026.
- Pronostico: 2027.

Los resultados exactos se encuentran en `resumen.json` y `predicciones_evaluacion_2026.csv`.

Resultados actuales:

- Validacion 2025: el MAE del Random Forest fue 236,11 frente a 330,97 del baseline.
- Evaluacion 2026: el MAE fue 712 frente a 844,82 del baseline.
- El RMSE de 2026 fue 763,94.
- La exactitud de clasificacion fue 61,38 %.
- El F1 de la clase Cara fue 75,46 %.
- El AUC fue 82,67 %.

El cambio de rendimiento entre 2025 y 2026 muestra deriva temporal y confirma que el dataset 2026 no puede considerarse una continuacion estable del anterior.

## 6. Pronostico 2027

El archivo `proyeccion_2027.csv` contiene combinaciones de banderas, provincias, productos y horarios observados en periodos recientes. Son estimaciones del modelo, no precios reales.

No incluye factores que pueden cambiar el precio, como subsidios, impuestos, devaluacion, importaciones o regulaciones oficiales.

## 7. Limitaciones

- 2026 tiene cobertura incompleta.
- La cobertura mensual no es homogenea.
- La participacion por bandera no representa el mercado completo.
- El modelo puede perder precision ante cambios de estructura.
- Random Forest no permite extrapolar tendencias economicas fuera de los valores vistos.
- No se incorporaron variables externas de inflacion o costos.

## 8. Monitoreo y mantenimiento

Al recibir datos nuevos:

- Validar tipos, fechas y rangos.
- Comparar distribuciones contra entrenamiento.
- Recalcular metricas mensualmente.
- Reentrenar cuando el MAE o el F1 empeoren.
- Revisar si aparecen nuevas banderas o productos.
- Mantener separadas observaciones reales y pronosticos.

## 9. Proximos pasos

- Incorporar 2026 completo.
- Agregar datos macroeconomicos y precio internacional.
- Probar Gradient Boosting.
- Evaluar intervalos de prediccion.
- Crear dashboard mensual.
- Aplicar validacion temporal rolling-origin.
