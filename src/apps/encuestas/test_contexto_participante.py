"""
Pruebas de la Fase 40D-G: grupo B1 como contexto exploratorio y adaptación por actividad física.
docker compose exec web python manage.py test apps.encuestas.test_contexto_participante
"""
import json
import re
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.test import override_settings

from apps.rondas.models import EventoRonda, TipoEventoRonda
from apps.rondas.test_40b2 import _pasar_plazo
from apps.rondas.test_40b3 import bloque_mrs, payload
from apps.usuarios.models import Usuario

from . import contexto_participante as C
from . import orientaciones as O
from .historial import construir_historial
from .models import MRS, Identificacion
from .sync import sincronizar_payload
from .test_orientaciones import ACTIVAS, Base40D, ids_principales, respuestas, seccion

DEFINICION_B1 = (Path(settings.BASE_DIR).parent / 'analisis' / 'fase37' / '37C_complemento_tres_preguntas'
                 / 'definiciones' / 'definicion_B1_B2.json')
CERO, UNA_DOS, TRES_CUATRO = 1, 2, 3


def bloque_actividad(dias):
    return {'tipo': 'actividad_fisica', 'uuid_local': str(uuid4()), 'datos': {'dias_ejercicio_semana': dias}}


class BaseG(Base40D):
    def ronda(self, numero, mrs, pareja='SI', dias=CERO, trabaja=True, usuaria=None, finalizar=True):
        """Guarda (y cierra) una ronda con MRS + pareja, actividad física opcional y «trabaja» en la ficha."""
        usuaria = usuaria or self.usuaria
        if numero > 1:
            _pasar_plazo()
        datos = dict(mrs)
        if pareja is not None:
            datos['tiene_pareja'] = pareja
        bloques = [bloque_mrs(datos, parcial=False)]
        if dias is not None:
            bloques.append(bloque_actividad(dias))
        p = payload(bloques, ronda=numero, finalizar=finalizar)
        p['identificacion']['datos']['trabaja_actualmente'] = trabaja
        res = sincronizar_payload(usuaria, p)
        self.assertTrue(res['ok'], res)
        if finalizar:
            self.assertEqual(res['cierre']['estado'], 'cerrada', res)

    def seleccion(self, usuaria=None):
        ficha = Identificacion.objects.get(usuario=usuaria or self.usuaria)
        return O.seleccionar(construir_historial(ficha))

    def tablero_de(self, usuaria):
        self.client.force_login(usuaria)
        return self.client.get('/mi-tablero/').content.decode()


class ReglaB1Test(BaseG):
    def test_mapa_identico_a_la_definicion_documentada(self):
        if not DEFINICION_B1.exists():
            self.skipTest('analisis/ no está disponible en este entorno')
        definicion = json.loads(DEFINICION_B1.read_text(encoding='utf-8'))
        self.assertEqual(definicion['variables'], ['trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana'])
        self.assertEqual(list(C.MAPA_B1), definicion['B1']['mapa'])

    def test_mapa_equivale_a_la_regla_de_cuatro_pasos(self):
        for trabaja in (False, True):
            for pareja in ('NO', 'SI'):
                for dias in range(1, 6):
                    esperado = ('S1' if dias >= TRES_CUATRO else 'S0' if pareja == 'NO'
                                else 'S2' if not trabaja else 'S3')
                    self.assertEqual(C.grupo_b1(trabaja, pareja, dias), esperado, (trabaja, pareja, dias))

    def test_sin_variable_no_se_asigna_grupo(self):
        for args in ((None, 'SI', 1), (True, None, 1), (True, 'SI', None), (True, 'NS', 1), (True, 'SI', 9)):
            self.assertIsNone(C.grupo_b1(*args), args)


