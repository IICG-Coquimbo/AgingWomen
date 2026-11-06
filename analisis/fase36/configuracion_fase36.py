"""
Fase 36B: constantes de la preparación de matrices. No lee datos ni escribe archivos.

Fija las rutas de entrada, los roles por variable y las agrupaciones de categorías de FAMD acordadas en el protocolo
ajustado. Las agrupaciones se escriben aquí, no se recalculan al construir: la regla solo se usa en una prueba, para
comprobar que produce esta misma tabla.
"""
from pathlib import Path

ANALISIS = Path(__file__).resolve().parents[1]
RAIZ = ANALISIS.parent
SALIDA_POR_DEFECTO = ANALISIS / 'fase36'

SUCIO = RAIZ / 'datos' / 'sintetico' / 'dataset_usuaria_sucio.csv'
LIMPIO = RAIZ / 'datos' / 'limpio_usuaria' / 'dataset_usuaria_limpio.csv'
F35 = RAIZ / 'datos' / 'analitico' / 'dataset_fase35.csv'
DICCIONARIO = ANALISIS / 'fase36_diseno' / 'diccionario_codificacion_fase36.csv'
MATRIZ_DECISIONES = ANALISIS / 'fase36_diseno' / 'matriz_decisiones_variables.csv'
RELEVANCIA = ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables' / 'permutaciones_50000' / 'relevancia_33.csv'
ORIGEN = ANALISIS / 'revision_correctiva_fase34' / 'tablas' / 'origen_respuestas_34D.csv'
AUDITORIA_FIGURAS = ANALISIS / 'revision_correctiva_fase34' / 'tablas' / 'auditoria_figuras_34D.csv'
MANIFIESTO_CIERRE = ANALISIS / 'cierre_fases_34_35' / 'integridad' / 'manifiesto_despues.csv'
# Archivos del simulador que esta fase nunca debe abrir.
PROHIBIDOS = ('dataset_usuaria_verdad.csv', 'bitacora_suciedad.csv')

SEMILLA = 42  # Solo para los datos de prueba de la validación: construir las matrices no usa azar.
VERSION = '36B-1'
FECHA_VERSION = '2026-11-05'
COMMIT_ESPERADO = '745d689'

CUANTITATIVAS = ['edad', 'imc', 'horas_sedentarismo']
BINARIAS = ['trabaja_actualmente', 'tiene_pareja', 'tiene_actividad_sexual', 'operada_no_mas_hijos', 'usa_medicamentos_presion']
NOMINALES = ['quien_prepara_comidas']
ORDINALES = ['alcohol_frecuencia', 'cantidad_personas_cuida', 'carnes_semana', 'dias_ejercicio_semana', 'distension_abdominal',
             'evacuacion_intestinal', 'falta_tiempo_influye', 'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_comida_fuera',
             'frecuencia_fuerza', 'frutas_dia', 'golosinas_semana', 'jugos_gaseosas_dia', 'lacteos_dia', 'legumbres_semana', 'panes_dia',
             'pescado_semana', 'platos_verduras_dia', 'tabaco_frecuencia', 'vasos_agua_dia']
