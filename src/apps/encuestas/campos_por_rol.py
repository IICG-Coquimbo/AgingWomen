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
        # Tamizaje ginecológico y VDRL: datos clínicos que la usuaria común
        # normalmente no maneja; se priorizan cuando responde personal de salud.
        'fecha_ultimo_pap',
        'resultado_pap',
        'fecha_mamografia',
        'resultado_birads',
        'fecha_ecotomografia_mamaria',
        'vdrl_rpr',
        # Talla máxima histórica: exclusiva de personal médico (osteoporosis).
        'talla_maxima_cm',
    ],
}

# Campos que la usuaria común ve pero NO está obligada a responder
# (datos que puede desconocer de memoria al autoaplicarse la encuesta).
OPCIONALES_USUARIA = {
    'SegmentoEMPA': [
        'fecha_ultimo_empa',
        'peso_kg',
        'talla_actual_cm',
        'circunferencia_cintura_cm',
    ],
}

# Campos obligatorios cuando la encuesta la aplica el personal de salud.
# Fase 40B-2 (revisión correctiva): las mediciones del EMPA son
# complementarias y NO obligatorias, tampoco para la profesional. Antes se
# exigían peso_kg, talla_actual_cm, presion_sistolica y presion_diastolica;
# ahora no bloquean el cierre de la ronda. Lo que no se registre queda nulo
# (dato no registrado), sin imputar ceros ni otros valores.
REQUERIDOS_PROFESIONAL = {}
