"""
Pruebas del análisis complementario de la Fase 35B. Usan solo datos inventados.
Uso, desde analisis/: python -m unittest preprocesamiento.test_complementario_35b
"""
import contextlib
import io
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import complementario_fase35b as K
import seleccionar_fase35b as P

from . import configuracion as C
from . import entropia as E
from . import fcbf as F
from .test_entropia import datos_inventados, escenario_ficticio, medidas_ficticias

E4 = K.Parametros('E4', 50000, 0.10, 'prueba')
PEQUENOS = (K.Parametros('E1', 99, 0.05, 'prueba'), K.Parametros('E2', 99, 0.10, 'prueba'),
            K.Parametros('E3', 199, 0.05, 'prueba'), K.Parametros('E4', 199, 0.10, 'prueba'))


def escribir_oficial(carpeta, datos, parametros=PEQUENOS[0]):
    """Archivos con el formato de la ejecución oficial, a partir de una evaluación."""
    principal = P.escenario_principal(datos)
    ev = K.evaluar(principal, parametros)
    rutas = K.RutasComplementarias(Path(carpeta))
    Path(carpeta).mkdir(parents=True, exist_ok=True)
    K.tabla_objetivo(principal, ev).to_csv(rutas.csv('su_objetivo'), index=False, encoding='utf-8-sig', float_format=P.FORMATO)
    K.tabla_pares(ev).to_csv(rutas.csv('su_pares'), index=False, encoding='utf-8-sig', float_format=P.FORMATO)
    K.tabla_decisiones(ev).to_csv(rutas.csv('decisiones_fcbf'), index=False, encoding='utf-8-sig', float_format=P.FORMATO)
    return rutas, ev


