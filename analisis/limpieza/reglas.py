"""
Reglas de limpieza (Fase 32 — OB1, Actividad 2).

Cada paso recibe el DataFrame (todo como texto o NA), lo corrige y anota en
la bitácora cuántas celdas cambió y por qué; con eso se arma el informe.
Los pasos se aplican en el orden de `limpiar()` y el orden importa: primero se
normaliza el formato, después se validan códigos y rangos, después se aplica
la lógica condicional (que necesita los códigos ya normalizados) y al final se
imputa lo que de verdad falta.
"""
import re
import unicodedata
from collections import Counter
from datetime import date

import numpy as np
import pandas as pd

from . import catalogo

# --- Parámetros de la limpieza ------------------------------------------------

EDAD_MINIMA, EDAD_MAXIMA = 40, 65          # forms.IdentificacionForm.EDAD_*
EDAD_PLAUSIBLE = (18, 100)                 # fuera de esto la fecha de nacimiento está mal

UMBRAL_IMPUTAR = 5.0                       # % faltante: < 5 → se imputa
UMBRAL_EXCLUIR = 30.0                      # 5-30 → se imputa y se marca; > 30 → no se modela

# Textos que significan "sin dato" en cualquier columna.
CENTINELAS_TEXTO = {'N/A', 'NA', 'N A', 'SIN DATO', '-', 'NO RECUERDO', 'NO SABE NO RESPONDE',
                    'NULL', 'NONE', 'NAN'}
# Números que significan "sin dato" en preguntas con opciones (escalas, códigos).
CENTINELAS_CODIGO = {-1, 99, 999, 9999}
# En mediciones continuas, -1/999/9999 también son centinelas (99 no: 99 kg es un peso real).
CENTINELAS_MEDICION = {-1, 999, 9999}

# Rangos plausibles de las mediciones (fuera de rango → vacío).
RANGOS = {
    'talla_actual_cm': (120, 200), 'talla_maxima_cm': (120, 200),
    'peso_kg': (30, 200), 'circunferencia_cintura_cm': (50, 170),
    'presion_sistolica': (70, 250), 'presion_diastolica': (40, 150),
    'colesterol_total_mg_dl': (80, 500), 'colesterol_hdl_mg_dl': (15, 150),
    'trigliceridos_mg_dl': (20, 1500), 'glicemia_mg_dl': (40, 600),
    'horas_sedentarismo': (0, 24),
}
CAMPOS_ENTEROS = {'talla_actual_cm', 'talla_maxima_cm', 'presion_sistolica', 'presion_diastolica',
                  'colesterol_total_mg_dl', 'colesterol_hdl_mg_dl', 'trigliceridos_mg_dl',
                  'glicemia_mg_dl', 'horas_sedentarismo'}

FECHAS = ['fecha_nacimiento', 'fecha_ultimo_empa', 'fecha_ultimo_pap', 'fecha_mamografia',
          'fecha_ecotomografia_mamaria']

MRS_ITEMS = [f'pregunta_{i}' for i in range(1, 12)]
# Orden de ítems del proyecto (no es el de Heinemann): ver models.MRS.
MRS_SUBESCALAS = {
    'mrs_somatico': ['pregunta_1', 'pregunta_2', 'pregunta_3', 'pregunta_4'],
    'mrs_psicologico': ['pregunta_5', 'pregunta_6', 'pregunta_7', 'pregunta_8'],
    'mrs_urogenital': ['pregunta_9', 'pregunta_10', 'pregunta_11'],
}

SATISFACCION = ['facilidad_uso', 'fatiga_mental', 'comodidad_diseno', 'recomendaria', 'incomodidad']
TRABAJO = ['rendimiento_afectado', 'bienestar_trabajo_afectado', 'frecuencia_ausencias',
           'lugar_trabajo_comprensivo', 'estres_entorno_laboral']

# Columnas que no son respuestas (metadatos del sistema): no se validan ni imputan.
METADATOS = ['participante_id', 'uuid_local', 'rut_hash', 'usuario_id', 'ronda', 'sincronizado_en',
             'creado_en', 'ronda_actual', 'ultima_finalizacion_en', 'fecha_evaluacion',
             'fecha_registro', 'origen_registro']

# Reglas propias del análisis, que la plataforma no aplica pero el dataset sí respeta:
# "¿cambió su relación de pareja…?" no tiene sentido sin pareja (los 170 vacíos
# del dataset coinciden con tiene_pareja = NO).
REGLAS_ADICIONALES = {
    'cambio_relacion_pareja_menopausia': {'campo': 'tiene_pareja', 'valor': 'SI'},
}

SINONIMOS = {
    'genero': {'MUJER': 'F', 'FEMENINA': 'F'},
}
# Abreviaturas y grafías alternativas de comunas → nombre oficial (datos_geograficos.py).
COMUNAS_ALIAS = {'SERENA': 'La Serena', 'P. ALTO': 'Puente Alto', 'PTE. ALTO': 'Puente Alto',
                 'COYHAIQUE': 'Coihaique', 'STGO': 'Santiago', 'STGO.': 'Santiago'}
SI = {'SI', 'S', 'YES', 'Y', 'TRUE', 'VERDADERO', '1'}
NO = {'NO', 'N', 'FALSE', 'FALSO', '0'}
NS = {'NS', 'NO SABE', 'NO SE'}

