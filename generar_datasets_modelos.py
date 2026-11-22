"""Genera datasets de regresión/clasificación para 2024-2027."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


AQUI = Path(__file__).resolve().parent
ENTRADA = AQUI / "precios-en-surtidor-resolucin-3142016.csv"
SALIDA = AQUI / "modelos_y_datos"
SALIDA.mkdir(exist_ok=True)

CATEGORICAS = ["empresabandera", "producto", "tipohorario", "provincia", "region"]
NUMERICAS = ["anio", "mes"]


def cargar_limpiar() -> pd.DataFrame:
    df = pd.read_csv(ENTRADA, sep=";", low_memory=False, encoding="utf-8")
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
    df["fecha"] = pd.to_datetime(df["indice_tiempo"], format="%Y-%m", errors="coerce")

    df = df.dropna(subset=[
        "precio", "empresabandera", "producto", "tipohorario",
        "provincia", "region", "fecha", "idempresa",
    ]).copy()
    df = df[
        df["precio"].between(50, 10000)
        & ~df["empresabandera"].isin(["SIN EMPRESA BANDERA", "WICO"])
    ].copy()

    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df = df.drop_duplicates([
        "idempresa", "idproducto", "idtipohorario", "empresabandera",
        "direccion", "provincia", "region", "precio", "indice_tiempo",
    ])
    return df


def preparar_clasificacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mediana = df.groupby(["anio", "mes", "producto"])["precio"].transform("median")
    df["clase"] = (df["precio"] > mediana).astype(int)
    df["mediana_mes_producto"] = mediana
    return df


def preparar_clasificacion_2026(test: pd.DataFrame, referencia: pd.DataFrame) -> pd.DataFrame:
    """Clasifica 2026 contra medianas de 2025 para evitar fuga de datos futuros."""
    df = test.copy()
    mediana_2025 = (
        referencia[referencia["anio"] == 2025]
        .groupby(["mes", "producto"])["precio"]
        .median()
        .rename("mediana_mes_producto")
        .reset_index()
    )
    df = df.merge(mediana_2025, on=["mes", "producto"], how="left")
    faltantes = df["mediana_mes_producto"].isna()
    if faltantes.any():
        mediana_global = referencia.groupby(["producto"])["precio"].median()
        df.loc[faltantes, "mediana_mes_producto"] = df.loc[
            faltantes, "producto"
        ].map(mediana_global)
    df["clase"] = (df["precio"] > df["mediana_mes_producto"]).astype(int)
    return df


def preprocesador():
    try:
        codificador = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        codificador = OneHotEncoder(handle_unknown="ignore", sparse=False)
    return ColumnTransformer([
        ("categoricas", codificador, CATEGORICAS),
        ("numericas", "passthrough", NUMERICAS),
    ])


def validar_2025(df: pd.DataFrame):
    """Entrena con 2024 y evalua con 2025 como validacion temporal."""
    train = df[df["anio"] == 2024].copy()
    test = df[df["anio"] == 2025].copy()
    columnas = CATEGORICAS + NUMERICAS

    regresor = Pipeline([
        ("transformacion", preprocesador()),
        ("modelo", RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2,
            random_state=42, n_jobs=-1,
        )),
    ])
    regresor.fit(train[columnas], train["precio"])
    pred = regresor.predict(test[columnas])

    baseline = DummyRegressor(strategy="median")
    baseline.fit(train[columnas], train["precio"])
    pred_baseline = baseline.predict(test[columnas])

    train_clase = preparar_clasificacion(train)
    test_clase = preparar_clasificacion_2026(test, train)
    clasificador = Pipeline([
        ("transformacion", preprocesador()),
        ("modelo", RandomForestClassifier(
            n_estimators=200, min_samples_leaf=2,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )),
    ])
    clasificador.fit(
        train_clase[columnas], train_clase["clase"]
    )
    pred_clase = clasificador.predict(test_clase[columnas])
    reporte = classification_report(
        test_clase["clase"], pred_clase,
        target_names=["Barata", "Cara"], output_dict=True,
    )

    baseline_clase = DummyClassifier(strategy="most_frequent")
    baseline_clase.fit(train_clase[columnas], train_clase["clase"])
    pred_baseline_clase = baseline_clase.predict(test_clase[columnas])

    return {
        "regresion": {
            "baseline_mae": round(float(mean_absolute_error(test["precio"], pred_baseline)), 2),
            "random_forest_mae": round(float(mean_absolute_error(test["precio"], pred)), 2),
            "random_forest_rmse": round(
                float(mean_squared_error(test["precio"], pred) ** 0.5), 2
            ),
        },
        "clasificacion": {
            "baseline_exactitud": round(
                float(accuracy_score(test_clase["clase"], pred_baseline_clase)), 4
            ),
            "random_forest_exactitud": round(
                float(accuracy_score(test_clase["clase"], pred_clase)), 4
            ),
            "random_forest_f1_cara": round(
                float(reporte["Cara"]["f1-score"]), 4
            ),
        },
    }


def crear_modelos(train: pd.DataFrame, test: pd.DataFrame):
    columnas = CATEGORICAS + NUMERICAS

    baseline_regresion = DummyRegressor(strategy="median")
    baseline_regresion.fit(train[columnas], train["precio"])
    precio_baseline = baseline_regresion.predict(test[columnas])

    mae_baseline = mean_absolute_error(test["precio"], precio_baseline)
    rmse_baseline = mean_squared_error(
        test["precio"], precio_baseline
    ) ** 0.5

    regresor = Pipeline([
        ("transformacion", preprocesador()),
        ("modelo", RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=-1,
        )),
    ])
    regresor.fit(train[columnas], train["precio"])
    precio_pred = regresor.predict(test[columnas])
    mae = mean_absolute_error(test["precio"], precio_pred)
    rmse = mean_squared_error(test["precio"], precio_pred) ** 0.5
    r2 = r2_score(test["precio"], precio_pred)

    clasificacion_train = preparar_clasificacion(train)
    clasificacion_test = preparar_clasificacion_2026(test, train)

    baseline_clasificacion = DummyClassifier(strategy="most_frequent")
    baseline_clasificacion.fit(
        clasificacion_train[columnas], clasificacion_train["clase"]
    )
    clase_baseline = baseline_clasificacion.predict(
        clasificacion_test[columnas]
    )
    exactitud_baseline = accuracy_score(
        clasificacion_test["clase"], clase_baseline
    )

    clasificador = Pipeline([
        ("transformacion", preprocesador()),
        ("modelo", RandomForestClassifier(
            n_estimators=200, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1,
        )),
    ])
    clasificador.fit(clasificacion_train[columnas], clasificacion_train["clase"])
    clase_pred = clasificador.predict(clasificacion_test[columnas])
    exactitud = accuracy_score(clasificacion_test["clase"], clase_pred)
    reporte = classification_report(
        clasificacion_test["clase"], clase_pred,
        target_names=["Barata", "Cara"], output_dict=True,
    )
    matriz = confusion_matrix(clasificacion_test["clase"], clase_pred)
    probabilidad_cara = clasificador.predict_proba(
        clasificacion_test[columnas]
    )[:, 1]
    auc = roc_auc_score(clasificacion_test["clase"], probabilidad_cara)

    joblib.dump(regresor, SALIDA / "modelo_regresion.joblib")
    joblib.dump(clasificador, SALIDA / "modelo_clasificacion.joblib")

    evaluacion = test[columnas + ["precio"]].copy()
    evaluacion["precio_predicho"] = precio_pred
    evaluacion["error"] = evaluacion["precio_predicho"] - evaluacion["precio"]
    evaluacion["clase_real"] = clasificacion_test["clase"].values
    evaluacion["clase_predicha"] = clase_pred
    evaluacion["mediana_referencia_2025"] = (
        clasificacion_test["mediana_mes_producto"].values
    )
    evaluacion["probabilidad_cara"] = probabilidad_cara
    evaluacion.to_csv(SALIDA / "predicciones_evaluacion_2026.csv", index=False)

    return {
        "regresion": {
            "baseline_mediana": {
                "mae": round(float(mae_baseline), 2),
                "rmse": round(float(rmse_baseline), 2),
            },
            "random_forest": {
                "mae": round(float(mae), 2),
                "rmse": round(float(rmse), 2),
                "r2": round(float(r2), 4),
            },
        },
        "clasificacion": {
            "baseline_mas_frecuente": {
                "exactitud": round(float(exactitud_baseline), 4),
            },
            "random_forest": {
                "exactitud": round(float(exactitud), 4),
                "precision_cara": round(float(reporte["Cara"]["precision"]), 4),
                "recall_cara": round(float(reporte["Cara"]["recall"]), 4),
                "f1_cara": round(float(reporte["Cara"]["f1-score"]), 4),
                "auc": round(float(auc), 4),
                "matriz_confusion": matriz.tolist(),
            },
        },
    }


def crear_pronostico_2027(df: pd.DataFrame, regresor):
    recientes = df[df["anio"].isin([2025, 2026])]
    columnas = CATEGORICAS
    combos = recientes[columnas].drop_duplicates()
    filas = []
    for mes in range(1, 13):
        lote = combos.copy()
        lote["anio"] = 2027
        lote["mes"] = mes
        lote["precio_predicho"] = regresor.predict(
            lote[CATEGORICAS + NUMERICAS]
        )
        filas.append(lote)
    pronostico = pd.concat(filas, ignore_index=True)

    mediana_2025 = (
        df[df["anio"] == 2025]
        .groupby(["producto", "tipohorario", "mes"])["precio"]
        .median()
        .rename("mediana_base_2025")
        .reset_index()
    )
    pronostico = pronostico.merge(
        mediana_2025,
        on=["producto", "tipohorario", "mes"],
        how="left",
    )
    pronostico["clase_predicha"] = (
        pronostico["precio_predicho"] > pronostico["mediana_base_2025"]
    ).astype(int)
    pronostico["clase"] = pronostico["clase_predicha"].map({0: "Barata", 1: "Cara"})
    pronostico.to_csv(SALIDA / "proyeccion_2027.csv", index=False)


def main():
    df = cargar_limpiar()
    historico = df[df["anio"].isin([2024, 2025])].copy()
    evaluacion = df[df["anio"] == 2026].copy()

    columnas_base = CATEGORICAS + NUMERICAS + [
        "precio", "indice_tiempo", "idempresa", "direccion", "localidad",
    ]
    historico[columnas_base].to_csv(
        SALIDA / "regresion_2024_2025.csv", index=False,
    )
    clasificacion_historico = preparar_clasificacion(historico)
    clasificacion_historico[
        CATEGORICAS + NUMERICAS + ["precio", "clase", "mediana_mes_producto"]
    ].to_csv(SALIDA / "clasificacion_2024_2025.csv", index=False)

    evaluacion[columnas_base].to_csv(
        SALIDA / "regresion_evaluacion_2026.csv", index=False,
    )
    clasificacion_evaluacion = preparar_clasificacion_2026(evaluacion, historico)
    clasificacion_evaluacion[
        CATEGORICAS + NUMERICAS + ["precio", "clase", "mediana_mes_producto"]
    ].to_csv(SALIDA / "clasificacion_evaluacion_2026.csv", index=False)

    metricas = crear_modelos(historico, evaluacion)
    validacion_2025 = validar_2025(historico)
    regresor = joblib.load(SALIDA / "modelo_regresion.joblib")
    crear_pronostico_2027(df, regresor)

    resumen = {
        "periodo_entrenamiento": "2024-2025",
        "periodo_evaluacion_real": "2026",
        "periodo_pronostico": "2027",
        "filas_entrenamiento": len(historico),
        "filas_evaluacion_2026": len(evaluacion),
        "estaciones_unicas_entrenamiento": historico["idempresa"].nunique(),
        "estaciones_unicas_evaluacion_2026": evaluacion["idempresa"].nunique(),
        "clasificacion": "Cara si el precio supera la mediana correspondiente de 2025",
        "validacion_temporal_2025": validacion_2025,
        "cobertura_2026": {
            str(mes): int(cantidad)
            for mes, cantidad in (
                evaluacion.groupby("mes").size().sort_index().items()
            )
        },
        "proyeccion_2027": "Modelo entrenado con datos reales 2024-2025; no usa precios reales futuros",
        "metricas": metricas,
    }
    with open(SALIDA / "resumen.json", "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2)

    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
