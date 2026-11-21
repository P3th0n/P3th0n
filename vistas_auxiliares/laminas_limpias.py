#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LÁMINAS LIMPIAS (estilo tablero, solo geometría) + LÁMINAS DE DISTANCIAS
=======================================================================
Misma geometría y comprobaciones que laminas_tablero.py, dibujadas como en la pizarra:
  * negro = aristas (ocultas en trazo), verde = líneas de origen, rojo discontinuo = LOS / ejes,
    rótulos rojos con subíndice de la vista. Sin rellenos ni flechas decorativas.
  * Tuerca con su agujero roscado (Ø estimado en proyecciones_auxiliares_tuerca.py).
  * Los rótulos se colocan automáticamente donde no tocan ninguna línea ni otro rótulo.

REGLA DE LAS DOS VISTAS (la que explica el profesor):
  la distancia de un punto a la línea de pliegue en una vista nueva se mide en la vista que está
  DOS LUGARES ATRÁS en la cadena, desde su propia línea de pliegue:
     perfil ─ eje ─ ALZADO ─ LOS1 ─ AUX 1 ─ LOS2 ─ AUX 2
     AUX 1: distancia a LOS1  = distancia en el PERFIL desde el eje de referencia
     AUX 2: distancia a LOS2  = distancia en el ALZADO desde LOS1
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import laminas_tablero as T          # geometría, vistas, comprobaciones y estilo
G = T.G
V = G.V
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "limpias")
os.makedirs(OUT, exist_ok=True)
BG, INK, RED, TEAL, BLUE = T.BG, T.INK, T.RED, T.TEAL, T.BLUE
DIM = "#6a35b8"                       # color de las cotas en las láminas de distancias
ALL, FACE = T.ALL, T.FACE


# ----------------------------------------------------------------------------------- utilidades
def view(ax, place, v):
    G.draw_view(ax, place, v, lw=2.2, hidden=True, cyl=True)


def groups(place, v, idx, suf):
    """Agrupa puntos que caen en el mismo sitio: 'A_F D_F'. Devuelve [(punto, texto)]."""
    P = V[idx]
    Q = place(P)
    used, out = [False] * len(idx), []
    for i in range(len(idx)):
        if used[i]:
            continue
        g = [i]; used[i] = True
        for j in range(i + 1, len(idx)):
            if not used[j] and np.linalg.norm(Q[i] - Q[j]) < 1e-6:
                g.append(j); used[j] = True
        g.sort(key=lambda t: -(P[t] @ v))
        out.append((Q[g[0]], "$" + r"\,".join(f"{T.LET[idx[t]]}_{{{suf}}}" for t in g) + "$"))
    return out


def fold_line(ax, a, b, name, reqs):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=RED, lw=1.4, ls=(0, (7, 4)), zorder=2)
    reqs.append((np.asarray(b, float), name, 16, "fold"))


def seg_dist(P, A, B):
    """Distancia de cada punto P (n,2) a cada segmento AB (m,2) -> (n,m)."""
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    C = A[None] + t[..., None] * AB[None]
    return np.linalg.norm(P[:, None, :] - C, axis=2)


