"""Genera Informe_final_Proyecto_Combustibles.docx con los resultados del pipeline."""
import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "Informe_final_Proyecto_Combustibles.docx"
R = json.load(open(AQUI / "modelos_y_datos" / "resumen.json", encoding="utf-8"))
ORA = json.load(open(AQUI / "modelos_y_datos" / "resultados_orange.json", encoding="utf-8"))
BIT = pd.read_csv(AQUI / "powerbi" / "bitacora_limpieza.csv")
COB = pd.read_csv(AQUI / "powerbi" / "cobertura_mensual.csv")
PAR = pd.read_csv(AQUI / "powerbi" / "participacion_banderas.csv")
FIG = AQUI / "figuras"
AUD = pd.read_csv(AQUI / "powerbi" / "auditoria_cobertura.csv")
AUDI = pd.read_csv(AQUI / "powerbi" / "auditoria_indicadores.csv").set_index("indicador")["valor"]
AUDR = pd.read_csv(AQUI / "powerbi" / "auditoria_region_conjunto.csv")
AUDC = pd.read_csv(AQUI / "powerbi" / "auditoria_controles.csv")
YR = pd.read_csv(AQUI / "powerbi" / "ypf_vs_resto_resumen.csv")
YCL = pd.read_csv(AQUI / "powerbi" / "ypf_clasificacion_region_2026.csv")
YM = pd.read_csv(AQUI / "powerbi" / "ypf_muestra_estaciones_region_mes.csv")
_f = pd.read_csv(AQUI / "powerbi" / "fact_precios.csv", usecols=["anio", "idempresa"])
_tr, _te = set(_f[_f.anio <= 2025].idempresa), _f[_f.anio == 2026].idempresa.unique()
PCT_VISTAS = 100 * sum(e in _tr for e in _te) / len(_te)
AZUL = RGBColor(31, 78, 121)


def n(x, d=0):  # numero con formato argentino
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def p(x, d=1):
    return n(x * 100, d) + " %"


def sombrear(celda, color):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), color)
    celda._tc.get_or_add_tcPr().append(sh)


