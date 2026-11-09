"""
Fase 40B-1: protección de la reproducibilidad de las Fases 34 a 39 frente a cambios de Django.

Los controles de integridad propios de las Fases 37D, 38 y 39 (integridad_*.py, pruebas_39.py)
exigen HEAD == 745d689 y ningún cambio en src/. Eran fotos del momento de cierre: ya no se
cumplen desde el respaldo 44bfe0b y no se modifican (Fases 34-39 protegidas). Esta prueba
los reemplaza con comprobaciones que no dependen de HEAD ni de src/:

1. Artefactos: cada archivo de los manifiestos finales de las Fases 34 a 39 tiene la huella
   registrada al cerrar la fase. No se leen archivos de la verdad del simulador ni la
   bitácora (solo se comprueba que existan).
2. Entradas que esas fases leen de Django: las clases de opciones de models.py que usa
   revision_35b_reunion_1103.py (y su prueba test_revision_35b.py, que lee el texto con
   expresiones regulares) son idénticas a las del commit 44bfe0b. Si una fase futura
   (por ejemplo, la 40B-2) cambia models.py, esta prueba dice si afecta lo que el análisis lee.
3. La Fase 40B-1 no tocó apps/encuestas/models.py (sus modelos están en apps/rondas).
   Fase 40B-2: este control se acotó. models.py solo puede diferir de 44bfe0b en lo que la
   40B-2 cambia a propósito (nulidad de los 11 ítems MRS y el cálculo del puntaje), y lo que
   el análisis lee de la plataforma debe seguir idéntico a lo congelado en la 40B-0.
   Además, los artefactos que ya no tienen la huella de su manifiesto por cambios anteriores
   a la 40B-2 se exigen con su huella actual exacta (EXCEPCIONES_CONOCIDAS).

Uso, desde la raíz: python -m unittest analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py -v
"""
import ast
import copy
import csv
import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
A = RAIZ / 'analisis'
MODELS = 'src/apps/encuestas/models.py'
COMMIT_REFERENCIA = '44bfe0b6617150d56ac3ddb73b26bdbdacafbb57'
NO_LEER = ('verdad', 'bitacora')

# (nombre, archivo del manifiesto, carpeta base de las rutas)
MANIFIESTOS = [
    ('Fases 34-35 (cierre)', A / 'cierre_fases_34_35/integridad/manifiesto_despues.csv', RAIZ),
    ('Revisión correctiva 34', A / 'revision_correctiva_fase34/manifiestos/manifiesto_correccion_despues.csv', RAIZ),
    ('Fase 36', A / 'fase36/integridad/manifiesto_final_36B.csv', A / 'fase36'),
    ('Fase 37A', A / 'fase37/37A_reduccion/integridad/manifiesto_final_37A.csv', A / 'fase37/37A_reduccion'),
    ('Fase 37B', A / 'fase37/37B_clustering/integridad/manifiesto_final_37B.csv', A / 'fase37/37B_clustering'),
    ('Fase 37C', A / 'fase37/37C_comparacion_seleccion/integridad/manifiesto_final_37C.csv',
     A / 'fase37/37C_comparacion_seleccion'),
    ('Complemento 37C', A / 'fase37/37C_complemento_tres_preguntas/integridad/manifiesto_final.csv',
     A / 'fase37/37C_complemento_tres_preguntas'),
    ('Fase 37D', A / 'fase37/37D_caracterizacion/integridad/manifiesto_final.csv', A / 'fase37/37D_caracterizacion'),
    ('Fase 38', A / 'fase38/38_reglas_asociacion_generales/integridad/manifiesto_final.csv',
     A / 'fase38/38_reglas_asociacion_generales'),
    ('Fase 39', A / 'fase39/39_asociaciones_condicionadas/integridad/manifiesto_final.csv',
     A / 'fase39/39_asociaciones_condicionadas'),
]


