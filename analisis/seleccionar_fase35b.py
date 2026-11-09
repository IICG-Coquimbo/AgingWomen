"""
Fase 35B (OB2): selección entrópica con SU y FCBF adaptado por cobertura.
Protocolo: analisis/protocolo_fase35b.md. Configuración: preprocesamiento/configuracion.py.

Uso (desde cualquier carpeta):
    python analisis/seleccionar_fase35b.py --respaldar     copia las entradas y resultados previos, con hashes
    python analisis/seleccionar_fase35b.py --verificar     verificación estructural; no calcula ninguna SU
    python analisis/seleccionar_fase35b.py --ejecutar --autorizado-por-usuaria

Solo --ejecutar calcula la selección, los remuestreos y las sensibilidades. Exige
el segundo indicador, un respaldo vigente y una verificación estructural sin fallas.
No ejecuta fases anteriores ni escribe fuera de los archivos declarados.
"""
import argparse
import csv
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from eda import variables as V
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E
from preprocesamiento import estabilidad as S
from preprocesamiento import fcbf as F

ANALISIS = V.RAIZ / 'analisis'
RESULTADOS = ANALISIS / 'resultados' / 'usuaria'
ANALITICO = V.RAIZ / 'datos' / 'analitico'
ENTRADA = ANALITICO / 'dataset_fase35.csv'
LIMPIO = V.LIMPIO_USUARIA / 'dataset_usuaria_limpio.csv'
RESPALDO = V.RAIZ / 'datos' / 'respaldos' / '2026-11-02_antes_35b'
FORMATO = f'%.{C.DECIMALES_35B}f'

NO_PREDICTORAS = ['participante_id', 'severo_mrs', 'mrs_total', 'severidad_mrs_4', 'imc_fue_imputado']
ARCHIVOS_RESULTADO = ['su_objetivo', 'su_pares', 'decisiones_fcbf', 'pares_no_eliminados_cobertura',
                      'estabilidad_fcbf', 'estabilidad_global', 'estabilidad_remuestreos', 'sensibilidad_fcbf']
# Los remuestreos guardados dependen de estos archivos: cualquier cambio invalida la caché.
ARCHIVOS_CALCULO = [ANALISIS / 'preprocesamiento' / n for n in ('configuracion.py', 'entropia.py', 'fcbf.py')]
# La ejecución real exige que todos estén en un commit, sin cambios pendientes.
PROTOCOLO = ANALISIS / 'protocolo_fase35b.md'
ARCHIVOS_CODIGO = [*ARCHIVOS_CALCULO, ANALISIS / 'preprocesamiento' / 'estabilidad.py',
                   ANALISIS / 'preprocesamiento' / 'test_entropia.py', ANALISIS / 'seleccionar_fase35b.py', PROTOCOLO]
ID_PRINCIPAL, ID_ESTABILIDAD, ID_DESCRIPTIVO = 0, 1, 90
ETIQUETA_VARIANTE = {'adaptado': 'FCBF adaptado por cobertura (selección definitiva)',
                     'estandar': 'FCBF estándar por cobertura (comparación)'}


# --- Rutas de salida: lista cerrada ------------------------------------------------------

@dataclass
class Rutas:
    resultados: Path
    figuras: Path
    informe: Path
    dataset: Path
    cache: Path
    log: Path

    def csv(self, nombre):
        return self.resultados / f'{nombre}.csv'

    def figura(self, nombre):
        return self.figuras / f'{nombre}.png'

    def declaradas(self):
        return {self.csv(n) for n in ARCHIVOS_RESULTADO} | {self.figura('su_por_variable'),
                                                            self.figura('estabilidad_seleccion'),
                                                            self.informe, self.dataset, self.log}


RUTAS_REALES = Rutas(RESULTADOS, ANALISIS / 'figuras' / 'seleccion_35b', ANALISIS / 'informe_seleccion_fase35b.md',
                     ANALITICO / 'dataset_fase35b.csv', ANALITICO / 'cache_35b',
                     RESULTADOS / 'log_seleccion_fase35b.txt')


class Escritor:
    """Solo escribe rutas declaradas y nunca sobrescribe un archivo que ya existe."""

    def __init__(self, rutas):
        self.permitidas = rutas.declaradas()

    def preparar(self, ruta):
        ruta = Path(ruta)
        if ruta not in self.permitidas:
            raise PermissionError(f'Ruta no declarada para la Fase 35B: {ruta}')
        if ruta.exists():
            raise FileExistsError(f'No se sobrescribe un archivo existente: {ruta}')
        ruta.parent.mkdir(parents=True, exist_ok=True)
        return ruta

    def tabla(self, ruta, df, formato=FORMATO):
        """`formato=None` conserva todos los decimales: el conjunto de datos no se redondea."""
        df.to_csv(self.preparar(ruta), index=False, encoding='utf-8-sig', float_format=formato)

    def texto(self, ruta, contenido):
        self.preparar(ruta).write_text(contenido, encoding='utf-8')


# --- Integridad --------------------------------------------------------------------------

def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def archivos_protegidos():
    """Entradas y productos de fases anteriores: no pueden cambiar en esta fase."""
    nuevos = RUTAS_REALES.declaradas()
    return sorted({ENTRADA, LIMPIO, V.LIMPIO_USUARIA / 'diccionario_variables.csv',
                   V.LIMPIO_USUARIA / 'excluidas.csv',
                   ANALISIS / 'informe_preprocesamiento_fase35.md', ANALISIS / 'preprocesar_fase35.py',
                   ANALISIS / 'preprocesamiento' / 'pasos.py',
                   *[r for r in RESULTADOS.glob('*') if r.is_file() and r not in nuevos]})


def manifiesto(rutas):
    return {str(r): sha256(r) for r in rutas}


def comparar_manifiestos(antes, despues):
    return sorted(r for r in set(antes) | set(despues) if antes.get(r) != despues.get(r))


