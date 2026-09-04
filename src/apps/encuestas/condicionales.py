"""
Reglas de preguntas y secciones condicionales (Sección 5.2 del spec).

El cliente evalúa estas reglas localmente (sin consultar al servidor) para
mostrar u ocultar preguntas mientras se responde offline. Se edita solo este
archivo para ajustar la lógica condicional; el esquema (esquema.py) las expone.
"""

# Preguntas que dependen de otra respuesta DE LA MISMA sección.
# {NombreModelo: {campo_dependiente: {'campo': campo_disparador, 'valor': valor_que_la_muestra}}}
PREGUNTAS_CONDICIONALES = {
    'MRS': {
        'tipo_metodo_anticonceptivo': {'campo': 'usa_metodo_anticonceptivo', 'valor': 'SI'},
        'control_otros_programas_cual': {'campo': 'control_otros_programas', 'valor': 'SI'},
    },
    'TareasCuidado': {
        'mas_de_una_persona_a_cargo': {'campo': 'cuida_otras_personas', 'valor': 'SI'},
    },
    'ActividadFisica': {
        'frecuencia_aerobico': {'campo': 'realiza_aerobico', 'valor': 'SI'},
        'frecuencia_bajo_impacto': {'campo': 'realiza_bajo_impacto', 'valor': 'SI'},
        'frecuencia_fuerza': {'campo': 'realiza_fuerza', 'valor': 'SI'},
    },
    'ConocimientoSistema': {
        'evaluacion_atencion_recibida': {'campo': 'ha_consultado_por_sintomas', 'valor': 'SI'},
        'principales_dificultades': {'campo': 'ha_tenido_dificultades_acceso', 'valor': 'SI'},
        'tipo_informacion_apoyo_deseado': {'campo': 'desea_mas_informacion_apoyo', 'valor': 'SI'},
    },
}

# Secciones completas que dependen de una respuesta de OTRA sección.
# {tipo_seccion: {'seccion': tipo_seccion_origen, 'campo': ..., 'valor': ...}}
SECCIONES_CONDICIONALES = {
    'trabajo': {'seccion': 'identificacion', 'campo': 'trabaja_actualmente', 'valor': True},
}
