# -*- coding: utf-8 -*-
"""Arma el borrador corregido y completo a partir del .docx exportado de Drive (conserva la plantilla APA)."""
import copy, os, re, sys
import docx
from docx.shared import Cm
from docx.enum.text import WD_COLOR_INDEX, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image, ImageOps

W = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(W)
VA = "/home/user/P3th0n/vistas_auxiliares"
OUT_DIR = "/home/user/P3th0n/documento"
os.makedirs(OUT_DIR, exist_ok=True)
IMG = os.path.join(W, "img"); os.makedirs(IMG, exist_ok=True)


# ---------------------------------------------------------------- imágenes
def trim(src, dst, maxw=2000, thr=242, pad=24, crop=None):
    im = Image.open(src).convert("RGB")
    if crop:
        im = im.crop(crop)
    g = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 255 - thr else 0)
    bb = g.getbbox()
    if bb:
        im = im.crop((max(bb[0] - pad, 0), max(bb[1] - pad, 0), min(bb[2] + pad, im.width), min(bb[3] + pad, im.height)))
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(dst, quality=88)
    return dst


iso = Image.open(os.path.join(SCR, "iso_rot.jpg"))
iso.crop((612, 420, 4060, 2900)).resize((1700, round(2480 * 1700 / 3448)), Image.LANCZOS).save(os.path.join(IMG, "iso_jose.jpg"), quality=86)
I_ISO = os.path.join(IMG, "iso_jose.jpg")
I_VISTAS = trim(f"{VA}/paso_1_vistas_principales.png", os.path.join(IMG, "vistas.png"), crop=(0, 230, 2240, 1200))
I_PARC = trim(f"{VA}/limpias/1_lamina_parcial.png", os.path.join(IMG, "parcial.png"), crop=(0, 200, 2850, 1470))
I_TOTAL = trim(f"{VA}/limpias/2_lamina_total.png", os.path.join(IMG, "total.png"), crop=(0, 200, 2850, 1470))
I_PASO5 = trim(f"{VA}/limpias/3_parcial_a_total.png", os.path.join(IMG, "paso5.png"), crop=(0, 200, 2850, 1470))
I_D1 = trim(f"{VA}/limpias/4_distancias_auxiliar1.png", os.path.join(IMG, "dist1.png"), crop=(0, 200, 2850, 1470))
I_D2 = trim(f"{VA}/limpias/5_distancias_auxiliar2.png", os.path.join(IMG, "dist2.png"), crop=(0, 200, 2850, 1470))
I_ROT = trim(f"{VA}/paso_7_rotacion_3d.png", os.path.join(IMG, "rotacion.png"), crop=(0, 330, 2240, 1150))
I_VERIF = trim(f"{VA}/paso_6_verificacion.png", os.path.join(IMG, "verificacion.png"), crop=(0, 100, 2240, 1200))

# ---------------------------------------------------------------- documento
d = docx.Document(os.path.join(W, "original.docx"))
E = list(d.element.body.iterchildren())          # índices = los del volcado de estructura


def runs_of(text, fmt=""):
    """'A_{F}' -> subíndice. fmt: b negrita, i cursiva, h resaltado amarillo."""
    out = []
    for part in re.split(r"(_\{[^}]*\})", text):
        if not part:
            continue
        if part.startswith("_{"):
            out.append((part[2:-1], fmt + "s"))
        else:
            out.append((part, fmt))
    return out


def P(spec, kind="body", img=None, width=16.0):
    """spec: lista de (texto, fmt) o str. kind: body, cap (sin sangría), img, nota, ref, center."""
    if isinstance(spec, str):
        spec = runs_of(spec)
    p = d.add_paragraph()
    pf = p.paragraph_format
    if kind in ("cap", "img", "nota", "center", "note"):
        pf.first_line_indent = Cm(0)
    if kind in ("img", "nota"):
        pf.line_spacing = 1.0
    if kind == "img":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if kind == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if kind == "ref":
        pf.left_indent = Cm(1.27); pf.first_line_indent = Cm(-1.27)
    for text, fmt in spec:
        for t, f in runs_of(text, fmt) if "_{" in text else [(text, fmt)]:
            r = p.add_run(t)
            r.bold = "b" in f or None
            r.italic = "i" in f or None
            if "s" in f:
                r.font.subscript = True
            if "h" in f:
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    if img:
        p.add_run().add_picture(img, width=Cm(width))
    return p._p


