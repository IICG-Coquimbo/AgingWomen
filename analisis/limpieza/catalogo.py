"""
Catálogo de la encuesta leído desde el código de la plataforma.

La limpieza no repite a mano los códigos válidos ni la lógica condicional:
los toma de src/apps/encuestas (models.py, condicionales.py, campos_por_rol.py,
datos_geograficos.py). Django no está instalado fuera de Docker, así que
models.py se lee con `ast` (sin importarlo) y los otros tres archivos, que son
solo diccionarios, se ejecutan con runpy.
"""
import ast
import runpy
from pathlib import Path

ENCUESTAS = Path(__file__).resolve().parents[2] / 'src' / 'apps' / 'encuestas'

_CLASES_CHOICES = {'IntegerChoices', 'TextChoices'}


def _nombre_base(nodo):
    return nodo.attr if isinstance(nodo, ast.Attribute) else getattr(nodo, 'id', None)


def _leer_choices(clase):
    """{valor: etiqueta} de una clase IntegerChoices/TextChoices."""
    opciones = {}
    for nodo in clase.body:
        if (isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Tuple)
                and len(nodo.value.elts) == 2):
            valor, etiqueta = (ast.literal_eval(e) for e in nodo.value.elts)
            opciones[valor] = etiqueta
    return opciones


def leer_modelos(ruta=ENCUESTAS / 'models.py'):
    """
    Devuelve (campos, severidad_mrs):
      campos = {campo: {'modelo', 'tipo', 'opciones' ({valor: etiqueta} o None)}}
      severidad_mrs = MRS.SEVERIDAD_TOTAL
    """
    arbol = ast.parse(ruta.read_text(encoding='utf-8'))
    choices = {}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ClassDef) and {_nombre_base(b) for b in nodo.bases} & _CLASES_CHOICES:
            if nodo.name in choices:
                raise ValueError(f'Clase de opciones repetida en models.py: {nodo.name}')
            choices[nodo.name] = _leer_choices(nodo)

    campos, severidad = {}, None
    for modelo in arbol.body:
        if not isinstance(modelo, ast.ClassDef) or {_nombre_base(b) for b in modelo.bases} & _CLASES_CHOICES:
            continue
        for nodo in modelo.body:
            if not isinstance(nodo, ast.Assign) or not isinstance(nodo.targets[0], ast.Name):
                continue
            nombre = nodo.targets[0].id
            if modelo.name == 'MRS' and nombre == 'SEVERIDAD_TOTAL':
                severidad = ast.literal_eval(nodo.value)
            if not (isinstance(nodo.value, ast.Call) and isinstance(nodo.value.func, ast.Attribute)):
                continue
            opciones = None
            for kw in nodo.value.keywords:
                if kw.arg == 'choices':
                    opciones = choices[_nombre_base(kw.value.value)]
            campos[nombre] = {'modelo': modelo.name, 'tipo': nodo.value.func.attr,
                              'opciones': opciones}
    return campos, severidad


def leer_condicionales():
    mod = runpy.run_path(str(ENCUESTAS / 'condicionales.py'))
    return mod['PREGUNTAS_CONDICIONALES'], mod['SECCIONES_CONDICIONALES']


def leer_solo_profesional():
    mod = runpy.run_path(str(ENCUESTAS / 'campos_por_rol.py'))
    return {c for lista in mod['SOLO_PROFESIONAL'].values() for c in lista}


def leer_comunas():
    return runpy.run_path(str(ENCUESTAS / 'datos_geograficos.py'))['COMUNAS_POR_REGION']
