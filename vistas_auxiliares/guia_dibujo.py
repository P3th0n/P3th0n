#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUÍA PARA DIBUJAR LA TUERCA A MANO — en orden, con planos a escala real
=======================================================================
Para cada hoja: una página de pasos y una página con el plano a escala real (A4 o A3).
Si se imprime la página del plano al 100 % (sin "ajustar a página"), 1 cm del dibujo = 1 cm real.
Toda la geometría sale de proyecciones_auxiliares_tuerca.py / laminas_tablero.py (verificada).
"""
import os
import textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

import laminas_tablero as T
import laminas_limpias as LL

G = T.G
V = G.V
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "guia")
os.makedirs(OUT, exist_ok=True)
BODY = "Inter"
INK, RED, TEAL, BLUE, DIM = T.INK, T.RED, T.TEAL, "#1f5fbf", LL.DIM
LW = 1.3                                                  # grosor de línea visible a escala real

# vistas con trazo fino para impresión a escala real
LL.view = lambda ax, place, v: G.draw_view(ax, place, v, lw=LW, hidden=True, cyl=True)

R, S, M, E, A_ = G.R, G.S, G.M, G.E, G.R
cx, cz, r = G.cx, G.cz, G.D_BORE / 2
fmt = lambda v: f"{v:.2f}".replace(".", ",")
EX = G.EXTRA                                   # agujero de la cara superior (Ø estimado)
DX = G.D_EXTRA
TH8 = np.deg2rad(np.arange(0, 360, 45))
TOP8 = [(cx + EX.r * np.cos(t), EX.yc + EX.r * np.sin(t)) for t in TH8]
X1, X2 = G.Q1, E - G.Q1                        # vértices de arriba/abajo (método de la caja)
SUP, INC = G.LADO_SUP, G.LADO_INC
_ab = T.pF(V[[G.iB, G.iA]]); _d = _ab[1] - _ab[0]
ANG = float(np.degrees(np.arctan2(_d[1], abs(_d[0]))))  # inclinación de A_F B_F
D2 = {}
for _i in range(6):
    D2.setdefault(round(float(T.H1 - T.pF(V[_i])[0] @ T.N1), 2), []).append(T.LET[_i] + ", " + T.LET[_i + 6])
D2_TXT = "; ".join(f"{', '.join(v)} = {fmt(k)} cm" for k, v in sorted(D2.items()))
_vis, _hid = G.visible_edges(T.LOS2)
HID2 = ", ".join(sorted(f"{T.LET[a]}₂{T.LET[b]}₂" for a, b in _hid))
_vis1, _hid1 = G.visible_edges(T.LOS1)
HID1 = ", ".join(sorted(f"{T.LET[a]}₁{T.LET[b]}₁" for a, b in _hid1))
_rim = T.p2(G.CILS[0].rim(0)[:-1]); ELL = (np.ptp(_rim[:, 0]), np.ptp(_rim[:, 1]))
TOP8_TXT = "   ".join(f"{k + 1}: x={fmt(x)} · aux1 {fmt(T.D_REF + y)} · aux2 {fmt(T.H1 - (x * T.N1[0] + S * T.N1[1]))}"
                       for k, (x, y) in enumerate(TOP8))


# ------------------------------------------------------------------------------------------ hoja
def paper(fmt_name, title, num, scale="1:1"):
    W, H = (29.7, 21.0) if fmt_name == "A4" else (42.0, 29.7)
    fig = plt.figure(figsize=(W / 2.54, H / 2.54), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, ec="0.75", lw=0.6))
    ax.add_patch(Rectangle((1, 1), W - 2, H - 2, fill=False, ec=INK, lw=1.0))
    rw, rh = 14.0, 3.5
    x0, y0 = W - 1 - rw, 1
    ax.add_patch(Rectangle((x0, y0), rw, rh, fill=False, ec=INK, lw=0.9))
    for yy in (y0 + 1.2, y0 + 2.35):
        ax.plot([x0, x0 + rw], [yy, yy], color=INK, lw=0.6)
    for xx in (x0 + 4.5, x0 + 9.0):
        ax.plot([xx, xx], [y0, y0 + rh], color=INK, lw=0.6)
    t = lambda x, y, s, **k: ax.text(x, y, s, fontsize=6.5, fontfamily=BODY, va="center", **k)
    t(x0 + 0.2, y0 + 2.9, "U.F.P.S.O."); t(x0 + 4.7, y0 + 2.9, "Ingeniería Mecánica"); t(x0 + 9.2, y0 + 2.9, "Expresión Gráfica")
    t(x0 + 0.2, y0 + 1.75, "Est.: ____________"); t(x0 + 4.7, y0 + 1.75, "Firma: __________"); t(x0 + 9.2, y0 + 1.75, f"Título: {title}")
    t(x0 + 0.2, y0 + 0.6, "Cód.: ___________"); t(x0 + 4.7, y0 + 0.6, "Fecha: __________")
    t(x0 + 9.2, y0 + 0.6, f"Nº {num} · Esc. {scale} · cm · {fmt_name}")
    return fig, ax, W, H


def sub_axes(fig, W, H, ox, oy, xr, yr):
    """Ejes cuyo origen de datos está en (ox, oy) cm de la hoja, con 1 unidad = 1 cm."""
    ax = fig.add_axes([(ox + xr[0]) / W, (oy + yr[0]) / H, (xr[1] - xr[0]) / W, (yr[1] - yr[0]) / H])
    ax.set_xlim(*xr); ax.set_ylim(*yr); ax.axis("off"); ax.patch.set_alpha(0)
    return ax


def placement(ax, ox, oy, xh, yv, H):
    """Cotas azules de ubicación desde los bordes de la hoja hasta la esquina del alzado."""
    kw = dict(arrowprops=dict(arrowstyle="<|-|>", color=BLUE, lw=0.8, mutation_scale=7, shrinkA=0, shrinkB=0))
    ax.annotate("", xy=(ox, yv), xytext=(0, yv), **kw)
    ax.text(ox / 2, yv + 0.25, f"{fmt(ox)} cm", color=BLUE, fontsize=7, fontfamily=BODY, ha="center")
    ax.annotate("", xy=(xh, oy), xytext=(xh, 0), **kw)
    ax.text(xh + 0.2, oy / 2, f"{fmt(oy)} cm", color=BLUE, fontsize=7, fontfamily=BODY, rotation=90, va="center")
    ax.plot([ox - 0.3, ox + 0.3], [oy, oy], color=BLUE, lw=0.8); ax.plot([ox, ox], [oy - 0.3, oy + 0.3], color=BLUE, lw=0.8)
    ax.text(ox + 0.15, oy - 0.45, "O (origen del alzado)", color=BLUE, fontsize=6.5, fontfamily=BODY)


# ------------------------------------------------------------------------------------------ texto
def text_page(title, intro, steps, extra=None, fmt_name="A4"):
    fig = plt.figure(figsize=(29.7 / 2.54, 21.0 / 2.54), facecolor="white")
    fig.text(0.04, 0.94, title, fontsize=22, color=INK, fontfamily=T.HAND if hasattr(T, "HAND") else BODY, va="center")
    y = 0.885
    for line in textwrap.wrap(intro, 150):
        fig.text(0.04, y, line, fontsize=10, color="#333", fontfamily=BODY, va="top"); y -= 0.03
    y -= 0.015
    for i, st in enumerate(steps, 1):
        lines = textwrap.wrap(st, 140)
        fig.text(0.04, y, f"{i}.", fontsize=10, color=RED, fontfamily=BODY, va="top", fontweight="bold")
        for ln in lines:
            fig.text(0.065, y, ln, fontsize=10, color=INK, fontfamily=BODY, va="top"); y -= 0.028
        y -= 0.008
    if extra:
        y -= 0.01
        for ln in extra:
            fig.text(0.04, y, ln, fontsize=9.5, color=DIM, fontfamily=BODY, va="top"); y -= 0.027
    return fig


# ================================================================================= PORTADA
def portada():
    fig = plt.figure(figsize=(29.7 / 2.54, 21.0 / 2.54), facecolor="white")
    fig.text(0.04, 0.93, "Guía para dibujar la tuerca, paso a paso", fontsize=28, fontfamily=T.HAND, color=INK)
    fig.text(0.04, 0.875, "Todo lo que tienes que dibujar a mano, en orden. Cada hoja trae primero los pasos y después el plano a escala real: "
             "si imprimes esa página al 100 % (sin «ajustar a página»), las medidas coinciden con tu regla.", fontsize=10.5, fontfamily=BODY, color="#333", wrap=True)
    rows = [("Orden", "Hoja", "Formato", "Escala", "Va en el documento"),
            ("1", "Vistas principales con cotas (frontal, superior y lateral)", "A4 horizontal", "1:1", "Figura 10 · sección 3.2.1"),
            ("2", "Isométrico (corrige tu hoja 2)", "A4 horizontal", "1:1", "Figura 9 · sección 3.2.1"),
            ("3", "Proyecciones auxiliares parciales", "A4 horizontal", "1:1", "Figura 14 · sección 3.2.2"),
            ("4", "Proyección auxiliar total (con el agujero)", "A3 horizontal", "1:1", "Figura 15 · sección 3.2.2"),
            ("5", "Bocetos descriptivos: explicativo, informativo y storyboard", "A4", "mano alzada", "Figuras 11, 12 y 13 · 3.2.1"),
            ("6", "Foto midiendo la tuerca con calibrador", "—", "—", "Anexo A")]
    y = 0.78
    xs = (0.04, 0.10, 0.52, 0.66, 0.75)
    for k, row in enumerate(rows):
        for x, c in zip(xs, row):
            fig.text(x, y, c, fontsize=10.5, fontfamily=BODY, color=INK if k else RED, fontweight="bold" if k == 0 else "normal")
        y -= 0.045
    info = ["Materiales: escuadras de 45° y de 30-60°, regla larga o regla T, compás, portaminas 0,5 mm (2H para construcción, HB para repasar), "
            "borrador y plantilla de curvas (para las elipses de la hoja 4).",
            f"Datos de la pieza (caja de tu isométrico): 7 cm de ancho × 7 cm de alto × 3 cm de espesor. Hexágono por el método de la caja: "
            f"vértices de arriba y abajo a {fmt(X1)} cm de cada esquina (lado superior {fmt(SUP)} cm, lados inclinados {fmt(INC)} cm). "
            f"Ø agujero = {G.D_BORE:.1f} cm (ESTIMADO: mídelo). Agujero de la cara superior: Ø {DX:.1f} cm (ESTIMADO de tu isométrico), centrado en esa cara "
            "y atravesando la pared hasta el agujero roscado.",
            "Convenciones: tercer diedro (planta encima del alzado, lateral derecha a su derecha), unidades en cm. "
            "Línea visible gruesa (HB), oculta en trazos de 3 mm, ejes en trazo-punto, construcción y proyectantes muy finas (2H).",
            "Colores de los planos de referencia: negro = lo que repasas; verde = proyectantes; rojo = ejes de referencia, LOS1 y LOS2; "
            "morado = cotas; azul = ubicación en la hoja (no se dibuja)."]
    y -= 0.02
    for par in info:
        for ln in textwrap.wrap(par, 150):
            fig.text(0.04, y, ln, fontsize=10, fontfamily=BODY, color="#333"); y -= 0.03
        y -= 0.012
    return fig


# ================================================================================= HOJA 1
OX1, OY1 = 6.0, 6.5


def pasos_hoja1():
    return text_page(
        "Hoja 1 · Vistas principales con cotas  (A4 horizontal, escala 1:1)",
        "Tercer diedro: la vista superior va ENCIMA del alzado y la lateral derecha a su DERECHA, alineadas con proyectantes. "
        "El origen O es la esquina inferior izquierda del recuadro de 7 × 7 que encierra el alzado.",
        ["Traza el marco a 1 cm del borde y el rótulo (14 × 3,5 cm abajo a la derecha). Título: «Tuerca para perno – Vistas principales», Nº 3.",
         f"Ubica O a {fmt(OX1)} cm del borde izquierdo y {fmt(OY1)} cm del borde inferior de la hoja.",
         f"ALZADO: recuadro guía fino de 7 × 7 cm desde O. En los lados superior e inferior marca {fmt(X1)} cm desde cada esquina; en los lados "
         f"izquierdo y derecho marca el punto medio (3,5 cm). Une los seis puntos: hexágono con caras planas arriba y abajo (lado superior "
         f"{fmt(SUP)} cm, lados inclinados {fmt(INC)} cm a {fmt(ANG)}° de la horizontal).",
         f"Ejes del alzado (trazo-punto) por el centro (3,5 ; 3,5), sobresaliendo 0,5 cm. Agujero: circunferencia de radio {fmt(r)} cm con centro en ese punto.",
         f"Proyectantes verticales finas hacia arriba desde x = 0 ; {fmt(X1)} ; {fmt(X2)} ; 7 (vértices), x = {fmt(cx - r)} ; {fmt(cx + r)} (agujero) "
         f"y x = {fmt(cx - EX.r)} ; {fmt(cx + EX.r)} (agujero de arriba).",
         f"VISTA SUPERIOR: 2 cm por encima del alzado, rectángulo de 7 × 3 cm. Líneas visibles verticales en x = {fmt(X1)} y {fmt(X2)} (aristas). "
         f"Ocultas (trazos) en x = {fmt(cx - r)} y {fmt(cx + r)} (agujero). Eje vertical en x = 3,5.",
         f"Proyectantes horizontales hacia la derecha desde z = 0 ; 3,5 ; 7 (vértices) y z = {fmt(cz - r)} ; {fmt(cz + r)} (agujero).",
         f"VISTA LATERAL DERECHA: 2 cm a la derecha del alzado, rectángulo de 3 × 7 cm. Línea visible horizontal a 3,5 cm (arista del vértice). "
         f"Ocultas a {fmt(cz - r)} y {fmt(cz + r)} cm (agujero). Eje horizontal a 3,5 cm.",
         f"AGUJERO DE ARRIBA (Ø {fmt(DX)} cm, estimado): en la vista superior, circunferencia de radio {fmt(EX.r)} con centro en x = 3,5 y a "
         f"{fmt(EX.yc)} cm del borde de abajo de esa vista. En el alzado: dos ocultas verticales en x = {fmt(cx - EX.r)} y {fmt(cx + EX.r)}, desde el borde "
         f"superior hasta tocar la circunferencia del agujero grande. En la lateral: dos ocultas verticales a {fmt(EX.yc - EX.r)} y {fmt(EX.yc + EX.r)} cm "
         f"de su borde izquierdo, desde arriba hasta {fmt(cz + r)} cm, unidas por una curva oculta que baja hasta {fmt(float(EX.zb(cx + EX.r)))} cm en el centro.",
         "Repasa: visibles gruesas, ocultas en trazos, ejes en trazo-punto. Deja las proyectantes muy finas.",
         f"COTAS (flechas cerradas, número sobre la línea): 7 de ancho bajo el alzado; 7 de alto a la izquierda; Ø 3,8 en el agujero; {fmt(SUP)} "
         f"(lado superior) sobre la vista superior; Ø {fmt(DX)} y su posición ({fmt(EX.yc)} cm) en la vista superior; 3 de espesor en la vista superior y en la lateral."],
        extra=[f"Comprobación rápida: la vista superior muestra tres bandas de {fmt(X1)} + {fmt(SUP)} + {fmt(X1)} = 7 cm; la lateral, una línea en la mitad."])


def plano_hoja1():
    fig, ax, W, H = paper("A4", "Vistas principales", 3)
    sub = sub_axes(fig, W, H, OX1, OY1, (-3.5, 16.5), (-3.2, 14.0))
    for pl, v in ((G.place_front, G.nF), (G.place_top, G.nT), (G.place_right, G.nR)):
        G.draw_view(sub, pl, v, lw=LW)
    cc = dict(color="#2c5aa0", lw=0.6, ls=(0, (8, 2, 1, 2)))
    yT = G.ZMAX + G.GAP; xR = G.XMAX + G.GAP
    sub.plot([-0.5, G.XMAX + 0.5], [cz, cz], **cc); sub.plot([cx, cx], [-0.5, G.ZMAX + 0.5], **cc)
    sub.plot([cx, cx], [yT - 0.5, yT + M + 0.5], **cc); sub.plot([xR - 0.5, xR + M + 0.5], [cz, cz], **cc)
    for x in (0, X1, X2, E, cx - r, cx + r):
        sub.plot([x, x], [G.ZMAX if x not in (cx - r, cx + r) else cz + r, yT], color=TEAL, lw=0.4)
    for z in (0, cz, S, cz - r, cz + r):
        sub.plot([G.XMAX if z in (0, cz, S) else cx + r, xR], [z, z], color=TEAL, lw=0.4)
    G.dim(sub, (0, 0), (E, 0), fmt(E), off=-1.0, fs=8)
    G.dim(sub, (0, 0), (0, S), fmt(S), off=1.0, fs=8)
    G.dim(sub, (cx - r, cz), (cx + r, cz), "Ø 3,8", off=0.0, fs=7)
    G.dim(sub, (X1, yT + M), (X2, yT + M), fmt(SUP), off=0.8, fs=8)
    G.dim(sub, (cx - EX.r, yT + EX.yc), (cx + EX.r, yT + EX.yc), f"Ø {fmt(DX)}", off=0.0, fs=6)
    G.dim(sub, (cx + 1.25, yT), (cx + 1.25, yT + EX.yc), fmt(EX.yc), off=0.0, fs=6)
    for x in (cx - EX.r, cx + EX.r):
        sub.plot([x, x], [G.ZMAX, yT], color=TEAL, lw=0.4)
    G.dim(sub, (E, yT), (E, yT + M), "3", off=-0.9, fs=8)
    G.dim(sub, (xR, 0), (xR + M, 0), "3", off=-1.0, fs=8)
    G.dim(sub, (xR + M, 0), (xR + M, S), fmt(S), off=-1.0, fs=8)
    for txt, xy in (("VISTA FRONTAL", (E / 2, -2.4)), ("VISTA SUPERIOR", (E / 2, yT + M + 1.6)), ("LATERAL DERECHA", (xR + M / 2, S + 0.6))):
        sub.text(*xy, txt, fontsize=7, fontfamily=BODY, color="0.35", ha="center")
    placement(ax, OX1, OY1, OX1 - 2.6, OY1 + S + 0.9, H)
    return fig


# ================================================================================= HOJA 2 (isométrico)
K_ISO = 1 / np.sqrt(2 / 3)                         # dibujo isométrico: medidas reales sobre los ejes
U_ISO, W_ISO = G.iso_basis(G.V_ISO)
OX2, OY2 = 8.5, 10.0


def iso(P):
    return K_ISO * G.proj(P, U_ISO, W_ISO) - K_ISO * G.proj(np.zeros(3), U_ISO, W_ISO)


def four_center(c3, e1, e2, rad, n=60):
    """Óvalo de 4 centros (construcción a mano) del círculo de radio rad, centro c3, en el plano de e1, e2."""
    Q = np.array([iso(c3 + rad * (s1 * e1 + s2 * e2))[0] for s1, s2 in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    Mm = np.array([(Q[i] + Q[(i + 1) % 4]) / 2 for i in range(4)])          # puntos medios (tangencia)
    ang = [np.degrees(np.arccos(np.clip(np.dot(unit(Q[(i - 1) % 4] - Q[i]), unit(Q[(i + 1) % 4] - Q[i])), -1, 1))) for i in range(4)]
    obt = [i for i in range(4) if ang[i] > 90]
    centers, arcs = [], []
    for i in obt:                                                            # arco grande: centro en vértice obtuso
        far = [Mm[(i + 1) % 4], Mm[(i + 2) % 4]]
        arcs.append((Q[i], far[0], far[1])); centers.append(Q[i])
    def inter(p1, d1, p2, d2):
        Mx = np.column_stack((d1, -d2))
        if abs(np.linalg.det(Mx)) < 1e-12:            # rectas paralelas: no hay cruce
            return None
        t = np.linalg.solve(Mx, p2 - p1); return p1 + t[0] * d1

    def inside(p):                                       # dentro del rombo (convexo)
        sg = [(Q[(i + 1) % 4] - Q[i])[0] * (p - Q[i])[1] - (Q[(i + 1) % 4] - Q[i])[1] * (p - Q[i])[0] for i in range(4)]
        return all(x > 1e-9 for x in sg) or all(x < -1e-9 for x in sg)
    o1, o2 = obt
    small = []
    for m1 in (Mm[(o1 + 1) % 4], Mm[(o1 + 2) % 4]):
        for m2 in (Mm[(o2 + 1) % 4], Mm[(o2 + 2) % 4]):
            if np.linalg.norm(m1 - m2) > 1e-9:
                p = inter(Q[o1], m1 - Q[o1], Q[o2], m2 - Q[o2])
                if p is not None and inside(p) and all(np.linalg.norm(p - x[0]) > 1e-6 for x in small):
                    small.append((p, m1, m2))
    assert len(small) == 2, "el método de 4 centros debe dar 2 centros pequeños"
    for p, m1, m2 in small:
        arcs.append((p, m1, m2)); centers.append(p)
    pts = []
    for cen, a, b in arcs:
        a0, a1 = np.arctan2(*(a - cen)[::-1]), np.arctan2(*(b - cen)[::-1])
        d = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
        t = np.linspace(a0, a0 + d, n)
        rr = np.linalg.norm(a - cen)
        pts.append(np.column_stack((cen[0] + rr * np.cos(t), cen[1] + rr * np.sin(t))))
    return Q, Mm, centers, pts


def unit(v):
    return v / np.linalg.norm(v)


def pasos_hoja2():
    return text_page(
        "Hoja 2 · Isométrico  (A4 horizontal, escala 1:1 — dibujo isométrico)",
        "En el dibujo isométrico las medidas se llevan REALES sobre los tres ejes: X (ancho) a 30° hacia abajo-derecha, Z (alto) vertical "
        "e Y (profundidad) a 30° hacia arriba-derecha. Caja de 7 × 7 × 3 cm, como en tu hoja 2.",
        ["Marco a 1 cm y rótulo. Título: «Tuerca para perno – Isométrico», Nº 2.",
         f"Punto de partida O (esquina delantera inferior izquierda de la caja) a {fmt(OX2)} cm del borde izquierdo y {fmt(OY2)} cm del inferior.",
         "Desde O traza los tres ejes con la escuadra de 30-60: X a 30° hacia abajo-derecha, Z vertical, Y a 30° hacia arriba-derecha.",
         "Caja envolvente (línea fina): 7 cm sobre X, 7 cm sobre Z y 3 cm sobre Y. Completa la caja con paralelas.",
         f"Hexágono en la cara delantera (la del plano X-Z): en las aristas inferior y superior marca {fmt(X1)} cm desde cada extremo; en las aristas "
         "verticales marca el punto medio (3,5 cm). Une los seis puntos.",
         "Cara trasera: desde cada vértice traza una paralela al eje Y de 3 cm y une los extremos. Las aristas que no se ven, en trazos (o bórralas).",
         "Agujero grande, método de 4 centros: centro C de la cara delantera a 3,5 cm sobre X y 3,5 cm sobre Z desde O. Rombo de lado 3,8 cm centrado "
         "en C, con lados paralelos a X y a Z.",
         "Desde cada vértice obtuso del rombo (el de 120°) traza rectas a los puntos medios de los dos lados opuestos. Donde se cruzan están los centros "
         "de los arcos pequeños.",
         "Arcos grandes: centro en cada vértice obtuso, de un punto medio al otro. Arcos pequeños: centro en cada cruce. Así obtienes la elipse.",
         "Borde trasero del agujero: la misma elipse desplazada 3 cm sobre Y; solo la parte que se ve (o toda en trazos).",
         f"AGUJERO DE ARRIBA (Ø {fmt(DX)} cm, estimado): en la cara superior (7 cm sobre O), centro a 3,5 cm sobre X y {fmt(EX.yc)} cm sobre Y. "
         f"Rombo de lado {fmt(DX)} cm con lados paralelos a X y a Y, y óvalo por el mismo método de 4 centros.",
         "Repasa lo visible y deja muy fina (o borra) la construcción."],
        extra=["Comprobación: la diagonal mayor de cada rombo (entre vértices agudos) es la dirección larga de su elipse."])


def plano_hoja2():
    fig, ax, W, H = paper("A4", "Isométrico", 2)
    sub = sub_axes(fig, W, H, OX2, OY2, (-2.5, 14.0), (-7.5, 11.0))
    lo, hi = np.zeros(3), np.array([E, M, S])
    box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    for a in range(8):
        for b in range(a + 1, 8):
            if np.sum(np.abs(box[a] - box[b]) > 1e-9) == 1:
                q = iso(box[[a, b]]); sub.plot(q[:, 0], q[:, 1], color=TEAL, lw=0.5)
    G.draw_view(sub, iso, G.V_ISO, lw=LW, hidden=True, cyl=False)
    # marcas de 2,02 y 3,5 en la cara delantera
    for p in ([X1, 0, 0], [X2, 0, 0], [X1, 0, S], [X2, 0, S], [0, 0, cz], [E, 0, cz]):
        q = iso(np.array(p))[0]; sub.plot(*q, "o", ms=2.5, color=RED)
    # óvalo de 4 centros (delantero visible, trasero oculto)
    for y, ls in ((0.0, "-"), (M, (0, (3, 2)))):
        Q, Mm, cen, arcs = four_center(np.array([cx, y, cz]), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), r)
        if y == 0:
            sub.plot(*np.vstack((Q, Q[:1])).T, color=TEAL, lw=0.5)
            for c in cen:
                sub.plot(*c, "o", ms=2.5, color=RED)
            o = [Q[i] for i in range(4) if any(np.allclose(Q[i], c) for c in cen)]
            for qo in o:
                for m in Mm:
                    if np.linalg.norm(m - qo) > np.linalg.norm(Q[0] - Q[1]) * 0.6:
                        sub.plot([qo[0], m[0]], [qo[1], m[1]], color=TEAL, lw=0.4)
        for a in arcs:
            sub.plot(a[:, 0], a[:, 1], color=INK, lw=LW if y == 0 else LW * 0.55, ls=ls)
    Q, Mm, cen, arcs = four_center(np.array([cx, EX.yc, S]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), EX.r)
    sub.plot(*np.vstack((Q, Q[:1])).T, color=TEAL, lw=0.5)
    for c in cen:
        sub.plot(*c, "o", ms=2.0, color=RED)
    for arc in arcs:
        sub.plot(arc[:, 0], arc[:, 1], color=INK, lw=LW)
    O = iso(np.zeros(3))[0]
    G.dim(sub, iso(np.array([0, 0, 0]))[0], iso(np.array([E, 0, 0]))[0], fmt(E), off=-0.8, fs=8)
    G.dim(sub, iso(np.array([0, 0, 0]))[0], iso(np.array([0, 0, S]))[0], "7", off=0.8, fs=8)
    G.dim(sub, iso(np.array([E, 0, 0]))[0], iso(np.array([E, M, 0]))[0], "3", off=-0.7, fs=8)
    G.dim(sub, iso(np.array([0, 0, S]))[0], iso(np.array([X1, 0, S]))[0], fmt(X1), off=0.6, fs=7)
    sub.text(*(O + np.array([-0.5, -0.4])), "O", color=BLUE, fontsize=8, fontfamily=BODY)
    for p, nm in (([E * 1.06, 0, 0], "X"), ([E, M + 0.9, 0], "Y"), ([0, 0, S * 1.06], "Z")):
        q = iso(np.array(p))[0]; sub.text(*q, nm, color=BLUE, fontsize=8, fontfamily=BODY)
    placement(ax, OX2, OY2, OX2 - 3.0, OY2 + 4.0, H)
    return fig


# ================================================================================= HOJA 3 y 4 (auxiliares)
OX3, OY3 = 7.6, 6.0
OX4, OY4 = 10.4, 9.0


def pasos_hoja3():
    return text_page(
        "Hoja 3 · Proyecciones auxiliares parciales  (A4 horizontal, escala 1:1)",
        "Se proyecta SOLO la cara inclinada ABCD. Regla de las dos vistas: la distancia de un punto a la línea de pliegue en la vista nueva se mide "
        "en la vista que está dos lugares atrás, desde su propia línea de pliegue. Origen O = esquina inferior izquierda del recuadro del alzado.",
        ["Marco y rótulo. Título: «Proyecciones auxiliares parciales», Nº 4, Escala 1:1.",
         f"ALZADO con O a {fmt(OX3)} cm del borde izquierdo y {fmt(OY3)} cm del inferior: hexágono y agujeros igual que en la hoja 1.",
         "EJE DE REFERENCIA: recta vertical 1,8 cm a la izquierda del alzado (x = −1,8). Desde ella se miden las profundidades.",
         "PERFIL IZQUIERDO: rectángulo de 3 × 7 cm entre x = −2,8 y x = −5,8 (cara delantera de la tuerca a 1 cm del eje, la trasera a 4 cm). "
         "Proyectantes horizontales desde el alzado.",
         f"Rotula: en el alzado A_F D_F en el vértice ({fmt(X2)} ; 7) y B_F C_F en (7 ; 3,5). En el perfil, A_L y B_L sobre el lado derecho y D_L y C_L sobre el izquierdo.",
         f"LOS1: el lado A_F B_F está inclinado {fmt(ANG)}°. Sus perpendiculares tienen pendiente 1:2 (por cada 2 cm a la derecha, 1 cm hacia arriba). "
         "Desde A_F y desde B_F traza esas perpendiculares y mide 3 cm sobre cada una. Une las dos marcas: esa es LOS1, paralela a la cara. Marca el 90°.",
         "Prolonga esas dos proyectantes unos 6 cm más allá de LOS1.",
         "Con el compás, mide en el PERFIL desde el eje: cara delantera (A, B) = 1 cm; cara trasera (C, D) = 4 cm. Lleva cada distancia desde LOS1 sobre "
         "su proyectante: A₁ y B₁ a 1 cm; D₁ (sobre la línea de A) y C₁ (sobre la de B) a 4 cm.",
         f"Une A₁-B₁-C₁-D₁: rectángulo de {fmt(INC)} × 3 cm = verdadera magnitud de la cara. Compruébalo con la regla.",
         f"LOS2: recta vertical a {fmt(T.H2)} cm a la derecha de O. Marca el 90°.",
         "Desde A₁, B₁, C₁ y D₁ traza proyectantes horizontales hacia la derecha, pasando LOS2.",
         "Mide en el ALZADO desde LOS1: A, B, C y D están a 3 cm (la cara está de canto). Lleva 3 cm desde LOS2 sobre cada horizontal: A₂, B₂, C₂ y D₂ "
         "quedan en una vertical — la cara se ve de canto.",
         "Repasa, rotula y escribe LOS1, LOS2 y «Eje de referencia»."])


def plano_aux(total):
    fmt_name, (ox, oy) = ("A3", (OX4, OY4)) if total else ("A4", (OX3, OY3))
    fig, ax, W, H = paper(fmt_name, "Aux. total" if total else "Aux. parciales", 5 if total else 4)
    sub = sub_axes(fig, W, H, ox, oy, (-7.2, 29.5 if total else 21.5), (-2.4, 14.6))
    reqs = []
    idx = T.ALL if total else T.FACE
    LL.base_views(sub, reqs, idx)
    LL.los1_and_aux1(sub, reqs, idx, total)
    LL.los2_and_aux2(sub, reqs, idx, total)
    reqs = [(q, t, 9 if k == "pt" else 10, k) for q, t, fs, k in reqs]
    LL.place_labels(fig, sub, reqs)
    for t in sub.texts:
        if t.get_fontsize() > 11:
            t.set_fontsize(8)
    placement(ax, ox, oy, ox - 6.6, oy + S + 1.2, H)
    return fig


def pasos_hoja4():
    return text_page(
        "Hoja 4 · Proyección auxiliar total  (A3 horizontal, escala 1:1)",
        "Es la hoja 3 aplicada a TODOS los vértices y a los dos agujeros. No cabe en A4 a escala 1:1: usa A3, o A4 a escala 1:2 dividiendo todas las medidas entre 2.",
        [f"Marco y rótulo (Nº 5, A3). ALZADO con O a {fmt(OX4)} cm del borde izquierdo y {fmt(OY4)} cm del inferior; eje de referencia, perfil y LOS1 igual que en la hoja 3.",
         "Proyectantes (pendiente 1:2) desde los SEIS vértices del alzado. En el alzado cada pareja coincide: A_F D_F, B_F C_F, E_F I_F, F_F J_F, G_F K_F, H_F L_F "
         "(delantero primero, trasero después).",
         "AUXILIAR 1 (distancias del perfil): delanteros A, B, E, F, G, H a 1 cm de LOS1; traseros C, D, I, J, K, L a 4 cm.",
         "Une hexágono delantero B-A-E-F-G-H, hexágono trasero C-D-I-J-K-L y laterales A-D, B-C, E-I, F-J, G-K, H-L. "
         f"En trazos (ocultas): {HID1}. Si una oculta cae encima de una visible, manda la visible.",
         "Agujero grande en la auxiliar 1: dos líneas OCULTAS entre 1 y 4 cm de LOS1, sobre las proyectantes que tocan (tangentes) la circunferencia del alzado.",
         f"LOS2 vertical a {fmt(T.H2)} cm de O. Proyectantes horizontales desde todos los puntos de la auxiliar 1.",
         f"AUXILIAR 2 (distancias del alzado desde LOS1): {D2_TXT}. Llévalas desde LOS2 sobre cada horizontal.",
         f"Une igual que en la auxiliar 1. En trazos (ocultas): {HID2}.",
         f"Agujero grande en la auxiliar 2: método de 12 puntos (página de apoyo). Elipse trasera visible, delantera oculta, unidas por dos verticales "
         f"ocultas tangentes. Ejes de la elipse: {fmt(ELL[0])} (horizontal) × {fmt(ELL[1])} cm (vertical).",
         f"AGUJERO DE ARRIBA: en la auxiliar 1 su borde se ve como ELIPSE VISIBLE (la cara superior mira hacia LOS1); en la auxiliar 2, OCULTA. Proyecta 8 "
         f"puntos de su borde (cada 45°) como vértices: en el alzado caen sobre el borde superior entre x = {fmt(cx - EX.r)} y {fmt(cx + EX.r)}. Tabla abajo.",
         "Repasa y rotula todos los puntos con su subíndice (₁ y ₂)."],
        extra=["Borde del agujero de arriba, 8 puntos (x en el alzado · distancia a LOS1 en la auxiliar 1 · a LOS2 en la auxiliar 2, cm):"]
        + textwrap.wrap(TOP8_TXT, 120))


def apoyo_circulo():
    fig = plt.figure(figsize=(29.7 / 2.54, 21.0 / 2.54), facecolor="white")
    img = plt.imread(os.path.join(HERE, "limpias", "6_circunferencia.png"))
    a = fig.add_axes([0.02, 0.24, 0.96, 0.74]); a.imshow(img); a.axis("off")
    steps = ["1. En el alzado divide la circunferencia del agujero en 12 partes de 30° (con la escuadra de 30-60 apoyada en el centro). Numera desde el 1 (a la derecha) en sentido antihorario.",
             "2. Proyecta cada punto a la auxiliar 1 por su proyectante (perpendicular a LOS1, pendiente 1:2): borde delantero a 1 cm de LOS1, borde trasero a 4 cm.",
             "3. Desde cada punto de la auxiliar 1 traza la horizontal hasta la auxiliar 2 y lleva desde LOS2 la distancia del alzado a LOS1 (tabla de arriba; es la misma para el borde delantero y el trasero).",
             "4. Une los 12 puntos de cada borde con la plantilla de curvas: el trasero continuo y el delantero en trazos. Comprueba los ejes: " + f"{fmt(ELL[0])} × {fmt(ELL[1])} cm."]
    y = 0.21
    for st in steps:
        for ln in textwrap.wrap(st, 160):
            fig.text(0.03, y, ln, fontsize=9.5, fontfamily=BODY, color=INK); y -= 0.028
        y -= 0.006
    return fig


# ================================================================================= HOJA 5 (bocetos descriptivos)
def explicativo_ref():
    fig = plt.figure(figsize=(29.7 / 2.54, 21.0 / 2.54), facecolor="white")
    fig.text(0.04, 0.94, "Hoja 5 · Bocetos descriptivos (a mano alzada) — referencias", fontsize=22, fontfamily=T.HAND, color=INK)
    a1 = fig.add_axes([0.02, 0.10, 0.52, 0.76]); a2 = fig.add_axes([0.55, 0.40, 0.43, 0.46])
    # --- explicativo: isométrico con llamadas
    G.draw_view(a1, iso, G.V_ISO, lw=1.4, hidden=False, cyl=False)
    for y, ls in ((0.0, "-"),):
        _, _, _, arcs = four_center(np.array([cx, y, cz]), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), r)
        for arc in arcs:
            a1.plot(arc[:, 0], arc[:, 1], color=INK, lw=1.4)
    for arc in four_center(np.array([cx, EX.yc, S]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), EX.r)[3]:
        a1.plot(arc[:, 0], arc[:, 1], color=INK, lw=1.2)
    calls = [((cx + 1.9 * np.cos(2.5), 0, cz + 1.9 * np.sin(2.5)), (-3.2, 9.5), f"Agujero roscado Ø {G.D_BORE:.1f} cm (estimado)"),
             ((cx, M / 2, S), (2.0, 13.5), f"Agujero superior Ø {fmt(DX)} cm (estimado):\npasador o alambre de seguridad"),
             (V[[G.iA, G.iB, G.iC, G.iD]].mean(axis=0), (11.0, 9.0), f"Cara inclinada ABCD ({fmt(ANG)}°)"),
             ((E / 2 - 2.5, 0, 0.6), (-3.2, -1.5), "Cuerpo hexagonal en caja de 7 × 7 cm"),
             ((E, M / 2, cz), (11.0, 2.5), "Espesor m = 3 cm")]
    for p3, xy, txt in calls:
        p = iso(np.array(p3))[0]
        a1.annotate(txt, xy=p, xytext=xy, fontsize=9, fontfamily=BODY, color=RED,
                    arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.8, mutation_scale=8))
    a1.set_title("Explicativo: la pieza con sus partes señaladas (flechas y notas)", fontsize=10, fontfamily=BODY)
    a1.set_aspect("equal"); a1.axis("off"); a1.set_xlim(-5, 18); a1.set_ylim(-3, 15)
    # --- storyboard: tres viñetas en vista lateral (esquemático)
    a2.set_title("Storyboard: secuencia de uso (3 viñetas)", fontsize=10, fontfamily=BODY)
    for k in range(3):
        x0 = k * 11.0
        a2.add_patch(Rectangle((x0 - 0.5, -2.5), 10.5, 12.5, fill=False, ec="0.6", lw=0.8))
        a2.add_patch(Rectangle((x0 + 0.2, 0), 1.2, 7, fill=False, ec=INK, lw=1.2))            # cabeza del perno
        a2.add_patch(Rectangle((x0 + 1.4, 1.6), 7.8, 3.8, fill=False, ec=INK, lw=1.2))        # vástago
        a2.add_patch(Rectangle((x0 + 1.4, -0.5), 1.0, 8.0, fill=False, ec="0.4", lw=1.0, hatch="///"))   # pieza a sujetar
        a2.add_patch(Rectangle((x0 + 2.4, -0.5), 1.0, 8.0, fill=False, ec="0.4", lw=1.0, hatch="\\\\\\"))
        nx = x0 + (6.6 if k == 0 else 3.4)
        a2.add_patch(Rectangle((nx, 0), 3.0, 7.0, fill=False, ec=RED, lw=1.4))               # tuerca
        if k == 0:
            a2.annotate("", xy=(x0 + 4.0, 3.5), xytext=(x0 + 6.4, 3.5), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2))
        if k == 2:
            a2.add_patch(Rectangle((nx + 1.25, 5.4), 0.5, 3.4, fill=True, fc="0.85", ec=INK, lw=1.0))
            a2.annotate("", xy=(nx + 1.5, 7.2), xytext=(nx + 1.5, 9.6), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2))
        a2.text(x0 + 4.7, -2.0, ("1. Acercar la tuerca", "2. Roscar y apretar", "3. Pasar el pasador")[k], fontsize=8.5,
                fontfamily=BODY, ha="center", color=INK)
    a2.set_aspect("equal"); a2.axis("off"); a2.set_xlim(-1, 32); a2.set_ylim(-3, 10.5)
    notes = ["Qué dibujar (3 figuras del documento):",
             "• Figura 11 — EXPLICATIVO: isométrico a mano alzada con flechas y notas que nombren cada parte y su función (como a la izquierda).",
             "• Figura 12 — INFORMATIVO: las vistas de la hoja 1 a mano alzada, con las cotas principales y notas técnicas (material: acero; "
             "medidas 7 × 7 × 3 y Ø; tipo de rosca si lo conoces).",
             "• Figura 13 — STORYBOARD: 3 viñetas de uso (arriba a la derecha): acercar la tuerca al perno, roscar y apretar, pasar el pasador por el agujero adicional.",
             "Son bocetos: a mano alzada, proporcionados, con estilógrafo o lápiz, en formato con márgenes y rótulo."]
    y = 0.36
    for ln in notes:
        for w in textwrap.wrap(ln, 62):
            fig.text(0.56, y, w, fontsize=9.5, fontfamily=BODY, color=INK if not ln.endswith(":") else RED); y -= 0.03
    return fig


def checklist():
    return text_page(
        "Al terminar · fotos y dónde va cada una en el documento",
        "Toma cada foto de frente, con luz pareja, sin sombras ni objetos alrededor, y que se lea el rótulo. Reemplaza en el borrador cada «IMAGEN DE REFERENCIA».",
        ["Hoja 1 (vistas principales) → Figura 10, sección 3.2.1.",
         "Hoja 2 (isométrico corregido) → Figura 9, sección 3.2.1 (reemplaza la foto actual).",
         "Hoja 3 (auxiliares parciales) → Figura 14, sección 3.2.2.",
         "Hoja 4 (auxiliar total) → Figura 15, sección 3.2.2.",
         "Bocetos explicativo, informativo y storyboard → Figuras 11, 12 y 13, sección 3.2.1.",
         "Foto midiendo la tuerca con calibrador → Anexo A.",
         "En cada «Nota. Realizado por…» escribe el nombre y el código de quien hizo la hoja.",
         f"Antes de entregar: confirma el Ø real de los dos agujeros (aquí 3,8 y {fmt(DX)} cm, estimados); si cambian, avísame y regenero todo."])


def main():
    pages = [("00_portada", portada), ("01_hoja1_pasos", pasos_hoja1), ("02_hoja1_plano_A4", plano_hoja1),
             ("03_hoja2_pasos", pasos_hoja2), ("04_hoja2_plano_A4", plano_hoja2),
             ("05_hoja3_pasos", pasos_hoja3), ("06_hoja3_plano_A4", lambda: plano_aux(False)),
             ("07_hoja4_pasos", pasos_hoja4), ("08_hoja4_plano_A3", lambda: plano_aux(True)),
             ("09_apoyo_12_puntos", apoyo_circulo), ("10_hoja5_bocetos", explicativo_ref), ("11_checklist", checklist)]
    with PdfPages(os.path.join(OUT, "Guia_para_dibujar_tuerca.pdf")) as pdf:
        for name, fn in pages:
            fig = fn()
            fig.savefig(os.path.join(OUT, name + ".png"), dpi=110, facecolor="white")
            pdf.savefig(fig, facecolor="white")
            plt.close(fig)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
