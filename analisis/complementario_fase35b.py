"""
Análisis complementario EXPLORATORIO de la Fase 35B, posterior a la ejecución original.
No sustituye el resultado oficial. Protocolo: analisis/protocolo_complementario_35b.md.

Uso:
    python analisis/complementario_fase35b.py --verificar     pruebas y estado; no calcula con los datos reales
    python analisis/complementario_fase35b.py --ejecutar --autorizado-por-usuaria

Solo ejecuta la selección principal: no contiene remuestreos ni sensibilidades.
Reutiliza las funciones congeladas de la Fase 35B, sin modificarlas.
"""
import argparse
import contextlib
import sys
import time
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import seleccionar_fase35b as P
from eda import variables as V
from preprocesamiento import configuracion as C
from preprocesamiento import fcbf as F

COMMIT_ORIGINAL = '745d689937a18c35b62fd25eccc401b169b20e11'
CARPETA = P.ANALISIS / 'complementario_35b_q10'
PROTOCOLO = P.ANALISIS / 'protocolo_complementario_35b.md'
PRUEBAS = P.ANALISIS / 'preprocesamiento' / 'test_complementario_35b.py'
INFORME_WORD = P.ANALISIS / 'informes_fase35b' / 'Informe_Tecnico_Implementacion_Verificacion_Fase35B.docx'
ARCHIVOS_CSV = ['su_objetivo', 'su_pares', 'decisiones_fcbf', 'pares_no_eliminados_cobertura', 'comparacion_con_original',
                'resumen_escenarios']
COLUMNAS_NO_ELIMINADOS = ['laboral', 'no_laboral', 'su_par', 'q_par', 'su_laboral_severidad', 'su_no_laboral_severidad',
                          'n']
COLUMNAS_PARES = ['variable_1', 'variable_2', 'n', 'su', 'p', 'q', 'supera_azar']


@dataclass(frozen=True)
class Parametros:
    nombre: str
    n_permutaciones: int
    alfa: float
    funcion: str


ESCENARIOS = (
    Parametros('E1', 5000, 0.05, 'Reproduce el resultado oficial'),
    Parametros('E2', 5000, 0.10, 'Comparación'),
    Parametros('E3', 50000, 0.05, 'Comparación'),
    Parametros('E4', 50000, 0.10, 'Análisis complementario'),
)


@dataclass
class Evaluacion:
    parametros: Parametros
    medidas: F.Medidas
    adaptado: dict
    estandar: dict
    no_eliminados: list
    segundos: float = 0.0


# --- Rutas: carpeta independiente y lista cerrada ------------------------------------------

@dataclass(frozen=True)
class RutasComplementarias:
    carpeta: Path

    def csv(self, nombre):
        return self.carpeta / f'{nombre}.csv'

    @property
    def informe(self):
        return self.carpeta / 'informe_complementario.md'

    @property
    def log(self):
        return self.carpeta / 'log_complementario.txt'

    def declaradas(self):
        return {self.csv(n) for n in ARCHIVOS_CSV} | {self.informe, self.log}


RUTAS_COMPLEMENTARIAS = RutasComplementarias(CARPETA)


def validar_separacion(rutas, originales=P.RUTAS_REALES):
    """La carpeta no puede estar dentro de las salidas originales ni contener un archivo que ya exista."""
    carpeta = Path(rutas.carpeta).resolve()
    for prohibida in (originales.resultados, originales.figuras, originales.cache, originales.dataset.parent):
        prohibida = Path(prohibida).resolve()
        if carpeta == prohibida or prohibida in carpeta.parents:
            raise PermissionError(f'La carpeta complementaria no puede estar dentro de {prohibida}.')
    if {Path(r).resolve() for r in rutas.declaradas()} & {Path(r).resolve() for r in originales.declaradas()}:
        raise PermissionError('Una ruta complementaria coincide con una salida original.')
    for ruta in rutas.declaradas():
        if ruta.exists():
            raise FileExistsError(f'No se sobrescribe un archivo existente: {ruta}')


# --- Cálculo: reutiliza medir y seleccionar ---------------------------------------------------

