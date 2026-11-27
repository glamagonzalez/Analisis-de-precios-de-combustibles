"""Reproduce en Orange (por codigo) las evaluaciones del flujo .ows y guarda resultados_orange.json."""
import json
from pathlib import Path
from Orange.data import Table
from Orange.classification import LogisticRegressionLearner, MajorityLearner, RandomForestLearner
from Orange.evaluation import AUC, CA, F1, MAE, R2, RMSE, TestOnTestData
from Orange.regression import LinearRegressionLearner, MeanLearner, RandomForestRegressionLearner

AQUI = Path(__file__).resolve().parent
c, ct = Table(str(AQUI / "orange/clasificacion_entrenamiento.csv")), Table(str(AQUI / "orange/clasificacion_evaluacion_2026.csv"))
g, gt = Table(str(AQUI / "orange/regresion_entrenamiento.csv")), Table(str(AQUI / "orange/regresion_evaluacion_2026.csv"))
r = TestOnTestData()(c, ct, [RandomForestLearner(n_estimators=200, min_samples_split=60, class_weight="balanced", random_state=0),
                             MajorityLearner(), LogisticRegressionLearner()])
oc = {n: {"CA": float(CA(r)[i]), "AUC": float(AUC(r)[i])} for i, n in enumerate(["RF", "Constante", "Logistica"])}
oc["RF"]["F1"] = float(F1(r, target=1)[0])
r2 = TestOnTestData()(g, gt, [RandomForestRegressionLearner(n_estimators=200, min_samples_split=60, random_state=0),
                              MeanLearner(), LinearRegressionLearner()])
orr = {n: {"MAE": float(MAE(r2)[i]), "RMSE": float(RMSE(r2)[i]), "R2": float(R2(r2)[i])} for i, n in enumerate(["RF", "Media", "Lineal"])}
json.dump({"clasificacion": oc, "regresion": orr}, open(AQUI / "modelos_y_datos/resultados_orange.json", "w"), indent=1)
print(oc, orr)
