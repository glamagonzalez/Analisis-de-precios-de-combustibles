from pathlib import Path
import json

import pandas as pd

import generar_datasets_modelos as proyecto


AQUI = Path(__file__).resolve().parents[1]
DATOS = AQUI / "modelos_y_datos"


def test_limpieza_genera_periodos_y_sin_nulos_criticos():
    df = proyecto.cargar_limpiar()

    assert set(df["anio"].unique()).issuperset({2024, 2025, 2026})
    assert df["precio"].between(50, 10000).all()
    assert df[["empresabandera", "producto", "tipohorario", "provincia", "region"]].notna().all().all()


def test_clasificacion_2026_no_deja_medianas_sin_resolver():
    df = proyecto.cargar_limpiar()
    referencia = df[df["anio"].isin([2024, 2025])]
    test = df[df["anio"] == 2026]

    clasificacion = proyecto.preparar_clasificacion_2026(test, referencia)

    assert "clase" in clasificacion
    assert clasificacion["mediana_mes_producto"].notna().all()
    assert set(clasificacion["clase"].unique()).issubset({0, 1})


def test_datasets_generados_tienen_el_tamano_esperado():
    evaluacion = pd.read_csv(DATOS / "regresion_evaluacion_2026.csv")
    predicciones = pd.read_csv(DATOS / "predicciones_evaluacion_2026.csv")
    pronostico = pd.read_csv(DATOS / "proyeccion_2027.csv")

    assert len(evaluacion) == len(predicciones)
    assert not pronostico["precio_predicho"].isna().any()
    assert not pronostico["mediana_base_2025"].isna().any()
    assert set(pronostico["anio"].unique()) == {2027}


def test_resumen_conservar_limites_del_modelo():
    resumen = json.loads((DATOS / "resumen.json").read_text(encoding="utf-8"))
    r2 = resumen["metricas"]["regresion"]["random_forest"]["r2"]

    assert resumen["periodo_entrenamiento"] == "2024-2025"
    assert resumen["periodo_evaluacion_real"] == "2026"
    assert resumen["periodo_pronostico"] == "2027"
    assert r2 < 0
