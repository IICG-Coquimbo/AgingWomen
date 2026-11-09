"""
Ensuciado del conjunto sintético (Fase 34A).

Recibe las filas limpias (una por encuesta, todas las celdas como texto) y
agrega errores como los que trae una exportación real de la plataforma: los
tipos del conjunto de la profesora y los patrones vistos en las respuestas
reales (P.SUCIEDAD). Cada cambio queda en la bitácora con el valor verdadero,
el valor sucio y el tipo de error, para poder evaluar después la limpieza.

Orden: omisiones (con su efecto en cascada) → errores de lógica → formatos →
valores imposibles → filas duplicadas. Con la misma semilla, el mismo resultado.
"""
import uuid
from datetime import date, timedelta

from . import parametros as P
from .generador import CONDICIONES, OBLIGATORIOS, _cumple

S = P.SUCIEDAD
META = ['participante_id', 'uuid_local', 'rut_hash', 'usuario_id', 'ronda', 'sincronizado_en',
        'creado_en', 'ronda_actual', 'ultima_finalizacion_en', 'fecha_evaluacion', 'fecha_registro',
        'origen_registro']
MRS_ITEMS = [f'pregunta_{i}' for i in range(1, 12)]
SATISFACCION = ['facilidad_uso', 'fatiga_mental', 'comodidad_diseno', 'recomendaria', 'incomodidad',
                'comentario_incomodidad']
TRABAJO = ['rendimiento_afectado', 'bienestar_trabajo_afectado', 'frecuencia_ausencias',
           'lugar_trabajo_comprensivo', 'estres_entorno_laboral']
# Campos con su propia tasa de omisión (patrón de las respuestas reales).
OMISION_PROPIA = {'peso_kg', 'talla_actual_cm', 'circunferencia_cintura_cm', 'fecha_ultimo_empa'}
NO_TOCAR = set(META) | set(OBLIGATORIOS['USUARIA'])

VARIANTES = {
    'SI': ['Sí', 'si', 'S', 'sí'], 'NO': ['No', 'no', 'N'], 'F': ['Femenino', 'FEMENINO', 'Mujer'],
    'True': ['verdadero', '1', 'TRUE'], 'False': ['falso', '0', 'FALSE'],
}
REGION_NOMBRE = ['Coquimbo', 'Región de Coquimbo', 'IV']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
         'octubre', 'noviembre', 'diciembre']
CENTINELA_NUMERO = ['-1', '99', '999', '9999']
CENTINELA_TEXTO = ['N/A', 'NA', 'sin dato', '-']
UNIDAD = {'peso_kg': 'kg', 'talla_actual_cm': 'cm', 'circunferencia_cintura_cm': 'cm'}


class Bitacora:
    def __init__(self):
        self.filas = []

    def cambiar(self, fila, columna, nuevo, tipo):
        if fila[columna] == nuevo:
            return
        self.filas.append({'participante_id': fila['participante_id'], 'uuid_local': fila['uuid_local'],
                           'columna': columna, 'valor_verdadero': fila[columna], 'valor_sucio': nuevo,
                           'tipo': tipo})
        fila[columna] = nuevo

    def fila_entera(self, fila, tipo, detalle=''):
        self.filas.append({'participante_id': fila['participante_id'], 'uuid_local': fila['uuid_local'],
                           'columna': '*', 'valor_verdadero': detalle, 'valor_sucio': '', 'tipo': tipo})


def _fecha_eval(fila):
    return date.fromisoformat(fila['fecha_evaluacion'])


def _visible(fila, campo):
    if campo in TRABAJO:
        return fila['trabaja_actualmente'] == 'True'
    if campo not in CONDICIONES:
        return True
    madre, op, esperado = CONDICIONES[campo]
    valor = fila.get(madre, '')
    if op == 'en':
        return False                                   # ecotomografía: solo personal de salud
    return _visible(fila, madre) and _cumple(valor, op, esperado, _fecha_eval(fila))


# --- 1. Omisiones -----------------------------------------------------------------
def omitir(rng, filas, bit):
    for f in filas:
        sin_peso = rng.random() < S['sin_peso']
        if sin_peso:
            bit.cambiar(f, 'peso_kg', '', 'omitida')
        if rng.random() < (S['sin_talla_si_falta_peso'] if sin_peso else S['sin_talla_con_peso']):
            bit.cambiar(f, 'talla_actual_cm', '', 'omitida')
        if rng.random() < S['sin_cintura']:
            bit.cambiar(f, 'circunferencia_cintura_cm', '', 'omitida')
        if rng.random() < S['sin_fecha_empa']:
            bit.cambiar(f, 'fecha_ultimo_empa', '', 'omitida')
        for col, valor in list(f.items()):
            if (valor != '' and col not in NO_TOCAR and col not in OMISION_PROPIA
                    and col not in SATISFACCION and rng.random() < P.PROP_BLANCOS):
                bit.cambiar(f, col, '', 'omitida')
        # Una pregunta "madre" en blanco oculta a sus dependientes, como en la plataforma.
        cambio = True
        while cambio:
            cambio = False
            for col in list(CONDICIONES) + TRABAJO:
                if f.get(col, '') != '' and not _visible(f, col):
                    bit.cambiar(f, col, '', 'omitida (cascada)')
                    cambio = True


