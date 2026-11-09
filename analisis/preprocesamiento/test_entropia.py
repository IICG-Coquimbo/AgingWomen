"""
Pruebas de la Fase 35B, solo con datos inventados.

Uso, desde la carpeta analisis:
    python -m unittest preprocesamiento.test_entropia -v
"""
import contextlib
import io
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from scipy import stats

import seleccionar_fase35b as P

from . import configuracion as C
from . import entropia as E
from . import estabilidad as S
from . import fcbf as F


def medidas_ficticias(su_objetivo, su_par, q_par=None, su_laboral=None, relevantes=None):
    """Medidas escritas a mano, para probar el recorrido sin azar."""
    relevantes = sorted(su_objetivo if relevantes is None else relevantes)
    claves = {tuple(sorted(k)): v for k, v in su_par.items()}
    q = {k: 0.001 for k in claves}
    q.update({tuple(sorted(k)): v for k, v in (q_par or {}).items()})
    return F.Medidas(su_objetivo, {v: 100 for v in su_objetivo}, {v: 0.001 for v in su_objetivo},
                     {v: 0.001 for v in su_objetivo}, relevantes, su_par=claves, n_par={k: 100 for k in claves},
                     p_par={k: 0.001 for k in claves}, q_par=q, su_objetivo_laboral=su_laboral or {})


def escenario_ficticio(candidatas, laborales=(), modo=F.COBERTURA):
    return F.Escenario('prueba', 0, {}, np.array([]), list(candidatas), set(laborales), np.array([], dtype=bool), modo)


class PruebasSU(unittest.TestCase):
    def test_independientes_da_cero(self):
        x, y = np.array([0, 0, 1, 1] * 25), np.array([0, 1, 0, 1] * 25)
        self.assertAlmostEqual(E.su(x, y), 0.0, places=12)

    def test_identicas_da_uno(self):
        x = np.array([0, 1, 2, 0, 1, 2, 2])
        self.assertAlmostEqual(E.su(x, x), 1.0, places=12)

    def test_simetria(self):
        rng = np.random.default_rng(1)
        x, y = rng.integers(0, 4, 500), rng.integers(0, 3, 500)
        self.assertAlmostEqual(E.su(x, y), E.su(y, x), delta=C.TOLERANCIA_SU_35B)

    def test_valor_calculado_a_mano(self):
        # Tabla 2x2 [[3, 1], [1, 3]]: H(X) = H(Y) = 1 y H(X,Y) = 2 - 0,75·log2(0,75) ... calculada abajo.
        x = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y = np.array([0, 0, 0, 1, 0, 1, 1, 1])
        hxy = -(2 * 3 / 8 * math.log2(3 / 8) + 2 * 1 / 8 * math.log2(1 / 8))
        self.assertAlmostEqual(E.su(x, y), 2 * (2 - hxy) / 2, places=12)

    def test_constante_da_cero_y_p_uno(self):
        x, y = np.zeros(20, dtype=int), np.arange(20) % 2
        self.assertEqual(E.su(x, y), 0.0)
        self.assertEqual(E.prueba_permutacion(y, x, 50, np.random.default_rng(0)), (0.0, 1.0))
        self.assertEqual(E.prueba_permutacion(x, y, 50, np.random.default_rng(0)), (0.0, 1.0))


class PruebasPermutacion(unittest.TestCase):
    def test_formula_del_valor_p(self):
        # Toda permutación de una variable independiente perfecta supera o iguala SU = 0: p = 1.
        x, y = np.array([0, 0, 1, 1] * 5), np.array([0, 1, 0, 1] * 5)
        self.assertEqual(E.prueba_permutacion(x, y, 99, np.random.default_rng(0))[1], 1.0)

    def test_el_conteo_de_permutaciones_usa_la_tolerancia(self):
        x = np.array([0, 1] * 50)
        # Con una tolerancia enorme toda permutación cuenta: p = 1.
        self.assertEqual(E.prueba_permutacion(x, x, 99, np.random.default_rng(0), tolerancia=2.0)[1], 1.0)
        self.assertLess(E.prueba_permutacion(x, x, 99, np.random.default_rng(0))[1], 1.0)
        self.assertEqual(C.TOLERANCIA_SU_35B, 1e-12)

    def test_la_tolerancia_corrige_empates_reales_de_redondeo(self):
        # Tablas equivalentes pueden diferir por redondeo: sin tolerancia esas permutaciones no se contarían.
        diferencias = 0
        for semilla in range(40):
            r = np.random.default_rng(semilla)
            x, y = r.integers(0, 3, 60), r.integers(0, 3, 60)
            sin = E.prueba_permutacion(x, y, 299, np.random.default_rng(semilla), tolerancia=0.0)[1]
            con = E.prueba_permutacion(x, y, 299, np.random.default_rng(semilla))[1]
            self.assertGreaterEqual(con, sin)
            diferencias += con > sin
        self.assertGreater(diferencias, 0)

    def test_valor_p_minimo(self):
        x = np.array([0, 1] * 200)
        self.assertAlmostEqual(E.prueba_permutacion(x, x, 999, np.random.default_rng(0))[1], 1 / 1000)

    def test_permutar_conserva_la_distribucion_marginal(self):
        rng = np.random.default_rng(2)
        x = rng.integers(0, 3, 300)
        barajada = rng.permuted(np.tile(x, (5, 1)), axis=1)
        for fila in barajada:
            self.assertTrue((np.bincount(fila, minlength=3) == np.bincount(x, minlength=3)).all())

    def test_por_lotes_no_altera_el_resultado(self):
        x, y = np.arange(200) % 3, np.arange(200) % 2
        a = E.prueba_permutacion(x, y, 2500, E.generador(1, 2, 3, 4))
        b = E.prueba_permutacion(x, y, 2500, E.generador(1, 2, 3, 4))
        self.assertEqual(a, b)

    def test_azar_no_es_significativo_en_general(self):
        rng = np.random.default_rng(3)
        ps = [E.prueba_permutacion(rng.integers(0, 3, 300), rng.integers(0, 2, 300), 199, rng)[1] for _ in range(60)]
        self.assertLess(np.mean(np.array(ps) < 0.05), 0.2)

    def test_relacion_real_es_significativa(self):
        rng = np.random.default_rng(4)
        x = rng.integers(0, 2, 400)
        y = np.where(rng.random(400) < 0.8, x, 1 - x)
        self.assertLess(E.prueba_permutacion(x, y, 499, rng)[1], 0.01)


