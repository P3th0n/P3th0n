#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Imágenes de referencia para las figuras que faltaban en el documento:
  ref_explicativo.png  (fig. 11)   ref_informativo.png (fig. 12)   ref_storyboard.png (fig. 13)
  ref_sw_pieza.png     (fig. 17)   ref_sw_render.png   (fig. 18)   ref_sw_plano.png   (fig. 19)
Toda la geometría sale del modelo verificado (proyecciones_auxiliares_tuerca.py).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import laminas_tablero as T
import guia_dibujo as GD

G = T.G
V = G.V
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referencias")
os.makedirs(OUT, exist_ok=True)
BODY, INK, RED = "Inter", "#111", "#c62828"
E, S, M = G.E, G.S, G.M
cx, cz, r = G.cx, G.cz, G.D_BORE / 2
EX = G.EXTRA
f2 = GD.fmt


# ============================================================ malla 3D exacta de la tuerca
def malla():
    """Caras de la tuerca: anillos de las caras con agujero (hexágono ↔ circunferencia), caras laterales,
    cilindro del agujero roscado y del agujero superior (hasta su curva de intersección)."""
    n = 72
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    caras = []

    def borde_hex(t):                                   # punto del contorno del hexágono en la dirección t
        d = np.array([np.cos(t), np.sin(t)])
        hx = T.pF(V[:6]) - np.array([cx, cz])
        best = None
        for i in range(6):
            a, b = hx[i], hx[(i + 1) % 6]
            Mx = np.column_stack((d, a - b))
            if abs(np.linalg.det(Mx)) < 1e-12:
                continue
            s_, u_ = np.linalg.solve(Mx, a)
            if s_ > 0 and -1e-9 <= u_ <= 1 + 1e-9:
                best = s_ if best is None else min(best, s_)
        return best * d + np.array([cx, cz])

    for y in (0.0, M):                                  # caras delantera y trasera (anillo)
        for i in range(n):
            t0, t1 = th[i], th[(i + 1) % n]
            h0, h1 = borde_hex(t0), borde_hex(t1)
            c0 = np.array([cx + r * np.cos(t0), cz + r * np.sin(t0)]); c1 = np.array([cx + r * np.cos(t1), cz + r * np.sin(t1)])
            caras.append(("cara", np.array([[h0[0], y, h0[1]], [h1[0], y, h1[1]], [c1[0], y, c1[1]], [c0[0], y, c0[1]]])))
    for k in range(6):                                  # caras laterales
        f = G.faces[2 + k]
        if k == 1 and EX is not None:                   # cara superior con agujero: anillo rectángulo ↔ círculo
            x0, x1 = V[f][:, 0].min(), V[f][:, 0].max()
            for i in range(n):
                t0, t1 = th[i], th[(i + 1) % n]
                def borde_rect(t):
                    d = np.array([np.cos(t), np.sin(t)]); hw, hd = (x1 - x0) / 2, M / 2
                    s_ = min(hw / abs(d[0]) if abs(d[0]) > 1e-9 else 1e9, hd / abs(d[1]) if abs(d[1]) > 1e-9 else 1e9)
                    return np.array([cx, EX.yc]) + s_ * d
                b0, b1 = borde_rect(t0), borde_rect(t1)
                c0 = np.array([cx + EX.r * np.cos(t0), EX.yc + EX.r * np.sin(t0)]); c1 = np.array([cx + EX.r * np.cos(t1), EX.yc + EX.r * np.sin(t1)])
                caras.append(("cara", np.array([[b0[0], b0[1], S], [b1[0], b1[1], S], [c1[0], c1[1], S], [c0[0], c0[1], S]])))
        else:
            caras.append(("cara", V[f]))
    for i in range(n):                                  # cilindro del agujero roscado
        t0, t1 = th[i], th[(i + 1) % n]
        p0 = [cx + r * np.cos(t0), cz + r * np.sin(t0)]; p1 = [cx + r * np.cos(t1), cz + r * np.sin(t1)]
        caras.append(("hueco", np.array([[p0[0], 0, p0[1]], [p1[0], 0, p1[1]], [p1[0], M, p1[1]], [p0[0], M, p0[1]]])))
    if EX is not None:                                  # cilindro del agujero superior
        for i in range(n):
            t0, t1 = th[i], th[(i + 1) % n]
            a = [cx + EX.r * np.cos(t0), EX.yc + EX.r * np.sin(t0)]; b = [cx + EX.r * np.cos(t1), EX.yc + EX.r * np.sin(t1)]
            caras.append(("hueco", np.array([[a[0], a[1], S], [b[0], b[1], S], [b[0], b[1], float(EX.zb(b[0]))], [a[0], a[1], float(EX.zb(a[0]))]])))
    return caras


