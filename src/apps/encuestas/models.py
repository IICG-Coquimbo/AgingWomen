from django.db import models
from encrypted_fields.fields import EncryptedCharField
from datetime import date

class Identificacion(models.Model):
    class GeneroOptions(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'
        NO_BINARIO = 'NB', 'No Binario'
        OTRO = 'O', 'Otro / Prefiero no decirlo'

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
    # Identificación única y encriptada
    rut = EncryptedCharField(max_length=20, unique=True, help_text="RUT encriptado")
    fecha_nacimiento = models.DateField()
    
    # Demografía con opciones estandarizadas para ML
    genero = models.CharField(max_length=2, choices=GeneroOptions.choices)
    nivel_educacion = models.CharField(max_length=8, choices=NivelEducativo.choices)
    pueblo_originario_afro = models.CharField(max_length=15, choices=IdentidadOrigen.choices, default=IdentidadOrigen.NINGUNO)
    origen_procedencia = models.CharField(max_length=4, choices=OrigenMigratorio.choices, default=OrigenMigratorio.CHILE)
    
    # vivienda
    comuna= models.CharField(max_length=15,null=False,help_text="Comuna donde reside")
    # Campo agregado: Región de residencia en Chile
    region_residencia = models.CharField(
        max_length=2,
        choices=RegionesChile.choices,
        default=RegionesChile.RM,
        help_text="Región de residencia"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

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

class MRS(models.Model):
    """
    Escala de Evaluación de la Menopausia (Menopause Rating Scale - MRS).
    Se guarda como un segmento temporal para evaluar cambios según los hábitos.
    """

    # --- ESCALA DE RESPUESTA (Likert 0 - 4) ---
    class IntensidadMolestia(models.IntegerChoices):
        NINGUNA = 0, 'No siento molestia'
        LEVE = 1, 'Siento molestia leve'
        MODERADA = 2, 'Siento molestia moderada'
        IMPORTANTE = 3, 'Siente molestia importante'
        DEMASIADA = 4, 'Siente demasiada molestia'

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

    # --- PREGUNTAS MRS (0 a 4) ---
    # Aquí puedes colocar tus preguntas. Dejo algunos ejemplos de la escala MRS real:
    
    # 1. Sofocos / bochornos, sudoración
    pregunta_1 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Bochornos, sudoración, calores?"
    )
    
    # 2. Molestias cardíacas (palpitaciones, etc.)
    pregunta_2 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Molestias al corazón (sentir latidos del corazón, palpitaciones, o presión al pecho)?"
    )
    
    # 3. Molestias musculares
    pregunta_3 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Molestias musculares y articulares (dolores de huesos y articulaciones, dolores reumáticos)"
    )

    # 4. Transtorno del sueño
    pregunta_4 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Dificultades en el sueño (insomnio, duermes poco y/o mal)"
    )

    # 5. Transtorno depresivo
    pregunta_5 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Estado de ánimo depresivo (sentirse deprimida, decaída, triste a punto de llorar, sin ganas de vivir)"
    )

    # 6. Transtorno anímico
    pregunta_6 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Irritabilidad (sentirse tensa, explotas fácil, sentirse rabiosa, sentirse intolerante)?"
    )

    # 7. Transtorno de ansiedad
    pregunta_7 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Ansiedad (sentirse angustiada, temerosa, inquieta, tendencia al pánico)?"
    )

    # 8. Cansancio físico
    pregunta_8 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Cansancio físico y mental (rinde menos, se cansa fácil, olvidos frecuentes, mala memoria, le cuesta concentrarse)?"
    )

    # 9 . Transtornos sexuales
    pregunta_9 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Sequedad vaginal (sensación de genitales secos, malestar o ardor en los genitales, malestar o dolor con las relaciones sexuales)?"
    )

    # 10. Transtornos urogenitales
    pregunta_10 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Problemas con la orina (problemas al orinar, orinas más veces, urgencia al orinar, se te escapa la orina)?"
    )

    # 11. Sequedad
    pregunta_11 = models.IntegerField(
        choices=IntensidadMolestia.choices,
        default=IntensidadMolestia.NINGUNA,
        help_text="¿Con cuánta intensidad sientes: Sequedad vaginal (sensación de genitales secos, malestar o ardor en los genitales, malestar o dolor con las relaciones sexuales)?"
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
        Suma automáticamente todos los ítems de la encuesta.
        Útil para saber la severidad total del síntoma sin hacer cálculos extra.
        """
        # Suma los valores numéricos de las preguntas
        return self.pregunta_1 + self.pregunta_2 + self.pregunta_3 + self.pregunta_4 + self.pregunta_5 + self.pregunta_6 + self.pregunta_7 + self.pregunta_8 + self.pregunta_9 + self.pregunta_10 + self.pregunta_11

class SegmentoEMPA(models.Model):
    """
    Segmento para el Examen de Medicina Preventiva del Adulto (EMPA).
    Muchos campos son opcionales (null=True, blank=True) porque pueden
    ser completados por personal médico o recuperados desde un sistema externo.
    """

    # --- RELACIÓN Y FECHA ---
    participante = models.ForeignKey(
        Participante, 
        on_delete=models.CASCADE, 
        related_name='evaluaciones_empa'
    )
    fecha_registro = models.DateField(
        auto_now_add=True, 
        help_text="Fecha de registro de los datos EMPA"
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

    # --- 1. ANTROPOMETRÍA Y SIGNOS VITALES (Pueden venir de clínica) ---
    peso_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, 
        help_text="Peso en kilogramos (ej: 70.5)"
    )
    estatura_cm = models.IntegerField(
        null=True, blank=True, 
        help_text="Estatura en centímetros (ej: 165)"
    )
    circunferencia_cintura_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, 
        help_text="Circunferencia abdominal en cm"
    )
    
    # Presión Arterial
    presion_sistolica = models.IntegerField(
        null=True, blank=True, 
        help_text="Presión sistólica (ej: 120)"
    )
    presion_diastolica = models.IntegerField(
        null=True, blank=True, 
        help_text="Presión diastólica (ej: 80)"
    )

    # --- 2. EXÁMENES DE LABORATORIO (Uso típico del personal médico / API) ---
    glicemia_mg_dl = models.IntegerField(
        null=True, blank=True, 
        help_text="Glicemia en ayunas (mg/dL)"
    )
    colesterol_total_mg_dl = models.IntegerField(
        null=True, blank=True, 
        help_text="Colesterol total (mg/dL)"
    )
    vdrl_rpr = models.CharField(
        max_length=20, null=True, blank=True, 
        help_text="Resultado VDRL/RPR (si aplica)"
    )
    mamografia_al_dia = models.BooleanField(
        null=True, blank=True, 
        help_text="¿Mamografía al día? (según rango de edad)"
    )
    pap_al_dia = models.BooleanField(
        null=True, blank=True, 
        help_text="¿Papanicolau al día?"
    )

    # --- 3. CUESTIONARIOS DE HABITOS / TAMIZAJE (Autorreportables) ---
    class RiesgoAlcohol(models.TextChoices):
        SIN_RIESGO = 'BAJO', 'Consumo normal / Sin riesgo (AUDIT C < 4)'
        RIESGO = 'ALTO', 'Consumo de riesgo (AUDIT C >= 4)'

    auditoria_alcohol = models.CharField(
        max_length=5, choices=RiesgoAlcohol.choices, null=True, blank=True
    )
    
    bebedor_problema = models.BooleanField(
        default=False, help_text="Resultado de tamizaje de alcoholismo"
    )
    fuma_actualmente = models.BooleanField(
        null=True, blank=True, help_text="¿Fuma actualmente?"
    )

    # --- PROPIEDADES CALCULADAS PARA MACHINE LEARNING ---
    @property
    def imc(self):
        """Calcula el Índice de Masa Corporal automáticamente si hay peso y estatura."""
        if self.peso_kg and self.estatura_cm and self.estatura_cm > 0:
            estatura_m = self.estatura_cm / 100.0
            return round(float(self.peso_kg) / (estatura_m ** 2), 2)
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