def codigo_sin_congelar():
    """Archivos de código con cambios respecto del último commit. Si Git falla, no se da por congelado."""
    relativas = [str(r.relative_to(V.RAIZ)) for r in ARCHIVOS_CODIGO]
    r = subprocess.run(['git', 'status', '--porcelain', '--', *relativas], cwd=V.RAIZ, capture_output=True, text=True,
                       encoding='utf-8')
    return ['No se pudo consultar Git.'] if r.returncode else r.stdout.splitlines()


def huella_codigo():
    return hashlib.sha256(''.join(sha256(r) for r in ARCHIVOS_CALCULO).encode()).hexdigest()


def huella_cache(escenario, n_permutaciones):
    """Identifica el código, las bibliotecas, los parámetros y los datos de los remuestreos guardados."""
    import scipy

    h = hashlib.sha256()
    for parte in (huella_codigo(), np.__version__, scipy.__version__, n_permutaciones, C.SEMILLA, escenario.id_analisis,
                  escenario.modo, sorted(escenario.candidatas), sorted(escenario.laborales)):
        h.update(repr(parte).encode())
    for v in sorted(escenario.datos):
        h.update(v.encode())
        h.update(escenario.datos[v].tobytes())
    h.update(escenario.objetivo.tobytes())
    h.update(escenario.mascara.tobytes())
    return h.hexdigest()[:16]


def preparar_cache(rutas, huella):
    """Solo reutiliza la caché de esta misma huella. Una caché de otra versión detiene la fase: se retira a mano."""
    rutas.cache.mkdir(parents=True, exist_ok=True)
    otras = sorted(d.name for d in rutas.cache.iterdir() if d.name != huella)
    if otras:
        raise RuntimeError(f'La caché {rutas.cache} tiene resultados de otra versión ({", ".join(otras)}). '
                           'Revísela y retírela antes de continuar; no se reutiliza ni se borra sola.')
    carpeta = rutas.cache / huella
    carpeta.mkdir(exist_ok=True)
    return carpeta


def _git(*argumentos):
    return subprocess.run(['git', *argumentos], cwd=V.RAIZ, capture_output=True, text=True, encoding='utf-8').stdout


def manifiesto_respaldo():
    ruta = RESPALDO / 'MANIFIESTO_sha256.csv'
    if not ruta.exists():
        return None
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        return {str(V.RAIZ / fila['archivo']): fila['sha256'] for fila in csv.DictReader(f)}


def protocolo_conservado(registrado=None, actual=None):
    """El protocolo solo puede diferir de su copia respaldada por la sección 12, agregada al final."""
    registrado = registrado or RESPALDO / PROTOCOLO.relative_to(V.RAIZ)
    actual = actual or PROTOCOLO
    antes, ahora = (Path(r).read_bytes().replace(b'\r\n', b'\n') for r in (registrado, actual))
    if not ahora.startswith(antes):
        return False
    adicion = ahora[len(antes):].decode('utf-8')
    return adicion.startswith('\n## 12. Tolerancia numérica\n') and adicion.count('\n## ') == 1


def diferencias_con_respaldo(previo):
    """Hashes idénticos en todo, salvo el protocolo, que se comprueba con `protocolo_conservado`."""
    esperados = {r: h for r, h in previo.items() if r != str(PROTOCOLO)}
    distintos = comparar_manifiestos(esperados, manifiesto(archivos_protegidos()))
    return distintos + ([] if protocolo_conservado() else [str(PROTOCOLO)])


def respaldar():
    protegidos = [*archivos_protegidos(), PROTOCOLO]
    actual = manifiesto(protegidos)
    previo = manifiesto_respaldo()
    if previo is not None:
        distintos = diferencias_con_respaldo(previo)
        if distintos:
            raise SystemExit('El respaldo existente no coincide con los archivos actuales: ' + ', '.join(distintos))
        print(f'El respaldo ya existe y coincide: {RESPALDO.relative_to(V.RAIZ)} ({len(previo)} archivos).')
        return
    RESPALDO.mkdir(parents=True)
    with open(RESPALDO / 'MANIFIESTO_sha256.csv', 'w', encoding='utf-8-sig', newline='') as f:
        escritor = csv.writer(f)
        escritor.writerow(['archivo', 'sha256', 'bytes'])
        for r in protegidos:
            relativa = r.relative_to(V.RAIZ)
            destino = RESPALDO / relativa
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(r, destino)
            if sha256(destino) != actual[str(r)]:
                raise SystemExit(f'La copia no coincide con el original: {relativa}')
            escritor.writerow([str(relativa), actual[str(r)], r.stat().st_size])
    (RESPALDO / 'git_head.txt').write_text(_git('rev-parse', 'HEAD'), encoding='utf-8')
    (RESPALDO / 'git_status.txt').write_text(_git('status', '--porcelain'), encoding='utf-8')
    print(f'Respaldo creado: {RESPALDO.relative_to(V.RAIZ)} ({len(protegidos)} archivos, hashes comprobados).')


# --- Datos -------------------------------------------------------------------------------

@dataclass
class Datos:
    tabla: pd.DataFrame
    mascara: np.ndarray           # respuesta laboral real en ambas preguntas
    candidatas: list
    control: list
    pendientes: list
    laborales: list


def cargar():
    """Une dataset_fase35 con el conjunto limpio por participante_id, solo para identificar respuestas reales."""
    tabla = pd.read_csv(ENTRADA, encoding='utf-8-sig', dtype={'participante_id': str}, float_precision='round_trip')
    limpio = pd.read_csv(LIMPIO, encoding='utf-8-sig', dtype=str, usecols=['participante_id', 'mrs_completo',
                                                                          *C.LABORALES_35B])
    unido = tabla[['participante_id']].merge(limpio, on='participante_id', how='left', validate='one_to_one',
                                             indicator=True)
    predictoras = [c for c in tabla.columns if c not in NO_PREDICTORAS]
    excluidas = set(C.CONTROL_35B) | set(C.PENDIENTES_35B)
    candidatas = sorted(c for c in predictoras if c not in excluidas)
    mascara = unido[C.LABORALES_35B].notna().all(axis=1).to_numpy()
    return Datos(tabla, mascara, candidatas, list(C.CONTROL_35B), list(C.PENDIENTES_35B),
                 list(C.LABORALES_35B)), unido


