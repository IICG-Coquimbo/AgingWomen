"""
Pruebas localizadas de H11 y H13 (cierre de las Fases 34 y 35). Todo ocurre en memoria: no escriben figuras,
tablas ni informes y no llaman al main de eda_univariado.py ni de eda_usuaria.py.
Uso, desde analisis/: python -m unittest cierre_fases_34_35/scripts/test_h11_h13.py -v
"""
import inspect
import sys
import unittest
from pathlib import Path
from unittest import mock

import matplotlib
matplotlib.use('Agg')
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ANALISIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ANALISIS))

import eda_usuaria as EU  # noqa: E402
from eda import estadistica as E, univariado as U, variables as V  # noqa: E402
from limpieza import catalogo  # noqa: E402
from preprocesamiento import configuracion as C  # noqa: E402

RES = ANALISIS / 'resultados' / 'usuaria'
AUDITORIA = ANALISIS / 'revision_correctiva_fase34' / 'tablas' / 'auditoria_figuras_34D.csv'
RELEVANCIA = ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables' / 'permutaciones_50000' / 'relevancia_33.csv'
NUEVE = {'usa_terapia_hormonal': (25, 24), 'tiene_utero': (26, 25), 'tiene_ovario': (23, 22),
         'usa_medicamentos_diabetes': (24, 23), 'distension_abdominal': (18, 17), 'realiza_bajo_impacto': (24, 22),
         'vasos_agua_dia': (25, 24), 'legumbres_semana': (27, 24), 'tabaco_frecuencia': (18, 17)}


def leer(ruta):
    return pd.read_csv(ruta, encoding='utf-8-sig')


class ReglaRecuento(unittest.TestCase):
    """H11 con datos mínimos: cuenta en la población de la figura, no sobre las 546."""

    def setUp(self):
        self.dicc = pd.DataFrame({'tratamiento': ['imputada por moda'], 'faltantes': [25]}, index=['x'])

    def contar(self, tabla, n_valido=529):
        mrs = pd.DataFrame({'x': ['1'] * 3})
        with mock.patch.object(U, '_tabla_origen', return_value=tabla):
            return U.recuento_imputados('x', n_valido, mrs, mrs, self.dicc)

    def test_marca_cuenta_solo_filas_de_la_poblacion(self):
        mrs = pd.DataFrame({'x': list('abcd'), 'x_imputado': ['1', '1', '1', '0']})
        self.assertEqual(U.recuento_imputados('x', 2, mrs.head(2), mrs, self.dicc), 2)

    def test_tabla_de_origen_prevalece_sobre_el_diccionario(self):
        self.assertEqual(self.contar({'x': {'n_valido': 529, 'imputadas': 24}}), 24)

    def test_tabla_de_otra_poblacion_no_se_usa(self):
        self.assertEqual(self.contar({'x': {'n_valido': 546, 'imputadas': 24}}), 25)

    def test_sin_tabla_queda_la_cota_del_diccionario(self):
        self.assertEqual(self.contar({}), 25)

    def test_variable_no_imputada_da_cero(self):
        mrs = pd.DataFrame({'y': ['1']})
        with mock.patch.object(U, '_tabla_origen', return_value={}):
            self.assertEqual(U.recuento_imputados('y', 1, mrs, mrs, self.dicc), 0)


class H11ConDatosReales(unittest.TestCase):
    """Repite describir() en memoria y lo compara con las tablas históricas."""

    @classmethod
    def setUpClass(cls):
        df, dicc = V.cargar(V.LIMPIO_USUARIA, 'dataset_usuaria_limpio.csv')
        campos, _ = catalogo.leer_modelos()
        cls.mrs = U.preparar(df)
        cls.resumen, cls.frec = U.describir(cls.mrs, campos, catalogo.leer_comunas()['04'], dicc)
        cls.hist = leer(RES / 'eda_univariado_resumen.csv').set_index('variable')
        cls.res = cls.resumen.set_index('variable')

    def test_poblacion_529(self):
        self.assertEqual(len(self.mrs), 529)

    def test_recuento_igual_a_la_auditoria_de_529(self):
        aud = leer(AUDITORIA).set_index('variable')['imputadas_exactas_529']
        comunes = aud.index.intersection(self.res.index)
        self.assertEqual(len(comunes), 65)
        pd.testing.assert_series_equal(self.res.loc[comunes, 'imputados_34B'].astype(int),
                                       aud.loc[comunes].astype(int), check_names=False)

    def test_las_nueve_variables_pasan_de_la_cota_al_valor_exacto(self):
        for v, (antes, ahora) in NUEVE.items():
            self.assertEqual(int(self.hist.at[v, 'imputados_34B']), antes, v)
            self.assertEqual(int(self.res.at[v, 'imputados_34B']), ahora, v)

    def test_solo_cambian_esas_nueve_variables(self):
        difieren = self.res.index[self.res['imputados_34B'].astype(int)
                                  != self.hist.loc[self.res.index, 'imputados_34B'].astype(int)]
        self.assertEqual(set(difieren), set(NUEVE))

    def test_estadisticos_iguales_a_los_historicos(self):
        for c in ['n_valido', 'n_faltante', 'porcentaje_faltante', 'n_categorias', 'porcentaje_dominante',
                  'entropia_shannon_bits', 'entropia_normalizada', 'n_aplica', 'n_no_aplica', *U.FORMA]:
            a = pd.to_numeric(self.res[c], errors='coerce').astype(float)
            b = pd.to_numeric(self.hist.loc[self.res.index, c], errors='coerce').astype(float)
            self.assertTrue(np.allclose(a, b, atol=6e-3, equal_nan=True), c)
        self.assertTrue((self.res['categoria_dominante'].astype(str)
                         == self.hist.loc[self.res.index, 'categoria_dominante'].astype(str)).all())

    def test_frecuencias_iguales_a_las_historicas(self):
        h = leer(RES / 'frecuencias_univariado.csv')
        self.assertEqual(len(h), len(self.frec))
        self.assertTrue((h['variable'].values == self.frec['variable'].values).all())
        self.assertTrue((h['categoria'].astype(str).values == self.frec['categoria'].astype(str).values).all())
        self.assertTrue((h['n'].values == self.frec['n'].values).all())
        self.assertTrue(np.allclose(h['pct'], self.frec['pct'], atol=6e-3))

    def test_ningun_comentario_cambia_de_tramo(self):
        for v in self.res.index:
            ojo = 'cambia de tramo' in str(self.res.at[v, 'comentario'])
            self.assertEqual(ojo, 'cambia de tramo' in str(self.hist.at[v, 'comentario']), v)

    def test_tratamiento_igual_al_historico(self):
        falt = leer(RES / 'faltantes_por_variable.csv').set_index('variable')['tratamiento_34B'].fillna('')
        comunes = falt.index.intersection(self.res.index)
        self.assertEqual(len(comunes), len(self.res))
        self.assertTrue((self.res.loc[comunes, 'tratamiento_34B'].fillna('') == falt.loc[comunes]).all())

    def test_describir_no_escribe_ni_borra(self):
        codigo = inspect.getsource(U.describir) + inspect.getsource(U.recuento_imputados)
        for orden in ('unlink', 'to_csv', 'savefig', 'write_text'):
            self.assertNotIn(orden, codigo)


