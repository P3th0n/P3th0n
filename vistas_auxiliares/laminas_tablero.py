#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LÁMINAS ESTILO TABLERO — proyecciones auxiliares PARCIALES y TOTALES de la tuerca
==================================================================================
Reproduce la construcción de las pizarras de clase:

    perfil (L) ─ eje de referencia ─ ALZADO (F) ─ LOS1 ─ AUXILIAR 1 ─ LOS2 ─ AUXILIAR 2
                                       │
                               eje de referencia
                                       │
                                  PLANTA (T)

  * Puntos rotulados con subíndice de la vista: A_F, A_L, A_1, A_2 …
  * Líneas de origen (proyectantes) finas, prolongadas, perpendiculares a cada línea de pliegue.
  * Regla de traslado de distancias (método del eje de referencia):
        distancia en AUX 1 desde LOS1  =  distancia en el PERFIL desde su eje de referencia
        distancia en AUX 2 desde LOS2  =  distancia en el ALZADO desde LOS1
  * Se dibuja por etapas: primero la auxiliar PARCIAL (solo la cara ABCD) y después,
    proyectando los vértices restantes con el mismo procedimiento, la auxiliar TOTAL.

La geometría (vértices, caras, normales por producto cruz, visibilidad, agujero) se importa de
proyecciones_auxiliares_tuerca.py, así que cualquier cambio de medidas allí se refleja aquí.
Cada vista se comprueba numéricamente: es una proyección ortogonal exacta colocada en la hoja
con una rotación rígida (sin espejo) y las líneas de origen son perpendiculares a los pliegues.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages

import proyecciones_auxiliares_tuerca as G

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------------------------
# Estilo "tablero": letra manuscrita (Patrick Hand, OFL), tinta negra, rótulos rojos, origen verde
# ---------------------------------------------------------------------------------------------
FONT = os.path.join(HERE, "fuentes", "PatrickHand-Regular.ttf")
if os.path.exists(FONT):
    font_manager.fontManager.addfont(FONT)
    HAND = font_manager.FontProperties(fname=FONT).get_name()
    plt.rcParams.update({"font.family": [HAND, "DejaVu Sans"], "mathtext.fontset": "custom",
                         "mathtext.rm": HAND, "mathtext.it": HAND, "mathtext.bf": HAND, "mathtext.sf": HAND,
                         "mathtext.cal": HAND})
BG, INK, RED, TEAL, BLUE, FILL = "#fbfbf8", "#121212", "#c62828", "#16917f", "#2f6fdc", "#ffe066"
G.C_VIS, G.C_HID = INK, "#2b2b2b"

V, X, Y, Z = G.V, G.X, G.Y, G.Z
unit, proj = G.unit, G.proj

# ---------------------------------------------------------------------------------------------
# Rótulos de los 12 vértices: cara inclinada ABCD (A,B delante; C,D detrás), resto E…L
# ---------------------------------------------------------------------------------------------
k = G.FACE_K
LET = {G.iA: "A", G.iB: "B", G.iC: "C", G.iD: "D"}
for j, ch in enumerate("EFGH"):
    i = (k + 2 + j) % 6
    LET[i], LET[i + 6] = ch, "IJKL"[j]
FACE = G.FACE                              # [A, B, C, D]
FRONT_FACE = [G.iA, G.iB]                  # vértices de la cara visibles en el alzado
ALL = list(range(12))

# ---------------------------------------------------------------------------------------------
# Distancias de la hoja (cm, escala 1:1)
# ---------------------------------------------------------------------------------------------
D_REF = 1.0      # eje de referencia → cara frontal de la pieza (y = 0)
G_EJE = 1.8      # alzado → eje de referencia (separa perfil y planta)
AUX_GAP1 = 3.0   # alzado → LOS1
AUX_GAP2 = 1.5   # auxiliar 1 → LOS2