@override_settings(**ACTIVAS)
class AsignacionTest(BaseG):
    def test_asignacion_reproducible_en_la_ronda_de_referencia(self):
        self.ronda(1, respuestas(p3=3), pareja='SI', dias=UNA_DOS, trabaja=True)
        a, b = self.seleccion(), self.seleccion()
        self.assertEqual(a['contexto_exploratorio'], {'grupo_b1': 'S3', 'faltantes': [], 'ronda': 1})
        self.assertEqual(a['contexto_exploratorio'], b['contexto_exploratorio'])

    def test_faltan_variables(self):
        self.ronda(1, respuestas(p3=3), pareja=None, dias=None, trabaja=None)
        ctx = self.seleccion()['contexto_exploratorio']
        self.assertIsNone(ctx['grupo_b1'])
        self.assertEqual(ctx['faltantes'], ['trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana'])

    def test_cierre_sin_foto_de_trabajo_no_asigna(self):
        """Cierres anteriores a la 40D-G no guardaron «trabaja»: no se usa el valor actual de la ficha."""
        self.ronda(1, respuestas(p3=3), trabaja=True)
        evento = EventoRonda.objects.get(tipo=TipoEventoRonda.CIERRE)
        datos = {k: v for k, v in evento.datos.items() if k != 'contexto'}
        EventoRonda.objects.filter(pk=evento.pk).update(datos=datos)   # simula un cierre antiguo
        ctx = self.seleccion()['contexto_exploratorio']
        self.assertIsNone(ctx['grupo_b1'])
        self.assertEqual(ctx['faltantes'], ['trabaja_actualmente'])

    def test_ronda_abierta_o_no_verificable_sin_contexto(self):
        self.ronda(1, respuestas(p3=3), finalizar=False)
        self.assertIsNone(self.seleccion()['contexto_exploratorio'])

    def test_cambios_entre_rondas_usan_los_datos_de_cada_ronda(self):
        self.ronda(1, respuestas(p3=3), pareja='SI', dias=CERO, trabaja=False)       # S2
        self.assertEqual(self.seleccion()['contexto_exploratorio']['grupo_b1'], 'S2')
        # En la ronda 2 (abierta) cambia «trabaja»: la ronda 1 conserva su valor al cierre.
        self.ronda(2, respuestas(p3=3), pareja='NO', dias=CERO, trabaja=True, finalizar=False)
        self.assertEqual(self.seleccion()['contexto_exploratorio'], {'grupo_b1': 'S2', 'faltantes': [], 'ronda': 1})
        _pasar_plazo()
        self.ronda(2, respuestas(p3=3), pareja='NO', dias=TRES_CUATRO, trabaja=True)  # S1
        self.assertEqual(self.seleccion()['contexto_exploratorio'], {'grupo_b1': 'S1', 'faltantes': [], 'ronda': 2})

    def test_separacion_de_participantes(self):
        otra = Usuario.objects.create_user(rut='33.333.333-3', email='o@e.cl')
        self.ronda(1, respuestas(p3=3), pareja='NO', dias=CERO, trabaja=True)                   # S0
        self.ronda(1, respuestas(p3=3), pareja='SI', dias=TRES_CUATRO, trabaja=False, usuaria=otra)  # S1
        self.assertEqual(self.seleccion()['contexto_exploratorio']['grupo_b1'], 'S0')
        self.assertEqual(self.seleccion(otra)['contexto_exploratorio']['grupo_b1'], 'S1')
        self.assertIn('data-nota-contexto', seccion(self.tablero_de(self.usuaria)))
        self.assertNotIn('data-nota-contexto', seccion(self.tablero_de(otra)))