def render3d(path, estilo):
    caras = malla()
    luz = G.unit([0.5, -0.8, 0.9])
    vista = G.unit([1.0, -1.25, 0.95])
    fig = plt.figure(figsize=(12, 8), facecolor="white" if estilo == "pieza" else "#e9edf2")
    ax = fig.add_axes([0, 0, 1, 1], projection="3d", facecolor=fig.get_facecolor())
    polys, cols, ecs = [], [], []
    for tipo, P in caras:
        nrm = np.cross(P[1] - P[0], P[2] - P[0])
        if np.linalg.norm(nrm) < 1e-12:
            continue
        nrm = G.unit(nrm)
        if tipo == "cara" and nrm @ (P.mean(axis=0) - V.mean(axis=0)) < 0:
            nrm = -nrm
        if tipo == "hueco":
            nrm = -nrm if nrm @ vista > 0 else nrm
        lam = max(0.0, nrm @ luz)
        spec = max(0.0, G.unit(luz + vista) @ nrm) ** 30
        if estilo == "pieza":
            g = 0.55 + 0.4 * lam
            cols.append((g, g, g)); ecs.append((g, g, g))
        else:
            base = np.array([0.62, 0.66, 0.72])
            c = np.clip(base * (0.35 + 0.75 * lam) + 0.55 * spec, 0, 1)
            cols.append(tuple(c)); ecs.append(tuple(c))
        polys.append(P)
    pc = Poly3DCollection(polys, facecolors=cols, edgecolors=ecs, linewidths=0.35)
    ax.add_collection3d(pc)
    if estilo == "pieza":                               # aristas reales visibles (como en SolidWorks)
        el, az = np.deg2rad(28), np.deg2rad(-58)
        vv = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        vis, _ = G.visible_edges(vv)
        for a, b in vis:
            ax.plot(*V[[a, b]].T, color="#222222", lw=1.1, zorder=10)
        for rim in (G.CILS[0].rim(0), EX.rim()):
            ax.plot(rim[:, 0], rim[:, 1], rim[:, 2], color="#222222", lw=1.0, zorder=10)
    ax.set_xlim(-0.5, E + 0.5); ax.set_ylim(-2.25, M + 2.25); ax.set_zlim(-0.5, S + 0.5)
    ax.set_box_aspect((E + 1, M + 4.5, S + 1))
    ax.view_init(elev=28, azim=-58)
    ax.set_axis_off()
    txt = ("MEDIDAS DE MODELADO (mm)\n"
           "1. Croquis en plano Alzado: hexágono dentro de un cuadrado de 70 × 70\n    (vértices a 17,5 de las esquinas, laterales a 35 de altura).\n"
           "2. Extruir saliente/base: 30.\n"
           f"3. Asistente para taladro: Ø {GD.nice(G.D_BORE, 10)} centrado (35 ; 35), pasante.\n"
           f"4. Cara superior: círculo Ø {GD.nice(G.D_EXTRA, 10)} centrado en X (35) y a {GD.nice(EX.yc, 10)} del borde\n    delantero · Extruir corte «hasta el siguiente».")
    fig.text(0.03, 0.04, txt, fontsize=10.5, fontfamily=BODY, color=INK, linespacing=1.5,
             bbox=dict(fc="white", ec="0.7", pad=8))
    fig.savefig(path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


# ============================================================ figura 11: explicativo
def explicativo(path):
    fig = plt.figure(figsize=(12, 8.5), facecolor="white")
    a1 = fig.add_axes([0.02, 0.02, 0.96, 0.9])
    G.draw_view(a1, GD.iso, G.V_ISO, lw=1.8, hidden=False, cyl=False)
    for c3, e2, rad in (([cx, 0, cz], [0, 0, 1.0], r), ([cx, EX.yc, S], [0, 1.0, 0], EX.r)):
        for arc in GD.four_center(np.array(c3), np.array([1.0, 0, 0]), np.array(e2), rad)[3]:
            a1.plot(arc[:, 0], arc[:, 1], color=INK, lw=1.8)
    _, _ab = None, T.pF(V[[G.iB, G.iA]])
    calls = [((cx + r * np.cos(2.6), 0, cz + r * np.sin(2.6)), (-5.2, 9.0), f"Agujero roscado Ø {f2(G.D_BORE)} cm\nrecibe el perno"),
             ((cx, EX.yc, S), (-1.0, 13.4), f"Agujero superior Ø {f2(G.D_EXTRA)} cm\nllega hasta la rosca: paso del pasador\no del alambre de seguridad"),
             (V[[G.iA, G.iB, G.iC, G.iD]].mean(axis=0), (10.5, 9.8), f"Cara inclinada ABCD\n({f2(GD.ANG)}°): superficie de apoyo\nde la llave"),
             ((E / 2, 0, 0.4), (-5.2, -1.6), "Cuerpo hexagonal (caja 7 × 7 cm):\nse aprieta con llave"),
             ((E, M / 2, cz), (10.5, 3.0), "Espesor 3 cm: longitud\nde rosca que trabaja")]
    for p3, xy, txt in calls:
        p = GD.iso(np.array(p3))[0]
        a1.annotate(txt, xy=p, xytext=xy, fontsize=11, fontfamily=BODY, color=RED,
                    arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.0, mutation_scale=10))
    Pi = lambda P: GD.iso(np.atleast_2d(np.asarray(P, float)))[0]
    G.dim(a1, Pi([G.Q1, 0, 0]), Pi([G.Q1, 0, S]), "7", off=2.6, fs=10)
    G.dim(a1, Pi([E, 0, cz]), Pi([E, M, cz]), "3", off=-1.2, fs=10)
    G.dim(a1, Pi([0, 0, 0]), Pi([E, 0, 0]), "7", off=-1.4, fs=10)
    fig.text(0.02, 0.95, "Boceto descriptivo explicativo · Tuerca para perno con agujero superior", fontsize=15, fontfamily=BODY, fontweight="bold")
    a1.set_aspect("equal"); a1.axis("off"); a1.set_xlim(-6, 17); a1.set_ylim(-3, 15)
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


