from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "Informe_avance_Proyecto_Combustibles.docx"


def sombrear(celda, color):
    sombreado = OxmlElement("w:shd")
    sombreado.set(qn("w:fill"), color)
    celda._tc.get_or_add_tcPr().append(sombreado)


def texto_celda(celda, texto, negrita=False, color=None):
    celda.text = ""
    parrafo = celda.paragraphs[0]
    corrida = parrafo.add_run(str(texto))
    corrida.bold = negrita
    if color:
        corrida.font.color.rgb = RGBColor(*color)
    celda.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def agregar_tabla(documento, encabezados, filas, anchos=None):
    tabla = documento.add_table(rows=1, cols=len(encabezados))
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"
    for i, encabezado in enumerate(encabezados):
        texto_celda(tabla.rows[0].cells[i], encabezado, True)
        sombrear(tabla.rows[0].cells[i], "1F4E78")
        for corrida in tabla.rows[0].cells[i].paragraphs[0].runs:
            corrida.font.color.rgb = RGBColor(255, 255, 255)
    for fila in filas:
        celdas = tabla.add_row().cells
        for i, valor in enumerate(fila):
            texto_celda(celdas[i], valor)
    if anchos:
        for fila in tabla.rows:
            for i, ancho in enumerate(anchos):
                fila.cells[i].width = Inches(ancho)
    documento.add_paragraph()
    return tabla


def configurar_margenes(section):
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)


documento = Document()
seccion = documento.sections[0]
configurar_margenes(seccion)

estilos = documento.styles
estilos["Normal"].font.name = "Aptos"
estilos["Normal"].font.size = Pt(10)
for nombre in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
    estilos[nombre].font.name = "Aptos"

logotipo_instituto = AQUI / "logo_instituto57.png"
logotipo_ypf = AQUI / "logo_ypf.png"

tabla_encabezado = documento.add_table(rows=1, cols=2)
tabla_encabezado.alignment = WD_TABLE_ALIGNMENT.CENTER
tabla_encabezado.autofit = False
if logotipo_instituto.exists():
    tabla_encabezado.rows[0].cells[0].paragraphs[0].add_run().add_picture(
        str(logotipo_instituto), width=Inches(1.55)
    )
if logotipo_ypf.exists():
    parrafo = tabla_encabezado.rows[0].cells[1].paragraphs[0]
    parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    parrafo.add_run().add_picture(str(logotipo_ypf), width=Inches(1.55))

titulo = documento.add_paragraph()
titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
corrida = titulo.add_run("INFORME DE AVANCE DEL PROYECTO")
corrida.bold = True
corrida.font.size = Pt(18)
corrida.font.color.rgb = RGBColor(31, 78, 121)

subtitulo = documento.add_paragraph()
subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
corrida = subtitulo.add_run("Análisis de precios de combustibles")
corrida.bold = True
corrida.font.size = Pt(14)

documento.add_paragraph(
    "Práctica profesionalizante - Instituto de Formación Docente y Técnica N.º 57"
).alignment = WD_ALIGN_PARAGRAPH.CENTER
documento.add_paragraph("Fecha: 22 de noviembre de 2026").alignment = WD_ALIGN_PARAGRAPH.CENTER

documento.add_heading("1. Resumen ejecutivo", level=1)
documento.add_paragraph(
    "El proyecto analiza los precios minoristas de combustibles publicados en un conjunto "
    "histórico de surtidores de Argentina. Durante el desarrollo se realizaron dos "
    "descargas del dataset, una primera exploración y una actualización posterior con una "
    "mayor cantidad de registros. La revisión mostró que los datos de 2026 no tenían una "
    "cobertura mensual completa ni uniforme."
)
documento.add_paragraph(
    "Por ese motivo se tomó una decisión técnica y documental: utilizar 2024 y 2025 como "
    "período real de entrenamiento, reservar los datos disponibles de 2026 para evaluación "
    "y utilizar combinaciones observadas de banderas, provincias, regiones y productos para "
    "generar una proyección orientativa de 2027."
)
documento.add_paragraph(
    "Se construyeron dos modelos Random Forest: uno de regresión para estimar el precio y "
    "uno de clasificación para determinar si un registro corresponde a precio Cara o Barata."
)

documento.add_heading("2. Origen y evolución del conjunto de datos", level=1)
documento.add_paragraph(
    "Primero se descargó una primera versión del archivo oficial de precios en surtidor "
    "para comprender su estructura, variables y calidad. A continuación se realizó un "
    "análisis exploratorio y una limpieza inicial."
)
documento.add_paragraph(
    "Luego se descargó una versión actualizada del dataset. Esta nueva base contenía más "
    "registros y permitió ampliar el análisis, pero también mostró que 2026 estaba incompleto:"
)