@override_settings(**ACTIVAS)
class AdaptacionTest(BaseG):
    def test_items_de_actividad_fisica_coinciden_con_el_catalogo(self):
        por_id = {o['id']: o for o in O.catalogo()['orientaciones']}
        for oid, i in C.ACTIVIDAD_FISICA_EN_TARJETA.items():
            item = por_id[oid]['autocuidado'][i]
            self.assertIn('actividad física', item['texto'], oid)
            self.assertTrue(item['fuentes'], oid)
        self.assertNotIn('O-01', C.ACTIVIDAD_FISICA_EN_TARJETA)   # F17: no se presenta como alivio de bochornos

    def test_cero_dias_destaca_la_medida_existente_sin_cambiar_la_seleccion(self):
        mrs = respuestas(p1=4, p3=4, p8=3)
        self.ronda(1, mrs, dias=CERO)
        sec = seccion(self.tablero())
        self.assertEqual(ids_principales(sec), ['O-01', 'O-03', 'O-08'])
        o03 = sec.split('data-orientacion="O-03"')[1].split('</article>')[0]
        self.assertIn('En tu ronda 1 indicaste que en una semana habitual no haces ejercicio.', o03)
        destacado = re.search(r'data-autocuidado-destacado>([^<]*)<', o03).group(1)
        self.assertIn('actividad física regular', destacado)
        o01 = sec.split('data-orientacion="O-01"')[1].split('</article>')[0]
        self.assertNotIn('data-nota-contexto', o01)
        biblioteca = sec.split('data-biblioteca-orientaciones')[1]
        self.assertNotIn('data-nota-contexto', biblioteca)

    def test_seleccion_igual_con_y_sin_contexto(self):
        mrs = respuestas(p5=4, p3=3, p6=2, p8=2, p10=2)
        otra = Usuario.objects.create_user(rut='33.333.333-3', email='o@e.cl')
        self.ronda(1, mrs, pareja='NO', dias=CERO, trabaja=True)
        self.ronda(1, mrs, pareja=None, dias=TRES_CUATRO, trabaja=None, usuaria=otra)
        a, b = self.seleccion(), self.seleccion(otra)
        for clave in ('principales', 'otras'):
            self.assertEqual([(t['orientacion']['id'], t['motivo']) for t in a[clave]],
                             [(t['orientacion']['id'], t['motivo']) for t in b[clave]])
        self.assertEqual(a['apoyo']['orientacion']['id'], 'O-05')
        self.assertTrue(a['apoyo']['nota_contexto'])          # el apoyo (O-05) también se adapta
        self.assertFalse(b['apoyo']['nota_contexto'])
        self.assertFalse(any(t['nota_contexto'] for t in b['principales'] + b['otras']))

    def test_uno_o_mas_dias_no_adapta(self):
        self.ronda(1, respuestas(p3=4), dias=UNA_DOS)
        self.assertNotIn('data-nota-contexto', seccion(self.tablero()))

    def test_orientaciones_no_mencionan_grupo_ni_estadistica_y_avisos_se_mantienen(self):
        # Se refiere al bloque de orientaciones: el grupo se muestra en su propia sección del tablero.
        self.ronda(1, respuestas(p3=4, p5=4), pareja='SI', dias=CERO, trabaja=True)
        sec = seccion(self.tablero())
        for vetada in (r'\bS[0-3]\b', r'B1', r'[Gg]rupo', r'[Ss]egmento', r'clúster', r'caracterizaci',
                       r'asociaci', r'estad[ií]stic', r'trabaj', r'pareja'):
            self.assertIsNone(re.search(vetada, re.sub(r'<article.*?</article>', '', sec, flags=re.S)), vetada)
            nota = ' '.join(re.findall(r'data-nota-contexto>([^<]*)<', sec))
            self.assertIsNone(re.search(vetada, nota), vetada)
        self.assertIn('data-aviso-orientaciones', sec)
        self.assertIn('data-aviso-borrador', sec)


class PilotoApagadoTest(BaseG):
    def test_apagado_no_calcula_ni_muestra(self):
        self.ronda(1, respuestas(p3=4), dias=CERO)
        self.assertIsNone(self.seleccion())
        self.assertEqual(seccion(self.tablero()), '')


def seccion_grupo(html):
    m = re.search(r'<section class="tarjeta mi-grupo".*?</section>', html, re.S)
    return m.group(0) if m else ''


