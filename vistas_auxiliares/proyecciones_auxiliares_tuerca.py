#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECCIONES AUXILIARES (PARCIAL Y TOTAL) DE UNA TUERCA HEXAGONAL
==================================================================
Todo se calcula con álgebra lineal (numpy): productos punto, productos cruz y
proyecciones ortogonales. Nada se dibuja "a ojo": cada línea sale de coordenadas
3D de los vértices.

Convenciones (método americano / tercer diedro, el de las pizarras de clase):
  X = derecha, Y = profundidad (0 = cara frontal de la pieza, crece hacia atrás), Z = altura.
  Vista = base ortonormal (u, w) con  u x w = n  (n apunta hacia el observador).
  Proyección de un punto P en la vista:  (P·u , P·w).

Parámetros de la pieza (cm).  S y M vienen de la hoja 2 (cotas 7 y 3).
  D_BORE es una ESTIMACIÓN a partir de la proporción de las elipses del isométrico.
  D_EXTRA = Ø del agujero de la cara superior, ESTIMADO de tu isométrico (≈1,4–1,5 cm). Atraviesa la pared
  hasta el agujero roscado; su fondo es la curva de intersección de los dos cilindros (cálculo exacto).
La pieza se modela como prisma hexagonal SIN chaflán (el chaflán son conos: curvas
hiperbólicas que no cambian el procedimiento de la vista auxiliar).

Salida: PDF + un PNG por paso, en la carpeta de este script.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ----------------------------------------------------------------------------
# 0. PARÁMETROS
# ----------------------------------------------------------------------------
S = 7.0          # distancia entre caras planas (cm)
M = 3.0          # espesor (cm)
D_BORE = 3.8     # Ø agujero roscado (cm)  -> ESTIMADO, confirmar con la pieza
D_EXTRA = 1.5    # Ø agujero de la cara superior (cm) -> ESTIMADO; None = no se dibuja
FACE_K = 0       # cara inclinada a analizar: normal a 30° + 60°·k (k = 0, 2, 3, 5 son inclinadas)
GAP = 2.0        # separación entre vistas principales en la hoja (cm)
AUX_GAP = 4.5    # separación entre el alzado y la línea de pliegue L.T.1 (cm)
EPS = 1e-9
OUT = os.path.dirname(os.path.abspath(__file__))

C_VIS, C_HID = "k", "0.45"
C_FOLD, C_PROJ, C_HI = "#c0392b", "#16897a", "#f2a900"

X = np.array([1.0, 0, 0]); Y = np.array([0, 1.0, 0]); Z = np.array([0, 0, 1.0])


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# ----------------------------------------------------------------------------
# 1. SÓLIDO: prisma hexagonal (vértices, caras, normales por producto cruz)
# ----------------------------------------------------------------------------
E = 7.0                              # ancho entre vértices: caja de 7 × 7 × 3 (medidas del isométrico)
Q1 = E / 4.0                         # método de la caja: vértices de arriba y abajo a 1/4 del ancho
R = E / 2.0                          # semiancho
cx, cz = E / 2.0, S / 2.0            # eje de la tuerca: recta paralela a Y por (cx, cz)
LADO_SUP = E - 2 * Q1                # lados superior e inferior (3,5 cm)
LADO_INC = float(np.hypot(Q1, S / 2))   # lados inclinados (3,91 cm): hexágono NO regular
Vf = np.array([[E, 0.0, cz], [E - Q1, 0.0, S], [Q1, 0.0, S],
               [0.0, 0.0, cz], [Q1, 0.0, 0.0], [E - Q1, 0.0, 0.0]])          # cara frontal (y=0)
Vb = Vf + np.array([0.0, M, 0.0])                                               # cara posterior (y=M)
V = np.vstack([Vf, Vb])             # 12 vértices: 0..5 delante, 6..11 detrás
ZMAX, XMAX = V[:, 2].max(), V[:, 0].max()

faces = [list(range(6)), list(range(6, 12))[::-1]]        # 0: frontal, 1: posterior
for k in range(6):
    k2 = (k + 1) % 6
    faces.append([k, k2, 6 + k2, 6 + k])                  # 2+k: caras laterales


def face_normal(f):
    """Normal unitaria saliente: n = (P1-P0) x (P2-P0), orientada con el centroide del sólido."""
    p = V[f]
    n = unit(np.cross(p[1] - p[0], p[2] - p[0]))
    return n if n @ (p.mean(axis=0) - V.mean(axis=0)) > 0 else -n


normals = [face_normal(f) for f in faces]

edges = {}
for fi, f in enumerate(faces):
    for i in range(len(f)):
        key = tuple(sorted((f[i], f[(i + 1) % len(f)])))
        edges.setdefault(key, []).append(fi)


def visible_edges(v):
    """Sólido convexo: una arista es visible si alguna de sus 2 caras mira al observador (n·v > 0)."""
    vis = [e for e, fs in edges.items() if any(normals[f] @ v > EPS for f in fs)]
    hid = [e for e, fs in edges.items() if not any(normals[f] @ v > EPS for f in fs)]
    return vis, hid


# Cilindros (agujeros): silueta = generatrices a ±r en la dirección  (eje x v);
# bordes circulares = circunferencias 3D proyectadas (elipses).
class Cil:
    def __init__(self, p0, a, L, r, n0=None, n1=None):
        self.p0, self.a, self.L, self.r = np.asarray(p0, float), unit(a), L, r
        h = X if abs(self.a[0]) < 0.9 else Y
        self.e1 = unit(np.cross(self.a, h))
        self.e2 = np.cross(self.a, self.e1)
        self.n0, self.n1 = n0, n1      # normal de la cara donde nace cada borde (None = extremo interno)

    def rim(self, t):
        th = np.linspace(0, 2 * np.pi, 181)
        c = self.p0 + t * self.L * self.a
        return c + self.r * (np.outer(np.cos(th), self.e1) + np.outer(np.sin(th), self.e2))

    def silhouettes(self, v):
        c = np.cross(self.a, v)
        if np.linalg.norm(c) < 1e-9:          # se mira a lo largo del eje: la silueta es la circunferencia
            return []
        c = unit(c)
        return [(self.p0 + s * self.r * c, self.p0 + s * self.r * c + self.L * self.a) for s in (1, -1)]


