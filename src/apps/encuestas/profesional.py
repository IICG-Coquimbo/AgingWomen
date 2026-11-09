"""
Panel de personal de salud (Fase 16): búsqueda de pacientes por RUT y ficha
con su historial de rondas. El ingreso de datos clínicos (EMPA) sigue
ocurriendo en /encuesta/, indicando el RUT de la paciente ahí mismo (Fase 6);
esta pantalla es solo de consulta del historial ya guardado.

Fase 40C-P: las estadísticas agregadas de la Fase 17 se reemplazan por el tablero
«Estadísticas generales» (apps.encuestas.estadisticas).
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.decorators import requiere_profesional
from apps.usuarios.privacidad import (
    MENSAJE_SIN_CONSENTIMIENTO_PACIENTE, ficha_sin_consentimiento, participacion_paciente, sin_consentimiento_vigente,
)
from apps.usuarios.rut import hash_rut, normalizar_rut, validar_rut

from .estadisticas import construir_estadisticas
from .evolucion import construir_evolucion
from .historial import construir_historial
from .models import Identificacion


@login_required
@requiere_profesional
def buscar_paciente(request):
    # Fase 40 (R-2): el RUT llega solo por POST con CSRF; nunca en la URL ni en los registros.
    rut = request.POST.get('rut', '').strip() if request.method == 'POST' else ''
    resultado = None
    error = None
    if rut:
        if not validar_rut(rut):
            error = 'El RUT ingresado no es válido.'
        else:
            resultado = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
            if resultado is None:
                error = 'No hay ninguna paciente registrada con ese RUT todavía.'

    valido = bool(rut) and validar_rut(rut)
    # Fase 40, Etapa 2: sin consentimiento vigente se ofrece registrar el consentimiento presencial.
    sin_consentimiento = valido and (ficha_sin_consentimiento(resultado) if resultado
                                     else sin_consentimiento_vigente(hash_rut(rut)))
    return render(request, 'encuestas/buscar_paciente.html', {
        'rut': rut, 'resultado': resultado, 'error': error,
        # Fase 29: RUT válido sin ficha -> se ofrece registrar a la paciente (con consentimiento vigente).
        'puede_registrar': valido and resultado is None and not sin_consentimiento,
        'sin_consentimiento': sin_consentimiento,
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
    if ficha_sin_consentimiento(paciente):   # Fase 40 (P7)
        return render(request, 'encuestas/buscar_paciente.html',
                      {'rut': '', 'resultado': None, 'error': MENSAJE_SIN_CONSENTIMIENTO_PACIENTE}, status=403)
    return render(request, 'encuesta.html', {
        'modo_profesional': True,
        'paciente': paciente,
        'contexto': f'prof:{request.user.rut_hash}:pac:{paciente.pk}',
        # Fase 40: la participación de la paciente viaja con lo que se envíe por ella.
        'participacion_paciente': participacion_paciente(paciente.rut_hash, usuario_id=paciente.usuario_id),
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
    if sin_consentimiento_vigente(hash_rut(rut)):   # Fase 40 (P7; Etapa 2: también sin cuenta)
        return render(request, 'encuestas/buscar_paciente.html',
                      {'rut': '', 'resultado': None, 'error': MENSAJE_SIN_CONSENTIMIENTO_PACIENTE}, status=403)
    existente = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
    if existente:
        return redirect('encuesta_paciente', identificacion_id=existente.pk)
    return render(request, 'encuesta.html', {
        'modo_profesional': True,
        'rut_nueva': normalizar_rut(rut),
        'contexto': f'prof:{request.user.rut_hash}:nueva:{hash_rut(rut)}',
        'participacion_paciente': participacion_paciente(hash_rut(rut)),
    })


@login_required
@requiere_profesional
def ficha_paciente(request, identificacion_id):
    paciente = get_object_or_404(Identificacion, pk=identificacion_id)
    rondas = construir_historial(paciente)
    return render(request, 'encuestas/ficha_paciente.html', {
        'paciente': paciente,
        # Fase 40: registro sin consentimiento vigente (p. ej., presencial antiguo sin constancia):
        # se conserva sin cambios, fuera de las estadísticas y sin respuestas nuevas.
        'sin_consentimiento': ficha_sin_consentimiento(paciente),
        'rondas': rondas,
        'evolucion': construir_evolucion(rondas),   # Fase 40C: mismo componente que el tablero
    })


@login_required
@requiere_profesional
def estadisticas(request):
    """
    Fase 40C-P: «Estadísticas generales». Solo agregados, con el umbral de celdas
    pequeñas de apps.encuestas.estadisticas; nunca identidades ni respuestas individuales.
    El permiso se revisa aquí, en el servidor (@requiere_profesional).
    """
    response = render(request, 'encuestas/estadisticas.html', {'est': construir_estadisticas()})
    response['Cache-Control'] = 'no-store'
    return response