def cortes_cuartiles(x):
    return np.unique(np.quantile(np.asarray(x, dtype=float), [0.25, 0.5, 0.75]))


def cortes_terciles(x):
    return np.unique(np.quantile(np.asarray(x, dtype=float), [1 / 3, 2 / 3]))


def _codigos(datos, candidatas, horas='cuartiles'):
    t, codigos = datos.tabla, {}
    for v in candidatas:
        if v == 'horas_sedentarismo' and horas == 'cuartiles':
            codigos[v] = E.tramos_cerrados_derecha(t[v], cortes_cuartiles(t[v]))
        elif v == 'horas_sedentarismo' and horas == 'terciles':
            codigos[v] = E.tramos_cerrados_derecha(t[v], cortes_terciles(t[v]))
        else:
            codigos[v] = E.codificar(t[v])
    return codigos


def escenario_principal(datos):
    return F.Escenario('Principal', ID_PRINCIPAL, _codigos(datos, datos.candidatas), E.codificar(datos.tabla['severo_mrs']),
                       datos.candidatas, set(datos.laborales), datos.mascara)


def escenarios_sensibilidad(datos):
    """Lista cerrada de la sección 8 del protocolo."""
    t, candidatas, laborales = datos.tabla, datos.candidatas, set(datos.laborales)
    objetivo, m = E.codificar(t['severo_mrs']), datos.mascara
    base = _codigos(datos, candidatas)
    trabajadoras = t['trabaja_actualmente'].to_numpy() == 1
    subconjunto = {v: x[m] for v, x in base.items()}
    return [
        F.Escenario('S1 horas en terciles', 11, _codigos(datos, candidatas, 'terciles'), objetivo, candidatas, laborales, m),
        F.Escenario('S1 horas en valores originales', 12, _codigos(datos, candidatas, 'originales'), objetivo, candidatas,
                    laborales, m),
        F.Escenario('S2 severidad en 4 clases', 20, base, E.codificar(t['severidad_mrs_4']), candidatas, laborales, m),
        F.Escenario('S3 laborales con las trabajadoras, incluidas las imputadas', 30, base, objetivo, candidatas, laborales,
                    trabajadoras),
        F.Escenario('S4 lista única con "no aplica" como categoría', 40, base, objetivo, candidatas, laborales, m,
                    F.LISTA_UNICA),
        F.Escenario('S5 FCBF completo con las respuestas laborales reales', 50, subconjunto, objetivo[m], candidatas,
                    laborales, m[m], F.LISTA_UNICA),
    ]


def _descriptivas(datos, n_permutaciones):
    """SU de control y pendientes: se informan, pero no entran a ninguna familia ni decisión."""
    t = datos.tabla
    y = E.codificar(t['severo_mrs'])
    filas = []

    def agregar(variable, grupo, x, mascara, nota, indice):
        rng = E.generador(ID_DESCRIPTIVO, 0, 0, indice)
        su, p = E.prueba_permutacion(y[mascara], x[mascara], n_permutaciones, rng)
        filas.append({'variable': variable, 'grupo': grupo, 'n': int(mascara.sum()), 'su': su, 'p': p, 'q': np.nan,
                      'relevante': '', 'nota': nota})

    todas = np.ones(len(t), dtype=bool)
    for i, v in enumerate(datos.control + datos.pendientes):
        grupo = 'pendiente' if v in datos.pendientes else 'control'
        if v == 'edad':
            x = E.tramos_cerrados_izquierda(t[v], C.CORTES_EDAD_35B)
        elif v == 'imc':
            x = E.tramos_cerrados_izquierda(t[v], C.CORTES_IMC_35B)
        else:
            x = E.codificar(t[v])
        agregar(v, grupo, x, todas, 'descriptiva; no decide', i)
        if v == 'imc':
            agregar(v, grupo, x, t['imc_fue_imputado'].to_numpy() == 0, 'descriptiva; solo IMC observado', 100 + i)
    return filas


# --- Ejecución ---------------------------------------------------------------------------

def _tabla_decisiones(decisiones, variante):
    filas = []
    for v in sorted(decisiones):
        d = decisiones[v]
        filas.append({'variante': variante, 'variable': v, 'etapa': d['etapa'], 'decision': d['decision'],
                      'eliminada_por': d['eliminada_por'], 'su_con_severidad': d['su_y'],
                      'su_eliminadora_con_severidad': d['su_z'], 'su_par': d['su_par'], 'q_par': d['q_par']})
    return filas


def _resumir_estabilidad(remuestreos, candidatas):
    por_variable, globales, detalle = [], [], []
    for variante in ('adaptado', 'estandar'):
        Z = np.array([[r[variante][v][0] == 'seleccionada' for v in candidatas] for r in remuestreos], dtype=int)
        indicadores = S.nogueira(Z)
        tamanos = Z.sum(axis=1)
        globales.append({'variante': variante, 'remuestreos': len(remuestreos), 'nogueira': indicadores['indice'],
                         'nogueira_ic95_inferior': indicadores['ic_inferior'],
                         'nogueira_ic95_superior': indicadores['ic_superior'], 'jaccard_promedio': S.jaccard_promedio(Z),
                         'tamano_medio': tamanos.mean(), 'tamano_minimo': int(tamanos.min()),
                         'tamano_maximo': int(tamanos.max())})
        for j, v in enumerate(candidatas):
            decisiones = [r[variante][v] for r in remuestreos]
            eliminadoras = pd.Series([d[1] for d in decisiones if d[0] == 'redundante'], dtype=object)
            pct = 100 * Z[:, j].mean()
            por_variable.append({
                'variante': variante, 'variable': v, 'pct_seleccionada': pct,
                'pct_no_relevante': 100 * np.mean([d[0] == 'no relevante' for d in decisiones]),
                'pct_redundante': 100 * np.mean([d[0] == 'redundante' for d in decisiones]),
                'eliminadora_mas_frecuente': eliminadoras.mode().sort_values().iloc[0] if len(eliminadoras) else '',
                'banda_descriptiva': S.banda(pct)})
        for r, fila in zip(remuestreos, Z):
            detalle.append({'variante': variante, 'remuestreo': r['remuestreo'], 'n_laboral': r['n_laboral'],
                            'n_seleccionadas': int(fila.sum()),
                            'seleccionadas': ';'.join(v for v, z in zip(candidatas, fila) if z)})
    return pd.DataFrame(por_variable), pd.DataFrame(globales), pd.DataFrame(detalle)


