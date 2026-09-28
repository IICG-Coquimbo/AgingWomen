"""
Retiro del estudio (Fase 23). La participante puede retirarse cuando quiera:
se eliminan TODAS sus respuestas (Identificación y, en cascada, todas las
secciones de todas las rondas y su evaluación de satisfacción) y se reinicia
su consentimiento. La cuenta de acceso se conserva, por si cambia de opinión.
"""
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .models import Identificacion


@login_required
def retirarse(request):
    if request.user.es_profesional:
        return redirect('buscar_paciente')

    error = None
    if request.method == 'POST':
        if request.POST.get('entiendo') == 'on':
            with transaction.atomic():
                Identificacion.objects.filter(usuario=request.user).delete()
                request.user.consentimiento_aceptado_en = None
                request.user.save(update_fields=['consentimiento_aceptado_en'])
            return render(request, 'encuestas/retirado.html')
        error = 'Marca la casilla para confirmar que entiendes lo que se eliminará.'

    return render(request, 'encuestas/retirarse.html', {'error': error})
