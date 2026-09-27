from django.contrib import admin

from .models import (
    ActividadFisica,
    ConocimientoSistema,
    EvaluacionSatisfaccion,
    EvaluacionTrabajo,
    HabitosDeVida,
    Identificacion,
    MRS,
    SegmentoEMPA,
    TareasCuidado,
)

_SYNC = ('uuid_local', 'sincronizado_en')
_SYNC_RONDA = _SYNC + ('ronda',)


class EvaluacionTrabajoInline(admin.StackedInline):
    model = EvaluacionTrabajo
    extra = 0
    readonly_fields = ('fecha_evaluacion',) + _SYNC_RONDA


class TareasCuidadoInline(admin.StackedInline):
    model = TareasCuidado
    extra = 0
    readonly_fields = ('fecha_evaluacion',) + _SYNC_RONDA


@admin.register(Identificacion)
class IdentificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'rut_hash_corto', 'edad', 'region', 'comuna', 'ronda_actual', 'creado_en')
    list_filter = ('region_residencia', 'genero', 'trabaja_actualmente')
    search_fields = ('rut_hash', 'comuna')
    readonly_fields = ('rut_hash', 'usuario', 'creado_en', 'edad', 'ronda_actual') + _SYNC
    inlines = (EvaluacionTrabajoInline, TareasCuidadoInline)

    @admin.display(description='RUT (hash)')
    def rut_hash_corto(self, obj):
        return (obj.rut_hash[:12] + '…') if obj.rut_hash else '—'

    @admin.display(description='Región')
    def region(self, obj):
        return obj.get_region_residencia_display()


@admin.register(MRS)
class MRSAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'fecha_evaluacion', 'puntaje_total',
                    'menstruacion_ausente')
    list_filter = ('fecha_evaluacion', 'ronda')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion', 'puntaje_total',
                       'meses_desde_ultima_menstruacion', 'menstruacion_ausente') + _SYNC_RONDA

    @admin.display(boolean=True, description='Ausencia menstrual (≥12 meses)')
    def menstruacion_ausente(self, obj):
        return obj.menstruacion_ausente


@admin.register(SegmentoEMPA)
class SegmentoEMPAAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'fecha_registro', 'origen_registro',
                    'imc', 'perdida_talla_cm')
    list_filter = ('origen_registro', 'fecha_registro', 'riesgo_cv_atp3', 'ronda')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_registro', 'imc', 'perdida_talla_cm',
                       'presion_arterial_str') + _SYNC_RONDA


@admin.register(ConocimientoSistema)
class ConocimientoSistemaAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'fecha_evaluacion',
                    'en_control_programa_consultorio')
    list_filter = ('fecha_evaluacion', 'en_control_programa_consultorio', 'ronda')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC_RONDA


@admin.register(EvaluacionTrabajo)
class EvaluacionTrabajoAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'fecha_evaluacion', 'estres_entorno_laboral')
    list_filter = ('ronda',)
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC_RONDA


@admin.register(TareasCuidado)
class TareasCuidadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'cuida_otras_personas',
                    'cantidad_personas_cuida', 'doble_carga')
    list_filter = ('ronda',)
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion', 'doble_carga') + _SYNC_RONDA

    @admin.display(boolean=True, description='Doble carga')
    def doble_carga(self, obj):
        return obj.doble_carga


@admin.register(ActividadFisica)
class ActividadFisicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'fecha_evaluacion', 'dias_ejercicio_semana')
    list_filter = ('ronda',)
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC_RONDA


@admin.register(HabitosDeVida)
class HabitosDeVidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'ronda', 'fecha_evaluacion', 'quien_prepara_comidas')
    list_filter = ('ronda',)
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC_RONDA


@admin.register(EvaluacionSatisfaccion)
class EvaluacionSatisfaccionAdmin(admin.ModelAdmin):
    list_display = ('participante', 'facilidad_uso', 'fatiga_mental', 'comodidad_diseno',
                    'recomendaria', 'incomodidad', 'actualizada_en')
    list_filter = ('recomendaria', 'incomodidad')
    raw_id_fields = ('participante',)
    readonly_fields = ('respondida_en', 'actualizada_en')
