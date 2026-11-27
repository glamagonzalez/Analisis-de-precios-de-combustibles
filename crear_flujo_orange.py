"""Genera Flujo_Orange_Combustibles.ows con todos los widgets conectados.

Abrir en Orange desde la carpeta del proyecto (las rutas son relativas al .ows).
"""
import base64
import pickle
import sys
import types
from pathlib import Path
from xml.sax.saxutils import quoteattr

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "Flujo_Orange_Combustibles.ows"

# --- RecentPath sin necesitar Orange instalado (mismo modulo/clase que Orange) --
modulo = types.ModuleType("orangewidget.utils.filedialogs")
class RecentPath:  # noqa: E302
    pass
RecentPath.__module__ = "orangewidget.utils.filedialogs"
modulo.RecentPath = RecentPath
sys.modules["orangewidget"] = types.ModuleType("orangewidget")
sys.modules["orangewidget.utils"] = types.ModuleType("orangewidget.utils")
sys.modules["orangewidget.utils.filedialogs"] = modulo


def ruta(relpath):
    r = RecentPath()
    r.abspath, r.prefix, r.relpath = str(AQUI / relpath), "basedir", relpath
    r.title, r.sheet, r.file_format = "", "", None
    return r


W = {  # nombre -> clase calificada
    "File": "Orange.widgets.data.owfile.OWFile",
    "Data Table": "Orange.widgets.data.owtable.OWTable",
    "Distributions": "Orange.widgets.visualize.owdistributions.OWDistributions",
    "Box Plot": "Orange.widgets.visualize.owboxplot.OWBoxPlot",
    "Violin Plot": "Orange.widgets.visualize.owviolinplot.OWViolinPlot",
    "Scatter Plot": "Orange.widgets.visualize.owscatterplot.OWScatterPlot",
    "Random Forest": "Orange.widgets.model.owrandomforest.OWRandomForest",
    "Constant": "Orange.widgets.model.owconstant.OWConstant",
    "Logistic Regression": "Orange.widgets.model.owlogisticregression.OWLogisticRegression",
    "Linear Regression": "Orange.widgets.model.owlinearregression.OWLinearRegression",
    "Test and Score": "Orange.widgets.evaluate.owtestandscore.OWTestAndScore",
    "Confusion Matrix": "Orange.widgets.evaluate.owconfusionmatrix.OWConfusionMatrix",
    "ROC Analysis": "Orange.widgets.evaluate.owrocanalysis.OWROCAnalysis",
    "Predictions": "Orange.widgets.evaluate.owpredictions.OWPredictions",
}

nodos, props = [], {}


def nodo(nombre, titulo, x, y, propiedades=None):
    i = len(nodos)
    nodos.append((i, nombre, titulo, x, y))
    if propiedades is not None:
        props[i] = propiedades
    return i


def archivo(titulo, relpath, x, y):
    cfg = {"recent_paths": [ruta(relpath)], "recent_urls": [], "source": 0,
           "url": "", "__version__": 2, "context_settings": []}
    return nodo("File", titulo, x, y, ("pickle", cfg))


def rf(titulo, x, y, balanceado):
    cfg = {"n_estimators": 200, "use_min_samples_split": True, "min_samples_split": 60,
           "use_random_state": True, "class_weight": balanceado,
           "learner_name": "Random Forest", "auto_apply": True, "__version__": 1}
    return nodo("Random Forest", titulo, x, y, ("pickle", cfg))


def test_and_score(titulo, x, y):
    # resampling 5 = "Test on test data" (entrena con el set de entrenamiento y evalua en 2026)
    return nodo("Test and Score", titulo, x, y,
                ("pickle", {"resampling": 5, "__version__": 4, "context_settings": []}))


# ---- 1. Exploracion ---------------------------------------------------------
f_all = archivo("Dataset limpio completo", "orange/dataset_limpio_completo.csv", 0, 0)
tabla = nodo("Data Table", "Tabla de datos", 200, -120)
dist = nodo("Distributions", "Distribucion de precios", 200, -40)
box = nodo("Box Plot", "Box Plot por bandera", 200, 40)
violin = nodo("Violin Plot", "Violin por producto", 200, 120)
disp = nodo("Scatter Plot", "Precio vs precio relativo", 200, 200)

# ---- 2. Clasificacion --------------------------------------------------------
c_tr = archivo("Clasificacion - entrenamiento 2024-2025", "orange/clasificacion_entrenamiento.csv", 0, 380)
c_te = archivo("Clasificacion - evaluacion 2026", "orange/clasificacion_evaluacion_2026.csv", 0, 520)
c_rf = rf("RF clasificacion", 220, 340, True)
c_const = nodo("Constant", "Baseline clase frecuente", 220, 440)
c_log = nodo("Logistic Regression", "Regresion logistica", 220, 540)
c_ts = test_and_score("Test and Score - clasificacion", 440, 440)
c_cm = nodo("Confusion Matrix", "Matriz de confusion", 660, 400)
c_roc = nodo("ROC Analysis", "Curva ROC", 660, 500)
c_pred = nodo("Predictions", "Predicciones 2026 - clase", 440, 600)

