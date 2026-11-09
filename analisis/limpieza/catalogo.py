"""
Catálogo de la encuesta usado por la limpieza histórica (Fases 32-34).

Desde la Fase 40B-0 la limpieza NO lee la plataforma. Usa una copia congelada
y versionada de las definiciones (definiciones_fase34.py): campos con sus
códigos y etiquetas, cortes de severidad del MRS, lógica condicional, campos
solo profesionales y comunas. Esa copia se generó desde src/apps/encuestas en
el commit 44bfe0b (mismas versiones vigentes cuando se produjeron las salidas
de la Fase 34) y se comprueba con una huella SHA-256 cada vez que se lee.
Así, cambiar models.py u otro archivo de Django no altera lo que la limpieza
reproduce.

Las funciones *_plataforma leen src/apps/encuestas como antes (models.py con
`ast`, sin importarlo; los otros tres archivos, que son solo diccionarios, con
runpy). Sirven únicamente para auditar o comparar contra la copia congelada;
la limpieza no las llama.
"""
import ast
import copy
import hashlib
import json
import runpy
from pathlib import Path

ENCUESTAS = Path(__file__).resolve().parents[2] / 'src' / 'apps' / 'encuestas'

_CLASES_CHOICES = {'IntegerChoices', 'TextChoices'}


# ---------------------------------------------------------------------------
# Definiciones congeladas (lo que usa la limpieza)
# ---------------------------------------------------------------------------

def _canonico(obj):
    """Forma JSON sin ambigüedad: conserva el orden y los tipos (int/str, tupla/lista, conjunto)."""
    if isinstance(obj, dict):
        return {'dict': [[_canonico(k), _canonico(v)] for k, v in obj.items()]}
    if isinstance(obj, tuple):
        return {'tupla': [_canonico(x) for x in obj]}
    if isinstance(obj, (set, frozenset)):
        elementos = [_canonico(x) for x in obj]
        return {'conjunto': sorted(elementos, key=lambda e: json.dumps(e, ensure_ascii=False, sort_keys=True))}
    if isinstance(obj, list):
        return [_canonico(x) for x in obj]
    if obj is None or isinstance(obj, (bool, int, str)):
        return {type(obj).__name__: obj}
    raise TypeError(f'Tipo no previsto en las definiciones: {type(obj).__name__}')


def huella(campos, severidad, condicionales, secciones, solo_profesional, comunas):
    """SHA-256 del contenido de las seis definiciones (independiente del formato del archivo)."""
    datos = [campos, severidad, condicionales, secciones, set(solo_profesional), comunas]
    texto = json.dumps(_canonico(datos), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def _congeladas():
    from . import definiciones_fase34 as D
    calculada = huella(D.CAMPOS, D.SEVERIDAD_TOTAL, D.PREGUNTAS_CONDICIONALES,
                       D.SECCIONES_CONDICIONALES, D.SOLO_PROFESIONAL, D.COMUNAS_POR_REGION)
    if calculada != D.HUELLA_CONTENIDO:
        raise RuntimeError('definiciones_fase34.py fue modificado: su huella no coincide con la '
                           f'registrada ({calculada} ≠ {D.HUELLA_CONTENIDO}).')
    return D


def leer_modelos():
    """
    Devuelve (campos, severidad_mrs) congelados:
      campos = {campo: {'modelo', 'tipo', 'opciones' ({valor: etiqueta} o None)}}
      severidad_mrs = MRS.SEVERIDAD_TOTAL de la Fase 34
    """
    D = _congeladas()
    return copy.deepcopy(D.CAMPOS), copy.deepcopy(D.SEVERIDAD_TOTAL)


def leer_condicionales():
    D = _congeladas()
    return copy.deepcopy(D.PREGUNTAS_CONDICIONALES), copy.deepcopy(D.SECCIONES_CONDICIONALES)


def leer_solo_profesional():
    return set(_congeladas().SOLO_PROFESIONAL)


def leer_comunas():
    return copy.deepcopy(_congeladas().COMUNAS_POR_REGION)


# ---------------------------------------------------------------------------
# Lectura de la plataforma (solo auditoría y comparación)
# ---------------------------------------------------------------------------

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


def leer_modelos_plataforma(ruta=ENCUESTAS / 'models.py'):
    """Misma salida que leer_modelos(), pero leída de un models.py (por defecto, el de Django)."""
    arbol = ast.parse(Path(ruta).read_text(encoding='utf-8'))
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


def leer_condicionales_plataforma(ruta=ENCUESTAS / 'condicionales.py'):
    mod = runpy.run_path(str(ruta))
    return mod['PREGUNTAS_CONDICIONALES'], mod['SECCIONES_CONDICIONALES']


def leer_solo_profesional_plataforma(ruta=ENCUESTAS / 'campos_por_rol.py'):
    mod = runpy.run_path(str(ruta))
    return {c for lista in mod['SOLO_PROFESIONAL'].values() for c in lista}


def leer_comunas_plataforma(ruta=ENCUESTAS / 'datos_geograficos.py'):
    return runpy.run_path(str(ruta))['COMUNAS_POR_REGION']


def leer_plataforma(directorio=ENCUESTAS):
    """Las seis definiciones leídas de un directorio con los cuatro archivos de la plataforma."""
    d = Path(directorio)
    campos, severidad = leer_modelos_plataforma(d / 'models.py')
    condicionales, secciones = leer_condicionales_plataforma(d / 'condicionales.py')
    return (campos, severidad, condicionales, secciones,
            leer_solo_profesional_plataforma(d / 'campos_por_rol.py'),
            leer_comunas_plataforma(d / 'datos_geograficos.py'))