class ReglaRotulo(unittest.TestCase):
    def test_solo_cambia_el_rol_de_la_etapa(self):
        t = pd.DataFrame({'variable': ['etapa_menopausica', 'edad', 'comuna'], 'rol': ['control', 'control', 'otra'],
                          'p': [0.1, 0.2, 0.3]})
        s = EU.rotular_roles(t)
        self.assertEqual(s['rol'].tolist(), ['descriptiva', 'control', 'otra'])
        pd.testing.assert_frame_equal(s.drop(columns='rol'), t.drop(columns='rol'))
        self.assertEqual(t.at[0, 'rol'], 'control')     # no altera la entrada

    def test_titulo_del_informe_y_bloque_de_calculo(self):
        self.assertEqual(EU.BLOQUES['control'][0], 'Variables de control')
        self.assertIn('etapa_menopausica', EU.BLOQUES['control'][1])
        self.assertEqual(EU.TITULOS_INFORME['control'], 'Variables de control y etapa menopáusica (descriptiva)')


class H13ConDatosReales(unittest.TestCase):
    """Rehace en memoria las dos familias FDR como eda_usuaria.py y las compara con el CSV histórico."""

    @classmethod
    def setUpClass(cls):
        df, _ = V.cargar(V.LIMPIO_USUARIA, 'dataset_usuaria_limpio.csv')
        df = df.copy()
        df['severidad'] = E.severidad_codigo(df)
        partes = [E.corregir_fdr(pd.concat([E.cruce_con_mrs(df, list(g), rol, resultado='severidad')
                                            for g, rol in grupos])).assign(familia=familia)
                  for grupos, familia in ((EU.GRUPOS_ASOCIACION, 'principal'), (EU.GRUPOS_SECUNDARIOS, 'secundaria'))]
        cls.sin_rotular = pd.concat(partes, ignore_index=True).sort_values('p_ajustado', ignore_index=True)
        cls.asoc = EU.rotular_roles(cls.sin_rotular)
        cls.hist = leer(RES / 'asociacion_severidad.csv')

    def test_mismas_pruebas(self):
        self.assertEqual(len(self.asoc), len(self.hist))
        self.assertEqual(set(self.asoc['variable']), set(self.hist['variable']))

    def test_rol_igual_al_historico_en_todas_las_filas(self):
        a = self.asoc.set_index('variable')['rol']
        b = self.hist.set_index('variable')['rol']
        pd.testing.assert_series_equal(a.sort_index(), b.sort_index(), check_names=False)
        self.assertEqual(a['etapa_menopausica'], 'descriptiva')
        self.assertEqual(self.sin_rotular.set_index('variable').at['etapa_menopausica', 'rol'], 'control')

    def test_rotular_no_cambia_ningun_valor(self):
        c = [x for x in self.asoc.columns if x != 'rol']
        pd.testing.assert_frame_equal(self.asoc[c], self.sin_rotular[c])

    def test_estadisticos_iguales_a_los_historicos(self):
        a = self.asoc.set_index('variable').sort_index()
        b = self.hist.set_index('variable').sort_index()
        for c in ['n', 'efecto', 'p', 'p_ajustado']:
            self.assertTrue(np.allclose(a[c].astype(float), b[c].astype(float), atol=1e-4, equal_nan=True), c)

    def test_etapa_sigue_fuera_de_las_elegibles(self):
        self.assertIn('etapa_menopausica', C.EXCLUIDAS_MODELADO)
        lista = leer(RELEVANCIA)['variable'].tolist()
        self.assertEqual(len(lista), 33)
        self.assertNotIn('etapa_menopausica', lista)


if __name__ == '__main__':
    unittest.main()