def after(anchor, items):
    for e in items:
        anchor.addnext(e)
        anchor = e
    return anchor


def before(anchor, items):
    for e in items:
        anchor.addprevious(e)


def drop(*els):
    for e in els:
        if e.getparent() is not None:
            e.getparent().remove(e)


def set_text(el, spec):
    """Reemplaza el texto de un párrafo existente. Conserva fuente y negrita del primer run; arma rPr en orden de esquema."""
    rs = [r for r in el.findall(qn("w:r")) if r.find(qn("w:t")) is not None]
    prpr = rs[0].find(qn("w:rPr")) if rs else None
    fonts = copy.deepcopy(prpr.find(qn("w:rFonts"))) if prpr is not None and prpr.find(qn("w:rFonts")) is not None else None
    bold = prpr is not None and prpr.find(qn("w:b")) is not None and prpr.find(qn("w:b")).get(qn("w:val")) in (None, "1", "true")
    for r in el.findall(qn("w:r")):
        el.remove(r)
    if isinstance(spec, str):
        spec = [(spec, "")]
    for text, fmt in spec:
        for t, f in runs_of(text, fmt):
            r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr"); r.append(rpr)
            if fonts is not None:
                rpr.append(copy.deepcopy(fonts))
            if bold or "b" in f:
                rpr.append(OxmlElement("w:b")); rpr.append(OxmlElement("w:bCs"))
            if "i" in f:
                rpr.append(OxmlElement("w:i")); rpr.append(OxmlElement("w:iCs"))
            if "h" in f:
                h = OxmlElement("w:highlight"); h.set(qn("w:val"), "yellow"); rpr.append(h)
            if "s" in f:
                v = OxmlElement("w:vertAlign"); v.set(qn("w:val"), "subscript"); rpr.append(v)
            te = OxmlElement("w:t"); te.text = t; te.set(qn("xml:space"), "preserve"); r.append(te)
            el.append(r)
    ppr = el.find(qn("w:pPr"))
    if ppr is not None and ppr.find(qn("w:rPr")) is not None:
        mark = ppr.find(qn("w:rPr"))
        for tag in ("w:color", "w:sz", "w:szCs", "w:highlight"):
            for x in mark.findall(qn(tag)):
                mark.remove(x)