@contextlib.contextmanager
def umbral(alfa):
    """Cambia el umbral solo en memoria y siempre lo restaura. No llega a procesos paralelos: aquí no se usan."""
    previo = C.ALFA_Q_35B
    C.ALFA_Q_35B = alfa
    try:
        yield
    finally:
        C.ALFA_Q_35B = previo


def evaluar(principal, parametros):
    """Un escenario completo: relevancia, pares de sus relevantes y las dos variantes de FCBF."""
    t0 = time.perf_counter()
    with umbral(parametros.alfa):
        medidas = F.medir(principal, 0, parametros.n_permutaciones)
        adaptado = F.seleccionar(principal, medidas, True)
        estandar = F.seleccionar(principal, medidas, False)
        P.controlar_seleccion(principal, medidas, adaptado)
        P.controlar_seleccion(principal, medidas, estandar)
        no_eliminados = F.pares_no_eliminados(principal, medidas, adaptado)
    return Evaluacion(parametros, medidas, adaptado, estandar, no_eliminados, time.perf_counter() - t0)


def tabla_objetivo(principal, ev):
    m = ev.medidas
    filas = [{'variable': v, 'grupo': 'laboral' if v in principal.laborales else 'no laboral', 'n': m.n_objetivo[v],
              'su': m.su_objetivo[v], 'p': m.p_objetivo[v], 'q': m.q_objetivo[v], 'relevante': v in m.relevantes,
              'nota': ''} for v in sorted(principal.candidatas)]
    filas += [{'variable': v, 'grupo': 'no laboral', 'n': int(principal.mascara.sum()), 'su': s, 'p': np.nan, 'q': np.nan,
               'relevante': '', 'nota': 'SU recalculada con las observaciones laborales (Etapa 2)'}
              for v, s in sorted(m.su_objetivo_laboral.items()) if v not in principal.laborales]
    return pd.DataFrame(filas)


def tabla_pares(ev):
    m = ev.medidas
    return pd.DataFrame([{'variable_1': a, 'variable_2': b, 'n': m.n_par[(a, b)], 'su': m.su_par[(a, b)],
                          'p': m.p_par[(a, b)], 'q': m.q_par[(a, b)], 'supera_azar': m.q_par[(a, b)] < ev.parametros.alfa}
                         for a, b in sorted(m.su_par)], columns=COLUMNAS_PARES)


def tabla_decisiones(ev):
    return pd.DataFrame(P._tabla_decisiones(ev.adaptado, 'adaptado') + P._tabla_decisiones(ev.estandar, 'estandar'))


def tabla_no_eliminados(ev):
    return pd.DataFrame(ev.no_eliminados, columns=COLUMNAS_NO_ELIMINADOS)


def eliminadas(decisiones):
    return {v: d['eliminada_por'] for v, d in sorted(decisiones.items()) if d['decision'] == 'redundante'}


def fila_resumen(ev):
    m, p = ev.medidas, ev.parametros
    fila = {'escenario': p.nombre, 'funcion': p.funcion, 'permutaciones': p.n_permutaciones, 'umbral_q': p.alfa,
            'n_relevantes': len(m.relevantes), 'relevantes': ';'.join(m.relevantes), 'n_pares': len(m.su_par),
            'n_pares_q_bajo_umbral': sum(q < p.alfa for q in m.q_par.values())}
    for variante, decisiones in (('adaptado', ev.adaptado), ('estandar', ev.estandar)):
        fuera, lista = eliminadas(decisiones), F.seleccionadas(decisiones)
        fila[f'n_redundantes_{variante}'] = len(fuera)
        fila[f'redundantes_{variante}'] = ';'.join(f'{v}<-{z}' for v, z in fuera.items())
        fila[f'n_seleccionadas_{variante}'] = len(lista)
        fila[f'seleccionadas_{variante}'] = ';'.join(lista)
    fila['segundos'] = ev.segundos
    return fila


