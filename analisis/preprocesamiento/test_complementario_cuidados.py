"""
Pruebas de la versión complementaria del módulo de cuidados.

Usan datos inventados, salvo `PruebasDatosReales`, que solo cuenta poblaciones y compara hashes: con los datos
reales no calculan SU, permutaciones ni selección, y nunca leen la versión verdadera del simulador.
Uso, desde analisis/: python -m unittest preprocesamiento.test_complementario_cuidados
"""
import contextlib
import functools
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd
from scipy import stats

import complementario_cuidados as M
import complementario_fase35b as K
import seleccionar_fase35b as P
from limpieza import reglas as R

from . import configuracion as C
from . import entropia as E
from . import fcbf as F
from .test_entropia import datos_inventados, escenario_ficticio

S = M.SOBRECARGA
PEQUENOS = (M.Plan(K.Parametros('C3', 199, 0.05, 'prueba'), M.OBSERVADAS, 'E3'),
            M.Plan(K.Parametros('C4', 199, 0.10, 'prueba'), M.OBSERVADAS, 'E4'),
            M.Plan(K.Parametros('S3', 199, 0.05, 'prueba'), M.CUIDADORAS, 'E3'),
            M.Plan(K.Parametros('S4', 199, 0.10, 'prueba'), M.CUIDADORAS, 'E4'))
TODO_RELEVANTE = M.Plan(K.Parametros('T', 99, 1.1, 'prueba'), M.OBSERVADAS, 'E4')


def datos_cuidados(n=240, semilla=7):
    d = datos_inventados(n, semilla)
    rng = np.random.default_rng(semilla + 1)
    t = d.tabla.copy()
    t['cantidad_personas_cuida'] = rng.integers(0, 4, n)
    t['doble_carga'] = ((t['trabaja_actualmente'] == 1) & (t['cantidad_personas_cuida'] > 0)).astype(int)
    return P.Datos(t, d.mascara, sorted([*d.candidatas, 'cantidad_personas_cuida', 'doble_carga']), d.control, d.pendientes,
                   d.laborales)


def poblacion_cuidados(datos, semilla=11):
    t, rng = datos.tabla, np.random.default_rng(semilla)
    cuida = t['cantidad_personas_cuida'].to_numpy() > 0
    x = np.clip(rng.integers(1, 4, len(t)) + 2 * t['severo_mrs'].to_numpy(), 1, 5).astype(float)
    return M.Poblacion(np.where(cuida, x, np.nan), cuida, cuida & (rng.random(len(t)) > 0.1), {'todas': len(t)})


def escenario(datos=None, nombre=M.OBSERVADAS):
    datos = datos or datos_cuidados()
    return M.escenario_cuidados(datos, poblacion_cuidados(datos), nombre)


def escribir_referencia(carpeta, datos, n_permutaciones=199):
    """Archivos con el formato del análisis complementario anterior."""
    principal = P.escenario_principal(datos)
    evs = [K.evaluar(principal, K.Parametros(nombre, n_permutaciones, alfa, 'prueba'))
           for nombre, alfa in (('E1', 0.05), ('E3', 0.05), ('E4', 0.10))]
    rutas = K.RutasComplementarias(Path(carpeta))
    Path(carpeta).mkdir(parents=True, exist_ok=True)
    K.tabla_comparacion(principal, evs).to_csv(rutas.csv('comparacion_con_original'), index=False, encoding='utf-8-sig',
                                               float_format=P.FORMATO)
    pares = pd.concat([K.tabla_pares(ev).assign(escenario=ev.parametros.nombre) for ev in evs], ignore_index=True)
    pares.to_csv(rutas.csv('su_pares'), index=False, encoding='utf-8-sig', float_format=P.FORMATO)
    return rutas


def marcos(filas):
    """Tablas limpio y sucio escritas a mano. Cada fila: id, cuida y sobrecarga en ambas; opcionales el resto."""
    limpio, sucio = [], []
    for f in filas:
        limpio.append({'participante_id': f['id'], 'cuida_otras_personas': f['cuida'], 'trabaja_actualmente': f.get('trabaja', 'False'),
                       S: f.get('sob'), **{c: None for c in C.LABORALES_35B}})
        sucio.append({'participante_id': f['id'], 'cuida_otras_personas': f.get('cuida_sucio', f['cuida']),
                      'trabaja_actualmente': f.get('trabaja_sucio', f.get('trabaja', 'False')), S: f.get('sob_sucio', f.get('sob')),
                      **{c: f.get('seccion') for c in R.TRABAJO}})
    return pd.DataFrame(limpio, dtype=object), pd.DataFrame(sucio, dtype=object)


def identificar(filas, doble=None, sucio_extra=None):
    limpio, sucio = marcos(filas)
    if sucio_extra is not None:
        sucio = pd.concat([sucio, sucio_extra], ignore_index=True)
    ids = [f['id'] for f in filas]
    return M.identificar_poblacion(ids, limpio, sucio, np.zeros(len(ids), dtype=bool),
                                   np.zeros(len(ids), dtype=int) if doble is None else doble)


def medidas_etapa3(su_obj, su_par, q_par=None, su_z=None, su_s=None, relevantes=None):
    claves = {tuple(sorted(k)): v for k, v in su_par.items()}
    q = {k: 0.001 for k in claves}
    q.update({tuple(sorted(k)): v for k, v in (q_par or {}).items()})
    relevantes = sorted(su_obj if relevantes is None else relevantes)
    return M.MedidasCuidados(su_obj, {v: 100 for v in su_obj}, {v: 0.001 for v in su_obj}, {v: 0.001 for v in su_obj}, relevantes,
                             su_par=claves, n_par={k: 100 for k in claves}, p_par={k: 0.001 for k in claves}, q_par=q,
                             su_otra_etapa3=su_z or {}, su_sobrecarga_etapa3=su_s or {})


def esc_ficticio(candidatas, laborales=()):
    return SimpleNamespace(base=escenario_ficticio(candidatas, laborales))


@functools.lru_cache(maxsize=1)
def reales():
    """Datos reales, sin calcular ninguna SU."""
    datos, _ = P.cargar()
    return datos, M.cargar_poblacion(datos)