CILS = [Cil([cx, 0, cz], Y, M, D_BORE / 2, -Y, Y)]


class AgujeroSuperior:
    """Agujero vertical desde la cara superior (z = S) hasta el agujero roscado.
    Su fondo es la intersección de los dos cilindros:  z = cz + sqrt(r_rosca² − (x − cx)²)."""

    def __init__(self, xc, yc, r):
        self.xc, self.yc, self.r = xc, yc, r

    def zb(self, x):
        return cz + np.sqrt((D_BORE / 2) ** 2 - (np.asarray(x) - cx) ** 2)

    def _ring(self, n=181):
        th = np.linspace(0, 2 * np.pi, n)
        return self.xc + self.r * np.cos(th), self.yc + self.r * np.sin(th)

    def rim(self):                                   # borde en la cara superior
        x, y = self._ring()
        return np.column_stack((x, y, np.full_like(x, S)))

    def bottom(self):                                # curva de intersección con el agujero roscado
        x, y = self._ring()
        return np.column_stack((x, y, self.zb(x)))

    def silhouettes(self, v):
        c = np.cross(Z, v)                           # generatrices de contorno: a ±r en la dirección Z × v
        if np.linalg.norm(c) < 1e-9:
            return []
        c = unit(c)
        out = []
        for s_ in (1, -1):
            x, y = self.xc + s_ * self.r * c[0], self.yc + s_ * self.r * c[1]
            out.append((np.array([x, y, S]), np.array([x, y, float(self.zb(x))])))
        return out


EXTRA = AgujeroSuperior(cx, M / 2, D_EXTRA / 2) if D_EXTRA else None
assert EXTRA is None or EXTRA.r < D_BORE / 2

# ----------------------------------------------------------------------------
# 2. VISTAS: base (u, w) con u x w = n  (n hacia el observador)
# ----------------------------------------------------------------------------
def basis_from_normal(n, up):
    n = unit(n)
    w = unit(up - (up @ n) * n)       # "arriba" de la imagen: componente de `up` perpendicular a n
    u = np.cross(w, n)                # u x w = n  (triple producto vectorial)
    return u, w


def proj(P, u, w):
    P = np.atleast_2d(P)
    return np.column_stack((P @ u, P @ w))


nF = -Y; uF, wF = basis_from_normal(nF, Z)      # alzado:  observador en y<0
nT = Z;  uT, wT = basis_from_normal(nT, Y)      # planta:  observador en z>0
nR = X;  uR, wR = basis_from_normal(nR, Z)      # perfil derecho
for n_, u_, w_ in ((nF, uF, wF), (nT, uT, wT), (nR, uR, wR)):
    assert np.allclose(np.cross(u_, w_), n_), "base no right-handed"


def place_front(P): return proj(P, uF, wF)
def place_top(P):   return proj(P, uT, wT) + np.array([0.0, ZMAX + GAP])     # planta ENCIMA del alzado
def place_right(P): return proj(P, uR, wR) + np.array([XMAX + GAP, 0.0])     # perfil a la DERECHA


# ----------------------------------------------------------------------------
# 3. VISTA AUXILIAR 1 (adyacente al alzado)
#    LOS1 = normal de la cara inclinada (⊥ a la cara). L.T. (pliegue) ⊥ LOS1.
# ----------------------------------------------------------------------------
class Aux:
    def __init__(self, n_adj, u_adj, w_adj, los, gap):
        self.los = unit(los)
        assert abs(self.los @ n_adj) < 1e-12, "LOS1 debe estar en el plano de la vista adyacente"
        self.n_adj = n_adj
        self.T3 = unit(np.cross(n_adj, self.los))                   # dirección de la línea de pliegue
        assert np.allclose(np.cross(self.T3, n_adj), self.los)      # (T3, n_adj) es base de la vista auxiliar
        self.T2 = np.array([self.T3 @ u_adj, self.T3 @ w_adj])      # T3 expresado en la hoja
        self.N2 = np.array([self.los @ u_adj, self.los @ w_adj])    # dirección de las proyectantes en la hoja
        pts = np.column_stack((V @ u_adj, V @ w_adj))
        self.hF = (pts @ self.N2).max() + gap                       # posición del pliegue sobre N2
        self.depth0 = (-(V @ n_adj)).min()

    def depth(self, P):   # distancia al eje de referencia (cara frontal, y=0)
        return -(np.atleast_2d(P) @ self.n_adj) - self.depth0

    def place(self, P):   # posición en la hoja (vista auxiliar "girada", como en la pizarra)
        P = np.atleast_2d(P)
        return np.outer(P @ self.T3, self.T2) + np.outer(self.hF + self.depth(P), self.N2)

    def image(self, P):   # imagen "derecha" vista por el observador a lo largo de LOS1
        P = np.atleast_2d(P)
        return np.column_stack((P @ self.T3, P @ self.n_adj))

    def fold(self, ext=1.0):
        a = V @ self.T3
        c = self.hF * self.N2
        return c + (a.min() - ext) * self.T2, c + (a.max() + ext) * self.T2


