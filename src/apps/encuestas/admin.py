from django.contrib import admin

from .models import (
    ActividadFisica,
    ConocimientoSistema,
    EvaluacionTrabajo,
    HabitosAlimenticios,
    Identificacion,
    MRS,
    SegmentoEMPA,
    TareasCuidado,
)

_SYNC = ('uuid_local', 'sincronizado_en')


class EvaluacionTrabajoInline(admin.StackedInline):
    model = EvaluacionTrabajo
    extra = 0
    readonly_fields = ('fecha_evaluacion',) + _SYNC


class TareasCuidadoInline(admin.StackedInline):
    model = TareasCuidado
    extra = 0
    readonly_fields = ('fecha_evaluacion',) + _SYNC


@admin.register(Identificacion)
class IdentificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'rut_hash_corto', 'edad', 'region', 'comuna', 'creado_en')
    list_filter = ('region_residencia', 'genero', 'trabaja_actualmente')
    search_fields = ('rut_hash', 'comuna')
    readonly_fields = ('rut_hash', 'usuario', 'creado_en', 'edad') + _SYNC
    inlines = (EvaluacionTrabajoInline, TareasCuidadoInline)

    @admin.display(description='RUT (hash)')
    def rut_hash_corto(self, obj):
        return (obj.rut_hash[:12] + '…') if obj.rut_hash else '—'

    @admin.display(description='Región')
    def region(self, obj):
        return obj.get_region_residencia_display()


@admin.register(MRS)
class MRSAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'fecha_evaluacion', 'puntaje_total',
                    'menstruacion_ausente')
    list_filter = ('fecha_evaluacion',)
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion', 'puntaje_total',
                       'meses_desde_ultima_menstruacion', 'menstruacion_ausente') + _SYNC

    @admin.display(boolean=True, description='Ausencia menstrual (≥12 meses)')
    def menstruacion_ausente(self, obj):
        return obj.menstruacion_ausente


@admin.register(SegmentoEMPA)
class SegmentoEMPAAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'fecha_registro', 'origen_registro',
                    'imc', 'perdida_talla_cm')
    list_filter = ('origen_registro', 'fecha_registro', 'riesgo_cv_atp3')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_registro', 'imc', 'perdida_talla_cm',
                       'presion_arterial_str') + _SYNC


@admin.register(ConocimientoSistema)
class ConocimientoSistemaAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'fecha_evaluacion',
                    'en_control_programa_consultorio')
    list_filter = ('fecha_evaluacion', 'en_control_programa_consultorio')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC


@admin.register(EvaluacionTrabajo)
class EvaluacionTrabajoAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'fecha_evaluacion')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC


@admin.register(TareasCuidado)
class TareasCuidadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'cuida_otras_personas',
                    'mas_de_una_persona_a_cargo', 'doble_carga')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion', 'doble_carga') + _SYNC

    @admin.display(boolean=True, description='Doble carga')
    def doble_carga(self, obj):
        return obj.doble_carga


@admin.register(ActividadFisica)
class ActividadFisicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'fecha_evaluacion', 'dias_ejercicio_semana')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC


@admin.register(HabitosAlimenticios)
class HabitosAlimenticiosAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'fecha_evaluacion', 'quien_prepara_comidas')
    list_select_related = ('participante',)
    raw_id_fields = ('participante',)
    readonly_fields = ('fecha_evaluacion',) + _SYNC
