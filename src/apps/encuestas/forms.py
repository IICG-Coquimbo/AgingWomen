from datetime import date

from django import forms

from apps.usuarios.models import Usuario

from . import campos_por_rol
from .datos_geograficos import COMUNAS_POR_REGION
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
            'excepcion_edad',
        )

    EDAD_MINIMA = 40
    EDAD_MAXIMA = 60

    def clean(self):
        cleaned = super().clean()
        if 'excepcion_edad' in cleaned and not cleaned['excepcion_edad']:
            cleaned['excepcion_edad'] = Identificacion.ExcepcionEdad.NINGUNA

        region = cleaned.get('region_residencia')
        comuna = cleaned.get('comuna')
        if region and comuna and region != '99':
            validas = COMUNAS_POR_REGION.get(region, [])
            if validas and comuna not in validas:
                self.add_error('comuna', 'La comuna no corresponde a la región seleccionada.')

        # Filtro de edad: el estudio es para personas de 40 a 60 años. Las
        # excepciones (menopausia quirúrgica / ausencia prolongada) solo
        # permiten entrar con menos de 40; sobre 60 no hay excepción.
        nacimiento = cleaned.get('fecha_nacimiento')
        if nacimiento:
            hoy = date.today()
            edad = hoy.year - nacimiento.year - (
                (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day)
            )
            excepcion = cleaned.get('excepcion_edad') or Identificacion.ExcepcionEdad.NINGUNA
            if edad > self.EDAD_MAXIMA:
                self.add_error(
                    'fecha_nacimiento',
                    f'El estudio está dirigido a personas de {self.EDAD_MINIMA} a '
                    f'{self.EDAD_MAXIMA} años.',
                )
            elif edad < self.EDAD_MINIMA and excepcion == Identificacion.ExcepcionEdad.NINGUNA:
                self.add_error(
                    'fecha_nacimiento',
                    f'El estudio está dirigido a personas de {self.EDAD_MINIMA} a '
                    f'{self.EDAD_MAXIMA} años, salvo que declare menopausia quirúrgica o '
                    f'ausencia prolongada de menstruación.',
                )
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


class HabitosDeVidaForm(EncuestaModelForm):
    class Meta:
        model = HabitosDeVida
        exclude = ('participante', 'fecha_evaluacion')


class SegmentoEMPAForm(EncuestaModelForm):
    class Meta:
        model = SegmentoEMPA
        exclude = ('participante', 'fecha_registro', 'origen_registro')


class ConocimientoSistemaForm(EncuestaModelForm):
    class Meta:
        model = ConocimientoSistema
        exclude = ('participante', 'fecha_evaluacion')


class EvaluacionSatisfaccionForm(forms.ModelForm):
    """Evaluación de la plataforma (Fase 22). Formulario Django normal, no del esquema."""

    class Meta:
        model = EvaluacionSatisfaccion
        fields = (
            'facilidad_uso', 'fatiga_mental', 'comodidad_diseno',
            'recomendaria', 'incomodidad', 'comentario_incomodidad',
        )
        labels = {
            campo: EvaluacionSatisfaccion._meta.get_field(campo).help_text
            for campo in fields[:-1]
        }
        labels['comentario_incomodidad'] = 'Si respondiste Sí, cuéntanos cuál pregunta o por qué'
        widgets = {
            campo: forms.RadioSelect for campo in fields[:-1]
        }
        widgets['comentario_incomodidad'] = forms.Textarea(attrs={'rows': 3})
        help_texts = {campo: '' for campo in fields}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sin la opción vacía "---------" en los radios.
        for campo in self.Meta.fields[:-1]:
            self.fields[campo].choices = [
                c for c in self.fields[campo].choices if c[0] != ''
            ]

    def clean(self):
        cleaned = super().clean()
        comentario = (cleaned.get('comentario_incomodidad') or '').strip()
        if cleaned.get('incomodidad') == 'SI' and not comentario:
            self.add_error(
                'comentario_incomodidad',
                'Cuéntanos brevemente qué pregunta te generó incomodidad o confusión.',
            )
        cleaned['comentario_incomodidad'] = comentario
        return cleaned