class PruebasDatosReales(unittest.TestCase):
    """Solo cuentan personas y comparan hashes."""

    def test_tamanos_de_las_poblaciones(self):
        datos, pob = reales()
        m = datos.mascara
        self.assertEqual(len(datos.tabla), 529)
        self.assertEqual(int(m.sum()), 287)
        self.assertEqual(int(pob.observada.sum()), 239)
        self.assertEqual(int((pob.observada & m).sum()), 130)
        self.assertEqual(int(pob.cuidadora.sum()), 251)
        self.assertEqual(int((pob.cuidadora & m).sum()), 137)
        M.controlar_tamanos(pob.conteos)

    def test_mascaras_del_escenario_dan_los_tamanos(self):
        datos, pob = reales()
        esc = M.escenario_cuidados(datos, pob, M.OBSERVADAS)
        lab = C.LABORALES_35B[0]
        no_lab = next(v for v in datos.candidatas if v not in C.LABORALES_35B)
        self.assertEqual(int(esc.mascara_de(no_lab).sum()), 529)
        self.assertEqual(int(esc.mascara_de(lab).sum()), 287)
        self.assertEqual(int(esc.mascara_de(S).sum()), 239)
        self.assertEqual(int(esc.mascara_de(no_lab, S).sum()), 239)
        self.assertEqual(int(esc.mascara_de(lab, S).sum()), 130)
        self.assertEqual(int(esc.mascara_de(lab, no_lab).sum()), 287)
        self.assertEqual(int(M.escenario_cuidados(datos, pob, M.CUIDADORAS).mascara_de(lab, S).sum()), 137)

    def test_las_239_son_realmente_observadas(self):
        """Se recalcula sin usar el programa: cuida SI en el limpio, respuesta 1-5 en el sucio e idéntica en el limpio."""
        datos, pob = reales()
        ids = datos.tabla['participante_id']
        limpio = pd.read_csv(P.LIMPIO, encoding='utf-8-sig', dtype=str).set_index('participante_id').loc[ids]
        sucio = pd.read_csv(M.SUCIO, encoding='utf-8-sig', dtype=str).drop_duplicates('participante_id').set_index('participante_id').loc[ids]
        original = pd.to_numeric(sucio[S].str.strip(), errors='coerce')
        esperado = (limpio['cuida_otras_personas'] == 'SI') & original.isin([1, 2, 3, 4, 5])
        self.assertTrue((esperado.to_numpy() == pob.observada).all())
        self.assertEqual(int(esperado.sum()), 239)
        self.assertTrue((pd.to_numeric(limpio[S])[esperado] == original[esperado]).all())

    def test_ninguna_de_las_239_depende_de_imputacion_de_cuida_o_sobrecarga(self):
        _, pob = reales()
        self.assertEqual(pob.conteos['cuida_imputada_en_observadas'], 0)
        self.assertEqual(pob.conteos['cuida_deducida_en_observadas'], 3)
        self.assertEqual(pob.conteos['sobrecarga_imputada'], 12)
        self.assertTrue((pob.valores[pob.cuidadora & ~pob.observada] == 3).all())    # las 12 tienen la mediana imputada

    def test_problemas_de_imputacion_documentados(self):
        _, pob = reales()
        c = pob.conteos
        self.assertEqual((c['doble_con_trabaja_imputada'], c['cuida_imputada_no'], c['trabaja_imputada']), (10, 21, 22))
        self.assertEqual((c['laborales_observadas_en_287'], c['laborales_observadas_en_sobrecarga_y_laboral']), (263, 122))
        texto = M.PROTOCOLO.read_text(encoding='utf-8')
        for frase in ('10 registros con `doble_carga` = 1', '21 respuestas vacías', '263 tienen ambas', 'solo por la versión verdadera'):
            self.assertIn(frase, texto)

    def test_no_aplica_queda_vacio_y_sin_ceros(self):
        datos, pob = reales()
        self.assertTrue(np.isnan(pob.valores[~pob.cuidadora]).all())
        self.assertEqual(int((~pob.cuidadora).sum()), 278)
        self.assertFalse((pob.valores == 0).any())
        esc = M.escenario_cuidados(datos, pob, M.OBSERVADAS)
        self.assertEqual(int(np.isnan(esc.sobrecarga).sum()), 529 - 239)
        self.assertNotIn(S, datos.tabla.columns)

    def test_candidatas_reales_sin_cambios(self):
        datos, _ = reales()
        self.assertEqual(M.comprobar_candidatas(datos), [])
        self.assertEqual(len(datos.candidatas), 30)
        self.assertIn('doble_carga', datos.candidatas)
        self.assertIn('cantidad_personas_cuida', datos.candidatas)

    def test_indices_reales_no_se_mueven(self):
        datos, pob = reales()
        esc = M.escenario_cuidados(datos, pob, M.OBSERVADAS)
        original = {v: i for i, v in enumerate(sorted(datos.candidatas))}
        indice = esc.indice()
        self.assertEqual({v: indice[v] for v in datos.candidatas}, original)
        self.assertEqual(indice[S], 30)
        self.assertEqual(len(set(indice.values())), 31)
        insertado = F.Escenario('x', 0, {}, np.array([]), [*datos.candidatas, S], set(), np.array([], dtype=bool)).indice()
        movidos = {v for v in datos.candidatas if insertado[v] != original[v]}
        self.assertEqual(movidos, {'tabaco_frecuencia', 'tiene_actividad_sexual', 'tiene_pareja', 'usa_medicamentos_presion',
                                   'vasos_agua_dia'})

    def test_familia_real_tiene_31_sin_calcular_su(self):
        """Las pruebas están simuladas: no se usa ningún dato para decidir."""
        datos, pob = reales()
        esc = M.escenario_cuidados(datos, pob, M.OBSERVADAS)
        with mock.patch.object(E, 'prueba_permutacion', return_value=(0.0, 1.0)) as simulada, \
                mock.patch.object(E, 'su', side_effect=AssertionError('no debe calcular SU')), \
                mock.patch.object(E, 'benjamini_hochberg', wraps=E.benjamini_hochberg) as bh:
            medidas = M.medir(esc, 1)
        self.assertEqual(simulada.call_count, 31)
        self.assertEqual(len(bh.call_args_list[0].args[0]), 31)
        self.assertEqual(len(medidas.q_objetivo), 31)

    def test_verificar_no_calcula_ni_modifica(self):
        previo = P.manifiesto(M.archivos_vigilados())
        existia = M.CARPETA.exists()
        with mock.patch.object(E, 'prueba_permutacion', side_effect=AssertionError('no debe permutar')), \
                mock.patch.object(E, 'su', side_effect=AssertionError('no debe calcular SU')):
            _, _, problemas = M.comprobar_datos_reales()
        self.assertEqual(problemas, [])
        self.assertEqual(P.comparar_manifiestos(previo, P.manifiesto(M.archivos_vigilados())), [])
        self.assertEqual(M.CARPETA.exists(), existia)

    def test_archivos_vigilados_cubren_lo_protegido(self):
        vigilados = {Path(r).resolve() for r in M.archivos_vigilados()}
        for ruta in (P.ENTRADA, P.LIMPIO, M.SUCIO, P.RUTAS_REALES.dataset, P.RUTAS_REALES.csv('su_objetivo'),
                     K.RUTAS_COMPLEMENTARIAS.csv('comparacion_con_original'), K.PROTOCOLO, P.PROTOCOLO,
                     P.ANALISIS / 'preprocesamiento' / 'fcbf.py', K.INFORME_WORD):
            self.assertIn(Path(ruta).resolve(), vigilados, ruta)

    def test_codigo_congelado_y_respaldo_intactos(self):
        self.assertEqual(P.codigo_sin_congelar(), [])
        self.assertEqual(P.diferencias_con_respaldo(P.manifiesto_respaldo()), [])