def place_labels(fig, ax, reqs):
    """Coloca cada rótulo en la posición (16 direcciones × 4 radios) con más holgura respecto
    de todas las líneas dibujadas y sin tocar otros textos."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    segs = []
    for ln in ax.lines:
        xy = np.column_stack((ln.get_xdata(), ln.get_ydata())).astype(float)
        segs += [(a, b) for a, b in zip(xy[:-1], xy[1:])]
    A = np.array([s[0] for s in segs]); B = np.array([s[1] for s in segs])
    boxes = []
    for t in ax.texts:
        bb = t.get_window_extent(rend).transformed(inv)
        boxes.append((bb.x0, bb.y0, bb.x1, bb.y1))
    for q, txt, fs, kind in reqs:
        t = ax.text(q[0], q[1], txt, fontsize=fs, color=RED, ha="center", va="center", zorder=8)
        bb = t.get_window_extent(rend).transformed(inv)
        w, h = bb.width, bb.height
        best, best_score = None, None
        for rad in (0.35, 0.6, 0.9, 1.3):
            for ang in np.deg2rad(np.arange(0, 360, 22.5)):
                c = q + np.array([np.cos(ang) * (rad + w / 2), np.sin(ang) * (rad + h / 2)])
                box = (c[0] - w / 2, c[1] - h / 2, c[0] + w / 2, c[1] + h / 2)
                gx, gy = np.meshgrid(np.linspace(box[0], box[2], 6), np.linspace(box[1], box[3], 3))
                clr = seg_dist(np.column_stack((gx.ravel(), gy.ravel())), A, B).min()
                ov = any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in boxes)
                score = (not ov, min(clr, 0.18), -rad, clr)
                if best_score is None or score > best_score:
                    best, best_score = (c, box), score
        t.set_position(best[0])
        boxes.append(best[1])


def dim_line(ax, p, q, text, reqs_dims, off=0.0):
    """Cota entre p y q (desplazada `off` en perpendicular), en morado."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    t = (q - p) / np.linalg.norm(q - p)
    n = np.array([-t[1], t[0]])
    p2, q2 = p + off * n, q + off * n
    ax.plot([p2[0], q2[0]], [p2[1], q2[1]], color=DIM, lw=1.3, zorder=6)
    ax.annotate("", xy=q2, xytext=p2, arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=1.3, mutation_scale=11,
                                                      shrinkA=0, shrinkB=0), zorder=6)
    if abs(off) > 1e-9:
        for a, a2 in ((p, p2), (q, q2)):
            ax.plot([a[0], a2[0] + 0.15 * np.sign(off) * n[0]], [a[1], a2[1] + 0.15 * np.sign(off) * n[1]],
                    color=DIM, lw=0.8, zorder=6)
    mid = (p2 + q2) / 2 + 0.38 * n * (np.sign(off) if off else 1)
    ang = np.degrees(np.arctan2(t[1], t[0]))
    ang = ang + 180 if ang > 90 or ang < -90 else ang
    ax.text(*mid, text, color=DIM, fontsize=15, rotation=ang, ha="center", va="center", zorder=7,
            bbox=dict(fc=BG, ec="none", pad=0.4))


def dim_ext(ax, foot, end, pts_from, text, dims):
    """Cota foot→end con líneas de extensión desde los puntos reales hasta la línea de cota."""
    for a, b in pts_from:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=DIM, lw=0.8, zorder=6)
    dim_line(ax, foot, end, text, dims)


def new_fig(title, sub):
    fig = plt.figure(figsize=(19, 10), facecolor=BG)
    ax = fig.add_axes([0.0, 0.035, 1.0, 0.85], facecolor=BG)
    fig.text(0.02, 0.955, title, fontsize=30, color=INK, ha="left", va="center")
    fig.text(0.02, 0.905, sub, fontsize=15, color="#333", ha="left", va="center")
    fig.text(0.02, 0.012, f"Tuerca hexagonal: s = {G.S:.2f} · e = {G.E:.2f} · m = {G.M:.2f} cm · Ø agujero ≈ {G.D_BORE:.1f} cm (estimado) · tercer diedro · escala 1:1 · "
             f"eje de referencia a {T.D_REF:g} cm de la pieza · LOS1 a {T.AUX_GAP1:g} cm del alzado · LOS2 a {T.AUX_GAP2:g} cm de la auxiliar 1",
             fontsize=11, color="#555")
    return fig, ax


def iso_inset(fig, rect, idx):
    ax = fig.add_axes(rect, facecolor=BG)
    v = G.V_ISO
    u, w = G.iso_basis(v)
    place = lambda P: G.proj(P, u, w)
    lo, hi = V.min(axis=0), V.max(axis=0)
    box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    for a in range(8):
        for b in range(a + 1, 8):
            if np.sum(np.abs(box[a] - box[b]) > 1e-9) == 1:
                q = place(box[[a, b]]); ax.plot(q[:, 0], q[:, 1], color=TEAL, lw=0.7)
    G.draw_view(ax, place, v, lw=1.8, cyl=True)
    c = place(V).mean(axis=0)
    for i in idx:
        p = place(V[i])[0]
        d = (p - c) / np.linalg.norm(p - c)
        ax.text(*(p + 0.6 * d), T.LET[i], color=RED, fontsize=14, ha="center", va="center")
    P = place(V)
    ax.set_xlim(P[:, 0].min() - 1.2, P[:, 0].max() + 1.2); ax.set_ylim(P[:, 1].min() - 1.2, P[:, 1].max() + 1.2)
    ax.set_aspect("equal"); ax.axis("off")