def tabla_comparacion(principal, evaluaciones):
    filas = []
    for ev in evaluaciones:
        m = ev.medidas
        for v in sorted(principal.candidatas):
            filas.append({'escenario': ev.parametros.nombre, 'permutaciones': ev.parametros.n_permutaciones,
                          'umbral_q': ev.parametros.alfa, 'variable': v, 'su': m.su_objetivo[v], 'p': m.p_objetivo[v],
                          'q': m.q_objetivo[v], 'relevante': v in m.relevantes,
                          'decision_adaptado': ev.adaptado[v]['decision'], 'eliminada_por_adaptado': ev.adaptado[v]['eliminada_por'],
                          'decision_estandar': ev.estandar[v]['decision'], 'eliminada_por_estandar': ev.estandar[v]['eliminada_por']})
    return pd.DataFrame(filas)


# --- Comprobaciones -----------------------------------------------------------------------

def iguales(a, b):
    """Coincidencia exacta de dos evaluaciones, con todos los decimales."""
    for campo in ('su_objetivo', 'n_objetivo', 'p_objetivo', 'q_objetivo', 'relevantes', 'su_par', 'n_par', 'p_par', 'q_par',
                  'su_objetivo_laboral'):
        if getattr(a.medidas, campo) != getattr(b.medidas, campo):
            return False
    return tabla_decisiones(a).equals(tabla_decisiones(b))


def _leer(ruta):
    return pd.read_csv(ruta, encoding='utf-8-sig', dtype=str, keep_default_na=False)


def _txt(x):
    return P.FORMATO % x


def comprobar_oficial(ev, oficial):
    """E1 debe reproducir los archivos oficiales, con los mismos decimales con que se guardaron."""
    m, errores = ev.medidas, []
    su = _leer(oficial.csv('su_objetivo'))
    su = su[su['nota'] == ''].set_index('variable')
    if set(su.index) != set(m.su_objetivo):
        errores.append('las candidatas no coinciden')
    else:
        for v in m.su_objetivo:
            esperado = (_txt(m.su_objetivo[v]), _txt(m.p_objetivo[v]), _txt(m.q_objetivo[v]), str(v in m.relevantes))
            if tuple(su.loc[v, ['su', 'p', 'q', 'relevante']]) != esperado:
                errores.append(f'SU, p, q o relevancia de {v}')
    pares = _leer(oficial.csv('su_pares'))
    filas = {(f['variable_1'], f['variable_2']): (f['su'], f['p'], f['q']) for _, f in pares.iterrows()}
    if filas != {k: (_txt(m.su_par[k]), _txt(m.p_par[k]), _txt(m.q_par[k])) for k in m.su_par}:
        errores.append('los pares')
    columnas = ['variante', 'variable', 'etapa', 'decision', 'eliminada_por']
    guardadas = _leer(oficial.csv('decisiones_fcbf'))[columnas].sort_values(columnas[:2]).reset_index(drop=True)
    nuevas = tabla_decisiones(ev)[columnas].astype(str).sort_values(columnas[:2]).reset_index(drop=True)
    if not guardadas.equals(nuevas):
        errores.append('las decisiones de FCBF')
    if errores:
        raise RuntimeError('E1 no reproduce los resultados oficiales: ' + '; '.join(errores))


def archivos_vigilados():
    """Todo lo original que no puede cambiar: resultados, figuras, caché, entradas, código y el Word."""
    cache = [r for r in P.RUTAS_REALES.cache.rglob('*') if r.is_file()]
    return sorted({*P.archivos_protegidos(), *P.RUTAS_REALES.declaradas(), *P.ARCHIVOS_CODIGO, *cache, INFORME_WORD})


def estado_inicial():
    """Lista de problemas que impiden ejecutar. Vacía: se puede ejecutar."""
    problemas = []
    head = P._git('rev-parse', 'HEAD').strip()
    if head != COMMIT_ORIGINAL:
        problemas.append(f'HEAD es {head}, no {COMMIT_ORIGINAL}.')
    versionados = P._git('status', '--porcelain', '--untracked-files=no').strip()
    if versionados:
        problemas.append(f'Hay cambios en archivos versionados: {versionados}')
    problemas += [f'Sin congelar: {r}' for r in P.codigo_sin_congelar()]
    previo = P.manifiesto_respaldo()
    if previo is None:
        problemas.append('No existe el respaldo de la Fase 35B.')
    else:
        problemas += [f'Difiere del respaldo: {r}' for r in P.diferencias_con_respaldo(previo)]
    return problemas