agregar_tabla(documento, ["Mes 2026", "Registros disponibles"], [
    ("Enero", "164"), ("Febrero", "286"), ("Marzo", "664"),
    ("Abril", "388"), ("Mayo", "941"), ("Junio", "514"),
    ("Julio", "1.230"), ("Agosto", "1.409"), ("Septiembre", "553"),
])

documento.add_paragraph(
    "La distribución no era uniforme. Algunos meses tenían menos observaciones y los cambios "
    "mensuales estaban acompañados por una cobertura distinta de estaciones y banderas. En "
    "consecuencia, no se consideró válido utilizar 2026 como entrenamiento ni presentar sus "
    "porcentajes como participación real del mercado."
)

documento.add_heading("3. Criterio para utilizar 2024 y 2025", level=1)
documento.add_paragraph(
    "Se decidió trabajar con los años 2024 y 2025 porque ofrecen observaciones reales "
    "mensuales y permiten entrenar modelos sin mezclar datos incompletos. 2024 se utilizó "
    "para validar el proceso temporal y 2025 permitió comprobar la capacidad de generalización."
)

agregar_tabla(documento, ["Período", "Uso en el proyecto"], [
    ("2024", "Validación temporal inicial."),
    ("2024-2025", "Entrenamiento de los modelos finales."),
    ("2025", "Validación temporal intermedia."),
    ("2026", "Evaluación únicamente con datos disponibles."),
    ("2027", "Pronóstico basado en el modelo; no contiene datos reales."),
])

documento.add_heading("4. Limpieza y preparación", level=1)
documento.add_paragraph(
    "El proceso se realizó en el script generar_datasets_modelos.py. Las principales "
    "transformaciones fueron:"
)

limpieza = [
    "Conversión del campo precio de texto a valor numérico.",
    "Conversión de indice_tiempo a fecha.",
    "Creación de las variables anio y mes.",
    "Eliminación de registros con precio, fecha, bandera, producto, región, provincia o horario faltantes.",
    "Exclusión de precios menores a 50 o mayores a 10.000.",
    "Exclusión de banderas sin identificación confiable.",
    "Eliminación de duplicados por estación, producto, horario, dirección, provincia, región y fecha.",
    "Cálculo de estación única mediante el identificador idempresa.",
    "Codificación one-hot de las variables categóricas.",
]
for item in limpieza:
    documento.add_paragraph(item, style="List Bullet")

documento.add_paragraph(
    "La limpieza produjo 19.990 filas reales para el entrenamiento con 2024-2025 y 6.149 "
    "filas disponibles para evaluar con 2026. El conjunto 2026 contiene 909 estaciones "
    "únicas dentro de la muestra utilizada."
)

documento.add_heading("5. Construcción del objetivo de clasificación", level=1)
documento.add_paragraph(
    "Para el modelo de clasificación se creó la variable clase. Se consideró Cara a un "
    "registro cuyo precio superó la mediana correspondiente de 2025 según producto y mes;"
    "los restantes registros se consideraron Barata."
)
documento.add_paragraph(
    "Esta regla permite interpretar el resultado comercialmente: cara significa que el "
    "producto está por encima de la referencia utilizada, no que tenga un precio elevado "
    "por decisión de una bandera o una región determinada."
)

documento.add_heading("6. Modelos desarrollados", level=1)
documento.add_paragraph(
    "Se seleccionó Random Forest porque puede representar relaciones no lineales y combina "
    "muchos árboles de decisión para reducir la variabilidad de una sola regla."
)

agregar_tabla(documento, ["Modelo", "Objetivo", "Evaluación"], [
    ("Random Forest Regressor", "Predecir el precio.", "MAE, RMSE y R²."),
    ("Random Forest Classifier", "Predecir Cara o Barata.", "Accuracy, Precision, Recall, F1 y AUC."),
    ("Baseline de mediana", "Referencia simple para regresión.", "Comparación con el Random Forest."),
    ("Baseline de clase frecuente", "Referencia simple para clasificación.", "Comparación con el Random Forest."),
])

documento.add_paragraph(
    "Los modelos principales se configuraron con 200 árboles, una semilla aleatoria fija "
    "para reproducibilidad y una hoja mínima de dos observaciones. Las variables utilizadas "
    "fueron bandera, producto, horario, provincia, región, año y mes."
)

documento.add_heading("7. Validación temporal y resultados", level=1)
documento.add_paragraph(
    "Para evitar mezclar observaciones futuras se utilizó una partición temporal:"
)
for item in [
    "En la primera validación se entrenó con 2024 y se evaluó con 2025.",
    "En la evaluación final se entrenó con 2024-2025 y se probó con los datos disponibles de 2026.",
    "Las medianas utilizadas para clasificar 2026 provienen de 2025.",
]:
    documento.add_paragraph(item, style="List Bullet")