k = FACE_K
iA, iB, iC, iD = (k + 1) % 6, k, 6 + k, 6 + (k + 1) % 6          # vértices de la cara: A,B (delante), C,D (detrás)
FACE = [iA, iB, iC, iD]
n_face = normals[2 + k]
aux = Aux(nF, uF, wF, n_face, AUX_GAP)
LBL = {iA: "A", iB: "B", iC: "C", iD: "D"}


# ----------------------------------------------------------------------------
# 4. VERIFICACIONES NUMÉRICAS (si algo no cuadra, el script se detiene)
# ----------------------------------------------------------------------------
def area3d(P):
    c = np.zeros(3)
    for i in range(len(P)):
        c += np.cross(P[i], P[(i + 1) % len(P)])
    return 0.5 * np.linalg.norm(c)


def area2d(Q):
    x, y = Q[:, 0], Q[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def verify():
    r = {}
    PF = V[FACE]
    r["AB"], r["AD"] = PF[1] - PF[0], PF[3] - PF[0]
    r["n_cross"] = unit(np.cross(r["AB"], r["AD"]))
    r["n_cross"] = r["n_cross"] if r["n_cross"] @ n_face > 0 else -r["n_cross"]
    assert np.allclose(r["n_cross"], n_face)
    r["n_dot_Y"] = n_face @ Y
    assert abs(r["n_dot_Y"]) < 1e-12                     # la cara es ⊥ al plano frontal -> se ve de canto
    ab2 = place_front(PF)
    d = ab2[1] - ab2[0]
    ang = np.degrees(np.arctan2(d[1], d[0])) % 180
    r["ang_edge"] = min(ang, 180 - ang)        # ángulo agudo con la horizontal
    r["T3_dot_n"] = aux.T3 @ n_face
    assert abs(r["T3_dot_n"]) < 1e-12                    # L.T. ⊥ LOS1
    # proyectantes ⊥ L.T.: (q - p_F)·T2 = 0 para los 12 vértices
    pf, q = place_front(V), aux.place(V)
    r["perp"] = np.abs(((q - pf) @ aux.T2)).max()
    assert r["perp"] < 1e-12
    # (q - p_F) paralelo a N2
    dq = q - pf
    r["par"] = np.abs(dq[:, 0] * aux.N2[1] - dq[:, 1] * aux.N2[0]).max()   # producto cruz 2D = 0
    assert r["par"] < 1e-12
    # verdadera magnitud
    img = aux.image(PF)
    r["a3"], r["a_aux"] = np.linalg.norm(PF[1] - PF[0]), np.linalg.norm(img[1] - img[0])
    r["m3"], r["m_aux"] = np.linalg.norm(PF[3] - PF[0]), np.linalg.norm(img[3] - img[0])
    r["A3"], r["A_aux"] = area3d(PF), area2d(img)
    assert abs(r["A_aux"] - r["A3"]) < 1e-9 and abs(r["a_aux"] - r["a3"]) < 1e-9
    # la imagen "girada" (hoja) es una rotación rígida de la imagen derecha: conserva distancias
    ph = aux.place(PF)
    assert abs(area2d(ph) - r["A3"]) < 1e-9
    r["A_top"] = area2d(proj(PF, uT, wT)); r["A_front"] = area2d(proj(PF, uF, wF)); r["A_right"] = area2d(proj(PF, uR, wR))
    assert abs(r["A_top"] - r["A3"] * abs(n_face @ nT)) < 1e-9      # A_proy = A · |n·v|
    return r


CHK = verify()

# ----------------------------------------------------------------------------
# 5. DIBUJO
# ----------------------------------------------------------------------------
def draw_view(ax, place, v, lw=1.8, hidden=True, cyl=True):
    vis, hid = visible_edges(v)
    if hidden:
        for a, b in hid:
            p = place(V[[a, b]])
            ax.plot(p[:, 0], p[:, 1], color=C_HID, lw=lw * 0.55, ls=(0, (4, 3)), zorder=2)
    for a, b in vis:
        p = place(V[[a, b]])
        ax.plot(p[:, 0], p[:, 1], color=C_VIS, lw=lw, solid_capstyle="round", zorder=4)
    if not cyl:
        return
    for c in CILS:
        for t, ne in ((0, c.n0), (1, c.n1)):
            if ne is not None and abs(ne @ v) <= EPS:
                continue                                   # borde visto de canto: cae sobre el contorno
            p = place(c.rim(t))
            vis_rim = ne is not None and ne @ v > EPS
            if vis_rim:
                ax.plot(p[:, 0], p[:, 1], color=C_VIS, lw=lw * 0.8, zorder=4)
            elif hidden:
                ax.plot(p[:, 0], p[:, 1], color=C_HID, lw=lw * 0.5, ls=(0, (4, 3)), zorder=2)
        if hidden:
            for p0, p1 in c.silhouettes(v):
                p = place(np.array([p0, p1]))
                ax.plot(p[:, 0], p[:, 1], color=C_HID, lw=lw * 0.5, ls=(0, (4, 3)), zorder=2)
    if EXTRA is not None:
        nz = Z @ v
        if abs(nz) > EPS:                                # el borde superior no está de canto
            p = place(EXTRA.rim())
            if nz > EPS:
                ax.plot(p[:, 0], p[:, 1], color=C_VIS, lw=lw * 0.8, zorder=4)
            elif hidden:
                ax.plot(p[:, 0], p[:, 1], color=C_HID, lw=lw * 0.5, ls=(0, (4, 3)), zorder=2)
        if hidden and abs(nz) < 0.999:
            p = place(EXTRA.bottom())
            ax.plot(p[:, 0], p[:, 1], color=C_HID, lw=lw * 0.5, ls=(0, (4, 3)), zorder=2)
            for p0, p1 in EXTRA.silhouettes(v):
                p = place(np.array([p0, p1]))
                ax.plot(p[:, 0], p[:, 1], color=C_HID, lw=lw * 0.5, ls=(0, (4, 3)), zorder=2)


def right_angle(ax, corner, d1, d2, s=0.28):
    p1, p3 = corner + s * d1, corner + s * d2
    ax.plot([p1[0], (p1 + s * d2)[0], p3[0]], [p1[1], (p1 + s * d2)[1], p3[1]], color=C_FOLD, lw=0.9)


def dim(ax, p, q, text, off=0.9, fs=9, color="0.1"):
    p, q = np.asarray(p, float), np.asarray(q, float)
    t = unit(q - p); nrm = np.array([-t[1], t[0]]) * np.sign(off)
    p2, q2 = p + off * np.array([-t[1], t[0]]), q + off * np.array([-t[1], t[0]])
    for a, a2 in ((p, p2), (q, q2)):
        ax.plot([a[0], a2[0] + 0.2 * nrm[0]], [a[1], a2[1] + 0.2 * nrm[1]], color=color, lw=0.6)
    ax.annotate("", xy=q2, xytext=p2, arrowprops=dict(arrowstyle="<|-|>", lw=0.8, color=color,
                                                      shrinkA=0, shrinkB=0, mutation_scale=7))
    mid = (p2 + q2) / 2 + 0.28 * nrm
    ang = np.degrees(np.arctan2(t[1], t[0]))
    ang = ang + 180 if ang > 90 or ang < -90 else ang
    ax.text(mid[0], mid[1], text, rotation=ang, ha="center", va="center", fontsize=fs, color=color,
            bbox=dict(fc="white", ec="none", pad=0.6), zorder=6)


def ray_exit(p, d, poly):
    best = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        Mx = np.column_stack((d, -(b - a)))
        if abs(np.linalg.det(Mx)) < 1e-12:
            continue
        lam, mu = np.linalg.solve(Mx, a - p)
        if -1e-9 <= mu <= 1 + 1e-9 and lam > best:
            best = lam
    return best


def label(ax, xy, text, off, fs=11, color="k", **kw):
    ax.text(xy[0] + off[0], xy[1] + off[1], text, fontsize=fs, color=color, ha="center", va="center", zorder=7, **kw)


def draw_layout(ax, mode="total", top=True, dims_aux=False):
    """Hoja con alzado, planta, línea de pliegue, proyectantes ⊥ y vista auxiliar (total o parcial)."""
    arrs = [place_front(V)]
    hexf = place_front(V[:6])
    draw_view(ax, place_front, nF, hidden=(mode != "partial"), cyl=(mode != "partial"))
    if top:
        draw_view(ax, place_top, nT)
        arrs.append(place_top(V))
        for x in sorted(set(np.round(V[:, 0], 9))):
            ax.plot([x, x], [ZMAX, ZMAX + GAP], color=C_PROJ, lw=0.8, ls=":")
        ax.plot([-1.0, XMAX + 1.0], [ZMAX + GAP] * 2, color=C_FOLD, lw=1.0, ls=(0, (6, 3, 1, 3)))
        ax.text(-1.2, ZMAX + GAP - 0.2, "eje de referencia\n(y = 0)", color=C_FOLD, fontsize=8, ha="right", va="top")
        label(ax, (XMAX / 2, ZMAX + GAP + M + 0.7), "Vista superior (planta)", (0, 0), fs=9, color="0.35")
    label(ax, (XMAX / 2, -0.8), "Vista frontal (alzado)", (0, 0), fs=9, color="0.35")
    # cara resaltada: de canto en el alzado
    AF, BF = place_front(V[iA])[0], place_front(V[iB])[0]
    ax.plot([AF[0], BF[0]], [AF[1], BF[1]], color=C_HI, lw=4.5, zorder=3, solid_capstyle="round", alpha=0.9)
    label(ax, AF, r"$A_F D_F$", unit(AF - hexf.mean(axis=0)) * 0.9, fs=10, color=C_FOLD)
    label(ax, BF, r"$B_F C_F$", unit(BF - hexf.mean(axis=0)) * 0.9, fs=10, color=C_FOLD)
    # vista auxiliar
    if mode == "partial":
        poly = aux.place(V[FACE])
        draw_idx = [iA, iB]
    else:
        draw_view(ax, aux.place, aux.los)
        poly = aux.place(V[FACE])
        draw_idx = range(6)
        arrs.append(aux.place(V))
    ax.fill(poly[:, 0], poly[:, 1], color=C_HI, alpha=0.35, zorder=1)
    ax.plot(*np.vstack((poly, poly[:1])).T, color="k", lw=2.0, zorder=5)
    arrs.append(poly)
    cen = poly.mean(axis=0)
    for i, name in zip(FACE, "ABCD"):
        p = aux.place(V[i])[0]
        label(ax, p, rf"${name}_1$", unit(p - cen) * 0.75, fs=11, color=C_FOLD)
    # pliegue L.T.1 + proyectantes + marcas de 90°
    f0, f1 = aux.fold(0.8)
    ax.plot([f0[0], f1[0]], [f0[1], f1[1]], color=C_FOLD, lw=1.1, ls=(0, (6, 3, 1, 3)))
    ax.text(*(f0 + np.array([0.3, -0.2])), "eje de referencia (L.T.₁)\n⊥ LOS1", color=C_FOLD, fontsize=8, ha="left", va="top")
    alongs = {i: (V[i] @ aux.T3) for i in draw_idx}
    for i in draw_idx:
        p = place_front(V[i])[0]
        lam0 = ray_exit(p, aux.N2, hexf)
        far = aux.place(V[(i + 6) if i < 6 else i])[0]
        s0 = p + lam0 * aux.N2
        ax.plot([s0[0], far[0]], [s0[1], far[1]], color=C_PROJ, lw=0.8, ls=":", zorder=1)
    for i, sg in ((iA, -1), (iB, +1)):
        p = place_front(V[i])[0]
        cr = p + (aux.hF - p @ aux.N2) * aux.N2
        right_angle(ax, cr, -aux.N2, sg * aux.T2)
        ax.text(*(cr - 0.8 * aux.N2 + sg * 0.55 * aux.T2), "90°", color=C_FOLD, fontsize=7, ha="center", va="center")
    # LOS1
    m = 0.5 * (AF + BF)
    ax.annotate("", xy=m + 1.9 * aux.N2, xytext=m, arrowprops=dict(arrowstyle="-|>", color=C_FOLD, lw=1.2, mutation_scale=10))
    label(ax, m + 1.9 * aux.N2, "LOS1", (0.1, 0.45), fs=9, color=C_FOLD)
    base = aux.place(V).mean(axis=0) if mode == "total" else poly.mean(axis=0)
    label(ax, base + (M / 2 + 2.8) * aux.N2, "Vista auxiliar 1" + (" (total)" if mode == "total" else " (parcial)"),
          (0, 0), fs=9, color="0.35")
    if dims_aux:
        dim(ax, aux.place(V[iB])[0], aux.place(V[iC])[0], f"y = {M:.2f}", off=0.0 + 0.9, fs=8, color=C_PROJ)
    return arrs


def finish(ax, arrs, pad=1.4):
    A = np.vstack(arrs)
    ax.set_xlim(A[:, 0].min() - pad, A[:, 0].max() + pad + 2.0)
    ax.set_ylim(A[:, 1].min() - pad - 0.5, A[:, 1].max() + pad)
    ax.set_aspect("equal"); ax.axis("off")


# isométrica -----------------------------------------------------------------
V_ISO = unit([1.0, -1.0, 1.0])


def iso_basis(v):
    return basis_from_normal(v, Z)


def draw_iso(ax, v=V_ISO, face=True, triad=True, title=None):
    u, w = iso_basis(v)
    place = lambda P: proj(P, u, w)
    draw_view(ax, place, v)
    if face and normals[2 + k] @ v > EPS:
        poly = place(V[FACE])
        ax.fill(poly[:, 0], poly[:, 1], color=C_HI, alpha=0.4, zorder=1)
        cen = place(V).mean(axis=0)
        for i, name in zip(FACE, "ABCD"):
            p = place(V[i])[0]
            if np.dot(V[i] - V.mean(axis=0), v) > -4:
                label(ax, p, name, unit(p - cen) * 0.55, fs=10, color=C_FOLD)
    allp = place(V)
    if triad:
        o = np.array([allp[:, 0].min() - 1.2, allp[:, 1].min() - 0.2])
        for vec, name, col in ((X, "X", "#c0392b"), (Y, "Y", "#27ae60"), (Z, "Z", "#2980b9")):
            d = 2.0 * np.array([vec @ u, vec @ w])
            ax.annotate("", xy=o + d, xytext=o, arrowprops=dict(arrowstyle="-|>", color=col, lw=1.3, mutation_scale=9))
            ax.text(*(o + d * 1.18), name, color=col, fontsize=9, ha="center", va="center")
    if title:
        ax.set_title(title, fontsize=10)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(allp[:, 0].min() - 2.0, allp[:, 0].max() + 1.2)
    ax.set_ylim(allp[:, 1].min() - 1.2, allp[:, 1].max() + 1.2)


FOOT = (f"Tuerca hexagonal · s = {S:.2f} cm · e = {E:.2f} cm · m = {M:.2f} cm · Ø agujero ≈ {D_BORE:.1f} cm (estimado) · "
        "sin chaflán · proyección de tercer diedro · escala 1:1 · unidades: cm")


def new_fig(title, sub=None, size=(16, 9)):
    fig = plt.figure(figsize=size)
    fig.suptitle(title, fontsize=15, fontweight="bold", x=0.02, ha="left", y=0.975)
    if sub:
        fig.text(0.02, 0.925, sub, fontsize=10.5, color="0.25", ha="left", va="top")
    fig.text(0.02, 0.012, FOOT, fontsize=8, color="0.4")
    return fig


def textbox(fig, rect, text, fs=10, mono=False):
    ax = fig.add_axes(rect); ax.axis("off")
    ax.text(0, 1, text, va="top", ha="left", fontsize=fs, family="monospace" if mono else None, linespacing=1.55)
    return ax


# ----------------------------------------------------------------------------
# 6. PÁGINAS (una por paso)
# ----------------------------------------------------------------------------
def page_resumen():
    fig = new_fig("Resumen · Proyección auxiliar total de la tuerca hexagonal",
                  "Tres partes: 1) plano 3D isométrico · 2) vistas principales (planta y alzado) · 3) vista auxiliar a 90° de la cara inclinada ABCD")
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 2.35], left=0.02, right=0.99, top=0.88, bottom=0.05, wspace=0.02)
    a1, a2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    draw_iso(a1, title="1 · Plano 3D (isométrica)")
    arrs = draw_layout(a2, "total", top=True)
    finish(a2, arrs)
    a2.set_title("2 · Vistas principales  +  3 · Vista auxiliar (proyección a 90° de la cara ABCD)", fontsize=10)
    return fig


