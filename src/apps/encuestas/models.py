import re
from datetime import date

from django.db import models


# ===========================================================================
# ESCALAS COMPARTIDAS (Regla del "Cerebro Habituado" - Sección 3.4 del spec)
# ---------------------------------------------------------------------------
# Todas las secciones de autoevaluación de la plataforma se unifican a un
# formato de 5 alternativas. La escala clínica MRS mantiene su rango 0-4.
# Excepciones puntuales de 4 alternativas (evacuación intestinal, distensión
# abdominal) cuando la pregunta no admite un punto medio natural.
# ===========================================================================

class EscalaNadaMucho(models.IntegerChoices):
    NADA = 1, 'Nada'
    POCO = 2, 'Poco'
    MODERADAMENTE = 3, 'Moderadamente'
    BASTANTE = 4, 'Bastante'
    MUCHO = 5, 'Mucho'


class EscalaFrecuencia(models.IntegerChoices):
    NUNCA = 1, 'Nunca'
    RARA_VEZ = 2, 'Rara vez'
    A_VECES = 3, 'A veces'
    FRECUENTEMENTE = 4, 'Frecuentemente'
    SIEMPRE = 5, 'Siempre'


class EscalaAcuerdo(models.IntegerChoices):
    MUY_EN_DESACUERDO = 1, 'Muy en desacuerdo'
    EN_DESACUERDO = 2, 'En desacuerdo'
    NEUTRAL = 3, 'Neutral'
    DE_ACUERDO = 4, 'De acuerdo'
    MUY_DE_ACUERDO = 5, 'Muy de acuerdo'


class EscalaFrecuenciaSemanal(models.IntegerChoices):
    """Frecuencia de consumo/hábito en una semana habitual (5 niveles)."""
    NUNCA = 1, 'Nunca'
    UNA_DOS = 2, '1-2 veces por semana'
    TRES_CUATRO = 3, '3-4 veces por semana'
    CINCO_SEIS = 4, '5-6 veces por semana'
    DIARIAMENTE = 5, 'Diariamente'


class EscalaPorciones(models.IntegerChoices):
    """Cantidad diaria consumida, expresada en tramos (vasos / porciones / platos)."""
    NO_CONSUMO = 1, 'No consumo'
    UNA_DOS = 2, '1-2 porciones'
    TRES_CUATRO = 3, '3-4 porciones'
    CINCO_SEIS = 4, '5-6 porciones'
    SIETE_O_MAS = 5, '7 o más porciones'


class EscalaFrecuenciaSubjetiva(models.IntegerChoices):
    """Frecuencia percibida de una situación (5 niveles, sin anclaje temporal exacto)."""
    NUNCA_CASI_NUNCA = 1, 'Nunca o casi nunca'
    RARA_VEZ = 2, 'Rara vez'
    A_VECES = 3, 'A veces'
    FRECUENTEMENTE = 4, 'Frecuentemente'
    SIEMPRE = 5, 'Siempre'


class EscalaEstresLaboral(models.IntegerChoices):
    """Nivel de estrés que genera el entorno laboral (1 = nada, 5 = extremo)."""
    NADA = 1, 'Nada de estrés'
    LEVE = 2, 'Estrés leve'
    MODERADO = 3, 'Estrés moderado'
    ALTO = 4, 'Estrés alto'
    EXTREMO = 5, 'Estrés extremo'


class FrecuenciaEvacuacionIntestinal(models.IntegerChoices):
    """Frecuencia de evacuación intestinal (Cuestionario Complementario MRS)."""
    MAS_DE_UNA_AL_DIA = 1, 'Más de una vez al día'
    UNA_AL_DIA = 2, '1 vez al día'
    CADA_DOS_DIAS = 3, 'Cada 2 días'
    TRES_O_MAS_DIAS = 4, '3 o más días entre evacuaciones'


class FrecuenciaDistensionAbdominal(models.IntegerChoices):
    """Frecuencia de distensión abdominal (Cuestionario Complementario MRS)."""
    NUNCA_CASI_NUNCA = 1, 'Nunca o casi nunca'
    A_VECES = 2, 'A veces'
    FRECUENTEMENTE = 3, 'Frecuentemente'
    SIEMPRE = 4, 'Siempre'


class CantidadPersonasCuidado(models.IntegerChoices):
    """Cantidad de personas bajo cuidado directo (sección Tareas de Cuidado)."""
    UNA = 1, '1 persona'
    DOS = 2, '2 personas'
    TRES_O_MAS = 3, '3 o más personas'


class RespuestaSiNo(models.TextChoices):
    SI = 'SI', 'Sí'
    NO = 'NO', 'No'


class RespuestaSiNoNoSabe(models.TextChoices):
    SI = 'SI', 'Sí'
    NO = 'NO', 'No'
    NO_SABE = 'NS', 'No sabe'


