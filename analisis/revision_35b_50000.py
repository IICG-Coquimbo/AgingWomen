"""
Versión B de la revisión de la Fase 35B (reunión del 03-11-2026): extensión reproducible de 10.000 a 50.000 permutaciones.
Entropía de Shannon, información mutua, SU, Benjamini-Hochberg con q < 0,10 y FCBF informativo. Complementa a la versión A,
que no se modifica. Protocolo: analisis/reunion_2026-11-03/protocolo_revision_35b.md y adenda_50000_permutaciones.md.

Uso, desde analisis/:
    python revision_35b_50000.py --verificar     pruebas, estado, tamaños y reproducción exacta de la versión A
    python revision_35b_50000.py --ejecutar --autorizado-por-usuaria

Solo cambia el número de permutaciones. No elimina variables de la Fase 36 y no genera ningún dataset.
"""
import argparse
import io
import re
import sys
import time
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import complementario_cuidados as M
import complementario_fase35b as K
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E
from preprocesamiento import fcbf as F

N_BASE, N_TOTAL = 10000, 50000
INDICE_MC_B = 2                    # clave (1103, 0, 4, 2): sorteos de la incertidumbre de la versión B
ADENDA = R.CARPETA / 'adenda_50000_permutaciones.md'
SALIDA = R.CARPETA / 'permutaciones_50000'
PRUEBAS = P.ANALISIS / 'preprocesamiento' / 'test_revision_35b_50000.py'
ARCHIVOS_CSV = [*R.ARCHIVOS_CSV, 'extension_conteos']


@dataclass(frozen=True)
class RutasB:
    carpeta: Path

    def csv(self, nombre):
        return self.carpeta / f'{nombre}.csv'

    @property
    def informe(self):
        return self.carpeta / 'informe_revision_50000.md'

    @property
    def log(self):
        return self.carpeta / 'log_revision_50000.txt'

    def declaradas(self):
        return {self.csv(n) for n in ARCHIVOS_CSV} | {self.informe, self.log}


RUTAS_B = RutasB(SALIDA)


# --- Tablas: las mismas funciones para las dos versiones ------------------------------------------------------

def plan(n_permutaciones, nombre='R50'):
    """'R10' es el nombre con que la versión A guardó sus tablas."""
    return M.Plan(K.Parametros(nombre, n_permutaciones, R.ALFA, 'Revisión 03-11, q < 0,10'), M.OBSERVADAS, '')


def tablas_version(datos, poblacion, esc, ev, monte_carlo, anteriores):
    """Las tablas de una versión. Solo `ev` y `monte_carlo` dependen del número de permutaciones."""
    relevancia = R.tabla_relevancia(esc, ev)
    direccion, categorias = R.tabla_direccion(datos, esc)
    d = direccion.merge(relevancia[['variable', 'q']], on='variable')
    direccion['clase'] = [R.clasificar_factor(f.direccion, f.q, f.rho_q) for f in d.itertuples()]
    orientacion = pd.DataFrame([{'variable': v, 'tipo': e.tipo, 'mayor_valor': e.mayor_valor, 'clase_models': e.clase_models,
                                 'niveles': '; '.join(f'{k} = {t}' for k, t in e.niveles.items())} for v, e in sorted(R.ORIENTACION.items())])
    return {'poblaciones': pd.DataFrame(list(poblacion.conteos.items()), columns=['poblacion', 'n']),
            'orientacion_escalas': orientacion, 'shannon_componentes': R.tabla_shannon(esc), 'relevancia_34': relevancia,
            'incertidumbre_monte_carlo': monte_carlo(relevancia), 'pares_relevantes': M.tabla_pares(ev),
            'decisiones_fcbf': M.tabla_decisiones(ev), 'pares_no_eliminados': R.tabla_no_eliminados(ev),
            'su_todas_las_parejas': R.tabla_todas_las_parejas(esc), 'direccion_resumen': direccion, 'direccion_categorias': categorias,
            'comparacion_anteriores': R.tabla_comparacion(relevancia, anteriores),
            'sensibilidades': R.tabla_sensibilidades(datos, esc, poblacion, ev)}


def monte_carlo_a(n_base):
    return lambda relevancia: R.tabla_monte_carlo(relevancia, n_base)


