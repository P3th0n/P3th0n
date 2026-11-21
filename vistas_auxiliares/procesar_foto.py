#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesa la foto de una lámina para el documento:
  1. detecta la hoja (el cuadrilátero claro más grande),
  2. corrige la perspectiva a proporción ISO A (√2), horizontal,
  3. normaliza la iluminación (quita sombras) y refuerza el trazo de lápiz.

Uso:  python3 procesar_foto.py entrada.jpg salida.jpg [--rotar 0|90|180|270] [--color]
"""
import sys
import argparse
import numpy as np
import cv2
from PIL import Image, ImageOps


def cargar(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")      # respeta la orientación del celular
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def ordenar(pts):
    pts = pts.reshape(4, 2).astype(np.float32)
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)  # TL, TR, BR, BL


def detectar_hoja(img):
    h, w = img.shape[:2]
    k = 1400 / max(h, w)
    small = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (7, 7), 0)
    cands = []
    for mask in (cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                 cv2.dilate(cv2.Canny(g, 40, 120), np.ones((5, 5), np.uint8))):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
            area = cv2.contourArea(cnt)
            if area < 0.15 * small.shape[0] * small.shape[1]:
                continue
            peri = cv2.arcLength(cnt, True)
            for eps in (0.015, 0.02, 0.03, 0.05):
                ap = cv2.approxPolyDP(cnt, eps * peri, True)
                if len(ap) == 4 and cv2.isContourConvex(ap):
                    cands.append((area, ap.reshape(4, 2) / k))
                    break
            else:
                box = cv2.boxPoints(cv2.minAreaRect(cnt))
                cands.append((area * 0.9, box / k))
    if not cands:
        return None
    return ordenar(max(cands, key=lambda c: c[0])[1])


def enderezar(img, quad, ancho=2400):
    tl, tr, br, bl = quad
    wq = (np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2
    hq = (np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2
    if wq >= hq:
        W, H = ancho, int(round(ancho / np.sqrt(2)))
    else:
        W, H = int(round(ancho / np.sqrt(2))), ancho
    M = cv2.getPerspectiveTransform(quad, np.float32([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]]))
    return cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_CUBIC)


def limpiar(img, color=False):
    if color:
        return img
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    fondo = cv2.GaussianBlur(cv2.dilate(g, np.ones((15, 15), np.uint8)), (0, 0), 25)
    n = np.clip(g / np.maximum(fondo, 1) * 255, 0, 255)                # divide por la iluminación
    lo, hi = np.percentile(n, 1.5), np.percentile(n, 99.5)
    n = np.clip((n - lo) / max(hi - lo, 1) * 255, 0, 255)
    n = 255 * (n / 255) ** 1.6                                         # oscurece el trazo
    return n.astype(np.uint8)


def procesar(entrada, salida, rotar=0, color=False):
    img = cargar(entrada)
    quad = detectar_hoja(img)
    out = enderezar(img, quad) if quad is not None else img
    if rotar:
        out = np.rot90(out, k={90: 1, 180: 2, 270: 3}[rotar])        # 90 = antihorario
    out = limpiar(np.ascontiguousarray(out), color)
    if out.ndim == 2 and out.shape[0] > out.shape[1] and rotar == 0:
        pass
    cv2.imwrite(salida, out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return quad is not None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("salida")
    ap.add_argument("--rotar", type=int, default=0, choices=(0, 90, 180, 270))
    ap.add_argument("--color", action="store_true")
    a = ap.parse_args()
    ok = procesar(a.entrada, a.salida, a.rotar, a.color)
    print("hoja detectada y enderezada" if ok else "no se detectó la hoja: se guardó sin enderezar")