def meses_desde_texto_fecha(texto):
    """
    Meses entre una fecha escrita como texto libre y hoy.

    Acepta ``AAAA``, ``AAAA-MM``, ``AAAA/MM``, ``MM/AAAA``, ``AAAA-MM-DD`` y
    ``DD/MM/AAAA``. Cuando solo hay año se asume julio (mitad de año).
    Devuelve ``None`` si el texto no se puede interpretar. La lógica de
    "ausencia menstrual" (Cuestionario Complementario MRS) se apoya en esto,
    y el cliente replica el mismo cálculo para ocultar preguntas offline.
    """
    txt = (texto or '').strip()
    if not txt:
        return None

    anio = mes = None
    m = re.fullmatch(r'(\d{4})', txt)
    if m:
        anio, mes = int(m.group(1)), 7
    if anio is None:
        m = re.fullmatch(r'(\d{4})[-/](\d{1,2})', txt)
        if m:
            anio, mes = int(m.group(1)), int(m.group(2))
    if anio is None:
        m = re.fullmatch(r'(\d{1,2})[-/](\d{4})', txt)
        if m:
            mes, anio = int(m.group(1)), int(m.group(2))
    if anio is None:
        m = re.fullmatch(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', txt)
        if m:
            anio, mes = int(m.group(1)), int(m.group(2))
    if anio is None:
        m = re.fullmatch(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', txt)
        if m:
            mes, anio = int(m.group(2)), int(m.group(3))

    if anio is None or mes is None or not (1 <= mes <= 12):
        return None

    hoy = date.today()
    return (hoy.year - anio) * 12 + (hoy.month - mes)


# ===========================================================================
# SINCRONIZACIÓN OFFLINE-FIRST (Sección 5.1 del spec)
# ---------------------------------------------------------------------------
# Cada registro que se contesta en el dispositivo lleva un `uuid_local`
# generado por el cliente. El servidor lo usa para no duplicar cuando el
# dispositivo reintenta la sincronización.
# ===========================================================================

class SegmentoSincronizable(models.Model):
    uuid_local = models.UUIDField(
        null=True, blank=True, unique=True, editable=False,
        help_text="ID generado en el dispositivo para sincronización idempotente"
    )
    sincronizado_en = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True


class SegmentoDeRonda(SegmentoSincronizable):
    """
    Mixin de los segmentos de la encuesta (todo excepto Identificación, que es
    el perfil único de la participante). Permite reaplicar la encuesta sin
    sobrescribir el historial (Fase 13): cada sección guardada queda marcada
    con la ronda vigente de `Identificacion.ronda_actual` al momento de
    guardar, y esa ronda avanza recién cuando el payload llega con
    `finalizar: true` y se guarda sin errores (ver sync.py). Así, reaplicar la
    encuesta más adelante crea filas nuevas en vez de reemplazar las
    anteriores, construyendo la línea de tiempo de evolución sintomática.
    """
    ronda = models.PositiveIntegerField(default=1, editable=False)

    class Meta:
        abstract = True


# ===========================================================================
# 1. IDENTIFICACIÓN
# ===========================================================================

class Identificacion(SegmentoSincronizable):
    class GeneroOptions(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'
        NO_BINARIO = 'NB', 'No binario'
        OTRO = 'O', 'Otro'
        PREFIERO_NO_DECIR = 'PND', 'Prefiero no decirlo'

    class NivelEducativo(models.TextChoices):
        SIN_ESTUDIOS = 'SIN', 'Sin estudios'
        BASICA_INC = 'B_INC', 'Educación Básica Incompleta'
        BASICA_COM = 'B_COM', 'Educación Básica Completa'
        MEDIA_INC = 'M_INC', 'Educación Media Incompleta'
        MEDIA_COM = 'M_COM', 'Educación Media Completa'
        SUPERIOR_N_INC = 'S_N_INC', 'Educación Superior No Universitaria Incompleta'
        SUPERIOR_N_COM = 'S_N_COM', 'Educación Superior No Universitaria Completa'
        UNIVERSITARIA_INC = 'U_INC', 'Educación Universitaria Incompleta'
        UNIVERSITARIA_COM = 'U_COM', 'Educación Universitaria Completa'
        POSTGRADO = 'POST', 'Postgrado (Magíster/Doctorado)'

    class IdentidadOrigen(models.TextChoices):
        NINGUNO = 'NINGUNO', 'No se identifica con ningún pueblo originario/afro'
        MAPUCHE = 'MAPUCHE', 'Mapuche'
        DIAGUITA = 'DIAGUITA', 'Diaguita'
        AYMARA = 'AYMARA', 'Aymara'
        RAPANUI = 'RAPANUI', 'Rapa Nui'
        LICKANANTAY = 'LICKANANTAY', 'Lickanantay / Atacameño'
        QUECHUA = 'QUECHUA', 'Quechua'
        COLLA = 'COLLA', 'Colla'
        KAWESQAR = 'KAWESQAR', 'Kawésqar'
        YAGAN = 'YAGAN', 'Yagán'
        CHANGO = 'CHANGO', 'Chango'
        AFRODESCENDIENTE = 'AFRO', 'Afrodescendiente chileno/latinoamericano'
        ASIATICO = 'ASIATICO', 'Asiático'
        OTRO = 'OTRO', 'Otro pueblo originario'

    class OrigenMigratorio(models.TextChoices):
        CHILE = 'CL', 'Chileno/a'
        VENEZUELA = 'VE', 'Venezolano/a o de origen venezolano'
        COLOMBIA = 'CO', 'Colombiano/a o de origen colombiano'
        PERU = 'PE', 'Peruano/a o de origen peruano'
        HAITI = 'HT', 'Haitiano/a o de origen haitiano'
        BOLIVIA = 'BO', 'Boliviano/a o de origen boliviano'
        ECUADOR = 'EC', 'Ecuatoriano/a o de origen ecuatoriano'
        ARGENTINA = 'AR', 'Argentino/a o de origen argentino'
        OTRA = 'OTRA', 'Otra nacionalidad u origen'

    # --- REGIONES DE CHILE (16 Regiones Oficiales) ---
    class RegionesChile(models.TextChoices):
        AP = '15', 'Arica y Parinacota'
        TA = '01', 'Tarapacá'
        AN = '02', 'Antofagasta'
        AT = '03', 'Atacama'
        CO = '04', 'Coquimbo'
        VS = '05', 'Valparaíso'
        RM = '13', 'Metropolitana de Santiago'
        OH = '06', "Del Libertador Gral. Bernardo O'Higgins"
        MA = '07', 'Maule'
        NB = '16', 'Ñuble'
        BI = '08', 'BíoBío'
        AR = '09', 'La Araucanía'
        LR = '14', 'Los Ríos'
        LL = '10', 'Los Lagos'
        AI = '11', 'Aysén del Gral. Carlos Ibáñez del Campo'
        MG = '12', 'Magallanes y de la Antártica Chilena'
        OTRA = '99', 'Reside fuera de Chile / No aplica'

    # --- CAMPOS ---
    # Identificación del sujeto de investigación. El RUT en claro NO se
    # almacena: solo su hash unidireccional (regla 1.2 del spec).
    rut_hash = models.CharField(
        max_length=64, unique=True, null=True, blank=True, editable=False,
        help_text="HMAC-SHA256 del RUT del sujeto de investigación"
    )
    usuario = models.OneToOneField(
        'usuarios.Usuario', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='identificacion',
        help_text="Cuenta asociada, si la participante se registró por sí misma"
    )
    fecha_nacimiento = models.DateField(help_text="Fecha de nacimiento")

    # Demografía con opciones estandarizadas para ML
    genero = models.CharField(
        max_length=3, choices=GeneroOptions.choices,
        help_text="Género con el que se identifica"
    )
    nivel_educacion = models.CharField(
        max_length=8, choices=NivelEducativo.choices,
        help_text="Nivel educacional"
    )
    origen_procedencia = models.CharField(
        max_length=4, choices=OrigenMigratorio.choices, default=OrigenMigratorio.CHILE,
        help_text="Lugar de nacimiento (origen/procedencia)"
    )
    pueblo_originario_afro = models.CharField(
        max_length=15, choices=IdentidadOrigen.choices, default=IdentidadOrigen.NINGUNO,
        help_text="Se identifica con un pueblo indígena u originario / afrodescendiente"
    )

    # vivienda
    comuna = models.CharField(max_length=100, null=False, help_text="Comuna donde reside")
    region_residencia = models.CharField(
        max_length=2,
        choices=RegionesChile.choices,
        default=RegionesChile.RM,
        help_text="Región de residencia"
    )

    trabaja_actualmente = models.BooleanField(
        null=True, blank=True,
        help_text="¿Trabaja actualmente?"
    )

    class ExcepcionEdad(models.TextChoices):
        NINGUNA = 'NINGUNA', 'No aplica'
        MENOPAUSIA_QUIRURGICA = 'QUIRURGICA', 'Menopausia quirúrgica (histerectomía y/o extracción de ovarios)'
        AUSENCIA_MENSTRUACION = 'AUSENCIA', 'Ausencia prolongada de menstruación (12 meses o más) sin causa quirúrgica'

    excepcion_edad = models.CharField(
        max_length=10,
        choices=ExcepcionEdad.choices,
        default=ExcepcionEdad.NINGUNA,
        blank=True,
        help_text="Motivo declarado para participar con menos de 40 años, si aplica",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    ronda_actual = models.PositiveIntegerField(
        default=1,
        editable=False,
        help_text=(
            "Número de la ronda de evaluación en curso. Avanza cuando se "
            "finaliza una ronda con éxito (Fase 13); las secciones ya "
            "guardadas quedan marcadas con la ronda a la que pertenecen y no "
            "se sobrescriben al reaplicar la encuesta."
        ),
    )
    ultima_finalizacion_en = models.DateTimeField(
        null=True, blank=True, editable=False,
        help_text="Cuándo se finalizó la última ronda (Fase 31: plazo de 15 días entre rondas).",
    )

    def __str__(self):
        return f"Participante {self.id} - Origen: {self.get_origen_procedencia_display()}"

    @property
    def edad(self):
        hoy = date.today()
        edad_calculada = hoy.year - self.fecha_nacimiento.year
        cumplio_anos = (hoy.month, hoy.day) >= (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        if not cumplio_anos:
            edad_calculada -= 1
        return edad_calculada


# ===========================================================================
# 4. ESCALA MRS (Menopause Rating Scale) + 5. CUESTIONARIO COMPLEMENTARIO MRS
# ===========================================================================

class MRS(SegmentoDeRonda):
    """
    Escala de Evaluación de la Menopausia (Menopause Rating Scale - MRS).
    Se guarda como un segmento temporal para evaluar cambios según los hábitos.
    """

    # --- ESCALA DE RESPUESTA (0 - 4) ---
    class IntensidadMolestia(models.IntegerChoices):
        NINGUNA = 0, 'Ninguna'
        LEVE = 1, 'Leve'
        MODERADA = 2, 'Moderada'
        INTENSA = 3, 'Intensa'
        MUY_INTENSA = 4, 'Muy intensa'

    # Descripción larga de cada nivel (Hoja 1 del Excel). Se usará para la
    # escala de calor + iconografía emocional del frontend (Sección 4.1).
    DESCRIPCION_NIVELES = {
        0: 'No tienes ese síntoma.',
        1: 'Lo sientes, pero es poco molesto y casi no afecta tus actividades.',
        2: 'Es evidente y te molesta, pero puedes realizar tus actividades normalmente.',
        3: 'Te molesta bastante y afecta algunas actividades o tu bienestar.',
        4: 'Es muy molesto y afecta considerablemente tu vida cotidiana.',
    }

    # Severidad según el puntaje total (cortes habituales del MRS; pendiente de
    # confirmación de la profesora). Cada tupla: (puntaje máximo, categoría).
    SEVERIDAD_TOTAL = (
        (4, 'Sin síntomas o muy leves'),
        (8, 'Leve'),
        (15, 'Moderada'),
        (44, 'Severa'),
    )

    # --- RELACIÓN Y FECHA ---
    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_mrs'
    )
    fecha_evaluacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se responde la escala MRS"
    )

    # --- PREGUNTAS MRS (0 a 4) - texto literal del Excel ---
    pregunta_1 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Bochornos, sudoración, calores?"
    )
    pregunta_2 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Molestias al corazón (sentir latidos del corazón, palpitaciones, o presión al pecho)?"
    )
    pregunta_3 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Molestias musculares y articulares (dolores de huesos y articulaciones, dolores reumáticos)"
    )
    pregunta_4 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Dificultades en el sueño (insomnio, duermes poco y/o mal)"
    )
    pregunta_5 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Estado de ánimo depresivo (sentirse deprimida, decaída, triste a punto de llorar, sin ganas de vivir)"
    )
    pregunta_6 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Irritabilidad (sentirse tensa, explotas fácil, sentirse rabiosa, sentirse intolerante)?"
    )
    pregunta_7 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Ansiedad (sentirse angustiada, temerosa, inquieta, tendencia al pánico)?"
    )
    pregunta_8 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Cansancio físico y mental (rinde menos, se cansa fácil, olvidos frecuentes, mala memoria, le cuesta concentrarse)?"
    )
    pregunta_9 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Problemas sexuales (menos ganas de tener relaciones sexuales, menor frecuencia de relaciones sexuales, menor satisfacción sexual)?"
    )
    pregunta_10 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Problemas con la orina (problemas al orinar, orinas más veces, urgencia al orinar, se te escapa la orina)?"
    )
    pregunta_11 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Sequedad vaginal (sensación de genitales secos, malestar o ardor en los genitales, malestar o dolor con las relaciones sexuales)?"
    )

    # --- 5. CUESTIONARIO COMPLEMENTARIO MRS ---

    class FrecuenciaMenstruacion(models.TextChoices):
        REGULAR = 'REGULAR', 'Regular (cada 21-35 días)'
        IRREGULAR = 'IRREGULAR', 'Irregular (<21 o >35 días)'
        NO_SEGURA = 'NO_SEGURA', 'No estoy segura / No sé'
        # "Ausencia" no es una opción de esta pregunta: el sistema la calcula
        # solo a partir de `fecha_ultima_menstruacion` (≥12 meses = ausencia,
        # ver `MRS.menstruacion_ausente`), no de lo que responda aquí.

    class TipoSangrado(models.TextChoices):
        MUY_LEVE = 'MUY_LEVE', 'Muy leve'
        LEVE = 'LEVE', 'Leve'
        MODERADO = 'MODERADO', 'Moderado'
        ABUNDANTE = 'ABUNDANTE', 'Abundante'
        MUY_ABUNDANTE = 'MUY_ABUND', 'Muy abundante'

    class TipoMetodoAnticonceptivo(models.TextChoices):
        ORAL = 'ORAL', 'Oral'
        INYECTABLE = 'INYECTABLE', 'Inyectable'
        DIU = 'DIU', 'DIU'
        IMPLANTE = 'IMPLANTE', 'Implante'
        PRESERVATIVO = 'PRESERVATIVO', 'Preservativo'
        NO_SE = 'NO_SE', 'No sé'
        OTRO = 'OTRO', 'Otro'

    # --- Cuestionario Complementario MRS ---
    # La fecha de la última menstruación va primero: de ella depende la lógica
    # de "ausencia menstrual" (≥12 meses ⇒ se ocultan regularidad y sangrado).
    fecha_ultima_menstruacion = models.CharField(
        max_length=10,
        null=True, blank=True,
        help_text="Fecha de la última menstruación (regla) - puede ser solo el año"
    )
    menstruacion_llega = models.CharField(
        max_length=10,
        choices=FrecuenciaMenstruacion.choices,
        null=True, blank=True,
        help_text="Durante el último año, mi menstruación llega"
    )
    tipo_sangrado = models.CharField(
        max_length=10,
        choices=TipoSangrado.choices,
        null=True, blank=True,
        help_text="El sangrado de mi menstruación es"
    )
    usa_metodo_anticonceptivo = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa método anticonceptivo?"
    )
    tipo_metodo_anticonceptivo = models.CharField(
        max_length=12,
        choices=TipoMetodoAnticonceptivo.choices,
        null=True, blank=True,
        help_text="Si la respuesta es sí, ¿qué tipo utiliza?"
    )
    tipo_metodo_anticonceptivo_otro = models.CharField(
        max_length=100,
        null=True, blank=True,
        help_text='Si seleccionó "Otro", ¿cuál método anticonceptivo?'
    )
    usa_terapia_hormonal = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa tratamiento de terapia hormonal?"
    )
    operada_no_mas_hijos = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Está operada para no tener más hijos?"
    )
    tiene_utero = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Tiene útero?"
    )
    tiene_ovario = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Tiene al menos un ovario?"
    )
    tiene_pareja = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Actualmente tiene pareja?"
    )
    cambio_relacion_pareja_menopausia = models.IntegerField(
        choices=EscalaNadaMucho.choices,
        null=True, blank=True,
        help_text="¿Ha cambiado su relación de pareja y considera que los cambios se asocian a la menopausia?"
    )
    tiene_actividad_sexual = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Tiene actividad sexual?"
    )
    usa_antidepresivos = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa antidepresivos o medicamentos para dormir?"
    )
    usa_medicamentos_diabetes = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa medicamentos para la diabetes?"
    )
    usa_medicamentos_presion = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa medicamentos para la presión arterial?"
    )
    evacuacion_intestinal = models.IntegerField(
        choices=FrecuenciaEvacuacionIntestinal.choices,
        null=True, blank=True,
        help_text="¿Con qué frecuencia tiene evacuación intestinal?"
    )
    distension_abdominal = models.IntegerField(
        choices=FrecuenciaDistensionAbdominal.choices,
        null=True, blank=True,
        help_text="¿Con qué frecuencia siente distensión o hinchazón abdominal?"
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Segmento MRS"
        verbose_name_plural = "Segmentos MRS"

    def __str__(self):
        return f"MRS de {self.participante} - Fecha: {self.fecha_evaluacion} (Puntaje Total: {self.puntaje_total})"

    # --- PROPIEDADES ÚTILES PARA ML Y REPORTES ---
    @property
    def puntaje_total(self):
        """
        Suma automática de los 11 ítems MRS. Rango: 0 a 44 puntos.
        Útil para saber la severidad total del síntoma sin cálculos extra.
        """
        return (
            self.pregunta_1 + self.pregunta_2 + self.pregunta_3 + self.pregunta_4
            + self.pregunta_5 + self.pregunta_6 + self.pregunta_7 + self.pregunta_8
            + self.pregunta_9 + self.pregunta_10 + self.pregunta_11
        )

    @property
    def meses_desde_ultima_menstruacion(self):
        """
        Meses transcurridos desde `fecha_ultima_menstruacion` hasta hoy.

        El campo es texto libre y "puede ser solo el año": se aceptan
        ``AAAA``, ``AAAA-MM``, ``MM/AAAA`` y fecha completa (``AAAA-MM-DD`` /
        ``DD/MM/AAAA``). Si solo hay año, se asume mitad de año (julio).
        Devuelve ``None`` cuando no se puede interpretar.
        """
        return meses_desde_texto_fecha(self.fecha_ultima_menstruacion)

    @property
    def menstruacion_ausente(self):
        """True si han pasado 12 meses o más desde la última menstruación."""
        meses = self.meses_desde_ultima_menstruacion
        return meses is not None and meses >= 12


# ===========================================================================
# 6. EMPA (Examen de Medicina Preventiva del Adulto)
# ===========================================================================

class SegmentoEMPA(SegmentoDeRonda):
    """
    Segmento para el Examen de Medicina Preventiva del Adulto (EMPA).
    Muchos campos son opcionales (null=True, blank=True) porque pueden
    ser completados por personal médico o recuperados desde un sistema externo.
    """

    # --- RELACIÓN Y FECHA ---
    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_empa'
    )
    fecha_registro = models.DateField(
        auto_now_add=True,
        help_text="Fecha de registro de los datos EMPA"
    )
    fecha_ultimo_empa = models.DateField(
        null=True, blank=True,
        help_text="Fecha último EMPA"
    )

    # --- ORIGEN DE LOS DATOS ---
    class OrigenDato(models.TextChoices):
        AUTORREPORTADO = 'AUTO', 'Autorreportado por el usuario'
        PERSONAL_MEDICO = 'MEDICO', 'Ingresado por personal médico'
        SISTEMA_EXTERNO = 'API', 'Importado desde ficha clínica externa'

    origen_registro = models.CharField(
        max_length=10,
        choices=OrigenDato.choices,
        default=OrigenDato.AUTORREPORTADO,
        help_text="Indica quién o qué sistema ingresó este registro"
    )

    class RiesgoCardiovascular(models.TextChoices):
        BAJO = 'BAJO', 'Bajo'
        MODERADO = 'MODERADO', 'Moderado'
        ALTO = 'ALTO', 'Alto'

    class ResultadoPAP(models.TextChoices):
        NEGATIVO = 'NEGATIVO', 'Negativo para neoplasia'
        INFLAMATORIO = 'INFLAMATORIO', 'Inflamatorio'
        SOSPECHOSO = 'SOSPECHOSO', 'Sospechoso'
        ATROFICO = 'ATROFICO', 'Atrófico'

    class ResultadoBIRADS(models.IntegerChoices):
        BIRADS_0 = 0, 'BI-RADS 0'
        BIRADS_1 = 1, 'BI-RADS 1'
        BIRADS_2 = 2, 'BI-RADS 2'
        BIRADS_3 = 3, 'BI-RADS 3'
        BIRADS_4 = 4, 'BI-RADS 4'
        BIRADS_5 = 5, 'BI-RADS 5'
        BIRADS_6 = 6, 'BI-RADS 6'

    # --- 1. ANTROPOMETRÍA Y SIGNOS VITALES ---
    talla_actual_cm = models.IntegerField(
        null=True, blank=True,
        help_text="Talla actual en centímetros (ej: 165)"
    )
    talla_maxima_cm = models.IntegerField(
        null=True, blank=True,
        help_text="Talla máxima registrada a lo largo de la vida adulta, en centímetros (indicador de riesgo de osteoporosis)"
    )
    peso_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Peso en kilogramos (ej: 70.5)"
    )
    circunferencia_cintura_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Circunferencia de cintura en cm"
    )

    # Presión Arterial (completado por personal médico)
    presion_sistolica = models.IntegerField(
        null=True, blank=True,
        help_text="Presión arterial sistólica actual en mmHg (completado por personal médico)"
    )
    presion_diastolica = models.IntegerField(
        null=True, blank=True,
        help_text="Presión arterial diastólica actual en mmHg (completado por personal médico)"
    )

    # --- 2. EXÁMENES DE LABORATORIO (completado por personal médico / API) ---
    colesterol_total_mg_dl = models.IntegerField(
        null=True, blank=True,
        help_text="Colesterol total mg/dL actual (completado por personal médico)"
    )
    colesterol_hdl_mg_dl = models.IntegerField(
        null=True, blank=True,
        help_text="Colesterol HDL mg/dL actual (completado por personal médico)"
    )
    trigliceridos_mg_dl = models.IntegerField(
        null=True, blank=True,
        help_text="Triglicéridos mg/dL actual (completado por personal médico)"
    )
    glicemia_mg_dl = models.IntegerField(
        null=True, blank=True,
        help_text="Glicemia mg/dL actual (completado por personal médico)"
    )
    vdrl_rpr = models.CharField(
        max_length=20, null=True, blank=True,
        help_text="Resultado VDRL/RPR (si aplica)"
    )
    riesgo_cv_atp3 = models.CharField(
        max_length=10,
        choices=RiesgoCardiovascular.choices,
        null=True, blank=True,
        help_text="Riesgo cardiovascular según ATP-III (puntaje calculado por personal médico)"
    )

    # --- Tamizaje ginecológico ---
    fecha_ultimo_pap = models.DateField(
        null=True, blank=True,
        help_text="Fecha último PAP (vigencia hasta 3 años)"
    )
    resultado_pap = models.CharField(
        max_length=15,
        choices=ResultadoPAP.choices,
        null=True, blank=True,
        help_text="Resultado PAP"
    )
    fecha_mamografia = models.DateField(
        null=True, blank=True,
        help_text="Fecha de la última mamografía"
    )
    resultado_birads = models.IntegerField(
        choices=ResultadoBIRADS.choices,
        null=True, blank=True,
        help_text="Resultado mamografía (BI-RADS). Vigencia: con TRH 1 año, sin TRH 2 años"
    )
    fecha_ecotomografia_mamaria = models.DateField(
        null=True, blank=True,
        help_text="Ecotomografía mamaria (si mamografía BI-RADS 0, 3 o 4)"
    )

    # Consumo de sustancias (alcohol, tabaco, marihuana) vive en la sección
    # "Hábitos de vida", no en el EMPA (regla de la profesora — Fase 4).

    # --- PROPIEDADES CALCULADAS PARA MACHINE LEARNING ---
    @property
    def imc(self):
        """Calcula el Índice de Masa Corporal automáticamente si hay peso y talla actual."""
        if self.peso_kg and self.talla_actual_cm and self.talla_actual_cm > 0:
            estatura_m = self.talla_actual_cm / 100.0
            return round(float(self.peso_kg) / (estatura_m ** 2), 2)
        return None

    @property
    def perdida_talla_cm(self):
        """
        Diferencia entre la talla máxima histórica y la talla actual.
        Se usa como indicador de riesgo de pérdida ósea / osteoporosis (Sección 3.2).
        """
        if self.talla_maxima_cm and self.talla_actual_cm:
            return self.talla_maxima_cm - self.talla_actual_cm
        return None

    @property
    def presion_arterial_str(self):
        """Retorna la presión en formato 120/80."""
        if self.presion_sistolica and self.presion_diastolica:
            return f"{self.presion_sistolica}/{self.presion_diastolica}"
        return "No registrada"

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Segmento EMPA"
        verbose_name_plural = "Segmentos EMPA"

    def __str__(self):
        return f"EMPA de {self.participante} - {self.fecha_registro} ({self.get_origen_registro_display()})"


