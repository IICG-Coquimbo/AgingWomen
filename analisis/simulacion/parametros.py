"""
Parámetros de la simulación.

Todos los números salen de analisis/supuestos_simulacion.md; la sección del
documento va indicada en cada bloque y cada valor lleva su etiqueta de fuente:
[C] Coquimbo, [N] Chile, [L] Latinoamérica/internacional, [S] supuesto propio.
Si la profesora corrige un valor, se cambia SOLO aquí y se vuelve a generar.

Fase 34A (reunión del 20-10): conjunto sintético de la usuaria común, solo
ronda 1, N = 550, con los efectos sobre el MRS validados por la profesora
(§8 y §13 del documento). La suciedad que se agrega después está al final.

Los códigos (FONASA, M_COM, 1-5…) son los mismos que usan los modelos de
Django, para que el Paso 3 cargue los CSV sin traducir nada.
"""
from datetime import date

# --- §1 Diseño de la muestra -------------------------------------------------
N_PARTICIPANTES = 550
N_RONDA2 = 0                           # solo primera encuesta (reunión 20-10)
# Con N = 550 cada muestra varía alrededor del efecto calibrado; se usa la primera
# semilla (desde 2026) cuya muestra cumple todos los controles de validación (§13).
SEMILLA = 2029

FECHA_INICIO_RONDA1 = date(2026, 3, 2)
FECHA_FIN_RONDA1 = date(2026, 9, 30)
FECHA_CORTE = date(2026, 9, 30)        # ninguna encuesta después de esta fecha
DIAS_ENTRE_RONDAS = 15                 # regla de la Fase 31 (plazo.py)
MAX_DIAS_ENTRE_RONDAS = 120

PROP_PROFESIONAL = 0.0                 # solo usuaria común: campos del servicio de salud vacíos
PROP_BLANCOS = 0.04                    # preguntas opcionales que se dejan en blanco
PROP_EXCEPCION_EDAD = 0.04             # menores de 40 con excepción de edad
EDAD_EXCEPCION = (36, 39)
EXCEPCION_TIPO = {'QUIRURGICA': 0.6, 'AUSENCIA': 0.4}                    # [S]

# --- §3 Perfil base ----------------------------------------------------------
# Edad 40-65 (forms.EDAD_MAXIMA). Mujeres de la región por tramo [C] Censo 2024;
# 60-64 y 65 estimados con la misma caída por tramo [S].
EDAD_MAXIMA = 65
TRAMOS_EDAD = [((40, 44), 30220), ((45, 49), 29334), ((50, 54), 28170),
               ((55, 59), 27740), ((60, 64), 24500), ((65, 65), 4600)]

REGION_COQUIMBO = '04'
# Comuna: (población femenina [C] Censo 2024, provincia). Nombres como en datos_geograficos.py.
COMUNAS = {
    'Coquimbo': (141325, 'Elqui'), 'La Serena': (137104, 'Elqui'),
    'Vicuña': (15522, 'Elqui'), 'Andacollo': (5964, 'Elqui'),
    'La Higuera': (2249, 'Elqui'), 'Paihuano': (2389, 'Elqui'),
    'Ovalle': (63505, 'Limarí'), 'Monte Patria': (16509, 'Limarí'),
    'Combarbalá': (7029, 'Limarí'), 'Punitaqui': (6342, 'Limarí'),
    'Río Hurtado': (2195, 'Limarí'),
    'Illapel': (16976, 'Choapa'), 'Salamanca': (15007, 'Choapa'),
    'Los Vilos': (12143, 'Choapa'), 'Canela': (4760, 'Choapa'),
}

GENERO = {'F': 0.99, 'PND': 0.01}                                         # [S]

# Migrantes por provincia [C] Casen 2022; país de origen [S].
PROP_MIGRANTE = {'Elqui': 0.039, 'Limarí': 0.022, 'Choapa': 0.042}
ORIGEN_MIGRANTE = {'VE': 0.35, 'PE': 0.15, 'CO': 0.15, 'BO': 0.10, 'HT': 0.10,
                   'AR': 0.05, 'EC': 0.03, 'OTRA': 0.07}