# ============================================================ figura 12: informativo
def informativo(path):
    fig = plt.figure(figsize=(13, 8.2), facecolor="white")
    ax = fig.add_axes([0.0, 0.0, 0.68, 0.93])
    for pl, v in ((G.place_front, G.nF), (G.place_top, G.nT), (G.place_right, G.nR)):
        G.draw_view(ax, pl, v, lw=1.6)
    yT, xR = S + G.GAP, E + G.GAP
    cc = dict(color="#2c5aa0", lw=0.7, ls=(0, (8, 2, 1, 2)))
    ax.plot([-0.5, E + 0.5], [cz, cz], **cc); ax.plot([cx, cx], [-0.5, S + 0.5], **cc)
    ax.plot([cx, cx], [yT - 0.5, yT + M + 0.5], **cc); ax.plot([xR - 0.5, xR + M + 0.5], [cz, cz], **cc)
    GD.acotar_vistas(ax, fs=8.5)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-3.0, xR + M + 2.5); ax.set_ylim(-3.0, yT + M + 2.6)
    notas = ["NOTAS TÉCNICAS", "1. Material: acero al carbono", "    con acabado zincado.", "2. Unidades: cm · Escala 1:1", "    · Tercer diedro.",
             f"3. Agujero roscado Ø {f2(G.D_BORE)}", "    (estimado), rosca con macho.",
             f"4. Agujero superior Ø {f2(G.D_EXTRA)}", "    (estimado), pasante hasta", "    el agujero roscado.",
             "5. Hexágono en caja de 7 × 7 cm,", f"    vértices a {f2(G.Q1)} cm de las esquinas.", "6. Aristas sin chaflán."]
    for k, t in enumerate(notas):
        fig.text(0.70, 0.88 - k * 0.052, t, fontsize=11, fontfamily=BODY, color=RED if k == 0 else INK, fontweight="bold" if k == 0 else "normal")
    fig.text(0.02, 0.955, "Boceto descriptivo informativo · vistas, cotas y notas técnicas", fontsize=15, fontfamily=BODY, fontweight="bold")
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