class MiGrupoTest(BaseG):
    """Fase 40D-H: sección «Mi grupo de caracterización» del tablero (no depende del piloto 40D)."""

    def test_grupo_valido_con_nombre_aviso_y_mrs_aparte(self):
        self.ronda(1, respuestas(p1=4, p3=2), pareja='SI', dias=CERO, trabaja=True)   # S3, MRS 6
        sec = seccion_grupo(self.tablero())
        self.assertIn('Grupo 4 — Entre múltiples actividades', sec)
        self.assertIn('tienen pareja y actualmente trabajan', sec)
        self.assertIn('no es un diagnóstico ni un indicador de salud'.capitalize()[1:], sec)
        self.assertNotIn('S3', sec)
        mrs = sec.split('data-grupo-mrs')[1]
        self.assertIn('Puntaje MRS: 6 de 44', mrs)
        self.assertIn('no explica ni predice', mrs)
        self.assertNotIn('Puntaje MRS', sec.split('data-grupo-mrs')[0])

    def test_nombres_de_los_cuatro_grupos(self):
        esperados = {'S0': 'Bienestar a tu ritmo', 'S1': 'Vida en movimiento',
                     'S2': 'Equilibrio personal', 'S3': 'Entre múltiples actividades'}
        self.assertEqual({k: v[1] for k, v in C.GRUPOS_VISIBLES.items()}, esperados)
        self.assertEqual([C.GRUPOS_VISIBLES[k][0] for k in C.GRUPOS_B1], ['Grupo 1', 'Grupo 2', 'Grupo 3', 'Grupo 4'])

    def test_grupo_ausente(self):
        self.client.force_login(self.usuaria)
        self.ronda(1, respuestas(p3=3), finalizar=False)                       # ronda abierta
        self.assertIn('Grupo aún no disponible', seccion_grupo(self.tablero()))
        _pasar_plazo()
        self.ronda(1, respuestas(p3=3), pareja=None, dias=CERO, trabaja=True)  # falta pareja
        sec = seccion_grupo(self.tablero())
        self.assertIn('Grupo aún no disponible', sec)
        self.assertNotIn('data-grupo-nombre', sec)
        self.assertNotIn('Puntaje MRS', sec)

    def test_no_infiere_de_datos_actuales(self):
        self.ronda(1, respuestas(p3=3), trabaja=True)
        evento = EventoRonda.objects.get(tipo=TipoEventoRonda.CIERRE)
        EventoRonda.objects.filter(pk=evento.pk).update(
            datos={k: v for k, v in evento.datos.items() if k != 'contexto'})
        self.assertIn('Grupo aún no disponible', seccion_grupo(self.tablero()))

    def test_coherencia_de_ronda(self):
        self.ronda(1, respuestas(p3=3), pareja='SI', dias=CERO, trabaja=False)               # S2, MRS 3
        self.ronda(2, respuestas(p3=4, p4=4), pareja='NO', dias=TRES_CUATRO, trabaja=True)   # S1, MRS 8
        sec = seccion_grupo(self.tablero())
        self.assertIn('Grupo 2 — Vida en movimiento', sec)
        self.assertIn('ronda 2', sec)
        self.assertIn('Puntaje MRS: 8 de 44', sec)
        self.assertNotIn('Puntaje MRS: 3 de 44', sec)
        # Ronda 3 abierta con otros datos: se mantiene la ronda 2.
        self.ronda(3, respuestas(p1=1), pareja='SI', dias=CERO, trabaja=False, finalizar=False)
        self.assertEqual(seccion_grupo(self.tablero()), sec)

    def test_acceso_entre_usuarias(self):
        otra = Usuario.objects.create_user(rut='33.333.333-3', email='o@e.cl')
        self.ronda(1, respuestas(p3=3), pareja='NO', dias=CERO, trabaja=True)                    # S0
        self.ronda(1, respuestas(p3=4), pareja='SI', dias=TRES_CUATRO, trabaja=False, usuaria=otra)  # S1
        mia, suya = seccion_grupo(self.tablero_de(self.usuaria)), seccion_grupo(self.tablero_de(otra))
        self.assertIn('Grupo 1 — Bienestar a tu ritmo', mia)
        self.assertNotIn('Vida en movimiento', mia)
        self.assertIn('Grupo 2 — Vida en movimiento', suya)
        self.assertNotIn('Bienestar a tu ritmo', suya)
        # La ficha profesional no muestra esta sección.
        self.client.force_login(self.prof)
        ficha = self.client.get(f'/profesional/paciente/{Identificacion.objects.get(usuario=self.usuaria).pk}/')
        self.assertEqual(seccion_grupo(ficha.content.decode()), '')


class MotivoSinGrupoTest(BaseG):
    """El tablero explica por qué no hay grupo. Solo informa: la regla no cambia."""

    def motivo(self):
        sec = seccion_grupo(self.tablero())
        self.assertIn('Grupo aún no disponible', sec)
        self.assertNotIn('data-grupo-nombre', sec)
        return sec

    def test_sin_ronda_finalizada(self):
        self.ronda(1, respuestas(p3=3), finalizar=False)
        self.assertIn('data-grupo-motivo="sin_ronda"', self.motivo())

    def test_faltan_datos_los_nombra(self):
        self.ronda(1, respuestas(p3=3), pareja=None, dias=None, trabaja=True)
        sec = self.motivo()
        self.assertIn('data-grupo-motivo="faltan_datos"', sec)
        self.assertIn('si tienes pareja', sec)
        self.assertIn('cuántos días haces ejercicio', sec)
        self.assertNotIn('si trabajas actualmente', sec)

    def test_no_sabe_pareja_cuenta_como_dato_faltante(self):
        self.ronda(1, respuestas(p3=3), pareja='SI', dias=CERO, trabaja=True)
        MRS.objects.update(tiene_pareja='NS')
        self.assertIn('si tienes pareja', self.motivo())

    def test_ronda_no_verificable(self):
        self.ronda(1, respuestas(p3=3), pareja='SI', dias=CERO, trabaja=True)
        MRS.objects.update(pregunta_5=None)
        self.assertIn('data-grupo-motivo="no_verificable"', self.motivo())
