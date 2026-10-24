"""
Generador de participantes simuladas (Paso 2).

Sigue la cadena de analisis/supuestos_simulacion.md §2: perfil → etapa
reproductiva → salud crónica → estilo de vida → cuidado y trabajo → síntomas
MRS → consecuencias. Cada bloque usa lo generado antes, para que las personas
salgan coherentes. Solo biblioteca estándar: corre igual en el computador y
dentro del contenedor.

Las respuestas se generan completas y después `aplicar_visibilidad` borra lo
que la encuesta real no mostraría (condicionales.py, campos solo para
personal de salud). Así un blanco en una pregunta "madre" oculta también a sus
hijas, igual que en la plataforma.
"""
import math
from datetime import date, timedelta

from . import parametros as P

# --- Columnas de cada sección (mismo orden que el esquema de la encuesta) -----
CAMPOS = {
    'identificacion': [
        'fecha_nacimiento', 'genero', 'nivel_educacion', 'origen_procedencia',
        'pueblo_originario_afro', 'region_residencia', 'comuna', 'trabaja_actualmente',
        'excepcion_edad',
    ],
    'trabajo': [
        'rendimiento_afectado', 'bienestar_trabajo_afectado', 'frecuencia_ausencias',
        'lugar_trabajo_comprensivo', 'estres_entorno_laboral',
    ],
    'tareas_cuidado': [
        'cuida_otras_personas', 'cantidad_personas_cuida', 'a_quien_cuida',
        'a_quien_cuida_otro', 'sobrecarga_fisica_emocional',
    ],
    'mrs': [f'pregunta_{i}' for i in range(1, 12)] + [
        'fecha_ultima_menstruacion', 'menstruacion_llega', 'tipo_sangrado',
        'usa_metodo_anticonceptivo', 'tipo_metodo_anticonceptivo',
        'tipo_metodo_anticonceptivo_otro', 'usa_terapia_hormonal', 'operada_no_mas_hijos',
        'tiene_utero', 'tiene_ovario', 'tiene_pareja', 'cambio_relacion_pareja_menopausia',
        'tiene_actividad_sexual', 'usa_antidepresivos', 'usa_medicamentos_diabetes',
        'usa_medicamentos_presion', 'evacuacion_intestinal', 'distension_abdominal',
    ],
    'empa': [
        'origen_registro', 'fecha_ultimo_empa', 'talla_actual_cm', 'talla_maxima_cm', 'peso_kg',
        'circunferencia_cintura_cm', 'presion_sistolica', 'presion_diastolica',
        'colesterol_total_mg_dl', 'colesterol_hdl_mg_dl', 'trigliceridos_mg_dl',
        'glicemia_mg_dl', 'vdrl_rpr', 'riesgo_cv_atp3', 'fecha_ultimo_pap', 'resultado_pap',
        'fecha_mamografia', 'resultado_birads', 'fecha_ecotomografia_mamaria',
    ],
    'habitos_de_vida': [
        'quien_prepara_comidas', 'quien_prepara_comidas_otro', 'frecuencia_comida_fuera',
        'falta_tiempo_influye', 'vasos_agua_dia', 'platos_verduras_dia', 'frutas_dia',
        'panes_dia', 'lacteos_dia', 'jugos_gaseosas_dia', 'bebidas_energeticas_dia',
        'pescado_semana', 'legumbres_semana', 'carnes_semana', 'golosinas_semana',
        'tabaco_frecuencia', 'marihuana_frecuencia', 'alcohol_frecuencia',
    ],
    'actividad_fisica': [
        'dias_ejercicio_semana', 'realiza_aerobico', 'frecuencia_aerobico',
        'realiza_bajo_impacto', 'frecuencia_bajo_impacto', 'realiza_fuerza',
        'frecuencia_fuerza', 'horas_sedentarismo',
    ],
    'conocimiento_sistema': [
        'prevision', 'conoce_sistema_publico_climaterio', 'ha_escuchado_programa_climaterio',
        'sabe_donde_acudir', 'ha_consultado_por_sintomas', 'evaluacion_atencion_recibida',
        'en_control_programa_consultorio', 'en_control_programa_cual',
        'considera_informacion_suficiente', 'nivel_informacion_servicios',
        'conoce_recursos_disponibles', 'ha_tenido_dificultades_acceso',
        'principales_dificultades', 'principales_dificultades_otra',
        'sintomas_tomados_en_serio', 'desea_mas_informacion_apoyo',
        'tipo_informacion_apoyo_deseado', 'tipo_informacion_apoyo_otro',
    ],
    'satisfaccion': [
        'facilidad_uso', 'fatiga_mental', 'comodidad_diseno', 'recomendaria', 'incomodidad',
        'comentario_incomodidad',
    ],
}
SECCIONES_POR_RONDA = [s for s in CAMPOS if s != 'identificacion']

# Campos que solo ve el personal de salud (campos_por_rol.SOLO_PROFESIONAL).
SOLO_PROFESIONAL = {
    'presion_sistolica', 'presion_diastolica', 'glicemia_mg_dl', 'colesterol_total_mg_dl',
    'colesterol_hdl_mg_dl', 'trigliceridos_mg_dl', 'riesgo_cv_atp3', 'fecha_ultimo_pap',
    'resultado_pap', 'fecha_mamografia', 'resultado_birads', 'fecha_ecotomografia_mamaria',
    'vdrl_rpr', 'talla_maxima_cm',
}
# Campos que nunca quedan en blanco (obligatorios en el formulario o del sistema).
OBLIGATORIOS = {
    'USUARIA': {'fecha_nacimiento', 'genero', 'nivel_educacion', 'origen_procedencia',
                'pueblo_originario_afro', 'region_residencia', 'comuna', 'excepcion_edad',
                'origen_registro'} | {f'pregunta_{i}' for i in range(1, 12)},
}
OBLIGATORIOS['PROFESIONAL'] = OBLIGATORIOS['USUARIA'] | {
    'talla_actual_cm', 'peso_kg', 'presion_sistolica', 'presion_diastolica'}