def frame(ax, arrays, pad=(2.6, 3.0, 2.2, 1.8)):
    A = np.vstack(arrays)
    ax.set_xlim(A[:, 0].min() - pad[0], A[:, 0].max() + pad[1])
    ax.set_ylim(A[:, 1].min() - pad[2], A[:, 1].max() + pad[3])
    ax.set_aspect("equal"); ax.axis("off")


hexF = T.pF(V[:6])


def base_views(ax, reqs, idx_lab, with_profile=True):
    """Perfil + eje de referencia + alzado, con sus líneas de origen horizontales."""
    view(ax, T.pF, G.nF)
    arrs = [T.pF(V)]
    if with_profile:
        view(ax, T.pL, T.nL)
        arrs.append(T.pL(V))
        for i in range(6):
            T.origin_line(ax, T.pF(V[i])[0], T.pL(V[i + 6])[0], np.array([-1.0, 0]), hexF, TEAL, ext=0.6)
        fold_line(ax, (T.X_EJE_L, G.ZMAX + 0.8), (T.X_EJE_L, -1.2), "Eje de referencia", reqs)
        reqs += [(q, t, 15, "pt") for q, t in groups(T.pL, T.nL, idx_lab, "L")]
    reqs += [(q, t, 15, "pt") for q, t in groups(T.pF, G.nF, idx_lab, "F")]
    return arrs


def los1_and_aux1(ax, reqs, idx_pts, total):
    """LOS1 (paralela a la cara de canto), líneas de origen ⊥ y auxiliar 1 (parcial o total)."""
    fr = [i for i in range(6) if (i in T.FRONT_FACE or total)]
    along = np.concatenate([T.pF(V[fr]) @ T.T1, T.p1(V[fr]) @ T.T1])
    a = T.H1 * T.N1 + (along.max() + 0.9) * T.T1
    b = T.H1 * T.N1 + (along.min() - 0.9) * T.T1
    fold_line(ax, a, b, "LOS1", reqs)
    for i in fr:
        T.origin_line(ax, T.pF(V[i])[0], T.p1(V[i + 6])[0], T.N1, hexF, TEAL)
    for i, sd in ((G.iA, -1), (G.iB, 1)):
        p = T.pF(V[i])[0]
        T.mark90(ax, p + (T.H1 - p @ T.N1) * T.N1, -T.N1, sd * T.T1)
    if total:
        view(ax, T.p1, T.LOS1)
    else:
        q = T.p1(V[FACE]); ax.plot(*np.vstack((q, q[:1])).T, color=INK, lw=2.3, zorder=5)
    reqs += [(q, t, 15, "pt") for q, t in groups(T.p1, T.LOS1, idx_pts, "1")]
    return [T.p1(V)]


def los2_and_aux2(ax, reqs, idx_pts, total):
    idx = ALL if total else FACE
    ys = np.concatenate((T.p1(V[idx])[:, 1], T.p2(V[idx])[:, 1]))
    fold_line(ax, (T.H2, ys.min() - 1.0), (T.H2, ys.max() + 1.0), "LOS2", reqs)
    poly = T.hull(T.p1(V[idx]))
    for i in idx:
        T.origin_line(ax, T.p1(V[i])[0], T.p2(V[i])[0], T.N2, poly, TEAL, ext=1.0)
    top = max(idx, key=lambda i: T.p1(V[i])[0, 1])
    T.mark90(ax, np.array([T.H2, T.p1(V[top])[0, 1]]), -T.N2, -T.T2)
    if total:
        view(ax, T.p2, T.LOS2)
    else:
        ax.plot(*T.p2(V[FACE]).T, color=INK, lw=2.6, zorder=5)
    reqs += [(q, t, 15, "pt") for q, t in groups(T.p2, T.LOS2, idx_pts, "2")]
    return [T.p2(V)]


