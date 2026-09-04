"""
Declaración de qué campos ve y debe llenar cada rol (regla 3.1 del spec).

Para mover un campo de categoría se edita SOLO este archivo; los formularios
(`EncuestaModelForm` en forms.py) leen estos diccionarios.

Las claves son el nombre de la clase del modelo (`Model.__name__`).
"""

# Campos que solo puede ver/llenar el personal de salud.
# Para la usuaria común se eliminan del formulario.
SOLO_PROFESIONAL = {
    'SegmentoEMPA': [
        'presion_sistolica',
        'presion_diastolica',
        'glicemia_mg_dl',
        'colesterol_total_mg_dl',
        'colesterol_hdl_mg_dl',
        'trigliceridos_mg_dl',
        'riesgo_cv_atp3',
    ],
}

# Campos que la usuaria común ve pero NO está obligada a responder
# (datos que puede desconocer de memoria al autoaplicarse la encuesta).
OPCIONALES_USUARIA = {
    'SegmentoEMPA': [
        'fecha_ultimo_empa',
        'fecha_ultimo_pap',
        'resultado_pap',
        'fecha_mamografia',
        'resultado_birads',
        'fecha_ecotomografia_mamaria',
        'circunferencia_cintura_cm',
        'talla_actual_cm',
        'vdrl_rpr',
    ],
}

# Campos obligatorios cuando la encuesta la aplica el personal de salud.
REQUERIDOS_PROFESIONAL = {
    'SegmentoEMPA': [
        'peso_kg',
        'talla_actual_cm',
        'presion_sistolica',
        'presion_diastolica',
    ],
}