# Fase 40B-2: archivos de los manifiestos que ya NO tienen la huella registrada al cerrar su
# fase, por cambios ANTERIORES a la 40B-2 (ninguno se tocó en la 40B-2). No se ocultan: se
# exige su huella ACTUAL exacta, así que cualquier cambio posterior vuelve a fallar.
# Origen verificado en la revisión correctiva 40B-2 (40B-2_revision_correctiva.md, §7): las huellas no se cambiaron.
EXCEPCIONES_CONOCIDAS = {
    'analisis/limpieza/catalogo.py': (
        'c988959005f1c26ae6c55d3bc9d5a98b19f4d7d34d3c00f7b44a6028b766356a',
        'Fase 40B-0 (commit 573d3a3): leer_* lee definiciones_fase34.py congelado. Igual a git 573d3a3; '
        'la 40B-0 verifica que la limpieza reproduce las salidas históricas.'),
    'analisis/eda/univariado.py': (
        '026087e07204e31f924eeb7eded98220526d745489e9ad8ccfb13eaf5f77bce6',
        'Modificado el 2026-11-04 23:43, después del manifiesto de la revisión correctiva 34 (23:11); '
        'contenido incluido en 44bfe0b. Cambio H11 del cierre de las Fases 34-35: su huella actual es la de '
        'cierre_fases_34_35/integridad/manifiesto_despues.csv y es un cambio autorizado (NUEVOS_AUTORIZADOS).'),
    'analisis/eda_usuaria.py': (
        '9c58cc64dfa203ec1bf5cda06832173f5d903ca4d9395aae679e19f34f909492',
        'Modificado el 2026-11-04 23:41, después del manifiesto de la revisión correctiva 34 (23:11); '
        'contenido incluido en 44bfe0b. Cambio H13 del cierre de las Fases 34-35: su huella actual es la de '
        'cierre_fases_34_35/integridad/manifiesto_despues.csv y es un cambio autorizado (NUEVOS_AUTORIZADOS).'),
}