# Espejo de condicionales.py: campo → (campo del que depende, operador, valor).
CONDICIONES = {
    'menstruacion_llega': ('fecha_ultima_menstruacion', 'meses_lt', 12),
    'tipo_sangrado': ('fecha_ultima_menstruacion', 'meses_lt', 12),
    'usa_metodo_anticonceptivo': ('fecha_ultima_menstruacion', 'meses_lt', 12),
    'tipo_metodo_anticonceptivo': ('usa_metodo_anticonceptivo', 'igual', 'SI'),
    'tipo_metodo_anticonceptivo_otro': ('tipo_metodo_anticonceptivo', 'igual', 'OTRO'),
    'cantidad_personas_cuida': ('cuida_otras_personas', 'igual', 'SI'),
    'a_quien_cuida': ('cuida_otras_personas', 'igual', 'SI'),
    'a_quien_cuida_otro': ('a_quien_cuida', 'contiene', 'Otro'),
    'sobrecarga_fisica_emocional': ('cuida_otras_personas', 'igual', 'SI'),
    'quien_prepara_comidas_otro': ('quien_prepara_comidas', 'igual', 'OTRO'),
    'frecuencia_aerobico': ('realiza_aerobico', 'igual', 'SI'),
    'frecuencia_bajo_impacto': ('realiza_bajo_impacto', 'igual', 'SI'),
    'frecuencia_fuerza': ('realiza_fuerza', 'igual', 'SI'),
    'conoce_sistema_publico_climaterio': ('prevision', 'igual', 'FONASA'),
    'ha_escuchado_programa_climaterio': ('prevision', 'igual', 'FONASA'),
    'sabe_donde_acudir': ('prevision', 'igual', 'FONASA'),
    'ha_consultado_por_sintomas': ('prevision', 'igual', 'FONASA'),
    'evaluacion_atencion_recibida': ('ha_consultado_por_sintomas', 'igual', 'SI'),
    'en_control_programa_consultorio': ('prevision', 'igual', 'FONASA'),
    'en_control_programa_cual': ('en_control_programa_consultorio', 'igual', 'SI'),
    'considera_informacion_suficiente': ('prevision', 'igual', 'FONASA'),
    'nivel_informacion_servicios': ('prevision', 'igual', 'FONASA'),
    'conoce_recursos_disponibles': ('prevision', 'igual', 'FONASA'),
    'ha_tenido_dificultades_acceso': ('prevision', 'igual', 'FONASA'),
    'principales_dificultades': ('ha_tenido_dificultades_acceso', 'igual', 'SI'),
    'principales_dificultades_otra': ('principales_dificultades', 'contiene', 'Otra'),
    'tipo_informacion_apoyo_deseado': ('desea_mas_informacion_apoyo', 'igual', 'SI'),
    'tipo_informacion_apoyo_otro': ('tipo_informacion_apoyo_deseado', 'contiene', 'Otro'),
    # No es de condicionales.py: la ecotomografía solo se pide con BI-RADS 0, 3 o 4.
    'fecha_ecotomografia_mamaria': ('resultado_birads', 'en', (0, 3, 4)),
}


# --- Utilidades de azar ---------------------------------------------------------
def elegir(rng, pesos):
    """Elige una clave de un dict {opción: peso}."""
    opciones = list(pesos)
    return rng.choices(opciones, weights=[pesos[o] for o in opciones])[0]


def normal(rng, media, de, minimo=None, maximo=None):
    x = rng.gauss(media, de)
    if minimo is not None:
        x = max(minimo, x)
    if maximo is not None:
        x = min(maximo, x)
    return x


def entre(a, b, t):
    """Interpolación lineal de a a b con t en [0, 1]."""
    return a + (b - a) * min(1.0, max(0.0, t))


def fecha_azar(rng, desde, hasta):
    return desde + timedelta(days=rng.randint(0, max(0, (hasta - desde).days)))


def multiseleccion(rng, probs, minimo_uno=True):
    """Marca cada opción con su probabilidad; formato 'a, b' como guarda la encuesta."""
    marcadas = [op for op, p in probs.items() if rng.random() < p]
    if not marcadas and minimo_uno:
        marcadas = [elegir(rng, probs)]
    return marcadas


def meses_entre(desde, hasta):
    return (hasta.year - desde.year) * 12 + (hasta.month - desde.month)


def meses_desde_texto(texto, hoy):
    """Mismo cálculo que models.meses_desde_texto_fecha (solo año ⇒ julio)."""
    if not texto:
        return None
    partes = texto.split('-')
    anio = int(partes[0])
    mes = int(partes[1]) if len(partes) > 1 else 7
    return (hoy.year - anio) * 12 + (hoy.month - mes)


def edad_en(nacimiento, dia):
    return dia.year - nacimiento.year - ((dia.month, dia.day) < (nacimiento.month, nacimiento.day))


def rut_valido(numero):
    """RUT ficticio con dígito verificador correcto (módulo 11)."""
    suma, factor = 0, 2
    for d in reversed(str(numero)):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    dv = 11 - suma % 11
    dv = {11: '0', 10: 'K'}.get(dv, str(dv))
    return f'{numero:,}'.replace(',', '.') + f'-{dv}'


