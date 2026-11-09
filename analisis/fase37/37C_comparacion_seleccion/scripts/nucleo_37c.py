"""
Fase 37C: núcleo compartido. Cadena recalibrable por niveles (E1, E2, E3), imputación en memoria y medidas de partición.

Importa de las Fases 36, 37A y 37B sin modificarlas. Debe activar dont_write_bytecode antes de esas importaciones, para no dejar
carpetas __pycache__ en fases protegidas. Un hilo por proceso, igual que la Fase 37B.
"""
import os
import sys

sys.dont_write_bytecode = True
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import hashlib  # noqa: E402
import json  # noqa: E402
import zipfile  # noqa: E402
from pathlib import Path  # noqa: E402
from xml.etree import ElementTree as ET  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
FASE37 = BASE.parent
B37 = FASE37 / '37B_clustering'
sys.path[:0] = [str(B37 / 'scripts')]

import nucleo_37b as Q  # noqa: E402  (fija rutas de las Fases 36 y 37A e importa reduccion y transformador)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import linear_sum_assignment  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

R = Q.R
TF = Q.TF
F36 = Q.F36
A37 = Q.A37
RAIZ = Q.RAIZ
SEMILLA = Q.SEMILLA
NIVELES = ('E1', 'E2', 'E3')
BASE_CFG = {'P': 'pca', 'F': 'famd'}
PROTEGIDAS = {'fase36': F36, '37A_reduccion': A37, '37B_clustering': B37}


# ---- protocolo y auditoría
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def huella_sello():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo de la Fase 37C no coincide con su sello.')
    return s['sha256']


instalar_gancho = Q.instalar_gancho
leidos = Q.leidos


def registrar(etapa, resultados):
    Q.registrar(BASE, etapa, resultados)