# Pueblo originario por provincia y composición [C] Casen 2022.
PROP_INDIGENA = {'Elqui': 0.056, 'Limarí': 0.094, 'Choapa': 0.050}
PUEBLOS = {'DIAGUITA': 0.578, 'MAPUCHE': 0.255, 'AYMARA': 0.069, 'CHANGO': 0.045,
           'COLLA': 0.019, 'QUECHUA': 0.009, 'OTRO': 0.025}

# Educación calibrada a 12,6 años promedio [C], algo más baja por generación [S].
# (código, peso, años de estudio aproximados)
EDUCACION = [('SIN', 0.01, 0), ('B_INC', 0.08, 5), ('B_COM', 0.07, 8),
             ('M_INC', 0.10, 10), ('M_COM', 0.32, 12), ('S_N_INC', 0.04, 13),
             ('S_N_COM', 0.14, 14), ('U_INC', 0.05, 14), ('U_COM', 0.15, 17),
             ('POST', 0.04, 19)]

PROP_TRABAJA = 0.61          # [C] ocupación mujeres 44,5 % ajustada a 40-60 años [S]

# Previsión de las mujeres [N] Casen 2022.
PREVISION = {'FONASA': 0.812, 'ISAPRE': 0.138, 'FFAA': 0.015, 'NINGUNA': 0.026, 'NS': 0.009}

# --- §4 Etapa reproductiva ---------------------------------------------------
EDAD_MENOPAUSIA_MEDIA = 49.0           # [L] REDLINC / estudio chileno
EDAD_MENOPAUSIA_DE = 3.5
EDAD_MENOPAUSIA_RANGO = (40, 58)
ANIOS_PERIMENOPAUSIA = 4
PROP_QUIRURGICA = 0.07                 # [S] histerectomía y/o ooforectomía (40-60)
PROP_SIN_OVARIOS_QUIRURGICA = 0.40     # [S]
PROP_FUM_SOLO_ANIO = 0.30              # [S] responde solo el año (si fue hace ≥2 años)

MENSTRUACION_LLEGA = {
    'pre': {'REGULAR': 0.75, 'IRREGULAR': 0.20, 'NO_SEGURA': 0.05},     # [S]
    'peri': {'REGULAR': 0.20, 'IRREGULAR': 0.75, 'NO_SEGURA': 0.05},
}
TIPO_SANGRADO = {
    'pre': {'MUY_LEVE': 0.08, 'LEVE': 0.25, 'MODERADO': 0.45, 'ABUNDANTE': 0.15, 'MUY_ABUND': 0.07},
    'peri': {'MUY_LEVE': 0.08, 'LEVE': 0.20, 'MODERADO': 0.37, 'ABUNDANTE': 0.23, 'MUY_ABUND': 0.12},
}
PROP_ANTICONCEPTIVO = 0.40             # [S] entre quienes menstrúan
TIPO_ANTICONCEPTIVO = {'DIU': 0.30, 'ORAL': 0.20, 'PRESERVATIVO': 0.20, 'IMPLANTE': 0.10,
                       'INYECTABLE': 0.10, 'OTRO': 0.05, 'NO_SE': 0.05}
OTRO_ANTICONCEPTIVO = ['Anillo vaginal', 'Parche', 'Método natural', 'Píldora del día después']
PROP_OPERADA_NO_MAS_HIJOS = 0.20       # [S]
PROP_TERAPIA_HORMONAL = {'post': 0.10, 'quirurgica': 0.10, 'peri': 0.03, 'pre': 0.0}  # [N] MUSA 2025

# --- §5 Salud crónica y EMPA -------------------------------------------------
HTA_POR_EDAD = (0.15, 0.45)            # 40 → 60 años [N] ENS 2016-17
DM_POR_EDAD = (0.06, 0.20)
FACTOR_DM_OBESIDAD = 1.8               # [L] la diabetes tipo 2 se concentra en IMC ≥ 30
FACTOR_BAJA_EDUCACION = 1.25           # < 8 años de estudio [N] ENS
PROP_MED_PRESION = 0.65                # [S] entre hipertensas
PROP_MED_DIABETES = 0.75               # [S] entre diabéticas

# Estado nutricional [N] ENS: (categoría, peso, rango de IMC).
IMC_CATEGORIAS = [('bajo', 0.005, (17.0, 18.5)), ('normal', 0.20, (18.5, 25.0)),
                  ('sobrepeso', 0.38, (25.0, 30.0)), ('obesidad', 0.37, (30.0, 40.0)),
                  ('morbida', 0.045, (40.0, 46.0))]
