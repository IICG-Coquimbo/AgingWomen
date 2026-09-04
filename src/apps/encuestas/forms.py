from django import forms

from apps.usuarios.models import Usuario

from . import campos_por_rol
from .datos_geograficos import COMUNAS_POR_REGION
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


class EncuestaModelForm(forms.ModelForm):
    """
    Base de los formularios de encuesta. Ajusta visibilidad y obligatoriedad
    de los campos según el rol de quien responde (regla 3.1 del spec).

    Uso: ``SegmentoEMPAForm(data, rol=request.user.rol)``.
      - USUARIA: se quitan los campos SOLO_PROFESIONAL y se relajan (required=False)
        los OPCIONALES_USUARIA.
      - PROFESIONAL: todos los campos presentes; se marcan required los
        REQUERIDOS_PROFESIONAL.
      - Sin rol: comportamiento por defecto del modelo.

    ``parcial=True`` (sincronización offline de una sección a medio contestar):
    ningún campo es obligatorio; solo se validan los valores que sí llegaron.
    """

    def __init__(self, *args, rol=None, parcial=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.rol = rol
        self.parcial = parcial
        nombre_modelo = self._meta.model.__name__

        if rol == Usuario.Rol.USUARIA_COMUN:
            for campo in campos_por_rol.SOLO_PROFESIONAL.get(nombre_modelo, []):
                self.fields.pop(campo, None)
            for campo in campos_por_rol.OPCIONALES_USUARIA.get(nombre_modelo, []):
                if campo in self.fields:
                    self.fields[campo].required = False

        elif rol == Usuario.Rol.PROFESIONAL_SALUD:
            for campo in campos_por_rol.REQUERIDOS_PROFESIONAL.get(nombre_modelo, []):
                if campo in self.fields:
                    self.fields[campo].required = True

        if parcial:
            for campo in self.fields.values():
                campo.required = False


class IdentificacionForm(EncuestaModelForm):
    class Meta:
        model = Identificacion
        # Orden explícito: la región va antes de la comuna (la comuna depende de ella).
        fields = (
            'fecha_nacimiento', 'genero', 'nivel_educacion', 'origen_procedencia',
            'pueblo_originario_afro', 'region_residencia', 'comuna', 'trabaja_actualmente',
        )

    def clean(self):
        cleaned = super().clean()
        region = cleaned.get('region_residencia')
        comuna = cleaned.get('comuna')
        if region and comuna and region != '99':
            validas = COMUNAS_POR_REGION.get(region, [])
            if validas and comuna not in validas:
                self.add_error('comuna', 'La comuna no corresponde a la región seleccionada.')
        return cleaned


class MRSForm(EncuestaModelForm):
    class Meta:
        model = MRS
        exclude = ('participante', 'fecha_evaluacion')


class EvaluacionTrabajoForm(EncuestaModelForm):
    class Meta:
        model = EvaluacionTrabajo
        exclude = ('participante', 'fecha_evaluacion')


class TareasCuidadoForm(EncuestaModelForm):
    class Meta:
        model = TareasCuidado
        exclude = ('participante', 'fecha_evaluacion')


class ActividadFisicaForm(EncuestaModelForm):
    class Meta:
        model = ActividadFisica
        exclude = ('participante', 'fecha_evaluacion')


class HabitosAlimenticiosForm(EncuestaModelForm):
    class Meta:
        model = HabitosAlimenticios
        exclude = ('participante', 'fecha_evaluacion')


class SegmentoEMPAForm(EncuestaModelForm):
    class Meta:
        model = SegmentoEMPA
        exclude = ('participante', 'fecha_registro', 'origen_registro')


class ConocimientoSistemaForm(EncuestaModelForm):
    class Meta:
        model = ConocimientoSistema
        exclude = ('participante', 'fecha_evaluacion')
