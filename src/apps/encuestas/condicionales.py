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
# Los operadores distintos de 'igual' se evalúan en el cliente desde la Fase 7;
# hasta entonces la pregunta se muestra igual (no se oculta por error).
OPERADORES = ('igual', 'meses_desde_lt', 'contiene')
PREGUNTAS_CONDICIONALES = {
    'MRS': {
        'tipo_metodo_anticonceptivo': {'campo': 'usa_metodo_anticonceptivo', 'valor': 'SI'},
        'tipo_metodo_anticonceptivo_otro': {'campo': 'tipo_metodo_anticonceptivo', 'valor': 'OTRO'},
        # Ausencia menstrual: si hace 12 meses o más de la última menstruación,
        # se ocultan regularidad y sangrado.
        'menstruacion_llega': {
            'campo': 'fecha_ultima_menstruacion', 'operador': 'meses_desde_lt', 'valor': 12,
        },
        'tipo_sangrado': {
            'campo': 'fecha_ultima_menstruacion', 'operador': 'meses_desde_lt', 'valor': 12,
        },
    },
    'TareasCuidado': {
        'cantidad_personas_cuida': {'campo': 'cuida_otras_personas', 'valor': 'SI'},
        'a_quien_cuida': {'campo': 'cuida_otras_personas', 'valor': 'SI'},
        # 'contiene': el disparador es una lista separada por comas y contiene `valor`.
        # El motor lo evalúa en la Fase 7 (hasta entonces la pregunta se muestra).
        'a_quien_cuida_otro': {'campo': 'a_quien_cuida', 'operador': 'contiene', 'valor': 'Otro'},
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
        'evaluacion_atencion_recibida': {'campo': 'ha_consultado_por_sintomas', 'valor': 'SI'},
        'en_control_programa_cual': {'campo': 'en_control_programa_consultorio', 'valor': 'SI'},
        'principales_dificultades': {'campo': 'ha_tenido_dificultades_acceso', 'valor': 'SI'},
        'tipo_informacion_apoyo_deseado': {'campo': 'desea_mas_informacion_apoyo', 'valor': 'SI'},
    },
}

# Secciones completas que dependen de una respuesta de OTRA sección.
# {tipo_seccion: {'seccion': tipo_seccion_origen, 'campo': ..., 'valor': ...}}
SECCIONES_CONDICIONALES = {
    'trabajo': {'seccion': 'identificacion', 'campo': 'trabaja_actualmente', 'valor': True},
}
