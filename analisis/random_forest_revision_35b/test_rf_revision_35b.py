"""
Pruebas de Random Forest para la revisión de la Fase 35B.

Usan datos inventados, salvo `PruebasDatosReales`, que solo cuenta personas y revisa variables: con los datos reales
no entrenan ningún modelo. Uso, desde analisis/: python -m unittest random_forest_revision_35b.test_rf_revision_35b
"""
import functools
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

import complementario_fase35b as K
import random_forest_fase35b as RF
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from random_forest_revision_35b import rf_revision_35b as RV

PEQUENO = {**RF.PARAMETROS_RF, 'n_estimators': 15}


def vista_33(n=240, semilla=3):
    """Forma de la vista real: las 33 variables, una señal, faltantes, «no aplica» vacío y una nominal."""
    rng = np.random.default_rng(semilla)
    y = rng.integers(0, 2, n)
    t = pd.DataFrame({v: rng.integers(1, 6, n).astype(float) for v in RV.VARIABLES_33})
    t['severo_mrs'] = y
    t['participante_id'] = [f'p{i}' for i in range(n)]
    t['mrs_total'] = y * 16 + rng.integers(0, 8, n)
    t['dias_ejercicio_semana'] = np.where(rng.random(n) < 0.9, y, 1 - y).astype(float)
    t['quien_prepara_comidas'] = rng.choice(['ella', 'pareja', 'otra'], n)
    t['imc'] = rng.uniform(18, 40, n)
    t.loc[rng.random(n) < 0.3, 'imc'] = np.nan
    laboral, cuidadoras = np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
    laboral[rng.permutation(n)[:n // 2 + 30]] = True
    cuidadoras[rng.permutation(n)[:n // 2 + 20]] = True
    t['trabaja_actualmente'] = np.where(laboral, 1.0, rng.integers(0, 2, n).astype(float))
    t.loc[~laboral, RV.LABORALES] = np.nan
    t.loc[laboral & (rng.random(n) < 0.05), 'estres_entorno_laboral'] = np.nan
    t.loc[~cuidadoras, RV.SOBRECARGA] = np.nan
    pob = {RV.TODAS: np.ones(n, dtype=bool), RV.TRABAJADORAS: laboral, RV.CUIDADORAS: cuidadoras}
    return RF.Vista(t, y, pob, {'todas': n})


def shannon_inventado():
    c = pd.DataFrame([{'variable': v, 'poblacion': 'cuidadoras' if v == RV.SOBRECARGA else 'laboral' if v in RV.LABORALES else 'general', 'n': '529', 'su': '0.01', 'q_10000': '0.09' if v in RV.SEIS_SHANNON else '0.5',
                       'q_50000': '0.09' if v in RV.SEIS_SHANNON else '0.5', 'relevante_10000': str(v in RV.SEIS_SHANNON), 'relevante_50000': str(v in RV.SEIS_SHANNON)} for v in RV.VARIABLES_33])
    d = pd.DataFrame([{'variable': v, 'direccion': 'positiva', 'clase': 'Sin respaldo tras la corrección', 'rho_mrs': 0.1} for v in RV.VARIABLES_33])
    return c, d


@functools.lru_cache(maxsize=1)
def reales():
    return RV.comprobar_datos_reales()


class PruebasDatosReales(unittest.TestCase):
    """Sin entrenar: un bosque en estas pruebas sería un error."""

    def setUp(self):
        parche = mock.patch.object(RandomForestClassifier, 'fit', side_effect=AssertionError('no debe entrenar'))
        parche.start()
        self.addCleanup(parche.stop)

    def test_sin_problemas(self):
        self.assertEqual(reales()[3], [])

    def test_poblaciones_y_severas(self):
        _, vista, _, _ = reales()
        self.assertEqual(int(vista.objetivo.sum()), 281)
        self.assertEqual(int((vista.objetivo == 0).sum()), 248)
        for pob, (n, s) in ((RV.TODAS, (529, 281)), (RV.TRABAJADORAS, (287, 166)), (RV.CUIDADORAS, (239, 136))):
            k = vista.poblaciones[pob]
            self.assertEqual((int(k.sum()), int(vista.objetivo[k].sum())), (n, s))

    def test_objetivo_corresponde_al_corte_del_mrs(self):
        _, vista, _, _ = reales()
        self.assertTrue(((vista.tabla['mrs_total'] >= 16).astype(int) == vista.tabla['severo_mrs']).all())

    def test_conteo_de_variables(self):
        n = {m.nombre: len(m.variables) for m in reales()[2]}
        self.assertEqual({k: n[k] for k in RV.PRINCIPALES}, {'A': 3, 'B': 30, 'C0': 29, 'C1': 31, 'D0': 30, 'D1': 31})

    def test_las_33_y_las_mismas_de_la_revision(self):
        por = {m.nombre: set(m.variables) for m in reales()[2]}
        self.assertEqual(len(RV.VARIABLES_33), 33)
        self.assertEqual(por['B'] | por['C1'] | por['D1'], set(RV.VARIABLES_33))
        self.assertEqual(por['B'], set(RV.VARIABLES_33) - set(RV.LABORALES) - {RV.SOBRECARGA})
        for v in ('sobrecarga_fisica_emocional', 'cantidad_personas_cuida', 'edad', 'imc', 'trabaja_actualmente'):
            self.assertIn(v, RV.VARIABLES_33)
        self.assertNotIn('usa_medicamentos_diabetes', RV.VARIABLES_33)

    def test_exclusiones_en_todos_los_modelos(self):
        for m in reales()[2]:
            for v in m.variables:
                self.assertFalse(RV.prohibida(v), f'{m.nombre}: {v}')
            self.assertNotIn('doble_carga', m.variables)
            self.assertNotIn('prevision', m.variables)
            self.assertNotIn('usa_medicamentos_diabetes', m.variables)
            self.assertFalse([v for v in m.variables if v.startswith(('mrs_', 'pregunta_')) or v in ('severidad_mrs_4', 'severo_mrs', 'imc_fue_imputado', 'participante_id')])
        for v in ('doble_carga', 'prevision', 'usa_medicamentos_diabetes', 'mrs_total', 'severidad_mrs_4', 'severo_mrs', 'participante_id', 'pregunta_3', 'imc_fue_imputado', 'etapa_menopausica'):
            self.assertTrue(RV.prohibida(v), v)

    def test_modelos_anidados(self):
        por = {m.nombre: set(m.variables) for m in reales()[2]}
        self.assertEqual(por['A'], {'edad', 'imc', 'trabaja_actualmente'})
        self.assertEqual(por['C1'] - por['C0'], set(RV.LABORALES))
        self.assertEqual(por['D1'] - por['D0'], {RV.SOBRECARGA})
        self.assertEqual(por['D0'], por['B'])
        self.assertNotIn('trabaja_actualmente', por['C0'] | por['C1'])
        self.assertFalse(set(RV.LABORALES) & (por['D0'] | por['D1']))
        self.assertIn('trabaja_actualmente', por['D1'])
        self.assertEqual(len(por['B_shannon']), 5)
        self.assertEqual(len(por['B_resto']), 25)
        self.assertEqual(por['B_shannon'] | por['B_resto'], por['B'])

    def test_no_aplica_no_es_cero(self):
        _, vista, _, _ = reales()
        t = vista.tabla
        self.assertEqual(RV.comprobar_no_aplica(vista), [])
        self.assertEqual(int(t[RV.SOBRECARGA].notna().sum()), 239)
        self.assertTrue(t.loc[~vista.poblaciones[RV.TRABAJADORAS], RV.LABORALES].isna().all().all())
        self.assertEqual(int(t['imc'].isna().sum()), 262)
        k = vista.poblaciones[RV.TRABAJADORAS]
        self.assertEqual(int(t.loc[k, 'lugar_trabajo_comprensivo'].isna().sum()), 16)
        self.assertEqual(int(t.loc[k, 'estres_entorno_laboral'].isna().sum()), 10)

    def test_el_conjunto_cargado_no_cambia(self):
        datos, _, _, _ = reales()
        self.assertFalse(datos.tabla['imc'].isna().any())

    def test_sin_fuga_del_mrs(self):
        self.assertEqual(RV.comprobar_fuga(reales()[1]), [])

    def test_particiones_iguales_en_modelos_comparables(self):
        _, vista, modelos, _ = reales()
        por = {m.nombre: m for m in modelos}
        for a, b in RV.COMPARACIONES['principal']:
            _, ya = RF.datos_de(vista, por[a])
            _, yb = RF.datos_de(vista, por[b])
            for (e1, v1), (e2, v2) in zip(RF.particiones(ya), RF.particiones(yb)):
                self.assertTrue((e1 == e2).all() and (v1 == v2).all())

    def test_shannon_guardado(self):
        c = K._leer(RV.COMPARACION_SHANNON)
        self.assertEqual(len(c), 33)
        self.assertEqual(sorted(c['variable']), sorted(RV.VARIABLES_33))
        for columna in ('relevante_10000', 'relevante_50000'):
            self.assertEqual(sorted(c[c[columna] == 'True']['variable']), sorted(RV.SEIS_SHANNON))

    def test_vigilados_cubren_shannon(self):
        vigilados = {Path(r).resolve() for r in RV.archivos_vigilados()}
        for r in (P.ENTRADA, RV.COMPARACION_SHANNON, RV.DIRECCION_SHANNON, R.CARPETA / 'informe_integrado' / 'informe_fase35b_integrado.docx', R.CARPETA / 'permutaciones_10000' / 'relevancia_34.csv',
                  R.CARPETA / 'permutaciones_50000' / 'relevancia_34.csv', Path(RF.__file__), Path(R.__file__)):
            self.assertIn(Path(r).resolve(), vigilados, r)

    def test_no_modifica_archivos(self):
        previo = P.manifiesto(RV.archivos_vigilados())
        RV.comprobar_datos_reales()
        self.assertEqual(P.comparar_manifiestos(previo, P.manifiesto(RV.archivos_vigilados())), [])


class PruebasValidacion(unittest.TestCase):
    def setUp(self):
        self.vista = vista_33()

    def _p(self, nombre='X', poblacion=RV.TODAS, variables=('dias_ejercicio_semana', 'imc')):
        return RV.validar_modelos([RV.Modelo(nombre, poblacion, tuple(variables), 'principal', 'prueba')], self.vista)

    def test_acepta_correcto(self):
        self.assertEqual(self._p(), [])

    def test_rechaza_excluidas_y_fuera_de_las_33(self):
        self.vista.tabla['doble_carga'] = 1
        self.assertTrue(any('prohibida' in x for x in self._p(variables=('imc', 'doble_carga'))))
        self.assertTrue(any('prohibida' in x for x in self._p(variables=('imc', 'mrs_total'))))
        self.assertTrue(any('prohibida' in x for x in self._p(variables=('imc', 'severo_mrs'))))
        self.vista.tabla['otra_del_eda'] = 1
        self.assertTrue(any('no está entre las 33' in x for x in self._p(variables=('imc', 'otra_del_eda'))))

    def test_rechaza_constante_y_faltantes(self):
        self.vista.tabla['edad'] = 1.0
        self.assertTrue(any('constante' in x for x in self._p(variables=('imc', 'edad'))))
        self.vista.tabla.loc[0, 'tabaco_frecuencia'] = np.nan
        self.assertTrue(any('faltantes no previstos' in x for x in self._p(variables=('imc', 'tabaco_frecuencia'))))

    def test_no_aplica_fuera_de_su_poblacion(self):
        self.assertTrue(any('sobrecarga fuera' in x for x in self._p(variables=('imc', RV.SOBRECARGA))))
        self.assertTrue(any('laborales fuera' in x for x in self._p(poblacion=RV.CUIDADORAS, variables=('imc', 'lugar_trabajo_comprensivo'))))

    def test_comparaciones_con_misma_poblacion(self):
        por = {m.nombre: m for m in RV.definir_modelos()}
        for pares in RV.COMPARACIONES.values():
            for a, b in pares:
                self.assertEqual(por[a].poblacion, por[b].poblacion, (a, b))

    def test_detecta_cero_en_no_aplica(self):
        self.vista.tabla.loc[~self.vista.poblaciones[RV.CUIDADORAS], RV.SOBRECARGA] = 0
        self.assertTrue(RV.comprobar_no_aplica(self.vista))

    def test_detecta_fuga(self):
        self.vista.tabla['edad'] = self.vista.tabla['mrs_total']
        self.assertTrue(any('edad' in x for x in RV.comprobar_fuga(self.vista)))

    def test_detiene_antes_de_entrenar(self):
        malo = RV.Modelo('X', RV.TODAS, ('severo_mrs',), 'principal', 'prueba')
        with tempfile.TemporaryDirectory() as d, mock.patch.object(RV, 'evaluar_modelos', side_effect=AssertionError('no debe entrenar')), self.assertRaisesRegex(RuntimeError, 'prohibida'):
            RV.calcular(self.vista, [malo], RV.Rutas(Path(d)))


class PruebasPreparacion(unittest.TestCase):
    def test_imputacion_solo_con_entrenamiento(self):
        vista = vista_33()
        m = RV.Modelo('X', RV.TODAS, ('imc', 'quien_prepara_comidas', 'edad'), 'principal', 'prueba')
        X, y = RF.datos_de(vista, m)
        ent, eva = RF.particiones(y)[0]
        ajustar = lambda Z: RF.crear_pipeline(m.variables, PEQUENO).fit(Z.iloc[ent], y[ent])
        a = ajustar(X)
        imputador = a.named_steps['preparar'].named_transformers_['numericas']
        i = list(imputador.feature_names_in_).index('imc')
        self.assertEqual(imputador.statistics_[i], np.nanmedian(X['imc'].iloc[ent]))
        Z = X.copy()
        Z.loc[Z.index[eva], 'imc'] = 1e6
        Z.loc[Z.index[eva], 'quien_prepara_comidas'] = 'nueva'
        b = ajustar(Z)
        self.assertTrue((a.predict_proba(X.iloc[eva]) == b.predict_proba(X.iloc[eva])).all())

    def test_vista_no_se_modifica_al_evaluar(self):
        vista = vista_33()
        antes = vista.tabla.copy()
        RV.evaluar_modelos(vista, [m for m in RV.definir_modelos() if m.nombre == 'A'], PEQUENO, 1, 1)
        pd.testing.assert_frame_equal(antes, vista.tabla)

    def test_parametros_del_protocolo(self):
        self.assertEqual(RV.PARAMETROS_RF, dict(n_estimators=500, min_samples_leaf=5, max_features='sqrt', class_weight='balanced', random_state=42, n_jobs=1))
        self.assertEqual((RV.PARTICIONES, RV.REPETICIONES, RV.N_ETIQUETAS, RV.REPETICIONES_IMPORTANCIA, RV.PROCESOS), (5, 3, 200, 20, 4))


class PruebasMetricas(unittest.TestCase):
    def test_a_mano(self):
        y = np.array([1, 1, 1, 0, 0, 0, 0, 0])
        pred = np.array([1, 1, 0, 1, 0, 0, 0, 0])
        prob = np.array([.9, .8, .4, .7, .3, .2, .1, .05])
        m = RV.metricas_ampliadas(y, prob, pred)
        self.assertAlmostEqual(m['precision_severos'], 2 / 3)
        self.assertAlmostEqual(m['sensibilidad_severos'], 2 / 3)
        self.assertAlmostEqual(m['precision_no_severos'], 4 / 5)
        self.assertAlmostEqual(m['sensibilidad_no_severos'], 4 / 5)

    def test_sin_predicciones_de_una_clase_no_divide_por_cero(self):
        y = np.array([1, 1, 0, 0])
        m = RV.metricas_ampliadas(y, np.array([.6, .6, .6, .6]), np.array([1, 1, 1, 1]))
        self.assertEqual(m['precision_no_severos'], 0.0)
        self.assertEqual(m['sensibilidad_no_severos'], 0.0)

    def test_intervalo_corregido_a_mano(self):
        d = np.arange(15) / 100
        inf, sup = RV.intervalo_corregido(d)
        from scipy import stats
        e = np.sqrt((1 / 15 + 0.25) * d.var(ddof=1)) * stats.t.ppf(0.975, 14)
        self.assertAlmostEqual(inf, d.mean() - e)
        self.assertAlmostEqual(sup, d.mean() + e)

    def test_intervalo_corregido_mas_ancho_que_el_ingenuo(self):
        d = np.random.default_rng(0).normal(0, 1, 15)
        inf, sup = RV.intervalo_corregido(d)
        self.assertGreater(sup - inf, 2 * 2.14 * d.std(ddof=1) / np.sqrt(15))

    def test_lectura(self):
        self.assertEqual(RV.lectura_diferencia(0.001, 0.02), 'Mejora respaldada')
        self.assertEqual(RV.lectura_diferencia(-0.02, -0.001), 'Empeora')
        self.assertEqual(RV.lectura_diferencia(-0.01, 0.01), 'Sin diferencia clara')

    def test_clasificar_aporte(self):
        self.assertEqual(RV.clasificar_aporte(0.005, 12), 'Aporte consistente')
        self.assertEqual(RV.clasificar_aporte(0.0049, 15), 'Aporte pequeño')
        self.assertEqual(RV.clasificar_aporte(0.05, 11), 'Aporte inestable')
        self.assertEqual(RV.clasificar_aporte(0.0, 15), 'Nulo o negativo')
        self.assertEqual(RV.clasificar_aporte(-0.01, 2), 'Nulo o negativo')

    def test_consistencia(self):
        self.assertEqual(RV.consistencia(True, 'Aporte consistente'), 'Coinciden ambos métodos')
        self.assertEqual(RV.consistencia(True, 'Aporte pequeño'), 'Shannon sí; RF aporte pequeño')
        self.assertEqual(RV.consistencia(True, 'Nulo o negativo'), 'Solo Shannon')
        self.assertEqual(RV.consistencia(False, 'Aporte consistente'), 'Solo Random Forest')
        self.assertEqual(RV.consistencia(False, 'Aporte pequeño'), 'Ninguno claro (aporte pequeño)')
        self.assertEqual(RV.consistencia(False, 'Aporte inestable'), 'Sin respaldo en ninguno')

    def test_grupos(self):
        self.assertEqual(RV.grupos_de(['dias_ejercicio_semana', 'frecuencia_fuerza', 'imc'])['Actividad física'], ('dias_ejercicio_semana', 'frecuencia_fuerza'))
        self.assertNotIn('Cuidados', RV.grupos_de(['cantidad_personas_cuida', 'imc']))
        self.assertIn('Cuidados', RV.grupos_de(['cantidad_personas_cuida', RV.SOBRECARGA]))
        self.assertIn('Trabajo', RV.grupos_de(RV.LABORALES))

    def test_importancia_solo_con_evaluacion(self):
        vista = vista_33()
        m = [x for x in RV.definir_modelos() if x.nombre == 'A'][0]
        tamanos, original = [], RF._puntajes

        def espia(pipe, X, y):
            tamanos.append(len(X))
            return original(pipe, X, y)

        with mock.patch.object(RF, '_puntajes', side_effect=espia):
            RV.evaluar_modelos(vista, [m], PEQUENO, 1, 2)
        _, y = RF.datos_de(vista, m)
        self.assertLessEqual(max(tamanos), max(len(e) for _, e in RF.particiones(y)))

    def test_senal_importa_mas_que_ruido(self):
        vista = vista_33(400)
        m = RV.Modelo('B', RV.TODAS, ('dias_ejercicio_semana', 'tabaco_frecuencia', 'edad'), 'principal', 'prueba')
        _, d = RV.evaluar_modelos(vista, [m], PEQUENO, 1, 3)
        t = RV.resumir_importancia(d, 'variable').set_index('nombre')
        self.assertEqual(t.loc['dias_ejercicio_semana', 'aporte'], 'Aporte consistente')
        self.assertEqual(t.loc['dias_ejercicio_semana', 'orden_en_modelo'], 1)
        self.assertTrue(t.loc['dias_ejercicio_semana', 'q_menor_0_10'])

    def test_iguales_con_uno_y_varios_procesos(self):
        vista = vista_33()
        modelos = [m for m in RV.definir_modelos() if m.nombre in ('A', 'D0')]
        a, ia = RV.evaluar_modelos(vista, modelos, PEQUENO, 1, 1)
        b, ib = RV.evaluar_modelos(vista, modelos, PEQUENO, 2, 1)
        pd.testing.assert_frame_equal(a, b)
        pd.testing.assert_frame_equal(ia, ib)

    def test_comparar_rechaza_tamanos_distintos(self):
        filas = [{'modelo': m, 'repeticion': 0, 'particion': k, 'conjunto': 'evaluacion', 'n': 10 if m == 'X' else 9, 'roc_auc': .6, 'balanced_accuracy': .6} for m in 'XY' for k in range(15)]
        with self.assertRaisesRegex(RuntimeError, 'no son comparables'):
            RV.comparar(pd.DataFrame(filas), {'principal': [('X', 'Y')]})


class PruebasFlujo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.vista = vista_33()
        cls.modelos = RV.definir_modelos()
        cls.rutas = RV.Rutas(Path(cls.dir.name) / 'salida')
        RV.calcular(cls.vista, cls.modelos, cls.rutas, PEQUENO, 3, 2, 2, huellas={'x': 'y'})
        cls.c, cls.d = shannon_inventado()
        cls.tablas = RV.resumir(cls.rutas, cls.modelos, {'todas': 240}, cls.c, cls.d)

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_quince_particiones_y_una_evaluacion_por_persona(self):
        t = RV.leer_crudo(self.rutas.crudo('rendimiento_particiones'))
        ev = t[t['conjunto'] == 'evaluacion']
        self.assertEqual(set(ev.groupby('modelo').size()), {15})
        self.assertEqual(set(ev.groupby('modelo').size().index), {m.nombre for m in self.modelos})
        for m in self.modelos:
            n = int(self.vista.poblaciones[m.poblacion].sum())
            self.assertEqual(ev[ev['modelo'] == m.nombre].groupby('repeticion')['n'].sum().tolist(), [n] * 3)

    def test_clasificador_sencillo(self):
        t = RV.leer_crudo(self.rutas.crudo('rendimiento_particiones'))
        ev = t[(t['conjunto'] == 'evaluacion') & t['modelo'].str.startswith('Ref_')]
        self.assertTrue((ev['roc_auc'] == 0.5).all())
        self.assertTrue((ev['balanced_accuracy'] == 0.5).all())

    def test_comparaciones_principales(self):
        t = self.tablas['comparacion_modelos']
        p = t[t['tipo'] == 'principal']
        self.assertEqual(set(zip(p['modelo'], p['referencia'])), {('B', 'A'), ('C1', 'C0'), ('D1', 'D0')})
        self.assertEqual(set(p['metrica']), {'roc_auc', 'balanced_accuracy'})
        self.assertTrue((p['particiones'] == 15).all())

    def test_tabla_de_33_filas_con_cada_variable_en_su_modelo(self):
        t = self.tablas['shannon_vs_rf']
        self.assertEqual(sorted(t['variable']), sorted(RV.VARIABLES_33))
        f = t.set_index('variable')
        self.assertEqual(f.loc[RV.SOBRECARGA, 'modelo_rf'], 'D1')
        self.assertEqual(f.loc['estres_entorno_laboral', 'modelo_rf'], 'C1')
        self.assertEqual(f.loc['imc', 'modelo_rf'], 'B')
        self.assertEqual(f.loc['trabaja_actualmente', 'modelo_rf'], 'B')
        self.assertTrue(f.loc['imc', 'q_menor_0_10'])
        self.assertIn('imputado', f.loc['imc', 'advertencias'])

    def test_orden_por_modelo_no_mezcla_poblaciones(self):
        t = self.tablas['importancia_variables']
        for modelo, g in t.groupby('modelo'):
            self.assertEqual(g['orden_en_modelo'].tolist(), list(range(1, len(g) + 1)), modelo)
        self.assertEqual(set(t['modelo']), set(RV.MODELOS_IMPORTANCIA))

    def test_sobrecarga_y_laborales_solo_en_su_poblacion(self):
        t = self.tablas['importancia_variables']
        self.assertEqual(set(t[t['nombre'] == RV.SOBRECARGA]['modelo']), {'D1', 'D1_sin_imc'})
        self.assertEqual(set(t[t['nombre'] == 'lugar_trabajo_comprensivo']['modelo']), {'C1', 'C1_sin_imc'})

    def test_grupos_en_su_modelo(self):
        t = self.tablas['importancia_grupos']
        self.assertIn('Trabajo', set(t[t['modelo'] == 'C1']['nombre']))
        self.assertNotIn('Trabajo', set(t[t['modelo'] == 'B']['nombre']))
        self.assertIn('Cuidados', set(t[t['modelo'] == 'D1']['nombre']))
        self.assertNotIn('Cuidados', set(t[t['modelo'] == 'D0']['nombre']))

    def test_azar_en_los_seis(self):
        t = self.tablas['pruebas_azar']
        self.assertEqual(set(t['modelo']), set(RV.PRINCIPALES))
        self.assertEqual(len(t), 12)

    def test_sensibilidad_sin_imc(self):
        t = self.tablas['sensibilidad_imc']
        self.assertTrue({f'{m}_sin_imc' for m in RV.PRINCIPALES} <= set(t['referencia']))
        m = self.tablas['modelos'].set_index('modelo')
        for k in RV.PRINCIPALES:
            self.assertNotIn('imc', m.loc[f'{k}_sin_imc', 'variables'].split(';'))

    def test_figuras(self):
        for f in ('rendimiento_modelos', 'comparacion_modelos', 'importancia_B', 'importancia_C1', 'importancia_D1', 'importancia_grupos', 'pruebas_azar', 'shannon_vs_rf', 'sensibilidad_imc', 'matrices_confusion'):
            self.assertGreater(self.rutas.figura(f).stat().st_size, 1000, f)

    def test_retoma_sin_recalcular_ni_sobrescribir(self):
        antes = {r: P.sha256(r) for r in self.rutas.crudo('x').parent.glob('*.csv') if r.stem != 'tiempos'}
        with mock.patch.object(RV, 'evaluar_modelos', side_effect=AssertionError('no debe recalcular')), mock.patch.object(RF, 'pruebas_azar', side_effect=AssertionError('no debe recalcular')):
            RV.calcular(self.vista, self.modelos, self.rutas, PEQUENO, 3, 2, 1)
        self.assertEqual(antes, {r: P.sha256(r) for r in antes})

    def test_crudo_no_se_sobrescribe(self):
        with self.assertRaises(FileExistsError):
            RV.escribir_crudo(self.rutas.crudo('rendimiento_particiones'), pd.DataFrame())

    def test_resumir_no_entrena(self):
        with mock.patch.object(RandomForestClassifier, 'fit', side_effect=AssertionError('no debe entrenar')):
            RV.resumir(self.rutas, self.modelos, None, self.c, self.d)

    def test_registro(self):
        texto = self.rutas.log.read_text(encoding='utf-8')
        for frase in ('HEAD', 'scikit-learn', 'Comprobaciones', 'Tiempo'):
            self.assertIn(frase, texto)


class PruebasProteccion(unittest.TestCase):
    def test_si_dos_corridas_difieren_no_guarda(self):
        vista = vista_33()
        modelos = [m for m in RV.definir_modelos() if m.nombre in ('A', 'C0', 'D1')]
        real, llamadas = RV.evaluar_modelos, []

        def alterar(*a, **k):
            llamadas.append(1)
            r, i = real(*a, **k)
            if len(llamadas) == 2:
                r = r.assign(roc_auc=r['roc_auc'] + 1e-9)
            return r, i

        with tempfile.TemporaryDirectory() as d, mock.patch.object(RV, 'evaluar_modelos', side_effect=alterar):
            rutas = RV.Rutas(Path(d) / 'n')
            with self.assertRaisesRegex(RuntimeError, 'no coinciden'):
                RV.calcular(vista, modelos, rutas, PEQUENO, 1, 1, 1)
            self.assertFalse(rutas.crudo('rendimiento_particiones').exists())
            self.assertFalse(rutas.crudo('importancia_particiones').exists())

    def test_rechaza_carpetas_anteriores(self):
        for carpeta in (R.CARPETA, R.CARPETA / 'x', RF.CARPETA, P.RUTAS_REALES.resultados, P.RUTAS_REALES.dataset.parent):
            with self.assertRaises(PermissionError, msg=carpeta):
                RV.validar_carpeta(RV.Rutas(carpeta))
        RV.validar_carpeta(RV.RUTAS)

    def test_no_lee_la_version_verdadera(self):
        fuente = Path(RV.__file__).read_text(encoding='utf-8')
        for prohibido in ('dataset_usuaria_verdad', 'bitacora_suciedad', 'dataset_fase35b.csv', 'GridSearch', 'RandomizedSearch', 'add_indicator=True', 'StandardScaler', 'feature_importances_'):
            self.assertNotIn(prohibido, fuente)

    def test_consola_no_admite_otros_parametros(self):
        import contextlib
        import io
        for extra in ('--semilla=7', '--n-estimators=10', '--permutaciones=5'):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                RV.construir_parser().parse_args(['--ejecutar', extra])

    def test_ejecutar_exige_autorizacion(self):
        import sys
        with mock.patch.object(sys, 'argv', ['p', '--ejecutar']), mock.patch.object(RV, 'estado', side_effect=AssertionError('no debe avanzar')), self.assertRaisesRegex(SystemExit, 'autorizado'):
            RV.main()

    def test_estado_ignora_solo_head(self):
        with mock.patch.object(K, 'estado_inicial', return_value=['HEAD es abc, no def.', 'Hay cambios en archivos versionados: x']):
            self.assertEqual(RV.estado(), ['Hay cambios en archivos versionados: x'])


if __name__ == '__main__':
    unittest.main()