# --- 1. Perfil base (§3) ---------------------------------------------------------
def generar_perfil(rng, p, fecha):
    if rng.random() < P.PROP_EXCEPCION_EDAD:
        edad = rng.randint(*P.EDAD_EXCEPCION)
        p['excepcion'] = elegir(rng, P.EXCEPCION_TIPO)
    else:
        tramos = {t: peso for t, peso in P.TRAMOS_EDAD if t[0] <= P.EDAD_MAXIMA}
        lo, hi = elegir(rng, tramos)
        edad = rng.randint(lo, min(hi, P.EDAD_MAXIMA))
        p['excepcion'] = False
    # Nacimiento tal que tenga exactamente `edad` el día de la ronda 1.
    nacimiento = date(fecha.year - edad - 1, fecha.month, fecha.day) + timedelta(days=rng.randint(1, 364))
    p['nacimiento'], p['edad'] = nacimiento, edad_en(nacimiento, fecha)

    comuna = elegir(rng, {c: v[0] for c, v in P.COMUNAS.items()})
    p['comuna'], p['provincia'] = comuna, P.COMUNAS[comuna][1]

    p['origen'] = (elegir(rng, P.ORIGEN_MIGRANTE)
                   if rng.random() < P.PROP_MIGRANTE[p['provincia']] else 'CL')
    p['pueblo'] = (elegir(rng, P.PUEBLOS)
                   if rng.random() < P.PROP_INDIGENA[p['provincia']] else 'NINGUNO')

    educ = elegir(rng, {e[0]: e[1] for e in P.EDUCACION})
    p['educacion'] = educ
    p['anios_estudio'] = {e[0]: e[2] for e in P.EDUCACION}[educ]

    # Trabajo: más probable con más estudios, menos después de los 55 [S].
    prob = P.PROP_TRABAJA + 0.012 * (p['anios_estudio'] - 12) - (0.15 if p['edad'] >= 55 else 0)
    p['trabaja'] = rng.random() < min(0.95, max(0.10, prob))

    # Previsión: Isapre más probable con estudios universitarios y trabajo [S].
    pesos = dict(P.PREVISION)
    factor = (1.8 if p['anios_estudio'] >= 17 else 0.5 if p['anios_estudio'] < 12 else 1.0)
    pesos['ISAPRE'] *= factor * (1.3 if p['trabaja'] else 0.7)
    p['prevision'] = elegir(rng, pesos)
    p['genero'] = elegir(rng, P.GENERO)


# --- 2. Etapa reproductiva (§4) ---------------------------------------------------
def generar_etapa(rng, p, fecha):
    edad = p['edad']
    if p['excepcion'] == 'AUSENCIA':
        # Menopausia precoz sin cirugía: ya pasaron ≥ 12 meses sin menstruación.
        p['etapa'] = 'post'
        p['edad_menopausia'] = rng.randint(max(33, edad - 4), edad - 1)
    elif p['excepcion'] == 'QUIRURGICA' or rng.random() < P.PROP_QUIRURGICA:
        p['etapa'] = 'quirurgica'
        p['edad_menopausia'] = rng.randint(max(30, edad - 6), edad)
    else:
        p['edad_menopausia'] = round(normal(rng, P.EDAD_MENOPAUSIA_MEDIA, P.EDAD_MENOPAUSIA_DE,
                                            *P.EDAD_MENOPAUSIA_RANGO))
        if edad < p['edad_menopausia'] - P.ANIOS_PERIMENOPAUSIA:
            p['etapa'] = 'pre'
        elif edad < p['edad_menopausia']:
            p['etapa'] = 'peri'
        else:
            p['etapa'] = 'post'

    # Fecha de la última menstruación.
    if p['etapa'] in ('pre', 'peri'):
        dias = rng.randint(3, 40) if p['etapa'] == 'pre' else rng.randint(15, 330)
        fum = fecha - timedelta(days=dias)
    else:
        fum = date(p['nacimiento'].year + p['edad_menopausia'], rng.randint(1, 12), 15)
        if meses_entre(fum, fecha) < 12:       # la menopausia se confirma con 12 meses sin regla
            fum = fecha - timedelta(days=rng.randint(370, 700))
    p['fum'] = fum
    solo_anio = meses_entre(fum, fecha) >= 24 and rng.random() < P.PROP_FUM_SOLO_ANIO
    p['fum_texto'] = f'{fum.year}' if solo_anio else f'{fum.year}-{fum.month:02d}'

    quirurgica = p['etapa'] == 'quirurgica'
    p['tiene_utero'] = 'NO' if quirurgica else 'SI'
    p['tiene_ovario'] = 'NO' if quirurgica and rng.random() < P.PROP_SIN_OVARIOS_QUIRURGICA else 'SI'
    p['operada'] = 'SI' if rng.random() < P.PROP_OPERADA_NO_MAS_HIJOS else 'NO'


# --- 3. Salud crónica (§5) -------------------------------------------------------
def generar_salud(rng, p):
    t = (p['edad'] - 40) / 20
    baja_educ = P.FACTOR_BAJA_EDUCACION if p['anios_estudio'] < 8 else 1.0
    p['hta'] = rng.random() < entre(*P.HTA_POR_EDAD, t) * baja_educ
    p['med_presion'] = p['hta'] and rng.random() < P.PROP_MED_PRESION

    # IMC: obesidad algo más frecuente con la edad y con baja educación.
    pesos = {}
    for cat, peso, _ in P.IMC_CATEGORIAS:
        if cat in ('obesidad', 'morbida'):
            peso *= (1 + 0.01 * (p['edad'] - 50)) * baja_educ
        pesos[cat] = peso
    cat = elegir(rng, pesos)
    lo, hi = {c: r for c, _, r in P.IMC_CATEGORIAS}[cat]
    p['imc_categoria'], p['imc'] = cat, rng.uniform(lo, hi)
    p['talla'] = normal(rng, P.TALLA_MEDIA, P.TALLA_DE, 140, 178)
    p['peso'] = p['imc'] * (p['talla'] / 100) ** 2
    p['cintura'] = normal(rng, 2.3 * p['imc'] + 25, 6, 60, 150)
    p['talla_maxima'] = p['talla'] + rng.uniform(0, 1) + max(0, p['edad'] - 45) * rng.uniform(0, 0.12)

    # Diabetes: más frecuente con obesidad.
    factor_dm = P.FACTOR_DM_OBESIDAD if p['imc'] >= 30 else 1.0
    p['dm'] = rng.random() < entre(*P.DM_POR_EDAD, t) * baja_educ * factor_dm
    p['med_diabetes'] = p['dm'] and rng.random() < P.PROP_MED_DIABETES