class PruebasBH(unittest.TestCase):
    def test_calculado_a_mano(self):
        q = E.benjamini_hochberg([0.01, 0.04, 0.03, 0.2])
        np.testing.assert_allclose(q, [0.04, 0.16 / 3, 0.16 / 3, 0.2])

    def test_no_depende_de_la_tolerancia(self):
        p = [0.01, 0.01 + 1e-13, 0.04, 0.2]
        esperado = stats.false_discovery_control(p, method='bh')
        with mock.patch.object(C, 'TOLERANCIA_SU_35B', 1.0):
            np.testing.assert_array_equal(E.benjamini_hochberg(p), esperado)

    def test_familia_vacia(self):
        self.assertEqual(len(E.benjamini_hochberg([])), 0)


class PruebasSemillas(unittest.TestCase):
    def test_deterministas_e_independientes(self):
        a, b, c = (E.generador(1, 5, 1, 7).random(4), E.generador(1, 5, 1, 7).random(4), E.generador(1, 6, 1, 7).random(4))
        np.testing.assert_array_equal(a, b)
        self.assertFalse((a == c).all())


class PruebasDiscretizacion(unittest.TestCase):
    def test_empates_en_cuartiles(self):
        x = [1, 5, 5, 6, 7, 8, 8, 9]
        self.assertEqual(E.tramos_cerrados_derecha(x, [5, 6, 8]).tolist(), [0, 0, 0, 1, 2, 2, 2, 3])

    def test_corte_repetido_se_fusiona(self):
        self.assertEqual(E.tramos_cerrados_derecha([1, 5, 6], [5, 5, 8]).tolist(), [0, 0, 1])

    def test_edad_e_imc_cerrados_a_la_izquierda(self):
        self.assertEqual(E.tramos_cerrados_izquierda([36, 39, 40, 65], C.CORTES_EDAD_35B).tolist(), [1, 1, 2, 6])
        self.assertEqual(E.tramos_cerrados_izquierda([18.4, 18.5, 24.9, 25, 40], C.CORTES_IMC_35B).tolist(), [0, 1, 1, 2, 5])


