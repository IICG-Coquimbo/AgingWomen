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
    HabitosDeVidaForm,
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
    ('habitos_de_vida', 'Hábitos de vida', HabitosDeVidaForm, None),
    ('actividad_fisica', 'Actividad física', ActividadFisicaForm, None),
    ('conocimiento_sistema', 'Conocimiento del sistema de salud', ConocimientoSistemaForm, None),
]

MRS_PREGUNTAS = {f'pregunta_{i}' for i in range(1, 12)}
GRUPO_MRS = 'mrs'

# Edad mínima para responder la encuesta (filtro al inicio — Fase 8).
EDAD_MINIMA = 40

# Definiciones que se muestran antes de empezar la encuesta.
DEFINICIONES = [
    {
        'termino': 'Perimenopausia',
        'texto': (
            'Etapa de transición previa a la menopausia. Las hormonas empiezan a '
            'fluctuar, la menstruación se vuelve irregular y pueden aparecer '
            'síntomas como bochornos o cambios de ánimo. Suele durar varios años.'
        ),
    },
    {
        'termino': 'Menopausia',
        'texto': (
            'Momento en que la menstruación se detiene de forma definitiva. Se '
            'confirma cuando han pasado 12 meses seguidos sin regla.'
        ),
    },
]

# Aviso que se muestra en cada sección: se puede omitir lo que no se sepa.
MENSAJE_OMITIR = (
    'Si no sabes una respuesta, puedes dejarla en blanco y continuar. Tu progreso '
    'se guarda automáticamente en este dispositivo.'
)

# Texto breve que introduce cada sección.
TEXTOS_SECCION = {
    'identificacion': (
        'Primero, algunos datos generales sobre ti. Nos ayudan a analizar los '
        'resultados del estudio.'
    ),
    'trabajo': (
        'Estas preguntas exploran cómo tu trabajo remunerado se relaciona con los '
        'síntomas del climaterio.'
    ),
    'tareas_cuidado': (
        'Aquí preguntamos por las tareas de cuidado no remuneradas (hijos, personas '
        'mayores u otras personas dependientes) y la carga que implican junto con el '
        'trabajo.'
    ),
    'mrs': (
        'La escala MRS mide la intensidad de 11 síntomas frecuentes durante el '
        'climaterio. Responde según cuánto te molesta cada uno actualmente.'
    ),
    'mrs_complementario': (
        'Preguntas complementarias sobre tu ciclo menstrual, métodos anticonceptivos, '
        'tratamientos y antecedentes de salud.'
    ),
    'empa': (
        'Datos del Examen de Medicina Preventiva del Adulto (EMPA). Esta sección puede '
        'quedar incompleta si no manejas esos datos clínicos: la completa '
        'principalmente el personal de salud.'
    ),
    'habitos_de_vida': (
        'Preguntas sobre tu alimentación habitual y el consumo de tabaco, marihuana y '
        'alcohol.'
    ),
    'actividad_fisica': (
        'Estas preguntas describen tu actividad física habitual y el tiempo que pasas '
        'sentada o en reposo.'
    ),
    'conocimiento_sistema': (
        'Por último, queremos saber qué conoces sobre la atención de climaterio y '
        'menopausia en el sistema público de salud y cuál ha sido tu experiencia.'
    ),
}

# Escalas cuyo extremo "alto" es positivo: el gradiente va al revés (rojo abajo,
# verde arriba). El resto usa 'directa' (más alto = más rojo, como el MRS).
ESCALAS_INVERSAS = {
    'lugar_trabajo_comprensivo',
    'evaluacion_atencion_recibida',
    'nivel_informacion_servicios',
    'considera_informacion_suficiente',
    'sintomas_tomados_en_serio',
    'dias_ejercicio_semana',
}

# Nota informativa que acompaña a una pregunta (se muestra bajo el enunciado).
# {NombreModelo: {campo: 'texto de la nota'}}
NOTAS_PREGUNTA = {
    'HabitosDeVida': {
        'tabaco_frecuencia': (
            "El consumo de tabaco influye significativamente en la efectividad y "
            "contraindicaciones de los tratamientos de terapia hormonal."
        ),
    },
}

# Campos de selección múltiple: el modelo los guarda como texto (lista separada
# por comas). El cliente los renderiza como casillas. {NombreModelo: {campo: [opciones]}}
OPCIONES_MULTISELECCION = {
    'TareasCuidado': {
        'a_quien_cuida': [
            'Hijos/as menores de edad',
            'Hijos/as adultos que dependen de usted',
            'Padres o suegros',
            'Abuelos u otros adultos mayores',
            'Cónyuge/pareja con dependencia',
            'Otro familiar o persona dependiente',
            'Otro',
        ],
    },
}


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


