"""
Fase 38: Apriori, FP-Growth y enumeración exhaustiva, escritos en el proyecto. Los tres buscan conjuntos frecuentes con, como máximo, `max_ant` ítems de antecedente
y un ítem de consecuente, con soporte mínimo absoluto `minsup`. Además: generación de reglas, evaluador matricial, redundancia.
"""
import sys
from collections import defaultdict
from itertools import combinations

import nucleo_38 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
CONS = set(N.CONSECUENTES)


def _bits(T, y):
    """Bits por ítem (entero de Python: bit i = participante i). Incluye los dos consecuentes."""
    V = T.to_numpy()
    out = {}
    for j, c in enumerate(T.columns):
        out[c] = int(''.join('1' if x else '0' for x in V[::-1, j]), 2)
    out[N.CONSECUENTES[0]] = int(''.join('1' if x == 1 else '0' for x in y[::-1]), 2)
    out[N.CONSECUENTES[1]] = int(''.join('1' if x == 0 else '0' for x in y[::-1]), 2)
    return out


def _valido(conj):
    """Restricción de forma: como máximo un consecuente y una variable por ítem."""
    nc = sum(1 for i in conj if i in CONS)
    if nc > 1:
        return False
    vs = [N.variable_de_item(i) for i in conj if i not in CONS]
    return len(vs) == len(set(vs))


def apriori(T, y, minsup, max_ant=3):
    bits = _bits(T, y)
    orden = sorted(bits)
    nivel = {}
    for i in orden:
        c = bits[i].bit_count()
        if c >= minsup:
            nivel[(i,)] = (c, bits[i])
    todos = {frozenset(k): v[0] for k, v in nivel.items()}
    k = 1
    while nivel:
        claves = sorted(nivel)
        nuevo = {}
        previos = set(claves)
        for a_i in range(len(claves)):
            a = claves[a_i]
            for b_i in range(a_i + 1, len(claves)):
                b = claves[b_i]
                if a[:-1] != b[:-1]:
                    break
                cand = a + (b[-1],)
                if not _valido(cand):
                    continue
                n_ant = sum(1 for x in cand if x not in CONS)
                if n_ant > max_ant:
                    continue
                if any(tuple(s) not in previos for s in combinations(cand, k)):
                    continue
                bb = nivel[a][1] & bits[b[-1]]
                c = bb.bit_count()
                if c >= minsup:
                    nuevo[cand] = (c, bb)
        for kk, v in nuevo.items():
            todos[frozenset(kk)] = v[0]
        nivel = nuevo
        k += 1
    return todos


class _Nodo:
    __slots__ = ('item', 'cuenta', 'padre', 'hijos', 'enlace')

    def __init__(self, item, padre):
        self.item, self.cuenta, self.padre, self.hijos, self.enlace = item, 0, padre, {}, None


def _arbol(trans, minsup):
    """trans: lista de (lista de ítems, cuenta)."""
    frec = defaultdict(int)
    for t, c in trans:
        for i in t:
            frec[i] += c
    frec = {i: c for i, c in frec.items() if c >= minsup}
    orden = {i: r for r, i in enumerate(sorted(frec, key=lambda i: (-frec[i], i)))}
    raiz = _Nodo(None, None)
    cabeza = {}
    for t, c in trans:
        nodo = raiz
        for i in sorted((i for i in t if i in frec), key=orden.get):
            h = nodo.hijos.get(i)
            if h is None:
                h = _Nodo(i, nodo)
                nodo.hijos[i] = h
                h.enlace = cabeza.get(i)
                cabeza[i] = h
            h.cuenta += c
            nodo = h
    return frec, cabeza


def fpgrowth(T, y, minsup, max_ant=3):
    trans = [(list(t), 1) for t in N.transacciones(T, y)]
    todos = {}

    def minar(trans, sufijo):
        frec, cabeza = _arbol(trans, minsup)
        for i in sorted(frec, key=lambda i: (frec[i], i)):
            nuevo = sufijo | {i}
            if not _valido(nuevo) or sum(1 for x in nuevo if x not in CONS) > max_ant:
                continue
            todos[frozenset(nuevo)] = frec[i]
            if len(nuevo) >= max_ant + 1:
                continue
            base = []
            nodo = cabeza[i]
            while nodo is not None:
                camino, p = [], nodo.padre
                while p.item is not None:
                    camino.append(p.item)
                    p = p.padre
                if camino:
                    base.append((camino, nodo.cuenta))
                nodo = nodo.enlace
            if base:
                minar(base, nuevo)

    minar(trans, frozenset())
    return todos


def exhaustiva(T, y, minsup, max_ant=3):
    bits = _bits(T, y)
    items = sorted(i for i in bits if i not in CONS)
    todos = {}
    for k in range(1, max_ant + 1):
        for comb in combinations(items, k):
            if not _valido(comb):
                continue
            b = bits[comb[0]]
            for i in comb[1:]:
                b &= bits[i]
            c = b.bit_count()
            if c >= minsup:
                todos[frozenset(comb)] = c
                for cc in N.CONSECUENTES:
                    x = (b & bits[cc]).bit_count()
                    if x >= minsup:
                        todos[frozenset(comb + (cc,))] = x
            # sin poda Apriori: se cuenta cada combinación
    for cc in N.CONSECUENTES:
        c = bits[cc].bit_count()
        if c >= minsup:
            todos[frozenset((cc,))] = c
    return todos


