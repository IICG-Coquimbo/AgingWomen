"""
Reglas de preguntas y secciones condicionales (Sección 5.2 del spec).

El cliente evalúa estas reglas localmente (sin consultar al servidor) para
mostrar u ocultar preguntas mientras se responde offline. Se edita solo este
archivo para ajustar la lógica condicional; el esquema (esquema.py) las expone.
"""

# Preguntas que dependen de otra respuesta DE LA MISMA sección.
# {NombreModelo: {campo_dependiente: {'campo': campo_disparador, 'valor': ..., ['operador': ...]}}}
#
# `operador` (opcional, por defecto 'igual'):
#   - 'igual'            : el campo disparador es exactamente `valor`.
#   - 'meses_desde_lt'   : han pasado MENOS de `valor` meses desde la fecha
#                          escrita en el campo disparador (texto libre).
#   - 'contiene'         : el campo disparador (lista separada por comas) incluye `valor`.
#
# Ocultar en cadena (Fase 26): si el campo disparador es otra pregunta de la
# misma sección y esa pregunta está oculta, la dependiente también se oculta.
# Así basta con condicionar la "pregunta madre" (ej. todo lo que depende de
# ha_consultado_por_sintomas se oculta cuando la previsión no es Fonasa).
# Las respuestas de preguntas ocultas no se envían al servidor.
OPERADORES = ('igual', 'meses_desde_lt', 'contiene')

# Ausencia menstrual: si hace 12 meses o más de la última menstruación
# (menopausia), se ocultan las preguntas que solo aplican con menstruación.
_CON_MENSTRUACION = {
    'campo': 'fecha_ultima_menstruacion', 'operador': 'meses_desde_lt', 'valor': 12,
}
_CON_FONASA = {'campo': 'prevision', 'valor': 'FONASA'}

PREGUNTAS_CONDICIONALES = {
    'MRS': {
        'menstruacion_llega': _CON_MENSTRUACION,
        'tipo_sangrado': _CON_MENSTRUACION,
        'usa_metodo_anticonceptivo': _CON_MENSTRUACION,
        'tipo_metodo_anticonceptivo': {'campo': 'usa_metodo_anticonceptivo', 'valor': 'SI'},
        'tipo_metodo_anticonceptivo_otro': {'campo': 'tipo_metodo_anticonceptivo', 'valor': 'OTRO'},
    },
    'TareasCuidado': {
        # Si no cuida a nadie, la sección termina en la primera pregunta.
        'cantidad_personas_cuida': {'campo': 'cuida_otras_personas', 'valor': 'SI'},
        'a_quien_cuida': {'campo': 'cuida_otras_personas', 'valor': 'SI'},
        # 'contiene': el disparador es una lista separada por comas y contiene `valor`.
        'a_quien_cuida_otro': {'campo': 'a_quien_cuida', 'operador': 'contiene', 'valor': 'Otro'},
        'sobrecarga_fisica_emocional': {'campo': 'cuida_otras_personas', 'valor': 'SI'},
    },
    'HabitosDeVida': {
        'quien_prepara_comidas_otro': {'campo': 'quien_prepara_comidas', 'valor': 'OTRO'},
    },
    'ActividadFisica': {
        'frecuencia_aerobico': {'campo': 'realiza_aerobico', 'valor': 'SI'},
        'frecuencia_bajo_impacto': {'campo': 'realiza_bajo_impacto', 'valor': 'SI'},
        'frecuencia_fuerza': {'campo': 'realiza_fuerza', 'valor': 'SI'},
    },
    'ConocimientoSistema': {
        # Con previsión distinta de Fonasa solo quedan visibles
        # sintomas_tomados_en_serio y desea_mas_informacion_apoyo (+ su detalle).
        'conoce_sistema_publico_climaterio': _CON_FONASA,
        'ha_escuchado_programa_climaterio': _CON_FONASA,
        'sabe_donde_acudir': _CON_FONASA,
        'ha_consultado_por_sintomas': _CON_FONASA,
        'evaluacion_atencion_recibida': {'campo': 'ha_consultado_por_sintomas', 'valor': 'SI'},
        'en_control_programa_consultorio': _CON_FONASA,
        'en_control_programa_cual': {'campo': 'en_control_programa_consultorio', 'valor': 'SI'},
        'considera_informacion_suficiente': _CON_FONASA,
        'nivel_informacion_servicios': _CON_FONASA,
        'conoce_recursos_disponibles': _CON_FONASA,
        'ha_tenido_dificultades_acceso': _CON_FONASA,
        'principales_dificultades': {'campo': 'ha_tenido_dificultades_acceso', 'valor': 'SI'},
        'principales_dificultades_otra': {'campo': 'principales_dificultades',
                                          'operador': 'contiene', 'valor': 'Otra'},
        'tipo_informacion_apoyo_deseado': {'campo': 'desea_mas_informacion_apoyo', 'valor': 'SI'},
        'tipo_informacion_apoyo_otro': {'campo': 'tipo_informacion_apoyo_deseado',
                                        'operador': 'contiene', 'valor': 'Otro'},
    },
}

# Secciones completas que dependen de una respuesta de OTRA sección.
# {tipo_seccion: {'seccion': tipo_seccion_origen, 'campo': ..., 'valor': ...}}
SECCIONES_CONDICIONALES = {
    'trabajo': {'seccion': 'identificacion', 'campo': 'trabaja_actualmente', 'valor': True},
}