def a_csv(t, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')


def a_json(o, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(o, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


# ---- listas
def tabla_37b():
    return pd.read_csv(B37 / 'resultados' / 'tabla_completa_configuraciones.csv', encoding='utf-8').set_index('config')


def tablas_docx(ruta):
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    cuerpo = ET.fromstring(zipfile.ZipFile(ruta).read('word/document.xml')).find(w + 'body')
    texto = lambda e: ''.join(t.text or '' for t in e.iter(w + 't')).strip()  # noqa: E731
    return [[[texto(c) for c in fila.findall(w + 'tc')] for fila in el.iter(w + 'tr')] for el in cuerpo if el.tag == w + 'tbl']


def lista_b():
    """Lee la Lista B del propio documento de preparación: la segunda tabla de 17_preparacion_37C.docx."""
    t = tablas_docx(B37 / 'informes' / '17_preparacion_37C.docx')[1]
    if t[0][0] != 'Configuración' or 'S-ORD' not in t[0]:
        raise SystemExit('La segunda tabla del documento no es la Lista B.')
    return [f[0] for f in t[1:]]


def lista_a():
    t = tabla_37b()
    return t.index[t['lista_37C']].tolist()


def vista_a():
    t = tabla_37b()
    return t.index[t['lista_37C_visible']].tolist()


def priorizadas():
    """Conjunto priorizado de la sección 3 del protocolo, con el motivo de inclusión de cada una, en orden estable."""
    b = lista_b()
    grupos = [('Lista B', b), ('Vista A', vista_a()), ('Referencia k = 2', ['F1_c05_km_k2', 'P1_c05_km_k2']), ('Comparador Ward', [c.replace('_km_', '_ward_') for c in b]),
              ('Referencia sin reducción', [f'{e}_cTodas_km_k{k}' for e in Q.ESPACIOS_R0 for k in (3, 4)])]
    salida = {}
    for nombre, cs in grupos:
        for c in cs:
            salida.setdefault(c, []).append(nombre)
    return {c: ' + '.join(m) for c, m in salida.items()}


def info_config(c):
    e, comp, a, k = c.split('_')
    return {'config': c, 'espacio': e, 'base': e[2:] if e.startswith('R0') else e, 'componentes': 0 if comp == 'cTodas' else int(comp[1:]), 'algoritmo': a, 'k': int(k[1:])}


# ---- entradas de la cadena
def celdas_generales():
    c = pd.read_csv(F36 / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False)
    return c[~c['variable'].isin(Q.NO_GENERALES)].copy()


def definiciones(e):
    """Definiciones de variables desde los artefactos de la Fase 36, con los grupos de FAMD fijados entonces."""
    carpeta = F36 / 'artefactos' / e
    esq = leer_json(carpeta / 'esquema_variables.json')
    cod = leer_json(carpeta / 'codificadores.json')
    ruta = esq['ruta']
    salida, roles, grupos = [], {}, {}
    for d in esq['variables']:
        n = dict(d)
        salida.append(n)
        if ruta == 'famd':
            roles[d['variable']] = d['rol']
            if d['rol'] == 'categorica':
                grupos[d['variable']] = cod[d['variable']]['grupos']
    return salida, ruta, roles, grupos


def a_puntuaciones_normales(par, tabla, defs, filas):
    """Convierte un escenario ridit a puntuaciones normales, Φ⁻¹(ridit), con media y DE de las filas de referencia. Representación exploratoria de la Fase 37C."""
    from scipy.stats import norm
    niveles = TF.leer_niveles(tabla, defs)[0][filas]
    n = int(filas.sum())
    for v, cod in par['codificadores'].items():
        if cod.get('modo') != 'ridit':
            continue
        cod['ridit'] = {k: float(norm.ppf(np.clip(x, 0.5 / n, 1 - 0.5 / n))) for k, x in cod['ridit'].items()}
        x = niveles[v].dropna().map(cod['ridit']).astype(float).to_numpy()
        par['escaladores'][v].update({'media': float(x.mean()), 'de': float(x.std()), 'minimo_referencia': float(x.min()), 'maximo_referencia': float(x.max())})
    return par


class Cadena:
    """Datos de partida en memoria, para no releerlos en cada repetición. Nunca escribe."""

    def __init__(self):
        self.ids = Q.identificadores()
        self.pos = {i: n for n, i in enumerate(self.ids)}
        self.tabla = Q.tabla_general()
        self.celdas = celdas_generales()
        c = self.celdas
        self.estado = c.pivot(index='participante_id', columns='variable', values='estado').reindex(self.ids)
        self.previa = c.pivot(index='participante_id', columns='variable', values='pregunta_previa_imputada').reindex(self.ids)
        self.valor = c.pivot(index='participante_id', columns='variable', values='valor_original').reindex(self.ids)
        self.defs = {e: definiciones(e) for e in Q.ESPACIOS}
        self.imputadas = (self.estado == 'imputada')
        self._congelados = {}

    def tabla_imputada(self, idx=None):
        """Reestima la imputación con la submuestra (posiciones `idx`; None = las 529). Devuelve una copia en memoria."""
        idx = np.arange(len(self.ids)) if idx is None else np.asarray(idx)
        t = self.tabla.copy()
        reglas = {d['variable']: d for d in self.defs['P1'][0]}
        en_sub = np.zeros(len(self.ids), bool)
        en_sub[idx] = True
        nuevos = {}
        for v, d in reglas.items():
            marc = self.imputadas[v].to_numpy()
            if not marc.any() or v == 'imc':
                continue
            obs = self.valor[v].to_numpy()[en_sub & (self.estado[v].to_numpy() == 'observada')]
            obs = obs[obs != '']
            if d['tipo'] in ('binaria', 'nominal'):
                s = pd.Series(obs).value_counts()
                nuevo = sorted(s.index[s == s.max()])[0]
            elif d['tipo'] == 'ordinal':
                nuevo = str(int(np.percentile(obs.astype(float), 50, method='lower')))
            else:
                nuevo = str(int(round(float(np.median(obs.astype(float))))))
            t.loc[t.index[marc], v] = nuevo
            nuevos[v] = nuevo
        # Preguntas madre: la moda sale de las filas no heredadas de la submuestra.
        for hija, madre in Q.MADRES.items():
            val = self.valor[hija].to_numpy()
            her = self.previa[hija].to_numpy() == '1'
            con_dato = (val[en_sub & ~her] != '')
            moda = 'SI' if con_dato.sum() > (~con_dato).sum() else 'NO'
            nuevos[madre] = moda
            if her.any():
                t.loc[t.index[her], madre] = moda
                if moda == 'SI':
                    obs = val[en_sub & (self.estado[hija].to_numpy() == 'observada')]
                    obs = obs[obs != '']
                    t.loc[t.index[her], hija] = str(int(np.percentile(obs.astype(float), 50, method='lower')))
                else:
                    t.loc[t.index[her], hija] = ''
        return t, nuevos

    def calibrada(self, e, tabla, idx, modo='consecutivo'):
        """Calibra el escenario solo con las filas `idx` y transforma las 529 con esos parámetros."""
        defs, ruta, roles, grupos = self.defs[e]
        filas = np.zeros(len(self.ids), bool)
        filas[idx] = True
        par = TF.calibrar(tabla, defs, ruta, modo_ordinal='ridit' if modo == 'normal' else modo, roles=roles or None, grupos=grupos or None, filas_ajuste=pd.Series(filas, index=tabla.index), excluir_de_congelado=self.imputadas)
        if modo == 'normal':
            par = a_puntuaciones_normales(par, tabla, defs, filas)
        return TF.Transformador(par).transformar(tabla)[0]

    def congelada(self, e):
        if e not in self._congelados:
            self._congelados[e] = TF.Transformador.cargar(F36 / 'artefactos' / e).transformar(self.tabla)[0]
        return self._congelados[e]

    def matriz_nivel(self, e, nivel, idx, modo='consecutivo'):
        """Matriz (529 filas) con los parámetros que corresponden al nivel. E1 usa los parámetros de las 529."""
        if nivel == 'E1':
            if modo != 'consecutivo':
                return self.calibrada(e, self.tabla, np.arange(len(self.ids)), modo)
            return self.congelada(e)
        if nivel == 'E2':
            return self.calibrada(e, self.tabla, idx, modo)
        if nivel == 'E3':
            return self.calibrada(e, self.tabla_imputada(idx)[0], idx, modo)
        raise ValueError(nivel)


def coordenadas_cadena(Z, idx, cmax=20):
    """Ajusta la reducción con las filas `idx` y proyecta las 529. Sin alinear signos ni rotaciones."""
    Z = np.asarray(Z, dtype=float)
    modelo = R.ajustar(Z[idx], [f'x{i}' for i in range(Z.shape[1])])
    return R.proyectar(modelo, Z, min(cmax, modelo['rango'])), modelo


# ---- medidas de partición
def ari_pares_compartidos(todas, usadas):
    """ARI de cada par de repeticiones, sobre las participantes que ambos usaron. `todas`: r × n; `usadas`: máscara r × n."""
    salida = []
    for i in range(len(todas)):
        for j in range(i + 1, len(todas)):
            m = usadas[i] & usadas[j]
            salida.append(adjusted_rand_score(todas[i][m], todas[j][m]))
    return salida


def ari_pares_fuera(todas, usadas):
    """ARI de cada par, solo con participantes que ninguno de los dos usó."""
    salida = []
    for i in range(len(todas)):
        for j in range(i + 1, len(todas)):
            m = ~usadas[i] & ~usadas[j]
            if m.sum() >= 5:
                salida.append(adjusted_rand_score(todas[i][m], todas[j][m]))
    return salida


def alinear(base, otra, k=None):
    """Reasigna los nombres de `otra` para que coincidan al máximo con `base` (método húngaro). Solo para leer tablas."""
    gb, go = np.unique(base), np.unique(otra)
    m = np.array([[np.sum((base == a) & (otra == b)) for b in go] for a in gb])
    f, c = linear_sum_assignment(-m)
    mapa = {go[j]: gb[i] for i, j in zip(f, c)}
    siguiente = (max(gb) if len(gb) else 0) + 1
    for g in go:
        if g not in mapa:
            mapa[g] = siguiente
            siguiente += 1
    return np.array([mapa[x] for x in otra])


def transicion(base, otra):
    return pd.crosstab(pd.Series(base, name='base'), pd.Series(alinear(base, otra), name='variante'))


def etiquetas_37b():
    return pd.read_csv(B37 / 'etiquetas' / 'etiquetas_principales.csv', dtype={'participante_id': str}).set_index('participante_id')


def auc(positivos, negativos):
    """AUC por rangos: probabilidad de que un positivo tenga mayor puntaje que un negativo."""
    p, n = np.asarray(positivos, float), np.asarray(negativos, float)
    if len(p) == 0 or len(n) == 0:
        return float('nan')
    r = pd.Series(np.concatenate([p, n])).rank().to_numpy()
    return float((r[:len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(n)))