TALLA_MEDIA, TALLA_DE = 156.0, 6.0     # [S]

FECHA_EMPA = {'reciente': 0.40, 'antiguo': 0.30, 'nunca': 0.30}          # [S]
PROP_VDRL_REACTIVO = 0.01
PROP_PAP_VIGENTE = 0.60
RESULTADO_PAP = {'NEGATIVO': 0.85, 'INFLAMATORIO': 0.08, 'ATROFICO': 0.06, 'SOSPECHOSO': 0.01}
PROP_MAMOGRAFIA_VIGENTE = {'menor_50': 0.35, 'desde_50': 0.60}
BIRADS = {1: 0.50, 2: 0.35, 0: 0.08, 3: 0.05, 4: 0.02}

# --- §6 Estilo de vida -------------------------------------------------------
# Días de ejercicio (códigos 1-5: 0 días … todos los días) [N] ENS sedentarismo 90-93 %.
DIAS_EJERCICIO = {1: 0.55, 2: 0.32, 3: 0.08, 4: 0.03, 5: 0.02}
FACTOR_ACTIVA_EDUCACION_ALTA = 1.5     # [S] más ejercicio con >12 años de estudio
FACTOR_ACTIVA_OBESIDAD = 0.6           # [L] menos ejercicio con IMC ≥ 30
PROP_CUMPLE_5_PORCIONES = 0.145        # [N] ENS 16 %, descontado el factor por educación

# Porciones diarias (1 no consumo, 2 1-2, 3 3-4, 4 5-6, 5 7+) y semanales
# (1 nunca, 2 1-2, 3 3-4, 4 5-6, 5 diario). [S] salvo frutas/verduras.
VASOS_AGUA = {1: 0.05, 2: 0.30, 3: 0.37, 4: 0.18, 5: 0.10}
DESPLAZA_AGUA_ACTIVA = 0.6             # [S] quien hace ejercicio toma más agua (sube ~medio nivel)
PANES = {1: 0.10, 2: 0.65, 3: 0.22, 4: 0.03}
LACTEOS = {1: 0.15, 2: 0.65, 3: 0.18, 4: 0.02}
JUGOS = {1: 0.30, 2: 0.50, 3: 0.15, 4: 0.05}
ENERGETICAS = {1: 0.93, 2: 0.07}
PESCADO = {1: 0.35, 2: 0.55, 3: 0.10}
LEGUMBRES = {1: 0.10, 2: 0.65, 3: 0.25}
CARNES = {1: 0.05, 2: 0.30, 3: 0.45, 4: 0.15, 5: 0.05}
GOLOSINAS = {1: 0.15, 2: 0.40, 3: 0.30, 4: 0.10, 5: 0.05}
QUIEN_PREPARA = {'YO_MAYORIA': 0.65, 'COMPARTIDO': 0.20, 'OTRA_HOGAR': 0.10,
                 'COMPRO': 0.04, 'OTRO': 0.01}
OTRO_PREPARA = ['Mi madre', 'Una vecina', 'Empleada de casa particular', 'Mi hija']

PROP_FUMA = 0.27                       # [N] ENS
FRECUENCIA_FUMADORA = {5: 0.60, 4: 0.10, 3: 0.10, 2: 0.20}
ALCOHOL = {1: 0.40, 2: 0.45, 3: 0.10, 4: 0.03, 5: 0.02}                 # [S]
ALCOHOL_FUMADORA = {1: 0.25, 2: 0.48, 3: 0.17, 4: 0.06, 5: 0.04}        # [L] tabaco y alcohol van juntos
MARIHUANA = {1: 0.94, 2: 0.04, 3: 0.01, 4: 0.005, 5: 0.005}             # [S] ENPG: uso bajo en 40-65
MARIHUANA_FUMADORA = {1: 0.80, 2: 0.12, 3: 0.04, 4: 0.02, 5: 0.02}
# Tabaco y hormonas [L]: los estrógenos combinados están contraindicados en fumadoras
# mayores de 35 años (criterios OMS), así que fuman menos quienes usan TH o píldora.
FACTOR_TH_FUMADORA = 0.5
FACTOR_ORAL_FUMADORA = 0.3             # peso de ORAL entre los métodos de una fumadora