# ----------------------------------------------------------------------------------- láminas
def lamina(total):
    title = "Análisis de vistas o proyecciones auxiliares totales" if total else "Proyecciones auxiliares parciales  (Escala 1:1)"
    sub = ("Toda la pieza se proyecta: alzado → auxiliar 1 (LOS1) → auxiliar 2 (LOS2)." if total else
           "Solo la cara inclinada ABCD: verdadera magnitud en la auxiliar 1 y de canto en la auxiliar 2.")
    fig, ax = new_fig(title, sub)
    reqs = []
    idx = ALL if total else FACE
    arrs = base_views(ax, reqs, idx)
    arrs += los1_and_aux1(ax, reqs, idx, total)
    arrs += los2_and_aux2(ax, reqs, idx, total)
    for txt, xy in (("ALZADO (F)", (G.XMAX / 2, -1.5)), ("PERFIL (L)", (T.X_EJE_L - T.D_REF - G.M / 2, -1.5))):
        ax.text(*xy, txt, color="#555", fontsize=14, ha="center", va="center")
    frame(ax, arrs + [T.p1(V), T.p2(V)])
    place_labels(fig, ax, reqs)
    iso_inset(fig, [0.80 if not total else 0.62, 0.02, 0.18 if not total else 0.16, 0.30 if not total else 0.27], idx)
    return fig


def lamina_parcial_a_total():
    fig, ax = new_fig("De la proyección parcial a la total",
                      "Verde: líneas de origen de la cara ABCD (parcial). Azul: las mismas reglas aplicadas a los vértices restantes E … L (total).")
    reqs = []
    arrs = base_views(ax, reqs, ALL)
    fr_extra = [i for i in range(6) if i not in T.FRONT_FACE]
    arrs += los1_and_aux1(ax, reqs, ALL, total=True)
    for i in fr_extra:                                      # repintar en azul las añadidas
        T.origin_line(ax, T.pF(V[i])[0], T.p1(V[i + 6])[0], T.N1, hexF, BLUE)
    arrs += los2_and_aux2(ax, reqs, ALL, total=True)
    poly = T.hull(T.p1(V))
    for i in ALL:
        if i not in FACE:
            T.origin_line(ax, T.p1(V[i])[0], T.p2(V[i])[0], T.N2, poly, BLUE, ext=1.0)
    frame(ax, arrs + [T.p1(V), T.p2(V)])
    place_labels(fig, ax, reqs)
    iso_inset(fig, [0.62, 0.02, 0.16, 0.27], ALL)
    return fig


def lamina_dist1():
    fig, ax = new_fig("Distancias de la auxiliar 1  (regla de las dos vistas)",
                      "Auxiliar 1 ← alzado ← PERFIL: la distancia de cada punto a LOS1 se mide en el perfil desde el eje de referencia.")
    reqs, dims = [], []
    arrs = base_views(ax, reqs, ALL)
    arrs += los1_and_aux1(ax, reqs, ALL, total=True)
    # cotas en el PERFIL: eje → cara delantera (y=0) y eje → cara trasera (y=m), sobre la vista
    xe = T.X_EJE_L
    x_front, x_back = T.pL(V[0])[0, 0], T.pL(V[6])[0, 0]
    y1, y2 = G.ZMAX + 1.0, G.ZMAX + 1.9
    for (x, y, d) in ((x_front, y1, T.D_REF), (x_back, y2, T.D_REF + G.M)):
        ax.plot([x, x], [G.ZMAX, y + 0.2], color=DIM, lw=0.8); ax.plot([xe, xe], [G.ZMAX + 0.8, y + 0.2], color=DIM, lw=0.8)
        dim_line(ax, (xe, y), (x, y), f"{d:.2f}".replace(".", ","), dims)
    # mismas cotas en la AUXILIAR 1, sobre la línea de origen de A y D (desde LOS1)
    iE = (G.FACE_K + 2) % 6
    amax = T.p1(V) @ T.T1
    for k, i in enumerate((iE, iE + 6)):                       # E (delantero) e I (trasero)
        q = T.p1(V[i])[0]
        a = amax.max() + 0.8 + 0.8 * k
        foot = a * T.T1 + T.H1 * T.N1
        end = a * T.T1 + (q @ T.N1) * T.N1
        dim_ext(ax, foot, end, [(q, end + 0.2 * T.T1)], f"{(q @ T.N1) - T.H1:.2f}".replace(".", ","), dims)
    e0, e1 = T.H1 * T.N1 + (amax.max() + 0.5) * T.T1, T.H1 * T.N1 + (amax.max() + 2.2) * T.T1   # prolongar LOS1
    ax.plot([e0[0], e1[0]], [e0[1], e1[1]], color=RED, lw=1.4, ls=(0, (7, 4)), zorder=2)
    fig.text(0.50, 0.075, "Delanteros (A, B, E, F, G, H) → 1 cm desde LOS1      ·      Traseros (C, D, I, J, K, L) → 4 cm desde LOS1",
             color=DIM, fontsize=15, ha="left", va="center")
    frame(ax, arrs + [T.p1(V)], pad=(2.6, 3.4, 2.4, 3.2))
    place_labels(fig, ax, reqs)
    return fig


