"""
Configuración ÚNICA del preprocesamiento de la Fase 35A (y de la selección de la 35B).

Todo lo que puede cambiar después de consultar a la profesora está aquí:
umbrales, variables candidatas, excepciones y decisiones. Para regenerar
todo con otra configuración basta editar este archivo y correr:

    python analisis/preprocesar_fase35.py

Origen de cada decisión:
  - reunión con la profesora del 27-10-2026 (MRS binario, filtros de
    redundancia y de dominancia, IMC imputado por la media, módulo de cuidado);
  - decisiones de la usuaria del 28-10-2026 (umbral de dominancia > 85 %,
    excepciones de diabetes y previsión, "no aplica" en trabajo);
  - decisión de la usuaria del 01-11-2026 (etapa menopáusica solo descriptiva,
    preguntas menstruales fuera del modelado, edad se evalúa en la Fase 37).
"""
SEMILLA = 42                      # para cualquier proceso aleatorio desde la Fase 35 en adelante

# --- Variable objetivo -----------------------------------------------------------
CORTE_SEVERO = 16                 # severo_mrs = 1 si mrs_total >= 16 (corte "severa" de Heinemann 2004)

# --- Filtro por baja variabilidad -----------------------------------------------
UMBRAL_ELIMINAR_DOMINANCIA = 85   # % de la categoría dominante: ESTRICTAMENTE mayor → se elimina
UMBRAL_REVISAR_DOMINANCIA = 80    # entre 80 y 85 % → se revisa y se conserva (decisión de la usuaria)

# Se conservan aunque superen el 85 %, con su justificación.
CONSERVAR_PESE_A_DOMINANCIA = {
    'usa_medicamentos_diabetes': 'Factor validado por la profesora (20-10) y variable de control; la '
                                 'diabetes es un modificador clínico conocido de los síntomas.',
    'prevision': 'Variable de control (acceso a salud); no supera el 85 % pero se deja explícita para que la '
                 'excepción no dependa de pequeñas variaciones.',
}

# --- Filtro por redundancia -----------------------------------------------------
UMBRAL_REDUNDANCIA = 0.80         # |rho| de Spearman (numéricas/ordinales) o V de Cramér (nominales), estricto

# Eliminadas por decisión de la profesora (27-10), aunque igual se informa la asociación medida.
ELIMINAR_POR_DECISION = {
    'peso_kg': ('imc', 'Redundante con el IMC (el IMC se calcula con peso y talla).'),
    'talla_actual_cm': ('imc', 'El IMC ya incorpora la talla en su cálculo. Ojo: medida sola, la talla casi no '
                               'se asocia con el IMC (ver valor), así que sale por decisión y no por redundancia '
                               'estadística.'),
    'cuida_otras_personas': ('cantidad_personas_cuida',
                             'El módulo de cuidado queda representado por la cantidad de personas que cuida '
                             '(0 = no cuida).'),
    'sobrecarga_fisica_emocional': ('cantidad_personas_cuida',
                                    'El módulo de cuidado queda representado por la cantidad de personas que '
                                    'cuida. Ojo: la cantidad mide intensidad de cuidado, no sobrecarga percibida.'),
    'a_quien_cuida': ('cantidad_personas_cuida',
                      'Selección múltiple del mismo módulo de cuidado; queda representado por la cantidad.'),
}

# Ante un par redundante se conserva la primera de esta lista que aparezca; si
# ninguna está, se usa el orden: control > menor % de faltantes > más categorías.
# Las frecuencias de ejercicio contienen a "realiza" (0 = no lo realiza) y
# agregan cuánto: por eso se prefieren.
PREFERENCIA = ['imc', 'cantidad_personas_cuida', 'dias_ejercicio_semana',
               'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza']

# --- Variables solo descriptivas (decisión de la usuaria 2026-11-01) ---------------
# Siguen en el conjunto limpio y en el EDA, pero no son candidatas: no entran a
# dataset_fase35.csv ni a ninguna fase de modelado (35B, 36, 37, 38, 39, 40).
# La etapa puede usarse para describir los clústeres DESPUÉS de formarlos.
# (variable: tipo, motivo)
EXCLUIDAS_MODELADO = {
    'etapa_menopausica': ('nominal', 'Clasificación derivada con una regla propia, basada en parte en STRAW+10 y sin '
                                     'validar por la profesora. No es una respuesta de la encuesta. Se usa solo para '
                                     'describir la muestra y caracterizar los clústeres ya formados.'),
    'menstruacion_llega': ('nominal', 'Cumple los criterios originales de selección, pero se excluye por una razón '
                                      'metodológica adicional: con su "no aplica" permite reconstruir indirectamente '
                                      'la etapa menopáusica, que se decidió mantener solo como descriptiva.'),
    'tipo_sangrado': ('ordinal', 'Comparte con la clasificación menopáusica las respuestas "no aplica": transmitiría '
                                 'indirectamente la etapa reproductiva y podría condicionar la segmentación.'),
    'usa_metodo_anticonceptivo': ('nominal', 'Comparte con la clasificación menopáusica las respuestas "no aplica": '
                                             'transmitiría indirectamente la etapa reproductiva y podría condicionar '
                                             'la segmentación.'),
}
N_PREDICTORAS_ESPERADAS = 35      # se verifica al correr: si cambia, revisar antes de usar el conjunto