class PruebasIdentificacion(unittest.TestCase):
    FILAS = [
        {'id': 'a', 'cuida': 'SI', 'sob': '4'},                                                     # observada
        {'id': 'b', 'cuida': 'SI', 'sob': '3', 'sob_sucio': None},                                  # imputada
        {'id': 'c', 'cuida': 'SI', 'sob': '3', 'sob_sucio': 'sin dato'},                            # centinela
        {'id': 'd', 'cuida': 'SI', 'sob': '3', 'sob_sucio': '99'},                                  # fuera de escala
        {'id': 'e', 'cuida': 'NO', 'sob': None, 'sob_sucio': '5'},                                  # respondió sin cuidar
        {'id': 'f', 'cuida': 'SI', 'sob': '2', 'cuida_sucio': None},                                # cuida deducida
        {'id': 'g', 'cuida': 'NO', 'sob': None, 'cuida_sucio': None},                               # cuida imputada
        {'id': 'h', 'cuida': 'SI', 'sob': '5', 'sob_sucio': ' 5 ', 'cuida_sucio': ' s '},           # con espacios
        {'id': 'i', 'cuida': 'NO', 'sob': None},                                                    # no cuida
    ]

    def test_clasifica_cada_caso(self):
        pob = identificar(self.FILAS)
        self.assertEqual(list(pob.observada), [True, False, False, False, False, True, False, True, False])
        self.assertEqual(list(pob.cuidadora), [True, True, True, True, False, True, False, True, False])
        c = pob.conteos
        self.assertEqual((c['sobrecarga_observada'], c['sobrecarga_imputada'], c['cuidadoras']), (3, 3, 6))
        self.assertEqual((c['cuida_imputada_no'], c['cuida_deducida'], c['cuida_deducida_en_observadas']), (1, 1, 1))
        self.assertEqual(c['cuida_imputada_en_observadas'], 0)
        self.assertEqual(c['sobrecarga_borrada_por_condicional'], 1)

    def test_un_valor_imputado_nunca_es_observado(self):
        pob = identificar([{'id': 'x', 'cuida': 'SI', 'sob': '3', 'sob_sucio': v} for v in (None,)]
                          + [{'id': 'y', 'cuida': 'SI', 'sob': '4'}])
        self.assertEqual(list(pob.observada), [False, True])

    def test_respuesta_distinta_entre_sucio_y_limpio_detiene(self):
        with self.assertRaisesRegex(RuntimeError, 'difiere'):
            identificar([{'id': 'x', 'cuida': 'SI', 'sob': '3', 'sob_sucio': '4'}])

    def test_sobrecarga_sin_cuidar_detiene(self):
        with self.assertRaisesRegex(RuntimeError, 'no cuidan'):
            identificar([{'id': 'x', 'cuida': 'NO', 'sob': '3'}])

    def test_cero_en_el_limpio_detiene(self):
        with self.assertRaisesRegex(RuntimeError, 'no cuidan'):
            identificar([{'id': 'x', 'cuida': 'NO', 'sob': '0'}])
        with self.assertRaisesRegex(RuntimeError, 'fuera de la escala'):
            identificar([{'id': 'x', 'cuida': 'SI', 'sob': '0'}])

    def test_cuidadora_sin_valor_detiene(self):
        with self.assertRaisesRegex(RuntimeError, 'sin sobrecarga'):
            identificar([{'id': 'x', 'cuida': 'SI', 'sob': None}])

    def test_repetido_en_conflicto_detiene_y_sin_conflicto_pasa(self):
        filas = [{'id': 'x', 'cuida': 'SI', 'sob': '3'}]
        _, sucio = marcos(filas)
        identificar(filas, sucio_extra=sucio)
        otro = sucio.copy()
        otro[S] = '4'
        with self.assertRaisesRegex(RuntimeError, 'discrepa'):
            identificar(filas, sucio_extra=otro)

    def test_participante_ausente_detiene(self):
        limpio, sucio = marcos([{'id': 'x', 'cuida': 'SI', 'sob': '3'}])
        with self.assertRaisesRegex(RuntimeError, 'Faltan'):
            M.identificar_poblacion(['x'], limpio, sucio[sucio['participante_id'] != 'x'], [False], [0])

    def test_doble_carga_dependiente_de_trabajo_imputado(self):
        filas = [{'id': 'a', 'cuida': 'SI', 'sob': '3', 'trabaja': 'True', 'trabaja_sucio': None},                    # imputada
                 {'id': 'b', 'cuida': 'SI', 'sob': '3', 'trabaja': 'True', 'trabaja_sucio': None, 'seccion': '2'},    # deducida
                 {'id': 'c', 'cuida': 'SI', 'sob': '3', 'trabaja': 'True'},                                           # respondida
                 {'id': 'd', 'cuida': 'NO', 'trabaja': 'True', 'trabaja_sucio': None}]                                # imputada, sin doble
        c = identificar(filas, doble=[1, 1, 1, 0]).conteos
        self.assertEqual(c['trabaja_imputada'], 2)
        self.assertEqual(c['doble_con_trabaja_imputada'], 1)

    def test_control_de_tamanos_detiene_si_cambia_alguno(self):
        M.controlar_tamanos(dict(M.TAMANOS_ESPERADOS))
        self.assertEqual([M.TAMANOS_ESPERADOS[k] for k in ('todas', 'laboral', 'sobrecarga_observada', 'sobrecarga_y_laboral')],
                         [529, 287, 239, 130])
        for clave in M.TAMANOS_ESPERADOS:
            conteos = dict(M.TAMANOS_ESPERADOS)
            conteos[clave] += 1
            with self.assertRaisesRegex(RuntimeError, 'tamaños', msg=clave):
                M.controlar_tamanos(conteos)


class PruebasNoAplica(unittest.TestCase):
    def setUp(self):
        self.datos = datos_cuidados()
        self.esc = escenario(self.datos)

    def _crear(self, x, m=None):
        return M.EscenarioCuidados(self.esc.base, x, self.esc.poblacion if m is None else m)

    def test_rechaza_cero_fuera_de_la_poblacion(self):
        x = self.esc.sobrecarga.copy()
        x[~self.esc.poblacion] = 0
        with self.assertRaisesRegex(ValueError, 'no aplica no es cero'):
            self._crear(x)

    def test_rechaza_cualquier_valor_fuera_de_la_poblacion(self):
        x = self.esc.sobrecarga.copy()
        x[np.flatnonzero(~self.esc.poblacion)[0]] = 3
        with self.assertRaisesRegex(ValueError, 'no aplica no es cero'):
            self._crear(x)

    def test_rechaza_cero_y_vacio_dentro_de_la_poblacion(self):
        i = np.flatnonzero(self.esc.poblacion)[0]
        for valor in (0, np.nan, 6):
            x = self.esc.sobrecarga.copy()
            x[i] = valor
            with self.assertRaisesRegex(ValueError, 'escala 1 a 5', msg=valor):
                self._crear(x)

    def test_las_pruebas_nunca_reciben_no_aplica_ni_cero(self):
        vistos = []
        original = E.prueba_permutacion

        def espia(permutada, fija, n, rng):
            for arreglo in (permutada, fija):
                if np.asarray(arreglo).dtype.kind == 'f':
                    vistos.append(np.asarray(arreglo))
            return original(permutada, fija, n, rng)

        with mock.patch.object(E, 'prueba_permutacion', side_effect=espia), K.umbral(1.1):
            M.medir(self.esc, 19)
        self.assertTrue(vistos)
        for arreglo in vistos:
            self.assertFalse(np.isnan(arreglo).any())
            self.assertTrue(np.isin(arreglo, M.ESCALA).all())

    def test_su_propia_difiere_de_la_que_daria_codificar_cero(self):
        with K.umbral(0.05):
            m = M.medir(self.esc, 19)
        y = self.esc.base.objetivo
        con_ceros = E.su(y, np.nan_to_num(self.esc.sobrecarga))
        propia = E.su(y[self.esc.poblacion], self.esc.sobrecarga[self.esc.poblacion])
        self.assertEqual(m.su_objetivo[S], propia)
        self.assertNotEqual(m.su_objetivo[S], con_ceros)
        self.assertEqual(m.n_objetivo[S], int(self.esc.poblacion.sum()))

    def test_promedios_por_nivel_solo_incluyen_la_poblacion(self):
        t = M.tabla_por_nivel(self.datos, self.esc)
        todas = t[t['condicion'] == 'todas']
        self.assertEqual(todas['n'].sum(), int(self.esc.poblacion.sum()))
        self.assertTrue(set(t['nivel']) <= set(M.ESCALA))

    def test_fila_con_ceros_rotulada_como_referencia(self):
        t = M.tabla_relacion(self.datos, self.esc)
        self.assertEqual(set(t['poblacion']), {'población de la sobrecarga', 'todas, con 0 si no aplica (solo referencia)'})
        self.assertEqual(set(t[t['poblacion'].str.contains('referencia')]['n']), {len(self.datos.tabla)})

    def test_detecta_sobrecarga_agregada_al_conjunto_analitico(self):
        datos = datos_cuidados()
        datos.tabla[S] = 0
        self.assertTrue(any('no debe tener un valor' in x for x in M.comprobar_candidatas(datos)))

    def test_sobrecarga_no_puede_ser_candidata_de_las_etapas_previas(self):
        base = self.esc.base
        otra = F.Escenario(base.nombre, base.id_analisis, base.datos, base.objetivo, [*base.candidatas, S], base.laborales, base.mascara)
        with self.assertRaisesRegex(ValueError, 'etapas 1 y 2'):
            M.EscenarioCuidados(otra, self.esc.sobrecarga, self.esc.poblacion)