def page_principales():
    fig = new_fig("Paso 1 · Vistas principales con cotas (hoja de referencia)",
                  "Alzado, planta (encima) y perfil derecho (a la derecha), alineados con proyectantes. Líneas de trazo = aristas ocultas; trazo-punto = ejes.")
    ax = fig.add_axes([0.03, 0.06, 0.94, 0.82])
    draw_view(ax, place_front, nF); draw_view(ax, place_top, nT); draw_view(ax, place_right, nR)
    cc = dict(color="#2c5aa0", lw=0.8, ls=(0, (8, 2, 1, 2)))
    ax.plot([-0.8, XMAX + 0.8], [cz, cz], **cc); ax.plot([cx, cx], [-0.8, ZMAX + 0.8], **cc)
    ax.plot([cx, cx], [ZMAX + GAP - 0.6, ZMAX + GAP + M + 0.6], **cc)
    ax.plot([XMAX + GAP - 0.6, XMAX + GAP + M + 0.6], [cz, cz], **cc)
    for x in sorted(set(np.round(V[:, 0], 9))):
        ax.plot([x, x], [ZMAX, ZMAX + GAP], color=C_PROJ, lw=0.8, ls=":")
    for z in sorted(set(np.round(V[:, 2], 9))):
        ax.plot([XMAX, XMAX + GAP], [z, z], color=C_PROJ, lw=0.8, ls=":")
    dim(ax, (0, 0), (XMAX, 0), f"e = {E:.2f}", off=-1.1)
    dim(ax, (0, 0), (0, S), f"s = {S:.2f}", off=1.1)
    dim(ax, (cx - D_BORE / 2, cz), (cx + D_BORE / 2, cz), f"Ø {D_BORE:.2f}", off=0.0, fs=8.5)
    ytop = ZMAX + GAP
    dim(ax, (Q1, ytop + M), (E - Q1, ytop + M), f"{LADO_SUP:.2f}", off=0.9)
    dim(ax, (XMAX, ytop), (XMAX, ytop + M), f"m = {M:.2f}", off=-1.1)
    if EXTRA is not None:
        dim(ax, (cx - EXTRA.r, ytop + EXTRA.yc), (cx + EXTRA.r, ytop + EXTRA.yc), f"Ø {D_EXTRA:.1f}", off=0.0, fs=7.5)
    dim(ax, (XMAX + GAP, 0), (XMAX + GAP + M, 0), f"m = {M:.2f}", off=-1.1)
    dim(ax, (XMAX + GAP + M, 0), (XMAX + GAP + M, S), f"s = {S:.2f}", off=-1.1)
    label(ax, (XMAX / 2, -2.4), "VISTA FRONTAL (alzado)", (0, 0), fs=10, color="0.3")
    label(ax, (XMAX / 2, ytop + M + 1.7), "VISTA SUPERIOR (planta)", (0, 0), fs=10, color="0.3")
    label(ax, (XMAX + GAP + M / 2, S + 0.9), "VISTA LATERAL DERECHA", (0, 0), fs=10, color="0.3")
    A = np.vstack((place_front(V), place_top(V), place_right(V)))
    ax.set_xlim(-2.5, A[:, 0].max() + 3); ax.set_ylim(-3.4, A[:, 1].max() + 2.6)
    ax.set_aspect("equal"); ax.axis("off")
    return fig