def tabla(doc, encabezados, filas, anchos, tam=9):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for i, h in enumerate(encabezados):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(tam)
        r.font.color.rgb = RGBColor(255, 255, 255); sombrear(c, "1F4E78")
    for fila in filas:
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = ""
            r = celdas[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(tam)
            celdas[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for fila in t.rows:
        for i, a in enumerate(anchos):
            fila.cells[i].width = Inches(a)
    # tablas de hasta 10 filas: no partir entre paginas; las largas solo repiten el encabezado
    if len(t.rows) <= 10:
        for fila in t.rows[:-1]:
            for c in fila.cells:
                for par in c.paragraphs:
                    par.paragraph_format.keep_with_next = True
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for fila in t.rows:
        cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); fila._tr.get_or_add_trPr().append(cs)
    doc.add_paragraph()
    return t


def parrafo(doc, texto, negrita_inicio=None):
    par = doc.add_paragraph()
    if texto.rstrip().endswith(":"):
        par.paragraph_format.keep_with_next = True
    if negrita_inicio:
        par.add_run(negrita_inicio).bold = True
    par.add_run(texto)
    return par


def lista(doc, items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def figura(doc, nombre, ancho, pie):
    doc.add_picture(str(FIG / nombre), width=Inches(ancho))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = doc.add_paragraph(pie); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.runs[0].italic = True; c.runs[0].font.size = Pt(8.5)


doc = Document()
s = doc.sections[0]
s.page_width, s.page_height = Inches(8.27), Inches(11.69)  # A4
for lado in ("top_margin", "bottom_margin"):
    setattr(s, lado, Inches(0.8))
s.left_margin = s.right_margin = Inches(0.9)
doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(10.5)
for nombre in ("Heading 1", "Heading 2"):
    doc.styles[nombre].font.name = "Calibri"; doc.styles[nombre].font.color.rgb = AZUL

# ---- encabezado ----------------------------------------------------------------
enc = doc.add_table(rows=1, cols=2); enc.autofit = False
enc.rows[0].cells[0].paragraphs[0].add_run().add_picture(str(AQUI / "logo_instituto57.png"), width=Inches(1.6))
pr = enc.rows[0].cells[1].paragraphs[0]; pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
pr.add_run().add_picture(str(AQUI / "logo_ypf.png"), width=Inches(1.3))
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("INFORME FINAL DEL PROYECTO"); r.bold = True; r.font.size = Pt(20); r.font.color.rgb = AZUL
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("YPF frente al mercado y por regiones: análisis de precios, regresión y clasificación"); r.bold = True; r.font.size = Pt(13)
for txt in ("Práctica profesionalizante - ISFDyT N.º 57 Juana Paula Manso",
            "Metodología CRISP-DM | Python, Orange y Power BI", "Fecha: 25 de noviembre de 2026"):
    q = doc.add_paragraph(txt); q.alignment = WD_ALIGN_PARAGRAPH.CENTER


def fy(nivel, grupo):
    return YR[(YR.nivel == nivel) & (YR.grupo == grupo)].iloc[0]


def ic(r):
    return f"{n(r.ic95_inf,1)} a {n(r.ic95_sup,1)}" if pd.notna(r.ic95_inf) else "n insuficiente"


tot = fy("Total", "Mes x producto x region")

ev, va = R["evaluacion_2026"], R["validacion_sep_dic_2025"]
rg, cl = ev["regresion"], ev["clasificacion"]["random_forest"]

# ---- 1 ----------------------------------------------------------------------------
doc.add_heading("1. Resumen ejecutivo", 1)
parrafo(doc, "El proyecto analiza los precios minoristas de combustibles en surtidor publicados en el dataset "
        "oficial de Argentina. Se construyeron dos modelos Random Forest: uno de regresión (estimar el precio) y uno "
        "de clasificación (determinar si un registro es Cara o Barata respecto del mercado de su mes). Los modelos "
        f"se entrenaron con 2024-2025 ({n(R['filas_entrenamiento'])} filas) y se evaluaron con los datos disponibles "
        f"de 2026 ({n(R['filas_evaluacion_2026'])} filas, enero a septiembre).")
parrafo(doc, "Principales resultados sobre 2026: ")
lista(doc, [
    f"Regresión: error absoluto medio (MAE) de ${n(rg['rf_precio_pronosticado']['mae'],2)} contra "
    f"${n(rg['baseline_ultimo_mes_producto']['mae'],2)} del baseline de último precio y "
    f"${n(rg['baseline_mediana_global']['mae'],2)} del baseline de mediana; R² = {n(rg['rf_precio_pronosticado']['r2'],2)}.",
    f"Clasificación: exactitud {p(cl['exactitud'])} contra {p(ev['clasificacion']['baseline_clase_frecuente']['exactitud'])} "
    f"del baseline; AUC {n(cl['auc'],2)}; F1 de la clase Cara {n(cl['f1_cara'],2)}.",
    f"YPF frente al resto del mercado: en una comparación controlada por mes, producto y región, YPF informa precios "
    f"{n(abs(tot.dif_pct),1)} % más bajos (IC 95 %: {ic(tot)} puntos), con la diferencia concentrada en 2025; en 2026 no se distingue de cero.",
    "El precio relativo de cada estación frente al mercado (bandera, provincia, producto) es difícil de predecir con "
    "las variables disponibles: la mejora se concentra en proyectar el nivel general de precios.",
    "2026 no se usa para entrenar por su cobertura mensual despareja; 2027 es un escenario estadístico, no un dato oficial.",
])
parrafo(doc, "Respecto del informe de avance, se corrigieron la definición de clases, el tratamiento de la inflación y la "
        "validación temporal, y se agregaron el flujo de Orange, las tablas para Power BI y la bitácora de limpieza.")

# ---- 2 ----------------------------------------------------------------------------
doc.add_heading("2. Comprensión del negocio", 1)
parrafo(doc, "Objetivo principal: analizar la bandera nacional YPF frente al resto del mercado, por región y producto, y estimar "
        "si una estación vende un producto por encima o por debajo del mercado. Objetivos técnicos y criterios de éxito:")
tabla(doc, ["Objetivo técnico", "Criterio de éxito"], [
    ("Comparar YPF con el resto del mercado por región y producto",
     "Diferencia de precio con intervalo de confianza, controlada por mes, producto y región"),
    ("Estimar el precio de un producto en una estación", "MAE menor que los baselines en datos no vistos"),
    ("Clasificar Cara / Barata", "Exactitud y AUC superiores al baseline de clase frecuente"),
    ("Separar dato real de proyección", "Etiquetado explícito de 2026 (parcial) y 2027 (escenario)"),
    ("Reproducibilidad", "Un script regenera datos, modelos, tablas y flujo de Orange"),
], [3.0, 3.6])

# ---- 3 ----------------------------------------------------------------------------
doc.add_heading("3. Comprensión de los datos", 1)
parrafo(doc, "Fuente: CSV oficial de precios en surtidor (resolución 314/2016), descarga actualizada: 36.669 filas y 19 columnas "
        "(estación, bandera, producto, horario, provincia, región, localidad, precio, fecha y coordenadas). Los hallazgos de "
        "calidad fueron:")
_c25 = COB[(COB.fecha_mes >= "2025-01-01") & (COB.fecha_mes < "2026-01-01")]
_c26 = COB[COB.fecha_mes >= "2026-01-01"]
_junio = COB[COB.fecha_mes == "2025-06-01"].iloc[0]
_resto25 = _c25[_c25.fecha_mes != "2025-06-01"]
_b = BIT.set_index("paso")
_n_periodo = int(_b.loc["3. Periodo de estudio: 2024 en adelante", "filas_eliminadas"])
_n_dup = int(_b.loc["5. Duplicados por estacion-producto-horario-mes", "filas_eliminadas"])
_n_ban = int(_b.loc["4. Banderas sin identificacion confiable", "filas_eliminadas"])
_n_rec = int(AUDI["Filas con precio recuperado (formato x.xxx.000)"])
lista(doc, [
    "El 21,7 % de los registros no tiene región (7.955 filas); se puede recuperar a partir de la provincia.",
    "398 registros (368 de Shell) tienen el precio mal formateado en el origen, por ejemplo “13.700.000” en lugar de 1.370. "
    "Un lector estándar los toma como nulos y descarta surtidores enteros. El valor es recuperable dividiendo por 10.000 "
    "y se valida contra la mediana de su producto y mes (rango de 0,68 a 1,04 veces la mediana).",
    f"Entre 2016 y 2023 hay solo {n(_n_periodo)} filas, con precios en pesos de otra época (por debajo de $50).",
    f"La cobertura mensual es muy despareja. Junio de 2025 concentra {n(_junio.registros)} filas ({n(_junio.estaciones)} estaciones), más de la "
    f"mitad del conjunto de entrenamiento; los demás meses de 2025 tienen entre {n(_resto25.registros.min())} y {n(_resto25.registros.max())} filas.",
    f"2026 llega solo hasta septiembre y cada mes cubre una muestra distinta de estaciones (de {n(_c26.estaciones.min())} a {n(_c26.estaciones.max())}).",
    f"Hay registros duplicados para una misma estación, producto, horario y mes ({n(_n_dup)} filas) y banderas sin identificación ({n(_n_ban)}).",
])
c26 = COB[COB.fecha_mes >= "2025-01-01"]
figura(doc, "cobertura_mensual.png", 5.8, "Figura 1. Registros por mes. En naranja, 2026 (parcial).")
filas = [(m[:7], n(r), n(e)) for m, r, e in zip(c26.fecha_mes, c26.registros, c26.estaciones) if m >= "2026-01-01"]
parrafo(doc, "Cobertura de 2026 disponible:")
tabla(doc, ["Mes", "Registros", "Estaciones"], filas, [1.6, 1.6, 1.6])
parrafo(doc, "Conclusión: 2026 no está “sucio”, está incompleto y cargado con rezago. Por eso se usa solo como evaluación.")

# ---- 4 ----------------------------------------------------------------------------
doc.add_heading("4. Limpieza y bitácora de decisiones", 1)
parrafo(doc, "El script registra cuántas filas elimina cada paso (archivo powerbi/bitacora_limpieza.csv):")
tabla(doc, ["Paso", "Filas restantes", "Filas eliminadas", "Decisión"],
      [(r.paso, n(r.filas_restantes), n(r.filas_eliminadas), r.decision) for r in BIT.itertuples()],
      [2.0, 0.9, 0.9, 2.8], tam=8.5)
parrafo(doc, f"Resultado: {n(R['filas_entrenamiento'])} filas de entrenamiento ({n(R['estaciones_unicas_entrenamiento'])} estaciones), "
        f"{n(R['filas_evaluacion_2026'])} de evaluación 2026 ({n(R['estaciones_unicas_evaluacion_2026'])} estaciones) y "
        f"{n(R['filas_validacion_sep_dic_2025'])} para la validación interna de septiembre a diciembre de 2025.")
doc.add_heading("Decisiones tomadas y alternativas descartadas", 2)
tabla(doc, ["Decisión", "Motivo", "Alternativa descartada", "Efecto"], [
    ("Recuperar precios mal formateados", "398 precios del origen con formato “x.xxx.000” (368 de Shell) se perdían como nulos", "Descartarlos", "Se recuperan 370 filas del período y 45 surtidores"),
    ("Estudiar solo 2024-2026", f"2016-2023: {n(_n_periodo)} filas en pesos de otra época", "Mantener todos los años",
     "Base coherente en valores"),
    ("No entrenar con 2026", "Cobertura parcial y despareja (enero-septiembre)", "Entrenar con todo",
     "2026 es una prueba fuera de muestra"),
    ("Entrenar con 2024-2025", "Es la base con más meses; se documenta que junio 2025 pesa más de la mitad",
     "Solo 2025", "Más filas; limitación declarada"),
    ("Recuperar región desde provincia", "21,7 % de región vacía", "Eliminar esas filas", "No se pierden 7.955 filas"),
    ("Cara = precio mayor a la mediana de su producto en el mismo mes",
     "Contra medianas de 2025, casi todo 2026 salía “Cara” por inflación (132 Baratas vs 6.017 Caras en el avance)",
     "Medianas de 2025 para 2026", f"Clases equilibradas ({p(ev['clasificacion']['baseline_clase_frecuente']['exactitud'])} Barata en 2026)"),
    ("Predecir precio relativo y multiplicar por un índice de tendencia",
     "Random Forest no extrapola precios fuera del rango visto (R² de -0,72 en el avance)",
     "Random Forest sobre el precio directo", f"R² de {n(rg['rf_precio_pronosticado']['r2'],2)} en 2026"),
    ("Quitar año y mes de las variables", "Cambian con la inflación y la cobertura, y el modelo no los extrapola",
     "Incluirlos", "Modelo más estable"),
    ("Duplicados: conservar la vigencia más reciente", "La clave anterior incluía el precio y dejaba duplicados",
     "Conservar el primero", "Un precio por estación-producto-horario-mes"),
], [1.6, 2.0, 1.4, 1.5], tam=8.5)

doc.add_heading("4.1 Auditoría de cobertura de surtidores y controles de calidad", 2)
parrafo(doc, "Se verificó que los datos de regresión y clasificación incluyen a todos los surtidores que sobreviven a la limpieza y que "
        "cada surtidor de 2026 recibe una predicción:")
tabla(doc, ["Conjunto", "Filas", "Surtidores"], [(r.conjunto, n(r.filas), n(r.surtidores)) for r in AUD.itertuples()], [3.4, 1.4, 1.4])
parrafo(doc, f"De los {n(AUD.surtidores.iloc[0])} surtidores del archivo original, {n(AUD.surtidores.iloc[1])} quedan en el período de estudio; los demás "
        "operan solo antes de 2024 o no tienen ningún precio válido. Antes de recuperar los precios mal formateados se perdían 45 surtidores "
        "más, casi todos Shell de Buenos Aires y Capital Federal.")
pv_ = AUDR.pivot(index="region", columns="conjunto", values=["filas", "surtidores"])
tabla(doc, ["Región", "Filas entren.", "Surtidores entren.", "Filas 2026", "Surtidores 2026"], [
    (r_, n(pv_[("filas", "Entrenamiento 2024-2025")][r_]), n(pv_[("surtidores", "Entrenamiento 2024-2025")][r_]),
     n(pv_[("filas", "Evaluacion 2026")][r_]), n(pv_[("surtidores", "Evaluacion 2026")][r_])) for r_ in pv_.index],
    [1.3, 1.2, 1.5, 1.2, 1.4])
lista(doc, [
    f"Solo {n(AUDI['Surtidores de 2026 que tambien estan en el entrenamiento (%)'],1)} % de los surtidores de 2026 también está en el entrenamiento: "
    "el modelo se evalúa sobre todo con surtidores nuevos, por lo que no puede apoyarse en el historial de cada surtidor.",
    f"{n(AUDI['Surtidores que aparecen en un solo mes (%)'],1)} % de los surtidores aparece en un único mes, consecuencia de la muestra rotativa del origen.",
    "Las regiones siguen la clasificación del origen; por ejemplo, Tucumán figura en Cuyo y La Pampa en Patagonia.",
])
tabla(doc, ["Control", "Resultado", "Detalle"], [(r.control, r.resultado, r.detalle) for r in AUDC.itertuples()], [3.6, 0.9, 2.1], tam=8.5)

# ---- 5 (nueva) -----------------------------------------------------------------
def fy(nivel, grupo):
    return YR[(YR.nivel == nivel) & (YR.grupo == grupo)].iloc[0]


def ic(r):
    return f"{n(r.ic95_inf,1)} a {n(r.ic95_sup,1)}" if pd.notna(r.ic95_inf) else "n insuficiente"


tot = fy("Total", "Mes x producto x region")
tot_sj = fy("Total", "Sin junio 2025 (volcado masivo)")
tot_loc = fy("Total", "Mes x producto x localidad")
y25, y26, y24 = fy("Anio", "2025"), fy("Anio", "2026"), fy("Anio", "2024")
doc.add_heading("5. YPF frente al resto del mercado y por regiones", 1)
doc.add_heading("5.1 Método de comparación", 2)
parrafo(doc, "La cobertura del dataset cambia mucho de un mes a otro, por lo que comparar el precio promedio de YPF con el del "
        "resto mezclaría meses, productos y regiones distintos. Por eso la comparación se hace dentro de cada celda "
        "mes x producto x región, con al menos 3 registros de YPF y 3 del resto. En cada celda se calcula la diferencia entre "
        "la mediana de YPF y la mediana del resto del mercado; luego se promedian las diferencias ponderando por la cantidad "
        "de registros de YPF. El intervalo de confianza de 95 % se obtiene con bootstrap sobre las celdas. Como control "
        "adicional se repite la comparación dentro de la misma localidad.")
doc.add_heading("5.2 Resultado general y por región", 2)
parrafo(doc, f"En {n(tot.celdas)} celdas comparables, YPF informa precios {n(abs(tot.dif_pct),1)} % más bajos que el resto del "
        f"mercado (intervalo de confianza 95 %: {ic(tot)} puntos) y es más barata en el {n(tot.pct_celdas_ypf_mas_barata,0)} % de las "
        f"celdas. Comparando dentro de la misma localidad el resultado es parecido ({n(tot_loc.dif_pct,1)} %, "
        f"{n(tot_loc.celdas)} celdas). Si se excluye junio de 2025, un mes con un volcado masivo de datos, la diferencia baja a "
        f"{n(tot_sj.dif_pct,1)} % (intervalo {ic(tot_sj)}).")
figura(doc, "ypf_region_producto.png", 6.4, "Figura 5. Diferencia de precio de YPF frente al resto, por región y producto.")
reg_rows = []
for rg_ in YR[YR.nivel == "Region"].sort_values("dif_pct").itertuples():
    reg_rows.append((rg_.grupo, n(rg_.celdas), n(rg_.dif_pct, 1) + " %", ic(rg_), n(rg_.pct_celdas_ypf_mas_barata, 0) + " %"))
tabla(doc, ["Región", "Celdas comparables", "Diferencia YPF vs. resto", "IC 95 % (puntos)", "% de celdas con YPF más barata"],
      reg_rows, [1.3, 1.1, 1.4, 1.4, 1.4])
parrafo(doc, "En todas las regiones YPF aparece por debajo del resto del mercado. La diferencia es mayor en NEA y en la región "
        "Pampeana, y menor en NOA. La región NEA tiene solo 8 celdas, y todas se concentran en 2025, por lo que su resultado es "
        "menos firme.")
prod = YR[YR.nivel == "Producto"].set_index("grupo")
gnc = prod.loc["GNC"]
parrafo(doc, f"Por producto, la diferencia se da en los combustibles líquidos (entre {n(abs(prod.loc['Nafta (súper) entre 92 y 95 Ron'].dif_pct),1)} % "
        f"en nafta súper y {n(abs(prod.loc['Gas Oil Grado 3'].dif_pct),1)} % en Gas Oil Grado 3). En GNC la diferencia es de solo "
        f"{n(abs(gnc.dif_pct),1)} % y el intervalo de confianza ({ic(gnc)}) incluye el cero: no hay evidencia de diferencia.")
doc.add_heading("5.3 Evolución en el tiempo", 2)
tabla(doc, ["Año", "Celdas comparables", "Diferencia YPF vs. resto", "IC 95 % (puntos)"], [
    ("2024", n(y24.celdas), n(y24.dif_pct, 1) + " %", ic(y24)),
    ("2025", n(y25.celdas), n(y25.dif_pct, 1) + " %", ic(y25)),
    ("2026 (enero-septiembre)", n(y26.celdas), n(y26.dif_pct, 1) + " %", ic(y26)),
], [2.0, 1.4, 1.8, 1.4])
figura(doc, "ypf_region_anio.png", 4.4, "Figura 6. Diferencia YPF vs. resto por región y año (azul: YPF más barata).")
parrafo(doc, f"La ventaja de precio de YPF está bien respaldada en 2025 ({n(y25.dif_pct,1)} %). En 2026 baja a {n(y26.dif_pct,1)} % y "
        "su intervalo incluye el cero, por lo que no puede afirmarse que YPF siguiera siendo más barata. En 2024 hay muy pocas "
        "celdas para concluir.")
doc.add_heading("5.4 Peso de YPF en la muestra", 2)
sh = YM.groupby("fecha_mes").apply(lambda d: d.estaciones_ypf.sum() / d.estaciones_total.sum() * 100)
parrafo(doc, f"El porcentaje de estaciones YPF dentro de las estaciones informadas cambia de {n(sh.min(),1)} % a {n(sh.max(),1)} % según "
        f"el mes. En junio de 2025 llega a {n(sh['2025-06-01'],1)} %, y desde septiembre de 2025 queda entre {n(sh['2025-09-01':].min(),1)} % y "
        f"{n(sh['2025-09-01':].max(),1)} %. Esa variación se debe a qué estaciones se cargaron cada mes, no a un cambio real "
        "del mercado. Por eso el análisis no calcula participación de mercado: solo compara precios dentro de cada mes, producto "
        "y región.")
figura(doc, "ypf_muestra.png", 5.6, "Figura 7. Porcentaje de estaciones YPF en las estaciones informadas, por región y mes.")
doc.add_heading("5.5 YPF en la clasificación Cara / Barata (evaluación 2026)", 2)
filas_c = []
for r_ in sorted(YCL.region.unique()):
    a_ = YCL[(YCL.region == r_) & (YCL.grupo_bandera == "YPF")]
    b_ = YCL[(YCL.region == r_) & (YCL.grupo_bandera == "Resto del mercado")]
    if len(a_) and len(b_):
        a_, b_ = a_.iloc[0], b_.iloc[0]
        nota = "" if a_.registros >= 50 else " (n bajo)"
        filas_c.append((r_, n(a_.registros) + nota, n(a_.pct_cara_real, 1) + " %", n(b_.pct_cara_real, 1) + " %",
                        n(a_.pct_cara_predicha, 1) + " %", n(b_.pct_cara_predicha, 1) + " %"))
tabla(doc, ["Región", "Registros YPF 2026", "% Cara real YPF", "% Cara real resto", "% Cara predicho YPF", "% Cara predicho resto"],
      filas_c, [1.1, 1.2, 1.0, 1.0, 1.1, 1.1], tam=8.5)
n26 = int((YCL[YCL.grupo_bandera == "YPF"].registros).sum())
parrafo(doc, f"En la evaluación de 2026 hay solo {n(n26)} registros de YPF ({n(n26 / R['filas_evaluacion_2026'] * 100,1)} % del total), "
        "por lo que los resultados por región son frágiles. Donde hay más registros (Centro, Pampeana y Patagonia), la proporción "
        "real de precios Cara es menor en YPF que en el resto, coherente con el resultado de 5.2. El modelo asigna a YPF una "
        "probabilidad de Cara más baja que al resto, pero no está bien calibrado en términos absolutos (por ejemplo, en la región "
        "Pampeana predice 0 % de Caras para YPF cuando en realidad son alrededor de 31 %). Se recomienda usarlo para ordenar "
        "registros más que para estimar porcentajes exactos.")
doc.add_heading("5.6 Cómo interpretar estos resultados", 2)
lista(doc, [
    "Los datos son precios informados por las estaciones; la diferencia no prueba por sí sola que YPF fije precios más bajos.",
    "Pueden influir las fechas de actualización de cada estación, el tipo de estación y la ubicación dentro de la región; "
    "la comparación por localidad controla una parte de esto, pero no todo.",
    "La conclusión sólida es para 2025; para 2026 la muestra de YPF es chica y la diferencia no se distingue de cero.",
    "El análisis no permite afirmar que YPF sea la bandera con mayor participación en el mercado nacional.",
])

# ---- 5 ----------------------------------------------------------------------------
doc.add_heading("6. Modelado", 1)
parrafo(doc, "Variables: bandera, producto, tipo de horario, provincia y región (codificación one-hot). "
        "Ambos modelos son Random Forest de 200 árboles, hoja mínima de 5 observaciones y semilla fija (42); "
        "el clasificador usa pesos de clase balanceados.")
lista(doc, [
    "Regresión: se predice el precio relativo (precio dividido por la mediana de su producto y mes). Para obtener el precio "
    "se multiplica por un índice de referencia proyectado con una tendencia logarítmica lineal por producto, ajustada con "
    "los últimos 12 meses observados del conjunto de entrenamiento.",
    "Clasificación: clase Cara si el precio supera la mediana de su producto en el mismo mes.",
    "Baselines: mediana global del precio y último precio mediano por producto (regresión); clase más frecuente (clasificación).",
    "Validación temporal: (a) entrenar con 2024 y enero-agosto de 2025 y validar con septiembre-diciembre de 2025; "
    "(b) entrenar con 2024-2025 y evaluar con 2026.",
])

# ---- 6 ----------------------------------------------------------------------------
doc.add_heading("7. Resultados", 1)
doc.add_heading("7.1 Regresión", 2)


def fila_reg(nombre, k):
    return (nombre, n(va["regresion"][k]["mae"], 2), n(ev["regresion"][k]["mae"], 2),
            n(ev["regresion"][k]["rmse"], 2), n(ev["regresion"][k]["r2"], 2))


tabla(doc, ["Modelo", "MAE val. sep-dic 2025", "MAE 2026", "RMSE 2026", "R² 2026"], [
    fila_reg("Baseline: mediana global", "baseline_mediana_global"),
    fila_reg("Baseline: último precio del producto", "baseline_ultimo_mes_producto"),
    fila_reg("Random Forest + índice proyectado", "rf_precio_pronosticado"),
    fila_reg("Random Forest + índice de mercado conocido", "rf_con_indice_de_mercado_conocido"),
], [2.5, 1.1, 0.9, 0.9, 0.8])
figura(doc, "real_vs_predicho.png", 6.0, "Figura 2. Precio real vs. predicho en 2026 (muestra de 3.000 registros).")
lista(doc, [
    f"El Random Forest reduce el MAE de 2026 de ${n(rg['baseline_ultimo_mes_producto']['mae'],0)} a "
    f"${n(rg['rf_precio_pronosticado']['mae'],0)} respecto del último precio conocido.",
    f"Si se conociera el nivel de mercado del mes, el MAE bajaría a ${n(rg['rf_con_indice_de_mercado_conocido']['mae'],0)}: "
    "la mayor parte del error restante proviene de proyectar la inflación, no del modelo de estaciones.",
    f"El componente de posicionamiento relativo casi no mejora al baseline (MAE relativo {n(rg['rf_precio_relativo']['mae'],4)} "
    f"contra {n(rg['rf_precio_relativo']['baseline_mae'],4)}). Solo {n(PCT_VISTAS,1)} % de las estaciones de 2026 aparece en el "
    "entrenamiento, y bandera, provincia y producto explican poco de la diferencia de precio entre estaciones.",
])
doc.add_heading("7.2 Clasificación", 2)
cv = va["clasificacion"]["random_forest"]
tabla(doc, ["Métrica", "Validación sep-dic 2025", "Evaluación 2026"], [
    ("Exactitud - baseline clase frecuente", p(va["clasificacion"]["baseline_clase_frecuente"]["exactitud"]),
     p(ev["clasificacion"]["baseline_clase_frecuente"]["exactitud"])),
    ("Exactitud - Random Forest", p(cv["exactitud"]), p(cl["exactitud"])),
    ("Precisión (Cara)", p(cv["precision_cara"]), p(cl["precision_cara"])),
    ("Recall (Cara)", p(cv["recall_cara"]), p(cl["recall_cara"])),
    ("F1 (Cara)", p(cv["f1_cara"]), p(cl["f1_cara"])),
    ("AUC", n(cv["auc"], 3), n(cl["auc"], 3)),
], [2.9, 1.8, 1.8])
figura(doc, "matriz_confusion.png", 3.0, "Figura 3. Matriz de confusión en 2026.")
mc = cl["matriz_confusion"]
parrafo(doc, f"El modelo supera al baseline, pero su poder de separación es moderado (AUC {n(cl['auc'],2)}). Tiende a "
        f"clasificar como Cara ({n(mc[0][1])} Baratas clasificadas como Cara y {n(mc[1][0])} Caras clasificadas como Barata), "
        "por lo que prioriza el recall de la clase Cara sobre la precisión.")

# ---- 7 ----------------------------------------------------------------------------
doc.add_heading("8. Escenario 2027", 1)
inf = R["aumento_anual_supuesto_en_proyeccion_pct"]
parrafo(doc, "El archivo proyeccion_2027.csv estima el precio mensual de las combinaciones de bandera, provincia, región, "
        "producto y horario observadas desde 2025. Se obtiene de multiplicar el precio relativo predicho por un índice de "
        "referencia que extiende la tendencia de los últimos 12 meses observados. Aumento anual implícito por producto: "
        + "; ".join(f"{k.replace('Nafta (premium) de más de 95 Ron', 'Nafta premium').replace('Nafta (súper) entre 92 y 95 Ron', 'Nafta súper')}: {n(v,1)} %" for k, v in inf.items()) + ".")
figura(doc, "tendencia_proyeccion.png", 5.8, "Figura 4. Precio mediano real y escenario 2027 (línea punteada).")
parrafo(doc, "Es un escenario estadístico: no incorpora impuestos, subsidios, tipo de cambio, costo internacional ni "
        "decisiones regulatorias, y no debe presentarse como dato oficial ni como anuncio de aumentos.")

# ---- 9 ----------------------------------------------------------------------------
doc.add_heading("9. Trabajo en Orange", 1)
parrafo(doc, "El archivo Flujo_Orange_Combustibles.ows contiene 23 widgets y 28 conexiones, verificados cargando el archivo "
        "en Orange 3.41. Las rutas son relativas: se abre desde la carpeta del proyecto. Los widgets File apuntan a los CSV "
        "de la carpeta orange/, donde la variable objetivo ya está marcada como clase.")
tabla(doc, ["Bloque", "Widgets y conexiones"], [
    ("1. Exploración", "File (dataset limpio completo) → Data Table, Distributions, Box Plot, Violin Plot, Scatter Plot"),
    ("2. Clasificación", "File (entrenamiento) → Random Forest, Constant, Logistic Regression → Test and Score "
     "(prueba con el File de 2026) → Confusion Matrix y ROC Analysis. Random Forest (modelo) + File 2026 → Predictions"),
    ("3. Regresión", "File (entrenamiento) → Random Forest, Constant, Linear Regression → Test and Score "
     "(prueba con 2026). Random Forest (modelo) + File 2026 → Predictions → Scatter Plot (real vs. predicho)"),
], [1.3, 5.3])
oc, orr = ORA["clasificacion"], ORA["regresion"]
tabla(doc, ["Tarea (evaluación 2026)", "Modelo", "Resultados"], [
    ("Clasificación", "Random Forest", f"Exactitud {p(oc['RF']['CA'])}, AUC {n(oc['RF']['AUC'],3)}, F1 Cara {n(oc['RF']['F1'],3)}"),
    ("Clasificación", "Regresión logística", f"Exactitud {p(oc['Logistica']['CA'])}, AUC {n(oc['Logistica']['AUC'],3)}"),
    ("Clasificación", "Constant (baseline)", f"Exactitud {p(oc['Constante']['CA'])}, AUC {n(oc['Constante']['AUC'],2)}"),
    ("Regresión (precio relativo)", "Random Forest", f"MAE {n(orr['RF']['MAE'],4)}, RMSE {n(orr['RF']['RMSE'],4)}, R² {n(orr['RF']['R2'],3)}"),
    ("Regresión (precio relativo)", "Regresión lineal", f"MAE {n(orr['Lineal']['MAE'],4)}, RMSE {n(orr['Lineal']['RMSE'],4)}, R² {n(orr['Lineal']['R2'],3)}"),
    ("Regresión (precio relativo)", "Constant (media)", f"MAE {n(orr['Media']['MAE'],4)}, RMSE {n(orr['Media']['RMSE'],4)}, R² {n(orr['Media']['R2'],3)}"),
], [1.9, 1.6, 3.1], tam=8.5)
parrafo(doc, f"Orange confirma el resultado de Python: en clasificación los modelos superan al baseline (exactitud alrededor "
        f"de {p(oc['RF']['CA'],0)} contra {p(oc['Constante']['CA'])}), y en regresión del precio relativo ningún modelo mejora de forma clara a la media. En Orange "
        "el modelo de regresión predice el precio relativo, no el precio final. Los valores pueden variar levemente según la "
        "semilla y la versión de Orange.")

# ---- 10 ---------------------------------------------------------------------------
doc.add_heading("10. Tablero en Power BI", 1)
parrafo(doc, "La carpeta powerbi/ contiene las diecinueve tablas listas para importar, el script de Power Query (cargar_datos.pq), "
        "las medidas DAX (medidas_DAX.txt) y la guía paso a paso (GUIA_POWERBI.md). Los modelos de Random Forest se "
        "entrenan en Python; Power BI muestra sus predicciones y métricas (por ejemplo, las medidas MAE, RMSE, R², "
        "exactitud, precisión, recall y F1 se calculan directamente sobre la tabla de predicciones).")
tabla(doc, ["Página", "Contenido", "Mensaje"], [
    ("1. Resumen", "Indicadores, precio mediano por producto", "Visión general y alcance"),
    ("2. Calidad de datos", "Cobertura mensual y bitácora de limpieza", "Por qué 2026 no se usa para entrenar"),
    ("3. Regresión", "Real vs. predicho, MAE, RMSE, R²", "El modelo supera a los baselines"),
    ("4. Clasificación", "Matriz de confusión, métricas, importancia de variables", "Capacidad de separar Cara/Barata"),
    ("5. Escenario 2027", "Precio proyectado y aviso", "Escenario, no dato oficial"),
    ("6. YPF vs. mercado", "Diferencia % por región, producto y año con IC; clasificación por región", "YPF es más barata en 2025; en 2026 no se distingue"),
], [1.4, 2.8, 2.4])
parrafo(doc, "Estado: las tablas, medidas y guía están listas; el archivo .pbix debe armarse en Power BI Desktop siguiendo la guía "
        "(no puede generarse desde Python).", negrita_inicio="")

# ---- 11 ---------------------------------------------------------------------------
doc.add_heading("11. Tiempos", 1)
tm = R["tiempos_segundos"]
parrafo(doc, "Tiempos medidos de ejecución del pipeline (equipo de desarrollo, dataset de 36.669 filas):")
tabla(doc, ["Etapa", "Tiempo"], [
    ("Lectura y limpieza", f"{n(tm['limpieza'],1)} s"),
    ("Entrenamiento y evaluación de los modelos (validación + 2026)", f"{n(tm['modelado'],1)} s"),
    ("Total del script", f"{n(tm['total'],1)} s"),
], [4.2, 1.6])
parrafo(doc, "Tiempos estimados (no medidos) de carga y mantenimiento:")
tabla(doc, ["Tarea", "Estimación"], [
    ("Cargar los 19 CSV en Power BI (aprox. 11 MB en total) y actualizar", "menos de 1 minuto"),
    ("Abrir el flujo de Orange y ejecutar los modelos", "1 a 3 minutos"),
    ("Armar el tablero de Power BI de 6 páginas con la guía", "6 a 8 horas"),
    ("Actualización mensual (descargar CSV, correr script, actualizar Power BI)", "15 a 20 minutos"),
    ("Si el dataset crece a 100 MB", "limpieza y modelado: unos minutos; la carga en Power BI sigue siendo de segundos a pocos minutos"),
], [4.2, 2.4])

# ---- 12 ---------------------------------------------------------------------------
doc.add_heading("12. Limitaciones", 1)
lista(doc, [
    "2026 es parcial y la muestra de estaciones cambia mes a mes.",
    "Junio de 2025 pesa más de la mitad del entrenamiento y 2024 aporta pocas filas.",
    "Solo una parte pequeña de las estaciones de 2026 aparece en el entrenamiento.",
    "El escenario 2027 supone que continúa la tendencia reciente y no incluye variables económicas ni regulatorias.",
    "El poder de predicción del precio relativo entre estaciones es bajo con las variables disponibles.",
    "El peso de YPF en la muestra varía de 3 % a 79 % según el mes: no se calcula participación de mercado.",
    "En 2026 hay pocos registros de YPF (alrededor de 6 %), por lo que la comparación de ese año y el detalle por región son frágiles.",
])

# ---- 13 ---------------------------------------------------------------------------
doc.add_heading("13. Conclusiones y próximos pasos", 1)
lista(doc, [
    "El pipeline es reproducible y documenta cada decisión de limpieza con su impacto en filas.",
    "Separar el nivel de precios del posicionamiento relativo corrigió el problema de extrapolación del Random Forest.",
    "La clasificación Cara/Barata supera al baseline, con poder de separación moderado.",
    f"YPF informa precios alrededor de {n(abs(tot.dif_pct),0)} % más bajos que el resto del mercado en 2025, en todas las regiones y en los combustibles líquidos; en 2026 la diferencia no se distingue de cero.",
    "El proyecto muestra con evidencia por qué una muestra parcial no sirve para estimar participación de mercado.",
])
parrafo(doc, "Próximos pasos: incorporar los meses faltantes de 2026 cuando se publiquen, sumar inflación, tipo de cambio y "
        "precio internacional, probar Gradient Boosting, usar validación rolling-origin, calcular intervalos de predicción "
        "y agregar un efecto por estación cuando haya series más largas por estación.")

doc.add_heading("14. Repositorio y entregables", 1)
parrafo(doc, "Repositorio: https://github.com/glamagonzalez/Analisis-de-precios-de-combustibles")
lista(doc, [
    "generar_datasets_modelos.py, orange_resultados.py, generar_figuras.py, crear_flujo_orange.py y crear_informe_final_word.py",
    "Flujo_Orange_Combustibles.ows y carpeta orange/",
    "Carpeta powerbi/ (tablas, auditoría de cobertura, script de Power Query, medidas DAX y guía)",
    "Carpeta modelos_y_datos/ (modelos, resumen.json y resultados de Orange) y carpeta figuras/",
    "README.md con instrucciones de reproducción",
])

pie = s.footer.paragraphs[0]; pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
rr = pie.add_run("Análisis de precios de combustibles - Práctica Profesionalizante - ISFDyT N.º 57")
rr.font.size = Pt(8); rr.font.color.rgb = RGBColor(100, 100, 100)
doc.save(SALIDA)
print(SALIDA)