# --- 4. Estilo de vida (§6) ------------------------------------------------------
def generar_estilo(rng, p):
    pesos = dict(P.DIAS_EJERCICIO)
    for k in (2, 3, 4, 5):
        if p['anios_estudio'] > 12 and k >= 3:
            pesos[k] *= P.FACTOR_ACTIVA_EDUCACION_ALTA
        if p['imc'] >= 30:
            pesos[k] *= P.FACTOR_ACTIVA_OBESIDAD
    p['dias_ejercicio'] = elegir(rng, pesos)
    p['activa'] = p['dias_ejercicio'] >= 3
    p['fuma'] = rng.random() < P.PROP_FUMA
    factor = 1.3 if p['anios_estudio'] > 12 else 1.0
    p['cumple_5_porciones'] = rng.random() < P.PROP_CUMPLE_5_PORCIONES * factor
    # Hábitos que influyen en el MRS: se fijan antes de calcular los síntomas.
    agua = elegir(rng, P.VASOS_AGUA)
    if p['dias_ejercicio'] >= 2 and rng.random() < P.DESPLAZA_AGUA_ACTIVA:
        agua = min(5, agua + 1)
    p['habitos'] = {
        'vasos_agua_dia': agua,
        'panes_dia': elegir(rng, P.PANES),
        'jugos_gaseosas_dia': elegir(rng, P.JUGOS),
        'bebidas_energeticas_dia': elegir(rng, P.ENERGETICAS),
        'golosinas_semana': elegir(rng, P.GOLOSINAS),
        'tabaco_frecuencia': elegir(rng, P.FRECUENCIA_FUMADORA) if p['fuma'] else 1,
        'alcohol_frecuencia': elegir(rng, P.ALCOHOL_FUMADORA if p['fuma'] else P.ALCOHOL),
        'marihuana_frecuencia': elegir(rng, P.MARIHUANA_FUMADORA if p['fuma'] else P.MARIHUANA),
    }


# --- 5. Cuidado y trabajo (§7) ---------------------------------------------------
def generar_cuidado(rng, p):
    tramo = '40-49' if p['edad'] < 50 else '50+'
    p['cuida'] = rng.random() < P.PROP_CUIDA[tramo]
    p['cantidad_cuida'] = elegir(rng, P.CANTIDAD_CUIDA) if p['cuida'] else None
    sobrecarga = 2.6 + (0.8 if p['trabaja'] else 0) + (0.6 if (p['cantidad_cuida'] or 0) >= 2 else 0)
    p['sobrecarga'] = min(5, max(1, round(normal(rng, sobrecarga, 0.9)))) if p['cuida'] else None
    p['estres'] = elegir(rng, P.ESTRES_LABORAL) if p['trabaja'] else None
    p['comprensivo'] = (escala(rng, P.COMPRENSIVO_MEDIA + P.COMPRENSIVO_POR_ESTRES * (p['estres'] - 3),
                               P.COMPRENSIVO_DE) if p['trabaja'] else None)


# --- 6. Síntomas MRS (§8) --------------------------------------------------------
def generar_latentes_mrs(rng, p):
    p['g'] = rng.gauss(0, 1)
    p['d'] = {dom: rng.gauss(0, 1) for dom in P.DOMINIOS_MRS}
    # Terapia hormonal: según etapa [N], más con Isapre y con muchos síntomas [S].
    prob = P.PROP_TERAPIA_HORMONAL[p['etapa']]
    prob *= (1.5 if p['prevision'] == 'ISAPRE' else 1.0) * (1.5 if p['g'] > 0.5 else 0.8)
    prob *= P.FACTOR_TH_FUMADORA if p['fuma'] else 1.0
    p['terapia_hormonal'] = rng.random() < prob


# Días de ejercicio (código 1-5) → valor del factor: la diferencia grande está
# entre no hacer ejercicio y hacerlo al menos un día.
VALOR_EJERCICIO = {1: 0.0, 2: 0.6, 3: 0.8, 4: 0.9, 5: 1.0}


def valores_factores(p):
    """Valor centrado de cada factor de P.EFECTOS_ESTILO (0 = situación típica)."""
    h = p['habitos']
    return {
        'imc': (p['imc'] - 27) / 5,
        'diabetes': float(p['dm']),
        'doble_carga': float(p['trabaja'] and p['cuida']),
        'sobrecarga': (p['sobrecarga'] - 3) if p['sobrecarga'] else 0,
        'estres': (p['estres'] - 3) if p['estres'] else 0,
        'comprensivo': (p['comprensivo'] - 3) if p['comprensivo'] else 0,
        'ejercicio': VALOR_EJERCICIO[p['dias_ejercicio']],
        'agua': h['vasos_agua_dia'] - 3,
        'tabaco': (h['tabaco_frecuencia'] - 1) / 4,
        'alcohol': (h['alcohol_frecuencia'] - 1) / 4,
        'marihuana': (h['marihuana_frecuencia'] - 1) / 4,
        'panes': h['panes_dia'] - 2,
        'golosinas': h['golosinas_semana'] - 2,
        'jugos': h['jugos_gaseosas_dia'] - 2,
        'energeticas': h['bebidas_energeticas_dia'] - 1,
    }


def efecto_estilo(p):
    """{dominio: desplazamiento latente} sumando todos los factores de estilo de vida."""
    valores = valores_factores(p)
    total = dict(P.AJUSTE_DOMINIO)
    for factor, (efecto, tipo) in P.EFECTOS_ESTILO.items():
        for dom, peso in P.PESO_DOMINIO[tipo].items():
            total[dom] += efecto * valores[factor] * peso
    return total


def calcular_mrs(rng, p):
    """Devuelve {1..11: 0-4} a partir del modelo latente y los efectos."""
    estilo = efecto_estilo(p)
    items = {}
    for dom, nums in P.DOMINIOS_MRS.items():
        for i in nums:
            x = P.BASE_ITEM[i] + P.CARGA_GENERAL * p['g'] + P.CARGA_DOMINIO * p['d'][dom]
            x += P.EFECTO_ETAPA[p['etapa']].get(i, 0)
            if p['terapia_hormonal']:
                x += P.EFECTO_TERAPIA_HORMONAL.get(i, 0)
            x += estilo[dom]
            x += rng.gauss(0, P.RUIDO_ITEM)
            items[i] = min(4, max(0, round(x)))
    return items