class PruebasParametros(unittest.TestCase):
    def test_escenarios_fijos(self):
        self.assertEqual([(e.nombre, e.n_permutaciones, e.alfa) for e in K.ESCENARIOS],
                         [('E1', 5000, 0.05), ('E2', 5000, 0.10), ('E3', 50000, 0.05), ('E4', 50000, 0.10)])

    def test_semilla_tolerancia_y_umbral_congelados_no_cambian(self):
        self.assertEqual((C.SEMILLA, C.TOLERANCIA_SU_35B, C.N_PERMUTACIONES_35B, C.ALFA_Q_35B), (42, 1e-12, 5000, 0.05))
        self.assertEqual(P.escenario_principal(datos_inventados()).id_analisis, 0)

    def test_consola_no_admite_otros_parametros(self):
        for extra in ('--semilla=7', '--permutaciones=10', '--alfa=0.5', '--remuestreos=5'):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                K.construir_parser().parse_args(['--ejecutar', extra])

    def test_50000_en_relevancia_y_en_pares(self):
        principal = P.escenario_principal(datos_inventados())
        with mock.patch.object(E, 'prueba_permutacion', return_value=(0.5, 1 / 50001)) as simulada:
            K.evaluar(principal, E4)
        n = len(principal.candidatas)
        self.assertEqual(simulada.call_count, n + n * (n - 1) // 2)         # relevancia y todos los pares
        self.assertEqual({llamada.args[2] for llamada in simulada.call_args_list}, {50000})

    def test_p_real_tiene_denominador_50001(self):
        principal = replace(P.escenario_principal(datos_inventados()), candidatas=['ruido', 'senal'])
        ev = K.evaluar(principal, E4)
        for p in [*ev.medidas.p_objetivo.values(), *ev.medidas.p_par.values()]:
            self.assertAlmostEqual(p * 50001, round(p * 50001), places=6)


class PruebasUmbral(unittest.TestCase):
    def _evaluar_con_q(self, q, alfa=0.10):
        principal = P.escenario_principal(datos_inventados())
        with mock.patch.object(E, 'prueba_permutacion', return_value=(0.5, 0.01)), \
                mock.patch.object(E, 'benjamini_hochberg', side_effect=lambda p: np.full(len(p), q)):
            return K.evaluar(principal, replace(E4, alfa=alfa))

    def test_relevancia_estricta_en_el_umbral(self):
        self.assertEqual(self._evaluar_con_q(0.10).medidas.relevantes, [])
        self.assertEqual(self._evaluar_con_q(0.10 + 1e-13).medidas.relevantes, [])
        self.assertEqual(len(self._evaluar_con_q(0.0999).medidas.relevantes), 7)
        self.assertEqual(self._evaluar_con_q(0.0999, alfa=0.05).medidas.relevantes, [])

    def test_redundancia_estricta_en_el_umbral(self):
        esc = escenario_ficticio(['A', 'B'])
        su = {'A': 0.05, 'B': 0.02}
        with K.umbral(0.10):
            for q, decision in ((0.10, 'seleccionada'), (0.10 - 1e-13, 'redundante'), (0.0999, 'redundante')):
                med = medidas_ficticias(su, {('A', 'B'): 0.03}, {('A', 'B'): q})
                self.assertEqual(F.seleccionar(esc, med, True)['B']['decision'], decision, q)

    def test_la_redundancia_se_reevalua_con_cada_umbral(self):
        esc = escenario_ficticio(['A', 'B'])
        med = medidas_ficticias({'A': 0.05, 'B': 0.02}, {('A', 'B'): 0.03}, {('A', 'B'): 0.07})
        with K.umbral(0.05):
            self.assertEqual(F.seleccionar(esc, med, True)['B']['decision'], 'seleccionada')
        with K.umbral(0.10):
            self.assertEqual(F.seleccionar(esc, med, True)['B']['decision'], 'redundante')

    def test_estandar_no_exige_q_en_el_par(self):
        esc = escenario_ficticio(['A', 'B'])
        med = medidas_ficticias({'A': 0.05, 'B': 0.02}, {('A', 'B'): 0.03}, {('A', 'B'): 0.9})
        with K.umbral(0.10):
            self.assertEqual(F.seleccionar(esc, med, False)['B']['decision'], 'redundante')

    def test_evaluar_distingue_las_dos_variantes(self):
        """Par con q alto: la adaptada conserva ambas variables y la estándar elimina una."""
        principal = replace(P.escenario_principal(datos_inventados()), candidatas=['ruido', 'senal'])
        familias = iter([np.array([0.01, 0.01]), np.array([0.9])])
        with mock.patch.object(E, 'prueba_permutacion', return_value=(0.5, 0.01)), \
                mock.patch.object(E, 'benjamini_hochberg', side_effect=lambda p: next(familias)):
            ev = K.evaluar(principal, E4)
        self.assertEqual(F.seleccionadas(ev.adaptado), ['ruido', 'senal'])
        self.assertEqual(ev.estandar['senal']['decision'], 'redundante')
        self.assertEqual(ev.estandar['senal']['eliminada_por'], 'ruido')

    def test_umbral_se_restaura_incluso_con_error(self):
        with self.assertRaises(ValueError), K.umbral(0.10):
            self.assertEqual(C.ALFA_Q_35B, 0.10)
            raise ValueError
        self.assertEqual(C.ALFA_Q_35B, 0.05)
        K.evaluar(P.escenario_principal(datos_inventados()), PEQUENOS[3])
        self.assertEqual(C.ALFA_Q_35B, 0.05)

    def test_umbral_vigente_en_pares_no_eliminados_y_en_tabla(self):
        principal = P.escenario_principal(datos_inventados())
        ev = K.evaluar(principal, PEQUENOS[3])
        pares = K.tabla_pares(ev)
        self.assertTrue((pares['supera_azar'] == (pares['q'] < 0.10)).all())


class PruebasSeparacion(unittest.TestCase):
    def test_carpeta_real_es_independiente(self):
        self.assertFalse(K.RUTAS_COMPLEMENTARIAS.declaradas() & P.RUTAS_REALES.declaradas())
        self.assertNotIn(P.RUTAS_REALES.resultados, K.CARPETA.parents)

    def test_rechaza_carpetas_originales(self):
        reales = P.RUTAS_REALES
        for carpeta in (reales.resultados, reales.resultados / 'sub', reales.figuras, reales.cache / 'x', reales.dataset.parent):
            with self.assertRaises(PermissionError, msg=carpeta):
                K.validar_separacion(K.RutasComplementarias(carpeta))

    def test_escritor_solo_acepta_rutas_declaradas(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = K.RutasComplementarias(Path(d))
            with self.assertRaises(PermissionError):
                P.Escritor(rutas).texto(Path(d) / 'otro.txt', 'x')
            with self.assertRaises(PermissionError):
                P.Escritor(rutas).texto(P.RUTAS_REALES.log, 'x')

    def test_flujo_escribe_solo_lo_declarado_y_no_sobrescribe(self):
        datos = datos_inventados()
        with tempfile.TemporaryDirectory() as d:
            oficial, _ = escribir_oficial(Path(d) / 'oficial', datos)
            rutas = K.RutasComplementarias(Path(d) / 'nuevo')
            K.correr(datos, rutas, oficial, PEQUENOS)
            self.assertEqual(set((Path(d) / 'nuevo').iterdir()), rutas.declaradas())
            antes = {r: P.sha256(r) for r in rutas.declaradas()}
            with self.assertRaises(FileExistsError):
                K.correr(datos, rutas, oficial, PEQUENOS)
            self.assertEqual(antes, {r: P.sha256(r) for r in rutas.declaradas()})

    def test_un_archivo_existente_detiene_antes_de_calcular(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = K.RutasComplementarias(Path(d))
            rutas.log.write_text('previo', encoding='utf-8')
            with mock.patch.object(K, 'evaluar', side_effect=AssertionError('no debe calcular')), \
                    self.assertRaises(FileExistsError):
                K.correr(datos_inventados(), rutas, rutas, PEQUENOS)
            self.assertEqual(rutas.log.read_text(encoding='utf-8'), 'previo')

    def test_no_existen_remuestreos_ni_cache(self):
        with mock.patch.object(F, 'un_remuestreo', side_effect=AssertionError('bootstrap')), \
                mock.patch.object(P, 'preparar_cache', side_effect=AssertionError('caché')), \
                mock.patch.object(P, 'escenarios_sensibilidad', side_effect=AssertionError('sensibilidad')):
            datos = datos_inventados()
            with tempfile.TemporaryDirectory() as d:
                oficial, _ = escribir_oficial(Path(d) / 'oficial', datos)
                K.correr(datos, K.RutasComplementarias(Path(d) / 'nuevo'), oficial, PEQUENOS)


class PruebasReproducibilidad(unittest.TestCase):
    def test_las_primeras_5000_son_las_de_la_corrida_de_5000(self):
        rng = np.random.default_rng(3)
        x, y = rng.integers(0, 3, 80), rng.integers(0, 2, 80)
        crear = lambda: E.generador(0, 0, F.TIPO_RELEVANCIA, 5)
        continuo = crear()
        _, p1 = E.prueba_permutacion(x, y, 5000, continuo)
        _, p2 = E.prueba_permutacion(x, y, 45000, continuo)
        _, oficial = E.prueba_permutacion(x, y, 5000, crear())
        _, total = E.prueba_permutacion(x, y, 50000, crear())
        self.assertEqual(p1, oficial)
        self.assertEqual(round(p1 * 5001) - 1 + round(p2 * 45001) - 1, round(total * 50001) - 1)

    def test_dos_corridas_coinciden_exactamente(self):
        principal = P.escenario_principal(datos_inventados())
        a, b = K.evaluar(principal, PEQUENOS[3]), K.evaluar(principal, PEQUENOS[3])
        self.assertTrue(K.iguales(a, b))

    def test_iguales_detecta_una_diferencia(self):
        principal = P.escenario_principal(datos_inventados())
        a, b = K.evaluar(principal, PEQUENOS[3]), K.evaluar(principal, PEQUENOS[3])
        v = next(iter(b.medidas.p_objetivo))
        b.medidas.p_objetivo[v] += 1e-15
        self.assertFalse(K.iguales(a, b))

    def test_oficial_acepta_lo_identico_y_rechaza_cambios(self):
        datos = datos_inventados()
        with tempfile.TemporaryDirectory() as d:
            rutas, ev = escribir_oficial(d, datos)
            K.comprobar_oficial(ev, rutas)
            su = pd.read_csv(rutas.csv('su_objetivo'), encoding='utf-8-sig', dtype=str, keep_default_na=False)
            su.loc[0, 'p'] = '0.123456'
            su.to_csv(rutas.csv('su_objetivo'), index=False, encoding='utf-8-sig')
            with self.assertRaisesRegex(RuntimeError, 'no reproduce'):
                K.comprobar_oficial(ev, rutas)

    def test_oficial_rechaza_decision_cambiada(self):
        datos = datos_inventados()
        with tempfile.TemporaryDirectory() as d:
            rutas, ev = escribir_oficial(d, datos)
            t = pd.read_csv(rutas.csv('decisiones_fcbf'), encoding='utf-8-sig', dtype=str, keep_default_na=False)
            t.loc[0, 'decision'] = 'otra'
            t.to_csv(rutas.csv('decisiones_fcbf'), index=False, encoding='utf-8-sig')
            with self.assertRaisesRegex(RuntimeError, 'decisiones'):
                K.comprobar_oficial(ev, rutas)

    def test_si_no_reproduce_lo_oficial_no_escribe_nada(self):
        datos = datos_inventados()
        with tempfile.TemporaryDirectory() as d:
            oficial, _ = escribir_oficial(Path(d) / 'oficial', datos, K.Parametros('E1', 149, 0.05, 'otra corrida'))
            nuevo = Path(d) / 'nuevo'
            with self.assertRaisesRegex(RuntimeError, 'no reproduce'):
                K.correr(datos, K.RutasComplementarias(nuevo), oficial, PEQUENOS)
            self.assertFalse(nuevo.exists())

    def test_si_dos_corridas_difieren_no_escribe_nada(self):
        datos = datos_inventados()
        with tempfile.TemporaryDirectory() as d:
            oficial, _ = escribir_oficial(Path(d) / 'oficial', datos)
            nuevo = Path(d) / 'nuevo'
            with mock.patch.object(K, 'iguales', return_value=False), self.assertRaisesRegex(RuntimeError, 'no coinciden'):
                K.correr(datos, K.RutasComplementarias(nuevo), oficial, PEQUENOS)
            self.assertFalse(nuevo.exists())


class PruebasResultado(unittest.TestCase):
    def setUp(self):
        self.datos = datos_inventados()
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        oficial, _ = escribir_oficial(Path(self.dir.name) / 'oficial', self.datos)
        self.rutas = K.RutasComplementarias(Path(self.dir.name) / 'nuevo')
        self.evaluaciones, _ = K.correr(self.datos, self.rutas, oficial, PEQUENOS)

    def _csv(self, nombre):
        return pd.read_csv(self.rutas.csv(nombre), encoding='utf-8-sig', keep_default_na=False)

    def test_cuatro_escenarios_con_su_redundancia_propia(self):
        resumen = self._csv('resumen_escenarios')
        self.assertEqual(resumen['escenario'].tolist(), ['E1', 'E2', 'E3', 'E4'])
        principal = P.escenario_principal(self.datos)
        for fila, parametros in zip(resumen.itertuples(), PEQUENOS):
            directo = K.evaluar(principal, parametros)
            self.assertEqual(fila.n_relevantes, len(directo.medidas.relevantes))
            self.assertEqual(fila.n_pares, len(directo.medidas.su_par))
            self.assertEqual(fila.seleccionadas_adaptado, ';'.join(F.seleccionadas(directo.adaptado)))
            self.assertEqual(fila.seleccionadas_estandar, ';'.join(F.seleccionadas(directo.estandar)))

    def test_detecta_la_copia_como_redundante(self):
        ultimo = self.evaluaciones[-1]
        self.assertEqual(ultimo.adaptado['senal']['decision'], 'redundante')
        self.assertEqual(ultimo.adaptado['senal']['eliminada_por'], 'copia_senal')

    def test_comparacion_tiene_todas_las_variables_por_escenario(self):
        t = self._csv('comparacion_con_original')
        self.assertEqual(len(t), 4 * len(self.datos.candidatas))
        self.assertEqual(set(t.groupby('escenario').size()), {len(self.datos.candidatas)})

    def test_informe_declara_el_caracter_exploratorio(self):
        texto = self.rutas.informe.read_text(encoding='utf-8')
        for frase in ('exploratorio', 'No sustituye el resultado oficial', 'precisión', 'menos estricta', 'por azar'):
            self.assertIn(frase, texto)
        self.assertNotIn('selección definitiva', texto.lower())


class PruebasEstado(unittest.TestCase):
    def test_estado_detecta_otro_head(self):
        with mock.patch.object(P, '_git', return_value='abc\n'), mock.patch.object(P, 'codigo_sin_congelar', return_value=[]), \
                mock.patch.object(P, 'manifiesto_respaldo', return_value=None):
            problemas = K.estado_inicial()
        self.assertTrue(any('HEAD' in x for x in problemas))
        self.assertTrue(any('respaldo' in x for x in problemas))

    def test_estado_detecta_diferencia_con_respaldo(self):
        def git(*a):
            return K.COMMIT_ORIGINAL if a[0] == 'rev-parse' else ''
        with mock.patch.object(P, '_git', side_effect=git), mock.patch.object(P, 'codigo_sin_congelar', return_value=[]), \
                mock.patch.object(P, 'manifiesto_respaldo', return_value={}), \
                mock.patch.object(P, 'diferencias_con_respaldo', return_value=['archivo.csv']):
            self.assertEqual(K.estado_inicial(), ['Difiere del respaldo: archivo.csv'])

    def test_manifiesto_detecta_un_cambio(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d) / 'a.txt'
            r.write_text('uno', encoding='utf-8')
            antes = P.manifiesto([r])
            r.write_text('dos', encoding='utf-8')
            self.assertEqual(P.comparar_manifiestos(antes, P.manifiesto([r])), [str(r)])

    def test_vigilados_incluye_resultados_codigo_y_word(self):
        vigilados = K.archivos_vigilados() if P.RUTAS_REALES.cache.exists() else []
        if vigilados:
            for r in (*P.RUTAS_REALES.declaradas(), *P.ARCHIVOS_CODIGO, K.INFORME_WORD):
                self.assertIn(r, vigilados)


if __name__ == '__main__':
    unittest.main()
