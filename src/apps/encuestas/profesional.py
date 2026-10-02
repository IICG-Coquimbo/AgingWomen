"""
Panel de personal de salud (Fase 16): búsqueda de pacientes por RUT y ficha
con su historial de rondas. El ingreso de datos clínicos (EMPA) sigue
ocurriendo en /encuesta/, indicando el RUT de la paciente ahí mismo (Fase 6);
esta pantalla es solo de consulta del historial ya guardado.

Fase 17 (versión básica): estadísticas agregadas y anónimas. El "grupo de
caracterización" sigue pendiente del algoritmo del equipo de investigación;
las estadísticas se ampliarán cuando haya datos reales.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.decorators import requiere_profesional
from apps.usuarios.rut import hash_rut, normalizar_rut, validar_rut

from .historial import construir_historial
from .models import MRS, Identificacion, SegmentoEMPA

# Umbral habitual de hipertensión (mmHg): sistólica ≥140 o diastólica ≥90.
SISTOLICA_ALTA = 140
DIASTOLICA_ALTA = 90


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
        # Fase 29: RUT válido sin ficha -> se ofrece registrar a la paciente.
        'puede_registrar': bool(rut) and resultado is None and validar_rut(rut),
    })


@login_required
@requiere_profesional
def encuesta_paciente(request, identificacion_id):
    """
    Fase 29: el personal de salud completa (o corrige) la encuesta de una
    paciente, precargada con lo que ella ya respondió en la ronda en curso.
    Si la paciente creó su propia cuenta, su Identificación queda bloqueada.
    """
    paciente = get_object_or_404(Identificacion, pk=identificacion_id)
    return render(request, 'encuesta.html', {
        'modo_profesional': True,
        'paciente': paciente,
        'contexto': f'prof:{request.user.rut_hash}:pac:{paciente.pk}',
    })


@login_required
@requiere_profesional
@require_POST
def nueva_paciente(request):
    """
    Fase 29: registrar una paciente que aún no tiene ficha. El RUT llega por
    POST (no queda en la URL ni en los registros del servidor) y se pasa a la
    encuesta, que lo envía al guardar por primera vez.
    """
    rut = request.POST.get('rut', '').strip()
    if not validar_rut(rut):
        return redirect('buscar_paciente')
    existente = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
    if existente:
        return redirect('encuesta_paciente', identificacion_id=existente.pk)
    return render(request, 'encuesta.html', {
        'modo_profesional': True,
        'rut_nueva': normalizar_rut(rut),
        'contexto': f'prof:{request.user.rut_hash}:nueva:{hash_rut(rut)}',
    })


@login_required
@requiere_profesional
def ficha_paciente(request, identificacion_id):
    paciente = get_object_or_404(Identificacion, pk=identificacion_id)
    return render(request, 'encuestas/ficha_paciente.html', {
        'paciente': paciente,
        'rondas': construir_historial(paciente),
    })


def _con_presion_alta():
    """
    Cantidad de participantes cuya presión MÁS RECIENTE (último EMPA con
    presión registrada, por ronda) está alta. Se cuentan personas, no
    registros: con rondas, una misma persona puede tener varios EMPA.
    """
    registros = (
        SegmentoEMPA.objects
        .exclude(presion_sistolica__isnull=True, presion_diastolica__isnull=True)
        .order_by('participante_id', '-ronda', '-id')
        .values_list('participante_id', 'presion_sistolica', 'presion_diastolica')
    )
    vistos = set()
    total = 0
    for participante_id, sistolica, diastolica in registros:
        if participante_id in vistos:
            continue
        vistos.add(participante_id)
        if (sistolica or 0) >= SISTOLICA_ALTA or (diastolica or 0) >= DIASTOLICA_ALTA:
            total += 1
    return total


@login_required
@requiere_profesional
def estadisticas(request):
    edades = [p.edad for p in Identificacion.objects.only('fecha_nacimiento')]
    return render(request, 'encuestas/estadisticas.html', {
        'total_participantes': len(edades),
        'edad_promedio': round(sum(edades) / len(edades), 1) if edades else None,
        'presion_alta': _con_presion_alta(),
        'total_mrs': MRS.objects.count(),
        'sistolica_alta': SISTOLICA_ALTA,
        'diastolica_alta': DIASTOLICA_ALTA,
    })
