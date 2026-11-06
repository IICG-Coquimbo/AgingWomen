"""
Roles de las variables y codificación numérica para los modelos (Fase 33).

Roles (decisión aprobada 2026-10-11):
  - PREDICTORES: hábitos y condiciones que la usuaria puede modificar o que
    describen su carga (lo que el modelo de recomendaciones va a usar).
  - CONTROL: características que influyen en los síntomas pero no son hábitos.
  - IMPACTO: consecuencias de los síntomas; NO entran como predictores (si no,
    el modelo "explicaría" los síntomas con sus propios efectos).
La sección Trabajo solo existe para quienes trabajan, así que sus predictores
van en un modelo aparte (PREDICTORES_TRABAJO).
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
LIMPIO = RAIZ / 'datos' / 'limpio'
LIMPIO_USUARIA = RAIZ / 'datos' / 'limpio_usuaria'

MRS_ITEMS = {
    'pregunta_1': 'Bochornos y sudoración', 'pregunta_2': 'Molestias al corazón',
    'pregunta_3': 'Dolor muscular y articular', 'pregunta_4': 'Problemas de sueño',
    'pregunta_5': 'Ánimo depresivo', 'pregunta_6': 'Irritabilidad', 'pregunta_7': 'Ansiedad',
    'pregunta_8': 'Cansancio físico y mental', 'pregunta_9': 'Problemas sexuales',
    'pregunta_10': 'Problemas urinarios', 'pregunta_11': 'Sequedad vaginal',
}
MRS_PUNTAJES = {'mrs_total': 'MRS total', 'mrs_somatico': 'MRS somático',
                'mrs_psicologico': 'MRS psicológico', 'mrs_urogenital': 'MRS urogenital'}
ORDEN_SEVERIDAD = ['Sin síntomas o muy leves', 'Leve', 'Moderada', 'Severa']
ORDEN_ETAPA = ['premenopausia', 'perimenopausia', 'posmenopausia', 'quirurgica', 'indeterminada']
# Corte "severa" = último tramo de MRS.SEVERIDAD_TOTAL (16 o más puntos).
CORTE_SEVERA = 16

PREDICTORES = {
    # Actividad física
    'dias_ejercicio_semana': 'Días de ejercicio a la semana',
    'frecuencia_aerobico': 'Frecuencia de ejercicio aeróbico',
    'frecuencia_bajo_impacto': 'Frecuencia de ejercicio de bajo impacto',
    'frecuencia_fuerza': 'Frecuencia de ejercicio de fuerza',
    'horas_sedentarismo': 'Horas sentada al día',
    # Alimentación
    'quien_prepara_comidas': 'Quién prepara las comidas',
    'frecuencia_comida_fuera': 'Comidas fuera del hogar',
    'falta_tiempo_influye': 'Falta de tiempo influye en lo que come',
    'vasos_agua_dia': 'Vasos de agua al día', 'platos_verduras_dia': 'Platos de verduras al día',
    'frutas_dia': 'Frutas al día', 'panes_dia': 'Panes al día', 'lacteos_dia': 'Lácteos al día',
    'jugos_gaseosas_dia': 'Jugos y gaseosas al día',
    'bebidas_energeticas_dia': 'Bebidas energéticas al día',
    'pescado_semana': 'Pescado a la semana', 'legumbres_semana': 'Legumbres a la semana',
    'carnes_semana': 'Carnes a la semana', 'golosinas_semana': 'Dulces y snacks a la semana',
    # Sustancias
    'tabaco_frecuencia': 'Tabaco', 'marihuana_frecuencia': 'Marihuana', 'alcohol_frecuencia': 'Alcohol',
    # Cuidado
    'cuida_otras_personas': 'Cuida a otras personas',
    'cantidad_personas_cuida': 'Cantidad de personas que cuida',
    'sobrecarga_fisica_emocional': 'Sobrecarga por trabajo y cuidado',
    'doble_carga': 'Doble carga (trabaja y cuida)',
}
PREDICTORES_TRABAJO = {
    'estres_entorno_laboral': 'Estrés del entorno laboral',
    'lugar_trabajo_comprensivo': 'Lugar de trabajo comprensivo',
}
CONTROL = {
    'edad': 'Edad', 'etapa_menopausica': 'Etapa menopáusica', 'imc': 'IMC',
    'usa_terapia_hormonal': 'Usa terapia hormonal', 'nivel_educacion': 'Nivel educacional',
    'prevision': 'Previsión de salud', 'trabaja_actualmente': 'Trabaja actualmente',
}
IMPACTO = {
    'rendimiento_afectado': 'Rendimiento laboral afectado',
    'bienestar_trabajo_afectado': 'Bienestar en el trabajo afectado',
    'frecuencia_ausencias': 'Ausencias o atrasos por síntomas',
    'cambio_relacion_pareja_menopausia': 'Cambio en la relación de pareja',
    'usa_antidepresivos': 'Usa antidepresivos o medicamentos para dormir',
}
# Otras variables que se describen y se cruzan con el MRS, pero no entran al modelo.
OTRAS = {
    'origen_procedencia': 'Origen', 'pueblo_originario_afro': 'Pueblo originario / afro',
    'tiene_pareja': 'Tiene pareja', 'tiene_actividad_sexual': 'Tiene actividad sexual',
    'usa_medicamentos_diabetes': 'Medicamentos para la diabetes',
    'usa_medicamentos_presion': 'Medicamentos para la presión',
    'evacuacion_intestinal': 'Frecuencia de evacuación intestinal',
    'distension_abdominal': 'Distensión abdominal', 'circunferencia_cintura_cm': 'Cintura (cm)',
    'ha_consultado_por_sintomas': 'Ha consultado por síntomas',
    'sintomas_tomados_en_serio': 'Siente que toman en serio sus síntomas',
    'considera_informacion_suficiente': 'Información del sistema suficiente',
    'nivel_informacion_servicios': 'Qué tan informada se siente',
}
SUBGRUPO_PROFESIONAL = {
    'presion_sistolica': 'Presión sistólica', 'presion_diastolica': 'Presión diastólica',
    'colesterol_total_mg_dl': 'Colesterol total', 'colesterol_hdl_mg_dl': 'Colesterol HDL',
    'trigliceridos_mg_dl': 'Triglicéridos', 'glicemia_mg_dl': 'Glicemia',
    'riesgo_cv_atp3': 'Riesgo cardiovascular', 'perdida_talla_cm': 'Pérdida de talla (cm)',
}
CONTINUAS = ['edad', 'imc', 'talla_actual_cm', 'peso_kg', 'circunferencia_cintura_cm',
             'horas_sedentarismo', 'mrs_total', 'mrs_somatico', 'mrs_psicologico', 'mrs_urogenital']
CONTINUAS_PROFESIONAL = ['presion_sistolica', 'presion_diastolica', 'colesterol_total_mg_dl',
                         'colesterol_hdl_mg_dl', 'trigliceridos_mg_dl', 'glicemia_mg_dl',
                         'perdida_talla_cm']

# --- Conjunto de la usuaria común (Fase 34C, plan aprobado 2026-10-24) ---
# Sin servicios de salud (laboratorio, presión, cintura, tamizaje), sin nivel
# educacional ni ConocimientoSistema. La diabetes pasa a control; el IMC entra
# como categoría con "no informado" (no se imputa) y, aparte, como número solo
# en quienes lo informaron. Son decisiones de la 34C: hoy la etapa es descriptiva
# (2026-11-01), la diabetes queda fuera de las 33 elegibles y la 35A imputa el IMC.
CONTROL_USUARIA = {
    'edad': 'Edad', 'etapa_menopausica': 'Etapa menopáusica', 'imc_categoria': 'IMC (categoría)',
    'imc': 'IMC (solo informadas)', 'usa_terapia_hormonal': 'Usa terapia hormonal',
    'prevision': 'Previsión de salud', 'usa_medicamentos_diabetes': 'Medicamentos para la diabetes',
    'trabaja_actualmente': 'Trabaja actualmente',
}
OTRAS_USUARIA = {
    'origen_procedencia': 'Origen', 'pueblo_originario_afro': 'Pueblo originario / afro',
    'comuna': 'Comuna', 'tiene_pareja': 'Tiene pareja', 'tiene_actividad_sexual': 'Tiene actividad sexual',
}
CONTINUAS_USUARIA = ['edad', 'imc', 'peso_kg', 'talla_actual_cm', 'horas_sedentarismo']
ORDEN_IMC = ['bajo peso', 'normal', 'sobrepeso', 'obesidad', 'no informado']

# Ajuste 34C (aprobado 2026-10-24): frecuencias de todas las variables y
# asociación con la severidad de las ginecológicas y de salud general.
GINECOLOGICAS = {
    'menstruacion_llega': 'Regularidad de la menstruación', 'tipo_sangrado': 'Tipo de sangrado',
    'usa_metodo_anticonceptivo': 'Usa método anticonceptivo',
    'tipo_metodo_anticonceptivo': 'Método anticonceptivo',
    'operada_no_mas_hijos': 'Operada para no tener más hijos', 'tiene_utero': 'Tiene útero',
    'tiene_ovario': 'Tiene ovarios',
}
SALUD_USUARIA = {
    'usa_medicamentos_presion': 'Medicamentos para la presión',
    'evacuacion_intestinal': 'Frecuencia de evacuación intestinal',
    'distension_abdominal': 'Distensión abdominal',
}
# Selección múltiple: se guarda como texto con las opciones separadas por ", ".
MULTISELECCION = ['a_quien_cuida']
# Ordinales guardadas como texto (orden de la pregunta).
ORDEN_TEXTO = {'tipo_sangrado': ['MUY_LEVE', 'LEVE', 'MODERADO', 'ABUNDANTE', 'MUY_ABUND']}

ETIQUETAS = {**MRS_ITEMS, **MRS_PUNTAJES, **PREDICTORES, **PREDICTORES_TRABAJO, **CONTROL,
             **IMPACTO, **OTRAS, **SUBGRUPO_PROFESIONAL, **CONTROL_USUARIA, **OTRAS_USUARIA,
             **GINECOLOGICAS, **SALUD_USUARIA,
             'imc': 'IMC', 'a_quien_cuida': 'A quién cuida', 'genero': 'Género',
             'realiza_aerobico': 'Realiza ejercicio aeróbico',
             'realiza_bajo_impacto': 'Realiza ejercicio de bajo impacto',
             'realiza_fuerza': 'Realiza ejercicio de fuerza',
             'talla_actual_cm': 'Talla (cm)', 'peso_kg': 'Peso (kg)',
             'talla_maxima_cm': 'Talla máxima (cm)', 'severidad': 'Severidad MRS (0-3)'}

# Preguntas condicionales: cuando la pregunta madre es "No", la hija vale 0
# ("no lo hace") en vez de quedar vacía.
CERO_SI_NO = {
    'frecuencia_aerobico': 'realiza_aerobico', 'frecuencia_bajo_impacto': 'realiza_bajo_impacto',
    'frecuencia_fuerza': 'realiza_fuerza', 'cantidad_personas_cuida': 'cuida_otras_personas',
    'sobrecarga_fisica_emocional': 'cuida_otras_personas',
}
# Orden del nivel educacional (models.Identificacion.NivelEducativo).
ORDEN_EDUCACION = ['SIN', 'B_INC', 'B_COM', 'M_INC', 'M_COM', 'S_N_INC', 'S_N_COM', 'U_INC',
                   'U_COM', 'POST']
BINARIAS = {'SI': 1, 'NO': 0, 'True': 1, 'False': 0}


def etiqueta(variable):
    """Nombre legible; para columnas one-hot 'var=valor' → 'Etiqueta: valor'."""
    if '=' in variable:
        base, valor = variable.split('=', 1)
        return f'{ETIQUETAS.get(base, base)}: {valor}'
    return ETIQUETAS.get(variable, variable)


def cargar(carpeta=LIMPIO, archivo='dataset_menopausia_limpio.csv'):
    """Dataset limpio y su diccionario de variables (por omisión, el de la profesora, Fase 32)."""
    df = pd.read_csv(carpeta / archivo, dtype=str, keep_default_na=False,
                     encoding='utf-8-sig').replace('', np.nan)
    diccionario = pd.read_csv(carpeta / 'diccionario_variables.csv', encoding='utf-8-sig')
    return df, diccionario


def numerica(serie):
    return pd.to_numeric(serie, errors='coerce')


def codificar(df, variables):
    """
    Matriz numérica para los modelos:
      - ordinales y continuas → número (nivel educacional según su orden);
      - SI/NO y True/False → 1/0;
      - categóricas de más de dos valores → una columna 0/1 por valor ('var=valor').
    """
    columnas = {}
    for v in variables:
        s = df[v]
        if v in CERO_SI_NO and CERO_SI_NO[v] in df:
            s = s.where(df[CERO_SI_NO[v]] != 'NO', '0')
        if v == 'nivel_educacion':
            columnas[v] = s.map({c: i for i, c in enumerate(ORDEN_EDUCACION)})
        elif v in ORDEN_TEXTO:
            columnas[v] = s.map({c: i for i, c in enumerate(ORDEN_TEXTO[v])})
        elif s.dropna().isin(BINARIAS).all():
            columnas[v] = s.map(BINARIAS)
        elif numerica(s.dropna()).notna().all():
            columnas[v] = numerica(s)
        else:
            for valor in sorted(s.dropna().unique()):
                columnas[f'{v}={valor}'] = (s == valor).astype(int)
    return pd.DataFrame(columnas, index=df.index)