def lamina_dist2():
    fig, ax = new_fig("Distancias de la auxiliar 2  (regla de las dos vistas)",
                      "Auxiliar 2 ← auxiliar 1 ← ALZADO: la distancia de cada punto a LOS2 se mide en el alzado desde LOS1.")
    reqs, dims = [], []
    arrs = base_views(ax, reqs, ALL, with_profile=False)
    arrs += los1_and_aux1(ax, reqs, ALL, total=True)
    arrs += los2_and_aux2(ax, reqs, ALL, total=True)
    # cotas en el ALZADO: desde LOS1 hasta A_F, E_F y F_F (medidas a 90° de LOS1)
    iE, iF = (G.FACE_K + 2) % 6, (G.FACE_K + 3) % 6
    a0 = (T.pF(V[:6]) @ T.T1).max()
    ytop = T.p2(V)[:, 1].max()
    for k, (i, j) in enumerate(((G.iA, G.iD), (iE, iE + 6), (iF, iF + 6))):
        # ALZADO: distancia desde LOS1 (medida a 90° de LOS1), cota por fuera, arriba a la izquierda
        p = T.pF(V[i])[0]
        a = a0 + 0.9 + 0.8 * k
        foot = a * T.T1 + T.H1 * T.N1
        end = a * T.T1 + (p @ T.N1) * T.N1
        txt = f"{T.H1 - p @ T.N1:.2f}".replace(".", ",")
        dim_ext(ax, foot, end, [(p, end + 0.2 * T.T1)], txt, dims)
        # AUXILIAR 2: la misma distancia desde LOS2, cota por encima de la vista
        q = max((T.p2(V[i])[0], T.p2(V[j])[0]), key=lambda r: r[1])
        y = ytop + 0.8 + 0.8 * k
        dim_ext(ax, (T.H2, y), (q[0], y), [(q, (q[0], y + 0.2))], f"{q[0] - T.H2:.2f}".replace(".", ","), dims)
    los1_ext = a0 + 0.9 + 0.8 * 2 + 0.6
    a, b = T.H1 * T.N1 + los1_ext * T.T1, T.H1 * T.N1 + (a0 - 0.5) * T.T1
    ax.plot([a[0], b[0]], [a[1], b[1]], color=RED, lw=1.4, ls=(0, (7, 4)), zorder=2)
    ax.plot([T.H2, T.H2], [ytop, ytop + 0.8 * 3 + 0.4], color=RED, lw=1.4, ls=(0, (7, 4)), zorder=2)
    frame(ax, arrs + [T.p1(V), T.p2(V)], pad=(3.2, 3.4, 2.0, 3.4))
    place_labels(fig, ax, reqs)
    return fig


