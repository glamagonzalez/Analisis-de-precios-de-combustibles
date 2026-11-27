# Analisis de precios de combustibles - Practica profesionalizante (ISFDyT 57)

Analisis de la bandera YPF frente al resto del mercado y por region, mas regresion y clasificacion (Random Forest) sobre el dataset oficial de precios en surtidor.
Entrenamiento 2024-2025, evaluacion con 2026 (parcial), escenario 2027. Entrega en Python, Orange y Power BI.

## Estructura
| Carpeta / archivo | Contenido |
|---|---|
| `precios-en-surtidor-resolucin-3142016.csv` | Dataset original (descarga actualizada) |
| `generar_datasets_modelos.py` | Limpieza con bitacora, recuperacion de precios mal formateados, modelos, validacion, proyeccion, comparacion YPF vs resto, auditoria y tablas de salida |
| `orange_resultados.py`, `generar_figuras.py` | Resultados de Orange por codigo y graficos del informe |
| `powerbi/` | CSV para Power BI + `cargar_datos.pq` + `medidas_DAX.txt` + `GUIA_POWERBI.md` |
| `orange/` | CSV para Orange (con la clase marcada como `c#`) |
| `Flujo_Orange_Combustibles.ows` | Flujo de Orange conectado (23 widgets, 28 conexiones) |
| `crear_flujo_orange.py` | Regenera el `.ows` |
| `modelos_y_datos/` | Modelos `.joblib`, `resumen.json`, `resultados_orange.json` |
| `figuras/` | Graficos del informe |
| `Informe_final_Proyecto_Combustibles.docx` | Informe de entrega |
| `crear_informe_final_word.py` | Regenera el informe |

## Reproducir
```bash
pip install pandas scikit-learn joblib python-docx matplotlib
python generar_datasets_modelos.py     # ~16 s: limpieza + modelos + tablas Power BI/Orange
pip install orange3 && python orange_resultados.py   # resultados de Orange
python generar_figuras.py              # graficos del informe
python crear_flujo_orange.py           # regenera el .ows
python crear_informe_final_word.py     # regenera el informe Word
```
Orange: abrir `Flujo_Orange_Combustibles.ows` (las rutas son relativas a la carpeta del proyecto).
Power BI: seguir `powerbi/GUIA_POWERBI.md`.

## Calidad de datos
- 398 precios del origen vienen mal formateados (ej. `13.700.000` = $1.370, casi todos Shell); se recuperan dividiendo por 10.000 y se validan contra la mediana de su producto y mes.
- `powerbi/auditoria_controles.csv` lista los controles de calidad y `auditoria_cobertura.csv` los surtidores por conjunto.

## Advertencias
- 2026 llega hasta septiembre con cobertura despareja: se usa solo para evaluar.
- 2027 es un escenario estadistico, no un dato real ni una prediccion oficial.
- La comparacion YPF vs resto se hace dentro de cada mes, producto y region; no es participacion de mercado (el peso de YPF en la muestra va de 3 % a 79 % segun el mes).
- La ventaja de precio de YPF esta respaldada en 2025; en 2026 hay pocos registros de YPF y la diferencia no se distingue de cero.
