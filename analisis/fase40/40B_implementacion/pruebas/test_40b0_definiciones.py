"""
Pruebas de la Fase 40B-0: la limpieza histórica no depende de src/apps/encuestas.

Ejecutar desde la raíz del repositorio:
    python -m unittest analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py -v

Solo lee los conjuntos SUCIOS y las salidas históricas (sin modificarlas); nunca la
verdad del simulador ni la bitácora del ensuciado. Las copias modificadas de la
plataforma se hacen en directorios temporales.
"""
import ast
import builtins
import hashlib
import io
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / 'analisis'))

import pandas as pd  # noqa: E402

from limpieza import catalogo, definiciones_fase34 as D  # noqa: E402
from limpieza.reglas import limpiar  # noqa: E402

ENCUESTAS = RAIZ / 'src' / 'apps' / 'encuestas'
FUENTES = ['models.py', 'condicionales.py', 'campos_por_rol.py', 'datos_geograficos.py']
# 32b439c: Fase 34B (limpieza del conjunto de la usuaria); 745d689: Fase 35B; 44bfe0b: respaldo.
COMMITS = ['32b439c', '745d689', '44bfe0b']
CASOS = {
    'usuaria': ('datos/sintetico/dataset_usuaria_sucio.csv', 'datos/limpio_usuaria', 'dataset_usuaria_limpio.csv'),
    'profesora': ('datos/dataset_menopausia_sucio.csv', 'datos/limpio', 'dataset_menopausia_limpio.csv'),
}
SALIDAS = ['excluidas.csv', 'diccionario_variables.csv']
SHA_MODELS_ARBOL = 'aeb1fded818b836f111c514417b0c8e4cd3d27e5f608ca4c6334dcd1dd469f78'


def congeladas():
    campos, sev = catalogo.leer_modelos()
    cond, sec = catalogo.leer_condicionales()
    return campos, sev, cond, sec, catalogo.leer_solo_profesional(), catalogo.leer_comunas()


def identicas(a, b):
    """Igualdad que exige el mismo orden de claves y los mismos tipos (int vs str, tupla vs lista)."""
    return catalogo._canonico(list(a)) == catalogo._canonico(list(b))


def leer(ruta):
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def salidas_csv(nombre):
    """Bytes de las tres salidas de limpiar(), escritas igual que limpiar_dataset.py."""
    entrada, _, archivo = CASOS[nombre]
    limpio, excl, dic, _ = limpiar(leer(RAIZ / entrada))
    out = {}
    for nom, df in [(archivo, limpio), ('excluidas.csv', excl), ('diccionario_variables.csv', dic)]:
        b = io.BytesIO()
        df.to_csv(b, index=False, encoding='utf-8-sig')
        out[nom] = b.getvalue()
    return out


def sha(b):
    return hashlib.sha256(b).hexdigest()


def extraer(commit, destino):
    for f in FUENTES:
        contenido = subprocess.run(['git', 'show', f'{commit}:src/apps/encuestas/{f}'], cwd=RAIZ,
                                   check=True, capture_output=True).stdout
        (Path(destino) / f).write_bytes(contenido)