# ============================================================ figura 13: storyboard
def storyboard(path):
    fig = plt.figure(figsize=(14, 5.6), facecolor="white")
    fig.text(0.02, 0.93, "Boceto descriptivo storyboard · secuencia de uso", fontsize=15, fontfamily=BODY, fontweight="bold")
    textos = [("1. Acercar la tuerca", "La tuerca se enrosca en el extremo del perno."),
              ("2. Roscar y apretar", "Se aprieta con llave contra las piezas a unir."),
              ("3. Bloquear", "Se pasa el pasador o alambre por el agujero superior.")]
    for k in range(3):
        a = fig.add_axes([0.02 + k * 0.33, 0.12, 0.30, 0.72]); a.axis("off"); a.set_xlim(-0.6, 11); a.set_ylim(-3.5, 11)
        a.add_patch(Rectangle((-0.5, -3.3), 11.3, 14.1, fill=False, ec="0.55", lw=1.0))
        a.add_patch(Rectangle((0.2, 0), 1.2, 7, fc="0.92", ec=INK, lw=1.4))                 # cabeza del perno
        a.add_patch(Rectangle((1.4, cz - r), 8.4, 2 * r, fc="0.97", ec=INK, lw=1.4))      # vástago
        for x0, h in ((1.4, "///"), (2.4, "\\\\\\")):
            a.add_patch(Rectangle((x0, -0.6), 1.0, 8.2, fill=False, ec="0.35", lw=1.0, hatch=h))
        nx = 6.8 if k == 0 else 3.4
        a.add_patch(Rectangle((nx, 0), M, S, fc="#fde2e2", ec=RED, lw=1.8))
        a.plot([nx + M / 2 - EX.r, nx + M / 2 - EX.r], [S, S - 1.7], color=RED, lw=0.9, ls=(0, (3, 2)))
        a.plot([nx + M / 2 + EX.r, nx + M / 2 + EX.r], [S, S - 1.7], color=RED, lw=0.9, ls=(0, (3, 2)))
        if k == 0:
            a.annotate("", xy=(4.0, cz), xytext=(6.6, cz), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
            G.dim(a, (nx, S), (nx + M, S), "3", off=0.6, fs=8); G.dim(a, (nx + M, 0), (nx + M, S), "7", off=-0.6, fs=8)
            G.dim(a, (2.0, cz - r), (2.0, cz + r), f"Ø {GD.nice(G.D_BORE)}", off=0.0, fs=7)
        if k == 1:
            a.annotate("", xy=(nx + M / 2, S + 1.6), xytext=(nx + M + 1.6, S + 0.6),
                       arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4, connectionstyle="arc3,rad=0.5"))
        if k == 2:
            a.add_patch(Rectangle((nx + M / 2 - 0.3, S - 1.6), 0.6, 4.4, fc="0.75", ec=INK, lw=1.2))
            a.annotate("", xy=(nx + M / 2, S + 0.2), xytext=(nx + M / 2, S + 3.4), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6))
        a.text(5.1, -1.7, textos[k][0], ha="center", fontsize=12, fontfamily=BODY, fontweight="bold")
        a.text(5.1, -2.7, textos[k][1], ha="center", fontsize=9.5, fontfamily=BODY, color="#444")
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