# --- Informe y registro ---------------------------------------------------------------------

def _tabla_md(encabezado, filas):
    lineas = ['| ' + ' | '.join(encabezado) + ' |', '|' + '---|' * len(encabezado)]
    return '\n'.join(lineas + ['| ' + ' | '.join(map(str, f)) + ' |' for f in filas])


def _p(x):
    return P._n(x, 5)


def _decision_corta(d):
    if d['decision'] == 'redundante':
        return f'redundante (por {V.etiqueta(d["eliminada_por"])})'
    return d['decision']


def informe(principal, evaluaciones, tiempos):
    por_nombre = {ev.parametros.nombre: ev for ev in evaluaciones}
    final = por_nombre.get('E4', evaluaciones[-1])
    m = final.medidas
    orden = sorted(principal.candidatas, key=lambda v: (-m.su_objetivo[v], v))
    tocadas = sorted({v for ev in evaluaciones for v in ev.medidas.relevantes}, key=lambda v: (-m.su_objetivo[v], v))
    partes = [
        '# Fase 35B. Análisis complementario exploratorio',
        f'*Generado por `analisis/complementario_fase35b.py` el {datetime.now():%d-%m-%Y}. '
        'Protocolo: `analisis/protocolo_complementario_35b.md`. Este informe no interpreta causalidad.*',
        '> **Análisis exploratorio, posterior a la ejecución original. No sustituye el resultado oficial de la Fase 35B: '
        f'0 variables seleccionadas con 5.000 permutaciones y q < 0,05 (commit `{COMMIT_ORIGINAL[:7]}`).**',
        '## 1. Resultado del análisis complementario (50.000 permutaciones, q < 0,10)',
        f'- Relevantes: **{len(m.relevantes)}**: {P._lista(m.relevantes)}.',
        f'- Eliminadas por redundancia con la variante adaptada: {P._lista(eliminadas(final.adaptado))}.',
        f'- Seleccionadas con FCBF adaptado: **{len(F.seleccionadas(final.adaptado))}**: '
        f'{P._lista(F.seleccionadas(final.adaptado))}.',
        f'- Seleccionadas con FCBF estándar: **{len(F.seleccionadas(final.estandar))}**: '
        f'{P._lista(F.seleccionadas(final.estandar))}.',
        '## 2. Comparación de los cuatro escenarios',
        'Cada escenario calcula de nuevo la relevancia, sus pares y FCBF. No se deduce de otro cambiando el umbral.',
        _tabla_md(['Escenario', 'Permutaciones', 'q <', 'Relevantes', 'Pares evaluados', 'Redundantes adaptado',
                   'Seleccionadas adaptado', 'Redundantes estándar', 'Seleccionadas estándar'],
                  [[ev.parametros.nombre, f'{ev.parametros.n_permutaciones:,}'.replace(',', '.'),
                    P._n(ev.parametros.alfa, 2), len(ev.medidas.relevantes), len(ev.medidas.su_par),
                    len(eliminadas(ev.adaptado)), len(F.seleccionadas(ev.adaptado)),
                    len(eliminadas(ev.estandar)), len(F.seleccionadas(ev.estandar))] for ev in evaluaciones]),
    ]
    if tocadas:
        for titulo, atributo in (('FCBF adaptado', 'adaptado'), ('FCBF estándar', 'estandar')):
            partes += [f'**Decisión por escenario, {titulo}** (variables relevantes en algún escenario):',
                       _tabla_md(['Variable', *[ev.parametros.nombre for ev in evaluaciones]],
                                 [[V.etiqueta(v), *[_decision_corta(getattr(ev, atributo)[v]) for ev in evaluaciones]]
                                  for v in tocadas])]
    partes += [
        '## 3. Las 30 candidatas con 50.000 permutaciones',
        _tabla_md(['Variable', 'Grupo', 'n', 'SU', 'p', 'q', 'Relevante (q < 0,10)'],
                  [[V.etiqueta(v), 'laboral' if v in principal.laborales else 'no laboral', m.n_objetivo[v],
                    P._n(m.su_objetivo[v]), _p(m.p_objetivo[v]), _p(m.q_objetivo[v]),
                    'sí' if v in m.relevantes else 'no'] for v in orden]),
        '## 4. Pares evaluados con 50.000 permutaciones y q < 0,10',
    ]
    pares = tabla_pares(final)
    partes.append(_tabla_md(['Variable 1', 'Variable 2', 'n', 'SU', 'p', 'q', 'q < 0,10'],
                            [[V.etiqueta(f.variable_1), V.etiqueta(f.variable_2), f.n, P._n(f.su), _p(f.p), _p(f.q),
                              'sí' if f.supera_azar else 'no'] for f in pares.itertuples()])
                  if len(pares) else 'No hay pares.')
    partes += [
        '## 5. Qué cambia con cada parámetro',
        '- **Más permutaciones** mejoran la precisión con que se estima cada valor p. No hacen más permisiva la prueba.',
        '- **Subir el umbral a 0,10** hace menos estricta la selección y aumenta el riesgo de incluir variables por azar: '
        'se tolera que, en promedio, hasta cerca de 1 de cada 10 variables declaradas relevantes sea un falso positivo.',
        '## 6. Advertencias',
        '- **Posterior a los resultados:** el umbral se eligió conociendo la ejecución oficial, por lo que este análisis no es confirmatorio.',
        '- **Sin estabilidad ni sensibilidad:** no se ejecutaron remuestreos ni S1-S5 para estas selecciones.',
        '- **Fuerza de la relación:** un q más bajo no indica una relación más fuerte; hay que leerlo junto con la SU.',
        '- **Carácter sintético:** refleja lo que generó el simulador, no evidencia sobre la población.',
        '- **Circularidad:** seleccionar por severidad puede hacer que los clústeres difieran en severidad por esa misma selección.',
        '- **Interpretación:** seleccionada no significa causal, y eliminada no significa irrelevante.',
        '- **Poblaciones distintas:** la SU laboral describe a trabajadoras (n = 287) y la no laboral a todas (n = 529).',
        '- **`doble_carga`:** es función exacta de `trabaja_actualmente` y `cantidad_personas_cuida`, y sigue en consulta con la profesora.',
        '## 7. Tiempo de ejecución',
        _tabla_md(['Etapa', 'Segundos'], [[k, P._n(v, 1)] for k, v in tiempos.items()]),
    ]
    return '\n\n'.join(partes) + '\n'