def leer_exacto(origen):
    """Lee un conjunto de datos sin perder precisión."""
    return pd.read_csv(origen, encoding='utf-8-sig', dtype={'participante_id': str}, float_precision='round_trip')


def controlar_seleccion(escenario, medidas, decisiones):
    """Controles de la sección 10 del protocolo: detienen la fase antes de escribir resultados."""
    m = int(escenario.mascara.sum())
    for v in escenario.candidatas:
        if v in escenario.laborales and medidas.n_objetivo[v] != m:
            raise RuntimeError(f'{v}: su relevancia no usa las {m} observaciones laborales.')
    for par, n in medidas.n_par.items():
        if escenario.laborales & set(par) and n != m:
            raise RuntimeError(f'{par}: el par no usa las {m} observaciones laborales.')
    for v, d in decisiones.items():
        if v not in escenario.laborales and d['eliminada_por'] in escenario.laborales:
            raise RuntimeError(f'La laboral {d["eliminada_por"]} eliminó a la no laboral {v}.')


def correr(datos, rutas, n_permutaciones, n_remuestreos, procesos):
    """Toda la fase. `rutas` y los tamaños son parámetros para poder probarla con datos inventados."""
    from joblib import Parallel, delayed

    inicio = time.perf_counter()
    salida = Escritor(rutas)
    for ruta in rutas.declaradas():
        if ruta.exists():
            raise FileExistsError(f'No se sobrescribe un archivo existente: {ruta}')
    principal = escenario_principal(datos)
    medidas = F.medir(principal, 0, n_permutaciones)
    adaptado = F.seleccionar(principal, medidas, True)
    estandar = F.seleccionar(principal, medidas, False)
    controlar_seleccion(principal, medidas, adaptado)
    controlar_seleccion(principal, medidas, estandar)
    tiempos = {'principal': time.perf_counter() - inicio}

    filas = [{'variable': v, 'grupo': 'laboral' if v in principal.laborales else 'no laboral',
              'n': medidas.n_objetivo[v], 'su': medidas.su_objetivo[v], 'p': medidas.p_objetivo[v],
              'q': medidas.q_objetivo[v], 'relevante': v in medidas.relevantes, 'nota': ''} for v in datos.candidatas]
    filas += [{'variable': v, 'grupo': 'no laboral', 'n': int(datos.mascara.sum()), 'su': s, 'p': np.nan, 'q': np.nan,
               'relevante': '', 'nota': 'SU recalculada con las observaciones laborales (Etapa 2)'}
              for v, s in medidas.su_objetivo_laboral.items() if v not in principal.laborales]
    su_objetivo = pd.DataFrame(filas + _descriptivas(datos, n_permutaciones))
    su_pares = pd.DataFrame(
        [{'variable_1': a, 'variable_2': b, 'n': medidas.n_par[(a, b)], 'su': medidas.su_par[(a, b)],
          'p': medidas.p_par[(a, b)], 'q': medidas.q_par[(a, b)], 'supera_azar': medidas.q_par[(a, b)] < C.ALFA_Q_35B}
         for a, b in sorted(medidas.su_par)],
        columns=['variable_1', 'variable_2', 'n', 'su', 'p', 'q', 'supera_azar'])
    decisiones = pd.DataFrame(_tabla_decisiones(adaptado, 'adaptado') + _tabla_decisiones(estandar, 'estandar'))
    no_eliminados = pd.DataFrame(F.pares_no_eliminados(principal, medidas, adaptado),
                                 columns=['laboral', 'no_laboral', 'su_par', 'q_par', 'su_laboral_severidad',
                                          'su_no_laboral_severidad', 'n'])

    # Estabilidad: se puede reanudar desde la caché de esta misma versión de código, datos y parámetros.
    t0 = time.perf_counter()
    muestra_estabilidad = F.Escenario('Estabilidad', ID_ESTABILIDAD, principal.datos, principal.objetivo,
                                      principal.candidatas, principal.laborales, principal.mascara)
    huella = huella_cache(muestra_estabilidad, n_permutaciones)
    cache = preparar_cache(rutas, huella)
    remuestreos = Parallel(n_jobs=procesos)(
        delayed(F.un_remuestreo)(muestra_estabilidad, i, n_permutaciones, str(cache)) for i in range(n_remuestreos))
    tiempos['remuestreos'] = time.perf_counter() - t0
    for i in range(min(3, n_remuestreos)):          # protocolo, sección 10: mismo resultado con un solo proceso
        if F.un_remuestreo(muestra_estabilidad, i, n_permutaciones) != remuestreos[i]:
            raise RuntimeError(f'El remuestreo {i} cambia con el número de procesos.')
    estabilidad, estabilidad_global, detalle = _resumir_estabilidad(remuestreos, datos.candidatas)

    # Sensibilidad: se informa, pero no modifica la lista seleccionada.
    t0 = time.perf_counter()
    final = F.seleccionadas(adaptado)
    sensibilidad = []
    for esc in escenarios_sensibilidad(datos):
        med = F.medir(esc, 0, n_permutaciones)
        for variante, exigir_q in (('adaptado', True), ('estandar', False)):
            lista = F.seleccionadas(F.seleccionar(esc, med, exigir_q))
            sensibilidad.append({'escenario': esc.nombre, 'regla': variante, 'n_relevantes': len(med.relevantes),
                                 'n_seleccionadas': len(lista), 'seleccionadas': ';'.join(lista),
                                 'entran': ';'.join(sorted(set(lista) - set(final))),
                                 'salen': ';'.join(sorted(set(final) - set(lista))),
                                 'jaccard_con_definitiva': S.jaccard(lista, final)})
    tiempos['sensibilidad'] = time.perf_counter() - t0
    sensibilidad = pd.DataFrame(sensibilidad)

    columnas = NO_PREDICTORAS + datos.control + final
    salida.tabla(rutas.dataset, datos.tabla[columnas], formato=None)
    if not leer_exacto(rutas.dataset).equals(datos.tabla[columnas].reset_index(drop=True)):
        raise RuntimeError('dataset_fase35b.csv no conserva exactamente los valores de la entrada.')
    for nombre, df in (('su_objetivo', su_objetivo), ('su_pares', su_pares), ('decisiones_fcbf', decisiones),
                       ('pares_no_eliminados_cobertura', no_eliminados), ('estabilidad_fcbf', estabilidad),
                       ('estabilidad_global', estabilidad_global), ('estabilidad_remuestreos', detalle),
                       ('sensibilidad_fcbf', sensibilidad)):
        salida.tabla(rutas.csv(nombre), df)
    _figuras(salida, rutas, su_objetivo, estabilidad)

    tiempos['total'] = time.perf_counter() - inicio
    resultado = dict(datos=datos, medidas=medidas, adaptado=adaptado, estandar=estandar, su_objetivo=su_objetivo,
                     no_eliminados=no_eliminados, estabilidad=estabilidad, estabilidad_global=estabilidad_global,
                     sensibilidad=sensibilidad, final=final, tiempos=tiempos, n_permutaciones=n_permutaciones,
                     n_remuestreos=n_remuestreos, procesos=procesos, huella=huella)
    salida.texto(rutas.informe, informe(resultado))
    salida.texto(rutas.log, registro(resultado))
    return resultado