def sha(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def git(*args):
    return subprocess.run(['git', *args], cwd=RAIZ, capture_output=True, check=True).stdout.decode('utf-8')


def bloque_de_clase(texto, clase):
    """Bloque de la clase de opciones (también anidada), con el mismo patrón que test_revision_35b."""
    m = re.search(rf'class {clase}\(models\.\w+\):\n((?:[ \t]*(?:""".*"""|\w+ = .*)\n)+)',
                  texto.replace('\r\n', '\n'))
    return m.group(0) if m else None


def clases_que_lee_el_analisis():
    sys.path.insert(0, str(A))
    import revision_35b_reunion_1103 as R  # noqa: E402  (solo define constantes; no ejecuta análisis)
    return sorted({e.clase_models for e in R.ORIENTACION.values() if e.clase_models})


class ArtefactosHistoricos(unittest.TestCase):
    def test_manifiestos_finales_de_las_fases_34_a_39(self):
        total = omitidos = 0
        excepciones = set()
        for nombre, manifiesto, base in MANIFIESTOS:
            with self.subTest(fase=nombre):
                with open(manifiesto, encoding='utf-8-sig', newline='') as f:
                    filas = list(csv.DictReader(f))
                self.assertTrue(filas)
                distintos = []
                for fila in filas:
                    rel = fila.get('ruta') or fila.get('archivo')
                    ruta = base / rel
                    if any(p in ruta.name.lower() for p in NO_LEER):
                        self.assertTrue(ruta.exists(), rel)
                        omitidos += 1
                        continue
                    if not ruta.exists():
                        distintos.append(rel)
                    elif sha(ruta) != fila['sha256']:
                        clave = ruta.resolve().relative_to(RAIZ).as_posix()
                        if clave in EXCEPCIONES_CONOCIDAS and sha(ruta) == EXCEPCIONES_CONOCIDAS[clave][0]:
                            excepciones.add(clave)
                        else:
                            distintos.append(rel)
                    total += 1
                self.assertEqual(distintos, [], f'{nombre}: archivos cambiados o ausentes')
        print(f'\n  {total} artefactos verificados por huella; {omitidos} de verdad/bitácora solo por existencia; '
              f'{len(excepciones)} excepciones conocidas con su huella actual: {sorted(excepciones)}')


class EntradasDeDjango(unittest.TestCase):
    def test_clases_de_opciones_que_lee_el_analisis(self):
        actual = (RAIZ / MODELS).read_text(encoding='utf-8')
        referencia = git('show', f'{COMMIT_REFERENCIA}:{MODELS}')
        clases = clases_que_lee_el_analisis()
        self.assertGreater(len(clases), 0)
        for clase in clases:
            with self.subTest(clase=clase):
                self.assertIsNotNone(bloque_de_clase(referencia, clase))
                self.assertEqual(bloque_de_clase(actual, clase), bloque_de_clase(referencia, clase))

    def test_models_solo_cambia_lo_previsto_en_la_40b2(self):
        # La 40B-1 no tocó models.py. La 40B-2 sí, a propósito y solo en esto:
        # - los 11 ítems MRS pasan de default=0 a null=True, default=None;
        # - MRS.puntaje_total devuelve None si falta un ítem y se agrega MRS.items_sin_responder.
        # Todo lo demás del archivo (incluidas las clases de opciones) debe ser idéntico a 44bfe0b.
        actual = ast.parse((RAIZ / MODELS).read_text(encoding='utf-8'))
        referencia = ast.parse(git('show', f'{COMMIT_REFERENCIA}:{MODELS}'))
        self.assertEqual(normalizar_40b2(actual), normalizar_40b2(referencia))
        cambios = items_mrs(actual)
        self.assertEqual(set(cambios), {f'pregunta_{i}' for i in range(1, 12)})
        for item, kws in cambios.items():
            self.assertEqual((kws.get('null'), kws.get('default'), 'blank' in kws), (True, None, False), item)

    def test_control_negativo_otro_cambio_en_models_se_detecta(self):
        texto = (RAIZ / MODELS).read_text(encoding='utf-8')
        referencia = normalizar_40b2(ast.parse(git('show', f'{COMMIT_REFERENCIA}:{MODELS}')))
        for viejo, nuevo in (("'Moderada'", "'Moderada (cambiada)'"),          # una etiqueta de opciones
                             ('(15, ', '(14, '),                                # un corte de severidad
                             ('max_length=10,', 'max_length=11,')):             # otro campo cualquiera
            with self.subTest(cambio=viejo):
                self.assertIn(viejo, texto)
                self.assertNotEqual(normalizar_40b2(ast.parse(texto.replace(viejo, nuevo, 1))), referencia)

    def test_el_analisis_lee_lo_mismo_de_la_plataforma(self):
        # Lo que la limpieza congeló en la 40B-0 (campos, opciones y cortes MRS) sigue igual en la
        # plataforma: el cambio de nulidad no es parte de lo que el análisis lee.
        sys.path.insert(0, str(A))
        from limpieza import catalogo  # noqa: E402
        self.assertEqual(catalogo._canonico(list(catalogo.leer_modelos_plataforma())),
                         catalogo._canonico(list(catalogo.leer_modelos())))


def items_mrs(arbol):
    """{pregunta_n: {kw: valor literal}} de los 11 ítems de la clase MRS."""
    mrs = next(n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == 'MRS')
    salida = {}
    for nodo in mrs.body:
        if (isinstance(nodo, ast.Assign) and isinstance(nodo.targets[0], ast.Name)
                and re.fullmatch(r'pregunta_\d+', nodo.targets[0].id)):
            salida[nodo.targets[0].id] = {k.arg: (ast.literal_eval(k.value) if isinstance(k.value, ast.Constant)
                                                  else ast.dump(k.value)) for k in nodo.value.keywords}
    return salida


def normalizar_40b2(arbol):
    """El módulo sin lo que la 40B-2 cambia a propósito (ver test_models_solo_cambia_lo_previsto_en_la_40b2)."""
    arbol = copy.deepcopy(arbol)
    mrs = next(n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == 'MRS')
    cuerpo = []
    for nodo in mrs.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name in ('puntaje_total', 'items_sin_responder'):
            continue
        if (isinstance(nodo, ast.Assign) and isinstance(nodo.targets[0], ast.Name)
                and re.fullmatch(r'pregunta_\d+', nodo.targets[0].id)):
            nodo.value.keywords = [k for k in nodo.value.keywords if k.arg not in ('default', 'null')]
        cuerpo.append(nodo)
    mrs.body = cuerpo
    return ast.dump(arbol)


if __name__ == '__main__':
    unittest.main()