# La edad sigue como candidata: es demográfica y no equivale a la etapa, aunque
# aporta información indirecta sobre ella. La Fase 37 debe comparar la
# segmentación con y sin edad (métricas, tamaño de grupos e interpretabilidad).
NOTA_EDAD = ('Se mantiene como candidata: es una característica demográfica y no equivale a la etapa menopáusica, '
             'aunque aporta información indirecta sobre la etapa reproductiva. No se usa la clasificación derivada. La '
             'Fase 37 comparará la segmentación con y sin edad (métricas de calidad, tamaño de los grupos e '
             'interpretabilidad), priorizando los patrones de hábitos, estilos de vida y contexto laboral.')

# --- Variables candidatas (tipo, bloque) ------------------------------------------
# Tipos: continua, ordinal, binaria, nominal. Las de "control" tienen prioridad
# ante la redundancia.
CONTROL = ['edad', 'imc', 'usa_terapia_hormonal', 'prevision',
           'usa_medicamentos_diabetes', 'trabaja_actualmente']

CANDIDATAS = {
    # Control
    'edad': ('continua', 'Control'),
    'imc': ('continua', 'Control'), 'usa_terapia_hormonal': ('binaria', 'Control'),
    'prevision': ('nominal', 'Control'), 'usa_medicamentos_diabetes': ('binaria', 'Control'),
    'trabaja_actualmente': ('binaria', 'Control'),
    # Identificación y vida en pareja
    'origen_procedencia': ('nominal', 'Identificación'), 'pueblo_originario_afro': ('nominal', 'Identificación'),
    'genero': ('nominal', 'Identificación'), 'tiene_pareja': ('binaria', 'Identificación'),
    'tiene_actividad_sexual': ('binaria', 'Identificación'),
    # Ginecológicas (las preguntas menstruales están en EXCLUIDAS_MODELADO)
    'tipo_metodo_anticonceptivo': ('nominal', 'Ginecológica'),
    'operada_no_mas_hijos': ('binaria', 'Ginecológica'), 'tiene_utero': ('binaria', 'Ginecológica'),
    'tiene_ovario': ('binaria', 'Ginecológica'),
    # Salud general
    'usa_medicamentos_presion': ('binaria', 'Salud'), 'evacuacion_intestinal': ('ordinal', 'Salud'),
    'distension_abdominal': ('ordinal', 'Salud'),
    # Medidas autodeclaradas
    'peso_kg': ('continua', 'Medidas'), 'talla_actual_cm': ('continua', 'Medidas'),
    # Trabajo (solo quienes trabajan)
    'lugar_trabajo_comprensivo': ('ordinal', 'Trabajo'), 'estres_entorno_laboral': ('ordinal', 'Trabajo'),
    # Cuidado
    'cuida_otras_personas': ('binaria', 'Cuidado'), 'cantidad_personas_cuida': ('ordinal', 'Cuidado'),
    'sobrecarga_fisica_emocional': ('ordinal', 'Cuidado'), 'a_quien_cuida': ('nominal', 'Cuidado'),
    'doble_carga': ('binaria', 'Cuidado'),
    # Actividad física
    'dias_ejercicio_semana': ('ordinal', 'Actividad física'),
    'realiza_aerobico': ('binaria', 'Actividad física'), 'frecuencia_aerobico': ('ordinal', 'Actividad física'),
    'realiza_bajo_impacto': ('binaria', 'Actividad física'),
    'frecuencia_bajo_impacto': ('ordinal', 'Actividad física'),
    'realiza_fuerza': ('binaria', 'Actividad física'), 'frecuencia_fuerza': ('ordinal', 'Actividad física'),
    'horas_sedentarismo': ('continua', 'Actividad física'),
    # Alimentación
    'quien_prepara_comidas': ('nominal', 'Alimentación'), 'frecuencia_comida_fuera': ('ordinal', 'Alimentación'),
    'falta_tiempo_influye': ('ordinal', 'Alimentación'),
    **{v: ('ordinal', 'Alimentación') for v in [
        'vasos_agua_dia', 'platos_verduras_dia', 'frutas_dia', 'panes_dia', 'lacteos_dia', 'jugos_gaseosas_dia',
        'bebidas_energeticas_dia', 'pescado_semana', 'legumbres_semana', 'carnes_semana', 'golosinas_semana']},
    # Sustancias
    'tabaco_frecuencia': ('ordinal', 'Sustancias'), 'alcohol_frecuencia': ('ordinal', 'Sustancias'),
    'marihuana_frecuencia': ('ordinal', 'Sustancias'),
}