def _figuras(salida, rutas, su_objetivo, estabilidad):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    azul, gris, tinta, tenue, grilla = '#1c5cab', '#898781', '#52514e', '#898781', '#e1e0d9'

    def barras(etiquetas, valores, colores, titulo, eje):
        fig, ax = plt.subplots(figsize=(8.5, max(3.0, 0.27 * len(valores) + 1.4)))
        ax.barh(range(len(valores)), valores, color=colores, height=0.62)
        ax.set_yticks(range(len(valores)), etiquetas, color=tinta, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel(eje, color=tinta)
        ax.set_title(titulo, loc='left', fontsize=12, fontweight='bold')
        ax.grid(axis='x', color=grilla, linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis='x', colors=tenue)
        ax.tick_params(axis='y', length=0)
        for lado in ('top', 'right', 'left'):
            ax.spines[lado].set_visible(False)
        ax.spines['bottom'].set_color(grilla)
        return fig, ax

    t = su_objetivo[(su_objetivo['nota'] == '')].sort_values(['su', 'variable'], ascending=[False, True])
    fig, ax = barras([V.etiqueta(v) for v in t['variable']], t['su'],
                     [azul if r is True or r == 'True' else gris for r in t['relevante']],
                     'SU de cada candidata con severo_mrs', 'Incertidumbre simétrica (SU)')
    ax.legend(handles=[Patch(color=azul, label='Relevante (q < 0,05)'), Patch(color=gris, label='No relevante')],
              frameon=False, loc='lower right')
    fig.tight_layout()
    fig.savefig(salida.preparar(rutas.figura('su_por_variable')), dpi=200)
    plt.close(fig)

    e = estabilidad[estabilidad['variante'] == 'adaptado'].sort_values(['pct_seleccionada', 'variable'],
                                                                       ascending=[False, True])
    fig, ax = barras([V.etiqueta(v) for v in e['variable']], e['pct_seleccionada'], azul,
                     'Selección en los remuestreos (FCBF adaptado)', '% de remuestreos en que queda seleccionada')
    ax.set_xlim(0, 100)
    fig.tight_layout()
    fig.savefig(salida.preparar(rutas.figura('estabilidad_seleccion')), dpi=200)
    plt.close(fig)


# --- Informe y registro ------------------------------------------------------------------

def _n(x, d=4):
    return '-' if pd.isna(x) else f'{x:.{d}f}'.replace('.', ',')


def _q(x):
    return '-' if pd.isna(x) else ('< 0,001' if x < 0.001 else _n(x, 3))


def _lista(variables):
    return ', '.join(V.etiqueta(v) for v in variables) or 'ninguna'


def _duracion(s):
    return f'{s / 60:.1f} min'.replace('.', ',')


def informe(r):
    from eda.informe import _tabla

    datos, final, g = r['datos'], r['final'], r['estabilidad_global'].set_index('variante')
    su = r['su_objetivo']
    cand = su[su['nota'] == ''].sort_values(['su', 'variable'], ascending=[False, True])
    desc = su[su['nota'].str.startswith('descriptiva')]
    adaptado, estandar = r['adaptado'], r['estandar']
    lista_estandar = F.seleccionadas(estandar)
    fila_decision = lambda v, d: [V.etiqueta(v), d['etapa'] or '-', d['decision'], (V.etiqueta(d['eliminada_por']) if d['eliminada_por'] else '-'),  # noqa: E731
                                  _n(d['su_y']), _n(d['su_par']), _q(d['q_par'])]
    est = r['estabilidad'][r['estabilidad']['variante'] == 'adaptado'].sort_values(['pct_seleccionada', 'variable'],
                                                                                   ascending=[False, True])
    sens = r['sensibilidad'][r['sensibilidad']['regla'] == 'adaptado']
    simuladas = [(v, {1: 'aumenta', -1: 'protege', 0: 'sin efecto'}[s]) for v, s, _, _ in C.PATRONES_SIMULACION
                 if v in datos.candidatas]
    out = [
        '# Fase 35B. Selección entrópica de variables',
        '',
        f'*Generado por `analisis/seleccionar_fase35b.py` el {datetime.now():%d-%m-%Y}. Protocolo: '
        '`analisis/protocolo_fase35b.md`. Este informe no interpreta causalidad.*',
        '',
        '## 1. Resultado',
        '',
        f'De las {len(datos.candidatas)} candidatas, **{len(final)} quedan seleccionadas** con el FCBF adaptado por '
        f'cobertura: {_lista(final)}.',
        '',
        f'Pasan además a la Fase 36, sin filtro, las {len(datos.control)} variables de control: {_lista(datos.control)}. '
        f'{_lista(datos.pendientes)} queda pendiente de consultar a la profesora y no pasa a la Fase 36.',
        '',
        '## 2. Las tres variantes',
        '',
        _tabla(['Variante', 'Personas', 'Regla de redundancia', 'Función', 'Seleccionadas'], [
            ['FCBF adaptado por cobertura', '529 y 287, en dos etapas', 'Con q < 0,05', '**Selección definitiva**', len(final)],
            ['FCBF estándar por cobertura', '529 y 287, en dos etapas', 'Sin exigir q < 0,05', 'Comparación', len(lista_estandar)],
            ['FCBF completo con n = 287 (S5)', '287 en todo, con una sola lista', 'Con q < 0,05', 'Sensibilidad',
             int(sens[sens['escenario'].str.startswith('S5')]['n_seleccionadas'].iloc[0])],
        ]),
        '',
        f'Las dos primeras comparten el filtro de relevancia. Diferencias entre ambas: entran con la estándar '
        f'{_lista(sorted(set(lista_estandar) - set(final)))}; salen con la estándar {_lista(sorted(set(final) - set(lista_estandar)))}.',
        '',
        '## 3. Relevancia de las candidatas',
        '',
        f'{r["n_permutaciones"]} permutaciones de la severidad, semilla {C.SEMILLA} y corrección de Benjamini-Hochberg '
        f'sobre {len(datos.candidatas)} pruebas. Relevante = q < 0,05.',
        '',
        _tabla(['Variable', 'Grupo', 'n', 'SU', 'p', 'q', 'Relevante'],
               [[V.etiqueta(f.variable), f.grupo, f.n, _n(f.su), _q(f.p), _q(f.q), 'sí' if f.relevante is True else 'no']
                for f in cand.itertuples()]),
        '',
        '![SU por variable](figuras/seleccion_35b/su_por_variable.png)',
        '',
        '**SU descriptivas (no deciden).** Variables de control y pendientes:',
        '',
        _tabla(['Variable', 'Grupo', 'n', 'SU', 'p', 'Nota'],
               [[V.etiqueta(f.variable), f.grupo, f.n, _n(f.su), _q(f.p), f.nota] for f in desc.itertuples()]),
        '',
        '## 4. Decisiones del FCBF adaptado por cobertura',
        '',
        _tabla(['Variable', 'Etapa', 'Decisión', 'Eliminada por', 'SU con severidad', 'SU del par', 'q del par'],
               [fila_decision(v, adaptado[v]) for v in sorted(adaptado, key=lambda x: (adaptado[x]['decision'], x))]),
        '',
        '**Pares laboral-no laboral que la regla de cobertura no permite eliminar.** Parecen redundantes entre las '
        'trabajadoras, pero la variable laboral no tiene datos para las demás participantes.',
        '',
        (_tabla(['Laboral', 'No laboral', 'SU del par', 'q del par', 'n'],
                [[V.etiqueta(f.laboral), V.etiqueta(f.no_laboral), _n(f.su_par), _q(f.q_par), f.n]
                 for f in r['no_eliminados'].itertuples()]) if len(r['no_eliminados']) else 'No hay pares en esta situación.'),
        '',
        '## 5. Estabilidad (complementaria)',
        '',
        f'{r["n_remuestreos"]} remuestreos bootstrap estratificados por `severo_mrs`, con {r["n_permutaciones"]} '
        f'permutaciones en cada uno. No modifica la selección. Las permutaciones tratan las filas repetidas como '
        'distintas, lo que puede favorecer la significancia, por lo que estos valores son descriptivos.',
        '',
        _tabla(['Variante', 'Índice de Nogueira', 'IC 95 %', 'Jaccard promedio', 'Tamaño medio', 'Mín.', 'Máx.'],
               [[ETIQUETA_VARIANTE[k], _n(g.loc[k, 'nogueira'], 3) if pd.notna(g.loc[k, 'nogueira']) else 'no calculable',
                 f'{_n(g.loc[k, "nogueira_ic95_inferior"], 3)} a {_n(g.loc[k, "nogueira_ic95_superior"], 3)}',
                 _n(g.loc[k, 'jaccard_promedio'], 3), _n(g.loc[k, 'tamano_medio'], 1), g.loc[k, 'tamano_minimo'],
                 g.loc[k, 'tamano_maximo']] for k in g.index]),
        '',
        _tabla(['Variable', '% seleccionada', '% no relevante', '% redundante', 'Eliminadora más frecuente', 'Banda'],
               [[V.etiqueta(f.variable), _n(f.pct_seleccionada, 1), _n(f.pct_no_relevante, 1), _n(f.pct_redundante, 1),
                 V.etiqueta(f.eliminadora_mas_frecuente) if isinstance(f.eliminadora_mas_frecuente, str) and f.eliminadora_mas_frecuente else '-',
                 f.banda_descriptiva] for f in est.itertuples()]),
        '',
        '![Estabilidad](figuras/seleccion_35b/estabilidad_seleccion.png)',
        '',
        '## 6. Sensibilidad (complementaria)',
        '',
        'Lista cerrada del protocolo, con la regla adaptada. No modifica la selección. El detalle con la regla estándar '
        'está en `resultados/usuaria/sensibilidad_fcbf.csv`.',
        '',
        _tabla(['Escenario', 'Relevantes', 'Seleccionadas', 'Entran', 'Salen', 'Jaccard'],
               [[f.escenario, f.n_relevantes, f.n_seleccionadas, _lista(f.entran.split(';')) if f.entran else '-',
                 _lista(f.salen.split(';')) if f.salen else '-', _n(f.jaccard_con_definitiva, 2)] for f in sens.itertuples()]),
        '',
        '## 7. Comparación con los efectos del simulador (descriptiva)',
        '',
        'Compara la selección con los efectos programados en la simulación. No es un descubrimiento sobre la población.',
        '',
        _tabla(['Variable', 'Efecto programado', '¿Seleccionada?'],
               [[V.etiqueta(v), e, 'sí' if v in final else 'no'] for v, e in simuladas]),
        '',
        '## 8. Advertencias y limitaciones',
        '',
        '- **Carácter sintético:** la selección refleja lo que generó el simulador, no evidencia sobre la población.',
        '- **Circularidad:** seleccionar por severidad puede hacer que los clústeres difieran en severidad por esa misma '
        'selección. Esa diferencia no es una confirmación independiente.',
        '- **Interpretación:** seleccionada no significa causal, y eliminada no significa irrelevante.',
        '- **Adaptaciones propias:** la prueba de azar entre predictoras y la regla de cobertura se apartan del FCBF original.',
        '- **Límite de la preespecificación:** ya se habían visto relaciones bivariadas con la severidad (34C y 34E), la SU '
        'de `prevision` y la SU del par laboral.',
        '- **Poblaciones distintas:** la SU laboral describe a trabajadoras y la no laboral a todas, y la Etapa 2 tiene '
        'menos potencia.',
        '- **Redundancia conservada:** puede quedar redundancia entre variables laborales y no laborales.',
        '- **`doble_carga`:** es función exacta de `trabaja_actualmente` y `cantidad_personas_cuida`. Los filtros por pares '
        'no detectan esa dependencia conjunta.',
        '- **`prevision`:** el diccionario de la 35A la sigue llamando "predictora". Está pendiente y no pasa a la Fase 36.',
        '- **Fase 37:** se mantiene la comparación de la segmentación con y sin edad.',
        '- **Límite de los valores p:** desde 23 variables relevantes, un par aislado no puede alcanzar q < 0,05, lo que '
        f'hace eliminar menos. En esta ejecución hay {len(r["medidas"].relevantes)} relevantes.',
        '- **Duplicados en el bootstrap:** las permutaciones tratan las filas repetidas como distintas, lo que puede '
        'favorecer la significancia en los remuestreos. Por eso la estabilidad es descriptiva y no un valor inferencial.',
    ]
    out += ['', '## 9. Tiempo de ejecución', '',
            f'Tiempo real: {_duracion(r["tiempos"]["total"])} con {r["procesos"]} procesos. Los tiempos estimados antes de '
            'ejecutar eran extrapolaciones de mediciones breves (cerca de 14 µs por SU).', '']
    return '\n'.join(out)


def registro(r):
    t = r['tiempos']
    return '\n'.join([
        'LOG Fase 35B — selección entrópica',
        f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}',
        f'Commit: {_git("rev-parse", "HEAD").strip()}',
        f'Huella de la caché: {r["huella"]}',
        f'Semilla: {C.SEMILLA}; permutaciones: {r["n_permutaciones"]}; remuestreos: {r["n_remuestreos"]}; procesos: {r["procesos"]}',
        f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}',
        f'Candidatas: {len(r["datos"].candidatas)}; relevantes: {len(r["medidas"].relevantes)}; seleccionadas: {len(r["final"])}',
        f'Seleccionadas: {", ".join(r["final"]) or "ninguna"}',
        f'Advertencia de valores p (23 o más relevantes): {"sí" if len(r["medidas"].relevantes) >= 23 else "no"}',
        'Tiempo real (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in t.items()),
        '',
    ])