class PruebasFCBF(unittest.TestCase):
    def test_ejemplo_lista_unica(self):
        # Ejemplo inventado: C repite a A y D repite a B; quedan A y B.
        su = {'A': 0.05, 'B': 0.04, 'C': 0.03, 'D': 0.02}
        pares = {('A', 'B'): 0.01, ('A', 'C'): 0.10, ('A', 'D'): 0.005, ('B', 'C'): 0.0, ('B', 'D'): 0.03, ('C', 'D'): 0.0}
        esc = escenario_ficticio(list(su) + ['E'], modo=F.LISTA_UNICA)
        med = medidas_ficticias({**su, 'E': 0.001}, pares, relevantes=list(su))
        d = F.seleccionar(esc, med, True)
        self.assertEqual(F.seleccionadas(d), ['A', 'B'])
        self.assertEqual((d['C']['decision'], d['C']['eliminada_por']), ('redundante', 'A'))
        self.assertEqual((d['D']['decision'], d['D']['eliminada_por']), ('redundante', 'B'))
        self.assertEqual(d['E']['decision'], 'no relevante')

    def test_q_distingue_adaptada_de_estandar(self):
        su = {'A': 0.05, 'B': 0.02}
        med = medidas_ficticias(su, {('A', 'B'): 0.03}, {('A', 'B'): 0.2})
        esc = escenario_ficticio(su, modo=F.LISTA_UNICA)
        self.assertEqual(F.seleccionadas(F.seleccionar(esc, med, True)), ['A', 'B'])
        self.assertEqual(F.seleccionadas(F.seleccionar(esc, med, False)), ['A'])

    def test_q_es_estricto(self):
        su = {'A': 0.05, 'B': 0.02}
        med = medidas_ficticias(su, {('A', 'B'): 0.03}, {('A', 'B'): C.ALFA_Q_35B})
        self.assertEqual(F.seleccionadas(F.seleccionar(escenario_ficticio(su, modo=F.LISTA_UNICA), med, True)), ['A', 'B'])

    def test_tolerancia_en_la_condicion_de_su(self):
        su = {'A': 0.05, 'B': 0.02}
        med = medidas_ficticias(su, {('A', 'B'): 0.02 - 1e-13})
        self.assertEqual(F.seleccionadas(F.seleccionar(escenario_ficticio(su, modo=F.LISTA_UNICA), med, True)), ['A'])

    def test_orden_sin_tolerancia_y_empate_alfabetico(self):
        self.assertEqual(F._orden(['B', 'A', 'C'], {'A': 0.1, 'B': 0.1, 'C': 0.1 + 1e-13}), ['C', 'A', 'B'])

    def test_orden_exacto_tambien_en_la_etapa_laboral(self):
        # LB supera a LA por 1e-13: va primero aunque LA sea anterior en el alfabeto.
        su = {'LA': 0.03, 'LB': 0.03 + 1e-13}
        med = medidas_ficticias(su, {('LA', 'LB'): 0.1}, su_laboral=su)
        d = F.seleccionar(escenario_ficticio(su, ['LA', 'LB']), med, True)
        self.assertEqual((d['LA']['decision'], d['LA']['eliminada_por']), ('redundante', 'LB'))
        self.assertEqual(d['LB']['decision'], 'seleccionada')

    def test_empate_exacto_en_la_etapa_laboral_es_alfabetico(self):
        su = {'LA': 0.03, 'LB': 0.03}
        med = medidas_ficticias(su, {('LA', 'LB'): 0.1}, su_laboral=su)
        d = F.seleccionar(escenario_ficticio(su, ['LB', 'LA']), med, True)
        self.assertEqual((d['LB']['decision'], d['LB']['eliminada_por']), ('redundante', 'LA'))

    def test_eliminadora_con_empate_exacto_es_alfabetica(self):
        su = {'NB': 0.09, 'NA': 0.09, 'L': 0.03}
        pares = {('NA', 'NB'): 0.0, ('L', 'NA'): 0.5, ('L', 'NB'): 0.5}
        med = medidas_ficticias(su, pares, su_laboral=su)
        self.assertEqual(F.seleccionar(escenario_ficticio(su, ['L']), med, True)['L']['eliminada_por'], 'NA')

    def test_tolerancia_en_la_fuerza_de_la_etapa_laboral(self):
        # SU(Z,C) >= SU(Y,C) es una condición de FCBF: usa la tolerancia, no el orden exacto.
        su = {'L': 0.03, 'N': 0.03 - 1e-13}
        med = medidas_ficticias(su, {('L', 'N'): 0.1}, su_laboral=su)
        self.assertEqual(F.seleccionar(escenario_ficticio(su, ['L']), med, True)['L']['decision'], 'redundante')

    def test_diferencia_mayor_que_la_tolerancia_no_elimina(self):
        su = {'A': 0.05, 'B': 0.02}
        med = medidas_ficticias(su, {('A', 'B'): 0.02 - 1e-11})
        self.assertEqual(F.seleccionadas(F.seleccionar(escenario_ficticio(su, modo=F.LISTA_UNICA), med, True)), ['A', 'B'])

    def test_orden_no_depende_de_la_tolerancia(self):
        with mock.patch.object(C, 'TOLERANCIA_SU_35B', 1.0):
            self.assertEqual(F._orden(['A', 'B', 'C'], {'A': 0.1, 'B': 0.3, 'C': 0.2}), ['B', 'C', 'A'])

    def test_eliminadora_no_usa_tolerancia_para_elegirse(self):
        # NB supera a NA por 1e-13: no es un empate, así que no se aplica el orden alfabético.
        su = {'NA': 0.09, 'NB': 0.09 + 1e-13, 'L': 0.03}
        pares = {('NA', 'NB'): 0.0, ('L', 'NA'): 0.5, ('L', 'NB'): 0.5}
        med = medidas_ficticias(su, pares, su_laboral=su)
        self.assertEqual(F.seleccionar(escenario_ficticio(su, ['L']), med, True)['L']['eliminada_por'], 'NB')

    def test_q_no_se_relaja_con_la_tolerancia(self):
        su = {'A': 0.05, 'B': 0.02}
        esc = escenario_ficticio(su, modo=F.LISTA_UNICA)
        with mock.patch.object(C, 'TOLERANCIA_SU_35B', 1.0):
            for q in (C.ALFA_Q_35B, C.ALFA_Q_35B + 1e-13):
                med = medidas_ficticias(su, {('A', 'B'): 0.03}, {('A', 'B'): q})
                self.assertEqual(F.seleccionadas(F.seleccionar(esc, med, True)), ['A', 'B'])

    def test_tolerancia_es_absoluta(self):
        # Con una tolerancia relativa, 5e-13 de diferencia sobre 1e-6 no alcanzaría.
        su = {'A': 0.05, 'B': 1e-6}
        med = medidas_ficticias(su, {('A', 'B'): 1e-6 - 5e-13})
        self.assertEqual(F.seleccionadas(F.seleccionar(escenario_ficticio(su, modo=F.LISTA_UNICA), med, True)), ['A'])

    def test_eliminada_no_elimina_a_otras(self):
        su = {'A': 0.05, 'B': 0.04, 'C': 0.03}
        pares = {('A', 'B'): 0.2, ('A', 'C'): 0.0, ('B', 'C'): 0.2}
        self.assertEqual(F.seleccionadas(F.seleccionar(escenario_ficticio(su, modo=F.LISTA_UNICA),
                                                       medidas_ficticias(su, pares), True)), ['A', 'C'])

    def test_laboral_nunca_elimina_a_no_laboral(self):
        su = {'L': 0.09, 'N': 0.01}
        med = medidas_ficticias(su, {('L', 'N'): 0.9}, su_laboral={'L': 0.09, 'N': 0.02})
        d = F.seleccionar(escenario_ficticio(su, ['L']), med, True)
        self.assertEqual(d['N']['decision'], 'seleccionada')
        self.assertEqual(d['L']['decision'], 'seleccionada')

    def test_el_par_no_eliminado_se_informa(self):
        su = {'L': 0.09, 'N': 0.01}
        med = medidas_ficticias(su, {('L', 'N'): 0.9}, su_laboral={'L': 0.09, 'N': 0.02})
        esc = escenario_ficticio(su, ['L'])
        filas = F.pares_no_eliminados(esc, med, F.seleccionar(esc, med, True))
        self.assertEqual([(f['laboral'], f['no_laboral']) for f in filas], [('L', 'N')])

    def test_no_laboral_elimina_a_laboral_usando_su_de_las_287(self):
        # Con n = 529, N (0,01) sería más débil que L (0,05); con las mismas 287 es más fuerte y la elimina.
        su = {'L': 0.05, 'N': 0.01}
        med = medidas_ficticias(su, {('L', 'N'): 0.2}, su_laboral={'L': 0.05, 'N': 0.06})
        d = F.seleccionar(escenario_ficticio(su, ['L']), med, True)
        self.assertEqual((d['L']['decision'], d['L']['eliminada_por']), ('redundante', 'N'))

    def test_no_laboral_mas_debil_en_287_no_elimina(self):
        # Con n = 529, N sería más fuerte; con las mismas 287 es más débil y no puede eliminar.
        su = {'L': 0.02, 'N': 0.30}
        med = medidas_ficticias(su, {('L', 'N'): 0.2}, su_laboral={'L': 0.05, 'N': 0.01})
        self.assertEqual(F.seleccionar(escenario_ficticio(su, ['L']), med, True)['L']['decision'], 'seleccionada')

    def test_etapa_laboral_exige_q(self):
        su = {'L': 0.05, 'N': 0.30}
        med = medidas_ficticias(su, {('L', 'N'): 0.2}, {('L', 'N'): 0.5}, su_laboral={'L': 0.05, 'N': 0.06})
        esc = escenario_ficticio(su, ['L'])
        self.assertEqual(F.seleccionar(esc, med, True)['L']['decision'], 'seleccionada')
        self.assertEqual(F.seleccionar(esc, med, False)['L']['decision'], 'redundante')

    def test_no_laboral_eliminada_no_participa_en_etapa_2(self):
        su = {'A': 0.10, 'B': 0.05, 'L': 0.04}
        pares = {('A', 'B'): 0.5, ('A', 'L'): 0.0, ('B', 'L'): 0.9}
        med = medidas_ficticias(su, pares, su_laboral={'A': 0.09, 'B': 0.08, 'L': 0.04})
        d = F.seleccionar(escenario_ficticio(su, ['L']), med, True)
        self.assertEqual(d['B']['decision'], 'redundante')
        self.assertEqual(d['L']['decision'], 'seleccionada')

    def test_laboral_eliminada_por_otra_laboral_mas_fuerte(self):
        su = {'L1': 0.08, 'L2': 0.03}
        med = medidas_ficticias(su, {('L1', 'L2'): 0.1}, su_laboral={'L1': 0.08, 'L2': 0.03})
        d = F.seleccionar(escenario_ficticio(su, ['L1', 'L2']), med, True)
        self.assertEqual((d['L2']['decision'], d['L2']['eliminada_por']), ('redundante', 'L1'))

    def test_eliminadora_registrada_es_la_mas_fuerte(self):
        su = {'A': 0.2, 'B': 0.1, 'L': 0.03}
        pares = {('A', 'B'): 0.0, ('A', 'L'): 0.5, ('B', 'L'): 0.5}
        med = medidas_ficticias(su, pares, su_laboral={'A': 0.05, 'B': 0.09, 'L': 0.03})
        self.assertEqual(F.seleccionar(escenario_ficticio(su, ['L']), med, True)['L']['eliminada_por'], 'B')