def registro(evaluaciones, tiempos, huellas):
    lineas = ['LOG Fase 35B — análisis complementario EXPLORATORIO (no sustituye el resultado oficial)',
              f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}',
              f'Commit original: {COMMIT_ORIGINAL}',
              f'HEAD: {P._git("rev-parse", "HEAD").strip()}',
              f'Semilla: {C.SEMILLA}; tolerancia: {C.TOLERANCIA_SU_35B}; un solo proceso',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}']
    lineas += [f'SHA-256 {nombre}: {h}' for nombre, h in huellas.items()]
    for ev in evaluaciones:
        p = ev.parametros
        lineas.append(f'{p.nombre} ({p.n_permutaciones} permutaciones, q < {p.alfa}): relevantes {len(ev.medidas.relevantes)}, '
                      f'pares {len(ev.medidas.su_par)}, adaptado [{";".join(F.seleccionadas(ev.adaptado))}], '
                      f'estandar [{";".join(F.seleccionadas(ev.estandar))}]')
    lineas.append('Comprobaciones: E1 reproduce los archivos oficiales; dos corridas del último escenario coinciden exactamente.')
    lineas.append('Tiempo real (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in tiempos.items()))
    return '\n'.join(lineas) + '\n'


# --- Flujo --------------------------------------------------------------------------------

def correr(datos, rutas, oficial, escenarios=ESCENARIOS, huellas=None):
    """Calcula todo y comprueba antes de escribir: si algo falla, no queda ningún archivo."""
    inicio = time.perf_counter()
    validar_separacion(rutas)
    salida = P.Escritor(rutas)
    alfa_original = C.ALFA_Q_35B
    principal = P.escenario_principal(datos)
    evaluaciones, tiempos = [], {}
    for parametros in escenarios:
        ev = evaluar(principal, parametros)
        evaluaciones.append(ev)
        tiempos[parametros.nombre] = ev.segundos
        if parametros is escenarios[0]:
            comprobar_oficial(ev, oficial)
    repeticion = evaluar(principal, escenarios[-1])
    tiempos['repeticion_ultimo_escenario'] = repeticion.segundos
    if not iguales(evaluaciones[-1], repeticion):
        raise RuntimeError('Dos corridas del último escenario no coinciden.')
    if C.ALFA_Q_35B != alfa_original:
        raise RuntimeError('El umbral original no se restauró.')

    final = evaluaciones[-1]
    def con_escenario(funcion):
        tablas = [funcion(ev).assign(escenario=ev.parametros.nombre) for ev in evaluaciones]
        tablas = [t for t in tablas if len(t)]
        if not tablas:
            return pd.DataFrame(columns=['escenario'])
        unida = pd.concat(tablas, ignore_index=True)
        return unida[['escenario', *[c for c in unida.columns if c != 'escenario']]]

    salida.tabla(rutas.csv('su_objetivo'), tabla_objetivo(principal, final))
    salida.tabla(rutas.csv('su_pares'), con_escenario(tabla_pares))
    salida.tabla(rutas.csv('decisiones_fcbf'), con_escenario(tabla_decisiones))
    salida.tabla(rutas.csv('pares_no_eliminados_cobertura'), con_escenario(tabla_no_eliminados))
    salida.tabla(rutas.csv('comparacion_con_original'), tabla_comparacion(principal, evaluaciones))
    salida.tabla(rutas.csv('resumen_escenarios'), pd.DataFrame([fila_resumen(ev) for ev in evaluaciones]))
    tiempos['total'] = time.perf_counter() - inicio
    salida.texto(rutas.informe, informe(principal, evaluaciones, tiempos))
    salida.texto(rutas.log, registro(evaluaciones, tiempos, huellas or {}))
    return evaluaciones, tiempos


def correr_pruebas():
    """Las pruebas congeladas y las nuevas. Devuelve True si todas pasan."""
    nombres = ['preprocesamiento.test_entropia', 'preprocesamiento.test_complementario_35b']
    suite = unittest.defaultTestLoader.loadTestsFromNames(nombres)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite).wasSuccessful()