# ---- 3. Regresion ------------------------------------------------------------
r_tr = archivo("Regresion - entrenamiento 2024-2025", "orange/regresion_entrenamiento.csv", 0, 780)
r_te = archivo("Regresion - evaluacion 2026", "orange/regresion_evaluacion_2026.csv", 0, 920)
r_rf = rf("RF regresion", 220, 740, False)
r_const = nodo("Constant", "Baseline media", 220, 840)
r_lin = nodo("Linear Regression", "Regresion lineal", 220, 940)
r_ts = test_and_score("Test and Score - regresion", 440, 840)
r_pred = nodo("Predictions", "Predicciones 2026 - precio relativo", 440, 1000)
r_scatter = nodo("Scatter Plot", "Real vs predicho", 660, 1000)

enlaces = [  # (origen, canal origen, destino, canal destino)
    (f_all, "data", tabla, "data"), (f_all, "data", dist, "data"),
    (f_all, "data", box, "data"), (f_all, "data", violin, "data"),
    (f_all, "data", disp, "data"),
    # clasificacion
    (c_tr, "data", c_rf, "data"), (c_tr, "data", c_const, "data"), (c_tr, "data", c_log, "data"),
    (c_tr, "data", c_ts, "train_data"), (c_te, "data", c_ts, "test_data"),
    (c_rf, "learner", c_ts, "learner"), (c_const, "learner", c_ts, "learner"),
    (c_log, "learner", c_ts, "learner"),
    (c_ts, "evaluations_results", c_cm, "evaluation_results"),
    (c_ts, "evaluations_results", c_roc, "evaluation_results"),
    (c_te, "data", c_pred, "data"), (c_rf, "model", c_pred, "predictors"),
    # regresion
    (r_tr, "data", r_rf, "data"), (r_tr, "data", r_const, "data"), (r_tr, "data", r_lin, "data"),
    (r_tr, "data", r_ts, "train_data"), (r_te, "data", r_ts, "test_data"),
    (r_rf, "learner", r_ts, "learner"), (r_const, "learner", r_ts, "learner"),
    (r_lin, "learner", r_ts, "learner"),
    (r_te, "data", r_pred, "data"), (r_rf, "model", r_pred, "predictors"),
    (r_pred, "annotated", r_scatter, "data"),
]

NOMBRES_CANAL = {  # id -> nombre visible
    "data": "Data", "train_data": "Data", "test_data": "Test Data", "learner": "Learner",
    "model": "Model", "predictors": "Predictors", "evaluations_results": "Evaluation Results",
    "evaluation_results": "Evaluation Results", "annotated": "Predictions",
}

lineas = ["<?xml version='1.0' encoding='utf-8'?>",
          '<scheme version="2.0" title="Analisis de precios de combustibles" '
          'description="Regresion y clasificacion con Random Forest - evaluacion con 2026">',
          "\t<nodes>"]
for i, nombre, titulo, x, y in nodos:
    lineas.append(
        f'\t\t<node id="{i}" name={quoteattr(nombre)} qualified_name="{W[nombre]}" '
        f'project_name="Orange3" version="" title={quoteattr(titulo)} position="({x}.0, {y}.0)" />')
lineas += ["\t</nodes>", "\t<links>"]
for k, (o, co, d, cd) in enumerate(enlaces):
    lineas.append(
        f'\t\t<link id="{k}" source_node_id="{o}" sink_node_id="{d}" '
        f'source_channel={quoteattr(NOMBRES_CANAL[co])} sink_channel={quoteattr(NOMBRES_CANAL[cd])} '
        f'enabled="true" source_channel_id="{co}" sink_channel_id="{cd}" />')
lineas += ["\t</links>", "\t<annotations>"]
notas = [
    ("1. Exploracion del dataset limpio", 0, -170),
    ("2. Clasificacion: Cara / Barata (RF vs baseline vs logistica)", 0, 300),
    ("3. Regresion: precio relativo al mercado (RF vs media vs lineal)", 0, 700),
]
for k, (texto, x, y) in enumerate(notas):
    lineas.append(f'\t\t<text id="{k}" type="text/plain" rect="({x}.0, {y}.0, 520.0, 30.0)" '
                  f'font-family="Helvetica" font-size="16">{texto}</text>')
lineas += ["\t</annotations>", "\t<thumbnail />", "\t<node_properties>"]
for i, (formato, cfg) in props.items():
    contenido = base64.encodebytes(pickle.dumps(cfg, protocol=4)).decode("ascii")
    lineas.append(f'\t\t<properties node_id="{i}" format="pickle">{contenido}</properties>')
lineas += ["\t</node_properties>", "\t<session_state>", "\t\t<window_groups />",
           "\t</session_state>", "</scheme>"]
SALIDA.write_text("\n".join(lineas), encoding="utf-8")
print("Escrito", SALIDA, "-", len(nodos), "widgets,", len(enlaces), "conexiones")