def datos_inventados(n=240, semilla=7):
    """Conjunto inventado con la misma forma que dataset_fase35, con una señal, una copia y ruido."""
    rng = np.random.default_rng(semilla)
    severo = rng.integers(0, 2, n)
    senal = np.where(rng.random(n) < 0.85, severo, 1 - severo)
    trabaja = (np.arange(n) % 3 != 0).astype(int)
    rng.shuffle(trabaja)
    lugar = np.where(trabaja == 1, rng.integers(1, 6, n), 0)
    estres = np.where(trabaja == 1, rng.integers(1, 6, n), 0)
    imputadas = np.flatnonzero(trabaja == 1)[:10]
    lugar[imputadas], estres[imputadas] = 3, 3
    mascara = trabaja == 1
    mascara[imputadas] = False
    tabla = pd.DataFrame({
        'participante_id': [f'p{i}' for i in range(n)], 'severo_mrs': severo, 'mrs_total': severo * 20,
        'severidad_mrs_4': np.where(severo == 1, 'Severa', 'Leve'), 'imc_fue_imputado': rng.integers(0, 2, n),
        'edad': rng.integers(36, 66, n), 'imc': rng.uniform(18, 45, n), 'usa_medicamentos_diabetes': rng.integers(0, 2, n),
        'trabaja_actualmente': trabaja, 'prevision': rng.choice(['FONASA', 'ISAPRE'], n),
        'senal': senal, 'copia_senal': senal, 'ruido': rng.integers(0, 3, n), 'horas_sedentarismo': rng.integers(1, 15, n),
        'lugar_trabajo_comprensivo': lugar, 'estres_entorno_laboral': estres, 'frutas_dia': rng.integers(1, 5, n)})
    candidatas = sorted(['senal', 'copia_senal', 'ruido', 'horas_sedentarismo', 'lugar_trabajo_comprensivo',
                         'estres_entorno_laboral', 'frutas_dia'])
    return P.Datos(tabla, mascara, candidatas, list(C.CONTROL_35B), list(C.PENDIENTES_35B), list(C.LABORALES_35B))