def page_identificar():
    fig = new_fig("Paso 2 · Identificar la cara inclinada y su normal (producto cruz)",
                  "La cara ABCD es perpendicular al plano frontal → en el alzado se ve de CANTO (A_F B_F) y no muestra su verdadera forma.")
    a1 = fig.add_axes([0.02, 0.08, 0.34, 0.80]); a2 = fig.add_axes([0.36, 0.08, 0.30, 0.80])
    draw_view(a1, place_front, nF)
    AF, BF = place_front(V[iA])[0], place_front(V[iB])[0]
    a1.plot([AF[0], BF[0]], [AF[1], BF[1]], color=C_HI, lw=5, solid_capstyle="round")
    hexf = place_front(V[:6])
    label(a1, AF, r"$A_F D_F$", unit(AF - hexf.mean(axis=0)) * 0.9, color=C_FOLD)
    label(a1, BF, r"$B_F C_F$", unit(BF - hexf.mean(axis=0)) * 0.9, color=C_FOLD)
    mid = 0.5 * (AF + BF)
    a1.annotate("", xy=mid + 1.8 * aux.N2, xytext=mid, arrowprops=dict(arrowstyle="-|>", color=C_FOLD, lw=1.3, mutation_scale=10))
    label(a1, mid + 1.8 * aux.N2, "n = LOS1", (0.2, 0.5), fs=9, color=C_FOLD)
    a1.set_title("Alzado: la cara se ve de canto", fontsize=10)
    a1.set_aspect("equal"); a1.axis("off"); a1.set_xlim(-2.2, XMAX + 3.2); a1.set_ylim(-1.5, S + 3)
    draw_iso(a2, title="Isométrica: cara ABCD resaltada")
    c = CHK
    fmt = lambda v: "[" + ", ".join(f"{x + 0.0:7.4f}" for x in v) + "]"
    txt = (
        "CÁLCULO (numpy)\n\n"
        f"A = {fmt(V[iA])}\nB = {fmt(V[iB])}\nD = {fmt(V[iD])}\n\n"
        f"AB = B − A = {fmt(c['AB'])}\nAD = D − A = {fmt(c['AD'])}\n\n"
        f"n = (AB × AD)/|AB × AD|\n  = {fmt(c['n_cross'])}\n\n"
        f"n · Y = {c['n_dot_Y']:+.1e}  ⇒  n ⊥ Y\n"
        "   ⇒ la cara es perpendicular al plano\n      frontal (se ve de canto).\n\n"
        f"Ángulo de A_F B_F con la horizontal:\n  {c['ang_edge']:.2f}°   (caja 7 × 7 → 63,43°)\n\n"
        "LOS1 = n  (la mirada debe ser ⊥ a la cara)\n"
        f"Área real de ABCD = {c['A3']:.4f} cm²\n"
        f"Área vista en el alzado = {c['A_front']:.4f} cm²")
    textbox(fig, [0.68, 0.10, 0.31, 0.80], txt, fs=9.2, mono=True)
    return fig