# ---------------------------------------------------------------------------------------------
# VISTAS PRINCIPALES  (tercer diedro: planta encima, perfil izquierdo a la izquierda)
# ---------------------------------------------------------------------------------------------
def pF(P):                                   # alzado: (x, z)
    return proj(P, G.uF, G.wF)


nL = -X                                      # perfil izquierdo: observador en x < 0
uL, wL = G.basis_from_normal(nL, Z)          # uL = −Y  → la cara frontal (y=0) queda junto al alzado
X_EJE_L = -G_EJE


def pL(P):
    return proj(P, uL, wL) + np.array([X_EJE_L - D_REF, 0.0])


Z_EJE_T = G.ZMAX + G_EJE


def pT(P):                                   # planta: (x, y) encima del alzado
    return proj(P, G.uT, G.wT) + np.array([0.0, Z_EJE_T + D_REF])


# ---------------------------------------------------------------------------------------------
# AUXILIAR 1  (adyacente al alzado; LOS1 = normal de la cara ABCD, calculada con producto cruz)
# ---------------------------------------------------------------------------------------------
LOS1 = G.n_face
N1 = np.array([LOS1 @ G.uF, LOS1 @ G.wF])            # dirección de las líneas de origen en la hoja
T1 = np.array([-N1[1], N1[0]])                        # dirección de LOS1 (pliegue) en la hoja
T3 = unit(np.cross(G.nF, LOS1))                       # la misma dirección en 3D
assert np.allclose([T3 @ G.uF, T3 @ G.wF], T1)
H1 = (pF(V) @ N1).max() + AUX_GAP1                   # posición de LOS1


def depth1(P):                                         # profundidad respecto del plano frontal (= y)
    return -(np.atleast_2d(P) @ G.nF)


def p1(P):
    P = np.atleast_2d(P)
    return np.outer(P @ T3, T1) + np.outer(H1 + D_REF + depth1(P), N1)


# ---------------------------------------------------------------------------------------------
# AUXILIAR 2  (adyacente a la auxiliar 1; líneas de origen horizontales y LOS2 vertical, como en el tablero)
# ---------------------------------------------------------------------------------------------
N2 = np.array([1.0, 0.0])
T2 = np.array([0.0, 1.0])
R1 = np.column_stack((T1, -N1))                       # p1 = O1 + R1·[P·T3, P·nF]  (rotación, det = +1)
ab = R1.T @ N2
LOS2 = unit(ab[0] * T3 + ab[1] * G.nF)                # dirección 3D de la mirada 2 (está en el plano de AUX 1)
assert abs(LOS2 @ LOS1) < 1e-12
H2 = (p1(V) @ N2).max() + AUX_GAP2                   # posición de LOS2


def p2(P):
    P = np.atleast_2d(P)
    dist_F = H1 - pF(P) @ N1                          # distancia en el ALZADO desde LOS1
    return np.outer(p1(P) @ T2, T2) + np.outer(H2 + dist_F, N2)


# ---------------------------------------------------------------------------------------------
# COMPROBACIONES (el script se detiene si alguna falla)
# ---------------------------------------------------------------------------------------------
def check_rigid(place, v, name):
    """La vista en la hoja = rotación rígida (sin espejo) de la proyección ortogonal según v."""
    u, w = G.basis_from_normal(v, Z if abs(unit(v) @ Z) < 0.9 else Y)
    pts = np.vstack([V] + [c.rim(t) for c in G.CILS for t in (0, 1)])
    I = np.column_stack((pts @ u, pts @ w, np.ones(len(pts))))
    Q = place(pts)
    sol, *_ = np.linalg.lstsq(I, Q, rcond=None)
    A = sol[:2].T
    res = np.abs(I @ sol - Q).max()
    assert res < 1e-9, f"{name}: no es una proyección ortogonal exacta ({res})"
    assert np.allclose(A.T @ A, np.eye(2), atol=1e-9), f"{name}: no conserva distancias"
    assert abs(np.linalg.det(A) - 1) < 1e-9, f"{name}: imagen en espejo"
    return res