class PruebasMedir(unittest.TestCase):
    def test_redundancia_y_mascara_con_datos_inventados(self):
        datos = datos_inventados()
        esc = P.escenario_principal(datos)
        med = F.medir(esc, 0, 199)
        self.assertEqual(med.n_objetivo['lugar_trabajo_comprensivo'], int(datos.mascara.sum()))
        self.assertEqual(med.n_objetivo['senal'], len(datos.tabla))
        d = F.seleccionar(esc, med, True)
        lista = F.seleccionadas(d)
        self.assertEqual(len({'senal', 'copia_senal'} & set(lista)), 1)
        self.assertNotIn('ruido', lista)

    def test_el_no_aplica_no_entra_en_el_par_laboral(self):
        # Fuera de la máscara ambas valen 0: sin máscara la SU del par sería mucho mayor.
        datos = datos_inventados()
        t, m = datos.tabla, datos.mascara
        con_mascara = E.su(t['lugar_trabajo_comprensivo'][m], t['estres_entorno_laboral'][m])
        sin_mascara = E.su(t['lugar_trabajo_comprensivo'], t['estres_entorno_laboral'])
        self.assertGreater(sin_mascara, con_mascara + 0.1)
        esc = P.escenario_principal(datos)
        esc = F.replace(esc, candidatas=list(C.LABORALES_35B))
        with mock.patch.object(C, 'ALFA_Q_35B', 1.01):   # fuerza que el par se calcule
            med = F.medir(esc, 0, 49)
        clave = tuple(sorted(C.LABORALES_35B))
        self.assertAlmostEqual(med.su_par[clave], con_mascara, places=12)
        self.assertEqual(med.n_par[clave], int(m.sum()))

    def test_relevancia_exige_q_estricto_sin_tolerancia(self):
        esc = P.escenario_principal(datos_inventados())
        with mock.patch.object(C, 'TOLERANCIA_SU_35B', 1.0):
            with mock.patch.object(E, 'benjamini_hochberg', side_effect=lambda p: np.full(len(p), C.ALFA_Q_35B)):
                self.assertEqual(F.medir(esc, 0, 9).relevantes, [])
            with mock.patch.object(E, 'benjamini_hochberg', side_effect=lambda p: np.full(len(p), C.ALFA_Q_35B - 1e-13)):
                self.assertEqual(len(F.medir(esc, 0, 9).relevantes), len(esc.candidatas))

    def test_medir_es_reproducible(self):
        esc = P.escenario_principal(datos_inventados())
        a, b = F.medir(esc, 0, 99), F.medir(esc, 0, 99)
        self.assertEqual(a.p_objetivo, b.p_objetivo)
        self.assertEqual(a.p_par, b.p_par)

    def test_bootstrap_estratificado_conserva_las_clases(self):
        y = np.array([0] * 30 + [1] * 70)
        idx = F.indices_bootstrap(y, np.random.default_rng(0))
        self.assertEqual(np.bincount(y[idx]).tolist(), [30, 70])
        self.assertLess(len(set(idx.tolist())), 100)

    def test_escenarios_de_sensibilidad_son_los_del_protocolo(self):
        datos = datos_inventados()
        escs = P.escenarios_sensibilidad(datos)
        self.assertEqual([e.id_analisis for e in escs], [11, 12, 20, 30, 40, 50])
        s3, s4, s5 = escs[3], escs[4], escs[5]
        self.assertEqual(int(s3.mascara.sum()), int((datos.tabla['trabaja_actualmente'] == 1).sum()))
        self.assertEqual(s4.modo, F.LISTA_UNICA)
        self.assertEqual(len(s5.objetivo), int(datos.mascara.sum()))
        self.assertEqual(s5.modo, F.LISTA_UNICA)