def page_construccion():
    fig = new_fig("Paso 3 · Línea de pliegue, proyectantes a 90° y profundidades",
                  "Método del eje de referencia (el de la pizarra): la profundidad y se mide en la planta desde y = 0 y se lleva sobre cada proyectante desde L.T.₁.")
    ax = fig.add_axes([0.02, 0.27, 0.96, 0.62])
    arrs = draw_layout(ax, "partial", top=True, dims_aux=True)
    pt = place_top(V)
    dim(ax, (0, ZMAX + GAP), (0, ZMAX + GAP + M), f"y = {M:.2f}", off=1.0, fs=8.5, color=C_PROJ)
    finish(ax, arrs)
    steps = ("1.  En el alzado la cara ABCD se ve de canto: segmento A_F B_F (a 63,43°).\n"
             f"2.  Trazar la línea de pliegue L.T.₁ (eje de referencia) PARALELA a A_F B_F, a {AUX_GAP:g} cm de la pieza (distancia cómoda).\n"
             "3.  Desde A_F y B_F trazar las proyectantes PERPENDICULARES a L.T.₁ (marca de 90°). Dirección = LOS1.\n"
             "4.  En la planta medir las profundidades desde el eje de referencia (y = 0): A, B → 0,00 · C, D → 3,00 cm.\n"
             "5.  Llevar esas distancias sobre cada proyectante, medidas desde L.T.₁ (A₁, B₁ sobre L.T.₁; C₁, D₁ a 3,00 cm).\n"
             "6.  Unir A₁-B₁-C₁-D₁: vista auxiliar parcial = verdadera magnitud de la cara.")
    textbox(fig, [0.03, 0.02, 0.94, 0.22], steps, fs=10.5)
    return fig


