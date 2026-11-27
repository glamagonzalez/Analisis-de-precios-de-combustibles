"""Genera los graficos del informe a partir de las tablas de powerbi/."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
P, F = AQUI / "powerbi", AQUI / "figuras"
F.mkdir(exist_ok=True)
NOM = {"Nafta (premium) de más de 95 Ron": "Nafta premium", "Nafta (súper) entre 92 y 95 Ron": "Nafta súper"}

cov = pd.read_csv(P / "cobertura_mensual.csv"); cov = cov[cov.fecha_mes >= "2025-01-01"]
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar(cov.fecha_mes.str[:7], cov.registros, color=cov.etapa.map({"2025": "#1F4E78", "2026 parcial": "#E07B00"}))
ax.set_ylabel("Registros"); ax.set_title("Cobertura mensual: registros por mes"); plt.xticks(rotation=60, fontsize=8)
ax.annotate("Volcado masivo\njun-2025", (5, cov.registros.max()), xytext=(8, cov.registros.max() * 0.9), fontsize=8, arrowprops=dict(arrowstyle="->"))
plt.tight_layout(); plt.savefig(F / "cobertura_mensual.png", dpi=160); plt.close()

pr = pd.read_csv(P / "predicciones.csv"); t = pr[pr.conjunto == "Evaluacion 2026"]
fig, ax = plt.subplots(1, 2, figsize=(9, 3.8)); s = t.sample(3000, random_state=1); m = [s.precio.min(), s.precio.max()]
ax[0].scatter(s.precio, s.precio_predicho, s=4, alpha=.4, color="#1F4E78"); ax[0].plot(m, m, "r--", lw=1)
ax[0].set_xlabel("Precio real"); ax[0].set_ylabel("Precio predicho"); ax[0].set_title("Regresion 2026 (precio pronosticado)")
ax[1].scatter(s.precio, s.precio_predicho_indice_conocido, s=4, alpha=.4, color="#2E8B57"); ax[1].plot(m, m, "r--", lw=1)
ax[1].set_xlabel("Precio real"); ax[1].set_title("Con indice de mercado conocido")
plt.tight_layout(); plt.savefig(F / "real_vs_predicho.png", dpi=160); plt.close()

mc = pd.read_csv(P / "matriz_confusion.csv"); mm = mc[mc.ensayo == "Evaluacion 2026"].pivot(index="clase_real", columns="clase_predicha", values="cantidad")
fig, ax = plt.subplots(figsize=(4.2, 3.6)); ax.imshow(mm.values, cmap="Blues")
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{mm.values[i, j]:,}".replace(",", "."), ha="center", va="center", fontsize=12, color="white" if mm.values[i, j] > mm.values.max() * .6 else "black")
ax.set_xticks([0, 1], mm.columns); ax.set_yticks([0, 1], mm.index); ax.set_xlabel("Predicha"); ax.set_ylabel("Real"); ax.set_title("Matriz de confusion 2026")
plt.tight_layout(); plt.savefig(F / "matriz_confusion.png", dpi=160); plt.close()

f = pd.read_csv(P / "fact_precios.csv"); med = f.groupby(["fecha_mes", "producto"]).precio.median().reset_index()
pj = pd.read_csv(P / "proyeccion_2027.csv"); pm = pj.groupby(["fecha_mes", "producto"]).precio_referencia_proyectado.first().reset_index()
fig, ax = plt.subplots(figsize=(8, 3.8))
for p_, g in med.groupby("producto"):
    l, = ax.plot(pd.to_datetime(g.fecha_mes), g.precio, lw=1.6, label=NOM.get(p_, p_)[:22]); q = pm[pm.producto == p_]
    ax.plot(pd.to_datetime(q.fecha_mes), q.precio_referencia_proyectado, "--", color=l.get_color(), lw=1.2)
ax.axvline(pd.Timestamp("2026-10-01"), color="gray", lw=.8); ax.set_ylabel("$ por unidad"); ax.legend(fontsize=7)
ax.set_title("Precio mediano por producto (real) y escenario 2027 (linea punteada)"); plt.tight_layout(); plt.savefig(F / "tendencia_proyeccion.png", dpi=160); plt.close()

r = pd.read_csv(P / "ypf_vs_resto_resumen.csv"); fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.6), sharex=True)
for a, nivel, tit in ((ax[0], "Region", "Por región"), (ax[1], "Producto", "Por producto")):
    d = r[r.nivel == nivel].sort_values("dif_pct"); y = list(range(len(d)))
    a.barh(y, d.dif_pct, xerr=[d.dif_pct - d.ic95_inf, d.ic95_sup - d.dif_pct], color="#1F4E78", capsize=3)
    a.set_yticks(y, [NOM.get(g, g) for g in d.grupo], fontsize=8); a.axvline(0, color="k", lw=.8); a.set_title(tit, fontsize=10); a.set_xlim(-13, 3.5)
    for i, (v, n_) in enumerate(zip(d.dif_pct, d.celdas)): a.text(v - 0.15, i, f"{v:.1f}%  (n={n_})", va="center", ha="right", fontsize=7)
    a.set_xlabel("Diferencia de precio YPF vs. resto (%)")
fig.suptitle("YPF frente al resto del mercado (mismo mes, producto y región; IC 95 %)", fontsize=10); plt.tight_layout(); plt.savefig(F / "ypf_region_producto.png", dpi=160); plt.close()

ra = pd.read_csv(P / "ypf_vs_resto_region_anio.csv"); pv = ra.pivot(index="region", columns="anio", values="dif_pct"); nn = ra.pivot(index="region", columns="anio", values="celdas")
fig, ax = plt.subplots(figsize=(5.6, 3.4)); ax.imshow(pv.values, cmap="RdBu", vmin=-9, vmax=9, aspect="auto")
for i in range(pv.shape[0]):
    for j in range(pv.shape[1]):
        v = pv.values[i, j]; ax.text(j, i, "sin datos" if np.isnan(v) else f"{v:.1f}%\n(n={int(nn.values[i, j])})", ha="center", va="center", fontsize=8)
ax.set_xticks(range(pv.shape[1]), pv.columns); ax.set_yticks(range(len(pv)), pv.index); ax.set_title("Diferencia YPF vs. resto por región y año", fontsize=10)
plt.tight_layout(); plt.savefig(F / "ypf_region_anio.png", dpi=160); plt.close()

m = pd.read_csv(P / "ypf_muestra_estaciones_region_mes.csv"); m = m[m.fecha_mes >= "2025-01-01"]; fig, ax = plt.subplots(figsize=(8, 3.4))
for reg, g in m.groupby("region"): ax.plot(pd.to_datetime(g.fecha_mes), g.pct_estaciones_ypf_en_muestra, marker="o", ms=3, label=reg)
ax.set_ylabel("% de estaciones YPF en la muestra"); ax.set_title("La muestra cambia: peso de YPF en las estaciones informadas por mes", fontsize=10)
ax.legend(fontsize=7, ncol=3); plt.tight_layout(); plt.savefig(F / "ypf_muestra.png", dpi=160); plt.close()
print("figuras ok")
