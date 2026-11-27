"""Pipeline del proyecto de precios de combustibles (v2).

Genera: datasets limpios, modelos de regresion y clasificacion, validacion
temporal, proyeccion 2027 y las tablas listas para Power BI y Orange.
Uso:  python generar_datasets_modelos.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score,
                             roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

AQUI = Path(__file__).resolve().parent
ENTRADA = AQUI / "precios-en-surtidor-resolucin-3142016.csv"
SALIDA = AQUI / "modelos_y_datos"
POWERBI = AQUI / "powerbi"
ORANGE = AQUI / "orange"
for carpeta in (SALIDA, POWERBI, ORANGE):
    carpeta.mkdir(exist_ok=True)

CATEGORICAS = ["empresabandera", "producto", "tipohorario", "provincia", "region"]
SEMILLA = 42
ULTIMO_ANIO_ENTRENAMIENTO = 2025
TRAIN_ANIOS = [2024, 2025]
TEST_ANIO = 2026


# ----------------------------------------------------------------------------
# 1. Limpieza con bitacora de decisiones
# ----------------------------------------------------------------------------
def cargar_limpiar():
    bitacora = []

    def paso(nombre, df, decision):
        previo = bitacora[-1]["filas_restantes"] if bitacora else len(df)
        bitacora.append({
            "paso": nombre,
            "filas_restantes": int(len(df)),
            "filas_eliminadas": int(previo - len(df)),
            "surtidores_restantes": int(df["idempresa"].nunique()),
            "decision": decision,
        })

    df = pd.read_csv(ENTRADA, sep=";", encoding="utf-8-sig", low_memory=False)
    paso("0. Archivo original", df, "Lectura con separador ';' y codificacion utf-8-sig.")

    # Precios mal formateados en el origen (ej. "13.700.000" = $1.370): se recuperan dividiendo por 10.000
    texto = df["precio"].astype(str).str.strip()
    mal_formato = texto.str.match(r"^\d{1,2}\.\d{3}\.\d{3}$")
    df["precio"] = pd.to_numeric(texto, errors="coerce")
    df.loc[mal_formato, "precio"] = texto[mal_formato].str.replace(".", "", regex=False).astype(float) / 10000
    df["precio_recuperado"] = mal_formato
    sin_recuperar = int(df["precio"].isna().sum())
    df["fecha"] = pd.to_datetime(df["indice_tiempo"], format="%Y-%m", errors="coerce")
    df["vigencia"] = pd.to_datetime(df["fecha_vigencia"], dayfirst=True, errors="coerce")

    paso("0b. Recuperar precios mal formateados", df,
         f"{int(mal_formato.sum())} filas con formato 'x.xxx.000' se corrigen (valor/10.000); {sin_recuperar} quedan nulas.")

    # region: 21 % vacia -> se recupera desde la provincia en lugar de borrar filas
    region_por_prov = (df.dropna(subset=["region"]).groupby("provincia")["region"]
                       .agg(lambda s: s.mode().iat[0]))
    vacias = df["region"].isna()
    df.loc[vacias, "region"] = df.loc[vacias, "provincia"].map(region_por_prov)
    imputadas = int(vacias.sum() - df["region"].isna().sum())
    paso("1. Imputar region desde provincia", df,
         f"{imputadas} filas recuperadas (no se descartan por region vacia).")

    esenciales = ["precio", "fecha", "empresabandera", "producto",
                  "tipohorario", "provincia", "region", "idempresa"]
    df = df.dropna(subset=esenciales).copy()
    paso("2. Quitar nulos en variables esenciales", df,
         "Precio, fecha, bandera, producto, horario, provincia, region e id.")

    df = df[df["fecha"] >= "2024-01-01"].copy()
    paso("3. Periodo de estudio: 2024 en adelante", df,
         "Se descartan 2016-2023: pocos registros y precios en pesos de otra epoca.")

    df = df[df["precio"].between(50, 10000)].copy()
    paso("3b. Control de rango de precio 50-10.000", df, "Control de errores de carga.")

    df = df[~df["empresabandera"].isin(["SIN EMPRESA BANDERA", "WICO"])].copy()
    paso("4. Banderas sin identificacion confiable", df,
         "SIN EMPRESA BANDERA y WICO (muy pocos registros).")

    df = df.sort_values("vigencia").drop_duplicates(
        ["idempresa", "idproducto", "idtipohorario", "indice_tiempo"], keep="last")
    paso("5. Duplicados por estacion-producto-horario-mes", df,
         "Se conserva el precio con vigencia mas reciente.")

    ref = df.groupby(["producto", "fecha"])["precio"].transform("median")
    ratio = df["precio"] / ref
    df = df[ratio.between(0.4, 2.5)].copy()
    paso("6. Atipicos relativos (0,4x a 2,5x la mediana)", df,
         "Precio muy alejado de la mediana de su producto y mes.")

    df["grupo_bandera"] = np.where(df["empresabandera"] == "YPF", "YPF", "Resto del mercado")
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["fecha_mes"] = df["fecha"].dt.strftime("%Y-%m-01")
    df["precio_referencia"] = df.groupby(["producto", "fecha"])["precio"].transform("median")
    df["precio_relativo"] = df["precio"] / df["precio_referencia"]
    df["clase"] = (df["precio"] > df["precio_referencia"]).astype(int)
    df["clase_texto"] = df["clase"].map({0: "Barata", 1: "Cara"})
    df = df.sort_values(["fecha", "idempresa"]).reset_index(drop=True)
    return df, pd.DataFrame(bitacora)


# ----------------------------------------------------------------------------
# 2. Modelos
# ----------------------------------------------------------------------------
def preprocesador():
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAS),
    ])


def regresor_rf():
    return Pipeline([("t", preprocesador()), ("m", RandomForestRegressor(
        n_estimators=200, min_samples_leaf=5, random_state=SEMILLA, n_jobs=-1))])


def clasificador_rf():
    return Pipeline([("t", preprocesador()), ("m", RandomForestClassifier(
        n_estimators=200, min_samples_leaf=5, class_weight="balanced",
        random_state=SEMILLA, n_jobs=-1))])


def indice_tendencia(df_ref: pd.DataFrame, meses_ajuste: int = 12):
    """Ajusta log(precio de referencia) ~ tiempo por producto (tendencia lineal)."""
    base = (df_ref.groupby(["producto", "fecha"])["precio"].median()
            .reset_index().sort_values("fecha"))
    base["t"] = (base["fecha"].dt.year - 2024) * 12 + base["fecha"].dt.month
    coef = {}
    for producto, g in base.groupby("producto"):
        g = g.tail(meses_ajuste)
        pendiente, ordenada = np.polyfit(g["t"], np.log(g["precio"]), 1)
        coef[producto] = (pendiente, ordenada)
    return coef


def predecir_indice(coef, producto, anio, mes):
    t = (anio - 2024) * 12 + mes
    return np.exp(np.array([coef[p][0] * ti + coef[p][1] for p, ti in zip(producto, t)]))


def metricas_reg(y, p):
    return {"mae": round(float(mean_absolute_error(y, p)), 2),
            "rmse": round(float(mean_squared_error(y, p) ** 0.5), 2),
            "r2": round(float(r2_score(y, p)), 4)}


def evaluar(train, test, nombre):
    """Entrena y evalua ambos modelos. Devuelve metricas y predicciones."""
    reg = regresor_rf().fit(train[CATEGORICAS], np.log(train["precio_relativo"]))
    rel_pred = np.exp(reg.predict(test[CATEGORICAS]))
    coef = indice_tiempo = indice_tendencia(train)
    ref_pronostico = predecir_indice(coef, test["producto"].values,
                                     test["anio"].values, test["mes"].values)

    precio_con_indice_real = rel_pred * test["precio_referencia"].values
    precio_pronosticado = rel_pred * ref_pronostico

    base_mediana = DummyRegressor(strategy="median").fit(train[CATEGORICAS], train["precio"])
    p_base = base_mediana.predict(test[CATEGORICAS])
    ultimo = (train[train["fecha"] == train["fecha"].max()]
              .groupby("producto")["precio"].median())
    p_naive = test["producto"].map(ultimo).fillna(train["precio"].median()).values

    clf = clasificador_rf().fit(train[CATEGORICAS], train["clase"])
    pred = clf.predict(test[CATEGORICAS])
    proba = clf.predict_proba(test[CATEGORICAS])[:, 1]
    base_clf = DummyClassifier(strategy="most_frequent").fit(train[CATEGORICAS], train["clase"])
    pred_base = base_clf.predict(test[CATEGORICAS])

    y = test["clase"]
    m = {
        "regresion": {
            "baseline_mediana_global": metricas_reg(test["precio"], p_base),
            "baseline_ultimo_mes_producto": metricas_reg(test["precio"], p_naive),
            "rf_precio_pronosticado": metricas_reg(test["precio"], precio_pronosticado),
            "rf_con_indice_de_mercado_conocido": metricas_reg(test["precio"], precio_con_indice_real),
            "rf_precio_relativo": {
                "mae": round(float(mean_absolute_error(test["precio_relativo"], rel_pred)), 4),
                "baseline_mae": round(float(mean_absolute_error(
                    test["precio_relativo"], np.full(len(test), 1.0))), 4)},
        },
        "clasificacion": {
            "baseline_clase_frecuente": {"exactitud": round(float(accuracy_score(y, pred_base)), 4)},
            "random_forest": {
                "exactitud": round(float(accuracy_score(y, pred)), 4),
                "precision_cara": round(float(precision_score(y, pred)), 4),
                "recall_cara": round(float(recall_score(y, pred)), 4),
                "f1_cara": round(float(f1_score(y, pred)), 4),
                "auc": round(float(roc_auc_score(y, proba)), 4),
                "matriz_confusion": confusion_matrix(y, pred).tolist(),
            },
        },
    }
    salida = test[["fecha_mes", "anio", "mes", "idempresa", "grupo_bandera"] + CATEGORICAS +
                  ["precio", "precio_referencia", "precio_relativo", "clase"]].copy()
    salida["precio_relativo_predicho"] = rel_pred
    salida["precio_predicho"] = precio_pronosticado
    salida["precio_predicho_indice_conocido"] = precio_con_indice_real
    salida["error"] = salida["precio_predicho"] - salida["precio"]
    salida["clase_predicha"] = pred
    salida["probabilidad_cara"] = proba
    salida["clase_texto"] = salida["clase"].map({0: "Barata", 1: "Cara"})
    salida["clase_predicha_texto"] = salida["clase_predicha"].map({0: "Barata", 1: "Cara"})
    salida["conjunto"] = nombre
    return m, salida, reg, clf


# ----------------------------------------------------------------------------
# 3. Proyeccion 2027
# ----------------------------------------------------------------------------
def proyeccion_2027(df, reg):
    recientes = df[df["anio"] >= 2025]
    combos = recientes[CATEGORICAS].drop_duplicates().reset_index(drop=True)
    rel = np.exp(reg.predict(combos[CATEGORICAS]))
    coef = indice_tendencia(df)  # ultimos 12 meses observados (oct-2025 a sep-2026)
    filas = []
    for mes in range(1, 13):
        lote = combos.copy()
        lote["anio"], lote["mes"] = 2027, mes
        lote["fecha_mes"] = f"2027-{mes:02d}-01"
        lote["precio_relativo_predicho"] = rel
        lote["precio_referencia_proyectado"] = predecir_indice(
            coef, lote["producto"].values, lote["anio"].values, lote["mes"].values)
        lote["precio_predicho"] = lote["precio_relativo_predicho"] * lote["precio_referencia_proyectado"]
        filas.append(lote)
    out = pd.concat(filas, ignore_index=True)
    out["clase_predicha"] = np.where(out["precio_relativo_predicho"] > 1, "Cara", "Barata")
    out["tipo"] = "Proyeccion (no es dato real)"
    inflacion = {p: round((np.exp(12 * coef[p][0]) - 1) * 100, 1) for p in coef}
    return out, inflacion



# ----------------------------------------------------------------------------
# 3b. YPF frente al resto del mercado (comparacion controlada)
# ----------------------------------------------------------------------------
MIN_OBS = 3  # minimo de registros de YPF y del resto en cada celda comparable


def celdas_comparables(df, claves):
    """Celdas (mes x producto x zona) con YPF y resto; dif = mediana YPF / mediana resto - 1."""
    g = (df.groupby(claves + ["grupo_bandera"])["precio"]
         .agg(med="median", n="size").unstack("grupo_bandera"))
    g.columns = [f"{a}_{'YPF' if b == 'YPF' else 'Resto'}" for a, b in g.columns]
    g = g.dropna()
    g = g[(g["n_YPF"] >= MIN_OBS) & (g["n_Resto"] >= MIN_OBS)].reset_index()
    g["dif_pct"] = (g["med_YPF"] / g["med_Resto"] - 1) * 100
    return g


def resumen_dif(g, nivel, grupo, rng):
    if len(g) == 0:
        return None
    x, w = g["dif_pct"].values, g["n_YPF"].values
    media = float(np.average(x, weights=w))
    ic = (np.nan, np.nan)
    if len(g) >= 8:
        boot = [np.average(x[i], weights=w[i])
                for i in (rng.integers(0, len(x), len(x)) for _ in range(2000))]
        ic = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))
    return {"nivel": nivel, "grupo": grupo, "celdas": int(len(g)), "registros_ypf": int(w.sum()),
            "dif_pct": round(media, 2), "ic95_inf": round(ic[0], 2), "ic95_sup": round(ic[1], 2),
            "pct_celdas_ypf_mas_barata": round(float((x < 0).mean() * 100), 1)}


def comparacion_ypf(df):
    rng = np.random.default_rng(SEMILLA)
    reg = celdas_comparables(df, ["fecha_mes", "producto", "region"])
    reg["anio"] = reg["fecha_mes"].str[:4].astype(int)
    loc = celdas_comparables(df, ["fecha_mes", "producto", "provincia", "localidad"])
    filas = [
        resumen_dif(reg, "Total", "Mes x producto x region", rng),
        resumen_dif(reg[reg["fecha_mes"] != "2025-06-01"], "Total", "Sin junio 2025 (volcado masivo)", rng),
        resumen_dif(loc, "Total", "Mes x producto x localidad", rng),
    ]
    for r, d in reg.groupby("region"):
        filas.append(resumen_dif(d, "Region", r, rng))
    for p_, d in reg.groupby("producto"):
        filas.append(resumen_dif(d, "Producto", p_, rng))
    for a, d in reg.groupby("anio"):
        filas.append(resumen_dif(d, "Anio", str(a), rng))
    resumen = pd.DataFrame([f for f in filas if f])
    reg_anio = []
    for (r, a), d in reg.groupby(["region", "anio"]):
        fila = resumen_dif(d, "Region x anio", f"{r} | {a}", rng)
        fila.update({"region": r, "anio": a})
        reg_anio.append(fila)
    reg_anio = pd.DataFrame(reg_anio)
    # muestra: participacion de estaciones YPF por region y mes (no es participacion de mercado)
    est = df.groupby(["fecha_mes", "region"])["idempresa"].nunique().rename("estaciones_total")
    est_y = (df[df["grupo_bandera"] == "YPF"].groupby(["fecha_mes", "region"])["idempresa"]
             .nunique().rename("estaciones_ypf"))
    muestra = pd.concat([est, est_y], axis=1).fillna(0).reset_index()
    muestra["pct_estaciones_ypf_en_muestra"] = (muestra["estaciones_ypf"] / muestra["estaciones_total"] * 100).round(1)
    return reg, resumen, reg_anio, muestra


def clasificacion_ypf(pred_eval):
    t = pred_eval.copy()
    t["cara_real"] = t["clase"]; t["cara_predicha"] = t["clase_predicha"]
    out = (t.groupby(["region", "grupo_bandera"])
           .agg(registros=("clase", "size"), pct_cara_real=("cara_real", "mean"),
                pct_cara_predicha=("cara_predicha", "mean"), prob_cara_media=("probabilidad_cara", "mean"),
                precio_relativo_medio=("precio_relativo", "mean")).reset_index())
    for c in ("pct_cara_real", "pct_cara_predicha"):
        out[c] = (out[c] * 100).round(1)
    out["prob_cara_media"] = out["prob_cara_media"].round(3)
    out["precio_relativo_medio"] = out["precio_relativo_medio"].round(4)
    return out


# ----------------------------------------------------------------------------
# 3c. Auditoria de cobertura de surtidores y controles de calidad
# ----------------------------------------------------------------------------
def auditoria(bitacora, df, train, test, sub_test, pred_val, pred_fin):
    surt = lambda d: int(d["idempresa"].nunique())
    vistas = test["idempresa"].isin(set(train["idempresa"])).groupby(test["idempresa"]).first().mean()
    meses_por_surt = df.groupby("idempresa")["fecha_mes"].nunique()
    cobertura = pd.DataFrame([
        ("Archivo original (2016-2026)", int(bitacora["filas_restantes"].iloc[0]), int(bitacora["surtidores_restantes"].iloc[0])),
        ("Limpio (2024-2026)", len(df), surt(df)),
        ("Entrenamiento 2024-2025", len(train), surt(train)),
        ("Validacion sep-dic 2025", len(sub_test), surt(sub_test)),
        ("Evaluacion 2026 (enero-septiembre)", len(test), surt(test)),
        ("Predicciones 2026 generadas", len(pred_fin), surt(pred_fin)),
    ], columns=["conjunto", "filas", "surtidores"])
    extra = pd.DataFrame([
        ("Surtidores de 2026 que tambien estan en el entrenamiento (%)", round(float(vistas) * 100, 1)),
        ("Surtidores que aparecen en un solo mes (%)", round(float((meses_por_surt == 1).mean()) * 100, 1)),
        ("Filas con precio recuperado (formato x.xxx.000)", int(df["precio_recuperado"].sum())),
    ], columns=["indicador", "valor"])
    por_region = (df.assign(conjunto=np.where(df["anio"] <= 2025, "Entrenamiento 2024-2025", "Evaluacion 2026"))
                  .groupby(["region", "conjunto"]).agg(filas=("precio", "size"), surtidores=("idempresa", "nunique"))
                  .reset_index())
    por_bandera = (df.assign(conjunto=np.where(df["anio"] <= 2025, "Entrenamiento 2024-2025", "Evaluacion 2026"))
                   .groupby(["empresabandera", "conjunto"]).agg(filas=("precio", "size"), surtidores=("idempresa", "nunique"))
                   .reset_index())
    cols = CATEGORICAS + ["precio", "precio_relativo", "clase"]
    precio_rec = df.loc[df["precio_recuperado"], "precio_relativo"]
    controles = [
        ("Sin nulos en las variables de los modelos (entrenamiento y 2026)",
         int(train[cols].isna().sum().sum() + test[cols].isna().sum().sum()) == 0, "nulos = 0"),
        ("Sin duplicados por surtidor-producto-horario-mes",
         int(df.duplicated(["idempresa", "idproducto", "idtipohorario", "indice_tiempo"]).sum()) == 0, "duplicados = 0"),
        ("Clase Cara/Barata coincide con la regla (precio > mediana de producto y mes)",
         bool(((df["precio"] > df["precio_referencia"]).astype(int) == df["clase"]).all()), "regla verificada en todas las filas"),
        ("Precio relativo = precio / mediana de producto y mes",
         bool(np.allclose(df["precio_relativo"], df["precio"] / df["precio_referencia"])), "verificado"),
        ("Precios dentro de 50 y 10.000", bool(df["precio"].between(50, 10000).all()),
         f"minimo {df['precio'].min():.0f}, maximo {df['precio'].max():.0f}"),
        ("Banderas de 2026 presentes en el entrenamiento",
         set(test["empresabandera"]) <= set(train["empresabandera"]), f"{test['empresabandera'].nunique()} banderas"),
        ("Provincias y regiones de 2026 presentes en el entrenamiento",
         set(test["provincia"]) <= set(train["provincia"]) and set(test["region"]) <= set(train["region"]), "sin categorias nuevas"),
        ("Todas las filas de 2026 tienen prediccion",
         len(pred_fin) == len(test) and pred_fin[["precio_predicho", "clase_predicha", "probabilidad_cara"]].isna().sum().sum() == 0,
         f"{len(pred_fin)} de {len(test)}"),
        ("Precios recuperados con valores plausibles (0,4x a 2,5x la mediana)",
         bool(precio_rec.between(0.4, 2.5).all()) if len(precio_rec) else True,
         f"mediana {precio_rec.median():.3f}, rango {precio_rec.min():.2f}-{precio_rec.max():.2f}"),
    ]
    controles = pd.DataFrame([(a, "OK" if b else "REVISAR", c) for a, b, c in controles],
                             columns=["control", "resultado", "detalle"])
    return cobertura, extra, por_region, por_bandera, controles

# ----------------------------------------------------------------------------
# 4. Programa principal
# ----------------------------------------------------------------------------
def main():
    t0 = time.time()
    df, bitacora = cargar_limpiar()
    t_limpieza = time.time() - t0
    bitacora.to_csv(POWERBI / "bitacora_limpieza.csv", index=False, encoding="utf-8-sig")

    train = df[df["anio"].isin(TRAIN_ANIOS)].copy()
    test = df[df["anio"] == TEST_ANIO].copy()

    # validacion temporal interna: 2024 + ene-ago 2025 -> sep-dic 2025
    sub_train = df[(df["fecha"] < "2025-09-01")].copy()
    sub_test = df[(df["fecha"] >= "2025-09-01") & (df["anio"] == 2025)].copy()
    t1 = time.time()
    m_val, pred_val, _, _ = evaluar(sub_train, sub_test, "Validacion sep-dic 2025")
    m_fin, pred_fin, reg, clf = evaluar(train, test, "Evaluacion 2026")
    t_modelos = time.time() - t1

    joblib.dump(reg, SALIDA / "modelo_regresion.joblib")
    joblib.dump(clf, SALIDA / "modelo_clasificacion.joblib")

    proy, inflacion = proyeccion_2027(df, reg)

    # ---- tablas Power BI -----------------------------------------------------
    cols_hecho = (["fecha_mes", "anio", "mes", "idempresa", "grupo_bandera"] + CATEGORICAS +
                  ["localidad", "precio_recuperado", "precio", "precio_referencia", "precio_relativo", "clase_texto"])
    hechos = df[cols_hecho].copy()
    hechos["conjunto"] = np.select([hechos["anio"].isin(TRAIN_ANIOS), hechos["anio"] == TEST_ANIO],
                                   ["Entrenamiento 2024-2025", "Evaluacion 2026 (parcial)"], "Otros")
    hechos.to_csv(POWERBI / "fact_precios.csv", index=False, encoding="utf-8-sig")

    pd.concat([pred_val, pred_fin]).to_csv(
        POWERBI / "predicciones.csv", index=False, encoding="utf-8-sig")
    proy.to_csv(POWERBI / "proyeccion_2027.csv", index=False, encoding="utf-8-sig")

    # ---- auditoria de cobertura ------------------------------------------------
    aud_cob, aud_extra, aud_reg, aud_ban, aud_ctl = auditoria(bitacora, df, train, test, sub_test, pred_val, pred_fin)
    aud_cob.to_csv(POWERBI / "auditoria_cobertura.csv", index=False, encoding="utf-8-sig")
    aud_extra.to_csv(POWERBI / "auditoria_indicadores.csv", index=False, encoding="utf-8-sig")
    aud_reg.to_csv(POWERBI / "auditoria_region_conjunto.csv", index=False, encoding="utf-8-sig")
    aud_ban.to_csv(POWERBI / "auditoria_bandera_conjunto.csv", index=False, encoding="utf-8-sig")

    # ---- YPF vs resto --------------------------------------------------------
    celdas, resumen_ypf, reg_anio, muestra_ypf = comparacion_ypf(df)
    celdas.to_csv(POWERBI / "ypf_vs_resto_celdas.csv", index=False, encoding="utf-8-sig")
    resumen_ypf.to_csv(POWERBI / "ypf_vs_resto_resumen.csv", index=False, encoding="utf-8-sig")
    reg_anio.to_csv(POWERBI / "ypf_vs_resto_region_anio.csv", index=False, encoding="utf-8-sig")
    muestra_ypf.to_csv(POWERBI / "ypf_muestra_estaciones_region_mes.csv", index=False, encoding="utf-8-sig")
    clasificacion_ypf(pred_fin).to_csv(POWERBI / "ypf_clasificacion_region_2026.csv", index=False, encoding="utf-8-sig")

    cobertura = (df.groupby("fecha_mes").agg(
        registros=("precio", "size"), estaciones=("idempresa", "nunique"),
        precio_mediano=("precio", "median")).reset_index())
    cobertura["etapa"] = np.where(cobertura["fecha_mes"] >= "2026-01-01", "2026 parcial",
                           np.where(cobertura["fecha_mes"] >= "2025-01-01", "2025", "2024 o anterior"))
    cobertura.to_csv(POWERBI / "cobertura_mensual.csv", index=False, encoding="utf-8-sig")

    part = []
    for etiqueta, sub in (("2025", df[df.anio == 2025]), ("2026 (parcial)", test)):
        t = sub.groupby("empresabandera")["idempresa"].nunique().rename("estaciones").reset_index()
        t["participacion_pct"] = (t["estaciones"] / sub["idempresa"].nunique() * 100).round(2)
        t["periodo"] = etiqueta
        t["precio_relativo_medio"] = t["empresabandera"].map(
            sub.groupby("empresabandera")["precio_relativo"].mean()).round(4)
        part.append(t)
    pd.concat(part).to_csv(POWERBI / "participacion_banderas.csv", index=False, encoding="utf-8-sig")

    filas_m = []
    for ensayo, mm in (("Validacion sep-dic 2025", m_val), ("Evaluacion 2026", m_fin)):
        for modelo, vals in mm["regresion"].items():
            for k, v in vals.items():
                filas_m.append((ensayo, "Regresion", modelo, k, v))
        for modelo, vals in mm["clasificacion"].items():
            for k, v in vals.items():
                if k != "matriz_confusion":
                    filas_m.append((ensayo, "Clasificacion", modelo, k, v))
    pd.DataFrame(filas_m, columns=["ensayo", "tarea", "modelo", "metrica", "valor"]).to_csv(
        POWERBI / "metricas.csv", index=False, encoding="utf-8-sig")

    mc = []
    for ensayo, mm in (("Validacion sep-dic 2025", m_val), ("Evaluacion 2026", m_fin)):
        c = mm["clasificacion"]["random_forest"]["matriz_confusion"]
        for i, real in enumerate(["Barata", "Cara"]):
            for j, pr in enumerate(["Barata", "Cara"]):
                mc.append((ensayo, real, pr, c[i][j]))
    pd.DataFrame(mc, columns=["ensayo", "clase_real", "clase_predicha", "cantidad"]).to_csv(
        POWERBI / "matriz_confusion.csv", index=False, encoding="utf-8-sig")

    nombres = clf.named_steps["t"].get_feature_names_out()
    imp = pd.DataFrame({
        "variable_codificada": nombres,
        "importancia_clasificacion": clf.named_steps["m"].feature_importances_,
        "importancia_regresion": reg.named_steps["m"].feature_importances_})
    imp["variable"] = imp["variable_codificada"].str.replace("cat__", "").str.split("_").str[0]
    imp.sort_values("importancia_clasificacion", ascending=False).to_csv(
        POWERBI / "importancia_variables.csv", index=False, encoding="utf-8-sig")

    # ---- tablas Orange (CSV con cabecera de tipos de Orange) -------------------
    def para_orange(d, objetivo, ruta):
        x = d[CATEGORICAS + ["mes", objetivo]].copy()
        x = x.rename(columns={objetivo: ("c#" + objetivo)})
        if objetivo == "clase_texto":
            x = x.rename(columns={"c#clase_texto": "c#clase"})
        x.to_csv(ruta, index=False, encoding="utf-8")

    para_orange(train, "precio_relativo", ORANGE / "regresion_entrenamiento.csv")
    para_orange(test, "precio_relativo", ORANGE / "regresion_evaluacion_2026.csv")
    para_orange(train, "clase_texto", ORANGE / "clasificacion_entrenamiento.csv")
    para_orange(test, "clase_texto", ORANGE / "clasificacion_evaluacion_2026.csv")
    df[["fecha_mes", "anio", "mes", "grupo_bandera"] + CATEGORICAS + ["precio", "precio_relativo", "clase_texto"]].to_csv(
        ORANGE / "dataset_limpio_completo.csv", index=False, encoding="utf-8")

    filas_orange = {n: len(pd.read_csv(ORANGE / n)) for n in (
        "regresion_entrenamiento.csv", "regresion_evaluacion_2026.csv",
        "clasificacion_entrenamiento.csv", "clasificacion_evaluacion_2026.csv")}
    ok_orange = (filas_orange["regresion_entrenamiento.csv"] == len(train) == filas_orange["clasificacion_entrenamiento.csv"]
                 and filas_orange["regresion_evaluacion_2026.csv"] == len(test) == filas_orange["clasificacion_evaluacion_2026.csv"])
    aud_ctl.loc[len(aud_ctl)] = ["Archivos de Orange con las mismas filas que entrenamiento y 2026",
                                 "OK" if ok_orange else "REVISAR", f"{len(train)} y {len(test)} filas"]
    aud_ctl.to_csv(POWERBI / "auditoria_controles.csv", index=False, encoding="utf-8-sig")

    resumen = {
        "periodo_entrenamiento": "2024-2025",
        "periodo_evaluacion_real": "2026 (enero-septiembre, cobertura parcial)",
        "periodo_pronostico": "2027",
        "filas_entrenamiento": int(len(train)),
        "filas_evaluacion_2026": int(len(test)),
        "filas_validacion_sep_dic_2025": int(len(sub_test)),
        "estaciones_unicas_entrenamiento": int(train["idempresa"].nunique()),
        "estaciones_unicas_evaluacion_2026": int(test["idempresa"].nunique()),
        "definicion_clase": "Cara si el precio supera la mediana de su producto en el mismo mes",
        "aumento_anual_supuesto_en_proyeccion_pct": inflacion,
        "tiempos_segundos": {"limpieza": round(t_limpieza, 1), "modelado": round(t_modelos, 1),
                              "total": round(time.time() - t0, 1)},
        "ypf_vs_resto": resumen_ypf.to_dict(orient="records"),
        "validacion_sep_dic_2025": m_val,
        "evaluacion_2026": m_fin,
    }
    with open(SALIDA / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(bitacora.to_string())


if __name__ == "__main__":
    main()