def true_shape_axes(ax, title=True):
    img = aux.image(V[FACE])
    ax.fill(img[:, 0], img[:, 1], color=C_HI, alpha=0.35)
    ax.plot(*np.vstack((img, img[:1])).T, color="k", lw=2.2)
    cen = img.mean(axis=0)
    for q, name in zip(img, "ABCD"):
        label(ax, q, rf"${name}_1$", unit(q - cen) * 0.45, fs=12, color=C_FOLD)
    dim(ax, img[1], img[0], f"a = {CHK['a_aux']:.2f}", off=0.8)
    dim(ax, img[1], img[2], f"m = {CHK['m_aux']:.2f}", off=-0.8)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(img[:, 0].min() - 2, img[:, 0].max() + 2); ax.set_ylim(img[:, 1].min() - 1.6, img[:, 1].max() + 1.8)
    if title:
        ax.set_title("Verdadera magnitud de la cara ABCD", fontsize=10)


def page_parcial():
    fig = new_fig("Paso 4 · Vista auxiliar PARCIAL (solo la cara inclinada)",
                  "Se proyecta únicamente la cara ABCD, perpendicular a LOS1; el resto de la pieza no se dibuja.")
    a1 = fig.add_axes([0.02, 0.07, 0.62, 0.82]); a2 = fig.add_axes([0.66, 0.30, 0.32, 0.55])
    arrs = draw_layout(a1, "partial", top=False)
    finish(a1, arrs)
    true_shape_axes(a2)
    c = CHK
    txt = (f"Comprobación:\n a (3D) = {c['a3']:.4f}   a (aux) = {c['a_aux']:.4f}\n"
           f" m (3D) = {c['m3']:.4f}   m (aux) = {c['m_aux']:.4f}\n"
           f" Área 3D = {c['A3']:.4f}   Área aux = {c['A_aux']:.4f}\n"
           f" Razón = {c['A_aux'] / c['A3']:.6f}")
    textbox(fig, [0.67, 0.10, 0.31, 0.16], txt, fs=9.5, mono=True)
    return fig


def page_total():
    fig = new_fig("Paso 5 · Vista auxiliar TOTAL (toda la pieza mirada a lo largo de LOS1)",
                  "Se proyectan todos los vértices; aristas ocultas y el taladro con trazo discontinuo. Se miden las bandas que forman las caras laterales.")
    a1 = fig.add_axes([0.02, 0.07, 0.60, 0.82]); a2 = fig.add_axes([0.63, 0.22, 0.36, 0.60])
    arrs = draw_layout(a1, "total", top=False)
    finish(a1, arrs)
    place = lambda P: aux.image(P)
    draw_view(a2, place, aux.los)
    img = aux.image(V)
    xs = np.unique(np.round(img[:, 0], 9))
    ytop, ybot = img[:, 1].max(), img[:, 1].min()
    for x0, x1 in zip(xs[:-1], xs[1:]):
        dim(a2, (x0, ytop), (x1, ytop), f"{x1 - x0:.2f}", off=0.9, fs=9)
    dim(a2, (xs[-1], ytop), (xs[-1], ybot), f"m = {ytop - ybot:.2f}", off=-1.1, fs=9)
    dim(a2, (xs[0], ybot), (xs[-1], ybot), f"e = {xs[-1] - xs[0]:.2f}", off=-1.1, fs=9)
    a2.set_aspect("equal"); a2.axis("off")
    a2.set_xlim(xs[0] - 1.5, xs[-1] + 3); a2.set_ylim(ybot - 2.5, ytop + 2.5)
    a2.set_title("Vista auxiliar total (imagen para leerse)", fontsize=10)
    textbox(fig, [0.64, 0.07, 0.34, 0.12],
            f"Ancho total de la vista = {xs[-1] - xs[0]:.4f} cm\nLas dos líneas discontinuas verticales son el taladro (Ø {D_BORE:.1f} cm).",
            fs=9.5)
    return fig


