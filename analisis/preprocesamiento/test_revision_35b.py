"""
Pruebas de la revisión de la Fase 35B (reunión del 03-11-2026).

Usan datos inventados, salvo `PruebasDatosReales`, que solo cuenta poblaciones y lista variables: con los datos reales
no calculan SU, permutaciones ni selección, y no usan la severidad.
Uso, desde analisis/: python -m unittest preprocesamiento.test_revision_35b
"""
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mutual_info_score

import complementario_cuidados as M
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from eda import variables as V

from . import configuracion as C
from . import entropia as E
from . import fcbf as F
from .test_complementario_cuidados import datos_cuidados, poblacion_cuidados


def bh_a_mano(p):
    """Benjamini-Hochberg escrito de forma independiente."""
    p = np.asarray(p, dtype=float)
    n, orden = len(p), np.argsort(p)
    q, minimo = np.empty(n), 1.0
    for rango in range(n, 0, -1):
        i = orden[rango - 1]
        minimo = min(minimo, p[i] * n / rango)
        q[i] = minimo
    return q


class PruebasShannon(unittest.TestCase):
    def test_valores_conocidos_en_bits(self):
        self.assertAlmostEqual(R.entropia_shannon([0, 1]), 1.0)
        self.assertAlmostEqual(R.entropia_shannon([0, 1, 2, 3]), 2.0)
        self.assertAlmostEqual(R.entropia_shannon([0, 0, 0, 1]), 0.8112781244591328)
        self.assertEqual(R.entropia_shannon([5, 5, 5]), 0.0)

    def test_coincide_con_scipy_en_base_2(self):
        rng = np.random.default_rng(1)
        for k in (2, 3, 7):
            x = rng.integers(0, k, 400)
            self.assertAlmostEqual(R.entropia_shannon(x), stats.entropy(np.bincount(x), base=2), places=12)

    def test_entropia_conjunta(self):
        x, y = np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1])
        self.assertAlmostEqual(R.entropia_conjunta_shannon(x, y), 2.0)
        self.assertAlmostEqual(R.entropia_conjunta_shannon(x, x), 1.0)
        rng = np.random.default_rng(2)
        a, b = rng.integers(0, 4, 300), rng.integers(0, 3, 300)
        tabla = pd.crosstab(a, b).to_numpy().ravel()
        self.assertAlmostEqual(R.entropia_conjunta_shannon(a, b), stats.entropy(tabla, base=2), places=12)

    def test_informacion_mutua(self):
        rng = np.random.default_rng(3)
        a, b = rng.integers(0, 4, 500), rng.integers(0, 3, 500)
        self.assertAlmostEqual(R.informacion_mutua(a, b), mutual_info_score(a, b) / np.log(2), places=12)
        self.assertAlmostEqual(R.informacion_mutua(a, b), R.informacion_mutua(b, a), places=12)
        self.assertAlmostEqual(R.informacion_mutua(a, a), R.entropia_shannon(a), places=12)
        self.assertAlmostEqual(R.informacion_mutua(np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1])), 0.0)

    def test_su_es_la_funcion_congelada_y_la_independiente(self):
        rng = np.random.default_rng(4)
        for k in (2, 5):
            a, b = rng.integers(0, k, 400), rng.integers(0, 3, 400)
            esperado = 2 * R.informacion_mutua(a, b) / (R.entropia_shannon(a) + R.entropia_shannon(b))
            self.assertAlmostEqual(E.su(a, b), esperado, places=12)
            self.assertAlmostEqual(R.symmetrical_uncertainty(a, b), R.su_independiente(a, b), places=10)
        self.assertAlmostEqual(R.symmetrical_uncertainty(a, a), 1.0)
        self.assertAlmostEqual(R.symmetrical_uncertainty(np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1])), 0.0)

    def test_variable_constante(self):
        x, y = np.zeros(20, dtype=int), np.arange(20) % 2
        self.assertEqual(R.symmetrical_uncertainty(x, y), 0.0)
        self.assertEqual(R.su_independiente(x, y), 0.0)
        self.assertEqual(E.prueba_permutacion(y, x, 50, np.random.default_rng(0)), (0.0, 1.0))

    def test_componentes_cierran(self):
        rng = np.random.default_rng(5)
        a, b = rng.integers(0, 4, 300), rng.integers(0, 2, 300)
        c = R.componentes(a, b)
        self.assertAlmostEqual(c['informacion_mutua'], c['h_x'] + c['h_severidad'] - c['h_conjunta'])
        self.assertAlmostEqual(c['su'], 2 * c['informacion_mutua'] / (c['h_x'] + c['h_severidad']))
        self.assertEqual(c['k_categorias'], 4)


