"""
Pruebas del análisis complementario con Random Forest.

Usan datos inventados, salvo `PruebasDatosReales`, que solo cuenta personas y revisa variables: con los datos reales
no entrenan ningún modelo y nunca leen la versión verdadera del simulador.
Uso, desde analisis/: python -m unittest preprocesamiento.test_random_forest_35b
"""
import contextlib
import functools
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

import complementario_cuidados as M
import complementario_fase35b as K
import random_forest_fase35b as RF
import seleccionar_fase35b as P

from . import configuracion as C
from .test_entropia import datos_inventados

PEQUENO = {**RF.PARAMETROS_RF, 'n_estimators': 15}
SENAL, RUIDO = 'senal_prueba', 'ruido_prueba'


def vista_inventada(n=200, semilla=3):
    """Vista con la forma de la real: una señal, ruido, faltantes y una nominal."""
    rng = np.random.default_rng(semilla)
    y = rng.integers(0, 2, n)
    t = pd.DataFrame({
        'participante_id': [f'p{i}' for i in range(n)], 'severo_mrs': y,
        SENAL: np.where(rng.random(n) < 0.9, y, 1 - y), RUIDO: rng.integers(0, 5, n), 'edad': rng.integers(40, 61, n),
        'imc': rng.uniform(18, 40, n), 'usa_medicamentos_diabetes': rng.integers(0, 2, n),
        'trabaja_actualmente': rng.integers(0, 2, n), 'cantidad_personas_cuida': rng.integers(0, 4, n),
        'quien_prepara_comidas': rng.choice(['ella', 'pareja', 'otra'], n), 'lugar_trabajo_comprensivo': rng.integers(1, 6, n).astype(float),
        'estres_entorno_laboral': rng.integers(1, 6, n).astype(float),
        M.SOBRECARGA: rng.integers(1, 6, n).astype(float)})
    t['doble_carga'] = ((t['trabaja_actualmente'] == 1) & (t['cantidad_personas_cuida'] > 0)).astype(int)
    t.loc[rng.random(n) < 0.3, 'imc'] = np.nan
    trabajadoras = rng.random(n) < 0.6
    cuidadoras = rng.random(n) < 0.5
    t.loc[~trabajadoras, list(C.LABORALES_35B)] = np.nan
    t.loc[trabajadoras & (rng.random(n) < 0.1), 'estres_entorno_laboral'] = np.nan
    t.loc[~cuidadoras, M.SOBRECARGA] = np.nan
    pob = {RF.TODAS: np.ones(n, dtype=bool), RF.TRABAJADORAS: trabajadoras, RF.CUIDADORAS: cuidadoras}
    return RF.Vista(t, y, pob, {'todas': n})


def modelo(nombre='X', poblacion=RF.TODAS, variables=(SENAL, RUIDO, 'imc'), referencia=False, funcion='principal'):
    return RF.Modelo(nombre, poblacion, tuple(variables), funcion, 'prueba', referencia)


def datos_para_modelos():
    d = datos_inventados()
    t = d.tabla.copy()
    t['cantidad_personas_cuida'] = (np.arange(len(t)) % 4)
    t['doble_carga'] = ((t['trabaja_actualmente'] == 1) & (t['cantidad_personas_cuida'] > 0)).astype(int)
    for v in RF.ACTIVIDAD + ['vasos_agua_dia', 'tabaco_frecuencia']:
        t[v] = np.arange(len(t)) % 5
    extra = ['cantidad_personas_cuida', 'doble_carga', *RF.ACTIVIDAD, 'vasos_agua_dia', 'tabaco_frecuencia']
    return P.Datos(t, d.mascara, sorted({*d.candidatas, *extra}), d.control, d.pendientes, d.laborales)


def vista_de_datos(datos=None):
    datos = datos or datos_para_modelos()
    t = datos.tabla
    cuida = t['cantidad_personas_cuida'].to_numpy() > 0
    rng = np.random.default_rng(1)
    valores = np.where(cuida, rng.integers(1, 6, len(t)).astype(float), np.nan)
    pob = M.Poblacion(valores, cuida, cuida & (rng.random(len(t)) > 0.1), {})
    observadas = {c: datos.mascara & (rng.random(len(t)) > 0.05) for c in C.LABORALES_35B}
    return datos, RF.construir_vista(datos, pob, observadas), pob, observadas


def comparacion_fcbf(candidatas):
    filas = [{'escenario': e, 'variable': v, 'decision_adaptado': 'no relevante'} for e in RF.ESCENARIOS_FCBF for v in candidatas]
    return pd.DataFrame(filas)


@functools.lru_cache(maxsize=1)
def reales():
    return RF.comprobar_datos_reales()