CHECKS = {nm: check_rigid(pl, v, nm) for nm, pl, v in
          (("alzado", pF, G.nF), ("perfil", pL, nL), ("planta", pT, G.nT), ("auxiliar 1", p1, LOS1), ("auxiliar 2", p2, LOS2))}
# líneas de origen ⟂ a cada pliegue
assert np.abs((p1(V) - pF(V)) @ T1).max() < 1e-12
assert np.abs((p2(V) - p1(V)) @ T2).max() < 1e-12
assert np.abs((pL(V) - pF(V)) @ np.array([0, 1.0])).max() < 1e-12
assert np.abs((pT(V) - pF(V)) @ np.array([1.0, 0])).max() < 1e-12
# regla del eje de referencia
assert np.allclose(p1(V) @ N1 - H1, X_EJE_L - pL(V)[:, 0])        # AUX1 desde LOS1 = PERFIL desde su eje
assert np.allclose(p1(V) @ N1 - H1, pT(V)[:, 1] - Z_EJE_T)        # … = PLANTA desde su eje
assert np.allclose(p2(V) @ N2 - H2, H1 - pF(V) @ N1)              # AUX2 desde LOS2 = ALZADO desde LOS1
# verdadera magnitud en AUX 1 y cara de canto en AUX 2
fa = p1(V[FACE])
assert abs(G.area2d(fa) - G.area3d(V[FACE])) < 1e-9
assert np.ptp(p2(V[FACE])[:, 0]) < 1e-9


# ---------------------------------------------------------------------------------------------
# DIBUJO
# ---------------------------------------------------------------------------------------------
def hull(pts):
    P = sorted(set(map(tuple, np.round(pts, 9))))
    if len(P) < 3:
        return np.array(P)
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


def origin_line(ax, p, q, d, poly, color, ext=1.0):
    """Línea de origen desde el contorno de la vista de partida hasta pasar la vista de llegada."""
    lam = G.ray_exit(p, d, poly) if poly is not None and len(poly) >= 3 else 0.0
    s, e = p + lam * d, q + ext * d
    ax.plot([s[0], e[0]], [s[1], e[1]], color=color, lw=0.85, zorder=1, solid_capstyle="butt")


def fold(ax, a, b, text, at="b", dx=(0.4, -0.6)):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=RED, lw=1.4, ls=(0, (7, 4)), zorder=2)
    end = b if at == "b" else a
    ax.annotate(text, xy=end, xytext=(end[0] + dx[0], end[1] + dx[1]), color=RED, fontsize=15,
                ha="left", va="center", arrowprops=dict(arrowstyle="->", color=RED, lw=1.1,
                                                        connectionstyle="angle,angleA=0,angleB=90,rad=4"))


def mark90(ax, corner, back, side, s=0.32):
    a, b = corner + s * back, corner + s * side
    ax.plot([a[0], a[0] + s * side[0], b[0]], [a[1], a[1] + s * side[1], b[1]], color=TEAL, lw=1.2, zorder=3)
    t = corner + 0.95 * back + 0.6 * side
    ax.text(t[0], t[1], "90°", color=TEAL, fontsize=12, ha="center", va="center")


def labels(ax, place, v, idx, suf, off=0.62, fs=15, center=None):
    P = V[idx]
    Q = place(P)
    c = place(V).mean(axis=0) if center is None else center
    used = [False] * len(idx)
    for i in range(len(idx)):
        if used[i]:
            continue
        grp = [i]
        used[i] = True
        for j in range(i + 1, len(idx)):
            if not used[j] and np.linalg.norm(Q[i] - Q[j]) < 1e-6:
                grp.append(j)
                used[j] = True
        grp.sort(key=lambda t: -(P[t] @ v))                       # el más cercano al observador primero
        txt = "$" + r"\,".join(f"{LET[idx[t]]}_{{{suf}}}" for t in grp) + "$"
        d = Q[grp[0]] - c
        d = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.array([0.7, 0.7])
        ax.text(*(Q[grp[0]] + off * d), txt, color=RED, fontsize=fs, ha="center", va="center", zorder=6)


