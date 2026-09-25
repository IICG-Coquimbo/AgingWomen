"""
Tablero de la usuaria (Fase 15, parte sin caracterización): sus propios
datos de identificación, el historial de rondas ya respondidas y el puntaje
MRS crudo de cada una. El "grupo de caracterización" queda pendiente del
algoritmo del equipo de investigación (decisión del 2026-09-24).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .historial import construir_historial
from .models import Identificacion


@login_required
def mi_tablero(request):
    if request.user.es_profesional:
        return redirect('buscar_paciente')

    paciente = Identificacion.objects.filter(usuario=request.user).first()
    rondas = construir_historial(paciente) if paciente else []

    return render(request, 'encuestas/mi_tablero.html', {
        'paciente': paciente,
        'rondas': rondas,
    })