# ============================================================ figura 19: plano tipo SolidWorks
def plano(path):
    fig, ax, W, H = GD.paper("A4", "Tuerca para perno", 6)
    sub = GD.sub_axes(fig, W, H, 3.8, 6.3, (-2.8, 15), (-2.8, 13.6))
    for pl, v in ((G.place_front, G.nF), (G.place_top, G.nT), (G.place_right, G.nR)):
        G.draw_view(sub, pl, v, lw=1.2)
    yT, xR = S + G.GAP, E + G.GAP
    GD.acotar_vistas(sub, k=10, fs=6)
    iso = GD.sub_axes(fig, W, H, 19.5, 9.5, (-1, 9.5), (-6.5, 7.5))
    G.draw_view(iso, lambda P: GD.iso(np.atleast_2d(P)), G.V_ISO, lw=1.0, hidden=False, cyl=False)
    for c3, e2, rad in (([cx, 0, cz], [0, 0, 1.0], r), ([cx, EX.yc, S], [0, 1.0, 0], EX.r)):
        for arc in GD.four_center(np.array(c3), np.array([1.0, 0, 0]), np.array(e2), rad)[3]:
            iso.plot(arc[:, 0], arc[:, 1], color=INK, lw=1.0)
    ax.text(1.4, 19.6, "Plano generado en SolidWorks (referencia) · cotas en mm", fontsize=7, fontfamily=BODY, color="0.4")
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


def vistas(path):
    fig = plt.figure(figsize=(12.5, 9.5), facecolor="white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 0.94])
    for pl, v in ((G.place_front, G.nF), (G.place_top, G.nT), (G.place_right, G.nR)):
        G.draw_view(ax, pl, v, lw=1.6)
    yT, xR = S + G.GAP, E + G.GAP
    cc = dict(color="#2c5aa0", lw=0.7, ls=(0, (8, 2, 1, 2)))
    ax.plot([-0.5, E + 0.5], [cz, cz], **cc); ax.plot([cx, cx], [-0.5, S + 0.5], **cc)
    ax.plot([cx, cx], [yT - 0.5, yT + M + 0.5], **cc); ax.plot([xR - 0.5, xR + M + 0.5], [cz, cz], **cc)
    GD.acotar_vistas(ax, fs=9)
    for txt, xy, ha in (("VISTA FRONTAL", (E / 2, -2.6), "center"), ("VISTA SUPERIOR", (-0.6, yT + M / 2), "right"),
                        ("LATERAL DERECHA", (xR + M / 2, S + 1.7), "center")):
        ax.text(*xy, txt, fontsize=10, fontfamily=BODY, color="0.35", ha=ha)
    fig.text(0.02, 0.96, "Vistas principales · cotas en cm · escala 1:1 · tercer diedro", fontsize=14, fontfamily=BODY, fontweight="bold")
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-5.0, xR + M + 2.5); ax.set_ylim(-3.2, yT + M + 2.6)
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


