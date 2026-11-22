"""Dashboard interactivo del proyecto de precios de combustibles YPF."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "modelos_y_datos"

st.set_page_config(
    page_title="Combustibles - Analisis 2024-2027",
    page_icon="⛽",
    layout="wide",
)


@st.cache_data
def cargar_csv(nombre: str) -> pd.DataFrame:
    return pd.read_csv(DATOS / nombre)


historico = cargar_csv("regresion_2024_2025.csv")
evaluacion_2026 = cargar_csv("regresion_evaluacion_2026.csv")
predicciones_2026 = cargar_csv("predicciones_evaluacion_2026.csv")
pronostico_2027 = cargar_csv("proyeccion_2027.csv")

historico["tipo_periodo"] = "Real 2024-2025"
evaluacion_2026["tipo_periodo"] = "Real disponible 2026"
pronostico_2027["tipo_periodo"] = "Pronostico 2027"

historico["precio_predicho"] = pd.NA
evaluacion_2026["precio_predicho"] = predicciones_2026["precio_predicho"].values

st.title("Analisis de precios de combustibles")
st.caption(
    "Proyecto CRISP-DM - datos oficiales de surtidores. "
    "2026 tiene cobertura incompleta y 2027 es una proyeccion."
)

logo = AQUI / "logo_ypf.png"
if logo.exists():
    st.sidebar.image(str(logo), width="stretch")

st.sidebar.header("Filtros")

producto_opciones = sorted(historico["producto"].dropna().unique())
producto = st.sidebar.multiselect(
    "Producto",
    producto_opciones,
    default=[],
)

bandera_opciones = sorted(historico["empresabandera"].dropna().unique())
bandera = st.sidebar.multiselect(
    "Bandera",
    bandera_opciones,
    default=[],
)

provincia_opciones = sorted(historico["provincia"].dropna().unique())
provincia = st.sidebar.multiselect(
    "Provincia",
    provincia_opciones,
    default=[],
)


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.copy()
    if producto:
        resultado = resultado[resultado["producto"].isin(producto)]
    if bandera:
        resultado = resultado[resultado["empresabandera"].isin(bandera)]
    if provincia:
        resultado = resultado[resultado["provincia"].isin(provincia)]
    return resultado


hist_f = filtrar(historico)
eval_f = filtrar(evaluacion_2026)

pronostico_f = pronostico_2027.copy()
if producto:
    pronostico_f = pronostico_f[pronostico_f["producto"].isin(producto)]
if bandera:
    pronostico_f = pronostico_f[pronostico_f["empresabandera"].isin(bandera)]
if provincia:
    pronostico_f = pronostico_f[pronostico_f["provincia"].isin(provincia)]

tab_resumen, tab_tendencias, tab_modelos, tab_participacion = st.tabs([
    "Resumen",
    "Tendencias",
    "Modelos",
    "Participacion",
])

with tab_resumen:
    st.subheader("Vista general")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Filas reales 2024-2025", f"{len(hist_f):,}")
    col2.metric("Filas disponibles 2026", f"{len(eval_f):,}")
    col3.metric(
        "Precio medio 2024-2025",
        f"${hist_f['precio'].mean():,.2f}" if len(hist_f) else "-",
    )
    col4.metric(
        "Estaciones 2026",
        f"{eval_f['idempresa'].nunique():,}" if len(eval_f) else "-",
    )

    st.warning(
        "Los datos de 2026 presentan cobertura mensual desigual. "
        "Los porcentajes de participacion son estimaciones de la muestra disponible."
    )

    resumen_banderas = (
        pd.concat([
            hist_f.assign(periodo="2024-2025"),
            eval_f.assign(periodo="2026"),
        ])
        .groupby(["periodo", "empresabandera"])
        .agg(
            estaciones=("idempresa", "nunique"),
            precio_medio=("precio", "mean"),
        )
        .reset_index()
    )
    if not resumen_banderas.empty:
        st.dataframe(
            resumen_banderas.sort_values(
                ["periodo", "estaciones"], ascending=[True, False]
            ).round({"precio_medio": 2}),
            width="stretch",
            hide_index=True,
        )

with tab_tendencias:
    st.subheader("Evolucion mensual")

    historico_tendencia = hist_f.copy()
    historico_tendencia["fecha"] = pd.to_datetime(
        historico_tendencia["indice_tiempo"], format="%Y-%m", errors="coerce"
    )

    evaluacion_tendencia = eval_f.copy()
    evaluacion_tendencia["fecha"] = pd.to_datetime(
        evaluacion_tendencia["indice_tiempo"], format="%Y-%m", errors="coerce"
    )

    tendencia_real = pd.concat([
        historico_tendencia,
        evaluacion_tendencia,
    ], ignore_index=True)
    tendencia_real = (
        tendencia_real.groupby(["fecha", "empresabandera"], as_index=False)
        ["precio"]
        .median()
        .rename(columns={"precio": "precio_mediano"})
    )

    if not tendencia_real.empty:
        tabla_tendencia = tendencia_real.pivot(
            index="fecha", columns="empresabandera", values="precio_mediano"
        )
        st.line_chart(tabla_tendencia)
    else:
        st.info("No hay datos para los filtros seleccionados.")

    if not pronostico_f.empty:
        st.subheader("Pronostico mensual 2027")
        pronostico_mensual = (
            pronostico_f.assign(
                fecha=pd.to_datetime(
                    pronostico_f["anio"].astype(str)
                    + "-"
                    + pronostico_f["mes"].astype(str).str.zfill(2),
                    format="%Y-%m",
                    errors="coerce",
                )
            )
            .groupby(["fecha", "empresabandera"], as_index=False)
            ["precio_predicho"]
            .median()
        )
        pronostico_pivot = pronostico_mensual.pivot(
            index="fecha",
            columns="empresabandera",
            values="precio_predicho",
        )
        st.line_chart(pronostico_pivot)
        st.caption("Linea proyectada; no representa precios reales observados.")

with tab_modelos:
    st.subheader("Evaluacion de los modelos")

    resumen_json = (DATOS / "resumen.json")
    if resumen_json.exists():
        import json
        with open(resumen_json, encoding="utf-8") as archivo:
            resumen = json.load(archivo)

        metricas = resumen["metricas"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "MAE regresion",
            f"${metricas['regresion']['random_forest']['mae']:,.2f}",
        )
        col2.metric(
            "Baseline MAE",
            f"${metricas['regresion']['baseline_mediana']['mae']:,.2f}",
        )
        col3.metric(
            "Accuracy clasificacion",
            f"{metricas['clasificacion']['random_forest']['exactitud']:.2%}",
        )
        col4.metric(
            "AUC clasificacion",
            f"{metricas['clasificacion']['random_forest']['auc']:.2%}",
        )

        validacion = resumen["validacion_temporal_2025"]
        st.markdown("### Validacion temporal 2025")
        st.write(
            pd.DataFrame([
                {
                    "Modelo": "Baseline",
                    "MAE regresion": validacion["regresion"]["baseline_mae"],
                    "Accuracy clasificacion": validacion["clasificacion"]["baseline_exactitud"],
                },
                {
                    "Modelo": "Random Forest",
                    "MAE regresion": validacion["regresion"]["random_forest_mae"],
                    "Accuracy clasificacion": validacion["clasificacion"]["random_forest_exactitud"],
                },
            ])
        )

    st.markdown("### Precio real vs predicho - 2026")
    pred_f = predicciones_2026.copy()
    if producto:
        pred_f = pred_f[pred_f["producto"].isin(producto)]
    if bandera:
        pred_f = pred_f[pred_f["empresabandera"].isin(bandera)]
    if provincia:
        pred_f = pred_f[pred_f["provincia"].isin(provincia)]
    if not pred_f.empty:
        st.scatter_chart(
            pred_f[["precio", "precio_predicho"]].rename(
                columns={
                    "precio": "Precio real",
                    "precio_predicho": "Precio predicho",
                }
            )
        )

with tab_participacion:
    st.subheader("Participacion de mercado por estaciones unicas")

    cobertura = pd.concat([
        hist_f.assign(periodo="2024-2025"),
        eval_f.assign(periodo="2026"),
    ])
    if not cobertura.empty:
        periodos = sorted(cobertura["periodo"].unique())
        periodo = st.selectbox("Periodo", periodos)
        corte = cobertura[cobertura["periodo"] == periodo]

        estaciones_totales = corte["idempresa"].nunique()
        participacion = (
            corte.groupby("empresabandera")["idempresa"]
            .nunique()
            .sort_values(ascending=False)
        )
        participacion = (participacion / estaciones_totales * 100).round(1)

        tabla = participacion.rename("participacion_porcentual").reset_index()
        tabla.columns = ["Banderas", "Participacion %"]
        st.bar_chart(tabla.set_index("Banderas"))
        st.dataframe(tabla, hide_index=True, width="stretch")

        if periodo == "2026":
            st.warning(
                "2026 esta incompleto. Estos porcentajes no deben presentarse "
                "como participacion real nacional."
            )
