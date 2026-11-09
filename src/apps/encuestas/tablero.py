"""
Tablero de la usuaria (Fase 15, parte sin caracterización): sus propios
datos de identificación, el historial de rondas ya respondidas y el puntaje
MRS crudo de cada una. Desde la Fase 40D-H también muestra el grupo de
caracterización B1, exploratorio y con advertencia (contexto_participante.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import EvaluacionSatisfaccionForm
from .contexto_participante import grupo_para_tablero
from .evolucion import construir_evolucion
from .historial import construir_historial
from .orientaciones import seleccionar as seleccionar_orientaciones
from .models import EvaluacionSatisfaccion, Identificacion
from .plazo import encuesta_bloqueada, mensaje_espera


def _puede_evaluar(paciente):
    """La evaluación se habilita tras finalizar al menos una ronda."""
    return paciente is not None and paciente.ronda_actual > 1


@login_required
def mi_tablero(request):
    if request.user.es_profesional:
        return redirect('buscar_paciente')

    paciente = Identificacion.objects.filter(usuario=request.user).first()
    rondas = construir_historial(paciente) if paciente else []

    return render(request, 'encuestas/mi_tablero.html', {
        'paciente': paciente,
        'rondas': rondas,
        'evolucion': construir_evolucion(rondas),   # Fase 40C
        'orientaciones': seleccionar_orientaciones(rondas) if paciente else None,   # Fase 40D
        'mi_grupo': grupo_para_tablero(rondas) if paciente else None,   # Fase 40D-H
        'puede_evaluar': _puede_evaluar(paciente),
        'evaluacion': EvaluacionSatisfaccion.objects.filter(participante=paciente).first()
        if paciente else None,
        'espera_encuesta': mensaje_espera(paciente) if encuesta_bloqueada(paciente) else None,
    })


@login_required
def mi_evaluacion(request):
    """Evaluación de satisfacción con la plataforma (Fase 22)."""
    if request.user.es_profesional:
        return redirect('buscar_paciente')

    paciente = Identificacion.objects.filter(usuario=request.user).first()
    if not _puede_evaluar(paciente):
        messages.info(request, 'Podrás evaluar la plataforma después de finalizar la encuesta.')
        return redirect('mi_tablero')

    evaluacion = EvaluacionSatisfaccion.objects.filter(participante=paciente).first()
    form = EvaluacionSatisfaccionForm(request.POST or None, instance=evaluacion)
    if request.method == 'POST' and form.is_valid():
        form.instance.participante = paciente
        form.save()
        messages.success(request, '¡Gracias! Tu evaluación quedó registrada.')
        return redirect('mi_tablero')

    return render(request, 'encuestas/mi_evaluacion.html', {
        'form': form, 'editando': evaluacion is not None,
    })