# --- §7 Cuidado y trabajo ----------------------------------------------------
PROP_CUIDA = {'40-49': 0.58, '50+': 0.42}                                # [S] promedio ~50 %
CANTIDAD_CUIDA = {1: 0.50, 2: 0.30, 3: 0.20}
# Probabilidad de marcar cada opción, por tramo de edad [S].
A_QUIEN_CUIDA = {
    'Hijos/as menores de edad': (0.70, 0.25),
    'Hijos/as adultos que dependen de usted': (0.10, 0.20),
    'Padres o suegros': (0.25, 0.50),
    'Abuelos u otros adultos mayores': (0.08, 0.08),
    'Cónyuge/pareja con dependencia': (0.04, 0.09),
    'Otro familiar o persona dependiente': (0.06, 0.06),
    'Otro': (0.03, 0.03),
}
OTRO_CUIDA = ['Nietos', 'Sobrina', 'Vecina adulta mayor', 'Hermano con discapacidad']
ESTRES_LABORAL = {1: 0.10, 2: 0.25, 3: 0.35, 4: 0.20, 5: 0.10}          # [S]
# Lugar de trabajo comprensivo (1-5): menos comprensivo donde hay más estrés [S].
COMPRENSIVO_MEDIA, COMPRENSIVO_DE, COMPRENSIVO_POR_ESTRES = 3.3, 1.0, -0.35

# --- §8 Síntomas MRS ---------------------------------------------------------
# Objetivo [N] Rev. Méd. Chile 2008, mujeres de 40-59 años.
OBJETIVO_MRS = {'somatico': 5.8, 'psicologico': 7.7, 'urogenital': 2.7, 'total': 16.2}
DOMINIOS_MRS = {'somatico': (1, 2, 3, 4), 'psicologico': (5, 6, 7, 8), 'urogenital': (9, 10, 11)}

# Modelo latente: intensidad continua de cada ítem =
#   base_i + CARGA_GENERAL·g + CARGA_DOMINIO·d_dominio + efectos + ruido,
# redondeada a la escala 0-4. Las bases se calibraron a mano (ver resumen del
# generador) para que las medias por dominio queden cerca del objetivo.
CARGA_GENERAL = 0.75
CARGA_DOMINIO = 0.55
RUIDO_ITEM = 0.55
BASE_ITEM = {1: 0.85, 2: 0.80, 3: 1.85, 4: 1.30,
             5: 1.60, 6: 1.75, 7: 1.65, 8: 2.10,
             9: 0.70, 10: 0.30, 11: 0.45}

# Efectos en unidades de la escala latente [L]/[N]/[S] (ver §8 del documento).
EFECTO_ETAPA = {
    'pre': {},
    'peri': {1: 0.45, 4: 0.30, 6: 0.30},
    'post': {1: 0.55, 2: 0.20, 3: 0.20, 4: 0.20, 5: 0.20, 6: 0.15, 7: 0.15, 8: 0.20,
             9: 0.45, 10: 0.35, 11: 0.70},
}
EFECTO_ETAPA['quirurgica'] = EFECTO_ETAPA['post']
EFECTO_TERAPIA_HORMONAL = {1: -0.60, 11: -0.45, 4: -0.20}