class PruebasDatosReales(unittest.TestCase):
    """Sin entrenar: un bosque en estas pruebas sería un error."""

    def setUp(self):
        for nombre in ('fit',):
            parche = mock.patch.object(RandomForestClassifier, nombre, side_effect=AssertionError('no debe entrenar'))
            parche.start()
            self.addCleanup(parche.stop)

    def test_tamanos_y_sin_problemas(self):
        datos, vista, modelos, problemas = reales()
        self.assertEqual(problemas, [])
        self.assertEqual(int(vista.poblaciones[RF.TODAS].sum()), 529)
        self.assertEqual(int(vista.poblaciones[RF.TRABAJADORAS].sum()), 287)
        self.assertEqual(int(vista.poblaciones[RF.CUIDADORAS].sum()), 239)
        self.assertEqual(vista.objetivo.sum(), 281)
        self.assertEqual((vista.objetivo[vista.poblaciones[RF.TRABAJADORAS]].sum(), vista.objetivo[vista.poblaciones[RF.CUIDADORAS]].sum()), (166, 136))

    def test_variables_de_cada_modelo(self):
        _, _, modelos, _ = reales()
        n = {m.nombre: len(m.variables) for m in modelos}
        self.assertEqual({k: n[k] for k in ('A', 'B', 'C0', 'C1', 'C2', 'D0', 'D1')}, {'A': 4, 'B': 32, 'C0': 3, 'C1': 31, 'C2': 33, 'D0': 31, 'D1': 32})
        por = {m.nombre: set(m.variables) for m in modelos}
        self.assertEqual(por['D1'] - por['D0'], {M.SOBRECARGA})
        self.assertNotIn('doble_carga', por['D0'])
        self.assertIn('cantidad_personas_cuida', por['D0'])
        self.assertIn('trabaja_actualmente', por['D0'])
        self.assertFalse(set(C.LABORALES_35B) & por['D1'])
        for k in ('C0', 'C1', 'C2'):
            self.assertNotIn('trabaja_actualmente', por[k])
        self.assertEqual(por['C2'] - por['C1'], set(C.LABORALES_35B))
        self.assertEqual(por['C1'] - por['C0'], por['B'] - por['A'])
        self.assertEqual(por['A'], set(C.CONTROL_35B))

    def test_las_30_candidatas_y_4_controles_presentes(self):
        datos, _, modelos, _ = reales()
        self.assertEqual(len(datos.candidatas), 30)
        por = {m.nombre: set(m.variables) for m in modelos}
        self.assertEqual(por['B'] | por['C2'], {*datos.candidatas, *C.CONTROL_35B})

    def test_ninguna_prohibida_en_ningun_modelo(self):
        _, _, modelos, _ = reales()
        for m in modelos:
            for v in m.variables:
                self.assertFalse(RF._prohibida(v), f'{m.nombre}: {v}')
        for v in ('participante_id', 'mrs_total', 'severidad_mrs_4', 'severo_mrs', 'prevision', 'etapa_menopausica', 'menstruacion_llega',
                  'imc_fue_imputado', 'pregunta_1', 'pregunta_nueva', 'rendimiento_afectado', 'lugar_trabajo_comprensivo_imputado'):
            self.assertTrue(RF._prohibida(v), v)

    def test_reconstruccion_de_faltantes(self):
        datos, vista, _, _ = reales()
        t = datos.tabla
        self.assertEqual(int(vista.tabla['imc'].isna().sum()), 262)
        self.assertTrue(vista.tabla['imc'].isna().equals(t['imc_fue_imputado'] == 1))
        k = vista.poblaciones[RF.TRABAJADORAS]
        self.assertEqual(int(vista.tabla['lugar_trabajo_comprensivo'][k].isna().sum()), 16)
        self.assertEqual(int(vista.tabla['estres_entorno_laboral'][k].isna().sum()), 10)
        self.assertTrue(vista.tabla['lugar_trabajo_comprensivo'][~k].isna().all())
        self.assertEqual(int(vista.tabla[M.SOBRECARGA].notna().sum()), 239)
        self.assertFalse((vista.tabla[M.SOBRECARGA] == 0).any())
        self.assertFalse(t['imc'].isna().any())               # el conjunto cargado no cambia

    def test_observadas_conservan_su_valor_y_el_resto_de_columnas_no_cambia(self):
        datos, vista, _, _ = reales()
        t = datos.tabla
        ok = vista.tabla['imc'].notna()
        self.assertTrue((vista.tabla.loc[ok, 'imc'] == t.loc[ok, 'imc']).all())
        for v in set(datos.candidatas) - set(C.LABORALES_35B):
            self.assertTrue(vista.tabla[v].equals(t[v]), v)

    def test_doble_carga_duplicada_segun_poblacion(self):
        _, vista, _, _ = reales()
        t = vista.tabla
        c = vista.poblaciones[RF.CUIDADORAS]
        self.assertTrue((t['doble_carga'][c] == t['trabaja_actualmente'][c]).all())
        k = vista.poblaciones[RF.TRABAJADORAS]
        self.assertTrue((t['doble_carga'][k] == (t['cantidad_personas_cuida'][k] > 0).astype(int)).all())

    def test_particiones_reales_reproducibles_y_sin_superposicion(self):
        _, vista, modelos, _ = reales()
        for pob in (RF.TODAS, RF.TRABAJADORAS, RF.CUIDADORAS):
            y = vista.objetivo[vista.poblaciones[pob]]
            a, b = RF.particiones(y), RF.particiones(y)
            RF.comprobar_particiones(a, y)
            for (e1, v1), (e2, v2) in zip(a, b):
                self.assertTrue((e1 == e2).all() and (v1 == v2).all())

    def test_comparaciones_con_misma_poblacion(self):
        _, _, modelos, _ = reales()
        por = {m.nombre: m for m in modelos}
        for a, b in [*RF.COMPARACIONES_PRINCIPALES, *RF.COMPARACIONES_ADICIONALES]:
            self.assertEqual(por[a].poblacion, por[b].poblacion, (a, b))

    def test_verificar_no_modifica_archivos(self):
        previo = P.manifiesto(RF.archivos_vigilados())
        existia = RF.CARPETA.exists()
        RF.comprobar_datos_reales()
        self.assertEqual(P.comparar_manifiestos(previo, P.manifiesto(RF.archivos_vigilados())), [])
        self.assertEqual(RF.CARPETA.exists(), existia)

    def test_vigilados_cubren_lo_anterior(self):
        vigilados = {Path(r).resolve() for r in RF.archivos_vigilados()}
        for ruta in (P.ENTRADA, P.LIMPIO, M.SUCIO, P.RUTAS_REALES.dataset, P.RUTAS_REALES.csv('su_objetivo'), K.RUTAS_COMPLEMENTARIAS.csv('su_objetivo'),
                     M.RUTAS_CUIDADOS.csv('su_objetivo'), M.PROTOCOLO, K.PROTOCOLO, P.PROTOCOLO, K.INFORME_WORD,
                     P.ANALISIS / 'preprocesamiento' / 'fcbf.py', Path(M.__file__), Path(K.__file__)):
            self.assertIn(Path(ruta).resolve(), vigilados, ruta)

    def test_referencias_fcbf_guardadas_disponibles(self):
        t = K._leer(M.RUTAS_CUIDADOS.csv('comparacion_resultados'))
        self.assertTrue(set(RF.ESCENARIOS_FCBF) <= set(t['escenario']))
        sel = lambda e: sorted(t[(t['escenario'] == e) & (t['decision_adaptado'] == 'seleccionada')]['variable'])
        self.assertEqual(sel('E1'), [])
        self.assertEqual(sel('E3'), sel('C3'))
        self.assertEqual(sel('E3'), ['dias_ejercicio_semana'])
        self.assertEqual(sel('E4'), ['doble_carga', 'frecuencia_fuerza', 'lugar_trabajo_comprensivo'])
        self.assertEqual(sel('E4'), sel('C4'))


