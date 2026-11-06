"""
Pruebas del informe integrado de la revisión de la Fase 35B. Lee los resultados guardados y no calcula permutaciones.
Uso, desde analisis/: python -m unittest preprocesamiento.test_informe_integrado_35b
"""
import unittest

import numpy as np

import informe_integrado_35b as I
import revision_35b_reunion_1103 as R

from . import entropia as E


class PruebasCalculo(unittest.TestCase):
    def test_z_a_mano(self):
        k, total = 100, 500
        p = 501 / 50001
        esperado = (100 / 10000 - 400 / 40000) / np.sqrt(p * (1 - p) * (1 / 10000 + 1 / 40000))
        self.assertAlmostEqual(float(I.z_incrementos([k], [total])[0]), esperado)
        self.assertAlmostEqual(float(I.z_incrementos([100], [500])[0]), 0.0)
        self.assertGreater(float(I.z_incrementos([200], [500])[0]), I.Z_BONFERRONI)

    def test_descomposicion_suma_la_diferencia(self):
        rng = np.random.default_rng(1)
        a = rng.random(34) ** 2
        b = np.clip(a + rng.normal(0, 0.002, 34), 1e-4, 1)
        propio, resto = I.descomponer_q(a, b)
        np.testing.assert_allclose(propio + resto, E.benjamini_hochberg(b) - E.benjamini_hochberg(a))

    def test_interpretar_no_exagera(self):
        self.assertIn('Se mantiene bajo', I.interpretar(True, True, 0.003, 1.0))
        self.assertIn('Se mantiene sobre', I.interpretar(False, False, 0.003, 1.0))
        self.assertIn('no es un cambio en la asociación', I.interpretar(True, True, 0.003, 1.0))
        self.assertIn('no un cambio en la asociación', I.interpretar(True, False, 0.003, 1.0))
        self.assertIn('otra causa técnica', I.interpretar(True, True, 0.003, 4.0))


class PruebasResultadosGuardados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a, cls.b = I.leer_version(I.CARPETA_A), I.leer_version(I.CARPETA_B)
        cls.c = I.tabla_comparacion(cls.a, cls.b)

    def test_34_variables_y_misma_su(self):
        self.assertEqual(sorted(self.c['variable']), R.VARIABLES_34)
        self.assertNotIn('doble_carga', set(self.c['variable']))
        self.assertNotIn('prevision', set(self.c['variable']))

    def test_columnas_pedidas(self):
        for col in ('su', 'p_10000', 'q_10000', 'p_50000', 'q_50000', 'relevante_10000', 'relevante_50000', 'cambia_relevancia', 'interpretacion'):
            self.assertIn(col, self.c.columns)

    def test_rechaza_familias_o_su_distintas(self):
        import copy
        b = copy.deepcopy(self.b)
        b['relevancia_34'].loc[0, 'su'] += 0.001
        with self.assertRaises(RuntimeError):
            I.tabla_comparacion(self.a, b)
        b = copy.deepcopy(self.b)
        b['relevancia_34'].loc[0, 'q'] = 0.5
        with self.assertRaises(RuntimeError):
            I.tabla_comparacion(self.a, b)
        b = copy.deepcopy(self.b)
        b['relevancia_34'] = b['relevancia_34'].iloc[1:]
        with self.assertRaises(RuntimeError):
            I.tabla_comparacion(self.a, b)

    def test_direccion_no_depende_de_las_permutaciones(self):
        self.assertTrue(self.a['direccion_resumen'].drop(columns='clase').equals(self.b['direccion_resumen'].drop(columns='clase')))
        self.assertTrue(self.a['direccion_categorias'].equals(self.b['direccion_categorias']))

    def test_primeros_sorteos_incluidos(self):
        self.assertTrue((self.c['k_50000'] >= self.c['k_10000']).all())

    def test_versiones_previas_rotuladas(self):
        t = I.tabla_versiones_previas()
        self.assertTrue({'E1', 'E3', 'E4', 'C3', 'C4'} <= set(t['version_previa']))
        self.assertEqual(t[t['version_previa'] == 'E1']['estado'].iloc[0], 'Oficial anterior')
        self.assertTrue(t['composicion'].str.contains('doble_carga').all())


if __name__ == '__main__':
    unittest.main()