# Factores de estilo de vida validados por la profesora (reunión 20-10, §13).
# Cada factor suma `efecto × valor` a todos los ítems de un dominio, con el peso
# del dominio. El valor va centrado (0 = situación típica), así la media del MRS
# casi no se mueve. Signo + = más síntomas; − = protector. Los efectos se
# calibraron con N = 20 000 para que la correlación de Spearman de cada factor
# con el MRS total quede en el rango pedido (IMC ~0,25-0,35; resto ~0,10-0,25).
PESO_DOMINIO = {
    'general': {'somatico': 1.0, 'psicologico': 1.0, 'urogenital': 0.6},
    'fisico': {'somatico': 1.3, 'psicologico': 0.7, 'urogenital': 0.6},
    'carga': {'somatico': 0.7, 'psicologico': 1.4, 'urogenital': 0.3},
}
EFECTOS_ESTILO = {
    # factor: (efecto por unidad, tipo de peso). Unidades en generador.valores_factores.
    'imc': (0.27, 'fisico'),            # por cada 5 puntos de IMC sobre 27 (gradual)
    'diabetes': (0.38, 'fisico'),
    'doble_carga': (0.40, 'carga'),     # trabaja y cuida a otras personas
    'sobrecarga': (0.14, 'carga'),      # por punto sobre 3 (solo quien cuida)
    'estres': (0.18, 'carga'),          # por punto sobre 3 (solo quien trabaja)
    'comprensivo': (-0.12, 'carga'),    # por punto sobre 3 (solo quien trabaja)
    'ejercicio': (-0.42, 'general'),    # 0 días → 0; ≥ 1 día baja, más con más días
    'agua': (-0.12, 'general'),         # por nivel sobre 3 vasos
    'tabaco': (0.40, 'general'),        # de nunca (0) a diario (1)
    'alcohol': (0.65, 'general'),       # de nunca (0) a diario (1)
    'marihuana': (0.60, 'general'),     # de nunca (0) a diario (1)
    # Alimentos con efecto chico (+) o nulo; ninguno protector (reunión 20-10).
    'panes': (0.05, 'fisico'),          # por nivel sobre 2
    'golosinas': (0.05, 'general'),     # por nivel sobre 2
    'jugos': (0.05, 'general'),         # por nivel sobre 2
    'energeticas': (0.10, 'general'),   # por nivel sobre 1
}
# La población tiene más IMC y factores de riesgo que la "situación típica", así
# que la suma de efectos sube la media; esto la devuelve al objetivo chileno.
AJUSTE_DOMINIO = {'somatico': -0.50, 'psicologico': -0.40, 'urogenital': -0.30}

PROP_TIENE_PAREJA = 0.65                                                 # [S]
EVACUACION = {2: 0.50, 3: 0.25, 1: 0.10, 4: 0.15}                        # [S]
DISTENSION = {1: 0.35, 2: 0.40, 3: 0.18, 4: 0.07}

# --- §9 Conocimiento del sistema de salud (todo [S]) -------------------------
CONOCE_SISTEMA = {'SI': 0.35, 'NO': 0.45, 'NS': 0.20}
ESCUCHO_PROGRAMA = {'SI': 0.30, 'NO': 0.55, 'NS': 0.15}
SABE_DONDE = {'SI': 0.45, 'NO': 0.40, 'NS': 0.15}
EVALUACION_ATENCION = {1: 0.05, 2: 0.15, 3: 0.35, 4: 0.35, 5: 0.10}
PROP_CONTROL_CRONICA = 0.70
PROP_CONTROL_OTRA = 0.10
PROGRAMA_CRONICA = 'Programa de Salud Cardiovascular'
PROGRAMAS_OTROS = ['Programa de Salud de la Mujer', 'Programa de Climaterio',
                   'Programa de Salud Mental']
INFORMACION_SUFICIENTE = {1: 0.25, 2: 0.40, 3: 0.22, 4: 0.10, 5: 0.03}
NIVEL_INFORMACION = {1: 0.20, 2: 0.40, 3: 0.25, 4: 0.12, 5: 0.03}
CONOCE_RECURSOS = {'SI': 0.45, 'NO': 0.40, 'NS': 0.15}
DIFICULTADES_ACCESO = {'SI': 0.40, 'NO': 0.45, 'NS': 0.15}
PRINCIPALES_DIFICULTADES = {
    'Dificultad para obtener horas': 0.60, 'Falta de información': 0.45,
    'Horarios incompatibles': 0.35, 'No saber dónde consultar': 0.30,
    'Minimización de síntomas': 0.25, 'Falta de especialistas': 0.25,
    'Costos': 0.10, 'Otra': 0.03,
}
OTRA_DIFICULTAD = ['Distancia al consultorio', 'No hay matrona disponible', 'Trámites']
SINTOMAS_EN_SERIO = {1: 0.15, 2: 0.35, 3: 0.30, 4: 0.15, 5: 0.05}
PROP_DESEA_APOYO = 0.80
TIPO_APOYO = {
    'Manejo de síntomas': 0.60, 'Información general': 0.50, 'Salud mental': 0.40,
    'Atención ginecológica': 0.35, 'Terapia hormonal': 0.30, 'Nutrición': 0.30,
    'Actividad física': 0.25, 'Apoyo laboral': 0.25, 'Otro': 0.02,
}
OTRO_APOYO = ['Grupos de apoyo entre mujeres', 'Charlas en el trabajo', 'Sexualidad']

