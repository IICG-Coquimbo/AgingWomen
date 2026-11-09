"""
Pruebas documentales del cierre: consistencia de las 33 variables, versión revisada de 35A y estructura de los Word.
Solo leen archivos. Uso, desde analisis/: python -m unittest cierre_fases_34_35/scripts/test_documental_cierre.py -v
"""
import json
import re
import unittest
import zipfile
from pathlib import Path

import pandas as pd

ANALISIS = Path(__file__).resolve().parents[2]
CIERRE = ANALISIS / 'cierre_fases_34_35'
INF = CIERRE / 'informes'
S33 = ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables'
RF = ANALISIS / 'random_forest_revision_35b_33_variables' / 'resultados'


def texto_docx(ruta):
    with zipfile.ZipFile(ruta) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'</w:p>', '\n', xml)))


class TreintaYTres(unittest.TestCase):
    def setUp(self):
        self.r = pd.read_csv(S33 / 'permutaciones_50000' / 'relevancia_33.csv', encoding='utf-8-sig')

    def test_misma_lista_en_10000_50000_y_random_forest(self):
        r10 = pd.read_csv(S33 / 'permutaciones_10000' / 'relevancia_33.csv', encoding='utf-8-sig')
        s = pd.read_csv(RF / 'shannon_vs_rf.csv', encoding='utf-8-sig')
        self.assertEqual(set(self.r['variable']), set(r10['variable']))
        self.assertEqual(set(self.r['variable']), set(s['variable']))

    def test_reparto_30_2_1(self):
        self.assertEqual(self.r['poblacion'].value_counts().to_dict(), {'general': 30, 'laboral': 2, 'cuidadoras': 1})
        lab = set(self.r.loc[self.r['poblacion'] == 'laboral', 'variable'])
        self.assertEqual(lab, {'lugar_trabajo_comprensivo', 'estres_entorno_laboral'})
        self.assertEqual(set(self.r.loc[self.r['poblacion'] == 'cuidadoras', 'variable']), {'sobrecarga_fisica_emocional'})

    def test_excluidas_siguen_fuera(self):
        for v in ('usa_medicamentos_diabetes', 'doble_carga', 'prevision', 'etapa_menopausica'):
            self.assertNotIn(v, set(self.r['variable']))


class Revisado35A(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = (ANALISIS / 'informe_preprocesamiento_fase35.md').read_text(encoding='utf-8')
        cls.v = (INF / 'informe_preprocesamiento_fase35_revisado.md').read_text(encoding='utf-8')

    def test_tablas_identicas(self):
        tabla = lambda t: [x for x in t.splitlines() if x.startswith('|')]  # noqa: E731
        self.assertEqual(tabla(self.h), tabla(self.v))

    def test_frase_antigua_solo_en_la_historica(self):
        self.assertIn('22 trabajadoras sin respuesta', self.h)
        self.assertNotIn('22 trabajadoras sin respuesta', self.v)

    def test_poblaciones_y_aclaraciones(self):
        for t in ('309 quedan clasificadas como trabajadoras', '287 con situación laboral respondida o deducida',
                  '22 clasificadas así por imputación', 'no es una respuesta observada', 'no una opinión neutral real',
                  '529 en la capa general y 287 en el módulo laboral'):
            self.assertIn(t, self.v)

    def test_todo_el_texto_historico_se_conserva_salvo_la_frase(self):
        for linea in self.h.splitlines():
            if linea.strip() and '22 trabajadoras sin respuesta' not in linea:
                self.assertIn(linea, self.v)


class Informes(unittest.TestCase):
    def test_cierre_fase35_tiene_titulo_y_12_secciones(self):
        t = texto_docx(INF / 'informe_cierre_fase35.docx')
        self.assertIn('Informe de cierre de la Fase 35 — Preparación analítica, Shannon, FCBF y Random Forest', t)
        for i, s in enumerate(('Resumen ejecutivo', 'Alcance y datos utilizados', 'Fase 35A', 'Fase 35B: Shannon', 'Selección FCBF',
                               'Random Forest complementario', 'Comparación entre Shannon y Random Forest',
                               'Decisiones metodológicas definitivas', 'Limitaciones', 'Verificación de integridad',
                               'Conclusiones', 'Trazabilidad'), 1):
            self.assertIn(f'{i}. {s}', t)

    def test_cierre_fase35_distingue_categorias_y_no_causalidad(self):
        t = texto_docx(INF / 'informe_cierre_fase35.docx')
        for x in ('Resultados históricos verificados', 'Análisis complementarios', 'Decisiones propuestas', 'causal', 'H17'):
            self.assertIn(x, t)

    def test_cierre_fase34_declara_limitaciones_abiertas(self):
        t = texto_docx(INF / 'informe_cierre_fase34_v2.docx')
        for x in ('H11', 'H13', 'H14', 'H17', 'A1', 'sin recalcular', 'versión anterior'):
            self.assertIn(x, t)
        hall = json.loads((CIERRE / 'tablas' / 'tablas_cierre.json').read_text(encoding='utf-8'))['hallazgos']
        self.assertEqual(len(hall), 18)
        for h in hall:
            if h['id'] in ('H14', 'H17', 'A1'):
                self.assertNotIn('Corregido', h['definitivo'])

    def test_protocolo_distingue_y_excluye_gmm(self):
        t = texto_docx(INF / 'protocolo_trabajo_fase36.docx')
        for x in ('Acordado', 'Por definir', '529', '287', '239', '251', 'Davies-Bouldin', 'Calinski-Harabasz', 'GMM'):
            self.assertIn(x, t)

    def test_cifras_rf_del_informe_salen_de_los_resultados(self):
        t = texto_docx(INF / 'informe_cierre_fase35.docx')
        r = pd.read_csv(RF / 'rendimiento_modelos.csv', encoding='utf-8-sig').set_index('modelo')
        for m in ('A', 'B', 'C0', 'C1', 'D0', 'D1'):
            self.assertIn(f'{r.at[m, "roc_auc_evaluacion"]:.3f}'.replace('.', ','), t, m)

    def test_cierres_anteriores_se_conservan(self):
        for n in ('informe_cierre_correccion_fase34.docx', 'nota_metodologica_fase36.docx'):
            self.assertTrue((ANALISIS / 'revision_correctiva_fase34' / 'informe' / n).exists())


if __name__ == '__main__':
    unittest.main()