def puntajes_mrs(items):
    out = {dom: sum(items[i] for i in nums) for dom, nums in P.DOMINIOS_MRS.items()}
    out['total'] = sum(items.values())
    return out


# --- Construcción de cada sección -------------------------------------------------
def seccion_identificacion(p):
    return {
        'fecha_nacimiento': p['nacimiento'].isoformat(),
        'genero': p['genero'],
        'nivel_educacion': p['educacion'],
        'origen_procedencia': p['origen'],
        'pueblo_originario_afro': p['pueblo'],
        'region_residencia': P.REGION_COQUIMBO,
        'comuna': p['comuna'],
        'trabaja_actualmente': p['trabaja'],
        'excepcion_edad': p['excepcion'] or 'NINGUNA',
    }


def escala(rng, media, de=0.8, minimo=1, maximo=5):
    return min(maximo, max(minimo, round(rng.gauss(media, de))))


def seccion_trabajo(rng, p, mrs):
    if not p['trabaja']:
        return None
    t = mrs['total'] / 44
    return {
        'rendimiento_afectado': escala(rng, 1 + 3.5 * t),
        'bienestar_trabajo_afectado': escala(rng, 1 + 3.5 * t + 0.2 * (p['estres'] - 3)),
        'frecuencia_ausencias': escala(rng, 0.7 + 2.5 * t, 0.7),
        'lugar_trabajo_comprensivo': p['comprensivo'],
        'estres_entorno_laboral': p['estres'],
    }


def seccion_cuidado(rng, p):
    if not p['cuida']:
        return {'cuida_otras_personas': 'NO'}
    col = 0 if p['edad'] < 50 else 1
    marcadas = multiseleccion(rng, {op: v[col] for op, v in P.A_QUIEN_CUIDA.items()})
    return {
        'cuida_otras_personas': 'SI',
        'cantidad_personas_cuida': p['cantidad_cuida'],
        'a_quien_cuida': ', '.join(marcadas),
        'a_quien_cuida_otro': rng.choice(P.OTRO_CUIDA),
        'sobrecarga_fisica_emocional': p['sobrecarga'],
    }


def seccion_mrs(rng, p, items, mrs):
    fila = {f'pregunta_{i}': v for i, v in items.items()}
    etapa_menstrual = p['etapa'] if p['etapa'] in ('pre', 'peri') else 'pre'
    pareja = p['tiene_pareja']
    if pareja == 'SI':
        cambio = escala(rng, 1 + 0.25 * mrs['urogenital'] + 0.1 * mrs['psicologico'] - 0.6, 0.9)
        p_sexual = 0.80 - 0.01 * (p['edad'] - 40) - (0.10 if items[11] >= 3 else 0)
    else:
        cambio, p_sexual = 1, 0.15
    p_antidep = 0.03 + 0.015 * mrs['psicologico'] + (0.05 if items[4] >= 3 else 0)
    metodos = dict(P.TIPO_ANTICONCEPTIVO)
    if p['fuma']:
        metodos['ORAL'] *= P.FACTOR_ORAL_FUMADORA
    fila.update({
        'fecha_ultima_menstruacion': p['fum_texto'],
        'menstruacion_llega': elegir(rng, P.MENSTRUACION_LLEGA[etapa_menstrual]),
        'tipo_sangrado': elegir(rng, P.TIPO_SANGRADO[etapa_menstrual]),
        'usa_metodo_anticonceptivo': 'SI' if rng.random() < P.PROP_ANTICONCEPTIVO else 'NO',
        'tipo_metodo_anticonceptivo': elegir(rng, metodos),
        'tipo_metodo_anticonceptivo_otro': rng.choice(P.OTRO_ANTICONCEPTIVO),
        'usa_terapia_hormonal': 'SI' if p['terapia_hormonal'] else 'NO',
        'operada_no_mas_hijos': p['operada'],
        'tiene_utero': p['tiene_utero'],
        'tiene_ovario': p['tiene_ovario'],
        'tiene_pareja': pareja,
        'cambio_relacion_pareja_menopausia': cambio,
        'tiene_actividad_sexual': 'SI' if rng.random() < p_sexual else 'NO',
        'usa_antidepresivos': 'SI' if rng.random() < p_antidep else 'NO',
        'usa_medicamentos_diabetes': 'SI' if p['med_diabetes'] else 'NO',
        'usa_medicamentos_presion': 'SI' if p['med_presion'] else 'NO',
        'evacuacion_intestinal': elegir(rng, P.EVACUACION),
        'distension_abdominal': elegir(rng, P.DISTENSION),
    })
    return fila


def riesgo_atp3(p, col, hdl, sistolica):
    """Clasificación simplificada a partir de factores de riesgo [S]."""
    puntos = (p['edad'] >= 50) + (p['edad'] >= 55) + (col >= 240) + (hdl < 40)
    puntos += (sistolica >= 140) + p['fuma'] + 2 * p['dm']
    return 'BAJO' if puntos <= 2 else 'MODERADO' if puntos <= 4 else 'ALTO'