# --- Encuesta de satisfacción (opcional, al final) [S] ----------------------------
PROP_RESPONDE_SATISFACCION = 0.45
FACILIDAD = {1: 0.03, 2: 0.09, 3: 0.20, 4: 0.40, 5: 0.28}
FATIGA = {1: 0.42, 2: 0.38, 3: 0.14, 4: 0.06}
COMODIDAD = {1: 0.02, 2: 0.06, 3: 0.22, 4: 0.40, 5: 0.30}
RECOMENDARIA = {'SI': 0.68, 'TAL_VEZ': 0.25, 'NO': 0.07}
PROP_INCOMODIDAD = 0.12
COMENTARIOS_INCOMODIDAD = [
    'Me costó recordar la fecha de la última menstruación', 'La encuesta es muy larga',
    'Las preguntas sobre vida sexual me incomodaron', 'Las preguntas de porciones eran confusas',
    'No sabía qué responder sobre el útero y los ovarios', 'No sé mi peso exacto',
]

# --- Ronda 2 [S] ---------------------------------------------------------------
PROP_CAMBIO_ITEM_MRS = 0.25            # ítems que cambian ±1
PROP_CAMBIO_HABITO = 0.10
PROP_INICIA_TERAPIA = 0.03

# --- §14 Suciedad (Fase 34A) ------------------------------------------------------
# Errores que se agregan al conjunto limpio para practicar la limpieza. Mezcla
# los tipos del conjunto de la profesora con los patrones vistos en las 5
# respuestas reales de la plataforma (marcados [R]). Proporción = probabilidad
# por fila (o por celda, cuando se indica).
SUCIEDAD = {
    # Filas
    'duplicado_exacto': 0.012,          # la misma fila exportada dos veces [R] (hábitos duplicados)
    'rut_repetido': 0.010,              # una versión anterior de la misma participante
    # Preguntas que la usuaria deja en blanco [R]
    'sin_peso': 0.45,                   # solo 2 de 5 informaron peso y talla
    'sin_talla_si_falta_peso': 0.85,
    'sin_talla_con_peso': 0.05,
    'sin_cintura': 0.55,
    'cintura_cero': 0.10,               # "0.00" en vez de dejarla vacía [R]
    'sin_fecha_empa': 0.50,
    # Formatos
    'fum_dd_mm_aaaa': 0.10,             # [R]
    'fum_mes_texto': 0.04,              # "julio 2021"
    'fum_mm_aaaa': 0.04,                # "04/2002"
    'nacimiento_dd_mm_aaaa': 0.08,
    'unidad_en_texto': 0.03,            # "81.0 kg", "147 cm" (por celda de peso/talla/cintura)
    'coma_decimal': 0.03,               # "81,5"
    'codigo_variante': 0.02,            # Sí/si/S, Femenino/Mujer, verdadero/1 (por celda)
    'minusculas': 0.01,                 # fonasa, isapre (por celda)
    'espacios': 0.01,                   # " SI " (por celda de texto)
    'region_nombre': 0.03,              # "Coquimbo" en vez de "04"
    # Valores imposibles o centinelas
    'centinela_numero': 0.006,          # -1, 99, 999, 9999 (por celda numérica)
    'centinela_texto': 0.004,           # N/A, NA, sin dato, - (por celda)
    'talla_en_metros': 0.02,            # 1.56
    'talla_sin_punto': 0.004,           # 1620 (156,2 cm sin el punto)
    'peso_digito_extra': 0.006,         # 994
    'mrs_fuera_rango': 0.004,           # 5 o 9 en un ítem 0-4 (por celda)
    'fecha_nacimiento_imposible': 0.006,  # edad negativa o > 100
    'edad_fuera_criterio': 0.008,       # < 40 sin excepción o > 65
    # Lógica de la encuesta
    'condicional_lleno': 0.06,          # responde una pregunta que no aplica [R]
    'ejercicio_sin_tipo': 0.05,         # días de ejercicio sin tipo marcado [R]
    'oral_con_terapia': 0.15,           # píldora y terapia hormonal a la vez [R] (entre quienes usan píldora)
}