agregar_tabla(documento, ["Prueba", "Baseline", "Random Forest"], [
    ("MAE de 2025", "330,97", "236,11"),
    ("RMSE de 2025", "No informado", "260,84"),
    ("MAE de 2026", "844,82", "712,00"),
    ("RMSE de 2026", "882,62", "763,94"),
    ("R² de 2026", "No aplica", "-0,7165"),
])

documento.add_paragraph(
    "Los resultados de clasificación sobre 2026 fueron: exactitud 61,38 %, Precision para "
    "Cara 99,73 %, Recall Cara 60,69 %, F1 Cara 75,46 % y AUC 82,67 %. La matriz de "
    "confusión fue 122 Baratas correctas, 10 Baratas clasificadas como Cara, 2.365 Caras "
    "clasificadas como Baratas y 3.652 Caras correctas."
)
documento.add_paragraph(
    "Estos números muestran que el modelo mejora al baseline en regresión, pero el "
    "rendimiento disminuye al pasar de 2025 a 2026. Esto es consistente con la deriva "
    "temporal y con la cobertura irregular del año 2026."
)

documento.add_heading("8. Proyección 2027", level=1)
documento.add_paragraph(
    "El archivo proyeccion_2027.csv contiene una estimación mensual de precios para "
    "combinaciones observadas de bandera, provincia, región, producto y horario."
)
documento.add_paragraph(
    "El resultado de 2027 no debe interpretarse como dato real ni como información oficial "
    "de próximos aumentos. Es una proyección estadística basada en relaciones observadas "
    "durante 2024-2026."
)
documento.add_paragraph(
    "El pronóstico no incorpora explícitamente inflación, impuestos, subsidios, "
    "devaluación, costos internacionales, decisiones regulatorias o cambios de política "
    "empresarial. Por ello debe presentarse como escenario orientativo."
)

documento.add_heading("9. Participación de banderas", level=1)
documento.add_paragraph(
    "La participación fue calculada mediante estaciones únicas identificadas por idempresa,"
    " no mediante la cantidad de filas. Las filas pueden repetir una estación por producto, "
    "horario y vigencia."
)
documento.add_paragraph(
    "YPF puede resaltarse como una compañía estatal con presencia relevante dentro de la "
    "muestra. Sin embargo, no corresponde afirmar que fue la bandera predominante del "
    "mercado nacional sin una muestra completa y representativa."
)

documento.add_heading("10. Dashboard interactivo", level=1)
documento.add_paragraph(
    "Se desarrolló un dashboard con Streamlit que permite filtrar por producto, bandera y "
    "provincia. Presenta tendencia histórica, pronóstico 2027, comparación de métricas, "
    "precio real versus predicho y participación por estaciones únicas."
)
documento.add_paragraph(
    "Para ejecutarlo:"
)
documento.add_paragraph("streamlit run dashboard_ypf.py", style="Intense Quote")

documento.add_heading("11. Conclusiones", level=1)
conclusiones = [
    "El primer dataset permitió comprender el formato y detectar problemas de calidad.",
    "La actualización posterior confirmó la necesidad de separar datos completos de datos incompletos.",
    "El período 2024-2025 fue adecuado como base de entrenamiento.",
    "Los datos disponibles de 2026 fueron útiles para evaluar deriva temporal.",
    "El Random Forest superó al baseline en las pruebas realizadas.",
    "La proyección 2027 es una estimación estadística y no una predicción oficial.",
    "YPF debe presentarse como actor estatal estratégico y relevante en la muestra, no como líder nacional comprobado.",
]
for item in conclusiones:
    documento.add_paragraph(item, style="List Bullet")

documento.add_heading("12. Próximos pasos", level=1)
for item in [
    "Completar el periodo 2026 cuando esté disponible.",
    "Agregar inflación, costo internacional y variables macroeconómicas.",
    "Incorporar validación rolling-origin.",
    "Comparar Random Forest con Gradient Boosting.",
    "Calcular intervalos de predicción.",
    "Actualizar el dashboard mensualmente.",
]:
    documento.add_paragraph(item, style="List Bullet")

documento.add_heading("13. Repositorio y entregables", level=1)
documento.add_paragraph(
    "El proyecto quedó publicado en el repositorio:"
)
parrafo = documento.add_paragraph(
    "https://github.com/glamagonzalez/Analisis-de-precios-de-combustibles"
)
parrafo.style = "Intense Quote"

documento.add_paragraph(
    "Entregables principales: informe CRISP-DM, notebook de análisis, script de limpieza "
    "y modelado, datasets de entrenamiento y evaluación, modelos entrenados, predicciones "
    "2026, proyección 2027 y dashboard interactivo."
)

pie = documento.sections[0].footer.paragraphs[0]
pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
pie_run = pie.add_run("Proyecto de Análisis de Precios de Combustibles - Práctica Profesionalizante")
pie_run.font.size = Pt(8)
pie_run.font.color.rgb = RGBColor(100, 100, 100)

documento.save(SALIDA)
print(SALIDA)