def seccion_empa(rng, p, fecha):
    tipo = elegir(rng, P.FECHA_EMPA)
    if tipo == 'reciente':
        f_empa = fecha_azar(rng, fecha - timedelta(days=365), fecha)
    elif tipo == 'antiguo':
        f_empa = fecha_azar(rng, fecha - timedelta(days=3 * 365), fecha - timedelta(days=366))
    else:
        f_empa = None
    fila = {
        'origen_registro': 'MEDICO' if p['aplicada_por'] == 'PROFESIONAL' else 'AUTO',
        'fecha_ultimo_empa': f_empa.isoformat() if f_empa else None,
        'talla_actual_cm': round(p['talla']),
        'talla_maxima_cm': round(p['talla_maxima']),
        'peso_kg': round(p['peso'], 1),
        'circunferencia_cintura_cm': round(p['cintura']),
    }
    if p['hta']:
        sis, dia = normal(rng, 138, 15, 100, 200), normal(rng, 86, 9, 60, 120)
    else:
        sis, dia = normal(rng, 117, 11, 90, 160), normal(rng, 74, 8, 50, 100)
    glicemia = normal(rng, 150, 40, 100, 350) if p['dm'] else normal(rng, 92, 10, 70, 125)
    col = normal(rng, 205 + (12 if p['etapa'] in ('post', 'quirurgica') else 0), 38, 120, 350)
    hdl = normal(rng, 52 - (5 if p['imc'] >= 30 else 0), 12, 25, 100)
    tg = math.exp(normal(rng, math.log(140) + (0.2 if p['imc'] >= 30 or p['dm'] else 0), 0.4))
    fila.update({
        'presion_sistolica': round(sis), 'presion_diastolica': round(dia),
        'colesterol_total_mg_dl': round(col), 'colesterol_hdl_mg_dl': round(hdl),
        'trigliceridos_mg_dl': round(min(tg, 800)), 'glicemia_mg_dl': round(glicemia),
        'vdrl_rpr': 'Reactivo' if rng.random() < P.PROP_VDRL_REACTIVO else 'No reactivo',
        'riesgo_cv_atp3': riesgo_atp3(p, col, hdl, sis),
    })
    # PAP: vigente (≤3 años), antiguo o nunca.
    r = rng.random()
    if r < P.PROP_PAP_VIGENTE:
        f_pap = fecha_azar(rng, fecha - timedelta(days=3 * 365), fecha)
    elif r < P.PROP_PAP_VIGENTE + 0.25:
        f_pap = fecha_azar(rng, fecha - timedelta(days=6 * 365), fecha - timedelta(days=3 * 365 + 1))
    else:
        f_pap = None
    resultados = dict(P.RESULTADO_PAP)
    if p['etapa'] not in ('post', 'quirurgica'):
        resultados.pop('ATROFICO')
    fila['fecha_ultimo_pap'] = f_pap.isoformat() if f_pap else None
    fila['resultado_pap'] = elegir(rng, resultados) if f_pap else None
    # Mamografía: vigente (≤2 años) más frecuente desde los 50.
    vigente = P.PROP_MAMOGRAFIA_VIGENTE['desde_50' if p['edad'] >= 50 else 'menor_50']
    r = rng.random()
    if r < vigente:
        f_mamo = fecha_azar(rng, fecha - timedelta(days=2 * 365), fecha)
    elif r < vigente + 0.30:
        f_mamo = fecha_azar(rng, fecha - timedelta(days=5 * 365), fecha - timedelta(days=2 * 365 + 1))
    else:
        f_mamo = None
    birads = elegir(rng, P.BIRADS) if f_mamo else None
    f_eco = (min(fecha, f_mamo + timedelta(days=rng.randint(7, 60)))
             if f_mamo and birads in (0, 3, 4) else None)
    fila.update({
        'fecha_mamografia': f_mamo.isoformat() if f_mamo else None,
        'resultado_birads': birads,
        'fecha_ecotomografia_mamaria': f_eco.isoformat() if f_eco else None,
    })
    return fila


def seccion_habitos(rng, p):
    if p['cumple_5_porciones']:
        frutas, verduras = rng.choice([(3, 3), (3, 2), (2, 3), (4, 2), (2, 4), (4, 3), (3, 4)])
    else:
        frutas = elegir(rng, {1: 0.10, 2: 0.78, 3: 0.12})
        verduras = elegir(rng, {1: 0.04, 2: 0.86, 3: 0.10})
        if frutas + verduras >= 6:             # 3-4 y 3-4 ya llegarían a 5 porciones
            verduras = 2
    trabaja_cuida = p['trabaja'] + p['cuida']
    return {
        'quien_prepara_comidas': elegir(rng, P.QUIEN_PREPARA),
        'quien_prepara_comidas_otro': rng.choice(P.OTRO_PREPARA),
        'frecuencia_comida_fuera': escala(rng, 1.6 + 0.6 * p['trabaja'], 0.8),
        'falta_tiempo_influye': escala(rng, 2.0 + 0.7 * trabaja_cuida, 0.9),
        'vasos_agua_dia': p['habitos']['vasos_agua_dia'],
        'platos_verduras_dia': verduras,
        'frutas_dia': frutas,
        'panes_dia': p['habitos']['panes_dia'],
        'lacteos_dia': elegir(rng, P.LACTEOS),
        'jugos_gaseosas_dia': p['habitos']['jugos_gaseosas_dia'],
        'bebidas_energeticas_dia': p['habitos']['bebidas_energeticas_dia'],
        'pescado_semana': elegir(rng, P.PESCADO),
        'legumbres_semana': elegir(rng, P.LEGUMBRES),
        'carnes_semana': elegir(rng, P.CARNES),
        'golosinas_semana': p['habitos']['golosinas_semana'],
        'tabaco_frecuencia': p['habitos']['tabaco_frecuencia'],
        'marihuana_frecuencia': p['habitos']['marihuana_frecuencia'],
        'alcohol_frecuencia': p['habitos']['alcohol_frecuencia'],
    }


def seccion_actividad(rng, p):
    dias = p['dias_ejercicio']
    nivel = 0 if dias == 1 else 1 if dias == 2 else 2
    prob = {'aerobico': (0.05, 0.25, 0.75), 'bajo_impacto': (0.15, 0.55, 0.70),
            'fuerza': (0.02, 0.15, 0.45)}
    fila = {'dias_ejercicio_semana': dias}
    for tipo, probs in prob.items():
        si = rng.random() < probs[nivel]
        fila[f'realiza_{tipo}'] = 'SI' if si else 'NO'
        # Escala Nunca(1)…Siempre(5): coherente con los días de ejercicio.
        fila[f'frecuencia_{tipo}'] = escala(rng, 2 + 0.8 * (dias - 1), 0.7, 2, 5)
    fila['horas_sedentarismo'] = round(normal(rng, 6, 2.5, 1, 14))
    return fila


