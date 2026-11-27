# Guia para armar el tablero en Power BI Desktop

## 1. Cargar los datos (10-15 min)
1. Inicio > Obtener datos > Texto/CSV, o usar `cargar_datos.pq` con el parametro `RutaProyecto`.
2. Cargar las 19 tablas: `fact_precios`, `predicciones`, `proyeccion_2027`, `cobertura_mensual`, `participacion_banderas` (solo referencia),
   `metricas`, `matriz_confusion`, `importancia_variables`, `bitacora_limpieza` y las cinco de YPF: `ypf_vs_resto_celdas`,
   `ypf_vs_resto_resumen`, `ypf_vs_resto_region_anio`, `ypf_muestra_estaciones_region_mes`, `ypf_clasificacion_region_2026` y las cinco de auditoria (`auditoria_*`).
3. Verificar tipos (fechas, decimales con punto) y que `fecha_mes` sea Fecha.

## 2. Modelo (10 min)
Crear las tablas `dim_fecha`, `dim_producto`, `dim_bandera`, `dim_provincia` y las relaciones indicadas en `medidas_DAX.txt`.
Crear las medidas del mismo archivo (carpeta de medidas: Datos, Regresion, Clasificacion, Proyeccion).

## 3. Paginas sugeridas
| Pagina | Visuales | Mensaje |
|---|---|---|
| 1. Resumen | Tarjetas (registros, estaciones, MAE, Exactitud), linea de precio mediano por producto | Vision general y alcance |
| 2. Calidad de datos | Columnas de `cobertura_mensual` (colorear por `etapa`), tabla `bitacora_limpieza`, `auditoria_cobertura` (surtidores por conjunto) y `auditoria_controles` | Por que 2026 no se usa para entrenar |
| 3. Regresion | Dispersion precio vs precio_predicho (filtro conjunto = Evaluacion 2026), tarjetas MAE/RMSE/R2, tabla `metricas` | El modelo supera a los baselines |
| 4. Clasificacion | Matriz (`matriz_confusion`), tarjetas Exactitud/Precision/Recall/F1, barras de `importancia_variables` | Capacidad de separar Cara/Barata |
| 5. Proyeccion 2027 | Linea de `precio_predicho` por mes y producto + cuadro de texto con la medida `Aviso` | Escenario, no dato oficial |
| 6. YPF vs mercado (pagina principal del analisis) | Barras de `dif_pct` con `ic95_inf/ic95_sup` por region, producto y anio (`ypf_vs_resto_resumen`); mapa de calor region x anio (`ypf_vs_resto_region_anio`); linea de `% estaciones YPF en muestra`; tabla de `ypf_clasificacion_region_2026`; cuadro con `Aviso YPF` | YPF informa precios menores en 2025; en 2026 no se distingue de cero |

Segmentadores sincronizados: Producto, Region, Bandera, Provincia, Conjunto. En la pagina 6 evitar mostrar participacion de mercado: la muestra cambia entre meses.

## 4. Publicar
Guardar el `.pbix` en el repositorio (o exportar PDF desde Archivo > Exportar) y actualizar con "Actualizar" si se regeneran los CSV.
