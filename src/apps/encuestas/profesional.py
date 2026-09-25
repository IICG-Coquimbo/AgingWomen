"""
Panel de personal de salud (Fase 16): búsqueda de pacientes por RUT y ficha
con su historial de rondas. El ingreso de datos clínicos (EMPA) sigue
ocurriendo en /encuesta/, indicando el RUT de la paciente ahí mismo (Fase 6);
esta pantalla es solo de consulta del historial ya guardado.

No incluye "grupo de caracterización" ni estadísticas agregadas: esos
algoritmos todavía no están definidos por el equipo de investigación
(decisión del 2026-09-24), quedan para una fase futura.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.usuarios.decorators import requiere_profesional
from apps.usuarios.rut import hash_rut, validar_rut

from .historial import construir_historial
from .models import Identificacion


@login_required
@requiere_profesional
def buscar_paciente(request):
    rut = request.GET.get('rut', '').strip()
    resultado = None
    error = None
    if rut:
        if not validar_rut(rut):
            error = 'El RUT ingresado no es válido.'
        else:
            resultado = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
            if resultado is None:
                error = 'No hay ninguna paciente registrada con ese RUT todavía.'

    return render(request, 'encuestas/buscar_paciente.html', {
        'rut': rut, 'resultado': resultado, 'error': error,
    })


@login_required
@requiere_profesional
def ficha_paciente(request, identificacion_id):
    paciente = get_object_or_404(Identificacion, pk=identificacion_id)
    return render(request, 'encuestas/ficha_paciente.html', {
        'paciente': paciente,
        'rondas': construir_historial(paciente),
    })