# --- 2. Errores de lógica -----------------------------------------------------------
# Pregunta que no aplica y aun así viene respondida [R]: (campo, valores posibles).
CONDICIONALES_LLENOS = [
    ('sobrecarga_fisica_emocional', ['2', '3', '4']),
    ('cantidad_personas_cuida', ['1', '2']),
    ('menstruacion_llega', ['REGULAR', 'IRREGULAR', 'NO_SEGURA']),
    ('tipo_sangrado', ['MUY_LEVE', 'LEVE', 'MODERADO']),
    ('usa_metodo_anticonceptivo', ['NO', 'SI']),
    ('frecuencia_aerobico', ['2', '3']),
    ('frecuencia_fuerza', ['2', '3']),
    ('tipo_metodo_anticonceptivo', ['ORAL', 'DIU']),
]


def errores_logica(rng, filas, bit):
    for f in filas:
        if rng.random() < S['condicional_lleno']:
            ocultas = [(c, v) for c, v in CONDICIONALES_LLENOS if f[c] == '' and not _visible(f, c)]
            if ocultas:
                campo, valores = rng.choice(ocultas)
                bit.cambiar(f, campo, rng.choice(valores), 'responde pregunta que no aplica')
        if f['dias_ejercicio_semana'] not in ('', '1') and rng.random() < S['ejercicio_sin_tipo']:
            for tipo in ('aerobico', 'bajo_impacto', 'fuerza'):
                bit.cambiar(f, f'realiza_{tipo}', 'NO', 'días de ejercicio sin tipo marcado')
                bit.cambiar(f, f'frecuencia_{tipo}', '', 'días de ejercicio sin tipo marcado')
        if f['tipo_metodo_anticonceptivo'] == 'ORAL' and rng.random() < S['oral_con_terapia']:
            bit.cambiar(f, 'usa_terapia_hormonal', 'SI', 'píldora y terapia hormonal a la vez')
        if f['circunferencia_cintura_cm'] == '' and rng.random() < S['cintura_cero']:
            bit.cambiar(f, 'circunferencia_cintura_cm', '0.00', 'cintura 0 en vez de vacía')


# --- 3. Formatos ------------------------------------------------------------------------
def formatos(rng, filas, bit):
    for f in filas:
        fum = f['fecha_ultima_menstruacion']
        if len(fum) == 7:                                  # AAAA-MM
            anio, mes = fum.split('-')
            r = rng.random()
            if r < S['fum_dd_mm_aaaa']:
                bit.cambiar(f, 'fecha_ultima_menstruacion', f'{rng.randint(1, 28):02d}/{mes}/{anio}',
                            'formato de fecha')
            elif r < S['fum_dd_mm_aaaa'] + S['fum_mes_texto']:
                bit.cambiar(f, 'fecha_ultima_menstruacion', f'{MESES[int(mes) - 1]} {anio}', 'formato de fecha')
            elif r < S['fum_dd_mm_aaaa'] + S['fum_mes_texto'] + S['fum_mm_aaaa']:
                bit.cambiar(f, 'fecha_ultima_menstruacion', f'{mes}/{anio}', 'formato de fecha')
        if rng.random() < S['nacimiento_dd_mm_aaaa']:
            a, m, d = f['fecha_nacimiento'].split('-')
            bit.cambiar(f, 'fecha_nacimiento', f'{d}/{m}/{a}', 'formato de fecha')
        if rng.random() < S['region_nombre']:
            bit.cambiar(f, 'region_residencia', rng.choice(REGION_NOMBRE), 'región como nombre')

        for col, unidad in UNIDAD.items():
            valor = f[col]
            if valor in ('', '0.00'):
                continue
            r = rng.random()
            if r < S['unidad_en_texto']:
                bit.cambiar(f, col, f'{valor} {unidad}', 'unidad en el texto')
            elif r < S['unidad_en_texto'] + S['coma_decimal']:
                texto = valor if '.' in valor else f'{valor}.0'
                bit.cambiar(f, col, texto.replace('.', ','), 'coma decimal')

        for col, valor in list(f.items()):
            if col in META or valor == '':
                continue
            if valor in VARIANTES and rng.random() < S['codigo_variante']:
                bit.cambiar(f, col, rng.choice(VARIANTES[valor]), 'código escrito distinto')
            elif valor.isupper() and len(valor) > 2 and rng.random() < S['minusculas']:
                bit.cambiar(f, col, valor.lower(), 'código en minúsculas')
            elif not valor[0].isdigit() and rng.random() < S['espacios']:
                bit.cambiar(f, col, f' {valor} ' if rng.random() < 0.5 else f'{valor} ', 'espacios sobrantes')