def monte_carlo_b(n_total):
    """Método de la sección 7 del protocolo con la versión B. La regla de la versión A no se vuelve a aplicar aquí."""
    def calcular(relevancia):
        actual = R.incertidumbre_mc(relevancia['k'].to_numpy(), n_total, E.generador(R.ID_REVISION, 0, R.TIPO_MONTE_CARLO, INDICE_MC_B))
        t = pd.concat([relevancia[['variable', 'k', 'p', 'q']], actual], axis=1)
        t['cercana'] = R.es_cercana(t['q_mc_inferior'], t['q_mc_superior'])
        return t
    return calcular


# --- Comprobaciones: secciones 3 y 5 de la adenda --------------------------------------------------------------

def _texto_csv(df):
    return df.to_csv(index=False, float_format=P.FORMATO).replace('\r\n', '\n')


def diferencias_tablas(tablas, carpeta):
    """Tablas cuyo CSV difiere del archivo guardado, byte a byte salvo el fin de línea."""
    distintas = []
    for nombre, df in tablas.items():
        ruta = Path(carpeta) / f'{nombre}.csv'
        guardado = ruta.read_text(encoding='utf-8-sig') if ruta.exists() else None
        if guardado != _texto_csv(df):
            distintas.append(nombre)
    return distintas


def codigo_a_intacto(log, archivos):
    """Compara el SHA-256 de cada archivo con el registrado por la versión A."""
    registrados = dict(re.findall(r'SHA-256 (\S+): ([0-9a-f]{64})', Path(log).read_text(encoding='utf-8')))
    problemas = []
    for ruta in archivos:
        ruta = Path(ruta)
        if ruta.name not in registrados:
            problemas.append(f'{ruta.name} no está en el registro de la versión A')
        elif registrados[ruta.name] != P.sha256(ruta):
            problemas.append(f'{ruta.name} cambió desde la versión A')
    return problemas


def _k(p, n):
    return int(R.excedencias([p], n)[0])


def comprobar_anidamiento(esc, medidas, relevancia_a, pares_a, n_base=N_BASE, n_total=N_TOTAL):
    """Continúa cada generador tras n_base sorteos: debe dar el k guardado en A y el k de la versión B."""
    datos, y, indice = esc.datos(), esc.base.objetivo, esc.indice()
    k_a = dict(zip(relevancia_a['variable'], relevancia_a['k']))
    p_pares = {(f.variable_1, f.variable_2): f.p for f in pares_a.itertuples()}
    filas, errores = [], []

    def tramo(permutada, fija, tipo, clave, nombre, p_total, esperado_base=None, p_base_texto=None):
        rng = E.generador(R.ID_REVISION, 0, tipo, clave)
        _, p1 = E.prueba_permutacion(permutada, fija, n_base, rng)
        _, p2 = E.prueba_permutacion(permutada, fija, n_total - n_base, rng)
        k1, k2 = _k(p1, n_base), _k(p2, n_total - n_base)
        total = _k(p_total, n_total)
        if k1 + k2 != total:
            errores.append(f'{nombre}: {k1} + {k2} no es {total}')
        if esperado_base is not None and k1 != esperado_base:
            errores.append(f'{nombre}: k de los primeros sorteos {k1}, guardado {esperado_base}')
        if p_base_texto is not None and K._txt(p1) != K._txt(p_base_texto):
            errores.append(f'{nombre}: p de los primeros sorteos no coincide con el guardado')
        filas.append({'tipo': 'par' if tipo == F.TIPO_PAR else 'variable', 'nombre': nombre, 'k_primeros': k1, 'k_siguientes': k2, 'k_total': total})

    for v in sorted(indice):
        m = esc.mascara_de(v)
        tramo(y[m], datos[v][m], F.TIPO_RELEVANCIA, indice[v], v, medidas.p_objetivo[v], k_a.get(v))
    for (a, b), p_total in sorted(medidas.p_par.items()):
        m = esc.mascara_de(a, b)
        tramo(datos[a][m], datos[b][m], F.TIPO_PAR, indice[a] * F.FACTOR_PAR + indice[b], f'{a} | {b}', p_total,
              p_base_texto=p_pares.get((a, b)))
    return pd.DataFrame(filas), errores


