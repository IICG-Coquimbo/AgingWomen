"""
Pruebas de la corrección controlada de la Fase 34. No escriben fuera de una carpeta temporal.
Uso, desde la raíz del proyecto: python -m unittest analisis/revision_correctiva_fase34/test_correccion_fase34.py
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

from eda import univariado as U  # noqa: E402

RES = AQUI.parent / 'resultados' / 'usuaria'
RESUMEN = pd.read_csv(RES / 'eda_univariado_resumen.csv', encoding='utf-8-sig')
FRECUENCIAS = pd.read_csv(RES / 'frecuencias_univariado.csv', encoding='utf-8-sig', dtype={'categoria': str}, keep_default_na=False)
FRECUENCIAS['n'] = FRECUENCIAS['n'].astype(int)
FRECUENCIAS['pct'] = FRECUENCIAS['pct'].astype(float)
ORIGEN = pd.read_csv(AQUI / 'tablas' / 'origen_respuestas_34D.csv', encoding='utf-8-sig')


def fila(variable):
    return next(f for f in RESUMEN.itertuples() if f.variable == variable)


class Rotulos(unittest.TestCase):
    def test_sobrecarga_dice_lo_acordado(self):
        self.assertIn('n = 251 cuidadoras: 239 respuestas observadas y 12 imputadas', U.subtitulo(fila('sobrecarga_fisica_emocional')))

    def test_separa_deducidas_faltantes_y_no_aplica(self):
        texto = U.subtitulo(fila('trabaja_actualmente'))
        self.assertIn('506 respuestas observadas, 1 deducida y 22 imputadas', texto)
        lugar = U.subtitulo(fila('lugar_trabajo_comprensivo'), 500)
        self.assertIn('faltantes reales = 22', lugar)
        self.assertIn('no aplica = 220', lugar)

    def test_sin_desglose_no_oculta_imputaciones(self):
        with mock.patch.object(U, 'origen_de', return_value=None):
            self.assertIn('puede incluir imputadas', U.subtitulo(fila('usa_medicamentos_diabetes')))

    def test_desglose_de_otra_limpieza_no_se_usa(self):
        f = fila('usa_medicamentos_diabetes')._replace(n_valido=500)
        self.assertIsNone(U.origen_de(f))

    def test_recuentos_suman_n_valido(self):
        self.assertTrue(((ORIGEN['observadas'] + ORIGEN['deducidas'] + ORIGEN['imputadas'] + ORIGEN['dependen_de_imputada']) == ORIGEN['n_valido']).all())

    def test_los_rotulos_caben_en_la_figura(self):
        cerrar = plt.close
        fuera = []

        def medir(fig=None):
            fig.canvas.draw()
            caja = fig.bbox
            for t in fig.axes[0].texts:
                if t.get_text().startswith('n ') and t.get_window_extent().x1 > caja.x1:
                    fuera.append(t.get_text()[:50])
            if fig.axes[0].title.get_window_extent().y1 > caja.y1:
                fuera.append('título')
            cerrar(fig)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(plt, 'close', medir), mock.patch.object(plt.Figure, 'savefig'):
            for f in RESUMEN.itertuples():
                U.figura(FRECUENCIAS[FRECUENCIAS['variable'] == f.variable], f, Path(tmp) / 'x.png')
        self.assertEqual(fuera, [])


class Revision(unittest.TestCase):
    def test_marcas_y_enlaces_de_los_informes_revisados(self):
        for ruta in (AQUI / 'informes_revisados').glob('*.md'):
            texto = ruta.read_text(encoding='utf-8')
            self.assertIn('Versión revisada del 04-11-2026', texto)
            for enlace in pd.Series(texto.split('](')[1:]).str.split(')').str[0]:
                if enlace.endswith('.png'):
                    self.assertTrue((ruta.parent / enlace).exists(), enlace)

    def test_el_error_de_celdas_no_se_presenta_como_197(self):
        texto = (AQUI / 'informes_revisados' / 'informe_limpieza_usuaria_revisado.md').read_text(encoding='utf-8')
        self.assertIn('Hubo **1 error de limpieza**, no 197', texto)
        self.assertNotIn('la limpieza cambió por error **1**', texto)


if __name__ == '__main__':
    unittest.main()
