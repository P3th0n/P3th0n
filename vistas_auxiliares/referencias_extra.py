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
    G.dim(ax, (0, 0), (E, 0), "7", off=-1.0); G.dim(ax, (0, 0), (0, S), "7", off=1.0)
    G.dim(ax, (cx - r, cz), (cx + r, cz), f"Ø {f2(G.D_BORE)}", off=0.0, fs=8)
    G.dim(ax, (G.Q1, yT + M), (E - G.Q1, yT + M), f2(G.LADO_SUP), off=0.8)
    G.dim(ax, (cx - EX.r, yT + EX.yc), (cx + EX.r, yT + EX.yc), f"Ø {f2(G.D_EXTRA)}", off=0.0, fs=7)
    G.dim(ax, (E, yT), (E, yT + M), "3", off=-0.9); G.dim(ax, (xR, 0), (xR + M, 0), "3", off=-1.0)
    G.dim(ax, (0, S), (G.Q1, S), f2(G.Q1), off=0.8)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-2.5, xR + M + 2); ax.set_ylim(-2.5, yT + M + 2)
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
    sub = GD.sub_axes(fig, W, H, 3.5, 7.0, (-2.5, 15), (-2.5, 13))
    for pl, v in ((G.place_front, G.nF), (G.place_top, G.nT), (G.place_right, G.nR)):
        G.draw_view(sub, pl, v, lw=1.2)
    yT, xR = S + G.GAP, E + G.GAP
    G.dim(sub, (0, 0), (E, 0), "70", off=-0.9, fs=7); G.dim(sub, (0, 0), (0, S), "70", off=0.9, fs=7)
    G.dim(sub, (cx - r, cz), (cx + r, cz), f"Ø{int(round(G.D_BORE * 10))}", off=0.0, fs=6)
    G.dim(sub, (E, yT), (E, yT + M), "30", off=-0.8, fs=7)
    G.dim(sub, (cx - EX.r, yT + EX.yc), (cx + EX.r, yT + EX.yc), f"Ø{int(round(G.D_EXTRA * 10))}", off=0.0, fs=5.5)
    iso = GD.sub_axes(fig, W, H, 19.5, 9.5, (-1, 9.5), (-6.5, 7.5))
    G.draw_view(iso, lambda P: GD.iso(np.atleast_2d(P)), G.V_ISO, lw=1.0, hidden=False, cyl=False)
    for c3, e2, rad in (([cx, 0, cz], [0, 0, 1.0], r), ([cx, EX.yc, S], [0, 1.0, 0], EX.r)):
        for arc in GD.four_center(np.array(c3), np.array([1.0, 0, 0]), np.array(e2), rad)[3]:
            iso.plot(arc[:, 0], arc[:, 1], color=INK, lw=1.0)
    ax.text(1.4, 19.6, "Plano generado en SolidWorks (referencia) · cotas en mm", fontsize=7, fontfamily=BODY, color="0.4")
    fig.savefig(path, dpi=150, facecolor="white"); plt.close(fig)


def main():
    explicativo(os.path.join(OUT, "ref_explicativo.png"))
    informativo(os.path.join(OUT, "ref_informativo.png"))
    storyboard(os.path.join(OUT, "ref_storyboard.png"))
    render3d(os.path.join(OUT, "ref_sw_pieza.png"), "pieza")
    render3d(os.path.join(OUT, "ref_sw_render.png"), "render")
    plano(os.path.join(OUT, "ref_sw_plano.png"))
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
