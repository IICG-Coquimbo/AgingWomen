"""
Pruebas de la versión B de la revisión de la Fase 35B (extensión a 50.000 permutaciones).

Usan datos inventados en carpetas temporales, salvo `PruebasDatosReales`, que solo compara hashes y parámetros.
Uso, desde analisis/: python -m unittest preprocesamiento.test_revision_35b_50000
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import complementario_cuidados as M
import revision_35b_50000 as B
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P

from . import entropia as E
from .test_complementario_cuidados import datos_cuidados, poblacion_cuidados

ADICIONALES = {v: R.Escala('ordinal', {}, 'prueba') for v in ('senal', 'copia_senal', 'ruido')}
N_BASE, N_TOTAL = 1000, 3000


class PruebasExtension(unittest.TestCase):
    """Una versión A inventada con 1.000 permutaciones, y su extensión a 3.000."""

    @classmethod
    def setUpClass(cls):
        cls.parche = mock.patch.dict(R.ORIENTACION, ADICIONALES)
        cls.parche.start()
        cls.temporal = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporal.cleanup)
        cls.addClassCleanup(cls.parche.stop)
        cls.datos = datos_cuidados()
        cls.poblacion = poblacion_cuidados(cls.datos)
        cls.anteriores = R.leer_anteriores()
        cls.a = Path(cls.temporal.name) / 'a'
        R.correr(cls.datos, cls.poblacion, R.RutasRevision(cls.a), None, n_permutaciones=N_BASE)
        cls.esc = R.construir_escenario(cls.datos, cls.poblacion)
        cls.ev = M.evaluar(cls.esc, B.plan(N_TOTAL))

    def leer(self, nombre):
        return pd.read_csv(self.a / f'{nombre}.csv', encoding='utf-8-sig', keep_default_na=False)

    def test_la_version_a_se_reproduce_byte_a_byte(self):
        self.assertEqual(B.reproducir_a(self.datos, self.poblacion, self.a, self.anteriores, N_BASE), [])

    def test_detecta_una_tabla_alterada(self):
        ev = M.evaluar(self.esc, B.plan(N_BASE, 'R10'))
        t = B.tablas_version(self.datos, self.poblacion, self.esc, ev, B.monte_carlo_a(N_BASE), self.anteriores)
        self.assertEqual(B.diferencias_tablas(t, self.a), [])
        t['relevancia_34'].loc[0, 'k'] += 1
        self.assertEqual(B.diferencias_tablas(t, self.a), ['relevancia_34'])

    def test_anidamiento(self):
        conteos, errores = B.comprobar_anidamiento(self.esc, self.ev.medidas, self.leer('relevancia_34'), self.leer('pares_relevantes'),
                                                   N_BASE, N_TOTAL)
        self.assertEqual(errores, [])
        self.assertTrue((conteos['k_primeros'] + conteos['k_siguientes'] == conteos['k_total']).all())
        self.assertEqual((conteos['tipo'] == 'variable').sum(), len(self.esc.indice()))
        a = self.leer('relevancia_34').set_index('variable')['k']
        v = conteos[conteos['tipo'] == 'variable'].set_index('nombre')['k_primeros']
        self.assertTrue((a.sort_index() == v.sort_index()).all())

    def test_anidamiento_detecta_k_guardado_distinto(self):
        rel = self.leer('relevancia_34')
        rel.loc[0, 'k'] += 1
        _, errores = B.comprobar_anidamiento(self.esc, self.ev.medidas, rel, self.leer('pares_relevantes'), N_BASE, N_TOTAL)
        self.assertEqual(len(errores), 1)

    def test_anidamiento_detecta_total_distinto(self):
        medidas = M.medir(self.esc, N_TOTAL)
        v = sorted(medidas.p_objetivo)[0]
        medidas.p_objetivo[v] = (R.excedencias([medidas.p_objetivo[v]], N_TOTAL)[0] + 3) / (N_TOTAL + 1)    # dos excedencias de más
        _, errores = B.comprobar_anidamiento(self.esc, medidas, self.leer('relevancia_34'), self.leer('pares_relevantes'), N_BASE, N_TOTAL)
        self.assertTrue(errores)

    def test_su_igual_y_cambio_detectado(self):
        rel = self.leer('relevancia_34')
        self.assertEqual(B.comprobar_su_iguales(self.ev.medidas, rel), [])
        rel.loc[0, 'su'] = 0.5
        self.assertEqual(len(B.comprobar_su_iguales(self.ev.medidas, rel)), 1)

    def test_flujo_completo_y_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = B.RutasB(Path(d) / 'b')
            ev, t, _ = B.correr(self.datos, self.poblacion, rutas, self.a, self.anteriores, N_BASE, N_TOTAL)
            self.assertEqual({p.name for p in rutas.carpeta.iterdir()}, {p.name for p in rutas.declaradas()})
            self.assertEqual(ev.plan.parametros.n_permutaciones, N_TOTAL)
            self.assertEqual(ev.plan.parametros.alfa, R.ALFA)
            texto = rutas.informe.read_text(encoding='utf-8')
            for buscado in ('entropía de Shannon', 'información mutua', 'causal', 'no se reemplaza'):
                self.assertIn(buscado, texto)
            np.testing.assert_allclose(t['relevancia_34']['q'], E.benjamini_hochberg(t['relevancia_34']['p']))
            antes = rutas.informe.read_bytes()
            with self.assertRaises(FileExistsError):
                B.correr(self.datos, self.poblacion, rutas, self.a, self.anteriores, N_BASE, N_TOTAL)
            self.assertEqual(rutas.informe.read_bytes(), antes)

    def test_no_escribe_si_la_version_a_no_se_reproduce(self):
        with tempfile.TemporaryDirectory() as d:
            copia = Path(d) / 'a'
            copia.mkdir()
            for f in self.a.glob('*'):
                copia.joinpath(f.name).write_bytes(f.read_bytes())
            archivo = copia / 'relevancia_34.csv'
            archivo.write_text(archivo.read_text(encoding='utf-8-sig').replace('\n', '\n ', 1), encoding='utf-8-sig')
            rutas = B.RutasB(Path(d) / 'b')
            with self.assertRaises(RuntimeError):
                B.correr(self.datos, self.poblacion, rutas, copia, self.anteriores, N_BASE, N_TOTAL)
            self.assertFalse(rutas.carpeta.exists())


class PruebasCodigoIntacto(unittest.TestCase):
    def test_detecta_cambios(self):
        with tempfile.TemporaryDirectory() as d:
            archivo, log = Path(d) / 'x.py', Path(d) / 'log.txt'
            archivo.write_text('uno', encoding='utf-8')
            log.write_text(f'SHA-256 x.py: {P.sha256(archivo)}\n', encoding='utf-8')
            self.assertEqual(B.codigo_a_intacto(log, [archivo]), [])
            archivo.write_text('dos', encoding='utf-8')
            self.assertEqual(len(B.codigo_a_intacto(log, [archivo])), 1)
            self.assertEqual(len(B.codigo_a_intacto(log, [Path(d) / 'otro.py'])), 1)


class PruebasDatosReales(unittest.TestCase):
    def test_parametros_fijos(self):
        self.assertEqual((B.N_BASE, B.N_TOTAL), (10000, 50000))
        self.assertEqual(B.N_BASE % E.LOTE_PERMUTACIONES, 0)
        self.assertEqual(B.N_TOTAL % E.LOTE_PERMUTACIONES, 0)
        self.assertEqual(R.ALFA, 0.10)
        self.assertEqual(R.ID_REVISION, 1103)

    def test_codigo_de_la_version_a_intacto(self):
        self.assertEqual(B.codigo_a_intacto(R.RUTAS_REVISION.log, [Path(R.__file__).resolve(), R.PROTOCOLO, R.PRUEBAS]), [])

    def test_mismas_34_variables_y_poblaciones(self):
        datos, poblacion, problemas = R.comprobar_datos_reales()
        self.assertEqual(problemas, [])
        esc = R.construir_escenario(datos, poblacion)
        self.assertEqual(sorted(esc.indice()), R.VARIABLES_34)
        self.assertEqual(int(esc.mascara_de('edad').sum()), 529)
        self.assertEqual(int(esc.mascara_de('lugar_trabajo_comprensivo').sum()), 287)
        self.assertEqual(int(esc.mascara_de(R.SOBRECARGA).sum()), 239)
        self.assertTrue(np.isnan(esc.sobrecarga[~esc.poblacion]).all())


if __name__ == '__main__':
    unittest.main()