class PruebasBenjaminiHochberg(unittest.TestCase):
    def test_ejemplo_a_mano(self):
        np.testing.assert_allclose(E.benjamini_hochberg([0.01, 0.02, 0.03, 0.5]), [0.04, 0.04, 0.04, 0.5])
        np.testing.assert_allclose(E.benjamini_hochberg([0.5, 0.01]), [0.5, 0.02])

    def test_coincide_con_implementacion_independiente(self):
        rng = np.random.default_rng(6)
        for n in (2, 34, 100):
            p = rng.random(n)
            np.testing.assert_allclose(E.benjamini_hochberg(p), bh_a_mano(p))

    def test_familia_de_34_en_el_programa(self):
        rng = np.random.default_rng(7)
        p = rng.random(34) ** 2
        q = dict(zip(range(34), bh_a_mano(p)))
        p_familia = dict(zip(range(34), p))
        self.assertAlmostEqual(R._q_reemplazando(p_familia, 3, p[3]), q[3])


class PruebasPermutaciones(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(8)
        self.y, self.x = rng.integers(0, 2, 300), rng.integers(0, 3, 300)

    def conteo(self, rng, n):
        _, p = E.prueba_permutacion(self.y, self.x, n, rng)
        return R.excedencias([p], n)[0]

    def test_extension_preserva_las_permutaciones(self):
        """Lo que hará 50.000 sobre 10.000: la misma corriente continúa, en lotes de 1.000."""
        a = np.random.default_rng(np.random.SeedSequence(42, spawn_key=(R.ID_REVISION, 0, 1, 3)))
        por_tramos = self.conteo(a, 2000) + self.conteo(a, 3000)
        b = np.random.default_rng(np.random.SeedSequence(42, spawn_key=(R.ID_REVISION, 0, 1, 3)))
        self.assertEqual(por_tramos, self.conteo(b, 5000))

    def test_misma_clave_mismo_resultado_y_clave_propia(self):
        self.assertEqual(E.prueba_permutacion(self.y, self.x, 200, E.generador(R.ID_REVISION, 0, 1, 2)),
                         E.prueba_permutacion(self.y, self.x, 200, E.generador(R.ID_REVISION, 0, 1, 2)))
        self.assertNotEqual(E.generador(R.ID_REVISION, 0, 1, 2).integers(0, 1 << 60), E.generador(0, 0, 1, 2).integers(0, 1 << 60))

    def test_excedencias(self):
        np.testing.assert_array_equal(R.excedencias([1 / 10001, 18 / 10001], 10000), [0, 17])
        with self.assertRaises(RuntimeError):
            R.excedencias([0.123456], 10000)


class PruebasMonteCarlo(unittest.TestCase):
    def test_regla_de_cercania(self):
        np.testing.assert_array_equal(R.es_cercana([0.08, 0.11, 0.05, 0.10], [0.12, 0.2, 0.09, 0.2]), [True, False, False, True])

    def test_recomendacion(self):
        self.assertFalse(R.recomendar([], [])['recomendar_50000'])
        self.assertTrue(R.recomendar(['x'], [])['recomendar_50000'])
        self.assertTrue(R.recomendar([], ['dos corridas no coinciden'])['recomendar_50000'])

    def test_intervalo_contiene_q_y_se_estrecha(self):
        k = np.array([3, 30, 100, 300, 3000, 9000, *([5000] * 28)])
        amplio = R.incertidumbre_mc(k, 10000, np.random.default_rng(1), sorteos=4000)
        estrecho = R.incertidumbre_mc(k * 5, 50000, np.random.default_rng(1), sorteos=4000)
        q = E.benjamini_hochberg((1 + k) / 10001)
        self.assertTrue(((amplio['q_mc_inferior'] <= q + 0.01) & (q - 0.01 <= amplio['q_mc_superior'])).all())
        self.assertTrue(((estrecho['q_mc_superior'] - estrecho['q_mc_inferior']) <= (amplio['q_mc_superior'] - amplio['q_mc_inferior']) + 1e-3).all())

    def test_detecta_una_variable_en_el_umbral(self):
        """p tal que q está muy cerca de 0,10: debe resultar cercana. Uno muy lejano, no."""
        k = np.array([0, 58, *([9000] * 32)])    # q de la segunda ~ 34/2 * 0,0059 = 0,10
        t = R.incertidumbre_mc(k, 10000, np.random.default_rng(2), sorteos=5000)
        cerca = R.es_cercana(t['q_mc_inferior'], t['q_mc_superior'])
        self.assertTrue(cerca[1])
        self.assertFalse(cerca[0])
        self.assertFalse(cerca[5])


class PruebasDireccion(unittest.TestCase):
    def test_clasificar_direccion(self):
        self.assertEqual(R.clasificar_direccion('ordinal', 0.05, 0.2, 0.1, 0.01), 'positiva')
        self.assertEqual(R.clasificar_direccion('ordinal', -0.2, -0.05, -0.1, 0.01), 'negativa')
        self.assertEqual(R.clasificar_direccion('ordinal', 0.05, 0.2, -0.01, 0.5), 'mixta')
        self.assertEqual(R.clasificar_direccion('ordinal', -0.1, 0.1, 0.0, 0.01), 'mixta')
        self.assertEqual(R.clasificar_direccion('ordinal', -0.1, 0.1, 0.0, 0.2), 'poco clara')
        self.assertEqual(R.clasificar_direccion('nominal', np.nan, np.nan, np.nan, 0.01), 'mixta')
        self.assertEqual(R.clasificar_direccion('nominal', np.nan, np.nan, np.nan, 0.3), 'poco clara')

    def test_clasificar_factor(self):
        self.assertEqual(R.clasificar_factor('positiva', 0.05, 0.5), 'Posible factor de riesgo')
        self.assertEqual(R.clasificar_factor('negativa', 0.09, 0.5), 'Posible factor de protección')
        self.assertEqual(R.clasificar_factor('mixta', 0.05, 0.5), 'Asociación sin dirección clara')
        self.assertEqual(R.clasificar_factor('poco clara', 0.05, 0.5), 'Asociación sin dirección clara')
        self.assertEqual(R.clasificar_factor('positiva', 0.2, 0.05), 'Indicio de riesgo (solo orden)')
        self.assertEqual(R.clasificar_factor('negativa', 0.2, 0.05), 'Indicio de protección (solo orden)')
        self.assertEqual(R.clasificar_factor('positiva', 0.2, 0.2), 'Sin respaldo tras la corrección')
        self.assertEqual(R.clasificar_factor('mixta', 0.2, 0.05), 'Sin respaldo tras la corrección')
        self.assertEqual(R.clasificar_factor('positiva', 0.10, 0.5), 'Sin respaldo tras la corrección')

    def test_wilson_newcombe_welch(self):
        li, ls = R.wilson(50, 100)
        self.assertAlmostEqual(li, 0.4038, places=3)
        self.assertAlmostEqual(ls, 0.5962, places=3)
        li, ls = R.newcombe(50, 100, 70, 100)
        self.assertLess(li, 0.2)
        self.assertGreater(ls, 0.2)
        a, b = np.array([1., 2, 3, 4]), np.array([3., 4, 5, 6])
        d, li, ls = R.welch(a, b)
        r = stats.ttest_ind(b, a, equal_var=False).confidence_interval(0.95)
        self.assertAlmostEqual(d, 2.0)
        self.assertAlmostEqual(li, r.low)
        self.assertAlmostEqual(ls, r.high)

    def test_bootstrap_de_rho(self):
        rng = np.random.default_rng(9)
        x = rng.integers(1, 6, 400).astype(float)
        y = x + rng.normal(0, 1.5, 400)
        li, ls = R.ic_rho_bootstrap(x, y, np.random.default_rng(1), 500)
        rho = stats.spearmanr(x, y)[0]
        self.assertLess(li, rho)
        self.assertGreater(ls, rho)
        self.assertGreater(li, 0)

    def test_signo_e_inversion_de_escala(self):
        """El signo se calcula con los valores tal como están: la lectura depende de la orientación."""
        rng = np.random.default_rng(10)
        x = rng.integers(1, 5, 500)
        mrs = np.clip(4 * x + rng.normal(0, 4, 500), 0, 44)
        severo = (mrs >= 16).astype(int)
        fila, cats = R.direccion_variable('evacuacion_intestinal', x, mrs, severo, x, np.random.default_rng(1))
        self.assertEqual(fila['direccion'], 'positiva')
        self.assertIn('MENOS', fila['mayor_valor'])
        self.assertEqual([c['categoria'] for c in cats][0], 'Más de una vez al día')
        self.assertEqual(sum(c['n'] for c in cats), 500)
        self.assertGreater(fila['dif_pct_severas'], 0)
        fila, _ = R.direccion_variable('vasos_agua_dia', 5 - x, mrs, severo, 5 - x, np.random.default_rng(1))
        self.assertEqual(fila['direccion'], 'negativa')

    def test_nominal_sin_signo(self):
        rng = np.random.default_rng(11)
        x = rng.choice(['YO_MAYORIA', 'COMPRO', 'OTRO'], 200)
        mrs = rng.normal(15, 5, 200)
        fila, cats = R.direccion_variable('quien_prepara_comidas', x, mrs, (mrs >= 16).astype(int), E.codificar(x), np.random.default_rng(1))
        self.assertTrue(np.isnan(fila['rho_mrs']))
        self.assertEqual(fila['tipo'], 'nominal')
        self.assertEqual(len(cats), 3)


class PruebasOrientacion(unittest.TestCase):
    """Comprueba la orientación contra el modelo de la encuesta, sin importar Django."""

    @classmethod
    def setUpClass(cls):
        cls.fuente = (V.RAIZ / 'src' / 'apps' / 'encuestas' / 'models.py').read_text(encoding='utf-8')

    def niveles_de(self, clase):
        m = re.search(rf'class {clase}\(models\.\w+\):\n((?:[ \t]*(?:""".*"""|\w+ = .*)\n)+)', self.fuente)
        self.assertIsNotNone(m, clase)
        return {int(a): b for a, b in re.findall(r"= (\d+), '([^']+)'", m.group(1))}

    def test_niveles_iguales_a_los_del_modelo(self):
        for v, e in R.ORIENTACION.items():
            if e.tipo != 'ordinal':
                continue
            modelo = self.niveles_de(e.clase_models)
            for valor, texto in e.niveles.items():
                if valor == 0:      # no aplica o no lo realiza: no es una opción de la encuesta
                    self.assertIn(v, C.CERO_SI_NO, v)
                    continue
                self.assertEqual(modelo[valor], texto, v)

    def test_cada_campo_usa_la_clase_declarada(self):
        for v, e in R.ORIENTACION.items():
            if e.clase_models:
                self.assertRegex(self.fuente, rf'{v} = models\.\w+\(\s*(?:max_length=\d+,\s*)?choices={e.clase_models}\.choices', v)

    def test_evacuacion_es_inversa_a_la_frecuencia(self):
        n = self.niveles_de('FrecuenciaEvacuacionIntestinal')
        self.assertEqual(n[1], 'Más de una vez al día')
        self.assertEqual(n[4], '3 o más días entre evacuaciones')
        self.assertIn('MENOS', R.ORIENTACION['evacuacion_intestinal'].mayor_valor)

    def test_dias_de_ejercicio_empiezan_en_cero_dias(self):
        self.assertEqual(self.niveles_de('DiasEjercicioSemana')[1], '0 días')


class PruebasFlujo(unittest.TestCase):
    """Datos inventados: el escenario y el recorrido reutilizan las funciones congeladas."""

    def setUp(self):
        self.datos = datos_cuidados()
        self.poblacion = poblacion_cuidados(self.datos)
        self.esc = R.construir_escenario(self.datos, self.poblacion)

    def test_exclusiones_y_controles(self):
        variables = self.esc.indice()
        self.assertNotIn('doble_carga', variables)
        self.assertNotIn('prevision', variables)
        self.assertIn(R.SOBRECARGA, variables)
        for v in R.CONTROLES_ANTIGUOS:
            self.assertIn(v, variables)
        self.assertEqual(sorted(variables.values()), list(range(len(variables))))

    def test_rechaza_valores_fuera_de_la_poblacion(self):
        s = np.nan_to_num(self.esc.sobrecarga)
        with self.assertRaises(ValueError):
            R.EscenarioRevision(self.esc.base, s, self.esc.poblacion)

    def test_familia_y_poblaciones(self):
        plan = M.Plan(M.K.Parametros('T', 99, R.ALFA, 'prueba'), M.OBSERVADAS, '')
        ev = M.evaluar(self.esc, plan)
        m = ev.medidas
        self.assertEqual(set(m.q_objetivo), set(self.esc.indice()))
        variables = sorted(m.p_objetivo)
        np.testing.assert_allclose([m.q_objetivo[v] for v in variables], bh_a_mano([m.p_objetivo[v] for v in variables]))
        self.assertEqual(m.n_objetivo['lugar_trabajo_comprensivo'], int(self.datos.mascara.sum()))
        self.assertEqual(m.n_objetivo[R.SOBRECARGA], int(self.poblacion.observada.sum()))
        self.assertEqual(m.n_objetivo['edad'], len(self.datos.tabla))
        self.assertTrue(R.M.iguales(ev, M.evaluar(self.esc, plan)))
        for d in ev.adaptado.values():
            self.assertNotEqual(d['eliminada_por'], R.SOBRECARGA)
        self.assertEqual(C.ALFA_Q_35B, 0.05)

    def test_discretizacion_solo_para_su(self):
        t = self.datos.tabla
        codigos = self.esc.datos()
        self.assertEqual(sorted(set(codigos['edad'])), sorted(set(E.tramos_cerrados_izquierda(t['edad'], C.CORTES_EDAD_35B))))
        self.assertLessEqual(len(set(codigos['imc'])), 6)
        self.assertLessEqual(len(set(codigos['horas_sedentarismo'])), 4)
        self.assertGreater(t['imc'].nunique(), 6)

    def test_constante_en_la_poblacion_laboral(self):
        m = self.esc.mascara_de('lugar_trabajo_comprensivo')
        self.assertEqual(E.su(self.esc.datos()['trabaja_actualmente'][m], self.esc.base.objetivo[m]), 0.0)

    def test_tabla_de_shannon_cierra(self):
        t = R.tabla_shannon(self.esc)
        self.assertEqual(set(t['variable']), set(self.esc.indice()))
        np.testing.assert_allclose(t['informacion_mutua'], t['h_x'] + t['h_severidad'] - t['h_conjunta'])
        self.assertTrue((t['su'].between(0, 1)).all())

    def test_todas_las_parejas(self):
        t = R.tabla_todas_las_parejas(self.esc)
        n = len(self.esc.indice())
        self.assertEqual(len(t), n * (n - 1) // 2)
        par = t[(t['variable_1'] == 'lugar_trabajo_comprensivo') & (t['variable_2'] == R.SOBRECARGA)]
        self.assertEqual(par['n'].iloc[0], int((self.datos.mascara & self.poblacion.observada).sum()))

    def test_comprobar_su_detecta_diferencias(self):
        med = F.Medidas({'a': 0.1234561}, {}, {}, {}, [])
        self.assertEqual(R.comprobar_su(med, {'a': '0.123456'}), [])
        self.assertTrue(R.comprobar_su(med, {'a': '0.123457'}))
        self.assertTrue(R.comprobar_su(med, {'b': '0.1'}))

    def test_comprobar_lista(self):
        self.assertEqual(R.comprobar_lista(R.VARIABLES_34), [])
        self.assertTrue(R.comprobar_lista(R.VARIABLES_34[1:]))
        self.assertTrue(R.comprobar_lista([*R.VARIABLES_34[1:], 'doble_carga']))
        self.assertEqual(len(R.VARIABLES_34), 34)
        self.assertEqual(len(set(R.VARIABLES_34)), 34)

    def test_comprobar_tamanos(self):
        esperado = {'general': len(self.datos.tabla), 'laboral': int(self.datos.mascara.sum()),
                    'cuidadoras_observadas': int(self.poblacion.observada.sum())}
        self.assertEqual(R.comprobar_tamanos(self.esc, esperado), [])
        self.assertTrue(R.comprobar_tamanos(self.esc))

    def test_el_programa_solo_admite_10000(self):
        self.assertEqual(R.N_PERMUTACIONES, 10000)
        self.assertEqual(R.ALFA, 0.10)
        self.assertEqual(R.ID_REVISION, 1103)

    def test_salidas_separadas(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = R.RutasRevision(Path(d) / 'x')
            R.M.validar_separacion(rutas)
            rutas.carpeta.mkdir()
            rutas.informe.write_text('x', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                R.M.validar_separacion(rutas)
        with self.assertRaises(PermissionError):
            R.M.validar_separacion(R.RutasRevision(P.RUTAS_REALES.resultados / 'sub'))


class PruebasFlujoCompleto(unittest.TestCase):
    """Corre el programa completo con datos inventados, en una carpeta temporal."""

    def test_escribe_lo_declarado_y_no_sobrescribe(self):
        datos = datos_cuidados()
        poblacion = poblacion_cuidados(datos)
        adicionales = {v: R.Escala('ordinal', {}, 'prueba') for v in ('senal', 'copia_senal', 'ruido')}
        with mock.patch.dict(R.ORIENTACION, adicionales), tempfile.TemporaryDirectory() as d:
            rutas = R.RutasRevision(Path(d) / 'salida')
            r = R.correr(datos, poblacion, rutas, n_permutaciones=199)
            self.assertEqual({p.name for p in rutas.carpeta.iterdir()}, {p.name for p in rutas.declaradas()})
            variables = set(R.lista_base(datos)) | {R.SOBRECARGA}
            guardada = pd.read_csv(rutas.csv('relevancia_34'), encoding='utf-8-sig')
            self.assertEqual(set(guardada['variable']), variables)
            np.testing.assert_allclose(r['relevancia']['q'], bh_a_mano(r['relevancia']['p']))
            self.assertEqual(set(r['direccion']['variable']), variables)
            texto = rutas.informe.read_text(encoding='utf-8')
            for buscado in ('entropía de Shannon', 'información mutua', 'causal', '## 9. Recomendación técnica'):
                self.assertIn(buscado, texto)
            antes = rutas.informe.read_bytes()
            with self.assertRaises(FileExistsError):
                R.correr(datos, poblacion, rutas, n_permutaciones=199)
            self.assertEqual(rutas.informe.read_bytes(), antes)


class PruebasDatosReales(unittest.TestCase):
    """Solo tamaños y lista: no calcula SU ni usa la severidad."""

    @classmethod
    def setUpClass(cls):
        cls.datos, cls.poblacion, cls.problemas = R.comprobar_datos_reales()
        cls.esc = R.construir_escenario(cls.datos, cls.poblacion)

    def test_sin_problemas(self):
        self.assertEqual(self.problemas, [])

    def test_34_variables_y_poblaciones(self):
        indice = self.esc.indice()
        self.assertEqual(sorted(indice), R.VARIABLES_34)
        poblaciones = [R.poblacion_de(self.esc, v) for v in indice]
        self.assertEqual({p: poblaciones.count(p) for p in set(poblaciones)}, {'general': 31, 'laboral': 2, 'cuidadoras': 1})
        self.assertEqual(int(self.esc.mascara_de('edad').sum()), 529)
        self.assertEqual(int(self.esc.mascara_de('estres_entorno_laboral').sum()), 287)
        self.assertEqual(int(self.esc.mascara_de(R.SOBRECARGA).sum()), 239)
        self.assertEqual(int(self.esc.mascara_de(R.SOBRECARGA, 'estres_entorno_laboral').sum()), 130)

    def test_valores_observados_coinciden_con_los_niveles_declarados(self):
        for v, e in R.ORIENTACION.items():
            if e.tipo not in ('ordinal', 'binaria'):
                continue
            x, m = R.valores_originales(self.datos, self.esc, v)
            self.assertTrue(set(x[m].astype(int)) <= set(e.niveles), v)


if __name__ == '__main__':
    unittest.main()