def iso_acotado(path):
    fig = plt.figure(figsize=(12, 10), facecolor="white")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.9])
    Pi = lambda P: GD.iso(np.atleast_2d(np.asarray(P, float)))[0]
    lo, hi = np.zeros(3), np.array([E, M, S])
    box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    for a in range(8):
        for b in range(a + 1, 8):
            if np.sum(np.abs(box[a] - box[b]) > 1e-9) == 1:
                q = GD.iso(box[[a, b]]); ax.plot(q[:, 0], q[:, 1], color="#9aa0a6", lw=0.7)
    G.draw_view(ax, lambda P: GD.iso(np.atleast_2d(P)), G.V_ISO, lw=1.8, hidden=True, cyl=False)
    for c3, e2, rad, ls in (([cx, 0, cz], [0, 0, 1.0], r, "-"), ([cx, M, cz], [0, 0, 1.0], r, "--"), ([cx, EX.yc, S], [0, 1.0, 0], EX.r, "-")):
        for arc in GD.four_center(np.array(c3), np.array([1.0, 0, 0]), np.array(e2), rad)[3]:
            ax.plot(arc[:, 0], arc[:, 1], color=INK, lw=1.8 if ls == "-" else 0.9, ls=ls)
    d = lambda p, q, t, off, f=10: G.dim(ax, Pi(p), Pi(q), t, off=off, fs=f)
    d([0, 0, 0], [E, 0, 0], "7", -1.4)
    d([0, 0, 0], [0, 0, S], "7", 1.4)
    d([E, 0, 0], [E, M, 0], "3", -1.0)
    d([0, 0, S], [G.Q1, 0, S], GD.nice(G.Q1), 0.8, 9); d([E - G.Q1, 0, S], [E, 0, S], GD.nice(G.Q1), -0.8, 9)
    d([0, 0, 0], [0, 0, cz], GD.nice(cz), 0.6, 9)
    d([0, 0, S], [cx, 0, S], GD.nice(cx), 1.9, 9)
    d([0, 0, S], [0, EX.yc, S], GD.nice(EX.yc), 0.8, 9)
    for p3, xy, t in (([cx - r * 0.7, 0, cz - r * 0.7], (-5.0, -1.0), f"Ø {GD.nice(G.D_BORE)}\n(centro a 3,5 × 3,5)"),
                      ([cx, EX.yc, S], (-2.5, 13.2), f"Ø {GD.nice(G.D_EXTRA)} (centro a {GD.nice(cx)} sobre X\ny {GD.nice(EX.yc)} sobre Y)")):
        ax.annotate(t, xy=Pi(p3), xytext=xy, fontsize=10, fontfamily=BODY, color=INK,
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9, mutation_scale=9))
    fig.text(0.02, 0.95, "Isométrico acotado · caja 7 × 7 × 3 cm · medidas reales sobre los ejes", fontsize=14, fontfamily=BODY, fontweight="bold")
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-6.5, 16); ax.set_ylim(-5, 14.5)
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


