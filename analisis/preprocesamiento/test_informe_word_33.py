"""
Compara el Word de 33 variables con los CSV de los que proviene. Desde analisis/, con python-docx instalado:
    python -m unittest preprocesamiento.test_informe_word_33

Se omite si falta python-docx o si el Word aún no existe.
"""
import re
import unittest

try:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    import informe_word_33 as G
except ImportError:
    G = None

import pandas as pd

import revision_33_variables as T

LISTO = G is not None and G.SALIDA.exists()
HISTORICO = T.CARPETA.parent / 'informe_integrado' / 'informe_fase35b_integrado.docx'


@unittest.skipUnless(LISTO, 'Falta python-docx o el Word.')
class InformeWord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = Document(G.SALIDA)
        cls.d = d
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
        cls.a, cls.b, cls.c, _, _, cls.comp, cls.dom = G.cargar()
        cls.nombres = {G.nombre(v): v for v in T.VARIABLES_33}

    def tabla(self, fragmento):
        hallados = [t for k, t in self.tablas.items() if fragmento in k]
        self.assertEqual(len(hallados), 1, fragmento)
        return hallados[0]

    def test_resultados_coinciden_con_csv(self):
        for N, ver in (('10.000', self.a), ('50.000', self.b)):
            t = self.tabla(f'Resultados de las 33 variables con {N}')
            self.assertEqual(len(t), 34)
            r = ver['relevancia_33'].set_index('variable')
            for f in t[1:]:
                v = self.nombres[f[0]]
                esperado = [str(int(r.loc[v, 'n'])), G.p4(r.loc[v, 'su']), f'{int(r.loc[v, "k"]):,}'.replace(',', '.'), G.p5(r.loc[v, 'p']), G.p5(r.loc[v, 'q'])]
                self.assertEqual(f[2:7], esperado, v)
                self.assertEqual(f[9], G.si(r.loc[v, 'q_bajo_0_10']), v)

    def test_comparacion_ejecuciones(self):
        t = self.tabla('Comparación de las 33 variables')
        self.assertEqual(len(t), 34)
        ra, rb = self.a['relevancia_33'].set_index('variable'), self.b['relevancia_33'].set_index('variable')
        for f in t[1:]:
            v = self.nombres[f[0]]
            self.assertEqual(f[1:6], [G.p4(ra.loc[v, 'su']), G.p5(ra.loc[v, 'p']), G.p5(ra.loc[v, 'q']), G.p5(rb.loc[v, 'p']), G.p5(rb.loc[v, 'q'])], v)

    def test_comparacion_34_33(self):
        for n, N in ((10000, '10.000'), (50000, '50.000')):
            t = self.tabla(f'Comparación entre 34 y 33 variables con {N}')
            self.assertEqual(len(t), 35)
            c = self.comp[n].set_index('variable')
            nombres = {**self.nombres, G.nombre(T.EXCLUIDA): T.EXCLUIDA}
            for f in t[1:]:
                v = nombres[f[0]]
                self.assertEqual([f[1], f[3], f[5]], [G.p4(c.loc[v, 'su_34']), G.p5(c.loc[v, 'p_34']), G.p5(c.loc[v, 'q_34'])], v)
                if v == T.EXCLUIDA:
                    self.assertEqual([f[2], f[4], f[6], f[9]], ['—', '—', '—', 'Excluida'])
                else:
                    self.assertEqual([f[2], f[4], f[6]], [G.p4(c.loc[v, 'su_33']), G.p5(c.loc[v, 'p_33']), G.p5(c.loc[v, 'q_33'])], v)
                    self.assertEqual(f[7], f[8], v)
                    self.assertEqual(f[9], 'no', v)
                    self.assertEqual(f[10], f[11], v)

    def test_clases_y_rho(self):
        t = self.tabla('Dirección y clasificación')
        self.assertEqual(len(t), 34)
        d = self.b['direccion_resumen'].set_index('variable')
        for f in t[1:]:
            v = self.nombres[f[0]]
            self.assertEqual(f[-1], d.loc[v, 'clase'], v)
            if pd.notna(d.loc[v, 'rho_mrs']):
                self.assertEqual(f[2], G.r3(d.loc[v, 'rho_mrs']), v)

    def test_catalogo_de_33(self):
        t = self.tabla('Las 33 variables analizadas')
        self.assertEqual(len(t), 34)
        texto = ' '.join(f[2] for f in t)
        for v in T.VARIABLES_33:
            self.assertIn(f'({v})', texto)
        for v in (T.EXCLUIDA, 'doble_carga', 'prevision'):
            self.assertNotIn(f'({v})', texto)

    def test_dominancia(self):
        t = self.tabla('mayor dominancia')
        self.assertEqual(t[1][0], G.nombre(T.EXCLUIDA))
        self.assertEqual(t[1][3], G.p1(self.dom.set_index('variable').loc[T.EXCLUIDA, 'pct_dominante_propia']))

    def test_excluida_fuera_de_tablas_de_resultados(self):
        nombre = G.nombre(T.EXCLUIDA)
        permitidas = ('mayor dominancia', 'Comparación entre 34 y 33', 'Guía de lectura', 'Efectos directos')
        for titulo, t in self.tablas.items():
            if not any(x in titulo for x in permitidas):
                self.assertFalse(any(nombre in c or T.EXCLUIDA in c for f in t for c in f), titulo)

    def test_aclaracion_de_sobrecarga(self):
        for frase in ('239', '251', '12 respuestas imputadas'):
            self.assertIn(frase, self.parrafos)

    def test_terminos_y_marcas(self):
        for marca in ('`', '**', 'None', ' nan'):
            self.assertNotIn(marca, self.todo)
        self.assertIsNone(re.search(r'base de datos', self.todo, re.I))
        for termino in ('entropía de Shannon', 'información mutua', 'Benjamini-Hochberg', 'FCBF', 'q < 0,10', 'sintético', 'causal'):
            self.assertIn(termino, self.todo)

    def test_no_quedan_q_de_la_revision_de_34_en_el_texto(self):
        """Los q de 34 solo pueden aparecer en la comparación y en la tabla de versiones previas."""
        q34 = {G.p3(self.comp[50000].set_index('variable').loc[v, 'q_34']) for v in ('dias_ejercicio_semana', 'imc', 'lugar_trabajo_comprensivo')} - {G.p3(self.comp[50000].set_index('variable').loc[v, 'q_33']) for v in ('dias_ejercicio_semana', 'imc', 'lugar_trabajo_comprensivo')}
        for q in q34:
            self.assertNotRegex(self.parrafos, rf'q\s*=\s*{re.escape(q)}\b')

    def test_historico_de_34_sigue_siendo_otro_archivo(self):
        self.assertTrue(HISTORICO.exists())
        self.assertNotEqual(HISTORICO.resolve(), G.SALIDA.resolve())
        self.assertEqual(G.SALIDA.parent, T.CARPETA / 'informe')


if __name__ == '__main__':
    unittest.main()