def comprobar_su_iguales(medidas, relevancia_a):
    guardada = dict(zip(relevancia_a['variable'], relevancia_a['su']))
    return [f'SU de {v} difiere de la versión A' for v, s in sorted(medidas.su_objetivo.items()) if K._txt(s) != K._txt(guardada[v])]


# --- Informe de la versión B -------------------------------------------------------------------------------------

def informe(t, ev, tiempos):
    rel = t['relevancia_34'].sort_values(['q', 'p', 'variable'])
    mc = t['incertidumbre_monte_carlo'].sort_values(['q', 'variable'])
    dec, pares, dir_ = t['decisiones_fcbf'], t['pares_relevantes'], t['direccion_resumen'].merge(t['relevancia_34'][['variable', 'q']], on='variable')
    pv, s = (lambda x: P._n(x, 5)), (lambda x: P._n(x, 4))
    partes = [
        '# Revisión de la Fase 35B. Versión B: 50.000 permutaciones',
        f'*Generado por `analisis/revision_35b_50000.py` el {datetime.now():%d-%m-%Y}. Protocolo: `protocolo_revision_35b.md` y '
        '`adenda_50000_permutaciones.md`.*',
        '> **Análisis complementario de la versión A (10.000 permutaciones), que no se reemplaza.** Usa entropía de Shannon, información mutua y '
        'SU. Ninguna variable sale de la Fase 36. Datos sintéticos; ninguna asociación se interpreta como causal. La comparación de ambas '
        'versiones está en `informe_integrado/`.',
        '## 1. Las 34 variables', 'p = (1 + k) / 50.001; Benjamini-Hochberg sobre una familia de 34 pruebas; q < 0,10 exploratorio.',
        K._tabla_md(['Variable', 'Población', 'n', 'SU', 'k', 'p', 'q', 'q < 0,10', 'q < 0,05'],
                    [[f'`{f.variable}`', f.poblacion, f.n, s(f.su), f.k, pv(f.p), pv(f.q), 'sí' if f.q_bajo_0_10 else 'no', 'sí' if f.q_bajo_0_05 else 'no']
                     for f in rel.itertuples()]),
        '## 2. FCBF informativo', f'Pares evaluados: {len(pares)}. Rótulos descriptivos: no eliminan variables de la Fase 36.',
        K._tabla_md(['Variante', 'Variable', 'Etapa', 'Decisión', 'Redundante con', 'SU con severidad', 'SU del par', 'q del par'],
                    [[f.variante, f'`{f.variable}`', f.etapa or '-', f.decision, f'`{f.eliminada_por}`' if f.eliminada_por else '-',
                      s(f.su_con_severidad), s(f.su_par), pv(f.q_par)]
                     for f in dec[dec['decision'] != 'no relevante'].sort_values(['variante', 'su_con_severidad'], ascending=[True, False]).itertuples()]),
        '## 3. Pares evaluados',
        K._tabla_md(['Variable 1', 'Variable 2', 'n', 'SU', 'p', 'q'],
                    [[f'`{f.variable_1}`', f'`{f.variable_2}`', f.n, s(f.su), pv(f.p), pv(f.q)] for f in pares.itertuples()]) if len(pares) else 'No hay pares.',
        '## 4. Clasificación descriptiva',
        K._tabla_md(['Clase', 'Variable', 'Un valor mayor significa', 'ρ con MRS', 'Dirección', 'q SU', 'q ρ'],
                    [[f.clase, f'`{f.variable}`', f.mayor_valor, R._r(f.rho_mrs), f.direccion, pv(f.q), pv(f.rho_q)]
                     for f in dir_.sort_values(['clase', 'q']).itertuples()]),
        '## 5. Incertidumbre Monte Carlo',
        K._tabla_md(['Variable', 'k', 'p', 'EE de p', 'q', 'IC MC de q', 'P(q < 0,10)', 'Cercana a 0,10'],
                    [[f'`{f.variable}`', f.k, pv(f.p), pv(f.error_estandar_p), pv(f.q), f'{pv(f.q_mc_inferior)} a {pv(f.q_mc_superior)}',
                      P._n(f.prob_q_bajo_umbral, 3), 'sí' if f.cercana else 'no'] for f in mc.itertuples()]),
        '## 6. Sensibilidades, fuera de la familia',
        K._tabla_md(['Variable', 'Versión', 'n', 'SU', 'p', 'q al reemplazar', 'ρ con MRS'],
                    [[f'`{f.variable}`', f.version, f.n, s(f.su), pv(f.p), pv(f.q_al_reemplazar), R._r(f.rho_mrs)] for f in t['sensibilidades'].itertuples()]),
        '## 7. Tiempo de ejecución', K._tabla_md(['Etapa', 'Segundos'], [[k, P._n(v, 1)] for k, v in tiempos.items()]),
    ]
    return '\n\n'.join(partes) + '\n'


