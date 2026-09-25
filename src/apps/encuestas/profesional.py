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

from .esquema import ORDEN_SECCIONES
from .models import Identificacion
from .sync import SECCIONES


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

    rondas = []
    for numero in range(1, paciente.ronda_actual + 1):
        secciones = []
        for tipo, titulo, _form_cls, _parte in ORDEN_SECCIONES:
            if tipo not in SECCIONES:
                continue  # 'identificacion' y 'mrs_complementario' no son secciones propias
            modelo, _form = SECCIONES[tipo]
            registro = modelo.objects.filter(participante=paciente, ronda=numero).first()
            fecha = None
            if registro is not None:
                fecha = getattr(registro, 'fecha_evaluacion', None) or getattr(registro, 'fecha_registro', None)
            secciones.append({'titulo': titulo, 'registro': registro, 'fecha': fecha})
        rondas.append({
            'numero': numero,
            'secciones': secciones,
            'es_actual': numero == paciente.ronda_actual,
        })
    rondas.reverse()  # ronda más reciente primero

    return render(request, 'encuestas/ficha_paciente.html', {
        'paciente': paciente,
        'rondas': rondas,
    })