def to_body(el):
    """Devuelve un párrafo al estilo normal de la plantilla (quita estilo de título y fuentes forzadas)."""
    ppr = el.find(qn("w:pPr"))
    if ppr is not None:
        el.remove(ppr)
    for r in el.findall(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is not None:
            for tag in ("w:rFonts", "w:b", "w:bCs", "w:color", "w:sz", "w:szCs"):
                for x in rpr.findall(qn(tag)):
                    rpr.remove(x)


def page_break_before(el):
    ppr = el.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr"); el.insert(0, ppr)
    for x in ppr.findall(qn("w:pageBreakBefore")):
        ppr.remove(x)
    pos = 0
    for i, ch in enumerate(ppr):
        if ch.tag in (qn("w:pStyle"), qn("w:keepNext"), qn("w:keepLines")):
            pos = i + 1
    pb = OxmlElement("w:pageBreakBefore"); pb.set(qn("w:val"), "1")
    ppr.insert(pos, pb)


def figure(num, title, img=None, nota="", placeholder=None, ref=False, width=16.0, label="Figura"):
    items = [P([(f"{label} {num}.", "b")], "cap"), P([(title, "i")], "cap")]
    if ref:
        items.append(P([("IMAGEN DE REFERENCIA (generada por computador): reemplazar por la foto de su lámina hecha a mano.", "bh")], "cap"))
    if img:
        items.append(P([], "img", img=img, width=width))
    if placeholder:
        items.append(P([(placeholder, "h")], "cap"))
    if nota:
        spec = [("Nota. ", "i")] + (nota if isinstance(nota, list) else [(nota, "")])
        items.append(P(spec, "nota"))
    items.append(P([], "cap"))
    return items


# =========================================================================== PÁGINA DE NOTAS (inicio)
notes = [
    P([("BORRADOR DE TRABAJO — BORRAR ESTA PÁGINA ANTES DE ENTREGAR", "bh")], "center"),
    P([("Cómo usar este borrador", "b")], "cap"),
    P("– Lo resaltado en amarillo es lo que falta completar, confirmar o reemplazar.", "cap"),
    P("– Las imágenes marcadas como «IMAGEN DE REFERENCIA» las generó un computador para indicar qué va en cada sitio. "
      "El profesor pide sus propios dibujos: reemplácenlas por las fotos de sus láminas hechas a mano.", "cap"),
    P([("Correcciones del profesor aplicadas", "b")], "cap"),
    P("1. Título en minúscula, con un solo verbo y relacionado con bocetos y trabajo colaborativo (portada y capítulo 1).", "cap"),
    P("2. Objetivo general ajustado al nuevo título.", "cap"),
    P("3. Eliminados los rótulos resaltados de la portada y todos los comentarios del profesor (texto rojo).", "cap"),
    P("4. Los párrafos del planteamiento del problema vuelven al formato de párrafo de la plantilla (estaban como títulos y entraban al índice).", "cap"),
    P("5. Sección 3.1.2 reescrita en párrafos, sin negritas ni listas, respetando la estructura APA de la plantilla.", "cap"),
    P([("Otras correcciones", "b")], "cap"),
    P("Numeración de figuras corregida (había dos «Figura 3» y dos «Figura 4»); notas de figura con nombre completo y código; "
      "la justificación pasa a 1.1 como indica el índice; «Objetivos General» → «Objetivo General»; nota de la Tabla 1 en formato APA; "
      "se quitaron los ejemplos del profesor (figuras «Realizado por xxx») y las instrucciones en rojo de la plantilla.", "cap"),
    P([("Pendiente antes de entregar", "b")], "cap"),
    P("[ ] Actualizar la tabla de contenido (en Google Docs: clic en el índice → actualizar).", "cap"),
    P("[ ] Llenar la Tabla 1 entre los cuatro y ajustar el párrafo de selección.", "cap"),
    P("[ ] Confirmar los roles de Jose y Davinson.", "cap"),
    P("[ ] Reemplazar las imágenes de referencia por fotos de sus láminas (de frente, con buena luz, sin sombras).", "cap"),
    P("[ ] Bocetos descriptivos explicativo, informativo y storyboard (figuras 11 a 13).", "cap"),
    P("[ ] Capturas de SolidWorks (figuras 17 a 19) y anexos A y F.", "cap"),
    P("[ ] Confirmar Ø del agujero roscado (aquí 3,8 cm, estimado) y del agujero adicional.", "cap"),
    P("[ ] Revisar las conclusiones, verificar las referencias y poner la fecha de entrega.", "cap"),
    P("[ ] Preguntar al profesor: la Tabla 1 evalúa «proyecciones auxiliares» y «escuadras» en los cuatro bocetos; "
      "quizá espera que cada integrante haga las vistas de su propia pieza, no solo de la tuerca.", "cap"),
]
before(E[0], notes)
pb = P([], "cap"); pb_r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); pb_r.append(br); pb.append(pb_r)
before(E[0], [pb])

# =========================================================================== PORTADA
drop(E[0])                                                    # comentario del profesor
set_text(E[1], "Elaboración colaborativa de bocetos de un componente mecánico")
drop(E[11])                                                   # rótulo resaltado
set_text(E[15], "Programa de Ingeniería Mecánica — Expresión Gráfica (informe de proyecto)")
docentes = copy.deepcopy(E[16]); set_text(docentes, "Docentes:"); E[16].addprevious(docentes)
drop(E[18])                                                   # rótulo resaltado
set_text(E[19], [("[Fecha de entrega]", "h")])

# =========================================================================== CAPÍTULO 1
set_text(E[35], "Título: Elaboración colaborativa de bocetos de un componente mecánico")
set_text(E[36], "Planteamiento del Problema y Justificación")
for i in (37, 38, 39, 40):
    to_body(E[i])
after(E[40], [E[56], E[57], E[58]])                           # justificación dentro de 1.1
_ppr = E[56].find(qn("w:pPr"))
if _ppr is not None:
    for _x in _ppr.findall(qn("w:numPr")) + _ppr.findall(qn("w:pStyle")):
        _ppr.remove(_x)