def registro(ev, cercanas, tiempos, huellas, n_total):
    m = ev.medidas
    lineas = [f'LOG revisión Fase 35B, versión B: entropía de Shannon, {n_total} permutaciones, COMPLEMENTARIO',
              f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}', f'HEAD: {P._git("rev-parse", "HEAD").strip()}',
              f'Semilla: SeedSequence({C.SEMILLA}, spawn_key=({R.ID_REVISION}, 0, tipo, indice)); tolerancia: {C.TOLERANCIA_SU_35B}; un solo proceso',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}',
              f'Variables: {len(m.su_objetivo)}; relevantes q<0,10: {len(m.relevantes)}; pares: {len(m.su_par)}', f'Relevantes: {";".join(m.relevantes)}',
              f'FCBF adaptado: {";".join(F.seleccionadas(ev.adaptado))}', f'FCBF estandar: {";".join(F.seleccionadas(ev.estandar))}',
              f'Cercanas a 0,10: {";".join(cercanas) or "ninguna"}',
              'Comprobaciones: la versión A se reproduce byte a byte; primeros sorteos iguales a A; k primeros + k siguientes = k total; '
              'SU igual; dos corridas idénticas.', 'Tiempo real (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in tiempos.items())]
    lineas += [f'SHA-256 {nombre}: {h}' for nombre, h in (huellas or {}).items()]
    return '\n'.join(lineas) + '\n'


# --- Flujo ------------------------------------------------------------------------------------------------------

def reproducir_a(datos, poblacion, carpeta_a, anteriores, n_base=N_BASE):
    """Recalcula la versión A completa y la compara con sus archivos."""
    esc = R.construir_escenario(datos, poblacion)
    ev = M.evaluar(esc, plan(n_base, 'R10'))
    return diferencias_tablas(tablas_version(datos, poblacion, esc, ev, monte_carlo_a(n_base), anteriores), carpeta_a)


def correr(datos, poblacion, rutas, carpeta_a, anteriores, n_base=N_BASE, n_total=N_TOTAL, huellas=None):
    """Calcula y comprueba todo antes de escribir: si algo falla, no queda ningún archivo."""
    inicio = time.perf_counter()
    M.validar_separacion(rutas)
    salida = P.Escritor(rutas)
    t0 = time.perf_counter()
    distintas = reproducir_a(datos, poblacion, carpeta_a, anteriores, n_base)
    if distintas:
        raise RuntimeError(f'La versión A no se reproduce: {distintas}')
    tiempos = {'reproduccion_version_a': time.perf_counter() - t0}
    esc = R.construir_escenario(datos, poblacion)
    alfa = C.ALFA_Q_35B
    ev = M.evaluar(esc, plan(n_total))
    repeticion = M.evaluar(esc, plan(n_total))
    tiempos.update(permutaciones=ev.segundos, repeticion=repeticion.segundos)
    if not M.iguales(ev, repeticion):
        raise RuntimeError('Dos corridas de la versión B no coinciden.')
    if C.ALFA_Q_35B != alfa:
        raise RuntimeError('El umbral original no se restauró.')
    leer = lambda n: pd.read_csv(Path(carpeta_a) / f'{n}.csv', encoding='utf-8-sig', keep_default_na=False)  # noqa: E731
    relevancia_a, pares_a = leer('relevancia_34'), leer('pares_relevantes')
    for problemas in (comprobar_su_iguales(ev.medidas, relevancia_a), R.comprobar_independiente(esc)):
        if problemas:
            raise RuntimeError('; '.join(problemas))
    t0 = time.perf_counter()
    conteos, errores = comprobar_anidamiento(esc, ev.medidas, relevancia_a, pares_a, n_base, n_total)
    tiempos['comprobacion_anidamiento'] = time.perf_counter() - t0
    if errores:
        raise RuntimeError('La extensión no conserva las permutaciones: ' + '; '.join(errores))
    tablas = tablas_version(datos, poblacion, esc, ev, monte_carlo_b(n_total), anteriores)
    tablas['extension_conteos'] = conteos
    # Lo que no depende de las permutaciones debe coincidir con la versión A.
    independientes = ['poblaciones', 'orientacion_escalas', 'shannon_componentes', 'su_todas_las_parejas', 'direccion_categorias']
    distintas = diferencias_tablas({n: tablas[n] for n in independientes}, carpeta_a)
    a_dir = pd.read_csv(Path(carpeta_a) / 'direccion_resumen.csv', encoding='utf-8-sig', keep_default_na=False, dtype=str)
    columnas = [c for c in a_dir.columns if c != 'clase']
    b_dir = pd.read_csv(io.StringIO(_texto_csv(tablas['direccion_resumen'])), keep_default_na=False, dtype=str)
    if not a_dir[columnas].equals(b_dir[columnas]):
        distintas.append('direccion_resumen')
    if distintas:
        raise RuntimeError(f'Tablas independientes de las permutaciones difieren de la versión A: {distintas}')
    cercanas = tablas['incertidumbre_monte_carlo'].query('cercana')['variable'].tolist()
    tiempos['total'] = time.perf_counter() - inicio
    texto, log = informe(tablas, ev, tiempos), registro(ev, cercanas, tiempos, huellas, n_total)
    for nombre, tabla in tablas.items():
        salida.tabla(rutas.csv(nombre), tabla)
    salida.texto(rutas.informe, texto)
    salida.texto(rutas.log, log)
    return ev, tablas, tiempos