def face_only(ax, place, fill=True, lw=2.3):
    q = place(V[FACE])
    if fill and G.area2d(q) > 1e-9:
        ax.fill(q[:, 0], q[:, 1], color=FILL, alpha=0.55, zorder=1)
    ax.plot(*np.vstack((q, q[:1])).T, color=INK, lw=lw, zorder=5, solid_capstyle="round")


def draw_iso(ax, total):
    v = G.V_ISO
    u, w = G.iso_basis(v)
    place = lambda P: proj(P, u, w)
    lo, hi = V.min(axis=0), V.max(axis=0)                 # caja envolvente (como en el tablero)
    box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    for a in range(8):
        for b in range(a + 1, 8):
            if np.sum(np.abs(box[a] - box[b]) > 1e-9) == 1:
                q = place(box[[a, b]])
                ax.plot(q[:, 0], q[:, 1], color=TEAL, lw=0.7, zorder=0)
    G.draw_view(ax, place, v, lw=1.7)
    q = place(V[FACE])
    ax.fill(q[:, 0], q[:, 1], color=FILL, alpha=0.55, zorder=1)
    idx = ALL if total else FACE
    c = place(V).mean(axis=0)
    for i in idx:
        p = place(V[i])[0]
        d = unit(p - c)
        ax.text(*(p + 0.55 * d), LET[i], color=RED, fontsize=13, ha="center", va="center")
    ax.set_aspect("equal"); ax.axis("off")
    P = place(V)
    ax.set_xlim(P[:, 0].min() - 1, P[:, 0].max() + 1); ax.set_ylim(P[:, 1].min() - 1, P[:, 1].max() + 1)


STAGES = {
    1: ("Paso 1 · Vistas principales y ejes de referencia",
        "Alzado (F), perfil (L) y planta alineados. Las distancias se miden desde los ejes de referencia (rojo)."),
    2: ("Paso 2 · LOS1 perpendicular a la cara ABCD",
        "En el alzado la cara se ve de canto (A_F D_F – B_F C_F). LOS1 se traza paralela a ella; las líneas de origen salen a 90°."),
    3: ("Paso 3 · Proyección auxiliar parcial 1 → verdadera magnitud de ABCD",
        "Distancia de cada punto a LOS1 = distancia en el perfil desde su eje de referencia."),
    4: ("Proyecciones auxiliares parciales  (Escala 1:1)",
        "Paso 4 · LOS2: líneas de origen horizontales desde la auxiliar 1. Distancia a LOS2 = distancia en el alzado desde LOS1. La cara vuelve a verse de canto."),
    5: ("Paso 5 · De la parcial a la total: se proyectan los vértices restantes E … L",
        "Mismo procedimiento que la cara ABCD (verde): las líneas azules llevan el resto de la tuerca a la auxiliar 1."),
    6: ("Análisis de vistas o proyecciones auxiliares totales",
        "Paso 6 · Auxiliar 2 total: toda la tuerca desde LOS2. La cara ABCD (amarilla) es la proyección parcial de la que sale todo."),
}