drop(E[41])                                                   # comentario del profesor
set_text(E[44], "Objetivo General")
set_text(E[45], "Elaborar, de manera colaborativa, bocetos exploratorios, descriptivos, persuasivos y técnicos de un "
                "componente mecánico, desde el dibujo a mano alzada hasta el modelado en SolidWorks.")
ppr45 = E[45].find(qn("w:pPr")); ppr45.getparent().remove(ppr45)
E[45].insert(0, copy.deepcopy(E[47].find(qn("w:pPr"))) if E[47].find(qn("w:pPr")) is not None else OxmlElement("w:pPr"))

# =========================================================================== 3.1
before(E[83], [P("Cada integrante propuso un elemento, pieza o componente mecánico a partir de la observación de su entorno y de documentación visual:")])
set_text(E[83], [("Jose Alejandro Julio Pinto (0182669) propuso una tuerca hexagonal para pernos con un agujero adicional en la cara superior, "
                  "que amplía sus funciones al permitir el paso de un pasador o alambre de seguridad que evita que la tuerca se afloje. ", ""),
                 ("[Antes decía que el agujero da «más soporte»; un agujero quita material, por eso se cambió la justificación. Confirmar.]", "h")])
set_text(E[84], "David Alexander Rodriguez Canales (0182683) propuso un soporte fijo para celulares, con mejoras orientadas al uso de herramientas manos libres.")
set_text(E[85], "Brayan Mauricio Ramirez Delgado (10432617771) propuso el diseño y la representación gráfica de una botella de vidrio, "
                "identificando sus componentes, formas y vistas mediante bocetos.")
set_text(E[86], "Davinson Guzman Trujillo (10432610898) propuso una grapa de fijación de rieles utilizada en ascensores, representada con sus vistas "
                "frontal, laterales, superior y posterior.")
# roles
before(E[90], [P("Los roles se asignaron según las fortalezas de cada integrante (roles mentales, sociales y de acción):")])
after(E[91], [P([("(0182669) Acción, Implementador / Dibujante técnico y modelado CAD ", ""), ("[CONFIRMAR]", "h")], "cap"),
              P([("(10432610898) Acción, Finalizador / Revisor de normas APA y calidad del documento ", ""), ("[CONFIRMAR]", "h")], "cap")])
drop(*E[92:97])

# =========================================================================== 3.1.2 (reescrita en párrafos)
tec = [
    P("A partir del contenido de la asignatura se describen los cuatro tipos de boceto empleados en el proyecto, con sus características, "
      "parámetros y técnicas de dibujo asociadas."),
    P([("Bocetos exploratorios (ideación rápida). ", "b"),
       ("Traducen de inmediato el pensamiento abstracto al plano bidimensional y se usan en las primeras fases del diseño para generar muchas "
        "alternativas de forma sin la restricción de la precisión técnica. Se caracterizan por su espontaneidad (trazos rápidos, fluidos y "
        "superpuestos), su baja fidelidad (sin detalles minuciosos ni acabados) y su abstracción, pues priorizan formas geométricas básicas "
        "y siluetas generales. Sus parámetros principales son la cantidad de propuestas, la fluidez del trazo, la variedad conceptual y la "
        "plasticidad de las formas. Se elaboran a mano alzada con lápices blandos (2B a 6B), bolígrafos de tinta fluida y técnicas de "
        "trazado ciego o silueteado rápido.", "")]),
    P([("Bocetos descriptivos (análisis y función). ", "b"),
       ("Explican la anatomía, el funcionamiento y la interacción de los componentes de un objeto para que la idea sea comprensible para "
        "terceros, como profesores, ingenieros o colaboradores. Se caracterizan por su claridad comunicativa (notas técnicas, flechas de "
        "dirección, despieces preliminares y llamadas de texto), su proporcionalidad y la contextualización del uso del objeto. Sus "
        "parámetros son la legibilidad de las notas, la coherencia de las proporciones, la claridad en la explicación del mecanismo y la "
        "correcta aplicación de la perspectiva. Se realizan con estilógrafos de diferentes calibres (0,2 a 0,8 mm) para jerarquizar "
        "líneas, color básico para diferenciar piezas y perspectiva axonométrica simple.", "")]),
    P([("Bocetos persuasivos (presentación y validación). ", "b"),
       ("Son bocetos de alta fidelidad estética que buscan un impacto visual y comercial en clientes o evaluadores, simulando de la forma "
        "más realista posible el acabado final del producto. Se caracterizan por el uso avanzado del color, la luz y la sombra, la "
        "simulación de materiales (plásticos, metales, vidrios, mates y brillos) y la composición escénica en un entorno que potencie su "
        "atractivo. Sus parámetros son la calidad del acabado, el manejo de la teoría del color, el realismo del comportamiento de la luz "
        "y la capacidad de convicción visual. Se elaboran con marcadores a base de alcohol, ilustración digital por capas o renderizado "
        "en software.", "")]),
    P([("Bocetos técnicos (pre-CAD y geometrización). ", "b"),
       ("Traducen el diseño a un lenguaje geométrico normalizado y son la información de entrada para el modelado en CAD. Se caracterizan "
        "por el rigor geométrico, las vistas normalizadas (proyecciones ortogonales e isométricas exactas) y la acotación preliminar de "
        "dimensiones críticas, ejes de simetría y radios de curvatura. Sus parámetros son la precisión de las proyecciones, la "
        "correspondencia entre vistas, el uso correcto del alfabeto de líneas y la viabilidad constructiva. Se realizan con instrumentos "
        "(escuadras, compás y reglas), el método de la cuadrícula y líneas guía para la posterior digitalización.", "")]),
]
after(E[97], tec)
drop(*E[98:132])

