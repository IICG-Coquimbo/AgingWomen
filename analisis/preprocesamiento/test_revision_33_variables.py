"""
Pruebas de la corrección de 34 a 33 variables. Desde analisis/:
    python -m unittest preprocesamiento.test_revision_33_variables

Las clases de salidas leen los archivos generados y se omiten si aún no existen.
"""
import csv
import io
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import informe_integrado_35b as I
import revision_33_variables as T
import revision_35b_reunion_1103 as R
from preprocesamiento import entropia as E

SALIDAS_LISTAS = (T.CARPETA / 'log_revision_33.txt').exists()


def bh_independiente(p):
    """Benjamini-Hochberg escrito aparte de la función del proyecto."""
    p = np.asarray(p, dtype=float)
    orden = np.argsort(p)
    q = p[orden] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    salida = np.empty(len(p))
    salida[orden] = np.minimum(q, 1)
    return salida


def leer(ruta):
    return pd.read_csv(ruta, encoding='utf-8-sig', keep_default_na=False, na_values=[''])


class Lista(unittest.TestCase):
    def test_33_variables_acordadas(self):
        self.assertEqual(len(T.VARIABLES_33), 33)
        self.assertNotIn(T.EXCLUIDA, T.VARIABLES_33)
        for v in ('edad', 'imc', 'trabaja_actualmente', 'cantidad_personas_cuida', 'sobrecarga_fisica_emocional'):
            self.assertIn(v, T.VARIABLES_33)
        for v in ('doble_carga', 'prevision'):
            self.assertNotIn(v, T.VARIABLES_33)


class ColumnaDataset(unittest.TestCase):
    ORIGINAL = [['id', 'a', T.EXCLUIDA, 'b'], ['1', '1.50', '0', ''], ['2', '2,3', '1', 'x']]

    def test_quita_solo_la_columna(self):
        nueva = T.quitar_columna(self.ORIGINAL, T.EXCLUIDA)
        self.assertEqual(nueva, [['id', 'a', 'b'], ['1', '1.50', ''], ['2', '2,3', 'x']])
        tabla = T.comparar_columnas(self.ORIGINAL, nueva)
        self.assertEqual(T.problemas_columnas(tabla, self.ORIGINAL, nueva), [])

    def test_conserva_texto_y_comillas(self):
        nueva = T.quitar_columna(self.ORIGINAL, T.EXCLUIDA)
        leida = list(csv.reader(io.StringIO(T.filas_a_bytes(nueva, '\r\n').decode('utf-8-sig'), newline='')))
        self.assertEqual(leida, nueva)

    def test_detecta_un_valor_alterado(self):
        nueva = T.quitar_columna(self.ORIGINAL, T.EXCLUIDA)
        nueva[1][1] = '1.5'
        tabla = T.comparar_columnas(self.ORIGINAL, nueva)
        self.assertTrue(T.problemas_columnas(tabla, self.ORIGINAL, nueva))

    def test_detecta_filas_reordenadas_y_columna_presente(self):
        nueva = T.quitar_columna(self.ORIGINAL, T.EXCLUIDA)
        nueva[1], nueva[2] = nueva[2], nueva[1]
        self.assertTrue(T.problemas_columnas(T.comparar_columnas(self.ORIGINAL, nueva), self.ORIGINAL, nueva))
        self.assertTrue(T.problemas_columnas(T.comparar_columnas(self.ORIGINAL, self.ORIGINAL), self.ORIGINAL, self.ORIGINAL))


class SinPermutaciones(unittest.TestCase):
    def test_permutar_detiene_y_se_restaura(self):
        original = E.prueba_permutacion
        with T.sin_permutaciones():
            with self.assertRaises(RuntimeError):
                E.prueba_permutacion(None, None, 1, None)
        self.assertIs(E.prueba_permutacion, original)