# --- Verificación estructural (no calcula ninguna SU) ---------------------------------------

def verificar():
    datos, unido = cargar()
    t, m = datos.tabla, datos.mascara
    trabajadoras = t['trabaja_actualmente'].to_numpy() == 1
    predictoras = [c for c in t.columns if c not in NO_PREDICTORAS]
    prohibidas = set(predictoras) & set(C.PROHIBIDAS)
    limpio = unido.set_index('participante_id')
    controles = []

    def control(nombre, ok, detalle=''):
        controles.append((nombre, bool(ok), str(detalle)))

    control('Filas en dataset_fase35', len(t) == C.N_PARTICIPANTES_35B, len(t))
    control('participante_id sin repetidos', t['participante_id'].is_unique)
    control('Unión uno a uno: todas encontradas en el conjunto limpio', (unido['_merge'] == 'both').all(),
            (unido['_merge'] == 'both').sum())
    control('Todas con MRS completo', (unido['mrs_completo'] == '1').all())
    control('Objetivo binario', set(t['severo_mrs']) == {0, 1})
    severidad = sorted(t['severo_mrs'].value_counts().tolist(), reverse=True)
    control('Tamaños de los estratos del bootstrap: 281 y 248', severidad == [281, 248], severidad)
    control('Severidad en 4 clases completa (S2)', t['severidad_mrs_4'].notna().all() and t['severidad_mrs_4'].nunique() == 4,
            t['severidad_mrs_4'].nunique())
    control('Horas sentada con 14 valores originales (S1)', t['horas_sedentarismo'].nunique() == 14,
            t['horas_sedentarismo'].nunique())
    control('Objetivo coincide con el corte MRS >= 16', ((t['mrs_total'] >= C.CORTE_SEVERO).astype(int) == t['severo_mrs']).all())
    control('35 predictoras', len(predictoras) == C.N_PREDICTORAS_ESPERADAS, len(predictoras))
    control('30 candidatas', len(datos.candidatas) == C.N_CANDIDATAS_35B, len(datos.candidatas))
    control('4 de control y 1 pendiente presentes', set(C.CONTROL_35B + C.PENDIENTES_35B) <= set(predictoras))
    control('28 no laborales y 2 laborales', len(set(datos.candidatas) - set(C.LABORALES_35B)) == 28 and
            set(C.LABORALES_35B) <= set(datos.candidatas))
    control('Sin variables prohibidas ni exclusiones entre las predictoras', not prohibidas, ', '.join(prohibidas))
    control('Predictoras sin vacíos', not t[predictoras].isna().any().any())
    control(f'{C.N_TRABAJADORAS_35B} trabajadoras', trabajadoras.sum() == C.N_TRABAJADORAS_35B, trabajadoras.sum())
    control(f'{C.N_RESPUESTA_LABORAL_35B} con respuestas laborales reales', m.sum() == C.N_RESPUESTA_LABORAL_35B, m.sum())
    control('Toda respuesta laboral real es de una trabajadora', not (m & ~trabajadoras).any())
    vacios = [limpio[v].isna().to_numpy() & trabajadoras for v in C.LABORALES_35B]
    control('Las trabajadoras sin respuesta son las mismas en ambas preguntas', (vacios[0] == vacios[1]).all(),
            f'{int(vacios[0].sum())} y {int(vacios[1].sum())}')
    for v, x in zip(C.LABORALES_35B, vacios):
        originales = pd.to_numeric(limpio[v]).to_numpy()
        control(f'{v}: las 287 coinciden con el conjunto limpio', (originales[m] == t[v].to_numpy()[m]).all())
        control(f'{v}: las imputadas tienen la mediana 3', (t[v].to_numpy()[x] == 3).all())
        control(f'{v}: quienes no trabajan tienen 0 = no aplica', (t[v].to_numpy()[~trabajadoras] == C.NO_APLICA).all())
    control('IMC observado', (t['imc_fue_imputado'] == 0).sum() == C.N_IMC_OBSERVADO_35B, (t['imc_fue_imputado'] == 0).sum())
    conteo = lambda codigos, k: np.bincount(codigos, minlength=k).tolist()  # noqa: E731
    edad = conteo(E.tramos_cerrados_izquierda(t['edad'], C.CORTES_EDAD_35B) - 1, 6) if t['edad'].min() >= 36 else None
    control('Tramos de edad según el protocolo', edad == C.CONTEO_EDAD_35B, edad)
    imc = conteo(E.tramos_cerrados_izquierda(t['imc'], C.CORTES_IMC_35B), 6)
    control('Categorías de IMC según el protocolo', imc == C.CONTEO_IMC_35B, imc)
    cuartiles = cortes_cuartiles(t['horas_sedentarismo']).tolist()
    control('Cuartiles de horas según el protocolo', cuartiles == C.CUARTILES_HORAS_35B, cuartiles)
    horas = conteo(E.tramos_cerrados_derecha(t['horas_sedentarismo'], cuartiles), 4)
    control('Tramos de horas según el protocolo', horas == C.CONTEO_HORAS_35B, horas)
    control('Terciles de horas disponibles para S1', len(cortes_terciles(t['horas_sedentarismo'])) >= 1,
            cortes_terciles(t['horas_sedentarismo']).round(4).tolist())
    doble = (t['trabaja_actualmente'] == 1) & (t['cantidad_personas_cuida'] > 0)
    control('doble_carga = trabaja y cuida, sin excepciones', (doble.astype(int) == t['doble_carga']).all())
    control('Los valores se guardan sin pérdida de decimales', leer_exacto(io.StringIO(t.to_csv(index=False))).equals(t),
            f'máximo de decimales en IMC: {t["imc"].map(lambda x: len(repr(float(x)).split(".")[1])).max()}')

    # Integridad
    previo = manifiesto_respaldo()
    control('Respaldo creado', previo is not None, RESPALDO.relative_to(V.RAIZ))
    if previo is not None:
        distintos = diferencias_con_respaldo(previo)
        control('Hashes iguales al respaldo; protocolo solo con la sección 12 agregada', not distintos,
                ', '.join(distintos) or f'{len(previo) - 1} archivos idénticos y texto registrado del protocolo intacto')
    rutas_35a = ['analisis/resultados', 'analisis/figuras', 'analisis/informe_preprocesamiento_fase35.md',
                 'analisis/preprocesar_fase35.py', 'analisis/preprocesamiento/pasos.py']
    cambios = [l for l in _git('status', '--porcelain', '--', *rutas_35a).splitlines()]
    control('Git: sin cambios en resultados, figuras ni código de fases anteriores', not cambios, '; '.join(cambios))
    numstat = _git('diff', '--numstat', '--', 'analisis/preprocesamiento/configuracion.py').split()
    control('configuracion.py solo agrega líneas', not numstat or numstat[1] == '0', ' '.join(numstat[:2]))
    nucleos = os.cpu_count() or 0
    control(f'Al menos {C.N_PROCESOS_35B} núcleos', nucleos >= C.N_PROCESOS_35B, nucleos)
    existentes = [str(r) for r in RUTAS_REALES.declaradas() if r.exists()]
    control('Las salidas de la 35B aún no existen', not existentes, ', '.join(existentes))
    return controles