def seccion_conocimiento(rng, p):
    # Sin vínculo con el MRS: según la profesora esta sección no aumenta ni
    # disminuye los síntomas (reunión 20-10), así que tampoco depende de ellos.
    consulto = rng.random() < 0.30
    controla = (rng.random() < P.PROP_CONTROL_CRONICA if (p['med_presion'] or p['med_diabetes'])
                else rng.random() < P.PROP_CONTROL_OTRA)
    programa = (P.PROGRAMA_CRONICA if (p['med_presion'] or p['med_diabetes'])
                else rng.choice(P.PROGRAMAS_OTROS))
    conoce = elegir(rng, P.CONOCE_SISTEMA)
    nivel = dict(P.NIVEL_INFORMACION)
    if conoce == 'SI':                          # quien conoce el sistema se siente más informada
        nivel = {k: v * (0.6 if k <= 2 else 1.6) for k, v in nivel.items()}
    dificultades = dict(P.PRINCIPALES_DIFICULTADES)
    if p['trabaja']:
        dificultades['Horarios incompatibles'] *= 1.4
    apoyo = dict(P.TIPO_APOYO)
    if not p['trabaja']:
        apoyo.pop('Apoyo laboral')
    return {
        'prevision': p['prevision'],
        'conoce_sistema_publico_climaterio': conoce,
        'ha_escuchado_programa_climaterio': elegir(rng, P.ESCUCHO_PROGRAMA),
        'sabe_donde_acudir': elegir(rng, P.SABE_DONDE),
        'ha_consultado_por_sintomas': 'SI' if consulto else elegir(rng, {'NO': 0.95, 'NS': 0.05}),
        'evaluacion_atencion_recibida': elegir(rng, P.EVALUACION_ATENCION),
        'en_control_programa_consultorio': 'SI' if controla else 'NO',
        'en_control_programa_cual': programa,
        'considera_informacion_suficiente': elegir(rng, P.INFORMACION_SUFICIENTE),
        'nivel_informacion_servicios': elegir(rng, nivel),
        'conoce_recursos_disponibles': elegir(rng, P.CONOCE_RECURSOS),
        'ha_tenido_dificultades_acceso': elegir(rng, P.DIFICULTADES_ACCESO),
        'principales_dificultades': ', '.join(multiseleccion(rng, dificultades)),
        'principales_dificultades_otra': rng.choice(P.OTRA_DIFICULTAD),
        'sintomas_tomados_en_serio': elegir(rng, P.SINTOMAS_EN_SERIO),
        'desea_mas_informacion_apoyo': 'SI' if rng.random() < P.PROP_DESEA_APOYO else 'NO',
        'tipo_informacion_apoyo_deseado': ', '.join(multiseleccion(rng, apoyo)),
        'tipo_informacion_apoyo_otro': rng.choice(P.OTRO_APOYO),
    }


def seccion_satisfaccion(rng):
    """Encuesta de satisfacción: opcional, se responde con un botón al final."""
    if rng.random() >= P.PROP_RESPONDE_SATISFACCION:
        return None
    incomoda = rng.random() < P.PROP_INCOMODIDAD
    return {
        'facilidad_uso': elegir(rng, P.FACILIDAD),
        'fatiga_mental': elegir(rng, P.FATIGA),
        'comodidad_diseno': elegir(rng, P.COMODIDAD),
        'recomendaria': elegir(rng, P.RECOMENDARIA),
        'incomodidad': 'SI' if incomoda else 'NO',
        'comentario_incomodidad': rng.choice(P.COMENTARIOS_INCOMODIDAD) if incomoda else None,
    }


# --- Visibilidad y blancos --------------------------------------------------------
def _cumple(valor, operador, esperado, fecha):
    if valor in (None, ''):
        return False
    if operador == 'igual':
        return valor == esperado
    if operador == 'en':
        return valor in esperado
    if operador == 'contiene':
        return esperado in [v.strip() for v in str(valor).split(',')]
    if operador == 'meses_lt':
        meses = meses_desde_texto(valor, fecha)
        return meses is not None and meses < esperado
    raise ValueError(operador)


def aplicar_visibilidad(respuestas, rol, fecha):
    """Borra lo que la encuesta no mostraría. `respuestas` = {campo: valor} de una ronda."""
    if rol != 'PROFESIONAL':
        for campo in SOLO_PROFESIONAL:
            respuestas.pop(campo, None)
    # Varias pasadas: un campo oculto puede ocultar a sus dependientes.
    cambio = True
    while cambio:
        cambio = False
        for campo, (madre, op, esperado) in CONDICIONES.items():
            if campo in respuestas and not _cumple(respuestas.get(madre), op, esperado, fecha):
                del respuestas[campo]
                cambio = True


def aplicar_blancos(rng, respuestas, rol):
    for campo in list(respuestas):
        if campo not in OBLIGATORIOS[rol] and rng.random() < P.PROP_BLANCOS:
            respuestas[campo] = None


# --- Ronda 2 -----------------------------------------------------------------------
def evolucionar(rng, p, items, fecha2):
    """Cambios leves entre rondas (§1): síntomas ±1, peso, hábitos, terapia."""
    p['edad'] = edad_en(p['nacimiento'], fecha2)
    if not p['terapia_hormonal'] and p['etapa'] != 'pre' and rng.random() < P.PROP_INICIA_TERAPIA:
        p['terapia_hormonal'] = True
    if p['etapa'] == 'peri' and meses_entre(p['fum'], fecha2) >= 12:
        p['etapa'] = 'post'
    nuevos = {}
    for i, v in items.items():
        if rng.random() < P.PROP_CAMBIO_ITEM_MRS:
            baja = 0.55 if (p['terapia_hormonal'] or p['activa']) else 0.45
            v += -1 if rng.random() < baja else 1
        nuevos[i] = min(4, max(0, v))
    p['peso'] = max(35, p['peso'] + normal(rng, 0, 1.2, -2, 2))
    return nuevos


