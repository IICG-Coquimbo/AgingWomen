"""
Esquema de la encuesta como estructura serializable (Fase 7B).

`construir_esquema(rol)` recorre los ModelForm de cada sección (ya filtrados por
rol en la Fase 5B) y produce el JSON que la app cliente usa para renderizar todo
sin tener el modelo delante. Es la fuente única: si cambia una pregunta en
models.py/forms.py, el esquema cambia solo.
"""
from django import forms

from .condicionales import PREGUNTAS_CONDICIONALES, SECCIONES_CONDICIONALES
from .datos_geograficos import COMUNAS_POR_REGION
from .forms import (
    ActividadFisicaForm,
    ConocimientoSistemaForm,
    EvaluacionTrabajoForm,
    HabitosAlimenticiosForm,
    IdentificacionForm,
    MRSForm,
    SegmentoEMPAForm,
    TareasCuidadoForm,
)
from .models import MRS

# Orden en que se presenta la encuesta.
# 4º elemento = "parte": None usa todos los campos del formulario; 'likert' y
# 'complementario' parten el MRS en dos pantallas (mismo modelo, mismo registro:
# ambas llevan grupo 'mrs' y el cliente las sincroniza juntas).
ORDEN_SECCIONES = [
    ('identificacion', 'Identificación', IdentificacionForm, None),
    ('trabajo', 'Trabajo', EvaluacionTrabajoForm, None),
    ('tareas_cuidado', 'Tareas de cuidado', TareasCuidadoForm, None),
    ('mrs', 'Escala de Evaluación de la Menopausia (MRS)', MRSForm, 'likert'),
    ('mrs_complementario', 'Cuestionario complementario', MRSForm, 'complementario'),
    ('empa', 'Examen de Medicina Preventiva del Adulto (EMPA)', SegmentoEMPAForm, None),
    ('actividad_fisica', 'Actividad física', ActividadFisicaForm, None),
    ('habitos_alimenticios', 'Hábitos alimenticios', HabitosAlimenticiosForm, None),
    ('conocimiento_sistema', 'Conocimiento del sistema de salud', ConocimientoSistemaForm, None),
]

MRS_PREGUNTAS = {f'pregunta_{i}' for i in range(1, 12)}
GRUPO_MRS = 'mrs'


def _tipo_campo(campo):
    if isinstance(campo, forms.DateField):
        return 'date'
    if isinstance(campo, (forms.BooleanField, forms.NullBooleanField)):
        return 'booleano'
    if getattr(campo, 'choices', None):
        return 'opciones'
    if isinstance(campo, (forms.IntegerField, forms.DecimalField, forms.FloatField)):
        return 'numero'
    if isinstance(campo.widget, forms.Textarea):
        return 'textarea'
    return 'texto'


def _opciones(campo):
    ops = []
    for valor, texto in getattr(campo, 'choices', []):
        if valor == '' or valor is None:
            continue
        ops.append({'valor': valor, 'texto': str(texto)})
    return ops


def construir_esquema(rol):
    secciones = []
    for tipo, titulo, form_cls, parte in ORDEN_SECCIONES:
        form = form_cls(rol=rol)
        modelo = form._meta.model.__name__
        condicionales = PREGUNTAS_CONDICIONALES.get(modelo, {})

        campos = list(form.fields.items())
        if parte == 'likert':
            campos = [(n, c) for n, c in campos if n in MRS_PREGUNTAS]
        elif parte == 'complementario':
            campos = [(n, c) for n, c in campos if n not in MRS_PREGUNTAS]

        preguntas = []
        for nombre, campo in campos:
            tc = _tipo_campo(campo)
            if tc == 'opciones':
                opciones = _opciones(campo)
            elif tc == 'booleano':
                opciones = [{'valor': True, 'texto': 'Sí'}, {'valor': False, 'texto': 'No'}]
            else:
                opciones = None

            preguntas.append({
                'nombre': nombre,
                'texto': str(campo.help_text) or str(campo.label or nombre),
                'etiqueta': str(campo.label or nombre),
                'tipo_campo': tc,
                'obligatoria': bool(campo.required),
                'opciones': opciones,
                'escala': 'mrs' if (modelo == 'MRS' and nombre in MRS_PREGUNTAS) else None,
                'mostrar_si': condicionales.get(nombre),
                'depende_de': 'region_residencia' if nombre == 'comuna' else None,
            })

        seccion = {
            'tipo': tipo,
            'titulo': titulo,
            'mostrar_si': SECCIONES_CONDICIONALES.get(tipo),
            'preguntas': preguntas,
        }
        if parte in ('likert', 'complementario'):
            # Las dos pantallas del MRS se guardan en un único registro.
            seccion['grupo'] = GRUPO_MRS
        secciones.append(seccion)

    return {
        'secciones': secciones,
        'mrs_niveles': {str(k): v for k, v in MRS.DESCRIPCION_NIVELES.items()},
        'comunas_por_region': COMUNAS_POR_REGION,
    }
