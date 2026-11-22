# Datos y modelos para 2024-2027

## Generacion

Ejecutar desde esta carpeta:

```powershell
python .\generar_datasets_modelos.py
```

## Archivos

- `regresion_2024_2025.csv`: datos reales usados para entrenar el modelo de regresion.
- `clasificacion_2024_2025.csv`: datos reales 2024-2025 con clase Cara/Barata.
- `regresion_evaluacion_2026.csv`: datos reales disponibles de 2026.
- `clasificacion_evaluacion_2026.csv`: datos reales disponibles de 2026 con su clase.
- `predicciones_evaluacion_2026.csv`: precio real, precio estimado y clase estimada para 2026.
- `proyeccion_2027.csv`: combinaciones futuras con precio predicho y clase estimada.
- `modelo_regresion.joblib`: modelo Random Forest de regresion.
- `modelo_clasificacion.joblib`: modelo Random Forest de clasificacion.
- `resumen.json`: cantidades y metricas principales.

## Criterios

- El objetivo de regresion es `precio`.
- En clasificacion, Cara = precio superior a la mediana de 2025 correspondiente a producto y mes.
- Los modelos se entrenaron exclusivamente con datos reales 2024-2025.
- 2026 se usa como evaluacion. No constituye una muestra completa del mercado.
- 2027 es una proyeccion basada en combinaciones observadas de 2025-2026.
- El archivo de 2027 no contiene precios reales.
- La evaluacion incluye baseline de mediana para regresion y baseline de clase mas frecuente para clasificacion.
- La clasificacion de 2026 usa como referencia la mediana de 2025 para evitar utilizar informacion futura.
- El dashboard interactivo se ejecuta con `streamlit run dashboard_ypf.py`.