GENERALES = CUANTITATIVAS + BINARIAS + NOMINALES + ORDINALES
LABORALES = ['lugar_trabajo_comprensivo', 'estres_entorno_laboral']
SOBRECARGA = 'sobrecarga_fisica_emocional'
MODULOS = LABORALES + [SOBRECARGA]
ORDINALES_CATEGORICAS = ['frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'cantidad_personas_cuida', 'tabaco_frecuencia']

# Pregunta que decide si la variable aplica. `estructural` es el nivel que corresponde cuando la madre vale NO.
MADRES = {
    'frecuencia_aerobico': {'variable': 'realiza_aerobico', 'no': 'NO', 'estructural': '0'},
    'frecuencia_bajo_impacto': {'variable': 'realiza_bajo_impacto', 'no': 'NO', 'estructural': '0'},
    'frecuencia_fuerza': {'variable': 'realiza_fuerza', 'no': 'NO', 'estructural': '0'},
    'cantidad_personas_cuida': {'variable': 'cuida_otras_personas', 'no': 'NO', 'estructural': '0'},
}
# Solo en estas tres variables «Nunca» (1) y «No lo realiza» (0) significan frecuencia efectiva cero.
NUNCA_UNIFICADO = ['frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza']
PREGUNTA_PREVIA = {
    'lugar_trabajo_comprensivo': 'trabaja_actualmente', 'estres_entorno_laboral': 'trabaja_actualmente',
    'cantidad_personas_cuida': 'cuida_otras_personas', 'sobrecarga_fisica_emocional': 'cuida_otras_personas',
    'frecuencia_aerobico': 'realiza_aerobico', 'frecuencia_bajo_impacto': 'realiza_bajo_impacto', 'frecuencia_fuerza': 'realiza_fuerza'}
CAMPOS_CONTEXTO = ['realiza_aerobico', 'realiza_bajo_impacto', 'realiza_fuerza', 'cuida_otras_personas']

# Agrupaciones fijas de FAMD. El 0 incluye a «Nunca» en las tres frecuencias de ejercicio.
GRUPOS_FAMD = {
    'frecuencia_aerobico': {'0': ['0', '1'], '2 + 3': ['2', '3'], '4 + 5': ['4', '5']},
    'frecuencia_bajo_impacto': {'0': ['0', '1'], '2': ['2'], '3': ['3'], '4 + 5': ['4', '5']},
    'frecuencia_fuerza': {'0': ['0', '1'], '2 + 3': ['2', '3'], '4 + 5': ['4', '5']},
    'cantidad_personas_cuida': {'0': ['0'], '1': ['1'], '2': ['2'], '3': ['3']},
    'tabaco_frecuencia': {'1': ['1'], '2 + 3 + 4': ['2', '3', '4'], '5': ['5']},
    'quien_prepara_comidas': {'YO_MAYORIA': ['YO_MAYORIA'], 'COMPARTIDO': ['COMPARTIDO'], 'OTRA_HOGAR': ['OTRA_HOGAR'], 'COMPRO + OTRO': ['COMPRO', 'OTRO']},
}
GRUPOS_SIN_AGRUPAR = {
    'frecuencia_aerobico': {'0': ['0', '1'], '2': ['2'], '3': ['3'], '4': ['4'], '5': ['5']},
    'frecuencia_bajo_impacto': {'0': ['0', '1'], '2': ['2'], '3': ['3'], '4': ['4'], '5': ['5']},
    'frecuencia_fuerza': {'0': ['0', '1'], '2': ['2'], '3': ['3'], '4': ['4'], '5': ['5']},
    'cantidad_personas_cuida': {'0': ['0'], '1': ['1'], '2': ['2'], '3': ['3']},
    'tabaco_frecuencia': {'1': ['1'], '2': ['2'], '3': ['3'], '4': ['4'], '5': ['5']},
    'quien_prepara_comidas': {x: [x] for x in ['YO_MAYORIA', 'COMPARTIDO', 'OTRA_HOGAR', 'COMPRO', 'OTRO']},
}
# Límites de plausibilidad técnica: solo rechazan valores imposibles. Salir del rango de referencia no es error, solo se marca.
LIMITES = {'edad': (18, 110), 'imc': (10, 80), 'horas_sedentarismo': (0, 24)}

EXCLUIDAS_NOMBRE = ['usa_medicamentos_diabetes', 'doble_carga', 'prevision', 'etapa_menopausica', 'cuida_otras_personas', 'mrs_total', 'mrs_completo',
                    'severo_mrs', 'participante_id', 'imc_fue_imputado', 'imc_categoria', 'rut_hash', 'usuario_id', 'uuid_local', 'fecha_nacimiento',
                    'comuna', 'menstruacion_llega', 'tiene_utero', 'tiene_ovario', 'meses_desde_fum'] + MODULOS
EXCLUIDAS_PREFIJO = ['realiza_', 'mrs_', 'severidad_', 'consecuencia']
EXCLUIDAS_SUFIJO = ['_imputado']

ESCENARIOS = {'P1': ('pca', True), 'P2': ('pca', False), 'F1': ('famd', True), 'F2': ('famd', False)}
NOMBRE_ARCHIVO = {'P1': 'P1_pca_con_imc', 'P2': 'P2_pca_sin_imc', 'F1': 'F1_famd_con_imc', 'F2': 'F2_famd_sin_imc'}
DIMENSIONES = {'P1': (529, 34), 'P2': (529, 33), 'F1': (529, 50), 'F2': (529, 49)}
INERCIA = {'P1': 29.505, 'P2': 29.0, 'F1': 38.505, 'F2': 38.0}