class PruebasVista(unittest.TestCase):
    def test_construir_no_altera_la_entrada(self):
        datos = datos_para_modelos()
        antes = datos.tabla.copy()
        vista_de_datos(datos)
        pd.testing.assert_frame_equal(antes, datos.tabla)

    def test_reconstruye_imc_y_laborales_y_no_aplica(self):
        datos, vista, pob, obs = vista_de_datos()
        t = datos.tabla
        self.assertTrue(vista.tabla['imc'].isna().equals(t['imc_fue_imputado'] == 1))
        for c in C.LABORALES_35B:
            self.assertTrue((vista.tabla[c].isna().to_numpy() == ~obs[c]).all())
        self.assertTrue((vista.tabla[M.SOBRECARGA].notna().to_numpy() == pob.observada).all())
        self.assertNotIn('indicador', ' '.join(vista.tabla.columns))

    def test_laborales_observadas_desde_el_sucio(self):
        datos = datos_para_modelos()
        ids = datos.tabla['participante_id']
        sucio = pd.DataFrame({'participante_id': ids, **{c: datos.tabla[c].astype(str) for c in C.LABORALES_35B}})
        c = C.LABORALES_35B[0]
        i = np.flatnonzero(datos.mascara)[:3]
        sucio.loc[i[0], c] = None
        sucio.loc[i[1], c] = 'sin dato'
        sucio.loc[i[2], c] = '99'
        obs = RF.laborales_observadas(datos, sucio)
        self.assertFalse(obs[c][i].any())
        self.assertFalse(obs[c][~datos.mascara].any())

    def test_respuesta_distinta_detiene(self):
        datos = datos_para_modelos()
        c = C.LABORALES_35B[0]
        sucio = pd.DataFrame({'participante_id': datos.tabla['participante_id'], **{v: datos.tabla[v].astype(str) for v in C.LABORALES_35B}})
        i = np.flatnonzero(datos.mascara & (datos.tabla[c].to_numpy() == 2))[0]
        sucio.loc[i, c] = '4'
        with self.assertRaisesRegex(RuntimeError, 'difiere'):
            RF.laborales_observadas(datos, sucio)

    def test_control_de_tamanos(self):
        RF.controlar_tamanos(dict(RF.TAMANOS_ESPERADOS))
        for clave in RF.TAMANOS_ESPERADOS:
            with self.assertRaisesRegex(RuntimeError, 'tamaños', msg=clave):
                RF.controlar_tamanos({**RF.TAMANOS_ESPERADOS, clave: -1})