def construir_parser():
    parser = argparse.ArgumentParser(description='Fase 35B: análisis complementario exploratorio.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    return parser


def main():
    args = construir_parser().parse_args()
    if args.ejecutar and not args.autorizado_por_usuaria:
        sys.exit('La ejecución requiere --autorizado-por-usuaria.')
    problemas = estado_inicial()
    for problema in problemas:
        print(f'[FALLA] {problema}')
    if not correr_pruebas():
        sys.exit('Fallaron pruebas: no se ejecuta el análisis.')
    if problemas:
        sys.exit('El estado inicial tiene fallas: no se ejecuta el análisis.')
    validar_separacion(RUTAS_COMPLEMENTARIAS)
    if args.verificar:
        print('Pruebas y estado inicial correctos. No se calculó nada con los datos reales.')
        return
    huellas = {r.name: P.sha256(r) for r in (Path(__file__).resolve(), PROTOCOLO, PRUEBAS)}
    antes = P.manifiesto(archivos_vigilados())
    datos, _ = P.cargar()
    evaluaciones, tiempos = correr(datos, RUTAS_COMPLEMENTARIAS, P.RUTAS_REALES, huellas=huellas)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    for ev in evaluaciones:
        print(f'{ev.parametros.nombre}: {len(ev.medidas.relevantes)} relevantes; adaptado '
              f'{len(F.seleccionadas(ev.adaptado))}; estándar {len(F.seleccionadas(ev.estandar))}.')
    print(f'Total {tiempos["total"]:.1f} s. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