class PruebasSemillas(unittest.TestCase):
    def setUp(self):
        self.datos = datos_cuidados()
        self.esc = escenario(self.datos)
        self.base = self.esc.base

    def test_indices_de_las_candidatas_y_sobrecarga(self):
        self.assertEqual({v: self.esc.indice()[v] for v in self.base.candidatas}, self.base.indice())
        self.assertEqual(self.esc.indice()[S], M.INDICE_SOBRECARGA)
        self.assertEqual(M.INDICE_SOBRECARGA, 30)

    def test_mas_de_30_candidatas_detiene(self):
        base = self.base
        muchas = [f'v{i:02d}' for i in range(31)]
        otra = F.Escenario('x', 0, base.datos, base.objetivo, muchas, set(), base.mascara)
        with self.assertRaisesRegex(ValueError, 'índice'):
            M.EscenarioCuidados(otra, self.esc.sobrecarga, self.esc.poblacion)

    def test_claves_de_semilla_conservadas_y_sin_colisiones(self):
        registro = {}

        def captura(clave, llamadas, escenario_):
            with mock.patch.object(E, 'generador', wraps=E.generador) as espia, K.umbral(1.1):
                llamadas(escenario_)
            registro[clave] = [c.args for c in espia.call_args_list]

        captura('original', lambda e: F.medir(e, 0, 9), self.base)
        captura('nueva', lambda e: M.medir(e, 9), self.esc)
        self.assertTrue(set(registro['original']) < set(registro['nueva']))
        self.assertEqual(len(registro['nueva']), len(set(registro['nueva'])))
        self.assertIn((0, 0, F.TIPO_RELEVANCIA, 30), registro['nueva'])
        self.assertEqual(sum(1 for c in registro['nueva'] if c[2] == F.TIPO_RELEVANCIA), len(self.base.candidatas) + 1)

    def test_las_30_reproducen_exactamente_fcbf_medir(self):
        with K.umbral(1.1):
            original = F.medir(self.base, 0, 199)
            nueva = M.medir(self.esc, 199)
        for campo in ('su_objetivo', 'p_objetivo', 'n_objetivo'):
            parte = {k: v for k, v in getattr(nueva, campo).items() if k != S}
            self.assertEqual(parte, getattr(original, campo), campo)
        for campo in ('su_par', 'p_par', 'n_par'):
            parte = {k: v for k, v in getattr(nueva, campo).items() if S not in k}
            self.assertEqual(parte, getattr(original, campo), campo)
        self.assertEqual(nueva.su_objetivo_laboral, original.su_objetivo_laboral)

    def test_mismos_p_con_el_umbral_habitual(self):
        with K.umbral(0.05):
            original = F.medir(self.base, 0, 199)
            nueva = M.medir(self.esc, 199)
        self.assertEqual({k: v for k, v in nueva.p_objetivo.items() if k != S}, original.p_objetivo)

    def test_otros_valores_de_sobrecarga_no_mueven_a_las_30(self):
        x = self.esc.sobrecarga.copy()
        x[self.esc.poblacion] = 6 - x[self.esc.poblacion]
        rng = np.random.default_rng(5)
        x[self.esc.poblacion] = rng.permutation(x[self.esc.poblacion])
        otro = M.EscenarioCuidados(self.base, x, self.esc.poblacion)
        a, b = M.medir(self.esc, 99), M.medir(otro, 99)
        self.assertEqual({k: v for k, v in a.p_objetivo.items() if k != S}, {k: v for k, v in b.p_objetivo.items() if k != S})

    def test_otra_poblacion_no_mueve_a_las_30(self):
        a = M.medir(self.esc, 99)
        b = M.medir(escenario(self.datos, M.CUIDADORAS), 99)
        self.assertEqual({k: v for k, v in a.p_objetivo.items() if k != S}, {k: v for k, v in b.p_objetivo.items() if k != S})

    def test_dos_corridas_coinciden_y_se_detecta_una_diferencia(self):
        a, b = M.evaluar(self.esc, PEQUENOS[1]), M.evaluar(self.esc, PEQUENOS[1])
        self.assertTrue(M.iguales(a, b))
        b.medidas.p_objetivo[S] += 1e-15
        self.assertFalse(M.iguales(a, b))

    def test_iguales_detecta_cambio_en_la_decision_de_sobrecarga(self):
        a, b = M.evaluar(self.esc, PEQUENOS[1]), M.evaluar(self.esc, PEQUENOS[1])
        b.adaptado[S] = {**b.adaptado[S], 'decision': 'otra'}
        self.assertFalse(M.iguales(a, b))