class PruebasValidacionModelos(unittest.TestCase):
    def setUp(self):
        self.vista = vista_inventada()

    def _problemas(self, *a, **k):
        return RF.validar_modelos([modelo(*a, **k)], self.vista)

    def test_acepta_modelo_correcto(self):
        self.assertEqual(self._problemas(), [])

    def test_rechaza_prohibidas(self):
        self.vista.tabla['mrs_total'] = 1
        for v in ('severo_mrs', 'mrs_total', 'participante_id'):
            self.assertTrue(any('prohibida' in p for p in self._problemas(variables=(SENAL, v))), v)

    def test_rechaza_constante_y_ausente(self):
        self.vista.tabla['const'] = 1
        self.assertTrue(any('constante' in p for p in self._problemas(variables=(SENAL, 'const'))))
        self.assertTrue(any('falta' in p for p in self._problemas(variables=(SENAL, 'no_existe'))))

    def test_rechaza_faltantes_no_previstos(self):
        self.vista.tabla.loc[0, RUIDO] = np.nan
        self.assertTrue(any('faltantes no previstos' in p for p in self._problemas(variables=(SENAL, RUIDO))))

    def test_sobrecarga_solo_en_d1_y_laborales_solo_en_su_cobertura(self):
        self.assertTrue(any('solo corresponde a D1' in p for p in self._problemas('D0', RF.CUIDADORAS, (SENAL, M.SOBRECARGA))))
        self.assertTrue(any('fuera de su cobertura' in p for p in self._problemas('B', RF.TODAS, (SENAL, 'lugar_trabajo_comprensivo'))))
        self.assertEqual(self._problemas('C2', RF.TRABAJADORAS, (SENAL, 'lugar_trabajo_comprensivo')), [])
        self.assertEqual(self._problemas('D1', RF.CUIDADORAS, (SENAL, M.SOBRECARGA)), [])

    def test_rechaza_comparar_poblaciones_distintas(self):
        problemas = RF.validar_modelos([modelo('B'), modelo('A', RF.TRABAJADORAS)], self.vista)
        self.assertTrue(any('misma población' in p for p in problemas))

    def test_rechaza_variables_repetidas(self):
        self.assertTrue(any('repetidas' in p for p in self._problemas(variables=(SENAL, SENAL))))

    def test_detiene_el_flujo_antes_de_entrenar(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(RF, 'evaluar_modelos', side_effect=AssertionError('no debe entrenar')), \
                self.assertRaisesRegex(RuntimeError, 'prohibida'):
            RF.correr(self.vista, [modelo(variables=('severo_mrs',))], RF.RutasRF(Path(d) / 'n'), pd.DataFrame(), [])


class PruebasParticiones(unittest.TestCase):
    def setUp(self):
        self.y = np.array([0, 1] * 60)

    def test_cinco_por_tres_reproducibles(self):
        a, b = RF.particiones(self.y), RF.particiones(self.y)
        self.assertEqual(len(a), 15)
        for (e1, v1), (e2, v2) in zip(a, b):
            self.assertTrue((e1 == e2).all() and (v1 == v2).all())

    def test_sin_superposicion_y_cada_persona_una_vez_por_repeticion(self):
        partes = RF.particiones(self.y)
        RF.comprobar_particiones(partes, self.y)
        for ent, eva in partes:
            self.assertFalse(set(ent) & set(eva))
            self.assertEqual(self.y[eva].sum(), len(eva) // 2)       # estratificada

    def test_repeticiones_distintas(self):
        partes = RF.particiones(self.y)
        self.assertFalse(np.array_equal(np.sort(partes[0][1]), np.sort(partes[5][1])))

    def test_detecta_superposicion(self):
        partes = RF.particiones(self.y)
        partes[0] = (partes[0][0], np.r_[partes[0][1][:-1], partes[0][0][0]])
        with self.assertRaisesRegex(RuntimeError, 'superposición'):
            RF.comprobar_particiones(partes, self.y)

    def test_detecta_persona_no_evaluada(self):
        partes = RF.particiones(self.y)
        ent, eva = partes[0]
        x = partes[1][1][0]
        partes[0] = (np.r_[np.setdiff1d(ent, [x]), eva[0]], np.r_[eva[1:], x])
        with self.assertRaisesRegex(RuntimeError, 'exactamente una vez'):
            RF.comprobar_particiones(partes, self.y)

    def test_detecta_numero_incorrecto(self):
        with self.assertRaisesRegex(RuntimeError, 'Número'):
            RF.comprobar_particiones(RF.particiones(self.y)[:5], self.y)

    def test_modelos_de_una_poblacion_comparten_particiones(self):
        vista = vista_inventada()
        vistos = {}
        original = RF._una_particion

        def espia(X, y, m, i, k, ent, eva, parametros, n):
            vistos[(m.nombre, k)] = (tuple(ent), tuple(eva), tuple(X.index), tuple(y))
            return original(X, y, m, i, k, ent, eva, parametros, n)

        d0, d1 = modelo('D0', RF.CUIDADORAS, (SENAL, RUIDO)), modelo('D1', RF.CUIDADORAS, (SENAL, RUIDO, M.SOBRECARGA))
        with mock.patch.object(RF, '_una_particion', side_effect=espia):
            RF.evaluar_modelos(vista, [d0, d1], PEQUENO, 1, 0)
        for k in range(15):
            self.assertEqual(vistos[('D0', k)], vistos[('D1', k)])
        d0x, _ = RF.datos_de(vista, d0)
        self.assertEqual(len(d0x), int(vista.poblaciones[RF.CUIDADORAS].sum()))


class PruebasPreparacion(unittest.TestCase):
    def setUp(self):
        self.vista = vista_inventada()
        self.m = modelo(variables=(SENAL, RUIDO, 'imc', 'quien_prepara_comidas'))
        self.X, self.y = RF.datos_de(self.vista, self.m)
        self.ent, self.eva = RF.particiones(self.y)[0]

    def _ajustar(self, X=None):
        X = self.X if X is None else X
        return RF.crear_pipeline(self.m.variables, PEQUENO).fit(X.iloc[self.ent], self.y[self.ent])

    def test_mediana_solo_de_entrenamiento(self):
        pipe = self._ajustar()
        imputador = pipe.named_steps['preparar'].named_transformers_['numericas']
        i = list(imputador.feature_names_in_).index('imc')
        self.assertEqual(imputador.statistics_[i], np.nanmedian(self.X['imc'].iloc[self.ent]))

    def test_datos_de_evaluacion_no_influyen_en_la_preparacion_ni_el_modelo(self):
        a = self._ajustar()
        alterado = self.X.copy()
        alterado.loc[alterado.index[self.eva], 'imc'] = 1e6
        alterado.loc[alterado.index[self.eva], 'quien_prepara_comidas'] = 'categoria_nueva'
        b = self._ajustar(alterado)
        estad = lambda p: p.named_steps['preparar'].named_transformers_['numericas'].statistics_
        self.assertTrue((estad(a) == estad(b)).all())
        Xe = self.X.iloc[self.eva]
        self.assertTrue((a.predict_proba(Xe) == b.predict_proba(Xe)).all())

    def test_categorias_solo_de_entrenamiento_y_categoria_nueva_no_rompe(self):
        X = self.X.copy()
        X.loc[X.index[self.eva], 'quien_prepara_comidas'] = 'categoria_nueva'
        pipe = self._ajustar(X)
        cod = pipe.named_steps['preparar'].named_transformers_['nominales']
        self.assertNotIn('categoria_nueva', cod.categories_[0])
        self.assertEqual(pipe.predict_proba(X.iloc[self.eva]).shape[1], 2)

    def test_sin_indicadores_y_sin_escalar(self):
        pipe = self._ajustar()
        prep = pipe.named_steps['preparar']
        self.assertIsNone(prep.named_transformers_['numericas'].indicator_)
        salida = prep.transform(self.X.iloc[self.eva])
        self.assertEqual(salida.shape[1], 3 + 3)        # 3 numéricas y 3 categorías, sin indicadores
        original = self.X[RUIDO].iloc[self.eva].to_numpy()
        self.assertTrue((salida[:, 1] == original).all())     # orden y valores ordinales intactos
        self.assertFalse(np.isnan(salida).any())

    def test_parametros_fijos(self):
        self.assertEqual(RF.PARAMETROS_RF, dict(n_estimators=500, min_samples_leaf=5, max_features='sqrt', class_weight='balanced', random_state=42, n_jobs=1))
        self.assertEqual((RF.PARTICIONES, RF.REPETICIONES, RF.SEMILLA_PARTICIONES, RF.N_ETIQUETAS), (5, 3, 42, 200))
        bosque = RF.crear_pipeline(['a']).named_steps['modelo']
        self.assertEqual((bosque.n_estimators, bosque.min_samples_leaf, bosque.max_features, bosque.class_weight, bosque.random_state),
                         (500, 5, 'sqrt', 'balanced', 42))


class PruebasMetricas(unittest.TestCase):
    def test_valores_calculados_a_mano(self):
        y = np.array([1, 1, 1, 0, 0, 0, 0, 0])
        pred = np.array([1, 1, 0, 1, 0, 0, 0, 0])
        prob = np.array([.9, .8, .4, .7, .3, .2, .1, .05])
        m = RF.calcular_metricas(y, prob, pred)
        self.assertEqual((m['vn'], m['fp'], m['fn'], m['vp']), (4, 1, 1, 2))
        self.assertAlmostEqual(m['balanced_accuracy'], (2 / 3 + 4 / 5) / 2)
        self.assertAlmostEqual(m['f1_severos'], 2 * 2 / (2 * 2 + 1 + 1))
        self.assertAlmostEqual(m['f1_no_severos'], 2 * 4 / (2 * 4 + 1 + 1))
        self.assertAlmostEqual(m['roc_auc'], 14 / 15)
        self.assertEqual(m['f1_severos'], f1_score(y, pred, pos_label=1))

    def test_clasificador_sencillo(self):
        vista = vista_inventada()
        ref = modelo('Ref', variables=(SENAL, RUIDO), referencia=True)
        r, _ = RF.evaluar_modelos(vista, [ref], None, 1, 0, ())
        ev = r[r['conjunto'] == 'evaluacion']
        self.assertTrue((ev['roc_auc'] == 0.5).all())
        self.assertTrue((ev['balanced_accuracy'] == 0.5).all())

    def test_senal_se_detecta_y_ruido_no(self):
        vista = vista_inventada(300)
        senal, ruido = modelo('S', variables=(SENAL,)), modelo('R', variables=(RUIDO,))
        r, _ = RF.evaluar_modelos(vista, [senal, ruido], PEQUENO, 1, 0)
        ev = r[r['conjunto'] == 'evaluacion'].groupby('modelo')['roc_auc'].mean()
        self.assertGreater(ev['S'], 0.8)
        self.assertLess(abs(ev['R'] - 0.5), 0.12)

    def test_detector_de_fuga_la_etiqueta_como_variable_da_auc_perfecto(self):
        vista = vista_inventada()
        vista.tabla['fuga'] = vista.objetivo
        r, _ = RF.evaluar_modelos(vista, [modelo('F', variables=('fuga', RUIDO))], PEQUENO, 1, 0)
        self.assertEqual(r[r['conjunto'] == 'evaluacion']['roc_auc'].min(), 1.0)

    def test_entrenamiento_y_evaluacion_separados_y_sobreajuste(self):
        vista = vista_inventada()
        param = {**PEQUENO, 'min_samples_leaf': 1}
        m = modelo('O', variables=(RUIDO, 'edad', 'imc'))
        r, _ = RF.evaluar_modelos(vista, [m], param, 1, 0)
        resumen = RF.resumir_rendimiento(r, [m]).iloc[0]
        self.assertGreater(resumen['roc_auc_entrenamiento'], resumen['roc_auc_evaluacion'] + 0.2)
        self.assertEqual(r[r['conjunto'] == 'evaluacion'].groupby('repeticion')['n'].sum().tolist(), [len(vista.objetivo)] * 3)

    def test_matrices_suman_la_poblacion_por_repeticion(self):
        vista = vista_inventada()
        r, _ = RF.evaluar_modelos(vista, [modelo()], PEQUENO, 1, 0)
        self.assertEqual(RF.matrices(r)['n'].tolist(), [len(vista.objetivo)] * 3)

    def _rendimiento(self, a, b):
        filas = []
        for nombre, valores in (('X', a), ('Y', b)):
            for k, v in enumerate(valores):
                filas.append({'modelo': nombre, 'repeticion': k // 5, 'particion': k, 'conjunto': 'evaluacion', 'n': 10, 'roc_auc': v, 'balanced_accuracy': v})
        return pd.DataFrame(filas)

    def test_diferencias_por_particion_a_mano(self):
        a, b = np.arange(15) / 100 + 0.6, np.full(15, 0.65)
        t = RF.comparar(self._rendimiento(a, b), [('X', 'Y')])
        f = t[t['metrica'] == 'roc_auc'].iloc[0]
        d = a - b
        self.assertAlmostEqual(f['diferencia'], d.mean())
        self.assertAlmostEqual(f['de'], d.std(ddof=1))
        self.assertEqual((f['minimo'], f['maximo']), (d.min(), d.max()))
        self.assertEqual(f['particiones_positivas'], int((d > 0).sum()))

    def test_comparacion_rechaza_tamanos_distintos(self):
        r = self._rendimiento(np.ones(15), np.ones(15))
        r.loc[r['modelo'] == 'Y', 'n'] = 9
        with self.assertRaisesRegex(RuntimeError, 'no son comparables'):
            RF.comparar(r, [('X', 'Y')])


class PruebasAzar(unittest.TestCase):
    def setUp(self):
        self.vista = vista_inventada()
        self.senal = modelo('A', variables=(SENAL,))

    def test_barajado_reproducible_y_compartido_por_poblacion(self):
        y = self.vista.objetivo
        self.assertTrue((RF.etiquetas_barajadas(y, RF.TODAS, 3) == RF.etiquetas_barajadas(y, RF.TODAS, 3)).all())
        self.assertFalse((RF.etiquetas_barajadas(y, RF.TODAS, 3) == RF.etiquetas_barajadas(y, RF.TODAS, 4)).all())
        self.assertEqual(RF.etiquetas_barajadas(y, RF.TODAS, 3).sum(), y.sum())

    def test_reentrena_todo_el_procedimiento_en_cada_permutacion(self):
        with mock.patch.object(RF, 'crear_pipeline', wraps=RF.crear_pipeline) as crear:
            RF.pruebas_azar(self.vista, [self.senal], 2, PEQUENO, 1)
        self.assertEqual(crear.call_count, 2 * 15)

    def test_particiones_se_generan_con_las_etiquetas_barajadas(self):
        with mock.patch.object(RF, 'particiones', wraps=RF.particiones) as partes:
            RF.pruebas_azar(self.vista, [self.senal], 2, PEQUENO, 1)
        barajadas = [RF.etiquetas_barajadas(self.vista.objetivo, RF.TODAS, i) for i in range(2)]
        for llamada, b in zip(partes.call_args_list, barajadas):
            self.assertTrue((llamada.args[0] == b).all())

    def test_entrena_con_las_etiquetas_barajadas_no_con_las_reales(self):
        vistos = []
        original = RF.crear_pipeline

        def crear(*a, **k):
            pipe = original(*a, **k)
            ajuste = pipe.fit

            def fit(X, y):
                vistos.append((X.index.to_numpy().copy(), np.asarray(y).copy()))
                return ajuste(X, y)
            pipe.fit = fit
            return pipe

        with mock.patch.object(RF, 'crear_pipeline', side_effect=crear):
            RF.pruebas_azar(self.vista, [self.senal], 1, PEQUENO, 1)
        barajada = RF.etiquetas_barajadas(self.vista.objetivo, RF.TODAS, 0)
        idx, y = vistos[0]
        self.assertTrue((y == barajada[idx]).all())
        self.assertFalse((y == self.vista.objetivo[idx]).all())

    def test_senal_supera_al_azar_y_ruido_no(self):
        ruido = modelo('C0', variables=(RUIDO,))
        r, _ = RF.evaluar_modelos(self.vista, [self.senal, ruido], PEQUENO, 1, 0)
        d = RF.pruebas_azar(self.vista, [self.senal, ruido], 9, PEQUENO, 1)
        a = RF.resumir_azar(d, r)
        p = a[a['metrica'] == 'roc_auc'].set_index('modelo')['p']
        self.assertAlmostEqual(p['A'], 1 / 10)
        self.assertGreater(p['C0'], 0.1)

    def test_formula_del_p(self):
        d = pd.DataFrame({'modelo': 'X', 'permutacion': range(4), 'roc_auc': [.4, .5, .6, .7], 'balanced_accuracy': [.4, .5, .6, .7]})
        r = pd.DataFrame({'modelo': 'X', 'conjunto': ['evaluacion', 'entrenamiento'], 'roc_auc': [.6, 1.0], 'balanced_accuracy': [.6, 1.0]})
        f = RF.resumir_azar(d, r).iloc[0]
        self.assertEqual((f['observado'], f['k_mayores_o_iguales'], f['p']), (.6, 2, 3 / 5))

    def test_modelos_de_azar_declarados(self):
        self.assertEqual(RF.MODELOS_AZAR, ('A', 'B', 'C0', 'C2'))

    def test_igual_con_uno_y_con_varios_procesos(self):
        a = RF.pruebas_azar(self.vista, [self.senal], 2, PEQUENO, 1)
        b = RF.pruebas_azar(self.vista, [self.senal], 2, PEQUENO, 2)
        pd.testing.assert_frame_equal(a, b)


class PruebasImportancia(unittest.TestCase):
    def setUp(self):
        self.vista = vista_inventada(300)
        self.m = modelo(variables=(SENAL, RUIDO, 'imc'))

    def test_baraja_en_una_copia_y_conserva_valores(self):
        X = pd.DataFrame({'a': np.arange(50.), 'b': np.arange(50.) * 2, 'c': 1.})
        antes = X.copy()
        Xp = RF.permutar_columnas(X, ('a',), np.random.default_rng(0))
        pd.testing.assert_frame_equal(X, antes)
        self.assertEqual(sorted(Xp['a']), sorted(X['a']))
        self.assertFalse((Xp['a'] == X['a']).all())
        self.assertTrue((Xp['b'] == X['b']).all())

    def test_grupo_barajado_por_filas_completas(self):
        X = pd.DataFrame({'a': np.arange(50.), 'b': np.arange(50.) * 2})
        Xp = RF.permutar_columnas(X, ('a', 'b'), np.random.default_rng(0))
        self.assertTrue((Xp['b'] == Xp['a'] * 2).all())
        self.assertFalse((Xp['a'] == X['a']).all())

    def test_nominal_se_baraja_antes_de_codificar(self):
        X = pd.DataFrame({'quien_prepara_comidas': ['x', 'y'] * 10})
        Xp = RF.permutar_columnas(X, ('quien_prepara_comidas',), np.random.default_rng(1))
        self.assertEqual(Xp['quien_prepara_comidas'].value_counts().to_dict(), {'x': 10, 'y': 10})

    def test_senal_importa_y_ruido_casi_no(self):
        _, d = RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 5, ('X',))
        t = RF.resumir_importancia(d, 'variable').set_index('nombre')
        self.assertGreater(t.loc[SENAL, 'auc_media'], 0.2)
        self.assertGreater(t.loc[SENAL, 'auc_media'], 5 * abs(t.loc[RUIDO, 'auc_media']))
        self.assertEqual(t.loc[SENAL, 'auc_positivas'], 15)
        self.assertEqual(t.loc[SENAL, 'particiones'], 15)

    def test_usa_solo_datos_de_evaluacion(self):
        tamanos = []
        original = RF._puntajes

        def espia(pipe, X, y):
            tamanos.append(len(X))
            return original(pipe, X, y)

        y = self.vista.objetivo
        with mock.patch.object(RF, '_puntajes', side_effect=espia):
            RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 2, ('X',))
        partes = RF.particiones(y)
        self.assertLessEqual(max(tamanos), max(len(e) for _, e in partes))

    def test_se_informan_auc_y_exactitud(self):
        _, d = RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 2, ('X',))
        t = RF.resumir_importancia(d, 'variable')
        for c in ('auc_media', 'auc_de', 'auc_minimo', 'auc_maximo', 'auc_positivas', 'ba_media', 'ba_de', 'ba_positivas', 'lectura'):
            self.assertIn(c, t.columns)

    def test_lectura_sin_umbrales(self):
        self.assertIn('nula o negativa', RF.lectura_importancia(-0.001, 7, 15))
        self.assertIn('nula o negativa', RF.lectura_importancia(0.0, 0, 15))
        self.assertIn('todas', RF.lectura_importancia(0.0001, 15, 15))
        self.assertIn('signo variable (9/15)', RF.lectura_importancia(0.05, 9, 15))

    def test_grupos_presentes_y_sin_repetir(self):
        g = RF.grupos_de(['dias_ejercicio_semana', 'frecuencia_fuerza', 'cantidad_personas_cuida', 'doble_carga', 'trabaja_actualmente'])
        self.assertEqual(g['actividad física'], ('dias_ejercicio_semana', 'frecuencia_fuerza'))
        self.assertEqual(g['cuidados'], ('cantidad_personas_cuida', 'doble_carga'))
        self.assertEqual(g['trabajo y cuidados'], ('trabaja_actualmente', 'cantidad_personas_cuida', 'doble_carga'))
        self.assertNotIn('entorno laboral', g)
        sin_trabajo = RF.grupos_de(['cantidad_personas_cuida', 'doble_carga'])
        self.assertNotIn('trabajo y cuidados', sin_trabajo)

    def test_grupo_de_una_senal_duplicada_importa_mas_que_cada_copia(self):
        v = self.vista
        v.tabla['dias_ejercicio_semana'] = v.tabla[SENAL]
        v.tabla['frecuencia_fuerza'] = v.tabla[SENAL]
        m = modelo(variables=('dias_ejercicio_semana', 'frecuencia_fuerza', RUIDO))
        _, d = RF.evaluar_modelos(v, [m], PEQUENO, 1, 5, ('X',))
        ind = RF.resumir_importancia(d, 'variable').set_index('nombre')['auc_media']
        gru = RF.resumir_importancia(d, 'grupo').set_index('nombre')['auc_media']
        self.assertGreater(gru['actividad física'], max(ind['dias_ejercicio_semana'], ind['frecuencia_fuerza']))

    def test_cada_variable_y_repeticion_usa_su_propia_semilla(self):
        with mock.patch.object(RF.E, 'generador', wraps=RF.E.generador) as generador:
            RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 2, ('X',))
        semillas = [llamada.args for llamada in generador.call_args_list]
        self.assertEqual(len(semillas), 15 * 3 * 2)         # 15 particiones, 3 variables, 2 repeticiones
        self.assertEqual(len(set(semillas)), len(semillas))

    def test_semillas_de_importancia_reproducibles(self):
        _, a = RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 2, ('X',))
        _, b = RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 2, ('X',))
        pd.testing.assert_frame_equal(a, b)

    def test_modelo_sin_importancia_declarada_no_la_calcula(self):
        _, d = RF.evaluar_modelos(self.vista, [self.m], PEQUENO, 1, 2, ('otro',))
        self.assertEqual(len(d), 0)

    def test_comparacion_con_fcbf_lee_cada_variable_en_su_modelo(self):
        self.assertEqual(RF.modelo_de_referencia(M.SOBRECARGA), 'D1')
        self.assertEqual(RF.modelo_de_referencia('estres_entorno_laboral'), 'C2')
        self.assertEqual(RF.modelo_de_referencia('frecuencia_fuerza'), 'B')
        imp = pd.DataFrame([{'modelo': m, 'nombre': v, 'auc_media': a, 'auc_de': .1, 'auc_positivas': 9, 'particiones': 15, 'ba_media': .1, 'lectura': 'x'}
                            for m, v, a in (('B', 'frecuencia_fuerza', .02), ('B', 'frecuencia_fuerza2', .9), ('C2', 'estres_entorno_laboral', .01), ('D1', M.SOBRECARGA, .03))])
        fcbf = comparacion_fcbf(['frecuencia_fuerza', 'estres_entorno_laboral'])
        fcbf.loc[(fcbf['escenario'] == 'E4') & (fcbf['variable'] == 'frecuencia_fuerza'), 'decision_adaptado'] = 'seleccionada'
        t = RF.tabla_rf_vs_fcbf(imp, fcbf, ['frecuencia_fuerza', 'estres_entorno_laboral']).set_index('variable')
        self.assertEqual(t.loc['frecuencia_fuerza', 'fcbf_E4'], 'seleccionada')
        self.assertEqual(t.loc['frecuencia_fuerza', 'fcbf_E3'], 'no relevante')
        self.assertEqual(t.loc[M.SOBRECARGA, 'fcbf_E4'], 'no evaluada')
        self.assertEqual(t.loc[M.SOBRECARGA, 'modelo_rf'], 'D1')