def variar_habitos(rng, fila):
    for campo, v in fila.items():
        if isinstance(v, int) and campo != 'tabaco_frecuencia' and rng.random() < P.PROP_CAMBIO_HABITO:
            fila[campo] = min(5, max(1, v + rng.choice((-1, 1))))
    return fila


# --- Orquestación -------------------------------------------------------------------
def generar(rng, n=P.N_PARTICIPANTES, n_ronda2=P.N_RONDA2, blancos=True):
    """
    Devuelve (participantes, encuestas). `participantes` es una lista de dicts
    con la persona y sus variables ocultas; `encuestas` es una lista de dicts
    {participante, ronda, fecha, rol, secciones: {seccion: fila | None}, mrs}.

    Con `blancos=False` las respuestas quedan completas: las omisiones las
    agrega después simulacion/ensuciar.py, que además las registra.
    """
    ultimo_dia_r1 = min(P.FECHA_FIN_RONDA1, P.FECHA_CORTE)
    personas, encuestas = [], []
    ruts = set()
    for k in range(1, n + 1):
        p = {'id': f'SIM-{k:03d}'}
        fecha1 = fecha_azar(rng, P.FECHA_INICIO_RONDA1, ultimo_dia_r1)
        p['fecha_ronda1'] = fecha1
        p['aplicada_por'] = 'PROFESIONAL' if rng.random() < P.PROP_PROFESIONAL else 'USUARIA'
        generar_perfil(rng, p, fecha1)
        generar_etapa(rng, p, fecha1)
        generar_salud(rng, p)
        generar_estilo(rng, p)
        generar_cuidado(rng, p)
        generar_latentes_mrs(rng, p)
        p['tiene_pareja'] = 'SI' if rng.random() < P.PROP_TIENE_PAREJA else 'NO'

        # RUT ficticio acorde a la edad (números más bajos = personas mayores).
        while True:
            numero = rng.randint(6_000_000, 9_500_000) + (60 - p['edad']) * 150_000
            if numero not in ruts:
                ruts.add(numero)
                break
        p['rut'] = rut_valido(numero)
        p['email'] = f'sim{k:03d}@example.com'
        personas.append(p)

    # Ronda 2: entre quienes alcanzan a cumplir el plazo antes de la fecha de corte.
    ultimo_r1_valido = P.FECHA_CORTE - timedelta(days=P.DIAS_ENTRE_RONDAS)
    elegibles = [p for p in personas if p['fecha_ronda1'] <= ultimo_r1_valido]
    con_ronda2 = {p['id'] for p in rng.sample(elegibles, min(n_ronda2, len(elegibles)))}

    for p in personas:
        items = None
        rondas = [1, 2] if p['id'] in con_ronda2 else [1]
        for ronda in rondas:
            if ronda == 1:
                fecha = p['fecha_ronda1']
                items = calcular_mrs(rng, p)
            else:
                desde = p['fecha_ronda1'] + timedelta(days=P.DIAS_ENTRE_RONDAS)
                hasta = min(P.FECHA_CORTE, p['fecha_ronda1'] + timedelta(days=P.MAX_DIAS_ENTRE_RONDAS))
                fecha = fecha_azar(rng, desde, hasta)
                p['fecha_ronda2'] = fecha
                items = evolucionar(rng, p, items, fecha)
            mrs = puntajes_mrs(items)
            secciones = {
                'trabajo': seccion_trabajo(rng, p, mrs),
                'tareas_cuidado': seccion_cuidado(rng, p),
                'mrs': seccion_mrs(rng, p, items, mrs),
                'empa': seccion_empa(rng, p, fecha),
                'habitos_de_vida': seccion_habitos(rng, p),
                'actividad_fisica': seccion_actividad(rng, p),
                'conocimiento_sistema': seccion_conocimiento(rng, p),
                'satisfaccion': seccion_satisfaccion(rng),
            }
            if ronda == 2:
                previa = encuestas[-1]['secciones']
                # La ronda 2 conserva lo estable y varía levemente los hábitos.
                secciones['habitos_de_vida'] = variar_habitos(rng, dict(previa['habitos_de_vida']))
                for campo in ('colesterol_total_mg_dl', 'colesterol_hdl_mg_dl', 'trigliceridos_mg_dl',
                              'glicemia_mg_dl', 'vdrl_rpr', 'fecha_ultimo_pap', 'resultado_pap',
                              'fecha_mamografia', 'resultado_birads', 'fecha_ecotomografia_mamaria',
                              'fecha_ultimo_empa', 'talla_actual_cm', 'talla_maxima_cm'):
                    if campo in previa['empa']:
                        secciones['empa'][campo] = previa['empa'][campo]
            if ronda == 1:
                secciones['identificacion'] = seccion_identificacion(p)
            encuestas.append({'participante': p['id'], 'ronda': ronda, 'fecha': fecha,
                              'rol': p['aplicada_por'], 'secciones': secciones, 'mrs': mrs,
                              'etapa': p['etapa']})

    # Visibilidad y blancos sobre todas las encuestas.
    for e in encuestas:
        for nombre, fila in e['secciones'].items():
            if fila is None:
                continue
            if blancos:
                aplicar_blancos(rng, fila, e['rol'])
            aplicar_visibilidad(fila, e['rol'], e['fecha'])
        ident = e['secciones'].get('identificacion')
        # Si "¿trabaja?" quedó en blanco, la sección Trabajo no se muestra.
        if ident is not None and ident.get('trabaja_actualmente') is None:
            e['secciones']['trabajo'] = None
    # La sección Trabajo de la ronda 2 sigue a la identificación de la ronda 1.
    sin_trabajo = {e['participante'] for e in encuestas
                   if e['ronda'] == 1 and e['secciones']['trabajo'] is None}
    for e in encuestas:
        if e['participante'] in sin_trabajo:
            e['secciones']['trabajo'] = None
    return personas, encuestas