# =========================================================================== 3.1.3 (figuras 1–8)
before(E[133], [P("En las figuras 1 a 4 se presentan los mapas mentales con los que cada integrante exploró ideas de forma divergente, "
                  "y en las figuras 5 a 8, los bocetos de exploración resultantes.")])
set_text(E[139], [("Mapa mental, botella de vidrio Jack Daniel's", "i")])
set_text(E[148], [("Mapa mental, grapa de riel", "i")])
set_text(E[142], [("Nota. ", "i"), ("Realizado por Brayan Mauricio Ramirez Delgado (10432617771)", "")])
set_text(E[146], [("Nota. ", "i"), ("Realizado por Jose Alejandro Julio Pinto (0182669)", "")])
set_text(E[150], [("Nota. ", "i"), ("Realizado por Davinson Guzman Trujillo (10432610898)", "")])
set_text(E[152], [("Boceto de exploración, soporte de celulares", "i")])
set_text(E[154], [("Nota. ", "i"), ("Realizado por David Alexander Rodriguez Canales (0182683)", "")])
set_text(E[158], [("Boceto de exploración, botella de vidrio", "i")])
set_text(E[161], [("Nota. ", "i"), ("Realizado por Brayan Mauricio Ramirez Delgado (10432617771)", "")])
set_text(E[162], [("Figura 7.", "")])
set_text(E[163], [("Boceto de exploración, tuerca para pernos", "i")])
set_text(E[165], [("Nota. ", "i"), ("Realizado por Jose Alejandro Julio Pinto (0182669)", "")])
set_text(E[166], [("Figura 8.", "")])
set_text(E[167], [("Boceto de exploración, grapa de riel", "i")])
set_text(E[169], [("Nota. ", "i"), ("Realizado por Davinson Guzman Trujillo (10432610898)", "")])

# =========================================================================== 3.2.1 (figuras 9–13)
desc = [P([("Según la evaluación de la Tabla 1, se desarrolló la tuerca para pernos. Sus bocetos descriptivos se elaboraron en formato "
            "estándar y con instrumentos de dibujo técnico. Las medidas de trabajo son: distancia entre caras s = 7 cm, distancia entre "
            "vértices e = 8,08 cm (e = s / cos 30°), lado del hexágono a = 4,04 cm y espesor m = 3 cm. En las figuras 9 a 13 se "
            "presentan la isometría, las vistas principales y los bocetos descriptivos explicativo, informativo y storyboard. ", ""),
           ("[Confirmar Ø del agujero roscado (3,8 cm estimado) y del agujero adicional.]", "h")])]