# ===========================================================================
# 9. CONOCIMIENTO DEL SISTEMA
# ===========================================================================

class ConocimientoSistema(SegmentoDeRonda):
    """
    Evaluación del conocimiento y acceso de la participante al sistema
    público de salud en relación al climaterio/menopausia.
    """

    class CalidadAtencion(models.IntegerChoices):
        MUY_MALA = 1, 'Muy mala'
        MALA = 2, 'Mala'
        NI_BUENA_NI_MALA = 3, 'Ni buena ni mala'
        BUENA = 4, 'Buena'
        MUY_BUENA = 5, 'Muy buena'

    class NivelInformacion(models.IntegerChoices):
        NADA = 1, 'Nada informada'
        POCO = 2, 'Poco informada'
        MODERADAMENTE = 3, 'Moderadamente informada'
        BASTANTE = 4, 'Bastante informada'
        MUY = 5, 'Muy informada'

    class Prevision(models.TextChoices):
        FONASA = 'FONASA', 'Fonasa'
        ISAPRE = 'ISAPRE', 'Isapre'
        FFAA = 'FFAA', 'FF.AA. y de Orden (Capredena, Dipreca)'
        NINGUNA = 'NINGUNA', 'Ninguna (particular)'
        NO_SE = 'NS', 'No sé'

    # --- RELACIÓN Y FECHA ---
    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_conocimiento_sistema'
    )
    fecha_evaluacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se responde el cuestionario"
    )

    # --- PREGUNTAS ---
    # Va primero: con Fonasa se muestra toda la sección; con otra previsión,
    # solo las preguntas que no dependen del sistema público (condicionales.py).
    prevision = models.CharField(
        max_length=7,
        choices=Prevision.choices,
        null=True, blank=True,
        help_text="¿Qué previsión de salud tiene?"
    )
    conoce_sistema_publico_climaterio = models.CharField(
        max_length=2,
        choices=RespuestaSiNoNoSabe.choices,
        null=True, blank=True,
        help_text="¿Conoce si el sistema público de salud en Chile ofrece atención para mujeres en etapa de climaterio o menopausia?"
    )
    ha_escuchado_programa_climaterio = models.CharField(
        max_length=2,
        choices=RespuestaSiNoNoSabe.choices,
        null=True, blank=True,
        help_text="¿Ha escuchado hablar del Programa de Climaterio o atención relacionada con menopausia en centros de salud públicos?"
    )
    sabe_donde_acudir = models.CharField(
        max_length=2,
        choices=RespuestaSiNoNoSabe.choices,
        null=True, blank=True,
        help_text="¿Sabe dónde acudir para recibir orientación o atención relacionada con síntomas del climaterio o menopausia?"
    )
    ha_consultado_por_sintomas = models.CharField(
        max_length=2,
        choices=RespuestaSiNoNoSabe.choices,
        null=True, blank=True,
        help_text="¿Ha consultado alguna vez en un centro de salud por síntomas relacionados con climaterio o menopausia?"
    )
    # Justo bajo la pregunta de la que depende: el orden de los campos es el
    # orden en que se muestran las preguntas.
    evaluacion_atencion_recibida = models.IntegerField(
        choices=CalidadAtencion.choices,
        null=True, blank=True,
        help_text="Si respondió 'Sí', ¿cómo evaluaría la atención recibida?"
    )
    # Pregunta reubicada desde el Cuestionario Complementario MRS (regla de la profesora).
    en_control_programa_consultorio = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Está en control en algún programa de su consultorio?"
    )
    en_control_programa_cual = models.CharField(
        max_length=255,
        null=True, blank=True,
        help_text="Si es sí, ¿en cuál programa?"
    )
    considera_informacion_suficiente = models.IntegerField(
        choices=EscalaNadaMucho.choices,
        null=True, blank=True,
        help_text="¿Considera que el sistema de salud entrega suficiente información sobre climaterio o menopausia?"
    )
    nivel_informacion_servicios = models.IntegerField(
        choices=NivelInformacion.choices,
        null=True, blank=True,
        help_text="¿Qué tan informada se considera respecto a los servicios disponibles para mujeres en climaterio o menopausia?"
    )
    conoce_recursos_disponibles = models.CharField(
        max_length=2,
        choices=RespuestaSiNoNoSabe.choices,
        null=True, blank=True,
        help_text=(
            "¿Conoce alguno de los siguientes recursos o prestaciones? "
            "(Atención médica en APS/CESFAM, Controles ginecológicos, Terapia hormonal, "
            "Atención psicológica, Consejería en salud mental, Orientación nutricional, "
            "Programas de actividad física, No conozco prestaciones relacionadas)."
        )
    )
    ha_tenido_dificultades_acceso = models.CharField(
        max_length=2,
        choices=RespuestaSiNoNoSabe.choices,
        null=True, blank=True,
        help_text="¿Ha sentido dificultades para acceder a atención relacionada con esta etapa?"
    )
    # Selección múltiple (lista separada por comas); las opciones están en
    # esquema.OPCIONES_MULTISELECCION.
    principales_dificultades = models.TextField(
        null=True, blank=True,
        help_text="¿Cuáles han sido las principales dificultades? (marque todas las opciones que apliquen)"
    )
    principales_dificultades_otra = models.CharField(
        max_length=200,
        null=True, blank=True,
        help_text='Si marcó "Otra", ¿cuál?'
    )
    sintomas_tomados_en_serio = models.IntegerField(
        choices=EscalaNadaMucho.choices,
        null=True, blank=True,
        help_text="¿Considera que los síntomas asociados al climaterio o menopausia son tomados en serio por los profesionales de salud?"
    )
    desea_mas_informacion_apoyo = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Le gustaría recibir más información o apoyo relacionado con esta etapa?"
    )
    tipo_informacion_apoyo_deseado = models.TextField(
        null=True, blank=True,
        help_text="¿Qué tipo de información o apoyo considera más necesario? (marque todas las opciones que apliquen)"
    )
    tipo_informacion_apoyo_otro = models.CharField(
        max_length=200,
        null=True, blank=True,
        help_text='Si marcó "Otro", especifique qué tipo de información o apoyo'
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Conocimiento del Sistema"
        verbose_name_plural = "Conocimiento del Sistema"

    def __str__(self):
        return f"Conocimiento Sistema de {self.participante} - {self.fecha_evaluacion}"


# ===========================================================================
# 2. TRABAJO (sección nueva)
# ===========================================================================

class EvaluacionTrabajo(SegmentoDeRonda):
    """
    Impacto del empleo actual en la salud y síntomas asociados a la menopausia
    (Sección 3.3 del spec: máximo 3-4 preguntas sobre sobrecarga laboral).
    """

    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_trabajo'
    )
    fecha_evaluacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se responde la sección Trabajo"
    )

    rendimiento_afectado = models.IntegerField(
        choices=EscalaNadaMucho.choices,
        null=True, blank=True,
        help_text="¿Su rendimiento o desempeño laboral se ha visto afectado por síntomas asociados a la menopausia?"
    )
    bienestar_trabajo_afectado = models.IntegerField(
        choices=EscalaNadaMucho.choices,
        null=True, blank=True,
        help_text="¿Su bienestar general en el trabajo se ha visto afectado por estos síntomas?"
    )
    frecuencia_ausencias = models.IntegerField(
        choices=EscalaFrecuencia.choices,
        null=True, blank=True,
        help_text="¿Con qué frecuencia ha debido ausentarse o llegar tarde al trabajo por síntomas relacionados con la menopausia?"
    )
    lugar_trabajo_comprensivo = models.IntegerField(
        choices=EscalaAcuerdo.choices,
        null=True, blank=True,
        help_text="¿Considera que su lugar de trabajo es comprensivo o flexible frente a estos síntomas?"
    )
    estres_entorno_laboral = models.IntegerField(
        choices=EscalaEstresLaboral.choices,
        null=True, blank=True,
        help_text="¿Su entorno laboral le genera niveles de estrés que intensifiquen sus síntomas?"
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Sección Trabajo"
        verbose_name_plural = "Secciones Trabajo"

    def __str__(self):
        return f"Trabajo de {self.participante} - {self.fecha_evaluacion}"


# ===========================================================================
# 3. TAREAS DE CUIDADO (sección nueva - "Crítico")
# ===========================================================================

class TareasCuidado(SegmentoDeRonda):
    """
    Sobrecarga por tareas de cuidado no remuneradas. El sistema pondera este
    factor de forma prioritaria: la doble carga (trabajo remunerado + cuidado)
    combinada con las fluctuaciones hormonales incrementa de forma sinérgica
    el nivel de estrés (Sección 3.3 del spec).
    """

    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_tareas_cuidado'
    )
    fecha_evaluacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se responde la sección Tareas de Cuidado"
    )

    cuida_otras_personas = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text=("¿Tiene a su cargo el cuidado directo de otras personas "
                   "(hijos, adultos mayores, familiares dependientes)?")
    )
    cantidad_personas_cuida = models.PositiveSmallIntegerField(
        choices=CantidadPersonasCuidado.choices,
        null=True, blank=True,
        help_text='Si respondió "Sí", ¿a cuántas personas cuida de forma directa?'
    )
    a_quien_cuida = models.TextField(
        null=True, blank=True,
        help_text="¿A quién cuida? (marque todas las opciones que apliquen)"
    )
    a_quien_cuida_otro = models.CharField(
        max_length=200,
        null=True, blank=True,
        help_text='Si marcó "Otro", especifique a quién cuida'
    )
    sobrecarga_fisica_emocional = models.IntegerField(
        choices=EscalaFrecuenciaSubjetiva.choices,
        null=True, blank=True,
        help_text=("¿Siente que la combinación entre su trabajo y las tareas de "
                   "cuidado le genera una sobrecarga física o emocional?")
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Sección Tareas de Cuidado"
        verbose_name_plural = "Secciones Tareas de Cuidado"

    def __str__(self):
        return f"Tareas de Cuidado de {self.participante} - {self.fecha_evaluacion}"

    @property
    def doble_carga(self):
        """
        True si la participante tiene trabajo remunerado y además personas a su
        cuidado. Factor de ponderación prioritaria para el nivel de estrés
        (el peso numérico se define en la etapa de scoring).
        """
        return bool(self.participante.trabaja_actualmente) and self.cuida_otras_personas == RespuestaSiNo.SI


# ===========================================================================
# 7. ACTIVIDAD FÍSICA (sección nueva)
# ===========================================================================

class ActividadFisica(SegmentoDeRonda):
    """Hábitos de actividad física y sedentarismo (Sección 7 del Excel)."""

    class DiasEjercicioSemana(models.IntegerChoices):
        CERO = 1, '0 días'
        UNA_DOS = 2, '1-2 días'
        TRES_CUATRO = 3, '3-4 días'
        CINCO_SEIS = 4, '5-6 días'
        TODOS = 5, 'Todos los días'

    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_actividad_fisica'
    )
    fecha_evaluacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se responde la sección Actividad Física"
    )

    dias_ejercicio_semana = models.IntegerField(
        choices=DiasEjercicioSemana.choices,
        null=True, blank=True,
        help_text="Durante una semana habitual, ¿cuántos días realiza ejercicio?"
    )
    realiza_aerobico = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Realiza ejercicio aeróbico? (trote, bicicleta, natación, baile, spinning)"
    )
    frecuencia_aerobico = models.IntegerField(
        choices=EscalaFrecuencia.choices,
        null=True, blank=True,
        help_text="Frecuencia del ejercicio aeróbico"
    )
    realiza_bajo_impacto = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Realiza actividades físicas de bajo impacto? (yoga, pilates, estiramientos, caminata suave, tai chi)"
    )
    frecuencia_bajo_impacto = models.IntegerField(
        choices=EscalaFrecuencia.choices,
        null=True, blank=True,
        help_text="Frecuencia de actividades de bajo impacto"
    )
    realiza_fuerza = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Realiza ejercicios de fuerza o resistencia muscular? (pesas, bandas elásticas, máquinas, peso corporal)"
    )
    frecuencia_fuerza = models.IntegerField(
        choices=EscalaFrecuencia.choices,
        null=True, blank=True,
        help_text="Frecuencia de ejercicios de fuerza"
    )
    horas_sedentarismo = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="En promedio, ¿cuántas horas al día permanece sentada o sedentaria?"
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Sección Actividad Física"
        verbose_name_plural = "Secciones Actividad Física"

    def __str__(self):
        return f"Actividad Física de {self.participante} - {self.fecha_evaluacion}"