def antecedentes(frec, min_ant, determinados=frozenset()):
    """Antecedentes (sin consecuente) con n_A ≥ min_ant que no contienen un par determinado."""
    out = {}
    for s, c in frec.items():
        if c >= min_ant and not (s & CONS) and not any((a, b) in determinados for a in s for b in s if a != b):
            out[s] = c
    return out


def reglas(frec, n, n_si, min_ant, min_conj, determinados=frozenset()):
    """Una regla por antecedente, en la dirección con lift > 1. El recuento del consecuente que falta (bajo el soporte mínimo) se obtiene como n_A − el otro."""
    ants = antecedentes(frec, min_ant, determinados)
    filas = []
    for s, c in ants.items():
        si = frec.get(s | {N.CONSECUENTES[0]})
        no = frec.get(s | {N.CONSECUENTES[1]})
        if si is None and no is None:
            raise ValueError(f'Antecedente sin recuento de consecuente: {sorted(s)}')
        si = si if si is not None else c - no
        filas.append((tuple(sorted(s)), c, si))
    if not filas:
        return pd.DataFrame()
    a, nA, k = zip(*filas)
    R = N.medidas(np.array(nA), np.array(k), n, n_si)
    R.insert(0, 'items', list(a))
    R.insert(0, 'antecedente', [' & '.join(x) for x in a])
    R.insert(2, 'largo', [len(x) for x in a])
    R.insert(3, 'variables', [' & '.join(sorted(N.variable_de_item(i) for i in x)) for x in a])
    R['cumple_conjunto'] = R['n_conjunto'] >= min_conj
    R = R[R['cumple_conjunto']].drop(columns='cumple_conjunto')
    R['marcada'] = R['diferencia_basal'].abs() >= N.DIF_MARCADA
    return R.sort_values(['largo', 'antecedente']).reset_index(drop=True)


def iguales(f1, f2):
    if set(f1) != set(f2):
        return False, len(set(f1) ^ set(f2))
    distintos = sum(1 for k in f1 if f1[k] != f2[k])
    return distintos == 0, distintos


# ---- evaluador matricial
def matriz_antecedentes(T, ants):
    """Indicadora (k × n, uint8) de cada antecedente."""
    col = {c: i for i, c in enumerate(T.columns)}
    V = T.to_numpy()
    A = np.ones((len(ants), len(T)), dtype=bool)
    for r, s in enumerate(ants):
        for i in s:
            A[r] &= V[:, col[i]]
    return A.astype(np.uint8)


def contar(A, Y, lote=20000):
    """A (k × n) por Y (n × m) en lotes de filas, en float32 con resultado entero."""
    out = np.empty((A.shape[0], Y.shape[1]), dtype=np.int32)
    Yf = Y.astype(np.float32)
    for i in range(0, A.shape[0], lote):
        out[i:i + lote] = np.rint(A[i:i + lote].astype(np.float32) @ Yf).astype(np.int32)
    return out


def z_y_validez(nA, k_si, n, n_si, min_conj):
    """|z| y validez (n_AC ≥ mínimo en la dirección con lift > 1) para recuentos dados. nA: (k,) o (k, m); k_si: (k, m)."""
    p0 = n_si / n
    nA = np.asarray(nA, float)
    if nA.ndim == 1:
        nA = nA[:, None]
    c = k_si / nA
    si = c >= p0
    kk = np.where(si, k_si, nA - k_si)
    z = np.abs(c - p0) / np.sqrt(p0 * (1 - p0) / nA)
    dif = np.abs(c - p0)
    return z, kk >= min_conj, dif


def redundancia(R, frec_cons):
    """Mejora mínima: una regla de 2 o 3 condiciones es redundante si algún subconjunto propio, en la misma dirección, tiene confianza > c − 0,05.
    frec_cons: dict antecedente (frozenset) → (n_A, n_SI) que debe contener todos los subconjuntos."""
    mejora, sub_mejor = [], []
    for items, cons, c in zip(R['items'], R['consecuente'], R['confianza']):
        if len(items) == 1:
            mejora.append(np.nan)
            sub_mejor.append('')
            continue
        mejor, quien = -1.0, ''
        for k in range(1, len(items)):
            for sub in combinations(items, k):
                nA, ks = frec_cons[frozenset(sub)]
                cs = ks / nA if cons == N.CONSECUENTES[0] else (nA - ks) / nA
                if cs > mejor:
                    mejor, quien = cs, ' & '.join(sub)
        mejora.append(c - mejor)
        sub_mejor.append(quien)
    R = R.copy()
    R['mejora_sobre_subreglas'] = mejora
    R['subregla_mas_cercana'] = sub_mejor
    R['redundante'] = R['mejora_sobre_subreglas'] < N.MEJORA_MIN
    return R