class PruebasEstabilidad(unittest.TestCase):
    def test_identicas_da_uno(self):
        Z = [[1, 1, 0, 0]] * 5
        r = S.nogueira(Z)
        self.assertAlmostEqual(r['indice'], 1.0)
        self.assertAlmostEqual(r['ic_inferior'], 1.0)

    @staticmethod
    def _teorema7(Z):
        """Transcripción con bucles de la Definición 4, el Teorema 7 y el Corolario 8 de Nogueira et al. (2018)."""
        Z = np.asarray(Z, dtype=float)
        M, d = Z.shape
        p = [sum(Z[i][f] for i in range(M)) / M for f in range(d)]
        k = [sum(Z[i]) for i in range(M)]
        kb = sum(k) / M
        den = (kb / d) * (1 - kb / d)
        indice = 1 - (sum(M / (M - 1) * p[f] * (1 - p[f]) for f in range(d)) / d) / den
        fi = [(sum(Z[i][f] * p[f] for f in range(d)) / d - k[i] * kb / d ** 2
               + indice / 2 * (2 * kb * k[i] / d ** 2 - k[i] / d - kb / d + 1)) / den for i in range(M)]
        media = sum(fi) / M
        v = 4 / M ** 2 * sum((x - media) ** 2 for x in fi)
        z = 1.959963984540054
        return indice, indice - z * math.sqrt(v), indice + z * math.sqrt(v)

    def test_nogueira_coincide_con_el_teorema_7(self):
        rng = np.random.default_rng(2026)
        for _ in range(200):
            M, d = int(rng.integers(2, 80)), int(rng.integers(2, 40))
            Z = (rng.random((M, d)) < rng.random(d)).astype(int)
            if Z.sum() in (0, M * d):
                continue
            r, t = S.nogueira(Z), self._teorema7(Z)
            for valor, esperado in zip((r['indice'], r['ic_inferior'], r['ic_superior']), t):
                self.assertAlmostEqual(valor, esperado, places=12)

    def test_nogueira_cota_inferior_del_articulo(self):
        # El mínimo es -1/(M-1): se alcanza con k = d/2 y selecciones repartidas por igual.
        Z = [[1, 1, 0, 0], [0, 0, 1, 1], [1, 1, 0, 0], [0, 0, 1, 1]]
        self.assertAlmostEqual(S.nogueira(Z)['indice'], -1 / 3)

    def test_nogueira_calculado_a_mano(self):
        self.assertAlmostEqual(S.nogueira([[1, 1, 0, 0], [0, 0, 1, 1]])['indice'], -1.0)
        self.assertAlmostEqual(S.nogueira([[1, 1, 0, 0], [1, 0, 1, 0]])['indice'], 0.0)

    def test_nogueira_no_calculable(self):
        self.assertTrue(math.isnan(S.nogueira([[0, 0], [0, 0]])['indice']))
        self.assertTrue(math.isnan(S.nogueira([[1, 1], [1, 1]])['indice']))

    def test_ic_contiene_al_indice(self):
        Z = np.random.default_rng(0).integers(0, 2, (200, 10))
        r = S.nogueira(Z)
        self.assertLess(r['ic_inferior'], r['indice'])
        self.assertLess(r['indice'], r['ic_superior'])

    def test_jaccard(self):
        self.assertEqual(S.jaccard([], []), 1.0)
        self.assertEqual(S.jaccard(['a', 'b'], ['b', 'c']), 1 / 3)
        self.assertAlmostEqual(S.jaccard_promedio([[1, 1, 0], [0, 1, 1], [0, 0, 0], [0, 0, 0]]),
                               (1 / 3 + 0 + 0 + 0 + 0 + 1) / 6)

    def test_bandas(self):
        self.assertEqual([S.banda(x) for x in (80, 79.9, 50, 49.9)], ['>= 80 %', '50-79 %', '50-79 %', '< 50 %'])