def render(stage):
    fig = plt.figure(figsize=(19, 10), facecolor=BG)
    ax = fig.add_axes([0.0, 0.035, 1.0, 0.86], facecolor=BG)
    title, sub = STAGES[stage]
    fig.text(0.02, 0.955, title, fontsize=30, color=INK, ha="left", va="center")
    fig.text(0.02, 0.905, sub, fontsize=15, color="#333", ha="left", va="center")
    fig.text(0.02, 0.015, f"Tuerca hexagonal: s = {G.S:.2f} · e = {G.E:.2f} · m = {G.M:.2f} cm · Ø agujero ≈ {G.D_BORE:.1f} cm (estimado) · "
             "tercer diedro · escala 1:1 · todas las líneas calculadas con numpy (proyecciones ortogonales verificadas)",
             fontsize=11, color="#555")
    total = stage >= 5
    hexF = pF(V[:6])

    # --- vistas principales -------------------------------------------------------------
    G.draw_view(ax, pF, G.nF, lw=2.2)
    G.draw_view(ax, pL, nL, lw=2.2)
    G.draw_view(ax, pT, G.nT, lw=2.2)
    face_only(ax, pF, fill=False, lw=4.0)                       # cara de canto, resaltada
    ax.plot(*pF(V[FRONT_FACE]).T, color=FILL, lw=9, alpha=0.7, zorder=1, solid_capstyle="round")
    # líneas de origen alzado ↔ perfil y alzado ↔ planta
    for i in range(6):
        p = pF(V[i])[0]
        origin_line(ax, p, pL(V[i + 6])[0], np.array([-1.0, 0]), hexF, TEAL, ext=0.6)
        origin_line(ax, p, pT(V[i + 6])[0], np.array([0, 1.0]), hexF, TEAL, ext=0.6)
    yb, yt = -1.4, G.ZMAX + 0.6
    fold(ax, (X_EJE_L, yt), (X_EJE_L, yb), "Eje de referencia", dx=(0.4, -0.5))
    ax.plot([-0.8, G.XMAX + 0.8], [Z_EJE_T] * 2, color=RED, lw=1.4, ls=(0, (7, 4)), zorder=2)
    ax.text(-0.95, Z_EJE_T, "Eje de referencia", color=RED, fontsize=14, ha="right", va="center")
    lab_idx = ALL if total else FACE
    labels(ax, pF, G.nF, lab_idx, "F")
    labels(ax, pL, nL, lab_idx, "L", off=0.55, fs=13)
    for txt, xy in (("ALZADO (F)", (G.XMAX / 2, -1.25)), ("PERFIL (L)", (X_EJE_L - D_REF - G.M / 2, -1.25)),
                    ("PLANTA", (G.XMAX / 2, Z_EJE_T + D_REF + G.M + 0.7))):
        ax.text(*xy, txt, color="#555", fontsize=13, ha="center", va="center")

    # --- LOS1 + auxiliar 1 ------------------------------------------------------------
    if stage >= 2:
        along = np.concatenate((pF(V) @ T1, p1(V) @ T1))
        a, b = H1 * N1 + (along.max() + 1.2) * T1, H1 * N1 + (along.min() - 1.6) * T1
        fold(ax, a, b, "LOS1", dx=(0.5, -0.6))
        idx_face = FRONT_FACE
        for i in idx_face:
            origin_line(ax, pF(V[i])[0], p1(V[i + 6] if i < 6 else V[i])[0], N1, hexF, TEAL)
        top_i = max(idx_face, key=lambda i: pF(V[i])[0] @ T1)
        bot_i = min(idx_face, key=lambda i: pF(V[i])[0] @ T1)
        for i, sd in ((top_i, -1), (bot_i, 1)):
            p = pF(V[i])[0]
            mark90(ax, p + (H1 - p @ N1) * N1, -N1, sd * T1)
        ax.annotate("", xy=(0.5 * (pF(V[G.iA]) + pF(V[G.iB]))[0] + 1.6 * N1),
                    xytext=(0.5 * (pF(V[G.iA]) + pF(V[G.iB]))[0]),
                    arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4, mutation_scale=14))
    if 3 <= stage <= 4:
        face_only(ax, p1)
        labels(ax, p1, LOS1, FACE, "1", center=p1(V[FACE]).mean(axis=0))
    if stage >= 5:
        for i in range(6):
            if i not in FRONT_FACE:
                origin_line(ax, pF(V[i])[0], p1(V[i + 6])[0], N1, hexF, BLUE)
        G.draw_view(ax, p1, LOS1, lw=2.2)
        face_only(ax, p1)
        labels(ax, p1, LOS1, ALL, "1")

    # --- LOS2 + auxiliar 2 ------------------------------------------------------------
    if stage >= 4:
        ys = np.concatenate((p1(V)[:, 1], p2(V)[:, 1]))
        fold(ax, (H2, ys.min() - 1.4), (H2, ys.max() + 1.4), "LOS2", dx=(0.5, 0.5))
        poly1 = hull(p1(V if total else V[FACE]))
        for i in FACE:
            origin_line(ax, p1(V[i])[0], p2(V[i])[0], N2, hull(p1(V[FACE])), TEAL, ext=1.2)
        ytop = max(FACE, key=lambda i: p1(V[i])[0, 1])
        p = p1(V[ytop])[0]
        mark90(ax, np.array([H2, p[1]]), -N2, -T2)
        face_only(ax, p2, fill=False, lw=3.0)
        ax.plot(*p2(V[FACE]).T, color=FILL, lw=9, alpha=0.7, zorder=1, solid_capstyle="round")
        if stage < 6:
            labels(ax, p2, LOS2, FACE, "2", center=p2(V[FACE]).mean(axis=0) - np.array([1.0, 0]))
    if stage >= 6:
        poly1 = hull(p1(V))
        for i in ALL:
            if i not in FACE:
                origin_line(ax, p1(V[i])[0], p2(V[i])[0], N2, poly1, BLUE, ext=1.2)
        G.draw_view(ax, p2, LOS2, lw=2.2)
        face_only(ax, p2, fill=False, lw=3.0)
        labels(ax, p2, LOS2, ALL, "2")

    # --- leyenda de colores (desde la etapa 5) -----------------------------------------
    if stage >= 5:
        fig.text(0.585, 0.085, "—— líneas de origen de la PARCIAL (cara ABCD)", color=TEAL, fontsize=14)
        fig.text(0.585, 0.052, "—— líneas añadidas para la TOTAL (E … L)", color=BLUE, fontsize=14)

    # --- isométrica (como en el tablero) ------------------------------------------------
    iso = fig.add_axes([0.80, 0.04, 0.19, 0.34], facecolor=BG)
    draw_iso(iso, total)

    # --- encuadre ---------------------------------------------------------------------
    pts = [pF(V), pL(V), pT(V)]
    if stage >= 2:
        pts.append(p1(V))
    if stage >= 4:
        pts.append(p2(V))
    A = np.vstack(pts + [p1(V), p2(V)])                 # mismo encuadre en todas las etapas
    ax.set_xlim(A[:, 0].min() - 2.4, A[:, 0].max() + 3.6)
    ax.set_ylim(A[:, 1].min() - 2.4, A[:, 1].max() + 1.6)
    ax.set_aspect("equal"); ax.axis("off")
    return fig


def main():
    names = {1: "tablero_paso_1_vistas", 2: "tablero_paso_2_LOS1", 3: "tablero_paso_3_auxiliar1_parcial",
             4: "tablero_paso_4_LAMINA_PARCIAL", 5: "tablero_paso_5_parcial_a_total", 6: "tablero_paso_6_LAMINA_TOTAL"}
    pdf = os.path.join(HERE, "Laminas_tablero_tuerca.pdf")
    with PdfPages(pdf) as out:
        for s in range(1, 7):
            fig = render(s)
            fig.savefig(os.path.join(HERE, names[s] + ".png"), dpi=150, facecolor=BG)
            out.savefig(fig, facecolor=BG)
            plt.close(fig)
    print("Comprobaciones OK:", ", ".join(f"{k} (residuo {v:.0e})" for k, v in CHECKS.items()))
    print("LOS1 =", np.round(LOS1, 6), " LOS2 =", np.round(LOS2, 6), " LOS1·LOS2 =", f"{LOS1 @ LOS2:.1e}")
    print("Archivos en:", HERE)


if __name__ == "__main__":
    main()