def archivos_vigilados(carpeta_a=R.SALIDA):
    """Todo lo anterior, incluida la versión A y su código."""
    base = [Path(R.__file__).resolve(), R.PROTOCOLO, R.PRUEBAS, ADENDA, *Path(carpeta_a).glob('*')]
    word = list((P.ANALISIS / 'informes_fase35b').glob('*.docx'))
    return sorted({*R.archivos_vigilados(), *base, *word})


def correr_pruebas():
    nombres = ['preprocesamiento.test_entropia', 'preprocesamiento.test_complementario_35b', 'preprocesamiento.test_complementario_cuidados',
               'preprocesamiento.test_revision_35b', 'preprocesamiento.test_revision_35b_50000']
    suite = unittest.defaultTestLoader.loadTestsFromNames(nombres)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite).wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description='Revisión de la Fase 35B, versión B: 50.000 permutaciones.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    args = parser.parse_args()
    if args.ejecutar and not args.autorizado_por_usuaria:
        sys.exit('La ejecución requiere --autorizado-por-usuaria.')
    problemas = K.estado_inicial()
    if not correr_pruebas():
        sys.exit('Fallaron pruebas: no se ejecuta el análisis.')
    datos, poblacion, de_datos = R.comprobar_datos_reales()
    problemas += de_datos
    problemas += codigo_a_intacto(R.RUTAS_REVISION.log, [Path(R.__file__).resolve(), R.PROTOCOLO, R.PRUEBAS])
    M.validar_separacion(RUTAS_B)
    anteriores = R.leer_anteriores()
    problemas += [f'La versión A no se reproduce: {t}' for t in reproducir_a(datos, poblacion, R.SALIDA, anteriores)]
    for problema in problemas:
        print(f'[FALLA] {problema}')
    if problemas:
        sys.exit('El estado inicial tiene fallas: no se ejecuta el análisis.')
    print(f'34 variables; general 529, laboral {int(datos.mascara.sum())}, cuidadoras {int(poblacion.observada.sum())}. '
          'La versión A se reproduce byte a byte.')
    if args.verificar:
        print('Pruebas, estado, tamaños y versión A correctos. No se calcularon 50.000 permutaciones.')
        return
    huellas = {r.name: P.sha256(r) for r in (Path(__file__).resolve(), ADENDA, PRUEBAS)}
    antes = P.manifiesto(archivos_vigilados())
    ev, _, tiempos = correr(datos, poblacion, RUTAS_B, R.SALIDA, anteriores, huellas=huellas)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Relevantes q<0,10: {len(ev.medidas.relevantes)}. Total {tiempos["total"]:.1f} s. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