def lamina_circunferencia():
    """Método de los 12 puntos: cada punto del borde del agujero se proyecta como un vértice más."""
    fig, ax = new_fig("Cómo se proyecta la circunferencia del agujero  (12 puntos)",
                      "Se divide el borde en 12 puntos (cada 30°) y cada uno se proyecta con la regla de las dos vistas. Se muestra el borde delantero; el trasero es igual a 4 cm de LOS1.")
    reqs = []
    view(ax, T.pF, G.nF); view(ax, T.p1, T.LOS1); view(ax, T.p2, T.LOS2)
    c = G.CILS[0]
    phis = np.deg2rad(np.arange(0, 360, 30))
    P = np.array([[G.cx + c.r * np.cos(f), 0.0, G.cz + c.r * np.sin(f)] for f in phis])     # borde delantero (y = 0)
    qF, q1, q2 = T.pF(P), T.p1(P), T.p2(P)
    along = np.concatenate([T.pF(V) @ T.T1, T.p1(V) @ T.T1])
    fold_line(ax, T.H1 * T.N1 + (along.max() + 0.9) * T.T1, T.H1 * T.N1 + (along.min() - 0.9) * T.T1, "LOS1", reqs)
    ys = np.concatenate((T.p1(V)[:, 1], T.p2(V)[:, 1]))
    fold_line(ax, (T.H2, ys.min() - 1.0), (T.H2, ys.max() + 1.0), "LOS2", reqs)
    for k in range(12):
        ax.plot([qF[k, 0], q1[k, 0] + 0.8 * T.N1[0]], [qF[k, 1], q1[k, 1] + 0.8 * T.N1[1]], color=TEAL, lw=0.7, zorder=1)
        ax.plot([q1[k, 0], q2[k, 0] + 0.8], [q1[k, 1], q2[k, 1]], color=TEAL, lw=0.7, zorder=1)
    for q in (qF, q1, q2):
        ax.plot(q[:, 0], q[:, 1], "o", color=RED, ms=4.5, zorder=7, ls="none")
    # ejes de la elipse en la auxiliar 2 (borde delantero)
    rim = T.p2(c.rim(0)[:-1]); C = rim.mean(axis=0)
    cF = T.pF(np.array([G.cx, 0.0, G.cz]))[0]
    for k in range(12):                       # número justo afuera de su punto, en dirección radial
        for q, cen in ((qF[k], cF), (q2[k], C)):
            u = (q - cen) / np.linalg.norm(q - cen)
            ax.text(*(q + 0.42 * u), str(k + 1), color=RED, fontsize=13, ha="center", va="center", zorder=8,
                    bbox=dict(fc=BG, ec="none", pad=0.15))
    a_semi, b_semi = np.ptp(rim[:, 0]) / 2, np.ptp(rim[:, 1]) / 2
    ax.plot([C[0] - a_semi, C[0] + a_semi], [C[1], C[1]], color=DIM, lw=1.0, ls=(0, (2, 2)), zorder=6)
    ax.plot([C[0], C[0]], [C[1] - b_semi, C[1] + b_semi], color=DIM, lw=1.0, ls=(0, (2, 2)), zorder=6)
    d = T.H1 - qF @ T.N1
    fig.text(0.02, 0.135, "Distancia de cada punto a LOS1 en el alzado  =  distancia a LOS2 en la auxiliar 2  (cm):", fontsize=15, color=DIM)
    fig.text(0.02, 0.10, "   ".join(f"{k + 1}: {v:.2f}".replace(".", ",") for k, v in enumerate(d)), fontsize=15, color=DIM)
    fig.text(0.02, 0.065, f"Auxiliar 1: el borde se ve de canto (segmento de {2 * c.r:.2f} cm a 1 cm de LOS1).   "
             f"Auxiliar 2: elipse de eje mayor {2 * a_semi:.2f} cm (diámetro real) y eje menor {2 * b_semi:.2f} cm = Ø · |cos(LOS2, eje)|".replace(".", ","),
             fontsize=15, color=DIM)
    frame(ax, [T.pF(V), T.p1(V), T.p2(V)], pad=(2.4, 3.0, 3.2, 2.6))
    place_labels(fig, ax, reqs)
    return fig


def main():
    pages = [("1_lamina_parcial", lambda: lamina(False)), ("2_lamina_total", lambda: lamina(True)),
             ("3_parcial_a_total", lamina_parcial_a_total), ("4_distancias_auxiliar1", lamina_dist1),
             ("5_distancias_auxiliar2", lamina_dist2), ("6_circunferencia", lamina_circunferencia)]
    with PdfPages(os.path.join(OUT, "Laminas_limpias_tuerca.pdf")) as pdf:
        for name, fn in pages:
            fig = fn()
            fig.savefig(os.path.join(OUT, name + ".png"), dpi=150, facecolor=BG)
            pdf.savefig(fig, facecolor=BG)
            plt.close(fig)
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
