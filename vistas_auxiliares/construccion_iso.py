#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construcción paso a paso del círculo de la cara superior en isométrico (método de 4 centros)."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import laminas_tablero as T
import guia_dibujo as GD

G = T.G
V = G.V
E, S, M, Q1, EX, cx = G.E, G.S, G.M, G.Q1, G.EXTRA, G.cx
BODY, INK, RED, DIM, GR = "Inter", "#111", "#d62828", "#6a35b8", "#b0b4ba"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referencias", "construccion_iso_agujero_superior.png")
Pi = lambda P: GD.iso(np.atleast_2d(np.asarray(P, float)))[0]
n = GD.nice

Q, Mm, cen, arcs = GD.four_center(np.array([cx, EX.yc, S]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), EX.r)
OB, SM = cen[:2], cen[2:]
C = Pi([cx, EX.yc, S])
R_big = np.linalg.norm(arcs[0][0] - OB[0]); R_small = np.linalg.norm(arcs[2][0] - SM[0])


def base(ax, texto):
    caja = [Pi([0, 0, S]), Pi([E, 0, S]), Pi([E, M, S]), Pi([0, M, S])]
    cara = [Pi([Q1, 0, S]), Pi([E - Q1, 0, S]), Pi([E - Q1, M, S]), Pi([Q1, M, S])]
    ax.plot(*np.vstack((caja, caja[:1])).T, color=GR, lw=1.0)
    ax.plot(*np.vstack((cara, cara[:1])).T, color=INK, lw=1.8)
    lo, hi = np.min(caja, axis=0), np.max(caja, axis=0)
    ax.set_xlim(lo[0] - 0.6, hi[0] + 0.6); ax.set_ylim(lo[1] - 1.7, hi[1] + 0.4); ax.set_aspect("equal"); ax.axis("off")
    ax.text(0.03, 0.02, texto, transform=ax.transAxes, fontsize=10.5, fontfamily=BODY, color=INK, va="bottom", linespacing=1.45)


def dot(ax, p, txt=None, off=(0.12, 0.12), c=RED):
    ax.plot(*p, "o", ms=5, color=c, zorder=6)
    if txt:
        ax.text(p[0] + off[0], p[1] + off[1], txt, fontsize=10, color=c, fontfamily=BODY, zorder=7)


fig, axs = plt.subplots(2, 2, figsize=(15, 11), facecolor="white")
fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.03, wspace=0.05, hspace=0.18)
fig.text(0.02, 0.955, f"Círculo de la cara superior en isométrico · Ø {n(G.D_EXTRA)} cm · método de 4 centros", fontsize=17, fontfamily=BODY, fontweight="bold")
fig.text(0.02, 0.925, "Gris = caja 7 × 7 × 3 · Negro = tuerca · Rojo = lo nuevo de cada paso · Morado = medidas (reales sobre los ejes)", fontsize=10.5, fontfamily=BODY, color="#555")

a = axs[0, 0]; base(a, "Desde la esquina de la caja (7 cm sobre O): mide 3,5 cm sobre X\ny luego 1,5 cm sobre Y. Ese punto es el centro C del agujero."); a.set_title("1 · Ubicar el centro C", fontsize=13, fontfamily=BODY, loc="left")
P0 = Pi([0, 0, S]); P1 = Pi([cx, 0, S])
dot(a, P0, "esquina de la caja", off=(-0.2, 0.45), c=INK)
a.plot([P0[0], P1[0]], [P0[1], P1[1]], color=RED, lw=2); a.plot([P1[0], C[0]], [P1[1], C[1]], color=RED, lw=2)
G.dim(a, P0, P1, f"{n(cx)} sobre X", off=0.55, fs=10, color=DIM); G.dim(a, P1, C, f"{n(EX.yc)} sobre Y", off=-0.5, fs=10, color=DIM)
dot(a, C, "C", off=(0.15, 0.1))