class PruebasFamilia(unittest.TestCase):
    def setUp(self):
        self.esc = escenario()
        self.variables = sorted([*self.esc.base.candidatas, S])

    def _medir_con_p(self, valores, alfa=0.05):
        iterador = iter(valores)
        with mock.patch.object(E, 'prueba_permutacion', side_effect=lambda *a, **k: (0.1, next(iterador, 0.5))), K.umbral(alfa):
            return M.medir(self.esc, 9)

    def test_bh_recibe_todas_las_candidatas_incluida_sobrecarga(self):
        with mock.patch.object(E, 'benjamini_hochberg', wraps=E.benjamini_hochberg) as bh:
            M.medir(self.esc, 19)
        self.assertEqual(len(bh.call_args_list[0].args[0]), len(self.esc.base.candidatas) + 1)

    def test_q_son_los_de_la_familia_completa(self):
        p = np.linspace(0.001, 0.9, len(self.variables))
        m = self._medir_con_p(p)
        esperado = stats.false_discovery_control(p, method='bh')
        self.assertEqual([m.q_objetivo[v] for v in self.variables], list(map(float, esperado)))

    def test_q_de_sobrecarga_no_viene_de_una_familia_propia(self):
        p = np.full(len(self.variables), 0.5)
        p[self.variables.index(S)] = 0.02
        m = self._medir_con_p(p)
        self.assertAlmostEqual(m.q_objetivo[S], 0.02 * len(self.variables), places=12)
        self.assertNotIn(S, m.relevantes)

    def test_relevancia_estricta(self):
        p = np.full(len(self.variables), 0.9)
        p[self.variables.index(S)] = 0.1 / len(self.variables)
        self.assertNotIn(S, self._medir_con_p(p, alfa=0.10).relevantes)
        p[self.variables.index(S)] = 0.0999 / len(self.variables)
        self.assertIn(S, self._medir_con_p(p, alfa=0.10).relevantes)

    def test_q_con_30_separa_el_efecto_de_la_familia(self):
        p = np.linspace(0.001, 0.9, len(self.variables))
        m = self._medir_con_p(p)
        q30 = M.q_familia_30(m)
        self.assertNotIn(S, q30)
        solo = [m.p_objetivo[v] for v in sorted(q30)]
        self.assertEqual([q30[v] for v in sorted(q30)], list(map(float, stats.false_discovery_control(solo, method='bh'))))
        ev = SimpleNamespace(medidas=m, plan=PEQUENOS[1])
        tabla = M.tabla_efecto_familia(ev)
        self.assertEqual(len(tabla), len(q30))
        self.assertTrue((tabla['q_familia_31'] >= tabla['q_familia_30'] - 1e-15).all())

    def test_control_detecta_familia_incompleta(self):
        m = M.medir(self.esc, 19)
        decisiones = M.seleccionar(self.esc, m, True)
        m.q_objetivo.pop(next(v for v in m.q_objetivo if v != S))
        with self.assertRaisesRegex(RuntimeError, 'familia'):
            M.controlar_etapa3(self.esc, m, decisiones)

    def test_pares_en_una_sola_familia(self):
        with mock.patch.object(E, 'benjamini_hochberg', wraps=E.benjamini_hochberg) as bh, K.umbral(1.1):
            m = M.medir(self.esc, 9)
        self.assertEqual(bh.call_count, 2)
        n = len(self.variables)
        self.assertEqual(len(bh.call_args_list[1].args[0]), n * (n - 1) // 2)
        self.assertEqual(len(m.q_par), n * (n - 1) // 2)


class PruebasEtapa3(unittest.TestCase):
    """Medidas escritas a mano: comprueban la regla, sin azar."""

    ESC = esc_ficticio(['A', 'B'])
    BASE_PARES = {('A', 'B'): 0.0001}
    BASE_Q = {('A', 'B'): 0.9}

    def _decidir(self, su_a=0.05, su_b=0.04, su_par_a=0.03, q_a=0.01, su_z_a=0.05, su_s_a=0.02, exigir_q=True, su_par_b=0.0,
                 su_z_b=0.0, su_s_b=0.02, q_b=0.9):
        m = medidas_etapa3({'A': su_a, 'B': su_b, S: 0.02}, {**self.BASE_PARES, ('A', S): su_par_a, ('B', S): su_par_b},
                           {**self.BASE_Q, ('A', S): q_a, ('B', S): q_b}, {'A': su_z_a, 'B': su_z_b}, {'A': su_s_a, 'B': su_s_b})
        return M.seleccionar(self.ESC, m, exigir_q)

    def test_elimina_si_se_cumplen_todas_las_condiciones(self):
        d = self._decidir()[S]
        self.assertEqual((d['decision'], d['eliminada_por'], d['etapa']), ('redundante', 'A', M.ETAPA_CUIDADORAS))

    def test_no_elimina_si_z_es_mas_debil_en_la_poblacion_comun(self):
        """Z más fuerte con todas (0,05), pero más débil entre cuidadoras (0,01): la comparación usa la población común."""
        self.assertEqual(self._decidir(su_a=0.05, su_z_a=0.01)[S]['decision'], 'seleccionada')

    def test_elimina_si_z_es_mas_debil_con_todas_pero_mas_fuerte_en_la_comun(self):
        d = self._decidir(su_a=0.001, su_z_a=0.05, su_b=0.04)[S]
        self.assertEqual((d['decision'], d['eliminada_por']), ('redundante', 'A'))

    def test_no_elimina_si_el_par_no_alcanza_la_su(self):
        self.assertEqual(self._decidir(su_par_a=0.019)[S]['decision'], 'seleccionada')

    def test_q_del_par_estricto_en_la_variante_adaptada(self):
        self.assertEqual(self._decidir(q_a=0.05)[S]['decision'], 'seleccionada')
        self.assertEqual(self._decidir(q_a=0.05 - 1e-13)[S]['decision'], 'redundante')

    def test_la_variante_estandar_no_exige_q(self):
        self.assertEqual(self._decidir(q_a=0.9, exigir_q=False)[S]['decision'], 'redundante')

    def test_tolerancia_igual_a_la_original(self):
        self.assertEqual(self._decidir(su_par_a=0.02 - 5e-13)[S]['decision'], 'redundante')
        self.assertEqual(self._decidir(su_par_a=0.02 - 5e-12)[S]['decision'], 'seleccionada')
        self.assertEqual(self._decidir(su_z_a=0.02 - 5e-13)[S]['decision'], 'redundante')
        self.assertEqual(self._decidir(su_z_a=0.02 - 5e-12)[S]['decision'], 'seleccionada')

    def test_elige_la_eliminadora_de_mayor_su_y_desempata_alfabetico(self):
        d = self._decidir(su_z_a=0.05, su_z_b=0.06, su_par_b=0.03, q_b=0.01)[S]
        self.assertEqual(d['eliminada_por'], 'B')
        d = self._decidir(su_z_a=0.05, su_z_b=0.05, su_par_b=0.03, q_b=0.01)[S]
        self.assertEqual(d['eliminada_por'], 'A')

    def test_una_variable_ya_eliminada_no_puede_eliminarla(self):
        m = medidas_etapa3({'A': 0.05, 'B': 0.04, S: 0.02}, {('A', 'B'): 0.5, ('A', S): 0.0, ('B', S): 0.9},
                           {('A', 'B'): 0.001, ('A', S): 0.9, ('B', S): 0.001}, {'A': 0.0, 'B': 0.9}, {'A': 0.02, 'B': 0.02})
        d = M.seleccionar(self.ESC, m, True)
        self.assertEqual(d['B']['decision'], 'redundante')
        self.assertEqual(d[S]['decision'], 'seleccionada')

    def test_no_relevante_no_pasa_por_la_etapa(self):
        m = medidas_etapa3({'A': 0.05, 'B': 0.04, S: 0.02}, self.BASE_PARES, self.BASE_Q, relevantes=['A', 'B'])
        d = M.seleccionar(self.ESC, m, True)[S]
        self.assertEqual((d['decision'], d['etapa']), ('no relevante', ''))

    def test_las_comparaciones_usan_la_poblacion_comun(self):
        esc = escenario()
        with K.umbral(1.1):
            m = M.medir(esc, 19)
        y = esc.base.objetivo
        for z in ('frutas_dia', 'lugar_trabajo_comprensivo'):
            k = esc.mascara_de(z, S)
            self.assertEqual(m.su_otra_etapa3[z], E.su(esc.base.datos[z][k], y[k]))
            self.assertEqual(m.su_sobrecarga_etapa3[z], E.su(esc.sobrecarga[k], y[k]))
            self.assertEqual(m.n_par[F._clave(z, S)], int(k.sum()))
        self.assertEqual(m.n_par[F._clave('frutas_dia', S)], int(esc.poblacion.sum()))
        self.assertEqual(m.n_par[F._clave('lugar_trabajo_comprensivo', S)], int((esc.poblacion & esc.base.mascara).sum()))
        self.assertLess((esc.poblacion & esc.base.mascara).sum(), esc.poblacion.sum())

    def test_control_detecta_par_con_otra_poblacion(self):
        esc = escenario()
        with K.umbral(1.1):
            m = M.medir(esc, 9)
        decisiones = M.seleccionar(esc, m, True)
        m.n_par[F._clave('frutas_dia', S)] += 1
        with self.assertRaisesRegex(RuntimeError, 'población común'):
            M.controlar_etapa3(esc, m, decisiones)

    def test_control_detecta_relevancia_con_otra_poblacion(self):
        esc = escenario()
        m = M.medir(esc, 9)
        decisiones = M.seleccionar(esc, m, True)
        m.n_objetivo[S] += 1
        with self.assertRaisesRegex(RuntimeError, 'su población'):
            M.controlar_etapa3(esc, m, decisiones)


class PruebasNoElimina(unittest.TestCase):
    """La sobrecarga no modifica las decisiones de las etapas anteriores."""

    def setUp(self):
        self.datos = datos_cuidados()
        base = escenario(self.datos)
        m = base.poblacion
        x = np.where(m, np.where(base.base.objetivo == 1, 5.0, 1.0), np.nan)     # copia de la severidad: SU máxima
        self.esc = M.EscenarioCuidados(base.base, x, m)

    def test_decisiones_anteriores_iguales_a_la_funcion_congelada(self):
        with K.umbral(1.1):
            medidas = M.medir(self.esc, 99)
            original = F.medir(self.esc.base, 0, 99)
            for exigir_q in (True, False):
                nuevas = M.seleccionar(self.esc, medidas, exigir_q)
                congeladas = F.seleccionar(self.esc.base, original, exigir_q)
                for v, d in congeladas.items():
                    self.assertEqual((nuevas[v]['decision'], nuevas[v]['eliminada_por'], nuevas[v]['etapa']),
                                     (d['decision'], d['eliminada_por'], d['etapa']), v)

    def test_nunca_figura_como_eliminadora(self):
        with K.umbral(1.1):
            medidas = M.medir(self.esc, 99)
            for exigir_q in (True, False):
                decisiones = M.seleccionar(self.esc, medidas, exigir_q)
                self.assertNotIn(S, {d['eliminada_por'] for d in decisiones.values()})
                self.assertEqual(decisiones[S]['decision'], 'seleccionada')

    def test_lo_que_habria_eliminado_solo_se_informa(self):
        with K.umbral(1.1):
            medidas = M.medir(self.esc, 99)
            decisiones = M.seleccionar(self.esc, medidas, True)
            filas = M.pares_no_eliminados_sobrecarga(medidas, decisiones)
        eliminables = {f['eliminable'] for f in filas}
        self.assertIn('copia_senal', eliminables)
        for v in eliminables:
            self.assertEqual(decisiones[v]['decision'], 'seleccionada')

    def test_sin_relevancia_no_se_informa_nada(self):
        with K.umbral(0.05), mock.patch.object(E, 'prueba_permutacion', return_value=(0.0, 1.0)):
            medidas = M.medir(self.esc, 9)
            self.assertEqual(M.pares_no_eliminados_sobrecarga(medidas, M.seleccionar(self.esc, medidas, True)), [])

    def test_control_detiene_si_elimina_a_otra(self):
        with K.umbral(1.1):
            medidas = M.medir(self.esc, 9)
        decisiones = M.seleccionar(self.esc, medidas, True)
        decisiones['ruido'] = {**decisiones['ruido'], 'decision': 'redundante', 'eliminada_por': S}
        with self.assertRaisesRegex(RuntimeError, 'eliminó'):
            M.controlar_etapa3(self.esc, medidas, decisiones)

    def test_control_detiene_si_se_evalua_en_otra_etapa(self):
        with K.umbral(1.1):
            medidas = M.medir(self.esc, 9)
        decisiones = M.seleccionar(self.esc, medidas, True)
        decisiones[S] = {**decisiones[S], 'etapa': 'no laboral'}
        with self.assertRaisesRegex(RuntimeError, 'Etapa 3'):
            M.controlar_etapa3(self.esc, medidas, decisiones)

    def test_vista_para_funciones_congeladas_no_contiene_sobrecarga_y_conserva_q(self):
        with K.umbral(1.1):
            medidas = M.medir(self.esc, 9)
        vista = M._sin_sobrecarga(medidas)
        self.assertNotIn(S, vista.relevantes)
        self.assertNotIn(S, vista.q_objetivo)
        self.assertFalse(any(S in par for par in vista.q_par))
        for par, q in vista.q_par.items():
            self.assertEqual(q, medidas.q_par[par])

    def test_sin_garantia_de_seleccion_para_las_variables_de_cuidado(self):
        esc = escenario(self.datos)
        with mock.patch.object(E, 'prueba_permutacion', return_value=(0.0, 1.0)), K.umbral(0.10):
            ev = M.evaluar(esc, PEQUENOS[1])
        for v in ('doble_carga', 'cantidad_personas_cuida', S):
            self.assertEqual(ev.adaptado[v]['decision'], 'no relevante', v)
            self.assertEqual(ev.estandar[v]['decision'], 'no relevante', v)
        self.assertEqual(F.seleccionadas(ev.adaptado), [])

    def test_doble_carga_puede_quedar_redundante_si_el_metodo_lo_decide(self):
        """La regla es la misma para todas: no hay excepción para las variables de cuidado."""
        m = medidas_etapa3({'a_otra': 0.05, 'doble_carga': 0.02, S: 0.01}, {('a_otra', 'doble_carga'): 0.04, ('a_otra', S): 0.0,
                                                                          ('doble_carga', S): 0.0},
                           {('a_otra', S): 0.9, ('doble_carga', S): 0.9}, {'a_otra': 0.0}, {'a_otra': 0.01})
        d = M.seleccionar(esc_ficticio(['a_otra', 'doble_carga']), m, True)
        self.assertEqual((d['doble_carga']['decision'], d['doble_carga']['eliminada_por']), ('redundante', 'a_otra'))


class PruebasFlujo(unittest.TestCase):
    def setUp(self):
        self.datos = datos_cuidados()
        self.pob = poblacion_cuidados(self.datos)
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.raiz = Path(self.dir.name)
        self.referencia = escribir_referencia(self.raiz / 'referencia', self.datos)
        self.rutas = M.RutasCuidados(self.raiz / 'nuevo')

    def _correr(self):
        return M.correr(self.datos, self.pob, self.rutas, self.referencia, PEQUENOS)

    def test_escribe_solo_lo_declarado_y_no_sobrescribe(self):
        self._correr()
        self.assertEqual(set(self.rutas.carpeta.iterdir()), self.rutas.declaradas())
        antes = {r: P.sha256(r) for r in self.rutas.declaradas()}
        with self.assertRaises(FileExistsError):
            self._correr()
        self.assertEqual(antes, {r: P.sha256(r) for r in self.rutas.declaradas()})

    def test_no_modifica_la_referencia_ni_los_datos(self):
        rutas = [self.referencia.csv('comparacion_con_original'), self.referencia.csv('su_pares')]
        antes = P.manifiesto(rutas)
        tabla, mascara = self.datos.tabla.copy(), self.datos.mascara.copy()
        self._correr()
        self.assertEqual(P.comparar_manifiestos(antes, P.manifiesto(rutas)), [])
        pd.testing.assert_frame_equal(tabla, self.datos.tabla)
        self.assertTrue((mascara == self.datos.mascara).all())

    def test_un_archivo_existente_detiene_antes_de_calcular(self):
        self.rutas.carpeta.mkdir()
        self.rutas.log.write_text('previo', encoding='utf-8')
        with mock.patch.object(M, 'evaluar', side_effect=AssertionError('no debe calcular')), self.assertRaises(FileExistsError):
            self._correr()
        self.assertEqual(self.rutas.log.read_text(encoding='utf-8'), 'previo')

    def test_si_no_reproduce_la_referencia_no_escribe_nada(self):
        ruta = self.referencia.csv('comparacion_con_original')
        t = K._leer(ruta)
        fila = t.index[t['escenario'] == 'E3'][0]
        t.loc[fila, 'p'] = '0.123456'
        t.to_csv(ruta, index=False, encoding='utf-8-sig')
        with self.assertRaisesRegex(RuntimeError, 'no reproduce E3'):
            self._correr()
        self.assertFalse(self.rutas.carpeta.exists())

    def test_si_otra_referencia_tiene_otras_permutaciones_no_escribe_nada(self):
        otra = escribir_referencia(self.raiz / 'otra', self.datos, 149)
        with self.assertRaisesRegex(RuntimeError, 'no reproduce'):
            M.correr(self.datos, self.pob, self.rutas, otra, PEQUENOS)
        self.assertFalse(self.rutas.carpeta.exists())

    def test_detecta_par_en_comun_alterado(self):
        esc = M.escenario_cuidados(self.datos, self.pob, M.OBSERVADAS)
        ev = M.evaluar(esc, TODO_RELEVANTE)
        with tempfile.TemporaryDirectory() as d:
            rutas = K.RutasComplementarias(Path(d))
            K.tabla_comparacion(esc.base, [K.evaluar(esc.base, K.Parametros('E4', 99, 1.1, 'x'))]).to_csv(
                rutas.csv('comparacion_con_original'), index=False, encoding='utf-8-sig', float_format=P.FORMATO)
            pares = K.tabla_pares(K.evaluar(esc.base, K.Parametros('E4', 99, 1.1, 'x'))).assign(escenario='E4')
            pares.to_csv(rutas.csv('su_pares'), index=False, encoding='utf-8-sig', float_format=P.FORMATO)
            M.comprobar_referencia(ev, rutas)
            pares = K._leer(rutas.csv('su_pares'))
            pares.loc[0, 'p'] = '0.999999'
            pares.to_csv(rutas.csv('su_pares'), index=False, encoding='utf-8-sig')
            with self.assertRaisesRegex(RuntimeError, 'el par'):
                M.comprobar_referencia(ev, rutas)

    def test_si_dos_corridas_difieren_no_escribe_nada(self):
        with mock.patch.object(M, 'iguales', return_value=False), self.assertRaisesRegex(RuntimeError, 'no coinciden'):
            self._correr()
        self.assertFalse(self.rutas.carpeta.exists())

    def test_umbral_restaurado_incluso_con_error(self):
        with mock.patch.object(M, 'comprobar_referencia', side_effect=ValueError), self.assertRaises(ValueError):
            self._correr()
        self.assertEqual(C.ALFA_Q_35B, 0.05)
        self._correr()
        self.assertEqual(C.ALFA_Q_35B, 0.05)

    def test_sin_bootstrap_ni_sensibilidades_ni_cache(self):
        with mock.patch.object(F, 'un_remuestreo', side_effect=AssertionError('bootstrap')), \
                mock.patch.object(P, 'preparar_cache', side_effect=AssertionError('caché')), \
                mock.patch.object(P, 'escenarios_sensibilidad', side_effect=AssertionError('sensibilidad')):
            self._correr()

    def test_resultados_por_escenario(self):
        evaluaciones, _ = self._correr()
        resumen = pd.read_csv(self.rutas.csv('resumen_escenarios'), encoding='utf-8-sig', keep_default_na=False)
        self.assertEqual(resumen['escenario'].tolist(), ['C3', 'C4', 'S3', 'S4'])
        self.assertEqual(set(resumen['familia']), {len(self.datos.candidatas) + 1})
        self.assertEqual(resumen['n_sobrecarga'].tolist(), [int(self.pob.observada.sum())] * 2 + [int(self.pob.cuidadora.sum())] * 2)
        for fila, ev in zip(resumen.itertuples(), evaluaciones):
            self.assertEqual(fila.seleccionadas_adaptado, ';'.join(F.seleccionadas(ev.adaptado)))
        self.assertEqual(evaluaciones[0].plan.parametros.alfa, 0.05)
        self.assertEqual(evaluaciones[1].plan.parametros.alfa, 0.10)

    def test_supera_azar_usa_el_umbral_del_escenario(self):
        self._correr()
        pares = pd.read_csv(self.rutas.csv('su_pares'), encoding='utf-8-sig')
        for nombre, alfa in (('C4', 0.10), ('S4', 0.10)):
            parte = pares[pares['escenario'] == nombre]
            self.assertTrue((parte['supera_azar'] == (parte['q'] < alfa)).all() if len(parte) else True)

    def test_comparacion_une_lo_guardado_y_lo_nuevo(self):
        self._correr()
        t = pd.read_csv(self.rutas.csv('comparacion_resultados'), encoding='utf-8-sig', keep_default_na=False)
        n = len(self.datos.candidatas)
        for nombre in ('E1', 'E3', 'E4'):
            self.assertEqual((t['escenario'] == nombre).sum(), n)
            self.assertNotIn(S, set(t[t['escenario'] == nombre]['variable']))
        for nombre in ('C3', 'C4', 'S3', 'S4'):
            self.assertEqual((t['escenario'] == nombre).sum(), n + 1)
            self.assertIn(S, set(t[t['escenario'] == nombre]['variable']))

    def test_informe_declara_el_caracter_exploratorio_y_las_limitaciones(self):
        self._correr()
        texto = self.rutas.informe.read_text(encoding='utf-8')
        for frase in ('exploratoria', 'No sustituye el resultado oficial', 'no tienen sobrecarga 0', 'imputada', 'ninguna variable se conserva',
                      'no se compara directamente'):
            self.assertIn(frase, texto)
        self.assertNotIn('selección definitiva', texto.lower())

    def test_registro_incluye_huellas_y_poblaciones(self):
        M.correr(self.datos, self.pob, self.rutas, self.referencia, PEQUENOS, huellas={'a.py': 'abc'})
        texto = self.rutas.log.read_text(encoding='utf-8')
        for frase in ('SHA-256 a.py: abc', K.COMMIT_ORIGINAL, 'Poblaciones:', 'índice de la sobrecarga: 30'):
            self.assertIn(frase, texto)


class PruebasParametrosYProteccion(unittest.TestCase):
    def test_escenarios_fijos(self):
        self.assertEqual([(p.parametros.nombre, p.parametros.n_permutaciones, p.parametros.alfa, p.poblacion, p.referencia) for p in M.PLANES],
                         [('C3', 50000, 0.05, M.OBSERVADAS, 'E3'), ('C4', 50000, 0.10, M.OBSERVADAS, 'E4'),
                          ('S3', 50000, 0.05, M.CUIDADORAS, 'E3'), ('S4', 50000, 0.10, M.CUIDADORAS, 'E4')])

    def test_constantes_congeladas_no_cambian(self):
        self.assertEqual((C.SEMILLA, C.TOLERANCIA_SU_35B, C.N_PERMUTACIONES_35B, C.ALFA_Q_35B), (42, 1e-12, 5000, 0.05))
        self.assertEqual(escenario().base.id_analisis, 0)

    def test_consola_no_admite_otros_parametros(self):
        for extra in ('--semilla=7', '--permutaciones=10', '--alfa=0.5', '--remuestreos=5', '--poblacion=todas'):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                M.construir_parser().parse_args(['--ejecutar', extra])

    def test_evaluar_distingue_las_dos_variantes(self):
        """Pares con q alto: la adaptada conserva las variables y la estándar elimina."""
        familias = iter([0.01, 0.9])
        with mock.patch.object(E, 'prueba_permutacion', return_value=(0.5, 0.01)), \
                mock.patch.object(E, 'benjamini_hochberg', side_effect=lambda p: np.full(len(p), next(familias))):
            ev = M.evaluar(escenario(), PEQUENOS[0])
        self.assertEqual(ev.adaptado['senal']['decision'], 'seleccionada')
        self.assertEqual(ev.estandar['senal']['decision'], 'redundante')

    def test_poblacion_desconocida_detiene(self):
        datos = datos_cuidados()
        with self.assertRaisesRegex(ValueError, 'desconocida'):
            M.escenario_cuidados(datos, poblacion_cuidados(datos), 'todas')

    def test_el_programa_no_lee_la_version_verdadera(self):
        fuente = Path(M.__file__).read_text(encoding='utf-8')
        for prohibido in ('dataset_usuaria_verdad', 'bitacora_suciedad', "'_verdad", 'generar_sintetico'):
            self.assertNotIn(prohibido, fuente)
        self.assertEqual(M.SUCIO.name, 'dataset_usuaria_sucio.csv')
        for columnas in (M.COLUMNAS_LIMPIO, M.COLUMNAS_SUCIO):
            self.assertNotIn('verdad', ' '.join(columnas))

    def test_el_programa_escribe_solo_con_el_escritor_de_rutas_declaradas(self):
        fuente = Path(M.__file__).read_text(encoding='utf-8')
        for prohibido in ('.to_csv(', '.write_text(', 'open(', 'shutil', 'os.remove', '.unlink('):
            self.assertNotIn(prohibido, fuente)
        self.assertNotIn('commit', [t.lower() for t in fuente.split() if t.lower() == 'git'])

    def test_rechaza_salidas_originales_y_del_complementario(self):
        reales_ = P.RUTAS_REALES
        for carpeta in (reales_.resultados, reales_.resultados / 'sub', reales_.figuras, reales_.cache / 'x', reales_.dataset.parent,
                        K.CARPETA, K.CARPETA / 'sub'):
            with self.assertRaises(PermissionError, msg=carpeta):
                M.validar_separacion(M.RutasCuidados(carpeta))

    def test_carpeta_real_independiente(self):
        self.assertFalse(M.RUTAS_CUIDADOS.declaradas() & P.RUTAS_REALES.declaradas())
        self.assertFalse(M.RUTAS_CUIDADOS.declaradas() & K.RUTAS_COMPLEMENTARIAS.declaradas())
        self.assertEqual(M.CARPETA.name, 'complementario_cuidados')

    def test_escritor_solo_acepta_rutas_declaradas(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = M.RutasCuidados(Path(d))
            with self.assertRaises(PermissionError):
                P.Escritor(rutas).texto(Path(d) / 'otro.txt', 'x')
            with self.assertRaises(PermissionError):
                P.Escritor(rutas).texto(P.RUTAS_REALES.log, 'x')

    def _main(self, *argumentos):
        with mock.patch.object(sys, 'argv', ['programa', *argumentos]), contextlib.redirect_stdout(io.StringIO()) as salida:
            M.main()
        return salida.getvalue()

    def test_ejecutar_exige_autorizacion_antes_de_todo(self):
        with mock.patch.object(K, 'estado_inicial', side_effect=AssertionError('no debe avanzar')), \
                mock.patch.object(M, 'correr', side_effect=AssertionError('no debe calcular')), \
                self.assertRaisesRegex(SystemExit, 'autorizado'):
            self._main('--ejecutar')

    def test_verificar_nunca_ejecuta_la_seleccion(self):
        datos = datos_cuidados()
        pob = poblacion_cuidados(datos)
        with mock.patch.object(K, 'estado_inicial', return_value=[]), mock.patch.object(M, 'correr_pruebas', return_value=True), \
                mock.patch.object(M, 'comprobar_datos_reales', return_value=(datos, pob, [])), \
                mock.patch.object(M, 'validar_separacion'), \
                mock.patch.object(M, 'correr', side_effect=AssertionError('no debe calcular')), \
                mock.patch.object(M, 'medir', side_effect=AssertionError('no debe medir')):
            self.assertIn('No se calculó ninguna SU', self._main('--verificar'))

    def test_fallas_detienen_incluso_con_autorizacion(self):
        datos = datos_cuidados()
        pob = poblacion_cuidados(datos)
        with mock.patch.object(K, 'estado_inicial', return_value=['HEAD distinto']), mock.patch.object(M, 'correr_pruebas', return_value=True), \
                mock.patch.object(M, 'comprobar_datos_reales', return_value=(datos, pob, [])), \
                mock.patch.object(M, 'correr', side_effect=AssertionError('no debe calcular')), \
                self.assertRaisesRegex(SystemExit, 'fallas'):
            self._main('--ejecutar', '--autorizado-por-usuaria')

    def test_pruebas_fallidas_detienen(self):
        with mock.patch.object(K, 'estado_inicial', return_value=[]), mock.patch.object(M, 'correr_pruebas', return_value=False), \
                mock.patch.object(M, 'correr', side_effect=AssertionError('no debe calcular')), \
                self.assertRaisesRegex(SystemExit, 'pruebas'):
            self._main('--ejecutar', '--autorizado-por-usuaria')

    def test_tamano_distinto_detiene(self):
        datos = datos_cuidados()
        pob = poblacion_cuidados(datos)
        with mock.patch.object(K, 'estado_inicial', return_value=[]), mock.patch.object(M, 'correr_pruebas', return_value=True), \
                mock.patch.object(M, 'comprobar_datos_reales', return_value=(datos, pob, ['Los tamaños no coinciden'])), \
                mock.patch.object(M, 'correr', side_effect=AssertionError('no debe calcular')), \
                self.assertRaisesRegex(SystemExit, 'fallas'):
            self._main('--ejecutar', '--autorizado-por-usuaria')

    def test_cambio_en_archivo_vigilado_se_detecta(self):
        datos = datos_cuidados()
        pob = poblacion_cuidados(datos)
        with tempfile.TemporaryDirectory() as d:
            r = Path(d) / 'vigilado.csv'
            r.write_text('uno', encoding='utf-8')

            def correr_y_alterar(*_a, **_k):
                r.write_text('dos', encoding='utf-8')
                return [], {'total': 0.0}

            with mock.patch.object(K, 'estado_inicial', return_value=[]), mock.patch.object(M, 'correr_pruebas', return_value=True), \
                    mock.patch.object(M, 'comprobar_datos_reales', return_value=(datos, pob, [])), \
                    mock.patch.object(M, 'validar_separacion'), mock.patch.object(M, 'archivos_vigilados', return_value=[r]), \
                    mock.patch.object(M, 'correr', side_effect=correr_y_alterar), \
                    self.assertRaisesRegex(SystemExit, 'vigilados'):
                self._main('--ejecutar', '--autorizado-por-usuaria')


if __name__ == '__main__':
    unittest.main()