def aux_acotada(path, total):
    import laminas_limpias as LL
    fig, ax = LL.new_fig("Proyección auxiliar total — acotada" if total else "Proyecciones auxiliares parciales — acotadas",
                         "Todas las distancias para trazar: separaciones (eje, LOS1, LOS2) y distancias trasladadas con la regla de las dos vistas.")
    reqs = []
    idx = T.ALL if total else T.FACE
    arrs = LL.base_views(ax, reqs, idx)
    arrs += LL.los1_and_aux1(ax, reqs, idx, total)
    arrs += LL.los2_and_aux2(ax, reqs, idx, total)
    DC = LL.DIM
    dd = lambda p, q, t, off, f=12: G.dim(ax, p, q, t, off=off, fs=f, color=DC)
    x_eje = T.X_EJE_L
    dd((0, cz), (E, cz), "7", -(cz + 1.4))
    dd((x_eje, -0.4), (0, -0.4), GD.nice(-x_eje), -0.5)
    dd((x_eje - T.D_REF, S), (x_eje, S), GD.nice(T.D_REF), 0.6)
    dd((x_eje - T.D_REF - M, S), (x_eje - T.D_REF, S), "3", 1.3)
    dd((x_eje - T.D_REF - M, 0), (x_eje - T.D_REF - M, S), "7", 0.9)
    pA = T.pF(V[G.iA])[0]; footA = pA + (T.H1 - pA @ T.N1) * T.N1
    dd(pA, footA, GD.nice(T.AUX_GAP1), 0.5)
    amax = (T.p1(V[idx]) @ T.T1).max()
    for kk, i in enumerate((G.iA, G.iD) if not total else ((G.FACE_K + 2) % 6, (G.FACE_K + 2) % 6 + 6)):
        q = T.p1(V[i])[0]; a = amax + 0.8 + 0.8 * kk
        foot, end = a * T.T1 + T.H1 * T.N1, a * T.T1 + (q @ T.N1) * T.N1
        ax.plot([q[0], end[0] + 0.2 * T.T1[0]], [q[1], end[1] + 0.2 * T.T1[1]], color=DC, lw=0.8)
        dd(foot, end, GD.nice((q @ T.N1) - T.H1), 0.0)
    e0, e1 = T.H1 * T.N1 + (amax + 0.5) * T.T1, T.H1 * T.N1 + (amax + 2.2) * T.T1
    ax.plot([e0[0], e1[0]], [e0[1], e1[1]], color="#c62828", lw=1.4, ls=(0, (7, 4)))
    q1 = T.p1(V[[G.iA, G.iB, G.iC]])
    dd(q1[1], q1[0], GD.nice(G.LADO_INC), -0.55, 11); dd(q1[1], q1[2], "3", 0.55, 11)
    ymin = min(T.p1(V[idx])[:, 1].min(), T.p2(V[idx])[:, 1].min())
    yl = -2.7
    dd((0, yl), (T.H2, yl), GD.nice(T.H2) + " (desde O)", 0.0)
    ax.plot([0, 0], [-1.7, yl - 0.2], color=DC, lw=0.6); ax.plot([T.H2, T.H2], [ymin - 1.0, yl - 0.2], color=DC, lw=0.6)
    ytop = T.p2(V[idx])[:, 1].max()
    groups = {}
    for i in idx:
        groups.setdefault(round(float(T.H1 - T.pF(V[i])[0] @ T.N1), 3), []).append(i)
    for kk, (dist, ii) in enumerate(sorted(groups.items())):
        q = max((T.p2(V[i])[0] for i in ii), key=lambda rr: rr[1])
        y = ytop + 0.8 + 0.8 * kk
        ax.plot([q[0], q[0]], [q[1], y + 0.2], color=DC, lw=0.8)
        dd((T.H2, y), (q[0], y), GD.nice(dist), 0.0)
    ax.plot([T.H2, T.H2], [ytop, ytop + 0.8 * (len(groups) + 1)], color="#c62828", lw=1.4, ls=(0, (7, 4)))
    LL.frame(ax, arrs + [T.p1(V), T.p2(V)], pad=(3.0, 3.4, 3.2, 0.8 * len(groups) + 1.6))
    LL.place_labels(fig, ax, reqs)
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


def main():
    vistas(os.path.join(OUT, "ref_vistas.png"))
    iso_acotado(os.path.join(OUT, "ref_iso.png"))
    aux_acotada(os.path.join(OUT, "ref_aux_parcial.png"), False)
    aux_acotada(os.path.join(OUT, "ref_aux_total.png"), True)
    explicativo(os.path.join(OUT, "ref_explicativo.png"))
    informativo(os.path.join(OUT, "ref_informativo.png"))
    storyboard(os.path.join(OUT, "ref_storyboard.png"))
    render3d(os.path.join(OUT, "ref_sw_pieza.png"), "pieza")
    render3d(os.path.join(OUT, "ref_sw_render.png"), "render")
    plano(os.path.join(OUT, "ref_sw_plano.png"))
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
