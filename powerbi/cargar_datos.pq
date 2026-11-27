// POWER BI - Power Query (Inicio > Transformar datos > Nuevo origen > Consulta en blanco > Editor avanzado)
// 1) Crear un parametro de texto llamado RutaProyecto, p. ej.:  C:\Proyecto\Analisis-de-precios-de-combustibles\powerbi\
// 2) Crear una consulta "fnCargarCsv" con este codigo y luego una consulta por cada tabla (lineas de abajo).

// ---- Consulta: fnCargarCsv ----
(nombreArchivo as text) as table =>
let
    Origen = Csv.Document(File.Contents(RutaProyecto & nombreArchivo),
                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true])
in
    Encabezados

// ---- Una consulta por tabla (cada una en su propia consulta) ----
// fact_precios:           = fnCargarCsv("fact_precios.csv")
// predicciones:           = fnCargarCsv("predicciones.csv")
// proyeccion_2027:        = fnCargarCsv("proyeccion_2027.csv")
// cobertura_mensual:      = fnCargarCsv("cobertura_mensual.csv")
// participacion_banderas: = fnCargarCsv("participacion_banderas.csv")
// metricas:               = fnCargarCsv("metricas.csv")
// matriz_confusion:       = fnCargarCsv("matriz_confusion.csv")
// importancia_variables:  = fnCargarCsv("importancia_variables.csv")
// bitacora_limpieza:      = fnCargarCsv("bitacora_limpieza.csv")
// ypf_vs_resto_celdas:                  = fnCargarCsv("ypf_vs_resto_celdas.csv")
// ypf_vs_resto_resumen:                 = fnCargarCsv("ypf_vs_resto_resumen.csv")
// ypf_vs_resto_region_anio:             = fnCargarCsv("ypf_vs_resto_region_anio.csv")
// ypf_muestra_estaciones_region_mes:    = fnCargarCsv("ypf_muestra_estaciones_region_mes.csv")
// ypf_clasificacion_region_2026:        = fnCargarCsv("ypf_clasificacion_region_2026.csv")
// auditoria_cobertura:                  = fnCargarCsv("auditoria_cobertura.csv")
// auditoria_indicadores:                = fnCargarCsv("auditoria_indicadores.csv")
// auditoria_region_conjunto:            = fnCargarCsv("auditoria_region_conjunto.csv")
// auditoria_bandera_conjunto:           = fnCargarCsv("auditoria_bandera_conjunto.csv")
// auditoria_controles:                  = fnCargarCsv("auditoria_controles.csv")

// ---- Tipos de datos (aplicar en cada consulta con "Cambiar tipo" o con Table.TransformColumnTypes) ----
// Fechas  : fecha_mes                                  -> Fecha (usar configuracion regional Ingles (EE. UU.) al convertir)
// Decimal : precio, precio_referencia, precio_relativo, precio_predicho, precio_predicho_indice_conocido,
//           precio_relativo_predicho, error, probabilidad_cara, precio_referencia_proyectado, valor, participacion_pct
// Entero  : anio, mes, idempresa, clase, clase_predicha, registros, estaciones, cantidad