class PruebasFlujo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.datos, cls.vista, _, _ = vista_de_datos()
        cls.modelos = RF.definir_modelos(cls.datos.candidatas, cls.datos.control)
        cls.fcbf = comparacion_fcbf(cls.datos.candidatas)
        cls.rutas = RF.RutasRF(Path(cls.dir.name) / 'nuevo')
        cls.resultado = RF.correr(cls.vista, cls.modelos, cls.rutas, cls.fcbf, cls.datos.candidatas, PEQUENO, 3, 2, 1)

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def _csv(self, nombre):
        return pd.read_csv(self.rutas.csv(nombre), encoding='utf-8-sig', keep_default_na=False)

    def test_escribe_exactamente_lo_declarado(self):
        escritos = {r for r in self.rutas.carpeta.rglob('*') if r.is_file()}
        self.assertEqual(escritos, self.rutas.declaradas())

    def test_no_sobrescribe(self):
        antes = {r: P.sha256(r) for r in self.rutas.declaradas()}
        with self.assertRaises(FileExistsError):
            RF.correr(self.vista, self.modelos, self.rutas, self.fcbf, self.datos.candidatas, PEQUENO, 1, 1, 1)
        self.assertEqual(antes, {r: P.sha256(r) for r in self.rutas.declaradas()})

    def test_no_altera_los_datos(self):
        self.assertFalse(self.datos.tabla['imc'].isna().any())

    def test_comparaciones_principales_presentes(self):
        t = self._csv('comparacion_modelos')
        pares = set(zip(t[t['tipo'] == 'principal']['modelo'], t[t['tipo'] == 'principal']['referencia']))
        self.assertEqual(pares, {('B', 'A'), ('C1', 'C0'), ('C2', 'C1'), ('D1', 'D0')})
        self.assertEqual(set(t['metrica']), {'roc_auc', 'balanced_accuracy'})

    def test_todos_los_modelos_con_quince_particiones_en_evaluacion(self):
        t = self._csv('rendimiento_particiones')
        n = t[t['conjunto'] == 'evaluacion'].groupby('modelo').size()
        self.assertEqual(set(n), {15})
        self.assertEqual(len(n), len(self.modelos))

    def test_d0_y_d1_mismas_personas_y_mismos_tamanos(self):
        t = self._csv('rendimiento_particiones')
        a, b = t[t['modelo'] == 'D0'], t[t['modelo'] == 'D1']
        self.assertEqual(a['n'].tolist(), b['n'].tolist())
        for x, y in (('A', 'B'), ('C0', 'C1'), ('C1', 'C2')):
            self.assertEqual(t[t['modelo'] == x]['n'].tolist(), t[t['modelo'] == y]['n'].tolist())

    def test_azar_solo_en_los_modelos_declarados(self):
        self.assertEqual(set(self._csv('distribucion_azar')['modelo']), {'A', 'B', 'C0', 'C2'})
        self.assertEqual(len(self._csv('pruebas_azar')), 8)

    def test_importancia_solo_en_los_modelos_declarados_y_sobrecarga_solo_en_d1(self):
        t = self._csv('importancia_variables')
        self.assertEqual(set(t['modelo']), set(RF.MODELOS_IMPORTANCIA))
        self.assertEqual(set(t[t['nombre'] == M.SOBRECARGA]['modelo']), {'D1'})

    def test_grupos_de_interes_en_su_modelo(self):
        t = self._csv('importancia_grupos')
        self.assertIn('entorno laboral', set(t[t['modelo'] == 'C2']['nombre']))
        self.assertNotIn('entorno laboral', set(t[t['modelo'] == 'B']['nombre']))
        self.assertIn('actividad física', set(t[t['modelo'] == 'B']['nombre']))
        self.assertIn(M.SOBRECARGA, t[(t['modelo'] == 'D1') & (t['nombre'] == 'cuidados')]['variables'].iloc[0])

    def test_sensibilidad_sin_imc(self):
        t = self._csv('sensibilidad_sin_imc')
        self.assertEqual(set(t['referencia']), {'A_sin_imc', 'B_sin_imc', 'C2_sin_imc'})
        m = self._csv('modelos_rf').set_index('modelo')
        for k in ('A_sin_imc', 'B_sin_imc', 'C2_sin_imc'):
            self.assertNotIn('imc', m.loc[k, 'variables'].split(';'))

    def test_informe_advierte_lo_necesario(self):
        texto = self.rutas.informe.read_text(encoding='utf-8')
        for frase in ('exploratorio', 'No reemplaza FCBF', 'sintéticos', 'potencialmente optimistas', 'no se implementó', 'combinaciones imposibles',
                      'No selecciona variables para la segmentación'):
            self.assertIn(frase, texto)

    def test_registro(self):
        texto = self.rutas.log.read_text(encoding='utf-8')
        for frase in (K.COMMIT_ORIGINAL, 'Avisos de Python', 'Tiempo real', 'scikit-learn'):
            self.assertIn(frase, texto)

    def test_figuras_generadas(self):
        for f in RF.FIGURAS:
            self.assertGreater(self.rutas.figura(f).stat().st_size, 1000, f)

    def test_si_dos_corridas_difieren_no_escribe_nada(self):
        with tempfile.TemporaryDirectory() as d:
            nuevo = Path(d) / 'n'
            real = RF.evaluar_modelos
            llamadas = []

            def alterar(*a, **k):
                llamadas.append(1)
                r, i = real(*a, **k)
                if len(llamadas) == 2:
                    r = r.assign(roc_auc=r['roc_auc'] + 1e-9)
                return r, i

            with mock.patch.object(RF, 'evaluar_modelos', side_effect=alterar), self.assertRaisesRegex(RuntimeError, 'no coinciden'):
                RF.correr(self.vista, self.modelos[:5], RF.RutasRF(nuevo), self.fcbf, self.datos.candidatas, PEQUENO, 1, 1, 1)
            self.assertFalse(nuevo.exists())