def page_verificacion():
    fig = new_fig("Paso 6 · Verificación numérica (garantía de que la vista es exacta)")
    c = CHK
    txt = (
        "PRUEBAS QUE EJECUTA EL SCRIPT (si una falla, se detiene)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        f" 1. Bases right-handed (u × w = n) en alzado, planta, perfil y auxiliar          OK\n"
        f" 2. n = AB × AD coincide con la normal saliente de la cara                       OK\n"
        f" 3. n · Y = {c['n_dot_Y']:+.1e}  → la cara es ⊥ al plano frontal                      OK\n"
        f" 4. L.T.₁ ⊥ LOS1:  T·n = {c['T3_dot_n']:+.1e}                                         OK\n"
        f" 5. Proyectantes ⊥ L.T.₁: máx |(q − p_F)·T| = {c['perp']:.1e}  (12 vértices)         OK\n"
        f" 6. Proyectantes || LOS1:  máx |(q − p_F) × N| = {c['par']:.1e}                        OK\n"
        f" 7. Verdadera magnitud: |a_aux − a_3D| = {abs(c['a_aux'] - c['a3']):.1e},  |Área_aux − Área_3D| = {abs(c['A_aux'] - c['A3']):.1e}   OK\n"
        f" 8. La hoja (vista girada) es rotación rígida: conserva el área                   OK\n"
        "\n"
        "¿POR QUÉ SOLO LA VISTA AUXILIAR MUESTRA LA VERDADERA FORMA?\n"
        "   Área proyectada = Área real · |n · v|   (v = dirección de mirada)\n"
        "\n"
        f"   Vista        v           |n · v|   Área vista (cm²)   Área real (cm²)\n"
        f"   Alzado      (0,−1,0)    {abs(n_face @ nF):.4f}    {c['A_front']:9.4f}         {c['A3']:.4f}\n"
        f"   Planta      (0,0,1)     {abs(n_face @ nT):.4f}    {c['A_top']:9.4f}         {c['A3']:.4f}\n"
        f"   Perfil der. (1,0,0)     {abs(n_face @ nR):.4f}    {c['A_right']:9.4f}         {c['A3']:.4f}\n"
        f"   Auxiliar 1  v = n       {abs(n_face @ aux.los):.4f}    {c['A_aux']:9.4f}         {c['A3']:.4f}   ← única con razón 1\n"
        "\n"
        "LÍMITES DEL MODELO\n"
        "   • Prisma hexagonal sin chaflán (el chaflán son conos; no cambia el procedimiento).\n"
        f"   • Ø del agujero roscado = {D_BORE:.1f} cm es una ESTIMACIÓN (de las elipses del isométrico).\n"
        f"   • Agujero de la cara superior: Ø {D_EXTRA} cm ESTIMADO de tu isométrico, pasante hasta el agujero roscado (D_EXTRA).\n"
        "   • Una cara oblicua (no ⊥ a ningún plano principal) necesita DOS vistas auxiliares sucesivas (LOS1 y LOS2);\n"
        "     las caras de la tuerca son todas inclinadas, no oblicuas: basta una.")
    textbox(fig, [0.03, 0.03, 0.95, 0.87], txt, fs=10.2, mono=True)
    return fig


def page_rotacion():
    fig = new_fig("Paso 7 · Rotación de la pieza en 3D (matriz de rotación Rz)",
                  "Girar la pieza un ángulo θ equivale a mirarla desde  v' = Rz(−θ)·v.  Rz(θ) = [[cosθ, −sinθ, 0],[sinθ, cosθ, 0],[0, 0, 1]].")
    gs = fig.add_gridspec(1, 4, left=0.01, right=0.99, top=0.84, bottom=0.06, wspace=0.0)
    for j, th in enumerate((0, 90, 180, 270)):
        t = np.deg2rad(-th)
        Rz = np.array([[np.cos(t), -np.sin(t), 0], [np.sin(t), np.cos(t), 0], [0, 0, 1]])
        v = unit(Rz @ V_ISO)
        draw_iso(fig.add_subplot(gs[j]), v=v, face=True, triad=False, title=f"θ = {th}°")
    return fig


def main():
    pages = [("paso_0_resumen", page_resumen), ("paso_1_vistas_principales", page_principales),
             ("paso_2_cara_inclinada", page_identificar), ("paso_3_construccion", page_construccion),
             ("paso_4_auxiliar_parcial", page_parcial), ("paso_5_auxiliar_total", page_total),
             ("paso_6_verificacion", page_verificacion), ("paso_7_rotacion_3d", page_rotacion)]
    pdf_path = os.path.join(OUT, "Proyecciones_auxiliares_tuerca.pdf")
    with PdfPages(pdf_path) as pdf:
        for name, fn in pages:
            fig = fn()
            fig.savefig(os.path.join(OUT, name + ".png"), dpi=140, facecolor="white")
            pdf.savefig(fig, facecolor="white")
            plt.close(fig)
    print("Verificaciones OK. Archivos en:", OUT)
    c = CHK
    print(f"n = {np.round(c['n_cross'], 6)}  n·Y = {c['n_dot_Y']:.1e}  ángulo A_F B_F = {c['ang_edge']:.2f}°")
    print(f"a: {c['a3']:.4f} → {c['a_aux']:.4f}   m: {c['m3']:.4f} → {c['m_aux']:.4f}   área razón = {c['A_aux'] / c['A3']:.6f}")


if __name__ == "__main__":
    main()