desc += figure(9, "Isometría de la tuerca para pernos construida con caja envolvente", img=I_ISO, width=13.5,
               nota=[("Realizado por Jose Alejandro Julio Pinto (0182669). ", ""), ("[Retomar la foto de frente, con buena luz y sin sombras.]", "h")])
desc += figure(10, "Vistas principales de la tuerca: alzado, planta y perfil (tercer diedro)", img=I_VISTAS, ref=True, width=15.5,
               nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
desc += figure(11, "Boceto descriptivo explicativo de la tuerca", placeholder="[INSERTAR FOTO — partes de la tuerca: cuerpo hexagonal, agujero "
               "roscado y agujero adicional, con flechas, llamadas de texto y despiece preliminar.]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
desc += figure(12, "Boceto descriptivo informativo de la tuerca", placeholder="[INSERTAR FOTO — tuerca con cotas principales (s = 7 cm, "
               "e = 8,08 cm, m = 3 cm, Ø de los agujeros) y notas técnicas.]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
desc += figure(13, "Boceto descriptivo storyboard de la tuerca", placeholder="[INSERTAR FOTO — secuencia de uso: 1) roscar la tuerca en el "
               "perno, 2) apretar, 3) pasar el pasador o alambre de seguridad por el agujero adicional.]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
after(E[172], desc)
drop(*E[173:190])

# =========================================================================== 3.2.2 (figuras 14–16)
aux = [
    P("La cara lateral ABCD de la tuerca es un plano inclinado: es perpendicular al plano frontal, por lo que en el alzado se ve de canto "
      "(segmento A_{F}D_{F} – B_{F}C_{F}, a 60° de la horizontal), mientras que en la planta y en el perfil aparece deformada, con el 50 % y el "
      "86,6 % de su área real, respectivamente. Para obtener su verdadera magnitud se trazó la línea de visión LOS1 perpendicular a la cara y la "
      "línea de pliegue paralela a ella; desde cada vértice se trazaron líneas de origen a 90° y sobre ellas se llevaron las distancias medidas "
      "en el perfil desde el eje de referencia."),
    P("La proyección auxiliar parcial (figura 14) muestra solo la cara ABCD en verdadera magnitud: un rectángulo de 4,04 × 3,00 cm (12,12 cm²). "
      "Con una segunda línea de visión, LOS2, trazada desde la auxiliar 1, la cara vuelve a verse de canto; en esta vista las distancias se "
      "toman en el alzado desde LOS1."),
    P("La proyección auxiliar total (figura 15) se obtuvo a partir de la parcial, proyectando con el mismo procedimiento los vértices restantes "
      "(E a L). En la auxiliar 1 la tuerca se ve como tres bandas de 2,02, 4,04 y 2,02 cm, cuya suma coincide con la distancia entre vértices "
      "(8,08 cm), lo que comprueba la construcción. La figura 16 muestra la rotación general de la pieza en 3D."),
]
aux += figure(14, "Proyección auxiliar parcial de la cara inclinada ABCD", img=I_PARC, ref=True, width=16.5,
              nota=[("Realizado por ", ""), ("[nombre (código)]", "h"), (". Escala 1:1.", "")])
aux += figure(15, "Proyección auxiliar total de la tuerca", img=I_TOTAL, ref=True, width=16.5,
              nota=[("Realizado por ", ""), ("[nombre (código)]", "h"), (". La construcción parte de la cara ABCD (proyección parcial).", "")])
aux += figure(16, "Rotación general de la tuerca en 3D (giros de 0°, 90°, 180° y 270°)", img=I_ROT, ref=True, width=16.0,
              nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
after(E[190], aux)
drop(E[191])

# =========================================================================== 3.2.3 (tabla de criterios)
set_text(E[193], [("Para seleccionar el modelo, los cuatro integrantes calificaron cada boceto con los criterios de la Tabla 1, en una escala de 1 "
                   "(deficiente) a 5 (excelente), aplicando el pensamiento convergente. ", ""),
                  ("[COMPLETAR EN GRUPO: Boceto 1 = soporte (David), Boceto 2 = botella (Brayan), Boceto 3 = tuerca (Jose), "
                   "Boceto 4 = grapa (Davinson). Máximo: 65 puntos.]", "h")])
to_body(E[193])
t = d.tables[0]
for c, name in zip(t.rows[2].cells[1:], ("soporte", "botella", "tuerca", "grapa")):
    p = c.paragraphs[0]
    r = p.add_run(); r.add_break(); r2 = p.add_run(f"({name})"); r2.bold = True
set_text(E[196], [("Nota. ", "i"), ("Adaptado de ", ""), ("Moda e projeto: Estratégias metodológicas em design", "i"),
                  (" (p. 174), por M. C. F. Sanches, 2018, Estação das Letras e Cores.", "")])
after(E[196], [P([("De acuerdo con la Tabla 1, la alternativa con mayor puntuación fue la tuerca para pernos (boceto 3), con ", ""),
                  ("[__]", "h"), (" de 65 puntos, por ", ""), ("[razones: funcionalidad, facilidad de representación, mejora innovadora…]", "h"),
                  ("; por esta razón se seleccionó para las fases siguientes. ", ""),
                  ("[Llenen la tabla con honestidad: si gana otro boceto, ajusten este párrafo.]", "h")])])

# =========================================================================== 3.3 (SolidWorks, figuras 17–19)
set_text(E[200], [("La tuerca se modeló en SolidWorks a partir de un croquis en el plano alzado: un polígono de seis lados con distancia entre "
                   "caras de 7 cm, extruido 3 cm (Extruir saliente/base). El agujero roscado se creó con el Asistente para taladro y el agujero "
                   "adicional de la cara superior, con un croquis circular y la operación Extruir corte. ", ""),
                  ("[Ajustar a las operaciones que realmente usaron.]", "h")])
to_body(E[200])
after(E[200], figure(17, "Modelo de la tuerca en SolidWorks sin apariencia", placeholder="[INSERTAR CAPTURA — pieza sin color, con el árbol "
                     "de operaciones visible.]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")]))
set_text(E[202], "Se asignó el material acero y una apariencia metálica, y se generó un renderizado con PhotoView 360 para obtener una "
                 "representación persuasiva del modelo.")
to_body(E[202])
after(E[202], figure(18, "Renderizado de la tuerca", placeholder="[INSERTAR CAPTURA — render con material y fondo.]",
                     nota=[("Realizado por ", ""), ("[nombre (código)]", "h")]))
set_text(E[204], "En el entorno de dibujo de SolidWorks se generó el plano de la pieza en formato A4, con las vistas principales, una vista "
                 "auxiliar de la cara inclinada (Insertar > Vista de dibujo > Auxiliar), las cotas y el rótulo.")
to_body(E[204])
after(E[204], figure(19, "Plano técnico de la tuerca en SolidWorks", placeholder="[INSERTAR CAPTURA — plano A4 con vistas, vista auxiliar, "
                     "cotas y rótulo.]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")]))

# =========================================================================== CAPÍTULO 4 — CONCLUSIONES
page_break_before(E[205])
concl = [
    P([("[BORRADOR: revisen y ajusten las conclusiones con sus resultados reales.]", "h")]),
    P("La elaboración de mapas mentales y bocetos de exploración permitió a cada integrante generar y comparar ideas de piezas mecánicas de su "
      "entorno, y pasar de una idea abstracta a una forma concreta mediante el pensamiento divergente."),
    P("Los bocetos descriptivos y las proyecciones auxiliares mostraron que una cara inclinada solo aparece en verdadera magnitud cuando se observa "
      "perpendicularmente a ella: la cara ABCD de la tuerca, que en el alzado se ve de canto y en la planta con la mitad de su área, se obtuvo con "
      "sus dimensiones reales (4,04 × 3,00 cm) en la vista auxiliar."),
    P([("El modelado en SolidWorks permitió ", ""), ("[completar: precisión del modelo, renderizado y plano obtenidos]", "h"), (".", "")]),
    P([("El trabajo colaborativo, con roles definidos y una tabla de criterios para seleccionar el modelo, mejoró la comunicación y la toma de "
        "decisiones del grupo; ", ""), ("[completar con una dificultad real y cómo la resolvieron]", "h"), (".", "")]),
]
after(E[205], concl)
drop(*E[206:226])

# =========================================================================== REFERENCIAS
page_break_before(E[226])
refs = [
    P([("[Verificar año y edición de cada fuente; dejen solo las que realmente consultaron.]", "h")], "cap"),
    P([("Bertoline, G. R., Wiebe, E. N., Hartman, N. W., & Ross, W. A. (2011). ", ""), ("Fundamentals of graphics communication", "i"),
       (" (6th ed.). McGraw-Hill.", "")], "ref"),
    P([("Giesecke, F. E., Mitchell, A., Spencer, H. C., Hill, I. L., Dygdon, J. T., Novak, J. E., & Lockhart, S. (2016). ", ""),
       ("Technical drawing with engineering graphics", "i"), (" (15th ed.). Peachpit Press.", "")], "ref"),
    P([("International Organization for Standardization. (1996). ", ""),
       ("Technical drawings — Projection methods — Part 2: Orthographic representations", "i"), (" (ISO Standard No. 5456-2:1996).", "")], "ref"),
    P([("International Organization for Standardization. (2012). ", ""),
       ("Fasteners — Hexagon regular nuts (style 1) — Product grades A and B", "i"), (" (ISO Standard No. 4032:2012).", "")], "ref"),
    P([("Jensen, C. H., Helsel, J. D., & Short, D. R. (2004). ", ""), ("Dibujo y diseño en ingeniería", "i"),
       (" (6.ª ed.). McGraw-Hill Interamericana.", "")], "ref"),
    P([("Sanches, M. C. F. (2018). ", ""), ("Moda e projeto: Estratégias metodológicas em design", "i"), (". Estação das Letras e Cores.", "")], "ref"),
]
after(E[226], refs)
drop(E[227], E[228])
drop(*E[229:246])

# =========================================================================== ANEXOS
page_break_before(E[246])
anex = [P("A continuación se presenta la evidencia fotográfica y de apoyo del trabajo individual y grupal.")]
anex += figure("A", "Medición de la tuerca con calibrador", label="Anexo", placeholder="[INSERTAR FOTO — medición de s, e, m y diámetros con "
               "calibrador (pie de rey).]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
anex += figure("B", "Construcción paso a paso: de la proyección auxiliar parcial a la total", label="Anexo", img=I_PASO5, ref=True, width=16.5,
               nota="En verde, las líneas de origen de la proyección parcial (cara ABCD); en azul, las añadidas para la proyección total.")
anex += figure("C", "Distancias de la auxiliar 1: se toman del perfil, desde el eje de referencia (regla de las dos vistas)", label="Anexo",
               img=I_D1, ref=True, width=16.5, nota="Delanteros (A, B, E, F, G, H) a 1 cm de LOS1; traseros (C, D, I, J, K, L) a 4 cm.")
anex += figure("D", "Distancias de la auxiliar 2: se toman del alzado, desde LOS1 (regla de las dos vistas)", label="Anexo",
               img=I_D2, ref=True, width=16.5, nota="A, B, C, D a 3 cm de LOS2; E, H, I, L a 6,5 cm; F, G, J, K a 10 cm.")
anex += figure("E", "Verificación numérica de las proyecciones auxiliares", label="Anexo", img=I_VERIF, width=15.5,
               nota=[("Elaboración propia con apoyo de un script en Python (numpy). ", ""),
                     ("[Opcional: inclúyanlo solo si lo pueden explicar.]", "h")])
anex += figure("F", "Evidencia del trabajo grupal", label="Anexo", placeholder="[INSERTAR FOTOS — el grupo trabajando: reuniones, bocetos, "
               "selección del modelo.]", nota=[("Realizado por ", ""), ("[nombre (código)]", "h")])
after(E[246], anex)
drop(E[247], E[248], E[249], E[250])

pars = d.paragraphs
for i, par in enumerate(pars):
    if re.match(r"^(Figura|Anexo) [0-9A-Z]+\.$", par.text.strip()):
        j = i
        while j < len(pars) and j < i + 5:
            pars[j].paragraph_format.keep_with_next = True
            if pars[j]._p.findall(".//" + qn("w:drawing")) or (j > i + 1 and "INSERTAR" in pars[j].text):
                break
            j += 1

out = os.path.join(OUT_DIR, "Borrador_Entrega_corregido.docx")
d.save(out)
print("guardado:", out)