# --- 4. Valores imposibles ----------------------------------------------------------------
def _es_numero(texto):
    try:
        float(texto)
        return True
    except ValueError:
        return False


def imposibles(rng, filas, bit, numericas):
    for f in filas:
        for col in numericas:
            if f[col] != '' and _es_numero(f[col]) and rng.random() < S['centinela_numero']:
                bit.cambiar(f, col, rng.choice(CENTINELA_NUMERO), 'centinela numérico')
        for col, valor in list(f.items()):
            if (valor != '' and col not in NO_TOCAR and col not in SATISFACCION
                    and rng.random() < S['centinela_texto']):
                bit.cambiar(f, col, rng.choice(CENTINELA_TEXTO), 'centinela de texto')
        for col in MRS_ITEMS:
            if rng.random() < S['mrs_fuera_rango']:
                bit.cambiar(f, col, rng.choice(['5', '9']), 'MRS fuera de rango')

        talla = f['talla_actual_cm']
        if _es_numero(talla) and float(talla) > 100:
            r = rng.random()
            if r < S['talla_en_metros']:
                bit.cambiar(f, 'talla_actual_cm', f'{float(talla) / 100:.2f}', 'talla en metros')
            elif r < S['talla_en_metros'] + S['talla_sin_punto']:
                bit.cambiar(f, 'talla_actual_cm', f'{talla}{rng.randint(0, 9)}', 'talla sin punto decimal')
        peso = f['peso_kg']
        if _es_numero(peso) and float(peso) > 30 and rng.random() < S['peso_digito_extra']:
            bit.cambiar(f, 'peso_kg', f'{peso.split(".")[0]}{rng.randint(0, 9)}', 'peso con dígito de más')

        nacimiento = f['fecha_nacimiento']
        if len(nacimiento) == 10 and nacimiento[4] == '-':
            anio_eval = _fecha_eval(f).year
            r = rng.random()
            if r < S['fecha_nacimiento_imposible']:
                anio = (anio_eval + rng.randint(1, 8) if rng.random() < 0.5
                        else anio_eval - rng.randint(101, 104))
                bit.cambiar(f, 'fecha_nacimiento', f'{anio}{nacimiento[4:]}', 'edad imposible')
            elif r < S['fecha_nacimiento_imposible'] + S['edad_fuera_criterio'] and f['excepcion_edad'] == 'NINGUNA':
                edad = rng.choice([rng.randint(35, 39), rng.randint(66, 70)])
                bit.cambiar(f, 'fecha_nacimiento', f'{anio_eval - edad - 1}{nacimiento[4:]}',
                            'edad fuera del criterio 40-65')


# --- 5. Filas duplicadas -------------------------------------------------------------------
def duplicar(rng, filas, bit):
    """Devuelve las filas con duplicados exactos y versiones antiguas del mismo RUT."""
    siguiente_id = max(int(f['participante_id']) for f in filas) + 1
    salida = []
    for f in filas:
        if rng.random() < S['rut_repetido']:
            # Versión anterior: misma persona (mismo RUT), registro distinto y algo antes.
            vieja = dict(f)
            dias = rng.randint(20, 90)
            vieja['participante_id'] = str(siguiente_id)
            vieja['usuario_id'] = str(int(f['usuario_id']) + 5000) if f['usuario_id'] else ''
            vieja['uuid_local'] = str(uuid.UUID(int=rng.getrandbits(128), version=4))
            for col in ('fecha_evaluacion', 'fecha_registro'):
                vieja[col] = (date.fromisoformat(f[col]) - timedelta(days=dias)).isoformat()
            for col in ('sincronizado_en', 'ultima_finalizacion_en', 'creado_en'):
                fecha, hora = f[col].split(' ')
                vieja[col] = f'{date.fromisoformat(fecha) - timedelta(days=dias)} {hora}'
            for col in rng.sample(MRS_ITEMS, 3):
                if vieja[col].isdigit() and int(vieja[col]) <= 4:
                    vieja[col] = str(min(4, max(0, int(vieja[col]) + rng.choice((-1, 1)))))
            siguiente_id += 1
            bit.fila_entera(vieja, 'RUT repetido (versión anterior)', f'participante {f["participante_id"]}')
            salida.append(vieja)
        salida.append(f)
        if rng.random() < S['duplicado_exacto']:
            copia = dict(f)
            bit.fila_entera(copia, 'duplicado exacto', f'participante {f["participante_id"]}')
            salida.append(copia)
    return salida


def ensuciar(rng, filas, numericas):
    """Devuelve (filas_sucias, bitacora). `filas` no se modifica."""
    filas = [dict(f) for f in filas]
    bit = Bitacora()
    omitir(rng, filas, bit)
    errores_logica(rng, filas, bit)
    formatos(rng, filas, bit)
    imposibles(rng, filas, bit, numericas)
    return duplicar(rng, filas, bit), bit.filas
