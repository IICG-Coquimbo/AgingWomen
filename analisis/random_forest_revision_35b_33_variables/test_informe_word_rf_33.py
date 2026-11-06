"""
Compara el Word de Random Forest con los CSV de los que proviene. Desde analisis/, con python-docx instalado:
    python -m unittest random_forest_revision_35b_33_variables.test_informe_word_rf_33

Se omite si falta python-docx o si el Word aún no existe.
"""
import re
import unittest

try:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from random_forest_revision_35b_33_variables import informe_word_rf_33 as G
    from random_forest_revision_35b_33_variables import rf_33_variables as RV
except ImportError:
    G = None

LISTO = G is not None and G.SALIDA.exists()


@unittest.skipUnless(LISTO, 'Falta python-docx o el Word.')
class InformeWord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = Document(G.SALIDA)
        cls.tablas, ultimo = {}, None
        for el in d.element.body:
            if el.tag.endswith('}p'):
                tx = Paragraph(el, d).text
                if tx.startswith('Tabla '):
                    ultimo = tx
            elif el.tag.endswith('}tbl') and ultimo:
                cls.tablas[ultimo] = [[c.text for c in f.cells] for f in Table(el, d).rows]
                ultimo = None
        cls.parrafos = '\n'.join(p.text for p in d.paragraphs)
        cls.todo = cls.parrafos + '\n' + '\n'.join(c for t in cls.tablas.values() for f in t for c in f)
        cls.T = G.cargar()
        cls.nombres = {G.nombre(v): v for v in RV.VARIABLES_33}

    def tabla(self, fragmento):
        hallados = [t for k, t in self.tablas.items() if fragmento in k]
        self.assertEqual(len(hallados), 1, fragmento)
        return hallados[0]

    def test_rendimiento_de_los_26_modelos(self):
        t = self.tabla('Rendimiento completo en evaluación')
        self.assertEqual(len(t), 27)
        R = self.T['rendimiento_modelos'].set_index('modelo')
        for f in t[1:]:
            self.assertEqual(f[4], G.p3(R.loc[f[0], 'roc_auc_evaluacion']), f[0])
            self.assertEqual(f[7], G.p3(R.loc[f[0], 'balanced_accuracy_evaluacion']), f[0])

    def test_comparaciones_principales(self):
        t = self.tabla('Comparaciones emparejadas principales')
        C = G.filas_cmp(self.T['comparacion_modelos'])
        self.assertEqual(len(t), 7)
        for f in t[1:]:
            a, b = f[0].split(' − ')
            fila = C.loc[(a, b, 'roc_auc' if f[1] == 'ROC-AUC' else 'balanced_accuracy')]
            self.assertEqual(f[4], G.r3(fila['diferencia']))
            self.assertEqual(f[7], f'{G.r3(fila["ic95_inferior"])} a {G.r3(fila["ic95_superior"])}')
            self.assertEqual(f[8], fila['lectura'])

    def test_azar(self):
        t = self.tabla('Pruebas contra el azar')
        Z = self.T['pruebas_azar']
        self.assertEqual(len(t), 13)
        for f, (_, z) in zip(t[1:], Z.iterrows()):
            self.assertEqual([f[0], f[2], f[6]], [z['modelo'], G.p3(z['observado']), G.p3(z['p'])])

    def test_importancias(self):
        I = self.T['importancia_variables'].set_index(['modelo', 'nombre'])
        for m, n in (('B', 30), ('C1', 31), ('D1', 31), ('A', 3), ('C0', 29), ('D0', 30)):
            t = self.tabla(f'Importancia por permutación en el modelo {m},')
            self.assertEqual(len(t), n + 1)
            for f in t[1:]:
                fila = I.loc[(m, self.nombres[f[1]] if f[1] in self.nombres else None)]
                self.assertEqual([f[2], f[4], f[7]], [G.f4(fila['auc_media']), str(int(fila['auc_positivas'])), fila['aporte']], f[1])

    def test_shannon_33_filas(self):
        t = self.tabla('Comparación de las 33 variables')
        S = self.T['shannon_vs_rf'].set_index('variable')
        self.assertEqual(len(t), 34)
        vistas = set()
        for f in t[1:]:
            v = self.nombres[f[0]]
            vistas.add(v)
            s = S.loc[v]
            self.assertEqual([f[2], f[3], f[4], f[6], f[8], f[10]], [G.p4(s['su']), G.p3(s['q_10000']), G.p3(s['q_50000']), G.f4(s['auc_media']), s['modelo_rf'], s['consistencia']], v)
        self.assertEqual(vistas, set(RV.VARIABLES_33))

    def test_variables_prohibidas_no_estan_en_modelos(self):
        t = self.tabla('Listado exacto de variables')
        for f in t[1:]:
            for v in ('usa_medicamentos_diabetes', 'doble_carga', 'prevision', 'mrs_total', 'severo_mrs', 'imc_fue_imputado'):
                self.assertNotIn(v, f[2], f[0])

    def test_marcas_y_lenguaje(self):
        for marca in ('`', '**', '__', 'None', ' nan', 'False', 'True'):
            self.assertNotIn(marca, self.todo)
        self.assertIsNone(re.search(r'base de datos', self.todo, re.I))
        for termino in ('causalidad', 'sintético', 'sobreajuste', 'Nadeau', 'Random Forest', 'q < 0,10'):
            self.assertIn(termino, self.todo)
        self.assertIsNone(re.search(r'\b(causa|provoca|produce) (la |los )?(severidad|síntomas)', self.todo, re.I))


if __name__ == '__main__':
    unittest.main()