class DefinicionesIdenticas(unittest.TestCase):
    def test_huella_registrada(self):
        self.assertEqual(catalogo.huella(*congeladas()), D.HUELLA_CONTENIDO)

    def test_igual_a_la_plataforma_actual(self):
        self.assertTrue(identicas(congeladas(), catalogo.leer_plataforma(ENCUESTAS)))

    def test_igual_a_los_commits_de_las_fases_34_y_35(self):
        for commit in COMMITS:
            with self.subTest(commit=commit), tempfile.TemporaryDirectory() as tmp:
                extraer(commit, tmp)
                self.assertTrue(identicas(congeladas(), catalogo.leer_plataforma(tmp)))

    def test_huellas_de_origen(self):
        with tempfile.TemporaryDirectory() as tmp:
            extraer(D.COMMIT_ORIGEN, tmp)
            for f in FUENTES:
                self.assertEqual(sha((Path(tmp) / f).read_bytes()), D.SHA256_ORIGEN[f], f)

    def test_generador_reproduce_el_archivo(self):
        r = subprocess.run([sys.executable, 'analisis/fase40/40B_implementacion/scripts/'
                            'congelar_definiciones_fase34.py', '--verificar'], cwd=RAIZ, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class CodigosYCortes(unittest.TestCase):
    def test_cortes_mrs(self):
        _, sev = catalogo.leer_modelos()
        self.assertEqual(sev, ((4, 'Sin síntomas o muy leves'), (8, 'Leve'), (15, 'Moderada'), (44, 'Severa')))

    def test_categoria_historica_sigue_los_cortes(self):
        _, sev = catalogo.leer_modelos()
        df = leer(RAIZ / 'datos/limpio_usuaria/dataset_usuaria_limpio.csv')
        df = df[df['mrs_total'] != '']
        self.assertGreater(len(df), 0)
        for total, cat in zip(df['mrs_total'].astype(float), df['mrs_severidad']):
            self.assertEqual(cat, next(n for m, n in sev if total <= m))

    def test_tamano_del_catalogo(self):
        campos, _ = catalogo.leer_modelos()
        self.assertEqual(len(campos), 130)
        self.assertEqual(len(catalogo.leer_solo_profesional()), 14)
        self.assertEqual(sum(len(v) for v in catalogo.leer_comunas().values()), 346)

    def test_codigos_y_etiquetas_campo_a_campo(self):
        actual, _ = catalogo.leer_modelos_plataforma()
        congelado, _ = catalogo.leer_modelos()
        self.assertEqual(list(actual), list(congelado))
        for campo in actual:
            with self.subTest(campo=campo):
                self.assertEqual(actual[campo], congelado[campo])
                if actual[campo]['opciones']:
                    self.assertEqual([(type(k), k, v) for k, v in actual[campo]['opciones'].items()],
                                     [(type(k), k, v) for k, v in congelado[campo]['opciones'].items()])

    def test_archivo_alterado_se_detecta(self):
        alterado = ((4, 'Sin síntomas o muy leves'), (8, 'Leve'), (14, 'Moderada'), (44, 'Severa'))
        with mock.patch.object(D, 'SEVERIDAD_TOTAL', alterado):
            with self.assertRaises(RuntimeError):
                catalogo.leer_modelos()

    def test_copias_independientes(self):
        campos, _ = catalogo.leer_modelos()
        primero = next(iter(campos))
        campos[primero] = 'alterado'
        self.assertNotEqual(catalogo.leer_modelos()[0][primero], 'alterado')
        self.assertEqual(catalogo.huella(*congeladas()), D.HUELLA_CONTENIDO)


class Independencia(unittest.TestCase):
    def test_copia_modificada_de_la_plataforma_no_cambia_la_limpieza(self):
        historico = {n: (RAIZ / CASOS['usuaria'][1] / n).read_bytes()
                     for n in [CASOS['usuaria'][2], *SALIDAS]}
        with tempfile.TemporaryDirectory() as tmp:
            for f in FUENTES:
                shutil.copy(ENCUESTAS / f, tmp)
            m = Path(tmp) / 'models.py'
            texto = m.read_text(encoding='utf-8')
            nuevo = texto.replace("(15, 'Moderada')", "(12, 'Moderada')").replace("'Leve'", "'Leve (modificada)'")
            self.assertNotEqual(nuevo, texto)
            m.write_text(nuevo, encoding='utf-8')
            c = Path(tmp) / 'campos_por_rol.py'
            c.write_text(c.read_text(encoding='utf-8') + "\nSOLO_PROFESIONAL['extra'] = ['edad']\n",
                         encoding='utf-8')
            # La copia modificada sí cambia lo que se lee de la plataforma...
            self.assertFalse(identicas(congeladas(), catalogo.leer_plataforma(tmp)))
            # ...pero ni el catálogo ni la limpieza la siguen, aunque ENCUESTAS apunte a ella.
            with mock.patch.object(catalogo, 'ENCUESTAS', Path(tmp)):
                self.assertEqual(catalogo.huella(*congeladas()), D.HUELLA_CONTENIDO)
                self.assertEqual(salidas_csv('usuaria'), historico)
        self.assertEqual(sha((ENCUESTAS / 'models.py').read_bytes()), SHA_MODELS_ARBOL)

    def test_limpieza_no_toca_la_plataforma_ni_la_verdad(self):
        abiertos = []
        abrir = builtins.open

        def registrar(ruta, *a, **k):
            abiertos.append(str(ruta))
            return abrir(ruta, *a, **k)

        def prohibido(*a, **k):
            raise AssertionError('la limpieza intentó leer la plataforma')

        crudo = leer(RAIZ / CASOS['usuaria'][0])
        with mock.patch.object(builtins, 'open', registrar), \
                mock.patch.object(io, 'open', registrar), \
                mock.patch.object(runpy, 'run_path', prohibido), \
                mock.patch.object(ast, 'parse', prohibido), \
                mock.patch.object(catalogo, 'ENCUESTAS', Path(tempfile.gettempdir()) / 'no_existe_40b0'):
            limpiar(crudo)
        normal = [a.replace('\\', '/').lower() for a in abiertos]
        self.assertFalse([a for a in normal if 'src/apps' in a or 'verdad' in a or 'bitacora' in a], normal)
        self.assertNotIn('django', sys.modules)


class Reproduccion(unittest.TestCase):
    def test_salidas_identicas_a_las_historicas(self):
        for nombre, (_, carpeta, _) in CASOS.items():
            for archivo, contenido in salidas_csv(nombre).items():
                with self.subTest(caso=nombre, archivo=archivo):
                    self.assertEqual(sha(contenido), sha((RAIZ / carpeta / archivo).read_bytes()))

    def test_plataforma_sin_cambios(self):
        r = subprocess.run(['git', 'status', '--porcelain', '--', 'src'], cwd=RAIZ,
                           capture_output=True, text=True)
        self.assertEqual(r.stdout, '')


if __name__ == '__main__':
    unittest.main()