VALORES_SI_NO = frozenset({'SI', 'NO'})
VALORES_SI_NO_NOSABE = frozenset({'SI', 'NO', 'NS'})


def _es_escala_ordinal_entera(opciones):
    valores = [o['valor'] for o in opciones]
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in valores):
        return False
    ordenados = sorted(valores)
    return ordenados == list(range(ordenados[0], ordenados[0] + len(ordenados)))


def _es_bloque_si_no(opciones):
    return frozenset(o['valor'] for o in opciones) in (VALORES_SI_NO, VALORES_SI_NO_NOSABE)


def _es_escala_horizontal(tipo_campo, opciones):
    """
    True si la pregunta debe dibujarse horizontal con gradiente de color, como
    el MRS pero sin caritas:
    - escalas ordinales (valores enteros consecutivos: 1-5, 0-4, 1-3…)
    - bloques Sí/No y Sí/No/No sé, incluidos los `BooleanField` (ajustes
      finales adicionales, regla 1: aplica a TODO bloque de ese tipo).
    Las preguntas categóricas (género, método anticonceptivo, quién prepara
    las comidas…) devuelven False.
    """
    if not opciones or len(opciones) < 2:
        return False
    if tipo_campo == 'booleano':
        return True
    if tipo_campo != 'opciones':
        return False
    return _es_bloque_si_no(opciones) or _es_escala_ordinal_entera(opciones)


# Preguntas que son una escala de severidad pero con valores de texto (no
# enteros consecutivos), así que el detector automático no las reconoce:
# se marcan a mano. {NombreModelo: {campo, ...}}
CAMPOS_ESCALA_FORZADA = {
    'MRS': {'tipo_sangrado'},
}

# Preguntas categóricas (selección única) que se muestran horizontales, en
# "chips" cuadrados, SIN gradiente de color: no son una escala ordenada
# (ajustes finales adicionales, regla 4). {NombreModelo: {campo, ...}}
CAMPOS_CHIPS = {
    'HabitosDeVida': {'quien_prepara_comidas'},
}


def construir_esquema(rol):
    secciones = []
    for tipo, titulo, form_cls, parte in ORDEN_SECCIONES:
        form = form_cls(rol=rol)
        modelo = form._meta.model.__name__
        condicionales = PREGUNTAS_CONDICIONALES.get(modelo, {})
        notas = NOTAS_PREGUNTA.get(modelo, {})
        multiseleccion = OPCIONES_MULTISELECCION.get(modelo, {})
        forzadas = CAMPOS_ESCALA_FORZADA.get(modelo, set())
        chips = CAMPOS_CHIPS.get(modelo, set())

        campos = list(form.fields.items())
        if parte == 'likert':
            campos = [(n, c) for n, c in campos if n in MRS_PREGUNTAS]
        elif parte == 'complementario':
            campos = [(n, c) for n, c in campos if n not in MRS_PREGUNTAS]

        preguntas = []
        for nombre, campo in campos:
            if nombre in multiseleccion:
                tc = 'multiseleccion'
                opciones = [{'valor': o, 'texto': o} for o in multiseleccion[nombre]]
            else:
                tc = _tipo_campo(campo)
                if tc == 'opciones':
                    opciones = _opciones(campo)
                elif tc == 'booleano':
                    opciones = [{'valor': True, 'texto': 'Sí'}, {'valor': False, 'texto': 'No'}]
                else:
                    opciones = None

            escala = 'mrs' if (modelo == 'MRS' and nombre in MRS_PREGUNTAS) else None
            es_chip = nombre in chips
            horizontal = escala != 'mrs' and not es_chip and (
                _es_escala_horizontal(tc, opciones) or nombre in forzadas
            )

            preguntas.append({
                'nombre': nombre,
                'texto': str(campo.help_text) or str(campo.label or nombre),
                'etiqueta': str(campo.label or nombre),
                'tipo_campo': tc,
                'obligatoria': bool(campo.required),
                'opciones': opciones,
                'escala': escala,
                'escala_horizontal': horizontal,
                'polaridad': (
                    ('inversa' if nombre in ESCALAS_INVERSAS else 'directa')
                    if horizontal else None
                ),
                'chips': es_chip,
                'mostrar_si': condicionales.get(nombre),
                'depende_de': 'region_residencia' if nombre == 'comuna' else None,
                'nota': notas.get(nombre),
            })

        seccion = {
            'tipo': tipo,
            'titulo': titulo,
            'descripcion': TEXTOS_SECCION.get(tipo),
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
        'edad_minima': EDAD_MINIMA,
        'definiciones': DEFINICIONES,
        'mensaje_omitir': MENSAJE_OMITIR,
    }
