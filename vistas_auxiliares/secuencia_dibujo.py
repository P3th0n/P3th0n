#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SECUENCIA DE CONSTRUCCIÓN, PASO A PASO (una imagen por paso)
============================================================
Cada hoja se divide en pasos. En cada imagen: lo ya hecho en gris/negro y lo NUEVO en rojo,
con sus cotas de construcción (morado), la escuadra que se usa y la posición en la hoja.
Toda la geometría sale del mismo modelo verificado (proyecciones_auxiliares_tuerca.py).
"""
import os
import textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Arc

import laminas_tablero as T
import guia_dibujo as GD

G = T.G
V = G.V
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guia")
BODY = "Inter"
INK, GRAY, HL, DIMC, PROJ, CEN = "#111111", "#9aa0a6", "#d62828", "#6a35b8", "#16917f", "#2c5aa0"
E, S, M, GAP = G.E, G.S, G.M, G.GAP
cx, cz, r = G.cx, G.cz, G.D_BORE / 2
EX, Q1 = G.EXTRA, G.Q1
f2 = GD.fmt


# ------------------------------------------------------------------------- primitivas (coordenadas de hoja, cm)
def ln(ax, p, q, kind="vis", c=None):
    st = {"vis": dict(color=INK, lw=1.6), "hid": dict(color=INK, lw=0.8, ls=(0, (4, 2.5))),
          "cen": dict(color=CEN, lw=0.6, ls=(0, (9, 2, 1.5, 2))), "con": dict(color=GRAY, lw=0.55),
          "proj": dict(color=PROJ, lw=0.5), "fold": dict(color="#c62828", lw=1.0, ls=(0, (6, 3)))}[kind].copy()
    if c:
        st["color"] = c
        st["lw"] = max(st["lw"], 1.1 if kind != "vis" else 2.0)
    ax.plot([p[0], q[0]], [p[1], q[1]], solid_capstyle="round", **st)


def poly(ax, pts, kind="vis", c=None, closed=True):
    pts = np.asarray(pts, float)
    if closed:
        pts = np.vstack((pts, pts[:1]))
    for a, b in zip(pts[:-1], pts[1:]):
        ln(ax, a, b, kind, c)


def dot(ax, p, c=None, label=None, off=(0.25, 0.25), fs=7):
    ax.plot(*p, "o", ms=3.2, color=c or INK, zorder=6)
    if label:
        ax.text(p[0] + off[0], p[1] + off[1], label, fontsize=fs, color=c or "#c62828", fontfamily=BODY, zorder=7)


def dim(ax, p, q, text, off=0.8, c=None, fs=7):
    G.dim(ax, p, q, text, off=off, fs=fs, color=c or DIMC)


def note(ax, p, text, c=None, fs=7, **kw):
    ax.text(p[0], p[1], text, fontsize=fs, color=c or HL, fontfamily=BODY, zorder=8,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85), **kw)


def view(ax, place, v, c=None, cyl=True, lw=1.6):
    old = (G.C_VIS, G.C_HID)
    if c:
        G.C_VIS, G.C_HID = c, c
    G.draw_view(ax, place, v, lw=lw if not c else lw * 1.2, hidden=True, cyl=cyl)
    G.C_VIS, G.C_HID = old


def sheet(ax, W, H, c=None, title="", num=""):
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, ec="0.7", lw=0.6))
    ax.add_patch(Rectangle((1, 1), W - 2, H - 2, fill=False, ec=c or INK, lw=1.0 if not c else 1.6))
    x0 = W - 15
    ax.add_patch(Rectangle((x0, 1), 14, 3.5, fill=False, ec=c or INK, lw=0.8 if not c else 1.4))
    for yy in (2.2, 3.35):
        ax.plot([x0, x0 + 14], [yy, yy], color=c or INK, lw=0.5)
    for xx in (x0 + 4.5, x0 + 9.0):
        ax.plot([xx, xx], [1, 4.5], color=c or INK, lw=0.5)
    ax.text(x0 + 9.2, 2.8, title, fontsize=6, fontfamily=BODY); ax.text(x0 + 9.2, 1.6, num, fontsize=6, fontfamily=BODY)
    if c:
        dim(ax, (0, H - 3), (1, H - 3), "1", off=0.6, c=DIMC)
        dim(ax, (x0, 4.5), (x0 + 14, 4.5), "14", off=0.6, c=DIMC)
        dim(ax, (W - 1, 1), (W - 1, 4.5), "3,5", off=-0.6, c=DIMC)


# ------------------------------------------------------------------------- render de una secuencia
def render(pdf, name, fmt_name, steps, intro):
    W, H = (29.7, 21.0) if fmt_name == "A4" else (42.0, 29.7)
    for k in range(len(steps)):
        fig = plt.figure(figsize=(29.7 / 2.54, 21.0 / 2.54), facecolor="white")
        ax = fig.add_axes([0.01, 0.06, 0.66, 0.66 * (29.7 / 21.0) * (H / W)])
        ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
        for j in range(k + 1):
            steps[j][2](ax, HL if j == k else None)
        title, text = steps[k][0], steps[k][1]
        fig.text(0.015, 0.95, f"{name} · Paso {k + 1} de {len(steps)}: {title}", fontsize=17, fontfamily=T.HAND, color=INK)
        fig.text(0.015, 0.905, intro, fontsize=8.5, fontfamily=BODY, color="#555")
        y = 0.86
        for par in text:
            for line in textwrap.wrap(par, 52):
                fig.text(0.69, y, line, fontsize=9.2, fontfamily=BODY, color=INK); y -= 0.034
            y -= 0.014
        fig.text(0.69, 0.08, "Rojo = lo que dibujas en este paso\nMorado = medidas para ubicarlo\nGris = construcción ya hecha (línea fina)\n"
                 "Verde = proyectantes", fontsize=8, fontfamily=BODY, color="#666", linespacing=1.6)
        pdf.savefig(fig, facecolor="white")
        fig.savefig(os.path.join(OUT, f"seq_{name.split()[0].lower()}{name.split()[1]}_{k + 1:02d}.png"), dpi=90, facecolor="white")
        plt.close(fig)


# ========================================================================= HOJA 1: vistas principales
OX1, OY1 = GD.OX1, GD.OY1
o1 = np.array([OX1, OY1])
L = lambda x, z: o1 + np.array([x, z])                         # local alzado -> hoja
HEX = [L(*T.pF(V[i])[0]) for i in range(6)]
yT = S + GAP; xR = E + GAP


def h1_marco(ax, c):
    sheet(ax, 29.7, 21.0, c, "Vistas principales", "Nº 3 · 1:1 · A4")


def h1_cuadro(ax, c):
    poly(ax, [L(0, 0), L(E, 0), L(E, S), L(0, S)], "con", c)
    dot(ax, L(0, 0), c, "O")
    if c:
        dim(ax, (0, OY1 + 1.0), (OX1, OY1 + 1.0), f2(OX1), off=0.5)
        dim(ax, (OX1 - 2.6, 0), (OX1 - 2.6, OY1), f2(OY1), off=0.5)
        dim(ax, L(0, 0), L(E, 0), "7", off=-0.8); dim(ax, L(0, 0), L(0, S), "7", off=0.8)


def h1_marcas(ax, c):
    for p in HEX:
        dot(ax, p, c)
    if c:
        dim(ax, L(0, 0), L(Q1, 0), f2(Q1), off=-0.8); dim(ax, L(E - Q1, 0), L(E, 0), f2(Q1), off=-0.8)
        dim(ax, L(0, S), L(Q1, S), f2(Q1), off=0.8); dim(ax, L(E - Q1, S), L(E, S), f2(Q1), off=0.8)
        dim(ax, L(0, 0), L(0, cz), "3,5", off=0.8)


def h1_hex(ax, c):
    poly(ax, HEX, "vis", c)


def h1_circ(ax, c):
    ln(ax, L(-0.6, cz), L(E + 0.6, cz), "cen", c); ln(ax, L(cx, -0.6), L(cx, S + 0.6), "cen", c)
    th = np.linspace(0, 2 * np.pi, 120)
    ax.plot(OX1 + cx + r * np.cos(th), OY1 + cz + r * np.sin(th), color=c or INK, lw=1.6 if not c else 2.0)
    if c:
        dim(ax, L(cx, cz), L(cx + r * 0.71, cz + r * 0.71), "R 1,9", off=0.0, c=DIMC)


def h1_proj(ax, c):
    for x in (0, Q1, E - Q1, E, cx - r, cx + r, cx - EX.r, cx + EX.r):
        ln(ax, L(x, S if x in (0, Q1, E - Q1, E) else S), L(x, yT + M + 0.5), "proj", c)
    for z in (0, cz, S, cz - r, cz + r):
        ln(ax, L(E, z), L(xR + M + 0.5, z), "proj", c)
    if c:
        dim(ax, L(E + 0.8, S), L(E + 0.8, yT), "2", off=-0.5); dim(ax, L(E, -0.9), L(xR, -0.9), "2", off=-0.5)


def h1_planta(ax, c):
    view(ax, lambda P: G.place_top(P) + o1, G.nT, c)
    ln(ax, L(cx, yT - 0.5), L(cx, yT + M + 0.5), "cen", c)
    if c:
        dim(ax, L(E, yT), L(E, yT + M), "3", off=-0.8)
        dim(ax, L(cx + 1.2, yT), L(cx + 1.2, yT + EX.yc), f2(EX.yc), off=0.0)
        note(ax, L(-3.8, yT + M + 0.8), "Vista superior: 7 × 3 a 2 cm del alzado")


def h1_inglete(ax, c):
    corner = L(xR, yT)
    ln(ax, corner, corner + np.array([M + 0.8, M + 0.8]), "con", c)
    for y in (0, EX.yc - EX.r, EX.yc, EX.yc + EX.r, M):
        ln(ax, L(E + 0.0, yT + y), L(xR + y, yT + y), "proj", c)
        ln(ax, L(xR + y, yT + y), L(xR + y, -0.3), "proj", c)
    if c:
        note(ax, corner + np.array([0.6, M + 1.0]), "Línea a 45° (escuadra de 45°):\npasa las profundidades de la\nvista superior a la lateral")


def h1_lateral(ax, c):
    view(ax, lambda P: G.place_right(P) + o1, G.nR, c)
    ln(ax, L(xR - 0.5, cz), L(xR + M + 0.5, cz), "cen", c)
    if c:
        dim(ax, L(xR, -0.9), L(xR + M, -0.9), "3", off=-0.5)


def h1_alzado_ocultas(ax, c):
    for x in (cx - EX.r, cx + EX.r):
        ln(ax, L(x, S), L(x, float(EX.zb(x))), "hid", c)


def h1_cotas(ax, c):
    if not c:
        return
    GD.acotar_vistas(ax, o=o1, color=DIMC, fs=6.5)


STEPS1 = [
    ("Marco y rótulo", ["Marco: rectángulo a 1 cm de cada borde de la hoja (regla T y escuadra para los verticales).",
                        "Rótulo: 14 × 3,5 cm en la esquina inferior derecha, dividido en 3 filas y 3 columnas."], h1_marco),
    ("Origen y recuadro del alzado", [f"Marca O a {f2(OX1)} cm del borde izquierdo y {f2(OY1)} cm del borde inferior.",
                                      "Desde O traza un cuadrado de 7 × 7 cm en línea muy fina (2H): horizontales con la regla T, verticales con la escuadra apoyada en ella."], h1_cuadro),
    ("Puntos del hexágono", [f"Arriba y abajo: marca {f2(Q1)} cm desde cada esquina (4 puntos).",
                             "Izquierda y derecha: marca el punto medio, a 3,5 cm (2 puntos).", "Son los 6 vértices del hexágono."], h1_marcas),
    ("Hexágono", ["Une los 6 puntos con línea firme (HB). Te queda el hexágono con caras planas arriba y abajo.",
                  f"Comprueba: lado superior {f2(G.LADO_SUP)} cm; lados inclinados {f2(G.LADO_INC)} cm."], h1_hex),
    ("Ejes y agujero grande", ["Ejes en trazo-punto por el centro (3,5 ; 3,5), sobresaliendo 0,5 cm.",
                               "Compás con radio 1,9 cm, punta en el centro: circunferencia del agujero (Ø 3,8)."], h1_circ),
    ("Agujero de arriba en el alzado", [f"Dos líneas OCULTAS (trazos de 3 mm) verticales en x = {f2(cx - EX.r)} y {f2(cx + EX.r)} desde O.",
                                        "Bajan desde el borde superior hasta tocar la circunferencia del agujero grande."], h1_alzado_ocultas),
    ("Proyectantes", ["Verticales finas hacia arriba (escuadra apoyada en la regla T) desde cada vértice y desde los bordes de los agujeros.",
                      "Horizontales finas hacia la derecha (regla T) desde las alturas de los vértices y del agujero.",
                      "Deja 2 cm de separación hasta la vista superior y hasta la lateral."], h1_proj),
    ("Vista superior", ["Rectángulo de 7 × 3 cm a 2 cm encima del alzado, entre las proyectantes de los extremos.",
                        f"Aristas visibles en x = {f2(Q1)} y {f2(E - Q1)}. Agujero grande: dos ocultas en x = {f2(cx - r)} y {f2(cx + r)}.",
                        f"Agujero de arriba: circunferencia de radio {f2(EX.r)} con centro en x = 3,5 y a {f2(EX.yc)} cm del borde de abajo de esta vista."], h1_planta),
    ("Línea a 45°", ["Desde la esquina donde se cruzan la prolongación del borde de abajo de la vista superior y el borde izquierdo de la lateral, traza una línea a 45° (escuadra de 45°).",
                     "Desde cada profundidad de la vista superior: horizontal hasta la línea a 45° y luego vertical hacia abajo. Así la lateral tiene las mismas profundidades."], h1_inglete),
    ("Vista lateral derecha", ["Rectángulo de 3 × 7 cm a 2 cm a la derecha del alzado.",
                               f"Arista visible horizontal a 3,5 cm. Agujero grande: ocultas a {f2(cz - r)} y {f2(cz + r)} cm.",
                               f"Agujero de arriba: ocultas verticales en {f2(EX.yc - EX.r)} y {f2(EX.yc + EX.r)} cm, desde arriba hasta {f2(cz + r)} cm, cerradas por una curva que baja a {f2(float(EX.zb(cx + EX.r)))} en el centro."], h1_lateral),
    ("Cotas y repaso", ["Repasa: visibles gruesas (HB, presionando), ocultas en trazos, ejes trazo-punto, construcción muy fina.",
                        "Cotas completas: en cadena (1,75 · 3,5 · 1,75) y totales (7), diámetros, posición del agujero de arriba (1,5) y su profundidad (1,6) en la lateral."], h1_cotas),
]


# ========================================================================= HOJA 2: isométrico
OX2, OY2 = GD.OX2, GD.OY2
o2 = np.array([OX2, OY2])
I = lambda P: GD.iso(np.atleast_2d(np.asarray(P, float)))[0] + o2


def h2_marco(ax, c):
    sheet(ax, 29.7, 21.0, c, "Isométrico", "Nº 2 · 1:1 · A4")


def h2_ejes(ax, c):
    O = I([0, 0, 0])
    for P, nm in (([E + 1.5, 0, 0], "X"), ([0, M + 1.5, 0], "Y"), ([0, 0, S + 1.5], "Z")):
        ln(ax, O, I(P), "con", c); note(ax, I(P) + np.array([0.1, 0.1]), nm, c=c or GRAY)
    dot(ax, O, c, "O", off=(-0.6, -0.3))
    if c:
        ax.add_patch(Arc(O, 3, 3, theta1=-30, theta2=0, color=DIMC, lw=0.8)); note(ax, O + np.array([1.6, -0.55]), "30°", c=DIMC)
        ax.add_patch(Arc(O, 3, 3, theta1=0, theta2=30, color=DIMC, lw=0.8)); note(ax, O + np.array([1.6, 0.25]), "30°", c=DIMC)
        ln(ax, O, O + np.array([3, 0]), "con", DIMC)
        dim(ax, (0, OY2), (OX2, OY2), f2(OX2), off=0.5); dim(ax, (OX2 - 3.0, 0), (OX2 - 3.0, OY2), f2(OY2), off=0.5)


def h2_caja(ax, c):
    lo, hi = np.zeros(3), np.array([E, M, S])
    box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    for a in range(8):
        for b in range(a + 1, 8):
            if np.sum(np.abs(box[a] - box[b]) > 1e-9) == 1:
                ln(ax, I(box[a]), I(box[b]), "con", c)
    if c:
        dim(ax, I([0, 0, 0]), I([E, 0, 0]), "7 (sobre X)", off=-0.8)
        dim(ax, I([0, 0, 0]), I([0, 0, S]), "7 (sobre Z)", off=0.8)
        dim(ax, I([E, 0, 0]), I([E, M, 0]), "3 (sobre Y)", off=-0.7)


def h2_marcas(ax, c):
    for P in ([Q1, 0, 0], [E - Q1, 0, 0], [Q1, 0, S], [E - Q1, 0, S], [0, 0, cz], [E, 0, cz]):
        dot(ax, I(P), c)
    if c:
        dim(ax, I([0, 0, S]), I([Q1, 0, S]), f2(Q1), off=0.6); dim(ax, I([E - Q1, 0, 0]), I([E, 0, 0]), f2(Q1), off=-0.6)
        dim(ax, I([0, 0, 0]), I([0, 0, cz]), "3,5", off=0.6)


def h2_hex(ax, c):
    poly(ax, [I(V[i]) for i in range(6)], "vis", c)


def h2_prisma(ax, c):
    view(ax, lambda P: GD.iso(np.atleast_2d(P)) + o2, G.V_ISO, c, cyl=False)
    if c:
        dim(ax, I(V[0]), I(V[6]), "3", off=-0.6)
        note(ax, I(V[7]) + np.array([0.4, 0.5]), "Paralelas al eje Y de 3 cm\ndesde cada vértice (escuadra 30°)")


def _fourc(ax, c, c3, e1, e2, rad, show_con, kind="vis"):
    Q, Mm, cen, arcs = GD.four_center(np.asarray(c3, float), np.asarray(e1, float), np.asarray(e2, float), rad)
    if show_con:
        poly(ax, Q + o2, "con", c)
        for cc in cen:
            dot(ax, cc + o2, c)
        obt = [q for q in Q if any(np.allclose(q, cc) for cc in cen)]
        for qo in obt:
            for m in Mm:
                if np.linalg.norm(m - qo) > np.linalg.norm(Q[0] - Q[1]) * 0.6:
                    ln(ax, qo + o2, m + o2, "con", c)
    for a in arcs:
        st = dict(color=c or INK, lw=2.0 if c else 1.6)
        if kind == "hid":
            st.update(ls=(0, (4, 2.5)), lw=1.0)
        ax.plot(a[:, 0] + o2[0], a[:, 1] + o2[1], **st)


def h2_agujero(ax, c):
    _fourc(ax, c, [cx, 0, cz], [1, 0, 0], [0, 0, 1], r, show_con=True)
    _fourc(ax, c, [cx, M, cz], [1, 0, 0], [0, 0, 1], r, show_con=False, kind="hid")
    if c:
        note(ax, I([cx + r, 0, cz + r]) + np.array([0.3, 0.6]), "Rombo de 3,8 con lados paralelos a X y Z;\ncentros en los vértices obtusos y en los cruces")


def h2_arriba(ax, c):
    _fourc(ax, c, [cx, EX.yc, S], [1, 0, 0], [0, 1, 0], EX.r, show_con=True)
    if c:
        note(ax, I([E, M, S]) + np.array([0.4, 0.4]), f"Rombo de {f2(G.D_EXTRA)} en la cara de arriba:\ncentro a 3,5 sobre X y {f2(EX.yc)} sobre Y")


STEPS2 = [
    ("Marco y rótulo", ["Igual que la hoja 1: marco a 1 cm y rótulo de 14 × 3,5 cm."], h2_marco),
    ("Punto O y ejes isométricos", [f"O a {f2(OX2)} cm del borde izquierdo y {f2(OY2)} cm del inferior.",
                                    "Con la escuadra de 30-60 apoyada en la regla T: eje X a 30° hacia abajo-derecha, eje Y a 30° hacia arriba-derecha, eje Z vertical."], h2_ejes),
    ("Caja envolvente 7 × 7 × 3", ["Mide REAL sobre cada eje: 7 cm sobre X, 7 cm sobre Z, 3 cm sobre Y.",
                                   "Completa la caja con paralelas (deslizando la escuadra sobre la regla). Línea muy fina."], h2_caja),
    ("Puntos del hexágono (cara delantera)", [f"En las aristas de arriba y abajo de la cara delantera: {f2(Q1)} cm desde cada extremo, medidos sobre X.",
                                              "En las aristas verticales: el punto medio (3,5 cm)."], h2_marcas),
    ("Hexágono delantero", ["Une los 6 puntos con línea firme."], h2_hex),
    ("Profundidad y cara trasera", ["Desde cada vértice, paralela al eje Y de 3 cm. Une los extremos: cara trasera.",
                                    "Lo que queda tapado, en trazos (o bórralo si el profesor no pide ocultas)."], h2_prisma),
    ("Agujero grande (4 centros)", ["Centro en la cara delantera a 3,5 sobre X y 3,5 sobre Z desde O. Rombo de lado 3,8 con lados paralelos a X y a Z.",
                                    "Desde los dos vértices obtusos (120°), rectas a los puntos medios de los lados opuestos; los cruces son los centros de los arcos pequeños.",
                                    "Arcos grandes con centro en los vértices obtusos; arcos pequeños con centro en los cruces. Borde trasero: igual, 3 cm atrás sobre Y, en trazos."], h2_agujero),
    ("Agujero de arriba (4 centros)", [f"En la cara superior: rombo de lado {f2(G.D_EXTRA)} con lados paralelos a X y a Y, centrado a 3,5 sobre X y {f2(EX.yc)} sobre Y.",
                                       "Mismo método de 4 centros. Repasa todo lo visible y borra o aclara la caja."], h2_arriba),
]


# ========================================================================= HOJA 3: auxiliares parciales
def make_aux_steps(total):
    ox, oy = (GD.OX4, GD.OY4) if total else (GD.OX3, GD.OY3)
    W, H = (42.0, 29.7) if total else (29.7, 21.0)
    off = np.array([ox, oy])
    F = lambda P: T.pF(P) + off
    Lp = lambda P: T.pL(P) + off
    A1 = lambda P: T.p1(P) + off
    A2 = lambda P: T.p2(P) + off
    iA, iB, iC, iD = G.iA, G.iB, G.iC, G.iD
    idx = T.ALL if total else T.FACE
    front = list(range(6)) if total else [iA, iB]

    def s_marco(ax, c):
        sheet(ax, W, H, c, "Aux. total" if total else "Aux. parciales", ("Nº 5 · 1:1 · A3" if total else "Nº 4 · 1:1 · A4"))

    def s_alzado(ax, c):
        view(ax, F, G.nF, c)
        if c:
            dim(ax, (0, oy + S + 1.2), (ox, oy + S + 1.2), f2(ox), off=0.5); dim(ax, (ox - 6.6, 0), (ox - 6.6, oy), f2(oy), off=0.5)
            note(ax, off + np.array([0.5, -1.4]), "Alzado igual que en la hoja 1 (O = esquina del cuadrado 7 × 7)")

    def s_perfil(ax, c):
        x_eje = T.X_EJE_L
        ln(ax, off + [x_eje, -1.2], off + [x_eje, S + 0.8], "fold", c)
        view(ax, Lp, T.nL, c)
        for i in range(6):
            ln(ax, F(V[i])[0], Lp(V[i + 6])[0] + [-0.5, 0], "proj", c)
        if c:
            dim(ax, off + [x_eje, -0.8], off + [0, -0.8], "1,8", off=-0.4)
            dim(ax, off + [x_eje - T.D_REF, S + 0.5], off + [x_eje, S + 0.5], "1", off=0.4)
            dim(ax, off + [x_eje - T.D_REF - M, S + 1.3], off + [x_eje - T.D_REF, S + 1.3], "3", off=0.4)
            note(ax, off + [x_eje - 0.2, -2.0], "Eje de referencia: desde aquí\nse miden las profundidades")

    def s_los1(ax, c):
        n1, t1 = T.N1, T.T1
        for i in (iA, iB):
            p = F(V[i])[0]
            foot = p + (T.H1 - T.pF(V[i])[0] @ n1) * n1
            ln(ax, p, foot, "proj", c)
            dot(ax, foot, c)
            if c:                                       # triángulo de pendiente 1:2
                ax.plot([p[0], p[0] + 2, p[0] + 2], [p[1], p[1], p[1] + 1], color=DIMC, lw=0.8)
                note(ax, p + np.array([0.9, -0.45]), "2", c=DIMC); note(ax, p + np.array([2.15, 0.3]), "1", c=DIMC)
                dim(ax, p, foot, "3", off=0.45)
        a = T.H1 * n1 + ((T.pF(V[front]) @ t1).max() + 1.0) * t1 + off
        b = T.H1 * n1 + ((T.pF(V[front]) @ t1).min() - 1.5) * t1 + off
        ln(ax, a, b, "fold", c)
        note(ax, b + np.array([0.2, -0.4]), "LOS1", c=c or "#c62828")
        if c:
            note(ax, F(V[iB])[0] + np.array([0.3, -2.2]), "Perpendicular a la cara = pendiente 1:2:\n2 cm a la derecha, 1 cm arriba.\nMide 3 cm y une: LOS1 (paralela a la cara)")

    def s_proy1(ax, c):
        for i in front:
            p = F(V[i])[0]
            q = A1(V[i + 6])[0] + 1.2 * T.N1
            ln(ax, p, q, "proj", c)
        if c:
            note(ax, A1(V[iD])[0] + np.array([0.6, 0.8]), "Prolonga las proyectantes:\nalinea la escuadra con la línea\n2:1 y deslízala sobre la otra")

    def s_dist1(ax, c):
        sel = idx
        for i in sel:
            dot(ax, A1(V[i])[0], c, f"{T.LET[i]}₁" if c else None, off=(0.2, 0.2))
        if c:
            for i, k in ((iA, 1), (iD, 2)):
                q = A1(V[i])[0]; foot = q - (T.p1(V[i])[0] @ T.N1 - T.H1) * T.N1
                dim(ax, foot, q, f2((T.p1(V[i])[0] @ T.N1) - T.H1), off=-0.5 * k)
            for i, k in ((iA, 1), (iD, 2)):
                q = Lp(V[i])[0]; x_eje = T.X_EJE_L + ox
                dim(ax, (x_eje, q[1] + 0.6 * k), (q[0], q[1] + 0.6 * k), f2(x_eje - q[0]), off=0.0)
            note(ax, A1(V[iC])[0] + np.array([0.6, -1.0]), "Compás: toma la distancia en el PERFIL\ndesde el eje y llévala desde LOS1:\ndelanteros 1 cm · traseros 4 cm")

    def s_cara1(ax, c):
        if total:
            view(ax, A1, T.LOS1, c, cyl=False)
        else:
            poly(ax, A1(V[[iA, iB, iC, iD]]), "vis", c)
        if c:
            dim(ax, A1(V[iB])[0], A1(V[iA])[0], f2(G.LADO_INC), off=-0.6); dim(ax, A1(V[iB])[0], A1(V[iC])[0], "3", off=0.6)

    def s_agujeros1(ax, c):
        cyl = G.CILS[0]
        for p0, p1 in cyl.silhouettes(T.LOS1):
            ln(ax, A1(p0)[0], A1(p1)[0], "hid", c)
        rim = A1(EX.rim()); ax.plot(rim[:, 0], rim[:, 1], color=c or INK, lw=1.6)
        bot = A1(EX.bottom()); ax.plot(bot[:, 0], bot[:, 1], color=c or INK, lw=0.8, ls=(0, (4, 2.5)))
        for p0, p1 in EX.silhouettes(T.LOS1):
            ln(ax, A1(p0)[0], A1(p1)[0], "hid", c)
        if c:
            note(ax, A1(EX.rim()).max(axis=0) + np.array([0.3, 0.3]), "Agujero de arriba: elipse visible\n(8 puntos, tabla de la hoja 4)")

    def s_los2(ax, c):
        ys = np.concatenate((T.p1(V[idx])[:, 1], T.p2(V[idx])[:, 1])) + oy
        ln(ax, (T.H2 + ox, ys.min() - 1.0), (T.H2 + ox, ys.max() + 1.0), "fold", c)
        note(ax, (T.H2 + ox + 0.2, ys.max() + 1.1), "LOS2", c=c or "#c62828")
        for i in idx:
            ln(ax, A1(V[i])[0], A2(V[i])[0] + [1.2, 0], "proj", c)
        if c:
            dim(ax, (ox, ys.min() - 1.6), (T.H2 + ox, ys.min() - 1.6), f2(T.H2), off=-0.4)
            note(ax, (T.H2 + ox + 0.4, ys.min() - 0.6), "LOS2 vertical (escuadra sobre la regla T);\nhorizontales con la regla T")

    def s_dist2(ax, c):
        for i in idx:
            dot(ax, A2(V[i])[0], c, f"{T.LET[i]}₂" if c else None, off=(0.2, 0.2))
        if c:
            done = set()
            for i in idx:
                d = round(float(T.H1 - T.pF(V[i])[0] @ T.N1), 2)
                if d in done:
                    continue
                done.add(d)
                q = A2(V[i])[0]
                dim(ax, (T.H2 + ox, q[1]), q, f2(d), off=0.45)
            note(ax, A2(V[idx]).min(axis=0) + np.array([0.0, -1.6]), "Compás: distancia en el ALZADO desde LOS1\n→ llévala desde LOS2")

    def s_cara2(ax, c):
        if total:
            view(ax, A2, T.LOS2, c, cyl=True)
        else:
            pts = A2(V[[iD, iA, iC, iB]]); ln(ax, pts[np.argmax(pts[:, 1])], pts[np.argmin(pts[:, 1])], "vis", c)
        if c:
            note(ax, A2(V[idx]).max(axis=0) + np.array([0.3, 0.3]),
                 "Elipses del agujero: método de 12 puntos" if total else "La cara se ve de canto:\nuna sola línea vertical")

    steps = [("Marco y rótulo", ["Marco a 1 cm y rótulo 14 × 3,5." + (" Hoja A3." if total else "")], s_marco),
             ("Alzado", [f"O a {f2(ox)} cm del borde izquierdo y {f2(oy)} cm del inferior.",
                         "Dibuja el alzado completo como en la hoja 1 (cuadrado 7 × 7, hexágono, agujeros)."], s_alzado),
             ("Eje de referencia y perfil", ["Eje de referencia: vertical 1,8 cm a la izquierda del alzado.",
                                             "Perfil izquierdo: rectángulo 3 × 7; su lado derecho a 1 cm del eje. Proyectantes horizontales desde el alzado."], s_perfil),
             ("LOS1", ["La cara A_F B_F está inclinada; su perpendicular sube 1 cm por cada 2 cm a la derecha.",
                       "Desde A_F y B_F traza esas perpendiculares, mide 3 cm y une las marcas: LOS1, paralela a la cara. Marca el 90°."], s_los1),
             ("Proyectantes 1", ["Prolonga las perpendiculares " + ("desde los 6 vértices" if total else "desde A_F y B_F") + " unos 6 cm más allá de LOS1.",
                                 "Truco: dibuja una vez la línea 2:1, apoya una escuadra en ella y deslízala sobre la otra para trazar todas paralelas."], s_proy1),
             ("Distancias de la auxiliar 1", ["Regla de las dos vistas: la distancia a LOS1 se toma del PERFIL, medida desde el eje de referencia.",
                                              "Delanteros (A, B" + (", E, F, G, H" if total else "") + ") a 1 cm; traseros (C, D" + (", I, J, K, L" if total else "") + ") a 4 cm."], s_dist1),
             ("Verdadera magnitud" if not total else "Auxiliar 1 completa",
              ([f"Une A₁-B₁-C₁-D₁: rectángulo de {f2(G.LADO_INC)} × 3 cm. Es la forma real de la cara."] if not total else
               ["Une hexágono delantero, trasero y laterales. Ocultas en trazos (ver lista en la hoja 4)."]), s_cara1)]
    if total:
        steps.append(("Agujeros en la auxiliar 1", ["Agujero grande: dos líneas ocultas entre 1 y 4 cm de LOS1, sobre las proyectantes tangentes a la circunferencia del alzado.",
                                                     "Agujero de arriba: su borde se ve como elipse VISIBLE (8 puntos con la tabla de la hoja 4)."], s_agujeros1))
    steps += [("LOS2 y proyectantes 2", [f"LOS2: vertical a {f2(T.H2)} cm a la derecha de O.",
                                         "Desde cada punto de la auxiliar 1, horizontal hacia la derecha pasando LOS2."], s_los2),
              ("Distancias de la auxiliar 2", ["Regla de las dos vistas: la distancia a LOS2 se toma del ALZADO, medida desde LOS1.",
                                               f"{GD.D2_TXT}." if total else "A, B, C y D están a 3 cm de LOS1 → a 3 cm de LOS2."], s_dist2),
              ("Auxiliar 2" + (" completa" if total else ""),
               (["Une todas las aristas; ocultas en trazos. Agujero grande: elipse trasera visible y delantera oculta (12 puntos, página de apoyo)."] if total else
                ["A₂, B₂, C₂ y D₂ quedan en una vertical: la cara se ve de canto. Repasa y rotula."]), s_cara2)]
    return steps, ("A4" if not total else "A3")


def main():
    with PdfPages(os.path.join(OUT, "Secuencia_paso_a_paso.pdf")) as pdf:
        render(pdf, "Hoja 1", "A4", STEPS1, "Vistas principales con cotas · A4 horizontal · escala 1:1 · tercer diedro")
        render(pdf, "Hoja 2", "A4", STEPS2, "Isométrico · A4 horizontal · escala 1:1 · medidas reales sobre los ejes")
        s3, f3 = make_aux_steps(False)
        render(pdf, "Hoja 3", f3, s3, "Proyecciones auxiliares parciales · A4 horizontal · escala 1:1")
        s4, f4 = make_aux_steps(True)
        render(pdf, "Hoja 4", f4, s4, "Proyección auxiliar total · A3 horizontal · escala 1:1")
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