class Conteos(unittest.TestCase):
    def test_k_desde_p(self):
        self.assertEqual(T.k_desde_p([round(24 / 10001, 6)], 10000)[0], 23)
        self.assertEqual(T.k_desde_p([round(103 / 50001, 6)], 50000)[0], 102)

    def test_rechaza_p_que_no_es_conteo(self):
        with self.assertRaises(RuntimeError):
            T.k_desde_p([0.00125], 50000)

    def test_dominancia(self):
        self.assertEqual(T.dominancia([0, 0, 0, 1])[1:], (3, 4, 75.0))


class DatosReales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos, cls.poblacion, cls.problemas = R.comprobar_datos_reales()
        cls.esc34, cls.esc, cls.versiones = T.calcular(cls.datos, cls.poblacion)

    def test_datos_correctos(self):
        self.assertEqual(self.problemas, [])

    def test_dominancia_exacta(self):
        d = self.datos.tabla[T.EXCLUIDA]
        self.assertEqual((int((d == 0).sum()), len(d)), (463, 529))
        self.assertGreater(100 * 463 / 529, T.UMBRAL_DOMINANCIA)

    def test_ninguna_otra_supera_el_umbral(self):
        self.assertEqual(T.problemas_dominancia(T.tabla_dominancia(self.datos, self.esc34)), [])

    def test_regla_detecta_otra_variable_sobre_el_umbral(self):
        t = T.tabla_dominancia(self.datos, self.esc34)
        t.loc[t['variable'] == 'edad', 'supera_85_regla'] = True
        self.assertTrue(T.problemas_dominancia(t))

    def test_indices_no_se_mueven(self):
        i34, i33 = self.esc34.indice(), self.esc.indice()
        self.assertEqual(len(i33), 33)
        self.assertEqual((i33['usa_medicamentos_presion'], i33['vasos_agua_dia']), (32, 33))
        self.assertTrue(all(i34[v] == i for v, i in i33.items()))

    def test_poblaciones_iguales(self):
        for v in T.VARIABLES_33:
            self.assertTrue((self.esc.mascara_de(v) == self.esc34.mascara_de(v)).all(), v)
        self.assertEqual((int(self.esc.base.mascara.sum()), int(self.esc.poblacion.sum())), (287, 239))

    def test_bh_con_implementacion_independiente(self):
        for n, (_, _, ev) in self.versiones.items():
            m = ev.medidas
            variables = sorted(m.p_objetivo)
            self.assertEqual(len(variables), 33)
            np.testing.assert_allclose([m.q_objetivo[v] for v in variables], bh_independiente([m.p_objetivo[v] for v in variables]), atol=1e-12, err_msg=str(n))

    def test_p_exactos_desde_k_guardado(self):
        for n, (t, g, _) in self.versiones.items():
            guardado = g['relevancia_34'].set_index('variable')
            for f in t['relevancia_33'].itertuples():
                self.assertEqual(f.k, int(guardado.loc[f.variable, 'k']))
                self.assertAlmostEqual(f.p, (f.k + 1) / (n + 1), places=15)

    def test_seis_relevantes_y_ningun_rastro_de_la_excluida(self):
        esperadas = ['dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'imc', 'lugar_trabajo_comprensivo', 'trabaja_actualmente']
        for _, (t, _, ev) in self.versiones.items():
            self.assertEqual(ev.medidas.relevantes, esperadas)
            for df in t.values():
                self.assertFalse(df.astype(str).isin([T.EXCLUIDA]).any().any())

    def test_cambio_de_relevantes_detiene(self):
        g = self.versiones[10000][1]
        pares = g['pares_relevantes'][g['pares_relevantes']['variable_1'] != 'imc']
        pares = pares[pares['variable_2'] != 'imc']
        with self.assertRaises(RuntimeError):
            T.medidas_33(self.esc, g['relevancia_34'], pares, 10000)

    def test_su_alterada_detiene(self):
        g = self.versiones[10000][1]
        r = g['relevancia_34'].copy()
        r.loc[r['variable'] == 'edad', 'su'] += 0.001
        with self.assertRaises(RuntimeError):
            T.medidas_33(self.esc, r, g['pares_relevantes'], 10000)

    def test_par_con_la_excluida_detiene(self):
        g = self.versiones[10000][1]
        pares = g['pares_relevantes'].copy()
        pares.loc[0, 'variable_1'] = T.EXCLUIDA
        with self.assertRaises(RuntimeError):
            T.medidas_33(self.esc, g['relevancia_34'], pares, 10000)

    def test_clases_con_regla_original(self):
        for _, (t, _, _) in self.versiones.items():
            d = t['direccion_resumen'].merge(t['relevancia_33'][['variable', 'q']], on='variable')
            for f in d.itertuples():
                self.assertEqual(f.clase, R.clasificar_factor(f.direccion, f.q, f.rho_q))
            con = d[d['rho_q'].notna()]
            self.assertEqual(len(con), 32)

    def test_decisiones_fcbf_coinciden_con_las_34_sin_la_excluida(self):
        for _, (t, g, _) in self.versiones.items():
            columnas = ['variante', 'variable', 'decision', 'eliminada_por']
            a = g['decisiones_fcbf'][g['decisiones_fcbf']['variable'] != T.EXCLUIDA][columnas].fillna('').sort_values(['variante', 'variable']).reset_index(drop=True)
            b = t['decisiones_fcbf'][columnas].fillna('').sort_values(['variante', 'variable']).reset_index(drop=True)
            pd.testing.assert_frame_equal(a, b)

    def test_sensibilidades_mismo_p(self):
        for _, (t, g, _) in self.versiones.items():
            self.assertEqual(t['sensibilidades']['p'].tolist(), g['sensibilidades']['p'].tolist())

    def test_informe_integrado_acepta_las_dos_versiones(self):
        c = I.tabla_comparacion(T.alias(self.versiones[10000][0]), T.alias(self.versiones[50000][0]))
        self.assertEqual(sorted(c['variable']), T.VARIABLES_33)
        self.assertFalse(c['cambia_relevancia'].any())
        self.assertTrue(c['compatible_monte_carlo'].all())


@unittest.skipUnless(SALIDAS_LISTAS, 'Las salidas aún no se generan.')
class Salidas(unittest.TestCase):
    def test_dataset_columna_por_columna(self):
        o = pd.read_csv(T.DATASET_ORIGINAL, encoding='utf-8-sig', dtype=str, keep_default_na=False)
        n = pd.read_csv(T.DATASET_33, encoding='utf-8-sig', dtype=str, keep_default_na=False)
        self.assertEqual(n.shape, (529, 39))
        pd.testing.assert_frame_equal(o.drop(columns=T.EXCLUIDA), n)

    def test_csv_igual_a_lo_calculado(self):
        for carpeta, nombre, n in ((T.VERSIONES[10000][2], 'q', 10000), (T.VERSIONES[50000][2], 'q', 50000)):
            r = leer(carpeta / 'relevancia_33.csv')
            self.assertEqual(sorted(r['variable']), T.VARIABLES_33)
            np.testing.assert_allclose(r['q'], bh_independiente((r['k'] + 1) / (n + 1)), atol=6e-7)

    def test_comparacion_tiene_34_filas_y_su_p_identicos(self):
        for n in (10000, 50000):
            c = leer(T.CARPETA / 'comparacion_34_33' / f'comparacion_{n}.csv')
            self.assertEqual(len(c), 34)
            self.assertTrue(c['su_identica'].all() and c['p_identico'].all())
            self.assertEqual(c[c['variable'] == T.EXCLUIDA]['clase_33'].iloc[0], 'Excluida por dominancia')

    def test_informe_sin_columna_de_q_antiguo(self):
        c = leer(T.CARPETA / 'informe' / 'comparacion_10000_50000.csv')
        for n in (10000, 50000):
            r = leer(T.VERSIONES[n][2] / 'relevancia_33.csv').set_index('variable')
            np.testing.assert_allclose(c.set_index('variable')[f'q_{n}'], r.loc[c['variable'], 'q'], atol=2e-6)


if __name__ == '__main__':
    unittest.main()