MESES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7,
         'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10, 'noviembre': 11,
         'diciembre': 12}


# --- Utilidades ---------------------------------------------------------------

def plano(texto):
    """Mayúsculas, sin tildes y sin espacios repetidos: para comparar textos."""
    t = unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', t).strip().upper()


def a_numero(valor):
    """'81.0 kg' → 81.0; '53,0' → 53.0; texto no numérico → None."""
    if pd.isna(valor):
        return None
    t = re.sub(r'\s*(kg|cm|mmhg|mg/dl)\s*$', '', str(valor).strip(), flags=re.I).replace(',', '.')
    try:
        return float(t)
    except ValueError:
        return None


def leer_fecha(texto):
    """ISO (AAAA-MM-DD), DD/MM/AAAA o DD-MM-AAAA → date; otra cosa → None."""
    if pd.isna(texto):
        return None
    t = str(texto).strip()
    for patron, orden in ((r'(\d{4})-(\d{1,2})-(\d{1,2})', 'amd'),
                          (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dma')):
        m = re.fullmatch(patron, t)
        if m:
            p = [int(x) for x in m.groups()]
            a, mes, d = (p[0], p[1], p[2]) if orden == 'amd' else (p[2], p[1], p[0])
            try:
                return date(a, mes, d)
            except ValueError:
                return None
    return None


def leer_fum(texto, evaluacion):
    """
    Fecha de la última menstruación (texto libre) → (año, mes o None).
    Acepta los formatos de models.meses_desde_texto_fecha y además 'julio 2021'
    y 'hace N años' (relativo a la fecha de evaluación).
    """
    if pd.isna(texto):
        return None
    t = str(texto).strip().lower()
    m = re.fullmatch(r'(\d{4})', t)
    if m:
        return int(m.group(1)), None
    m = re.fullmatch(r'(\d{4})[-/](\d{1,2})', t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r'(\d{1,2})[-/](\d{4})', t)
    if m:
        return int(m.group(2)), int(m.group(1))
    f = leer_fecha(t)
    if f:
        return f.year, f.month
    m = re.fullmatch(r'([a-záéíóú]+)\s+(?:de\s+)?(\d{4})', t)
    if m and m.group(1) in MESES:
        return int(m.group(2)), MESES[m.group(1)]
    m = re.fullmatch(r'hace\s+(\d{1,2})\s+años?', plano(t).lower())
    if m and evaluacion:
        return evaluacion.year - int(m.group(1)), None
    return None


def meses_entre(anio, mes, ref):
    """Igual que models.meses_desde_texto_fecha, pero contra la fecha de evaluación."""
    return (ref.year - anio) * 12 + (ref.month - (mes or 7))


class Bitacora:
    """Conteo de correcciones: (paso, columna, motivo) → n."""

    def __init__(self):
        self.conteo = Counter()
        self.ejemplos = {}
        self.notas = []

    def anotar(self, paso, columna, motivo, n=1, ejemplo=None):
        if n:
            self.conteo[(paso, columna, motivo)] += n
            if ejemplo is not None:
                self.ejemplos.setdefault((paso, columna, motivo), set()).add(str(ejemplo))


# --- Pasos --------------------------------------------------------------------

def p1_formato(df, bit):
    """Quita espacios sobrantes y convierte cadenas vacías en NA."""
    for c in df.columns:
        antes = df[c].copy()
        df[c] = df[c].str.strip().str.replace(r'\s+', ' ', regex=True)
        df.loc[df[c] == '', c] = pd.NA
        cambios = (antes.fillna('') != df[c].fillna('')) & df[c].notna()
        bit.anotar('1 formato', c, 'espacios sobrantes', int(cambios.sum()))
    return df


def p2_duplicados(df, bit):
    """Filas idénticas (salvo el id) y RUT repetidos: queda la más reciente."""
    columnas = [c for c in df.columns if c != 'participante_id']
    dup = df.duplicated(subset=columnas, keep='first')
    bit.anotar('2 duplicados', '(fila)', 'fila idéntica a otra', int(dup.sum()))
    eliminadas = df[dup].assign(motivo_exclusion='duplicado exacto')
    df = df[~dup]

    orden = df.sort_values('sincronizado_en')
    repetido = orden.duplicated(subset=['rut_hash'], keep='last')
    bit.anotar('2 duplicados', '(fila)', 'mismo RUT, ficha más antigua', int(repetido.sum()))
    eliminadas = pd.concat([eliminadas,
                            orden[repetido].assign(motivo_exclusion='RUT repetido (versión antigua)')])
    df = df.drop(index=orden[repetido].index)
    return df, eliminadas


def p3_centinelas(df, bit, campos):
    for c in df.columns:
        if c in METADATOS or c == 'region_residencia':     # '99' es un código válido de región
            continue
        es_texto = df[c].map(lambda v: pd.notna(v) and plano(v) in CENTINELAS_TEXTO)
        bit.anotar('3 centinelas', c, 'texto "sin dato"', int(es_texto.sum()),
                   ejemplo=', '.join(sorted(set(df.loc[es_texto, c]))) or None)
        df.loc[es_texto, c] = pd.NA

        info = campos.get(c, {})
        if info.get('opciones') or c in RANGOS:
            numeros = CENTINELAS_CODIGO if info.get('opciones') else CENTINELAS_MEDICION
            es_num = df[c].map(lambda v: a_numero(v) in numeros)
            # Excepción: 99 es legítimo donde el modelo lo admite como opción.
            if info.get('opciones') and 99 in info['opciones']:
                es_num &= df[c].map(lambda v: a_numero(v) != 99)
            bit.anotar('3 centinelas', c, 'número "sin dato" (-1/99/999/9999)', int(es_num.sum()),
                       ejemplo=', '.join(sorted(set(df.loc[es_num, c]))) or None)
            df.loc[es_num, c] = pd.NA
    return df


def _normalizar_opcion(valor, opciones, sinonimos):
    """Devuelve el código válido equivalente a `valor`, o None si no calza."""
    if isinstance(next(iter(opciones)), int):
        n = a_numero(valor)
        return str(int(n)) if n is not None and n == int(n) and int(n) in opciones else None
    p = plano(valor)
    if p in sinonimos:
        return sinonimos[p]
    if set(opciones) <= {'SI', 'NO', 'NS'}:
        if p in SI:
            return 'SI'
        if p in NO:
            return 'NO'
        if p in NS and 'NS' in opciones:
            return 'NS'
        return None
    for codigo, etiqueta in opciones.items():
        if p == plano(codigo) or p == plano(etiqueta):
            return codigo
    return None


def p4_codigos(df, bit, campos, comunas):
    for c in df.columns:
        info = campos.get(c)
        if c in METADATOS or not info:
            continue
        if info['tipo'] == 'BooleanField':
            nuevos = df[c].map(lambda v: v if pd.isna(v) else
                               ('True' if plano(v) in SI else 'False' if plano(v) in NO else None))
        elif c == 'region_residencia':
            # '4' → '04'; nombre de región → código.
            def region(v):
                if pd.isna(v):
                    return v
                if re.fullmatch(r'\d{1,2}', v):
                    v = v.zfill(2)
                return _normalizar_opcion(v, info['opciones'], {})
            nuevos = df[c].map(region)
        elif info['opciones']:
            sin = SINONIMOS.get(c, {})
            nuevos = df[c].map(lambda v: v if pd.isna(v) else _normalizar_opcion(v, info['opciones'], sin))
        else:
            continue
        nuevos = nuevos.astype(object)
        invalido = df[c].notna() & nuevos.isna()
        # '2.0' → '2' es solo formato: no se cuenta como recodificación.
        recodificado = pd.Series([pd.notna(a) and pd.notna(b) and a != b
                                  and not (a_numero(a) is not None and a_numero(a) == a_numero(b))
                                  for a, b in zip(df[c], nuevos)], index=df.index)
        bit.anotar('4 códigos', c, 'recodificado al código del sistema', int(recodificado.sum()),
                   ejemplo=', '.join(sorted(set(df.loc[recodificado, c]))[:8]) or None)
        bit.anotar('4 códigos', c, 'valor fuera de las opciones → vacío', int(invalido.sum()),
                   ejemplo=', '.join(sorted(set(df.loc[invalido, c]))[:8]) or None)
        df[c] = nuevos.map(lambda v: pd.NA if v is None or pd.isna(v) else str(v))

    # Comuna: ortografía oficial y región deducida si faltaba.
    oficial = {plano(com): (com, reg) for reg, lista in comunas.items() for com in lista}
    oficial.update({alias: oficial[plano(com)] for alias, com in COMUNAS_ALIAS.items()})
    canon = df['comuna'].map(lambda v: oficial.get(plano(v), (None, None))[0] if pd.notna(v) else None)
    cambia = canon.notna() & (canon != df['comuna'])
    bit.anotar('4 códigos', 'comuna', 'ortografía oficial', int(cambia.sum()))
    df.loc[cambia, 'comuna'] = canon[cambia]
    reg_comuna = df['comuna'].map(lambda v: oficial.get(plano(v), (None, None))[1] if pd.notna(v) else None)
    deducir = df['region_residencia'].isna() & reg_comuna.notna()
    bit.anotar('4 códigos', 'region_residencia', 'deducida desde la comuna', int(deducir.sum()))
    df.loc[deducir, 'region_residencia'] = reg_comuna[deducir]
    incoherente = reg_comuna.notna() & df['region_residencia'].notna() & (reg_comuna != df['region_residencia'])
    if incoherente.any():
        ids = ', '.join(df.loc[incoherente, 'participante_id'])
        bit.notas.append(f'{int(incoherente.sum())} filas con comuna que no pertenece a la región '
                         f'declarada (participante_id {ids}); se dejaron como venían porque no se '
                         'sabe cuál de los dos datos está mal.')
    return df


def p5_mediciones(df, bit):
    for c, (minimo, maximo) in RANGOS.items():
        numeros = df[c].map(a_numero)
        texto_con_unidad = df[c].notna() & numeros.notna() & df[c].str.contains(r'[a-zA-Z,]', regex=True, na=False)
        bit.anotar('5 mediciones', c, 'unidad o coma decimal quitada', int(texto_con_unidad.sum()),
                   ejemplo=', '.join(sorted(set(df.loc[texto_con_unidad, c]))[:6]) or None)
        no_numero = df[c].notna() & numeros.isna()
        bit.anotar('5 mediciones', c, 'texto no numérico → vacío', int(no_numero.sum()),
                   ejemplo=', '.join(sorted(set(df.loc[no_numero, c]))) or None)

        if c.startswith('talla'):          # 1.56 → 156: venía en metros
            metros = numeros.between(1.2, 2.2)
            bit.anotar('5 mediciones', c, 'metros → centímetros (×100)', int(metros.sum()),
                       ejemplo=', '.join(str(v) for v in sorted(set(numeros[metros]))) or None)
            numeros = numeros.where(~metros, numeros * 100)
        if c.startswith('presion'):        # 12/8 → 120/80: venía en cmHg
            limite = 30 if c == 'presion_sistolica' else 20
            cmhg = numeros.between(4, limite, inclusive='left')
            bit.anotar('5 mediciones', c, 'cmHg → mmHg (×10)', int(cmhg.sum()),
                       ejemplo=', '.join(str(v) for v in sorted(set(numeros[cmhg]))) or None)
            numeros = numeros.where(~cmhg, numeros * 10)

        fuera = numeros.notna() & ~numeros.between(minimo, maximo)
        bit.anotar('5 mediciones', c, f'fuera del rango plausible {minimo}-{maximo} → vacío',
                   int(fuera.sum()),
                   ejemplo=', '.join(str(v) for v in sorted(set(numeros[fuera]))) or None)
        numeros = numeros.where(~fuera)
        if c in CAMPOS_ENTEROS:
            numeros = numeros.round()
        df[c] = numeros.map(lambda v: pd.NA if pd.isna(v) else
                            (str(int(v)) if c in CAMPOS_ENTEROS else f'{v:g}'))

    # Diastólica mayor o igual a la sistólica: medición imposible, se borran ambas.
    pas, pad = df['presion_sistolica'].map(a_numero), df['presion_diastolica'].map(a_numero)
    imposible = pas.notna() & pad.notna() & (pad >= pas)
    bit.anotar('5 mediciones', 'presion_*', 'diastólica ≥ sistólica → ambas vacías', int(imposible.sum()))
    df.loc[imposible, ['presion_sistolica', 'presion_diastolica']] = pd.NA

    # Cintura incoherente con el IMC (Fase 34): la cintura sigue de cerca al IMC
    # (r ≈ 0,9). Si el residuo robusto de la recta cintura ~ IMC supera
    # ±Z_CINTURA desviaciones (MAD), la medición se considera errónea → vacía
    # (se imputa en el paso 9 desde el IMC).
    incoherente = cintura_incoherente(df)
    bit.anotar('5 mediciones', 'circunferencia_cintura_cm',
               f'incoherente con el IMC (|z robusto| > {Z_CINTURA:g}) → vacía', int(incoherente.sum()),
               ejemplo=', '.join(f'{c} cm con IMC {i:.1f}' for c, i in
                                 zip(df.loc[incoherente, 'circunferencia_cintura_cm'],
                                     _imc(df)[incoherente])) or None)
    df.loc[incoherente, 'circunferencia_cintura_cm'] = pd.NA
    return df


Z_CINTURA = 4.0


def _imc(df):
    peso, talla = df['peso_kg'].map(a_numero), df['talla_actual_cm'].map(a_numero)
    return peso / (talla / 100) ** 2


def recta_cintura(df, imc_desde_cintura=False):
    """
    Recta cintura = a + b·IMC (o IMC = a + b·cintura) ajustada con las filas que
    tienen ambos datos. Se ajusta en la dirección en que se va a predecir: invertir
    la otra recta exagera los extremos.
    """
    imc, cintura = _imc(df), df['circunferencia_cintura_cm'].map(a_numero)
    ok = imc.notna() & cintura.notna()
    x, y = (cintura, imc) if imc_desde_cintura else (imc, cintura)
    b, a = np.polyfit(x[ok].astype(float), y[ok].astype(float), 1)
    return a, b


def cintura_incoherente(df):
    """Filas cuya cintura se aleja más de Z_CINTURA desviaciones robustas de la recta."""
    a, b = recta_cintura(df)
    imc, cintura = _imc(df), df['circunferencia_cintura_cm'].map(a_numero)
    residuo = cintura - (a + b * imc)
    r = residuo.dropna()
    mad = 1.4826 * (r - r.median()).abs().median()
    return (residuo.abs() / mad > Z_CINTURA).fillna(False)


def p6_fechas(df, bit):
    evaluacion = df['fecha_evaluacion'].map(leer_fecha)
    for c in FECHAS:
        fechas = df[c].map(leer_fecha)
        ilegible = df[c].notna() & fechas.isna()
        bit.anotar('6 fechas', c, 'fecha ilegible → vacío', int(ilegible.sum()),
                   ejemplo=', '.join(sorted(set(df.loc[ilegible, c]))) or None)
        reformateada = df[c].notna() & fechas.notna() & (df[c] != fechas.map(lambda f: f and f.isoformat()))
        bit.anotar('6 fechas', c, 'formato DD/MM/AAAA → AAAA-MM-DD', int(reformateada.sum()))
        futura = pd.Series([bool(f and e and f > e) for f, e in zip(fechas, evaluacion)], index=df.index)
        bit.anotar('6 fechas', c, 'posterior a la evaluación → vacío', int(futura.sum()))
        fechas = fechas.where(~futura)
        df[c] = fechas.map(lambda f: pd.NA if f is None or pd.isna(f) else f.isoformat())

    # Última menstruación: texto libre → 'AAAA-MM' o 'AAAA'.
    c = 'fecha_ultima_menstruacion'
    nacimiento = df['fecha_nacimiento'].map(leer_fecha)
    nuevos, motivos = [], Counter()
    for valor, ev, nac in zip(df[c], evaluacion, nacimiento):
        if pd.isna(valor):
            nuevos.append(pd.NA)
            continue
        fum = leer_fum(valor, ev)
        if fum is None:
            motivos['texto ilegible → vacío'] += 1
            nuevos.append(pd.NA)
            continue
        anio, mes = fum
        if ev and meses_entre(anio, mes, ev) < 0 and not (mes is None and anio == ev.year):
            motivos['posterior a la evaluación → vacío'] += 1
            nuevos.append(pd.NA)
            continue
        if nac and anio < nac.year + 8:
            motivos['anterior a los 8 años de edad → vacío'] += 1
            nuevos.append(pd.NA)
            continue
        texto = f'{anio}-{mes:02d}' if mes else str(anio)
        if texto != valor:
            motivos['normalizada a AAAA-MM / AAAA'] += 1
        nuevos.append(texto)
    for motivo, n in motivos.items():
        bit.anotar('6 fechas', c, motivo, n)
    df[c] = nuevos
    return df


def p7_elegibilidad(df, bit):
    """Edad a la fecha de evaluación y criterio de inclusión del sistema."""
    df = df.copy()                        # evita el aviso de DataFrame fragmentado
    evaluacion = df['fecha_evaluacion'].map(leer_fecha)
    nacimiento = df['fecha_nacimiento'].map(leer_fecha)
    edad = pd.Series([
        (e.year - n.year - ((e.month, e.day) < (n.month, n.day))) if e and n else np.nan
        for e, n in zip(evaluacion, nacimiento)], index=df.index)

    motivo = pd.Series(pd.NA, index=df.index, dtype=object)
    no_verificable = edad.isna() | ~edad.between(*EDAD_PLAUSIBLE)
    motivo[no_verificable] = 'edad no verificable (fecha de nacimiento imposible)'
    motivo[motivo.isna() & (edad > EDAD_MAXIMA)] = f'mayor de {EDAD_MAXIMA} años'
    motivo[motivo.isna() & (edad < EDAD_MINIMA) & (df['excepcion_edad'].fillna('NINGUNA') == 'NINGUNA')] = \
        f'menor de {EDAD_MINIMA} sin excepción de edad'
    for m, n in motivo.value_counts().items():
        bit.anotar('7 elegibilidad', '(fila)', m, int(n))
    df['edad'] = edad.map(lambda v: pd.NA if pd.isna(v) else str(int(v)))
    excluidas = df[motivo.notna()].assign(motivo_exclusion=motivo[motivo.notna()])
    return df[motivo.isna()].copy(), excluidas


def _cumple(regla, fila, evaluacion):
    actual = fila.get(regla['campo'])
    op = regla.get('operador', 'igual')
    if op == 'meses_desde_lt':
        fum = leer_fum(actual, evaluacion) if pd.notna(actual) else None
        if fum is None:
            return True                       # fecha ilegible: la plataforma muestra la pregunta
        return meses_entre(*fum, evaluacion) < regla['valor']
    if pd.isna(actual):
        return False
    if op == 'contiene':
        return regla['valor'] in [x.strip() for x in str(actual).split(',')]
    return str(actual) == str(regla['valor'])


def p8_condicionales(df, bit, condicionales, secciones_cond, solo_profesional, campos):
    """
    Borra respuestas a preguntas que la encuesta no habría mostrado y marca
    esas celdas como "no aplica" (no son datos faltantes).
    """
    no_aplica = pd.DataFrame(False, index=df.index, columns=df.columns)
    reglas = {campo: regla for por_modelo in condicionales.values() for campo, regla in por_modelo.items()}
    reglas.update(REGLAS_ADICIONALES)

    # Sección Trabajo: solo si trabaja. Si "trabaja" vino vacío pero respondió la sección, se deduce.
    responde_trabajo = df[TRABAJO].notna().any(axis=1)
    deducir = df['trabaja_actualmente'].isna() & responde_trabajo
    bit.anotar('8 condicionales', 'trabaja_actualmente', 'vacío pero respondió Trabajo → True',
               int(deducir.sum()))
    df.loc[deducir, 'trabaja_actualmente'] = 'True'

    # Pregunta "madre" vacía pero con una dependiente respondida (Fase 34B): la
    # madre se perdió (centinela, omisión), pero la dependiente solo se muestra con
    # un valor, así que se deduce. Solo reglas de la plataforma con operador 'igual'.
    cambio = True
    while cambio:
        cambio = False
        for por_modelo in condicionales.values():
            for campo, regla in por_modelo.items():
                if regla.get('operador', 'igual') != 'igual':
                    continue
                madre = regla['campo']
                deducir = df[madre].isna() & df[campo].notna()
                if deducir.any():
                    bit.anotar('8 condicionales', madre,
                               f'vacía pero respondió {campo} → {regla["valor"]}', int(deducir.sum()))
                    df.loc[deducir, madre] = str(regla['valor'])
                    cambio = True
    regla_trabajo = secciones_cond['trabajo']
    oculta = df[regla_trabajo['campo']].fillna('') != str(regla_trabajo['valor'])
    for c in TRABAJO:
        borrar = oculta & df[c].notna()
        bit.anotar('8 condicionales', c, 'respondida sin trabajar → borrada', int(borrar.sum()))
        df.loc[oculta, c] = pd.NA
        no_aplica.loc[oculta, c] = True

    # Preguntas condicionales dentro de cada sección. Se repite hasta que nada
    # cambie para respetar el "ocultar en cadena" (Fase 26).
    evaluacion = df['fecha_evaluacion'].map(leer_fecha)
    cambio = True
    while cambio:
        cambio = False
        for campo, regla in reglas.items():
            visible = pd.Series([_cumple(regla, fila, ev) and not no_aplica.at[i, regla['campo']]
                                 for (i, fila), ev in zip(df.iterrows(), evaluacion)], index=df.index)
            nuevos = ~visible & ~no_aplica[campo]
            if nuevos.any():
                cambio = True
                borrar = nuevos & df[campo].notna()
                bit.anotar('8 condicionales', campo,
                           f'pregunta oculta (depende de {regla["campo"]}) → borrada', int(borrar.sum()))
                df.loc[nuevos, campo] = pd.NA
                no_aplica.loc[nuevos, campo] = True

    # Campos solo para personal de salud: no se muestran en encuestas autoaplicadas.
    auto = df['origen_registro'].fillna('') == 'AUTO'
    for c in sorted(solo_profesional):
        borrar = auto & df[c].notna()
        bit.anotar('8 condicionales', c, 'campo solo profesional en encuesta autoaplicada → borrado',
                   int(borrar.sum()))
        df.loc[auto, c] = pd.NA
        no_aplica.loc[auto, c] = True

    # Satisfacción: voluntaria; quien no la respondió no tiene datos faltantes.
    sin_satisf = df[SATISFACCION].isna().all(axis=1)
    no_aplica.loc[sin_satisf, SATISFACCION + ['comentario_incomodidad']] = True
    no_aplica.loc[df['incomodidad'].fillna('') != 'SI', 'comentario_incomodidad'] = True

    # Sin fecha de última menstruación no se sabe si las preguntas que dependen de
    # ella aplicaban (la plataforma las muestra, pero en posmenopausia no aplican).
    # Si vienen vacías quedan sin dato: imputar inventaría un sangrado (Fase 34B).
    no_imputar = pd.DataFrame(False, index=df.index, columns=df.columns)
    sin_fum = df['fecha_ultima_menstruacion'].isna()
    for campo, regla in reglas.items():
        if regla.get('operador') == 'meses_desde_lt':
            no_imputar.loc[sin_fum & df[campo].isna(), campo] = True

    # Combinaciones incoherentes que no se pueden corregir (no se sabe cuál dato
    # está mal): se marcan para revisarlas y se informan.
    tipos = ['realiza_aerobico', 'realiza_bajo_impacto', 'realiza_fuerza']
    sin_tipo = (df['dias_ejercicio_semana'].map(a_numero) >= 2) & df[tipos].eq('NO').all(axis=1)
    pildora_th = df['tipo_metodo_anticonceptivo'].eq('ORAL') & df['usa_terapia_hormonal'].eq('SI')
    for nombre, marca, texto in [
            ('incoherencia_ejercicio', sin_tipo, 'hacen ejercicio al menos 1 día pero no marcan ningún tipo'),
            ('incoherencia_pildora_th', pildora_th, 'usan píldora anticonceptiva y terapia hormonal a la vez')]:
        df[nombre] = marca.fillna(False).map(int)
        if marca.any():
            bit.notas.append(f'{int(marca.sum())} filas {texto}; se conservan y se marcan en `{nombre}` '
                             '(no se sabe cuál de los datos está mal).')
    return df, no_aplica, no_imputar


MULTISELECCION = ['principales_dificultades', 'tipo_informacion_apoyo_deseado', 'a_quien_cuida']


def _tipo_variable(c, campos):
    info = campos.get(c, {})
    if c in MULTISELECCION:
        return 'multiseleccion'
    if c in RANGOS:
        return 'continua'
    if info.get('tipo') == 'BooleanField':
        return 'categorica'
    if info.get('opciones'):
        return 'ordinal' if isinstance(next(iter(info['opciones'])), int) else 'categorica'
    return None


# Mediciones que se imputan desde una variable relacionada y no con la mediana
# (Fase 34): la mediana sola puede crear combinaciones imposibles, p. ej.
# sistólica imputada 120 junto a una diastólica real de 126, o un peso de 71 kg
# a una mujer de 1,75 m con 53 cm de cintura.
IMPUTACION_POR_RELACION = {'peso_kg', 'circunferencia_cintura_cm', 'presion_sistolica',
                           'presion_diastolica'}


def _imputar_por_relacion(df, c, faltante, aplica):
    """
    Imputa `c` en las filas `faltante` y devuelve la descripción del método.
      - peso: IMC estimado desde la cintura (recta IMC ~ cintura) × talla²;
        sin cintura, mediana.
      - cintura: recta cintura ~ IMC (paso 5); sin IMC, mediana.
      - presiones: la otra presión ± la mediana de la presión de pulso
        (sistólica − diastólica) de los pares medidos; sin ninguna, mediana.
    """
    obs = df.loc[aplica & df[c].notna(), c].map(a_numero)
    mediana = float(obs.median())
    if c == 'peso_kg':
        a, b = recta_cintura(df, imc_desde_cintura=True)
        talla = df['talla_actual_cm'].map(a_numero)
        imc = a + b * df['circunferencia_cintura_cm'].map(a_numero)
        estimado = (imc * (talla / 100) ** 2).round(1)
        metodo = f'IMC desde la cintura (IMC = {a:.1f} + {b:.3f}·cintura) × talla²; sin cintura, mediana {mediana:g}'
    elif c == 'circunferencia_cintura_cm':
        a, b = recta_cintura(df)
        estimado = (a + b * _imc(df)).round(1)
        metodo = f'recta cintura = {a:.1f} + {b:.2f}·IMC; sin IMC, mediana {mediana:g}'
    else:
        pas, pad = df['presion_sistolica'].map(a_numero), df['presion_diastolica'].map(a_numero)
        medidos = pas.notna() & pad.notna()
        if 'presion_sistolica_imputado' in df:          # al imputar la diastólica
            medidos &= df['presion_sistolica_imputado'] == 0
        pulso = float((pas - pad)[medidos].median())
        estimado = pad + pulso if c == 'presion_sistolica' else pas - pulso
        otra = 'diastólica +' if c == 'presion_sistolica' else 'sistólica −'
        metodo = f'{otra} presión de pulso mediana ({pulso:g}); sin la otra, mediana {mediana:g}'
    valores = estimado.where(estimado.notna(), mediana)
    if c in CAMPOS_ENTEROS:
        df.loc[faltante, c] = valores[faltante].map(lambda v: str(int(round(v))))
    else:
        df.loc[faltante, c] = valores[faltante].map(lambda v: f'{v:g}')
    return metodo


def p9_imputacion(df, bit, no_aplica, no_imputar, campos, solo_profesional):
    """
    Imputa solo los faltantes reales (vacíos que NO son "no aplica").
    El % se calcula sobre las filas donde la pregunta aplica.
    """
    filas = []
    for c in df.columns:
        tipo = _tipo_variable(c, campos)
        if c in METADATOS or tipo is None:
            continue
        aplica = ~no_aplica[c]
        todos = aplica & df[c].isna()
        faltante = todos & ~no_imputar[c]
        n_aplica, n_falta = int(aplica.sum()), int(todos.sum())
        n_sin_fum = n_falta - int(faltante.sum())
        pct = 100 * n_falta / n_aplica if n_aplica else 0.0
        ambito = ('subgrupo profesional' if c in solo_profesional else
                  'satisfacción' if c in SATISFACCION else 'general')

        if c in MRS_ITEMS:
            tratamiento = 'no se imputa (variable resultado)'
        elif tipo == 'multiseleccion':
            tratamiento = 'no se imputa (selección múltiple)'
        elif c in SATISFACCION:
            tratamiento = 'no se imputa (encuesta voluntaria, Fase 39)'
        elif n_falta == 0:
            tratamiento = 'sin faltantes'
        elif pct > UMBRAL_EXCLUIR:
            tratamiento = f'> {UMBRAL_EXCLUIR:g} %: no se modela'
        elif c in IMPUTACION_POR_RELACION:
            metodo = _imputar_por_relacion(df, c, faltante, aplica)
            bit.anotar('9 imputación', c, f'imputado por {metodo}', int(faltante.sum()))
            df[f'{c}_imputado'] = faltante.map(int)
            tratamiento = f'imputada ({metodo}) + marca {c}_imputado'
        else:
            valores = df.loc[aplica & df[c].notna(), c]
            if tipo == 'categorica':
                valor = valores.mode().sort_values().iloc[0]
                metodo = 'moda'
            else:
                numeros = valores.map(a_numero)
                if tipo == 'ordinal':
                    valor = str(int(np.percentile(numeros, 50, method='lower')))
                    metodo = 'mediana'
                else:
                    med = float(numeros.median())
                    valor = str(int(round(med))) if c in CAMPOS_ENTEROS else f'{med:g}'
                    metodo = 'mediana'
            df.loc[faltante, c] = valor
            bit.anotar('9 imputación', c, f'imputado con {metodo} ({valor})', int(faltante.sum()))
            if pct >= UMBRAL_IMPUTAR:
                df[f'{c}_imputado'] = faltante.map(int)
                tratamiento = f'imputada ({metodo} = {valor}) + marca {c}_imputado'
            else:
                tratamiento = f'imputada ({metodo} = {valor})'
        if n_sin_fum and tratamiento.startswith('imputada'):
            tratamiento += f'; {n_sin_fum} sin fecha de última menstruación quedan sin dato'
        filas.append({'variable': c, 'seccion': campos.get(c, {}).get('modelo', ''), 'tipo': tipo,
                      'ambito': ambito, 'filas_aplica': n_aplica, 'faltantes': n_falta,
                      'pct_faltante': round(pct, 1), 'tratamiento': tratamiento})
    return df, pd.DataFrame(filas)


def p10_derivadas(df, bit, severidad):
    num = {c: df[c].map(a_numero) for c in MRS_ITEMS}
    completo = pd.concat(num, axis=1).notna().all(axis=1)
    bit.anotar('10 derivadas', 'mrs_*', 'MRS incompleto: sin puntaje (fuera del análisis de severidad)',
               int((~completo).sum()))
    df['mrs_completo'] = completo.map(int)
    for sub, items in MRS_SUBESCALAS.items():
        df[sub] = pd.concat([num[i] for i in items], axis=1).sum(axis=1).where(completo).astype('Int64')
    df['mrs_total'] = pd.concat(num, axis=1).sum(axis=1).where(completo).astype('Int64')

    def categoria(total):
        if pd.isna(total):
            return pd.NA
        return next(nombre for maximo, nombre in severidad if total <= maximo)
    df['mrs_severidad'] = df['mrs_total'].map(categoria)

    edad = df['edad'].map(a_numero)
    df['tramo_edad'] = pd.cut(edad, [0, 39, 44, 49, 54, 59, 65],
                              labels=['<40', '40-44', '45-49', '50-54', '55-59', '60-65']).astype(object)

    # Etapa menopáusica (STRAW+10 simplificado, pendiente de validar con la profesora).
    evaluacion = df['fecha_evaluacion'].map(leer_fecha)
    meses, etapas = [], []
    for fum, ev, llega, ovario, utero in zip(df['fecha_ultima_menstruacion'], evaluacion,
                                             df['menstruacion_llega'], df['tiene_ovario'], df['tiene_utero']):
        f = leer_fum(fum, ev) if pd.notna(fum) else None
        m = meses_entre(*f, ev) if f else None
        meses.append(m)
        if ovario == 'NO':
            etapas.append('quirurgica')
        elif m is not None and m >= 12:
            etapas.append('posmenopausia')
        elif m is not None and llega == 'REGULAR':
            etapas.append('premenopausia')
        elif m is not None:
            etapas.append('perimenopausia')
        else:
            etapas.append('indeterminada' if utero != 'NO' else 'indeterminada (histerectomía)')
    df['meses_desde_fum'] = pd.Series(meses, index=df.index, dtype='Int64')
    df['etapa_menopausica'] = etapas

    peso, talla = df['peso_kg'].map(a_numero), df['talla_actual_cm'].map(a_numero)
    imc = (peso / (talla / 100) ** 2).round(1)
    df['imc'] = imc
    # Sin peso o talla el IMC no se imputa: queda como categoría "no informado"
    # (decisión de la Fase 34B; en el conjunto de la usuaria falta en ~45 %).
    df['imc_categoria'] = pd.cut(imc, [0, 18.5, 25, 30, 100], right=False,
                                 labels=['bajo peso', 'normal', 'sobrepeso', 'obesidad']).astype(object)
    df['imc_categoria'] = df['imc_categoria'].where(imc.notna(), 'no informado')
    perdida = df['talla_maxima_cm'].map(a_numero) - talla
    negativa = perdida < 0
    bit.anotar('10 derivadas', 'perdida_talla_cm', 'talla actual > talla máxima → sin dato',
               int(negativa.sum()))
    df['perdida_talla_cm'] = perdida.where(~negativa).astype('Int64')
    pas, pad = df['presion_sistolica'].map(a_numero), df['presion_diastolica'].map(a_numero)
    df['presion_elevada'] = ((pas >= 140) | (pad >= 90)).map(int).where(pas.notna() & pad.notna()).astype('Int64')
    df['doble_carga'] = ((df['trabaja_actualmente'] == 'True') & (df['cuida_otras_personas'] == 'SI')).map(int)
    return df


def limpiar(df):
    """Aplica todos los pasos. Devuelve (limpio, excluidas, diccionario, bitácora)."""
    campos, severidad = catalogo.leer_modelos()
    condicionales, secciones_cond = catalogo.leer_condicionales()
    solo_profesional = catalogo.leer_solo_profesional()
    comunas = catalogo.leer_comunas()
    bit = Bitacora()
    bit.filas_entrada = len(df)

    df = p1_formato(df, bit)
    df, duplicadas = p2_duplicados(df, bit)
    df = p3_centinelas(df, bit, campos)
    df = p4_codigos(df, bit, campos, comunas)
    df = p5_mediciones(df, bit)
    df = p6_fechas(df, bit)
    df, fuera = p7_elegibilidad(df, bit)
    df, no_aplica, no_imputar = p8_condicionales(df, bit, condicionales, secciones_cond,
                                                 solo_profesional, campos)
    df, diccionario = p9_imputacion(df, bit, no_aplica, no_imputar, campos, solo_profesional)
    df = p10_derivadas(df, bit, severidad)
    bit.severidad = severidad
    excluidas = pd.concat([duplicadas, fuera])
    return df, excluidas, diccionario, bit