# ===========================================================================
# 8. HÁBITOS DE VIDA (antes "Hábitos alimenticios")
# ===========================================================================

class HabitosDeVida(SegmentoDeRonda):
    """
    Hábitos de alimentación y consumo de sustancias (tabaco, marihuana,
    alcohol). Todas las cantidades y frecuencias usan escalas de 5 niveles
    (regla de la profesora — requisitos finales, sección 6). El consumo de
    sustancias se trasladó aquí desde el EMPA.
    """

    class QuienPreparaComidas(models.TextChoices):
        YO_MAYORIA = 'YO_MAYORIA', 'Yo preparo la mayoría'
        COMPARTIDO = 'COMPARTIDO', 'Yo preparo algunas y otras personas otras'
        OTRA_PERSONA_HOGAR = 'OTRA_HOGAR', 'Otra persona de mi hogar prepara la mayoría'
        COMPRO_PREPARADA = 'COMPRO', 'Generalmente compro comida preparada'
        OTRO = 'OTRO', 'Otro'

    participante = models.ForeignKey(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluaciones_habitos_de_vida'
    )
    fecha_evaluacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se responde la sección Hábitos de vida"
    )

    quien_prepara_comidas = models.CharField(
        max_length=15,
        choices=QuienPreparaComidas.choices,
        null=True, blank=True,
        help_text="¿Quién prepara habitualmente sus comidas principales?"
    )
    quien_prepara_comidas_otro = models.CharField(
        max_length=100,
        null=True, blank=True,
        help_text='Si seleccionó "Otro", ¿quién prepara sus comidas?'
    )
    frecuencia_comida_fuera = models.IntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Con qué frecuencia consume comidas compradas/preparadas fuera del hogar?"
    )
    falta_tiempo_influye = models.IntegerField(
        choices=EscalaFrecuenciaSubjetiva.choices,
        null=True, blank=True,
        help_text="¿La falta de tiempo influye en su elección de alimentos?"
    )
    vasos_agua_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántos vasos de agua toma al día?"
    )
    platos_verduras_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántos platos de verduras o ensaladas come al día?"
    )
    frutas_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántas frutas come cada día?"
    )
    panes_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántos panes (marraqueta, hallulla) come al día?"
    )
    lacteos_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántos productos lácteos come al día?"
    )
    jugos_gaseosas_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántos vasos al día toma de jugos y/o bebidas gaseosas?"
    )
    bebidas_energeticas_dia = models.PositiveSmallIntegerField(
        choices=EscalaPorciones.choices,
        null=True, blank=True,
        help_text="¿Cuántos vasos al día toma de bebidas energéticas?"
    )
    pescado_semana = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Cuántas veces a la semana come pescado?"
    )
    legumbres_semana = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Cuántas veces a la semana come legumbres?"
    )
    carnes_semana = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Cuántas veces a la semana come carnes (pollo, carne, cerdo)?"
    )
    golosinas_semana = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text=("¿Cuántas veces a la semana come pasteles, dulces, chocolates, "
                   "golosinas, helados o snacks salados?")
    )
    tabaco_frecuencia = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Fuma tabaco o cigarrillo?"
    )
    marihuana_frecuencia = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Fuma marihuana?"
    )
    alcohol_frecuencia = models.PositiveSmallIntegerField(
        choices=EscalaFrecuenciaSemanal.choices,
        null=True, blank=True,
        help_text="¿Consume bebidas alcohólicas?"
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Sección Hábitos de Vida"
        verbose_name_plural = "Secciones Hábitos de Vida"

    def __str__(self):
        return f"Hábitos de Vida de {self.participante} - {self.fecha_evaluacion}"


# ===========================================================================
# EVALUACIÓN DE SATISFACCIÓN CON LA PLATAFORMA (Fase 22)
# ===========================================================================

class EvaluacionSatisfaccion(models.Model):
    """
    Evaluación breve de la plataforma, voluntaria, a la que la participante
    entra con un botón tras finalizar al menos una ronda. Es una sola por
    participante (evalúa la herramienta, no cada ronda); si la vuelve a
    enviar, se actualiza.
    """

    class Facilidad(models.IntegerChoices):
        MUY_DIFICIL = 1, '😡 Muy difícil'
        DIFICIL = 2, '😕 Difícil'
        NORMAL = 3, '😐 Normal'
        FACIL = 4, '🙂 Fácil'
        MUY_FACIL = 5, '😍 Muy fácil'

    class Fatiga(models.IntegerChoices):
        NINGUNA = 1, 'Ninguno'
        POCA = 2, 'Poco'
        MODERADA = 3, 'Moderado'
        MUCHA = 4, 'Mucho'

    class Estrellas(models.IntegerChoices):
        UNA = 1, '★'
        DOS = 2, '★★'
        TRES = 3, '★★★'
        CUATRO = 4, '★★★★'
        CINCO = 5, '★★★★★'

    class Recomendaria(models.TextChoices):
        SI = 'SI', 'Definitivamente sí'
        TAL_VEZ = 'TAL_VEZ', 'Tal vez'
        NO = 'NO', 'No'

    participante = models.OneToOneField(
        Identificacion,
        on_delete=models.CASCADE,
        related_name='evaluacion_satisfaccion',
    )
    facilidad_uso = models.PositiveSmallIntegerField(
        choices=Facilidad.choices,
        help_text='¿Cómo evalúas la facilidad para responder el cuestionario?',
    )
    fatiga_mental = models.PositiveSmallIntegerField(
        choices=Fatiga.choices,
        help_text='¿Sentiste fatiga o cansancio mental al responder la encuesta?',
    )
    comodidad_diseno = models.PositiveSmallIntegerField(
        choices=Estrellas.choices,
        help_text='¿Qué tan cómodo te pareció el diseño y la navegación de la plataforma?',
    )
    recomendaria = models.CharField(
        max_length=7,
        choices=Recomendaria.choices,
        help_text='¿Recomendarías este Observatorio a otras mujeres en etapa de peri o menopausia?',
    )
    incomodidad = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        help_text='¿Hubo alguna pregunta que te generara incomodidad o confusión?',
    )
    comentario_incomodidad = models.TextField(
        blank=True,
        help_text='Cuál pregunta o por qué (obligatorio si respondió Sí)',
    )
    respondida_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'evaluación de satisfacción'
        verbose_name_plural = 'evaluaciones de satisfacción'

    def __str__(self):
        return f'Evaluación de satisfacción de {self.participante}'