a = axs[0, 1]; base(a, "Desde C mide 0,75 cm a cada lado sobre X y sobre Y (puntos morados:\ndonde el círculo toca el rombo). Por ellos, paralelas a los ejes = rombo 1,5 × 1,5."); a.set_title(f"2 · Rombo de {n(G.D_EXTRA)} × {n(G.D_EXTRA)}", fontsize=13, fontfamily=BODY, loc="left")
dot(a, C, "C", off=(0.12, -0.3))
a.plot(*np.vstack((Q, Q[:1])).T, color=RED, lw=2)
for m in Mm:
    dot(a, m, None, c=DIM)
G.dim(a, Q[2], Q[3], n(G.D_EXTRA), off=-0.45, fs=10, color=DIM); G.dim(a, Q[3], Q[0], n(G.D_EXTRA), off=-0.45, fs=10, color=DIM)

a = axs[1, 0]; base(a, "Desde cada vértice obtuso (O1, O2, de 120°) traza rectas a los puntos\nmedios de los dos lados opuestos. Donde se cruzan están S1 y S2."); a.set_title("3 · Centros de los arcos", fontsize=13, fontfamily=BODY, loc="left")
a.plot(*np.vstack((Q, Q[:1])).T, color=INK, lw=1.2)
for o in OB:
    for m in Mm:
        if np.linalg.norm(m - o) > np.linalg.norm(Q[0] - Q[1]) * 0.6:
            a.plot([o[0], m[0]], [o[1], m[1]], color=RED, lw=1.3)
for k, o in enumerate(OB):
    dot(a, o, f"O{k + 1} (120°)", off=(0.12, 0.12 if o[1] > C[1] else -0.32))
for k, sm in enumerate(SM):
    dot(a, sm, f"S{k + 1}", off=(0.0, 0.14))

a = axs[1, 1]; base(a, f"Compás en O1 y O2 con radio {n(R_big)} cm: arcos grandes.\nCompás en S1 y S2 con radio {n(R_small)} cm: arcos pequeños.\nCada arco va de un punto morado al siguiente."); a.set_title("4 · Arcos con el compás", fontsize=13, fontfamily=BODY, loc="left")
a.plot(*np.vstack((Q, Q[:1])).T, color=GR, lw=1.0)
for k, arc in enumerate(arcs):
    a.plot(arc[:, 0], arc[:, 1], color=RED, lw=2.4)
for o in OB:
    dot(a, o, None, c=DIM)
for sm in SM:
    dot(a, sm, None, c=DIM)
o, arc = OB[0], arcs[0]; mid = arc[len(arc) // 2]
a.plot([o[0], mid[0]], [o[1], mid[1]], color=DIM, lw=1.0, ls=(0, (3, 2)))
a.annotate(f"R {n(R_big)}", xy=(o + mid) / 2, xytext=(o + mid) / 2 + np.array([1.6, 0.5]), fontsize=10, color=DIM, fontfamily=BODY,
           arrowprops=dict(arrowstyle="-", color=DIM, lw=0.7))
sm, arc = SM[1], arcs[3]; mid = arc[len(arc) // 2]
a.plot([sm[0], mid[0]], [sm[1], mid[1]], color=DIM, lw=1.0, ls=(0, (3, 2)))
a.annotate(f"R {n(R_small)}", xy=(sm + mid) / 2, xytext=(sm + mid) / 2 + np.array([1.4, -0.7]), fontsize=10, color=DIM, fontfamily=BODY,
           arrowprops=dict(arrowstyle="-", color=DIM, lw=0.7))
for k, o in enumerate(OB):
    a.text(*(o + np.array([0.12, 0.12 if o[1] > C[1] else -0.32])), f"O{k + 1}", fontsize=10, color=DIM, fontfamily=BODY)
for k, sm in enumerate(SM):
    a.text(*(sm + np.array([-0.1, 0.14])), f"S{k + 1}", fontsize=10, color=DIM, fontfamily=BODY, ha="center")
fig.savefig(OUT, dpi=150, facecolor="white")
print(OUT, round(R_big, 3), round(R_small, 3))