# --- Preguntas condicionales ----------------------------------------------------
# Frecuencias que valen 0 ("no lo hace") cuando la pregunta madre es "No": el 0
# es un valor real de la escala (frecuencia cero).
CERO_SI_NO = {
    'frecuencia_aerobico': 'realiza_aerobico', 'frecuencia_bajo_impacto': 'realiza_bajo_impacto',
    'frecuencia_fuerza': 'realiza_fuerza', 'cantidad_personas_cuida': 'cuida_otras_personas',
    'sobrecarga_fisica_emocional': 'cuida_otras_personas',
}
# Preguntas que NO aplican a una parte de las participantes: se codifican con
# NO_APLICA (0 en las ordinales, 'NO_APLICA' en las nominales). No es un valor
# de la escala; quien no aplica nunca se mezcla con quien no respondió.
NO_APLICA = 0
CONDICIONALES_NO_APLICA = {
    'lugar_trabajo_comprensivo': 'no trabaja', 'estres_entorno_laboral': 'no trabaja',
    'menstruacion_llega': 'no menstrúa o sin fecha de última menstruación',
    'tipo_sangrado': 'no menstrúa o sin fecha de última menstruación',
    'usa_metodo_anticonceptivo': 'no menstrúa o sin fecha de última menstruación',
    'tipo_metodo_anticonceptivo': 'no usa método anticonceptivo (o no menstrúa)',
}
# Quienes debían responder la sección Trabajo pero no tienen dato: se imputa la
# mediana de las trabajadoras (mismo criterio de la Fase 34B) y se marca.
IMPUTAR_MEDIANA_TRABAJO = ['lugar_trabajo_comprensivo', 'estres_entorno_laboral']

# --- Validación contra la simulación (Módulo 3; NO decide nada) -------------------
# (variable, signo esperado con mrs_total: +1, -1 o 0 = sin efecto, subconjunto, texto)
PATRONES_SIMULACION = [
    ('imc', +1, None, 'IMC: más IMC, más síntomas (efecto gradual)'),
    ('usa_medicamentos_diabetes', +1, None, 'Diabetes: más síntomas'),
    ('doble_carga', +1, None, 'Doble carga trabajo + cuidado: más síntomas'),
    ('sobrecarga_fisica_emocional', +1, 'cuida', 'Sobrecarga por cuidado: más síntomas'),
    ('estres_entorno_laboral', +1, 'trabaja', 'Estrés laboral: más síntomas'),
    ('lugar_trabajo_comprensivo', -1, 'trabaja', 'Lugar de trabajo comprensivo: protector'),
    ('dias_ejercicio_semana', -1, None, 'Días de ejercicio: protector'),
    ('vasos_agua_dia', -1, None, 'Vasos de agua: protector'),
    ('tabaco_frecuencia', +1, None, 'Tabaco: más síntomas'),
    ('alcohol_frecuencia', +1, None, 'Alcohol: más síntomas'),
    ('marihuana_frecuencia', +1, None, 'Marihuana: más síntomas'),
    ('menstruacion_llega', 0, 'menstrua', 'Ginecológica generada sin efecto'),
    ('tipo_sangrado', 0, 'menstrua', 'Ginecológica generada sin efecto'),
    ('usa_metodo_anticonceptivo', 0, 'menstrua', 'Ginecológica generada sin efecto'),
    ('operada_no_mas_hijos', 0, None, 'Ginecológica generada sin efecto'),
    ('tiene_utero', 0, None, 'Ginecológica generada sin efecto'),
    ('tiene_ovario', 0, None, 'Ginecológica generada sin efecto'),
    ('usa_medicamentos_presion', 0, None, 'Medicamentos para la presión: generados sin efecto'),
    ('evacuacion_intestinal', 0, None, 'Evacuación intestinal: generada sin efecto'),
    ('distension_abdominal', 0, None, 'Distensión abdominal: generada sin efecto'),
    ('rendimiento_afectado', +1, 'trabaja', 'Consecuencia: aumenta con la severidad (no predictora)'),
    ('bienestar_trabajo_afectado', +1, 'trabaja', 'Consecuencia: aumenta con la severidad (no predictora)'),
    ('frecuencia_ausencias', +1, 'trabaja', 'Consecuencia: aumenta con la severidad (no predictora)'),
    ('cambio_relacion_pareja_menopausia', +1, 'pareja', 'Consecuencia: aumenta con la severidad (no predictora)'),
    ('usa_antidepresivos', +1, None, 'Consecuencia: aumenta con la severidad (no predictora)'),
]

# Columnas que jamás pueden quedar como predictoras (control de fuga).
PROHIBIDAS = ['mrs_total', 'mrs_severidad', 'severidad_mrs_4', 'severo_mrs', 'mrs_somatico', 'mrs_psicologico',
              'mrs_urogenital', *[f'pregunta_{i}' for i in range(1, 12)], 'rendimiento_afectado',
              'bienestar_trabajo_afectado', 'frecuencia_ausencias', 'cambio_relacion_pareja_menopausia',
              'usa_antidepresivos', 'imc_fue_imputado', 'comuna', 'nivel_educacion', *EXCLUIDAS_MODELADO]