class PruebasProteccion(unittest.TestCase):
    def test_el_programa_no_lee_la_version_verdadera_ni_escribe_por_fuera(self):
        fuente = Path(RF.__file__).read_text(encoding='utf-8')
        for prohibido in ('dataset_usuaria_verdad', 'bitacora_suciedad', 'dataset_fase35b.csv', '.to_csv(', '.write_text(', 'open(', 'shutil', '.unlink(', 'GridSearch',
                          'RandomizedSearch', 'add_indicator=True', 'StandardScaler', 'MinMaxScaler', 'F.medir', 'F.seleccionar', 'un_remuestreo'):
            self.assertNotIn(prohibido, fuente)

    def test_consola_no_admite_otros_parametros(self):
        for extra in ('--semilla=7', '--n-estimators=10', '--permutaciones=5', '--particiones=2'):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                RF.construir_parser().parse_args(['--ejecutar', extra])

    def test_rechaza_carpetas_anteriores(self):
        r = P.RUTAS_REALES
        for carpeta in (r.resultados, r.figuras, r.dataset.parent, K.CARPETA, K.CARPETA / 'x', M.CARPETA, M.CARPETA / 'x'):
            with self.assertRaises(PermissionError, msg=carpeta):
                RF.validar_separacion(RF.RutasRF(carpeta))

    def test_carpeta_real_independiente(self):
        self.assertEqual(RF.CARPETA.name, 'random_forest_35b')
        self.assertFalse(RF.RUTAS_RF.declaradas() & P.RUTAS_REALES.declaradas())
        self.assertFalse(RF.RUTAS_RF.declaradas() & M.RUTAS_CUIDADOS.declaradas())
        self.assertFalse(RF.RUTAS_RF.declaradas() & K.RUTAS_COMPLEMENTARIAS.declaradas())

    def test_escritor_solo_acepta_lo_declarado(self):
        with tempfile.TemporaryDirectory() as d:
            salida = P.Escritor(RF.RutasRF(Path(d)))
            with self.assertRaises(PermissionError):
                salida.texto(Path(d) / 'otro.txt', 'x')
            with self.assertRaises(PermissionError):
                salida.texto(P.RUTAS_REALES.log, 'x')

    def _main(self, *argumentos):
        with mock.patch.object(sys, 'argv', ['programa', *argumentos]), contextlib.redirect_stdout(io.StringIO()) as salida:
            RF.main()
        return salida.getvalue()

    def _parches(self, estado=(), pruebas=True, problemas=()):
        datos, vista, _, _ = vista_de_datos()
        return [mock.patch.object(K, 'estado_inicial', return_value=list(estado)), mock.patch.object(RF, 'correr_pruebas', return_value=pruebas),
                mock.patch.object(RF, 'comprobar_datos_reales', return_value=(datos, vista, [], list(problemas))), mock.patch.object(RF, 'validar_separacion'),
                mock.patch.object(RF, 'correr', side_effect=AssertionError('no debe entrenar'))]

    def _con(self, parches, funcion):
        for p in parches:
            p.start()
            self.addCleanup(p.stop)
        return funcion()

    def test_ejecutar_exige_autorizacion_antes_de_todo(self):
        with mock.patch.object(K, 'estado_inicial', side_effect=AssertionError('no debe avanzar')), self.assertRaisesRegex(SystemExit, 'autorizado'):
            self._main('--ejecutar')

    def test_verificar_nunca_entrena(self):
        texto = self._con(self._parches(), lambda: self._main('--verificar'))
        self.assertIn('No se entrenó', texto)

    def test_fallas_de_estado_detienen(self):
        with self.assertRaisesRegex(SystemExit, 'fallas'):
            self._con(self._parches(estado=['HEAD distinto']), lambda: self._main('--ejecutar', '--autorizado-por-usuaria'))

    def test_pruebas_fallidas_detienen(self):
        with self.assertRaisesRegex(SystemExit, 'pruebas'):
            self._con(self._parches(pruebas=False), lambda: self._main('--ejecutar', '--autorizado-por-usuaria'))

    def test_problemas_de_datos_detienen(self):
        with self.assertRaisesRegex(SystemExit, 'fallas'):
            self._con(self._parches(problemas=['tamaño distinto']), lambda: self._main('--ejecutar', '--autorizado-por-usuaria'))

    def test_cambio_en_archivo_vigilado_se_detecta(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d) / 'vigilado.csv'
            r.write_text('uno', encoding='utf-8')

            def correr(*_a, **_k):
                r.write_text('dos', encoding='utf-8')
                return {'tiempos': {'total': 0.0}}

            parches = self._parches()[:-1] + [mock.patch.object(RF, 'correr', side_effect=correr), mock.patch.object(RF, 'archivos_vigilados', return_value=[r]),
                                              mock.patch.object(K, '_leer', return_value=pd.DataFrame())]
            with self.assertRaisesRegex(SystemExit, 'vigilados'):
                self._con(parches, lambda: self._main('--ejecutar', '--autorizado-por-usuaria'))


if __name__ == '__main__':
    unittest.main()