def imprimir(controles):
    for nombre, ok, detalle in controles:
        print(f'[{"OK" if ok else "FALLA"}] {nombre}' + (f': {detalle}' if detalle else ''))
    fallas = sum(1 for _, ok, _ in controles if not ok)
    print(f'{len(controles) - fallas} de {len(controles)} controles correctos.')
    return fallas


def main():
    parser = argparse.ArgumentParser(description='Fase 35B: selección entrópica.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--respaldar', action='store_true')
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    args = parser.parse_args()

    if args.respaldar:
        respaldar()
    elif args.verificar:
        fallas = imprimir(verificar())
        pendientes = codigo_sin_congelar()
        if pendientes:
            print(f'Aviso: {len(pendientes)} archivos de código sin commit: --ejecutar no correrá hasta congelarlos.')
        sys.exit(1 if fallas else 0)
    else:
        if not args.autorizado_por_usuaria:
            sys.exit('La ejecución real requiere --autorizado-por-usuaria.')
        pendientes = codigo_sin_congelar()
        if pendientes:
            sys.exit('El código no está congelado en un commit: ' + '; '.join(pendientes))
        if imprimir(verificar()):
            sys.exit('La verificación estructural tiene fallas: no se ejecuta la selección.')
        antes = manifiesto([*archivos_protegidos(), *ARCHIVOS_CODIGO])
        datos, _ = cargar()
        resultado = correr(datos, RUTAS_REALES, C.N_PERMUTACIONES_35B, C.N_REMUESTREOS_35B, C.N_PROCESOS_35B)
        cambiados = comparar_manifiestos(antes, manifiesto([*archivos_protegidos(), *ARCHIVOS_CODIGO]))
        if cambiados:
            sys.exit('Cambiaron archivos protegidos o de código: ' + ', '.join(cambiados))
        print(f'{len(resultado["final"])} seleccionadas de {len(datos.candidatas)}. Archivos protegidos sin cambios.')


if __name__ == '__main__':
    main()