class PruebasIntegridad(unittest.TestCase):
    def test_detecta_cambios(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'a.csv'
            ruta.write_text('1', encoding='utf-8')
            antes = P.manifiesto([ruta])
            ruta.write_text('2', encoding='utf-8')
            self.assertEqual(P.comparar_manifiestos(antes, P.manifiesto([ruta])), [str(ruta)])

    def _rutas(self, d):
        d = Path(d)
        return P.Rutas(d / 'res', d / 'fig', d / 'informe.md', d / 'dataset.csv', d / 'cache', d / 'log.txt')

    def test_escritor_rechaza_rutas_no_declaradas(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):
                P.Escritor(self._rutas(d)).texto(Path(d) / 'otro.txt', 'x')

    def test_escritor_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = self._rutas(d)
            rutas.log.write_text('previo', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                P.Escritor(rutas).texto(rutas.log, 'x')
            self.assertEqual(rutas.log.read_text(encoding='utf-8'), 'previo')

    def test_las_salidas_reales_no_tocan_archivos_de_la_35a(self):
        declaradas = {p.name for p in P.RUTAS_REALES.declaradas()}
        for nombre in ('dataset_fase35.csv', 'informe_preprocesamiento_fase35.md', 'decisiones_preprocesamiento.csv',
                       'pares_asociacion_todos.csv', 'log_eda_fase34c_35.txt'):
            self.assertNotIn(nombre, declaradas)
        self.assertFalse(P.RUTAS_REALES.declaradas() & set(P.archivos_protegidos()))

    def test_ejecutar_exige_autorizacion(self):
        with mock.patch('sys.argv', ['x', '--ejecutar']), mock.patch.object(P, 'correr') as correr:
            with self.assertRaises(SystemExit):
                P.main()
            correr.assert_not_called()

    def test_argumento_es_obligatorio(self):
        with mock.patch('sys.argv', ['x']), mock.patch.object(P, 'correr') as correr, mock.patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                P.main()
            correr.assert_not_called()

    def test_controles_detectan_subconjunto_incorrecto(self):
        datos = datos_inventados()
        esc = P.escenario_principal(datos)
        med = F.medir(esc, 0, 49)
        P.controlar_seleccion(esc, med, F.seleccionar(esc, med, True))
        med.n_objetivo['lugar_trabajo_comprensivo'] = len(datos.tabla)
        with self.assertRaisesRegex(RuntimeError, 'su relevancia no usa'):
            P.controlar_seleccion(esc, med, F.seleccionar(esc, med, True))

    def _escenario_n_par(self):
        """529 personas, 287 con respuesta laboral; pares con una y dos laborales, y uno sin laborales."""
        mascara = np.zeros(529, dtype=bool)
        mascara[:287] = True
        esc = F.replace(escenario_ficticio(['L1', 'L2', 'N1', 'N2'], ['L1', 'L2']), mascara=mascara)
        su = {'L1': 0.08, 'L2': 0.07, 'N1': 0.06, 'N2': 0.05}
        pares = {('L1', 'L2'): 0.0, ('L1', 'N1'): 0.0, ('L1', 'N2'): 0.0, ('L2', 'N1'): 0.0, ('L2', 'N2'): 0.0, ('N1', 'N2'): 0.0}
        med = medidas_ficticias(su, pares, su_laboral=su)
        med.n_objetivo.update({'L1': 287, 'L2': 287, 'N1': 529, 'N2': 529})
        med.n_par.update({k: (287 if {'L1', 'L2'} & set(k) else 529) for k in med.n_par})
        return esc, med

    def test_control_n_par_acepta_tamanos_correctos(self):
        esc, med = self._escenario_n_par()
        P.controlar_seleccion(esc, med, F.seleccionar(esc, med, True))

    def test_control_n_par_detecta_tamano_incorrecto(self):
        for par in (('L1', 'L2'), ('L1', 'N1'), ('L2', 'N2')):
            for n in (286, 288, 309, 529):
                with self.subTest(par=par, n=n):
                    esc, med = self._escenario_n_par()
                    med.n_par[par] = n
                    with self.assertRaisesRegex(RuntimeError, r'el par no usa las 287 observaciones laborales'):
                        P.controlar_seleccion(esc, med, F.seleccionar(esc, med, True))

    def test_controles_detectan_laboral_que_elimina_no_laboral(self):
        esc = escenario_ficticio(['L', 'N'], ['L'])
        esc = F.replace(esc, mascara=np.ones(100, dtype=bool))
        med = medidas_ficticias({'L': 0.1, 'N': 0.05}, {('L', 'N'): 0.5}, su_laboral={'L': 0.1, 'N': 0.05})
        decisiones = {'L': {'decision': 'seleccionada', 'eliminada_por': ''},
                      'N': {'decision': 'redundante', 'eliminada_por': 'L'}}
        with self.assertRaises(RuntimeError):
            P.controlar_seleccion(esc, med, decisiones)

    def test_ejecucion_completa_con_datos_inventados(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = self._rutas(d)
            datos = datos_inventados()
            original = datos.tabla.copy()
            r = P.correr(datos, rutas, 49, 6, 2)
            for ruta in rutas.declaradas():
                self.assertTrue(ruta.exists(), ruta)
            pd.testing.assert_frame_equal(datos.tabla, original)
            salida = P.leer_exacto(rutas.dataset)
            self.assertEqual(list(salida.columns), P.NO_PREDICTORAS + C.CONTROL_35B + r['final'])
            self.assertNotIn('prevision', salida.columns)
            for v in salida.columns:
                self.assertTrue((salida[v].to_numpy() == original[v].to_numpy()).all(), v)
            self.assertEqual(rutas.log.read_text(encoding='utf-8').count(r['huella']), 1)
            self.assertEqual(len(pd.read_csv(rutas.csv('estabilidad_remuestreos'))), 12)
            self.assertEqual(set(pd.read_csv(rutas.csv('sensibilidad_fcbf'))['escenario'].str[:2]),
                             {'S1', 'S2', 'S3', 'S4', 'S5'})
            texto = rutas.informe.read_text(encoding='utf-8')
            for frase in ('FCBF adaptado por cobertura', 'FCBF estándar por cobertura', 'FCBF completo con n = 287',
                          'Carácter sintético', 'Circularidad', 'extrapolaciones'):
                self.assertIn(frase, texto)
            # Reejecutar no sobrescribe nada.
            with self.assertRaises(FileExistsError):
                P.correr(datos, rutas, 49, 6, 2)

    def test_dataset_no_redondea_con_los_decimales_de_resultados(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = self._rutas(d)
            tabla = pd.DataFrame({'participante_id': ['p1'], 'imc': [27.123456789012345]})
            P.Escritor(rutas).tabla(rutas.dataset, tabla, formato=None)
            self.assertEqual(P.leer_exacto(rutas.dataset)['imc'][0], 27.123456789012345)
            P.Escritor(rutas).tabla(rutas.csv('su_pares'), tabla)
            self.assertEqual(P.leer_exacto(rutas.csv('su_pares'))['imc'][0], 27.123457)

    def test_huella_cambia_con_el_codigo_y_con_los_datos(self):
        esc = P.escenario_principal(datos_inventados())
        base = P.huella_cache(esc, 49)
        self.assertEqual(P.huella_cache(esc, 49), base)
        self.assertNotEqual(P.huella_cache(esc, 99), base)
        self.assertNotEqual(P.huella_cache(F.replace(esc, id_analisis=9), 49), base)
        self.assertNotEqual(P.huella_cache(F.replace(esc, objetivo=1 - esc.objetivo), 49), base)
        with mock.patch.object(P, 'huella_codigo', return_value='otra version'):
            self.assertNotEqual(P.huella_cache(esc, 49), base)

    def test_huella_de_codigo_cambia_si_cambia_un_archivo(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'modulo.py'
            ruta.write_text('a = 1', encoding='utf-8')
            with mock.patch.object(P, 'ARCHIVOS_CALCULO', [ruta]):
                antes = P.huella_codigo()
                ruta.write_text('a = 2', encoding='utf-8')
                self.assertNotEqual(P.huella_codigo(), antes)

    def test_cache_de_otra_version_detiene_la_fase_sin_borrarla(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = self._rutas(d)
            guardado = P.preparar_cache(rutas, 'version1') / 'rem_0000.json'
            guardado.write_text('{}', encoding='utf-8')
            self.assertEqual(P.preparar_cache(rutas, 'version1'), guardado.parent)   # misma versión: se reutiliza
            with self.assertRaisesRegex(RuntimeError, 'otra versión'):
                P.preparar_cache(rutas, 'version2')
            self.assertTrue(guardado.exists())
            self.assertFalse((rutas.cache / 'version2').exists())

    def test_flujo_con_cache_de_otra_version_no_reutiliza(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = self._rutas(d)
            (rutas.cache / 'version_anterior').mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, 'otra versión'):
                P.correr(datos_inventados(), rutas, 19, 1, 1)
            self.assertFalse(rutas.dataset.exists())

    def test_ejecutar_exige_codigo_congelado(self):
        with mock.patch('sys.argv', ['x', '--ejecutar', '--autorizado-por-usuaria']), \
                mock.patch.object(P, 'codigo_sin_congelar', return_value=[' M fcbf.py']), \
                mock.patch.object(P, 'verificar') as verificar, mock.patch.object(P, 'correr') as correr:
            with self.assertRaisesRegex(SystemExit, 'no está congelado'):
                P.main()
            verificar.assert_not_called()
            correr.assert_not_called()

    def test_git_que_falla_no_cuenta_como_congelado(self):
        with mock.patch.object(P.subprocess, 'run', return_value=mock.Mock(returncode=128, stdout='')):
            self.assertTrue(P.codigo_sin_congelar())

    def test_ejecucion_autorizada_usa_los_parametros_del_protocolo(self):
        with mock.patch('sys.argv', ['x', '--ejecutar', '--autorizado-por-usuaria']), \
                mock.patch.object(P, 'codigo_sin_congelar', return_value=[]), \
                mock.patch.object(P, 'verificar', return_value=[]), mock.patch.object(P, 'archivos_protegidos', return_value=[]), \
                mock.patch.object(P, 'cargar', return_value=(datos_inventados(), None)), \
                mock.patch.object(P, 'correr', return_value={'final': []}) as correr, \
                contextlib.redirect_stdout(io.StringIO()):
            P.main()
        self.assertEqual(correr.call_args.args[1:], (P.RUTAS_REALES, 5000, 500, 11))

    def test_protocolo_solo_admite_la_seccion_12_al_final(self):
        seccion = '\n## 12. Tolerancia numérica\n\nTexto.\n'
        with tempfile.TemporaryDirectory() as d:
            antes, ahora = Path(d) / 'antes.md', Path(d) / 'ahora.md'
            antes.write_bytes(b'# Protocolo\n\nRegla original.\n')
            for contenido, esperado in (('# Protocolo\n\nRegla original.\n' + seccion, True),
                                        ('# Protocolo\r\n\r\nRegla original.\r\n' + seccion.replace('\n', '\r\n'), True),
                                        ('# Protocolo\n\nRegla original.\n', False),
                                        ('# Protocolo\n\nRegla cambiada.\n' + seccion, False),
                                        ('# Protocolo\n\nRegla original.\n' + seccion + '\n## 13. Otra\n', False)):
                ahora.write_bytes(contenido.encode('utf-8'))
                self.assertEqual(P.protocolo_conservado(antes, ahora), esperado, contenido)

    def test_protocolo_establece_la_regla_de_tolerancia(self):
        texto = P.PROTOCOLO.read_text(encoding='utf-8')
        seccion = texto[texto.index('## 12. Tolerancia numérica'):]
        for frase in ('tolerancia absoluta τ = 1e-12 exclusivamente', 'SU permutada ≥ SU observada − τ', 'Ordenar las variables por SU',
                      'Determinar empates', 'corrección de Benjamini-Hochberg', 'q < 0,05 es una comparación estricta',
                      'únicamente cuando los valores de SU son exactamente iguales'):
            self.assertIn(frase, seccion)
        self.assertEqual(C.TOLERANCIA_SU_35B, 1e-12)

    def test_paralelo_igual_a_secuencial_y_cache(self):
        from joblib import Parallel, delayed
        esc = P.escenario_principal(datos_inventados())
        esc = F.replace(esc, id_analisis=P.ID_ESTABILIDAD)
        uno = [F.un_remuestreo(esc, i, 49) for i in range(4)]
        varios = Parallel(n_jobs=C.N_PROCESOS_35B)(delayed(F.un_remuestreo)(esc, i, 49) for i in range(4))
        self.assertEqual(uno, varios)
        with tempfile.TemporaryDirectory() as d:
            primero = F.un_remuestreo(esc, 0, 49, d)
            with mock.patch.object(F, 'medir', side_effect=AssertionError('no debía recalcular')):
                self.assertEqual(F.un_remuestreo(esc, 0, 49, d), primero)
            self.assertEqual(primero, uno[0])


if __name__ == '__main__':
    unittest.main()
