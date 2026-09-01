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

#Faltaba agregar esta pregunta
    trabaja_actualmente = models.BooleanField(
        null=True, blank=True,
        help_text="¿Trabaja actualmente?"
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
        help_text="¿Con cuánta intensidad sientes: Problemas sexuales (menos ganas de tener relaciones sexuales, menos frecuencia de relaciones sexuales, menor satisfacción sexual)?"
        #Esta pregunta duplicaba a la pregunta 11 así que la actualicé basandome en el excel que se nos compartió
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
#Acá se agrega la sección complementaria "Cuestionario complementario MRS"
    # --- Cuestionario Complementario MRS ---
    
    class FrecuenciaMenstruacion(models.TextChoices):
        UNA_VEZ_MES = 'UNA_VEZ', 'Una vez cada mes'
        VARIAS_VECES = 'VARIAS', 'Varias veces al mes'
        NO_TODOS_MESES = 'NO_TODOS', 'No me llega todos los meses'
        SANGRA_TODO_MES = 'TODO_MES', 'Sangro durante todo el mes'
        NO_SANGRA = 'NO_SANGRA', 'No sangro'

    class TipoSangrado(models.TextChoices):
        IGUAL_SIEMPRE = 'IGUAL', 'Igual que siempre'
        POCO = 'POCO', 'Poco comparado con lo habitual'
        DIFERENTE = 'DIFERENTE', 'Diferente a lo habitual'
        ABUNDANTE = 'ABUNDANTE', 'Abundante comparado con lo habitual'
        CON_COAGULOS = 'COAGULOS', 'Con más coágulos comparado con lo habitual'

    class RespuestaSiNo(models.TextChoices):
        SI = 'SI', 'Si'
        NO = 'NO', 'No'
        NO_SABE = 'NS', 'No Sabe'

    menstruacion_llega = models.CharField(
        max_length=10,
        choices=FrecuenciaMenstruacion.choices,
        null=True, blank=True,
        help_text="Durante el último año mi menstruación llega"
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
        help_text="¿Usa método anticonceptivo? (orales, inyectables o DIU)"
    )
    usa_terapia_hormonal = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa hormonas (terapia hormonal)?"
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
    respuesta_pareja_menopausia = models.TextField(
        null=True, blank=True,
        help_text="¿Cómo consideras que tu pareja ha respondido a los cambios asociados a tu menopausia?"
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
        help_text="¿Usa antidepresivos o remedios para dormir?"
    )
    usa_remedios_diabetes = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa remedios para la diabetes?"
    )
    usa_remedios_presion = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Usa remedios para la presión arterial?"
    )
    control_otros_programas = models.CharField(
        max_length=2,
        choices=RespuestaSiNo.choices,
        null=True, blank=True,
        help_text="¿Está en control en otros programas de su consultorio?"
    )
    fecha_ultima_menstruacion = models.CharField(
        #Esta como un charfield en vez de un datefield porque el excel dicen que puede ser solo el año si no lo recuerdan
        max_length=10,
        null=True, blank=True,
        help_text="Fecha de la última menstruación (regla) - puede ser solo el año"
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
        Identificacion, # acá estaba como participante, pero los datos que se almacenaban coincidían con las características de identificación
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
    
    #--> Acá pondré lo del conocimiento del sistema

class ConocimientoSistema(models.Model):
    """
    Evaluación del conocimiento y acceso de la participante al sistema
    público de salud en relación al climaterio/menopausia.
    """

    class RespuestaSiNoInsegura(models.TextChoices):
        SI = 'SI', 'Si'
        NO = 'NO', 'No'
        NO_SEGURA = 'NS', 'No estoy segura'

    class CalidadAtencion(models.TextChoices):
        MUY_MALA = 'MUY_MALA', 'Muy mala'
        MALA = 'MALA', 'Mala'
        REGULAR = 'REGULAR', 'Regular'
        BUENA = 'BUENA', 'Buena'
        MUY_BUENA = 'MUY_BUENA', 'Muy Buena'

    class NivelInformacion(models.TextChoices):
        NADA = 'NADA', 'Nada informada'
        POCO = 'POCO', 'Poco informada'
        MODERADA = 'MODERADA', 'Moderadamente informada'
        MUY = 'MUY', 'Muy informada'

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
    conoce_sistema_publico_climaterio = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Conoce si el sistema público de salud en Chile ofrece atención para mujeres en etapa de climaterio o menopausia?"
    )
    ha_escuchado_programa_climaterio = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Ha escuchado hablar del Programa de Climaterio o atención relacionada con menopausia en centros de salud públicos?"
    )
    sabe_donde_acudir = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Sabe dónde acudir para recibir orientación o atención relacionada con síntomas del climaterio o menopausia?"
    )
    ha_consultado_por_sintomas = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Ha consultado alguna vez en un centro de salud por síntomas relacionados con climaterio o menopausia?"
    )
    evaluacion_atencion_recibida = models.CharField(
        max_length=10,
        choices=CalidadAtencion.choices,
        null=True, blank=True,
        help_text="Si respondió 'Sí', ¿cómo evaluaría la atención recibida?"
    )
    considera_informacion_suficiente = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Considera que el sistema de salud entrega suficiente información sobre climaterio o menopausia?"
    )
    nivel_informacion_servicios = models.CharField(
        max_length=10,
        choices=NivelInformacion.choices,
        null=True, blank=True,
        help_text="¿Qué tan informada se considera respecto a los servicios disponibles para mujeres en climaterio o menopausia?"
    )
    recursos_conocidos = models.TextField(
        null=True, blank=True,
        help_text="¿Conoce alguno de los siguientes recursos o prestaciones? (Atención médica en APS/CESFAM, Controles ginecológicos, Terapia hormonal, Atención psicológica, Consejería en salud mental, Orientación nutricional, Programas de actividad física, No conozco prestaciones relacionadas). Guardar como lista separada por comas."
    )
    ha_tenido_dificultades_acceso = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Ha sentido dificultades para acceder a atención relacionada con esta etapa?"
    )
    principales_dificultades = models.TextField(
        null=True, blank=True,
        help_text="¿Cuáles han sido las principales dificultades? (Falta de información, Dificultad para obtener horas, Costos, Falta de especialistas, No saber dónde consultar, Minimización de síntomas, Horarios incompatibles, Otra). Guardar como lista separada por comas."
    )
    sintomas_tomados_en_serio = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Considera que los síntomas asociados al climaterio o menopausia son tomados en serio por los profesionales de salud?"
    )
    desea_mas_informacion_apoyo = models.CharField(
        max_length=10,
        choices=RespuestaSiNoInsegura.choices,
        null=True, blank=True,
        help_text="¿Le gustaría recibir más información o apoyo relacionado con esta etapa?"
    )
    tipo_informacion_apoyo_deseado = models.TextField(
        null=True, blank=True,
        help_text="¿Qué tipo de información o apoyo considera más necesario? (Información general, Salud mental, Nutrición, Actividad física, Manejo de síntomas, Atención ginecológica, Terapia hormonal, Apoyo laboral, Otro). Guardar como lista separada por comas."
    )

    class Meta:
        ordering = ['-fecha_evaluacion']
        verbose_name = "Conocimiento del Sistema"
        verbose_name_plural = "Conocimiento del Sistema"

    def __str__(self):
        return f"Conocimiento Sistema de {self.participante} - {self.fecha_evaluacion}"