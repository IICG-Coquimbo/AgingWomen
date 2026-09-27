import json
from datetime import date
from uuid import uuid4

from django.test import TestCase

from apps.usuarios.models import Usuario
from apps.usuarios.rut import hash_rut

from .forms import IdentificacionForm, MRSForm, SegmentoEMPAForm
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
    meses_desde_texto_fecha,
)
from .esquema import construir_esquema
from .sync import ErrorSincronizacion, sincronizar_payload


class SegmentoEMPAFormRolTest(TestCase):
    # Ocultos para la usuaria común (Sección 4/5 de los requisitos finales).
    OCULTOS_USUARIA = (
        'presion_sistolica', 'riesgo_cv_atp3', 'glicemia_mg_dl',
        'fecha_ultimo_pap', 'resultado_pap', 'fecha_mamografia', 'resultado_birads',
        'fecha_ecotomografia_mamaria', 'vdrl_rpr', 'talla_maxima_cm',
    )

    def test_usuaria_no_ve_campos_solo_profesional(self):
        form = SegmentoEMPAForm(rol=Usuario.Rol.USUARIA_COMUN)
        for campo in self.OCULTOS_USUARIA:
            self.assertNotIn(campo, form.fields, campo)

    def test_consumo_sustancias_ya_no_esta_en_empa(self):
        campos = SegmentoEMPAForm(rol=Usuario.Rol.PROFESIONAL_SALUD).fields
        self.assertNotIn('consumo_alcohol', campos)
        self.assertNotIn('consumo_tabaco', campos)

    def test_profesional_ve_todos_los_campos_clinicos(self):
        form = SegmentoEMPAForm(rol=Usuario.Rol.PROFESIONAL_SALUD)
        for campo in self.OCULTOS_USUARIA:
            self.assertIn(campo, form.fields, campo)

    def test_usuaria_campos_visibles_no_obligatorios(self):
        form = SegmentoEMPAForm(rol=Usuario.Rol.USUARIA_COMUN)
        for campo in ('circunferencia_cintura_cm', 'talla_actual_cm', 'peso_kg',
                      'fecha_ultimo_empa'):
            self.assertIn(campo, form.fields, campo)
            self.assertFalse(form.fields[campo].required, campo)

    def test_profesional_campos_requeridos(self):
        form = SegmentoEMPAForm(rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.assertTrue(form.fields['peso_kg'].required)
        self.assertTrue(form.fields['presion_sistolica'].required)

    def test_usuaria_puede_enviar_empa_vacio(self):
        form = SegmentoEMPAForm(data={}, rol=Usuario.Rol.USUARIA_COMUN)
        self.assertTrue(form.is_valid(), form.errors)

    def test_profesional_no_puede_enviar_empa_vacio(self):
        form = SegmentoEMPAForm(data={}, rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.assertFalse(form.is_valid())
        self.assertIn('peso_kg', form.errors)

    def test_empa_de_usuaria_se_guarda(self):
        ident = Identificacion.objects.create(
            fecha_nacimiento='1975-05-20',
            genero=Identificacion.GeneroOptions.FEMENINO,
            nivel_educacion=Identificacion.NivelEducativo.MEDIA_COM,
            comuna='Santiago',
        )
        form = SegmentoEMPAForm(data={'peso_kg': '68.5', 'talla_actual_cm': '160'},
                                rol=Usuario.Rol.USUARIA_COMUN)
        self.assertTrue(form.is_valid(), form.errors)
        empa = form.save(commit=False)
        empa.participante = ident
        empa.save()
        self.assertEqual(SegmentoEMPA.objects.count(), 1)
        self.assertEqual(empa.imc, 26.76)


class MRSFormTest(TestCase):
    def test_mrs_igual_para_ambos_roles(self):
        campos_usuaria = set(MRSForm(rol=Usuario.Rol.USUARIA_COMUN).fields)
        campos_prof = set(MRSForm(rol=Usuario.Rol.PROFESIONAL_SALUD).fields)
        self.assertEqual(campos_usuaria, campos_prof)

    def test_mrs_incluye_las_11_preguntas_y_el_complementario(self):
        campos = MRSForm().fields
        for i in range(1, 12):
            self.assertIn(f'pregunta_{i}', campos)
        self.assertIn('tipo_metodo_anticonceptivo', campos)
        self.assertIn('cambio_relacion_pareja_menopausia', campos)


class SincronizacionTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD,
        )
        self.ident_datos = {
            'fecha_nacimiento': '1975-05-20',
            'genero': 'F',
            'nivel_educacion': 'M_COM',
            'origen_procedencia': 'CL',
            'pueblo_originario_afro': 'NINGUNO',
            'comuna': 'Santiago',
            'region_residencia': '13',
        }

    def _payload_ident(self, **extra):
        return {'uuid_local': str(uuid4()), 'datos': dict(self.ident_datos, **extra)}

    def test_crea_identificacion_y_seccion(self):
        payload = {
            'identificacion': self._payload_ident(),
            'secciones': [{
                'tipo': 'trabajo', 'uuid_local': str(uuid4()), 'parcial': False,
                'datos': {'rendimiento_afectado': 3, 'bienestar_trabajo_afectado': 2,
                          'frecuencia_ausencias': 1, 'lugar_trabajo_comprensivo': 4},
            }],
        }
        res = sincronizar_payload(self.usuaria, payload)
        self.assertTrue(res['ok'], res)
        ident = Identificacion.objects.get()
        self.assertEqual(ident.usuario, self.usuaria)
        self.assertEqual(ident.rut_hash, self.usuaria.rut_hash)
        self.assertEqual(EvaluacionTrabajo.objects.count(), 1)

    def test_reenvio_no_duplica(self):
        u = str(uuid4())
        payload = {
            'identificacion': self._payload_ident(),
            'secciones': [{'tipo': 'tareas_cuidado', 'uuid_local': u, 'parcial': True,
                           'datos': {'cuida_otras_personas': 'SI',
                                     'cantidad_personas_cuida': 1}}],
        }
        sincronizar_payload(self.usuaria, payload)
        payload['secciones'][0]['datos']['cantidad_personas_cuida'] = 3
        res = sincronizar_payload(self.usuaria, payload)
        self.assertEqual(TareasCuidado.objects.count(), 1)
        self.assertEqual(res['resultados'][1]['estado'], 'actualizado')
        self.assertEqual(TareasCuidado.objects.get().cantidad_personas_cuida, 3)

    def test_tareas_cuidado_guarda_seleccion_multiple(self):
        payload = {
            'identificacion': self._payload_ident(),
            'secciones': [{'tipo': 'tareas_cuidado', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'cuida_otras_personas': 'SI', 'cantidad_personas_cuida': 2,
                                     'a_quien_cuida': 'Padres o suegros, Otro',
                                     'a_quien_cuida_otro': 'Un vecino'}}],
        }
        res = sincronizar_payload(self.usuaria, payload)
        self.assertTrue(res['ok'], res)
        tc = TareasCuidado.objects.get()
        self.assertEqual(tc.cantidad_personas_cuida, 2)
        self.assertIn('Otro', tc.a_quien_cuida)
        self.assertEqual(tc.a_quien_cuida_otro, 'Un vecino')

    def test_mrs_en_dos_bloques_se_guarda_en_un_registro(self):
        u = str(uuid4())
        payload = {
            'identificacion': self._payload_ident(),
            'secciones': [
                {'tipo': 'mrs', 'uuid_local': u, 'parcial': True,
                 'datos': {'pregunta_1': 3, 'pregunta_2': 2}},
                {'tipo': 'mrs_complementario', 'uuid_local': u, 'parcial': True,
                 'datos': {'fecha_ultima_menstruacion': '2020', 'tiene_pareja': 'SI'}},
            ],
        }
        res = sincronizar_payload(self.usuaria, payload)
        self.assertTrue(res['ok'], res)
        self.assertEqual(MRS.objects.count(), 1)
        mrs = MRS.objects.get()
        self.assertEqual(mrs.pregunta_1, 3)
        self.assertEqual(mrs.pregunta_5, 0)  # no enviada: conserva el default
        self.assertEqual(mrs.tiene_pareja, 'SI')
        self.assertEqual(mrs.fecha_ultima_menstruacion, '2020')

    def test_usuaria_no_puede_colar_campo_solo_profesional(self):
        payload = {
            'identificacion': self._payload_ident(),
            'secciones': [{'tipo': 'empa', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'presion_sistolica': 200, 'peso_kg': '70'}}],
        }
        sincronizar_payload(self.usuaria, payload)
        empa = SegmentoEMPA.objects.get()
        self.assertIsNone(empa.presion_sistolica)
        self.assertEqual(empa.origen_registro, SegmentoEMPA.OrigenDato.AUTORREPORTADO)

    def test_profesional_requiere_rut_de_paciente(self):
        payload = {'identificacion': self._payload_ident(), 'secciones': []}
        with self.assertRaises(ErrorSincronizacion):
            sincronizar_payload(self.prof, payload)

    def test_profesional_crea_identificacion_por_rut(self):
        payload = {
            'identificacion': self._payload_ident(rut='9.876.543-3'),
            'secciones': [{'tipo': 'empa', 'uuid_local': str(uuid4()), 'parcial': False,
                           'datos': {'peso_kg': '70', 'talla_actual_cm': 160,
                                     'presion_sistolica': 120, 'presion_diastolica': 80}}],
        }
        res = sincronizar_payload(self.prof, payload)
        self.assertTrue(res['ok'], res)
        ident = Identificacion.objects.get()
        self.assertEqual(ident.rut_hash, hash_rut('9.876.543-3'))
        self.assertIsNone(ident.usuario)
        self.assertEqual(SegmentoEMPA.objects.get().origen_registro,
                         SegmentoEMPA.OrigenDato.PERSONAL_MEDICO)

    def test_error_en_una_seccion_no_bloquea_las_demas(self):
        payload = {
            'identificacion': self._payload_ident(),
            'secciones': [
                {'tipo': 'trabajo', 'uuid_local': str(uuid4()), 'parcial': False,
                 'datos': {'rendimiento_afectado': 99}},
                {'tipo': 'tareas_cuidado', 'uuid_local': str(uuid4()), 'parcial': True,
                 'datos': {'cuida_otras_personas': 'SI'}},
            ],
        }
        res = sincronizar_payload(self.usuaria, payload)
        self.assertFalse(res['ok'])
        self.assertEqual(EvaluacionTrabajo.objects.count(), 0)
        self.assertEqual(TareasCuidado.objects.count(), 1)

    def test_identificacion_incompleta_es_error_y_no_guarda_secciones(self):
        payload = {
            'identificacion': {'uuid_local': str(uuid4()), 'datos': {'comuna': 'Santiago'}},
            'secciones': [{'tipo': 'tareas_cuidado', 'uuid_local': str(uuid4()),
                           'datos': {'cuida_otras_personas': 'SI'}}],
        }
        res = sincronizar_payload(self.usuaria, payload)
        self.assertFalse(res['ok'])
        self.assertEqual(res['resultados'][0]['estado'], 'error')
        self.assertEqual(Identificacion.objects.count(), 0)
        self.assertEqual(TareasCuidado.objects.count(), 0)


class HistoricoRondaTest(TestCase):
    """Fase 13: reaplicar la encuesta no sobrescribe rondas ya finalizadas."""

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.ident_datos = {
            'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
            'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
            'comuna': 'Santiago', 'region_residencia': '13',
        }

    def _payload_ident(self, **extra):
        return {'uuid_local': str(uuid4()), 'datos': dict(self.ident_datos, **extra)}

    def _payload_mrs(self, uuid_local=None, **extra_datos):
        datos = {'pregunta_1': 2}
        datos.update(extra_datos)
        return {'tipo': 'mrs', 'uuid_local': uuid_local or str(uuid4()), 'parcial': True,
                'datos': datos}

    def test_guardar_cambios_sin_finalizar_no_avanza_ronda(self):
        uuid_mrs = str(uuid4())
        payload = {'identificacion': self._payload_ident(),
                   'secciones': [self._payload_mrs(uuid_mrs, pregunta_1=1)]}
        res = sincronizar_payload(self.usuaria, payload)
        self.assertEqual(res['ronda_actual'], 1)

        # Un segundo "Guardar cambios" con el mismo uuid_local sigue
        # actualizando la misma fila (comportamiento ya existente).
        payload2 = {'identificacion': self._payload_ident(),
                    'secciones': [self._payload_mrs(uuid_mrs, pregunta_1=3)]}
        res2 = sincronizar_payload(self.usuaria, payload2)
        self.assertEqual(res2['ronda_actual'], 1)
        self.assertEqual(MRS.objects.count(), 1)
        self.assertEqual(MRS.objects.get().pregunta_1, 3)
        self.assertEqual(MRS.objects.get().ronda, 1)

    def test_finalizar_avanza_ronda_actual(self):
        payload = {'identificacion': self._payload_ident(),
                   'secciones': [self._payload_mrs()], 'finalizar': True}
        res = sincronizar_payload(self.usuaria, payload)
        self.assertTrue(res['ok'], res)
        self.assertEqual(res['ronda_actual'], 2)
        self.assertEqual(Identificacion.objects.get().ronda_actual, 2)
        self.assertEqual(MRS.objects.get().ronda, 1)

    def test_reaplicar_encuesta_crea_fila_nueva_sin_borrar_la_anterior(self):
        # Ronda 1: se responde y se finaliza.
        sincronizar_payload(self.usuaria, {
            'identificacion': self._payload_ident(),
            'secciones': [self._payload_mrs(pregunta_1=1)],
            'finalizar': True,
        })

        # Ronda 2 (Fase 14: el cliente parte con un uuid_local nuevo).
        res = sincronizar_payload(self.usuaria, {
            'identificacion': self._payload_ident(),
            'secciones': [self._payload_mrs(pregunta_1=4)],
        })
        self.assertTrue(res['ok'], res)

        self.assertEqual(MRS.objects.count(), 2)
        rondas = sorted(MRS.objects.values_list('ronda', flat=True))
        self.assertEqual(rondas, [1, 2])
        mrs_ronda_1 = MRS.objects.get(ronda=1)
        mrs_ronda_2 = MRS.objects.get(ronda=2)
        self.assertEqual(mrs_ronda_1.pregunta_1, 1)
        self.assertEqual(mrs_ronda_2.pregunta_1, 4)

    def test_reutilizar_uuid_de_ronda_cerrada_da_error(self):
        uuid_mrs = str(uuid4())
        sincronizar_payload(self.usuaria, {
            'identificacion': self._payload_ident(),
            'secciones': [self._payload_mrs(uuid_mrs, pregunta_1=1)],
            'finalizar': True,
        })

        res = sincronizar_payload(self.usuaria, {
            'identificacion': self._payload_ident(),
            'secciones': [self._payload_mrs(uuid_mrs, pregunta_1=9)],
        })
        self.assertFalse(res['ok'])
        self.assertEqual(res['resultados'][1]['estado'], 'error')
        self.assertEqual(MRS.objects.get(uuid_local=uuid_mrs).pregunta_1, 1)


class SincronizarEndpointTest(TestCase):
    URL = '/api/sincronizar/'

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.client.force_login(self.usuaria)
        self.ident = {
            'uuid_local': str(uuid4()),
            'datos': {
                'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
                'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
                'comuna': 'Santiago', 'region_residencia': '13',
            },
        }

    def _post(self, obj):
        return self.client.post(self.URL, data=json.dumps(obj), content_type='application/json')

    def test_requiere_login(self):
        self.client.logout()
        resp = self._post({})
        self.assertEqual(resp.status_code, 302)

    def test_get_no_permitido(self):
        self.assertEqual(self.client.get(self.URL).status_code, 405)

    def test_json_invalido(self):
        resp = self.client.post(self.URL, data='no-json', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_sincroniza_ok(self):
        resp = self._post({
            'identificacion': self.ident,
            'secciones': [{'tipo': 'tareas_cuidado', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'cuida_otras_personas': 'SI'}}],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ok'])
        self.assertEqual(TareasCuidado.objects.count(), 1)

    def test_error_de_payload_devuelve_400(self):
        prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD,
        )
        self.client.force_login(prof)
        resp = self._post({'identificacion': self.ident})  # profesional sin rut de paciente
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json())

    def test_estado_sin_datos(self):
        resp = self.client.get('/api/estado/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['identificacion'])

    def test_estado_despues_de_sincronizar(self):
        self._post({
            'identificacion': self.ident,
            'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'pregunta_1': 2}}],
        })
        datos = self.client.get('/api/estado/').json()
        self.assertTrue(datos['identificacion'])
        self.assertEqual(datos['secciones']['mrs'], 1)

    def test_estado_tras_finalizar_muestra_ronda_nueva_en_cero(self):
        self._post({
            'identificacion': self.ident,
            'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'pregunta_1': 2}}],
            'finalizar': True,
        })
        datos = self.client.get('/api/estado/').json()
        self.assertEqual(datos['ronda_actual'], 2)
        self.assertEqual(datos['secciones']['mrs'], 0)


class EsquemaTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD,
        )

    def _esquema(self, usuario):
        self.client.force_login(usuario)
        resp = self.client.get('/api/esquema/')
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def _seccion(self, esquema, tipo):
        return next(s for s in esquema['secciones'] if s['tipo'] == tipo)

    def _pregunta(self, seccion, nombre):
        return next(p for p in seccion['preguntas'] if p['nombre'] == nombre)

    def test_requiere_login(self):
        self.assertEqual(self.client.get('/api/esquema/').status_code, 302)

    def test_secciones_en_orden(self):
        esquema = self._esquema(self.usuaria)
        tipos = [s['tipo'] for s in esquema['secciones']]
        self.assertEqual(tipos, [
            'identificacion', 'trabajo', 'tareas_cuidado', 'mrs', 'mrs_complementario',
            'empa', 'habitos_de_vida', 'actividad_fisica', 'conocimiento_sistema',
        ])

    def test_habitos_de_vida_usa_escalas_de_cinco_niveles(self):
        hv = self._seccion(self._esquema(self.usuaria), 'habitos_de_vida')
        nombres = {p['nombre'] for p in hv['preguntas']}
        # Consumo de sustancias movido desde el EMPA.
        self.assertLessEqual({'tabaco_frecuencia', 'marihuana_frecuencia',
                              'alcohol_frecuencia'}, nombres)
        # Todas las cantidades/frecuencias son ahora preguntas de opción (5 niveles).
        for campo in ('vasos_agua_dia', 'pescado_semana', 'golosinas_semana',
                      'tabaco_frecuencia'):
            p = self._pregunta(hv, campo)
            self.assertEqual(p['tipo_campo'], 'opciones', campo)
            self.assertEqual(len(p['opciones']), 5, campo)
        # Nota informativa del tabaco y campo libre condicional de "quién prepara".
        self.assertIn('terapia hormonal', self._pregunta(hv, 'tabaco_frecuencia')['nota'])
        self.assertEqual(
            self._pregunta(hv, 'quien_prepara_comidas_otro')['mostrar_si'],
            {'campo': 'quien_prepara_comidas', 'valor': 'OTRO'},
        )

    def test_mrs_y_complementario_son_pantallas_separadas_del_mismo_registro(self):
        esquema = self._esquema(self.usuaria)
        mrs = self._seccion(esquema, 'mrs')
        comp = self._seccion(esquema, 'mrs_complementario')
        # Las 11 Likert van solo en 'mrs'.
        nombres_mrs = {p['nombre'] for p in mrs['preguntas']}
        self.assertEqual(nombres_mrs, {f'pregunta_{i}' for i in range(1, 12)})
        # El complementario no repite ninguna Likert y empieza por la fecha.
        nombres_comp = [p['nombre'] for p in comp['preguntas']]
        self.assertNotIn('pregunta_1', nombres_comp)
        self.assertEqual(nombres_comp[0], 'fecha_ultima_menstruacion')
        # Ambas pantallas se sincronizan contra el mismo registro.
        self.assertEqual(mrs['grupo'], 'mrs')
        self.assertEqual(comp['grupo'], 'mrs')

    def test_usuaria_no_recibe_campos_solo_profesional(self):
        empa = self._seccion(self._esquema(self.usuaria), 'empa')
        nombres = {p['nombre'] for p in empa['preguntas']}
        self.assertNotIn('presion_sistolica', nombres)

    def test_profesional_si_recibe_campos_clinicos(self):
        empa = self._seccion(self._esquema(self.prof), 'empa')
        nombres = {p['nombre'] for p in empa['preguntas']}
        self.assertIn('presion_sistolica', nombres)

    def test_preguntas_mrs_marcadas_con_escala_mrs(self):
        mrs = self._seccion(self._esquema(self.usuaria), 'mrs')
        for i in range(1, 12):
            self.assertEqual(self._pregunta(mrs, f'pregunta_{i}')['escala'], 'mrs')

    def test_seccion_trabajo_es_condicional(self):
        trabajo = self._seccion(self._esquema(self.usuaria), 'trabajo')
        self.assertEqual(trabajo['mostrar_si'],
                         {'seccion': 'identificacion', 'campo': 'trabaja_actualmente', 'valor': True})

    def test_contrato_de_esquema(self):
        esquema = self._esquema(self.usuaria)
        self.assertEqual(esquema['edad_minima'], 40)
        self.assertEqual(esquema['edad_maxima'], 60)
        self.assertEqual({d['termino'] for d in esquema['definiciones']},
                         {'Perimenopausia', 'Menopausia'})
        self.assertIn('blanco', esquema['mensaje_omitir'])
        for s in esquema['secciones']:
            self.assertTrue(s['descripcion'], s['tipo'])

    def test_escalas_horizontales_y_polaridad(self):
        esquema = self._esquema(self.usuaria)
        trabajo = self._seccion(esquema, 'trabajo')
        rendimiento = self._pregunta(trabajo, 'rendimiento_afectado')
        self.assertTrue(rendimiento['escala_horizontal'])
        self.assertIsNone(rendimiento['escala'])
        self.assertEqual(rendimiento['polaridad'], 'directa')
        self.assertEqual(self._pregunta(trabajo, 'lugar_trabajo_comprensivo')['polaridad'],
                         'inversa')
        # El MRS conserva las caritas: no es escala horizontal.
        p1 = self._pregunta(self._seccion(esquema, 'mrs'), 'pregunta_1')
        self.assertEqual(p1['escala'], 'mrs')
        self.assertFalse(p1['escala_horizontal'])
        # Pregunta categórica: ni horizontal ni polaridad.
        genero = self._pregunta(self._seccion(esquema, 'identificacion'), 'genero')
        self.assertFalse(genero['escala_horizontal'])
        self.assertIsNone(genero['polaridad'])

    def test_bloques_si_no_son_escala_horizontal(self):
        # Ajustes finales adicionales, regla 1: todo Sí/No (y el booleano
        # trabaja_actualmente) se dibuja horizontal con color, sin importar el
        # campo — no hace falta listarlos uno por uno.
        esquema = self._esquema(self.usuaria)
        comp = self._seccion(esquema, 'mrs_complementario')
        p = self._pregunta(comp, 'usa_metodo_anticonceptivo')
        self.assertTrue(p['escala_horizontal'])
        self.assertEqual(len(p['opciones']), 2)

        ident = self._seccion(esquema, 'identificacion')
        trabaja = self._pregunta(ident, 'trabaja_actualmente')
        self.assertEqual(trabaja['tipo_campo'], 'booleano')
        self.assertTrue(trabaja['escala_horizontal'])

    def test_bloques_si_no_no_sabe_son_escala_horizontal(self):
        cs = self._seccion(self._esquema(self.usuaria), 'conocimiento_sistema')
        p = self._pregunta(cs, 'conoce_sistema_publico_climaterio')
        self.assertTrue(p['escala_horizontal'])
        self.assertEqual({o['valor'] for o in p['opciones']}, {'SI', 'NO', 'NS'})

    def test_tipo_sangrado_es_escala_horizontal_forzada(self):
        # Es una escala de severidad con valores de texto: el detector
        # automático no la reconoce, así que se marca a mano.
        comp = self._seccion(self._esquema(self.usuaria), 'mrs_complementario')
        p = self._pregunta(comp, 'tipo_sangrado')
        self.assertTrue(p['escala_horizontal'])
        self.assertEqual(len(p['opciones']), 5)

    def test_menstruacion_llega_sin_ausencia(self):
        comp = self._seccion(self._esquema(self.usuaria), 'mrs_complementario')
        p = self._pregunta(comp, 'menstruacion_llega')
        valores = {o['valor'] for o in p['opciones']}
        self.assertEqual(valores, {'REGULAR', 'IRREGULAR', 'NO_SEGURA'})
        textos = {o['texto'] for o in p['opciones']}
        self.assertIn('No estoy segura / No sé', textos)
        # No es un bloque Sí/No ni una escala de severidad: sigue categórica.
        self.assertFalse(p['escala_horizontal'])

    def test_quien_prepara_comidas_sin_delivery_y_en_chips(self):
        hv = self._seccion(self._esquema(self.usuaria), 'habitos_de_vida')
        p = self._pregunta(hv, 'quien_prepara_comidas')
        valores = {o['valor'] for o in p['opciones']}
        self.assertNotIn('DELIVERY', valores)
        self.assertEqual(len(valores), 5)
        self.assertTrue(p['chips'])
        self.assertFalse(p['escala_horizontal'])
        self.assertIsNone(p['polaridad'])

    def test_conocimiento_recursos_es_pregunta_general(self):
        cs = self._seccion(self._esquema(self.usuaria), 'conocimiento_sistema')
        nombres = {p['nombre'] for p in cs['preguntas']}
        self.assertNotIn('recursos_conocidos', nombres)
        p = self._pregunta(cs, 'conoce_recursos_disponibles')
        self.assertEqual({o['valor'] for o in p['opciones']}, {'SI', 'NO', 'NS'})
        self.assertTrue(p['escala_horizontal'])

    def test_ninguna_pregunta_muestra_nota_de_implementacion(self):
        esquema = self._esquema(self.usuaria)
        for seccion in esquema['secciones']:
            for p in seccion['preguntas']:
                self.assertNotIn('separada por comas', p['texto'],
                                 f"{seccion['tipo']}.{p['nombre']}")

    def test_trabajo_incluye_pregunta_de_estres(self):
        trabajo = self._seccion(self._esquema(self.usuaria), 'trabajo')
        p = self._pregunta(trabajo, 'estres_entorno_laboral')
        self.assertEqual(len(p['opciones']), 5)
        self.assertIn('estrés', p['texto'].lower())

    def test_tareas_cuidado_redisenada(self):
        tc = self._seccion(self._esquema(self.usuaria), 'tareas_cuidado')
        nombres = {p['nombre'] for p in tc['preguntas']}
        self.assertNotIn('mas_de_una_persona_a_cargo', nombres)
        self.assertLessEqual(
            {'cantidad_personas_cuida', 'a_quien_cuida', 'a_quien_cuida_otro',
             'sobrecarga_fisica_emocional'}, nombres)
        for campo in ('cantidad_personas_cuida', 'a_quien_cuida'):
            self.assertEqual(self._pregunta(tc, campo)['mostrar_si'],
                             {'campo': 'cuida_otras_personas', 'valor': 'SI'})
        aq = self._pregunta(tc, 'a_quien_cuida')
        self.assertEqual(aq['tipo_campo'], 'multiseleccion')
        self.assertEqual(len(aq['opciones']), 7)

    def test_pregunta_condicional_en_mrs(self):
        comp = self._seccion(self._esquema(self.usuaria), 'mrs_complementario')
        cond = self._pregunta(comp, 'tipo_metodo_anticonceptivo')['mostrar_si']
        self.assertEqual(cond, {'campo': 'usa_metodo_anticonceptivo', 'valor': 'SI'})

    def test_metodo_anticonceptivo_otro_y_ausencia_menstrual(self):
        comp = self._seccion(self._esquema(self.usuaria), 'mrs_complementario')
        # "No sé" y "Otro" están disponibles en el método anticonceptivo.
        valores = {o['valor'] for o in self._pregunta(comp, 'tipo_metodo_anticonceptivo')['opciones']}
        self.assertIn('NO_SE', valores)
        self.assertIn('OTRO', valores)
        # El campo libre aparece solo si se eligió "Otro".
        self.assertEqual(
            self._pregunta(comp, 'tipo_metodo_anticonceptivo_otro')['mostrar_si'],
            {'campo': 'tipo_metodo_anticonceptivo', 'valor': 'OTRO'},
        )
        # Regularidad y sangrado dependen de los meses desde la última menstruación.
        for campo in ('menstruacion_llega', 'tipo_sangrado'):
            self.assertEqual(
                self._pregunta(comp, campo)['mostrar_si'],
                {'campo': 'fecha_ultima_menstruacion', 'operador': 'meses_desde_lt', 'valor': 12},
            )

    def test_programa_consultorio_esta_en_conocimiento_del_sistema(self):
        esquema = self._esquema(self.usuaria)
        comp = self._seccion(esquema, 'mrs_complementario')
        self.assertNotIn('control_otros_programas',
                         {p['nombre'] for p in comp['preguntas']})
        cs = self._seccion(esquema, 'conocimiento_sistema')
        nombres = {p['nombre'] for p in cs['preguntas']}
        self.assertIn('en_control_programa_consultorio', nombres)
        self.assertEqual(
            self._pregunta(cs, 'en_control_programa_cual')['mostrar_si'],
            {'campo': 'en_control_programa_consultorio', 'valor': 'SI'},
        )

    def test_incluye_descripciones_de_niveles_mrs(self):
        esquema = self._esquema(self.usuaria)
        self.assertEqual(len(esquema['mrs_niveles']), 5)
        self.assertEqual(esquema['mrs_niveles']['0'], 'No tienes ese síntoma.')

    def test_texto_de_pregunta_usa_el_help_text(self):
        mrs = self._seccion(self._esquema(self.usuaria), 'mrs')
        self.assertIn('Bochornos', self._pregunta(mrs, 'pregunta_1')['texto'])

    def test_region_va_antes_que_comuna(self):
        ident = self._seccion(self._esquema(self.usuaria), 'identificacion')
        nombres = [p['nombre'] for p in ident['preguntas']]
        self.assertLess(nombres.index('region_residencia'), nombres.index('comuna'))

    def test_comuna_depende_de_region(self):
        ident = self._seccion(self._esquema(self.usuaria), 'identificacion')
        self.assertEqual(self._pregunta(ident, 'comuna')['depende_de'], 'region_residencia')

    def test_incluye_comunas_por_region(self):
        esquema = self._esquema(self.usuaria)
        self.assertIn('Santiago', esquema['comunas_por_region']['13'])
        self.assertEqual(sum(len(v) for v in esquema['comunas_por_region'].values()), 346)


class IdentificacionFormComunaTest(TestCase):
    datos_base = {
        'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
        'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
        'trabaja_actualmente': '',
    }

    def test_comuna_valida_para_region(self):
        form = IdentificacionForm(data=dict(self.datos_base, region_residencia='13', comuna='Maipú'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_comuna_invalida_para_region(self):
        form = IdentificacionForm(data=dict(self.datos_base, region_residencia='13', comuna='Valdivia'))
        self.assertFalse(form.is_valid())
        self.assertIn('comuna', form.errors)


class IdentificacionFormEdadTest(TestCase):
    base = {
        'genero': 'F', 'nivel_educacion': 'M_COM', 'origen_procedencia': 'CL',
        'pueblo_originario_afro': 'NINGUNO', 'region_residencia': '13', 'comuna': 'Santiago',
        'trabaja_actualmente': '',
    }

    def _form(self, anios):
        hoy = date.today()
        return IdentificacionForm(data=dict(
            self.base, fecha_nacimiento=f'{hoy.year - anios}-01-01'))

    def test_rechaza_menor_de_40(self):
        form = self._form(30)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_nacimiento', form.errors)

    def test_acepta_40_o_mas(self):
        self.assertTrue(self._form(45).is_valid(), self._form(45).errors)

    def test_limites_del_rango_40_a_60(self):
        for anios in (40, 60):
            form = self._form(anios)
            self.assertTrue(form.is_valid(), (anios, form.errors))
        for anios in (39, 61):
            form = self._form(anios)
            self.assertFalse(form.is_valid(), anios)
            self.assertIn('fecha_nacimiento', form.errors)

    def test_rechaza_mayor_de_60_aunque_declare_excepcion(self):
        hoy = date.today()
        for excepcion in ('QUIRURGICA', 'AUSENCIA'):
            form = IdentificacionForm(data=dict(
                self.base, fecha_nacimiento=f'{hoy.year - 65}-01-01', excepcion_edad=excepcion))
            self.assertFalse(form.is_valid(), excepcion)
            self.assertIn('fecha_nacimiento', form.errors)

    def test_acepta_menor_de_40_con_excepcion(self):
        hoy = date.today()
        form = IdentificacionForm(data=dict(
            self.base, fecha_nacimiento=f'{hoy.year - 30}-01-01', excepcion_edad='QUIRURGICA'))
        self.assertTrue(form.is_valid(), form.errors)


class SincronizacionEdadTest(TestCase):
    def _payload_menor_de_edad(self, **extra_datos):
        hoy = date.today()
        datos = {
            'fecha_nacimiento': f'{hoy.year - 25}-06-01', 'genero': 'F',
            'nivel_educacion': 'M_COM', 'origen_procedencia': 'CL',
            'pueblo_originario_afro': 'NINGUNO', 'comuna': 'Santiago',
            'region_residencia': '13',
        }
        datos.update(extra_datos)
        return {
            'identificacion': {'uuid_local': str(uuid4()), 'datos': datos},
            'secciones': [],
        }

    def test_sync_rechaza_identificacion_menor_de_40(self):
        usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        res = sincronizar_payload(usuaria, self._payload_menor_de_edad())
        self.assertFalse(res['ok'])
        self.assertEqual(res['resultados'][0]['estado'], 'error')
        self.assertIn('fecha_nacimiento', res['resultados'][0]['errores'])

    def test_sync_acepta_menor_de_40_con_excepcion_menopausia_quirurgica(self):
        usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        payload = self._payload_menor_de_edad(excepcion_edad='QUIRURGICA')
        res = sincronizar_payload(usuaria, payload)
        self.assertTrue(res['ok'])
        self.assertEqual(res['resultados'][0]['estado'], 'creado')
        ident = Identificacion.objects.get(usuario=usuaria)
        self.assertEqual(ident.excepcion_edad, 'QUIRURGICA')

    def test_sync_acepta_menor_de_40_con_excepcion_ausencia_menstruacion(self):
        usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        payload = self._payload_menor_de_edad(excepcion_edad='AUSENCIA')
        res = sincronizar_payload(usuaria, payload)
        self.assertTrue(res['ok'])

    def test_sync_rechaza_mayor_de_60(self):
        usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        hoy = date.today()
        payload = self._payload_menor_de_edad(
            fecha_nacimiento=f'{hoy.year - 70}-06-01', excepcion_edad='AUSENCIA')
        res = sincronizar_payload(usuaria, payload)
        self.assertFalse(res['ok'])
        self.assertIn('fecha_nacimiento', res['resultados'][0]['errores'])
        self.assertFalse(Identificacion.objects.filter(usuario=usuaria).exists())


class EsquemaExcepcionEdadTest(TestCase):
    def test_excepcion_edad_no_aparece_como_pregunta_de_la_seccion(self):
        esquema = construir_esquema(Usuario.Rol.USUARIA_COMUN)
        seccion_ident = next(s for s in esquema['secciones'] if s['tipo'] == 'identificacion')
        nombres = {p['nombre'] for p in seccion_ident['preguntas']}
        self.assertNotIn('excepcion_edad', nombres)

    def test_excepciones_edad_se_exponen_en_el_esquema(self):
        esquema = construir_esquema(Usuario.Rol.USUARIA_COMUN)
        valores = {op['valor'] for op in esquema['excepciones_edad']}
        self.assertEqual(valores, {'QUIRURGICA', 'AUSENCIA'})


class PaginaEncuestaTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')

    def test_requiere_login(self):
        resp = self.client.get('/encuesta/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/cuenta/ingresar/', resp.url)

    def test_redirige_a_consentimiento_si_no_se_ha_aceptado(self):
        self.client.force_login(self.usuaria)
        resp = self.client.get('/encuesta/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/cuenta/consentimiento/', resp.url)

    def test_pagina_carga_con_el_script(self):
        from django.utils import timezone
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save(update_fields=['consentimiento_aceptado_en'])
        self.client.force_login(self.usuaria)
        resp = self.client.get('/encuesta/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'js/encuesta.js')
        # El botón "Salir" (base.html) es lo que garantiza que se emita la
        # cookie csrftoken; el cliente ya no depende de un <meta> con el token
        # (podía quedar obsoleto si la página se sirve desde caché offline).
        self.assertContains(resp, 'name="csrfmiddlewaretoken"')

    def test_service_worker_se_sirve_desde_la_raiz(self):
        resp = self.client.get('/sw.js')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/javascript')
        contenido = b''.join(resp.streaming_content)
        self.assertIn(b'addEventListener', contenido)

    def test_service_worker_no_requiere_login(self):
        # el navegador pide /sw.js sin sesión; debe responder igual
        self.client.logout()
        self.assertEqual(self.client.get('/sw.js').status_code, 200)

    def test_service_worker_no_precachea_pagina_con_sesion(self):
        # /encuesta/ NO va en la lista de precarga: si el SW se instala sin
        # sesión, cachearía la redirección al login y rompería la navegación
        # (Salir / cargar la encuesta) con net::ERR_FAILED.
        contenido = b''.join(self.client.get('/sw.js').streaming_content).decode()
        estaticos = contenido.split('ESTATICOS = [')[1].split(']')[0]
        self.assertNotIn('/encuesta/', estaticos)
        self.assertIn('!resp.redirected', contenido)  # no se cachean respuestas redirigidas


class PropiedadesModeloTest(TestCase):
    def _ident(self, **kw):
        base = dict(fecha_nacimiento='1970-06-15', genero='F',
                    nivel_educacion='M_COM', comuna='Santiago', region_residencia='13')
        base.update(kw)
        return Identificacion.objects.create(**base)

    def test_edad(self):
        hoy = date.today()
        ident = self._ident(fecha_nacimiento=date(hoy.year - 45, 1, 1))
        self.assertEqual(ident.edad, 45)

    def test_puntaje_total_mrs(self):
        mrs = MRS.objects.create(participante=self._ident(),
                                 pregunta_1=4, pregunta_2=3, pregunta_5=2)
        self.assertEqual(mrs.puntaje_total, 9)

    def test_perdida_talla(self):
        ident = self._ident()
        empa = SegmentoEMPA.objects.create(participante=ident,
                                           talla_maxima_cm=162, talla_actual_cm=158)
        self.assertEqual(empa.perdida_talla_cm, 4)
        sin_max = SegmentoEMPA.objects.create(participante=ident, talla_actual_cm=160)
        self.assertIsNone(sin_max.perdida_talla_cm)

    def test_doble_carga(self):
        con = TareasCuidado.objects.create(
            participante=self._ident(trabaja_actualmente=True), cuida_otras_personas='SI')
        self.assertTrue(con.doble_carga)
        sin = TareasCuidado.objects.create(
            participante=self._ident(trabaja_actualmente=False), cuida_otras_personas='SI')
        self.assertFalse(sin.doble_carga)

    def test_menstruacion_ausente_segun_fecha(self):
        hoy = date.today()
        reciente = MRS.objects.create(
            participante=self._ident(),
            fecha_ultima_menstruacion=f'{hoy.month:02d}/{hoy.year}')
        self.assertFalse(reciente.menstruacion_ausente)
        antigua = MRS.objects.create(
            participante=self._ident(),
            fecha_ultima_menstruacion=str(hoy.year - 3))
        self.assertTrue(antigua.menstruacion_ausente)
        sin_fecha = MRS.objects.create(participante=self._ident())
        self.assertIsNone(sin_fecha.meses_desde_ultima_menstruacion)
        self.assertFalse(sin_fecha.menstruacion_ausente)


class MesesDesdeTextoFechaTest(TestCase):
    def test_formatos_aceptados(self):
        hoy = date.today()
        self.assertEqual(meses_desde_texto_fecha(f'{hoy.year}-{hoy.month:02d}'), 0)
        self.assertEqual(meses_desde_texto_fecha(str(hoy.year - 1)),
                         12 + (hoy.month - 7))  # solo año -> se asume julio
        self.assertEqual(meses_desde_texto_fecha(f'15/{hoy.month:02d}/{hoy.year}'), 0)

    def test_texto_invalido_o_vacio(self):
        for txt in ('', None, 'el año pasado', '2020-13', '99/99/9999'):
            self.assertIsNone(meses_desde_texto_fecha(txt))


class SincronizacionCompletaTest(TestCase):
    def test_sincroniza_las_siete_secciones(self):
        usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        payload = {
            'identificacion': {'uuid_local': str(uuid4()), 'datos': {
                'fecha_nacimiento': '1972-03-10', 'genero': 'F', 'nivel_educacion': 'U_COM',
                'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
                'comuna': 'Providencia', 'region_residencia': '13',
            }},
            'secciones': [
                {'tipo': t, 'uuid_local': str(uuid4()), 'parcial': True, 'datos': d}
                for t, d in [
                    ('trabajo', {'rendimiento_afectado': 3}),
                    ('tareas_cuidado', {'cuida_otras_personas': 'NO'}),
                    ('mrs', {'pregunta_1': 2, 'pregunta_2': 1}),
                    ('empa', {'peso_kg': '65', 'talla_actual_cm': 158}),
                    ('actividad_fisica', {'dias_ejercicio_semana': 3}),
                    ('habitos_de_vida', {'vasos_agua_dia': 4, 'tabaco_frecuencia': 1}),
                    ('conocimiento_sistema', {'conoce_sistema_publico_climaterio': 'NO'}),
                ]
            ],
        }
        res = sincronizar_payload(usuaria, payload)
        self.assertTrue(res['ok'], res)
        ident = Identificacion.objects.get()
        self.assertEqual(ident.evaluaciones_trabajo.count(), 1)
        self.assertEqual(ident.evaluaciones_tareas_cuidado.count(), 1)
        self.assertEqual(ident.evaluaciones_mrs.count(), 1)
        self.assertEqual(ident.evaluaciones_empa.count(), 1)
        self.assertEqual(ident.evaluaciones_actividad_fisica.count(), 1)
        self.assertEqual(ident.evaluaciones_habitos_de_vida.count(), 1)
        self.assertEqual(ident.evaluaciones_conocimiento_sistema.count(), 1)
        self.assertEqual(ActividadFisica.objects.get().dias_ejercicio_semana, 3)
        self.assertEqual(HabitosDeVida.objects.get().vasos_agua_dia, 4)
        self.assertEqual(ConocimientoSistema.objects.get().conoce_sistema_publico_climaterio, 'NO')


class PanelProfesionalTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD,
        )
        payload = {
            'identificacion': {
                'uuid_local': str(uuid4()), 'rut': '9.876.543-3',
                'datos': {
                    'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
                    'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
                    'comuna': 'Santiago', 'region_residencia': '13',
                },
            },
            'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'pregunta_1': 2}}],
            'finalizar': True,
        }
        res = sincronizar_payload(self.prof, payload)
        assert res['ok'], res  # si esto falla, revisa el payload de arriba, no el resto del test
        self.paciente = Identificacion.objects.get(rut_hash=hash_rut('9.876.543-3'))

    def test_requiere_login(self):
        resp = self.client.get('/profesional/buscar/')
        self.assertEqual(resp.status_code, 302)

    def test_usuaria_comun_no_puede_ver_el_buscador(self):
        self.client.force_login(self.usuaria)
        resp = self.client.get('/profesional/buscar/')
        self.assertEqual(resp.status_code, 403)

    def test_usuaria_comun_no_puede_ver_la_ficha(self):
        self.client.force_login(self.usuaria)
        resp = self.client.get(f'/profesional/paciente/{self.paciente.id}/')
        self.assertEqual(resp.status_code, 403)

    def test_profesional_encuentra_paciente_existente(self):
        self.client.force_login(self.prof)
        resp = self.client.get('/profesional/buscar/', {'rut': '9.876.543-3'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['resultado'], self.paciente)

    def test_profesional_no_encuentra_rut_inexistente(self):
        self.client.force_login(self.prof)
        resp = self.client.get('/profesional/buscar/', {'rut': '11.111.111-1'})
        self.assertIsNone(resp.context['resultado'])
        self.assertIn('No hay ninguna paciente', resp.context['error'])

    def test_profesional_rut_invalido(self):
        self.client.force_login(self.prof)
        resp = self.client.get('/profesional/buscar/', {'rut': '11.111.111-2'})
        self.assertIn('no es válido', resp.context['error'])

    def test_ficha_muestra_historial_por_ronda(self):
        # Segunda ronda: nuevo uuid_local, como haría el cliente tras Fase 14.
        res = sincronizar_payload(self.prof, {
            'identificacion': {'uuid_local': str(uuid4()), 'rut': '9.876.543-3', 'datos': {
                'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
                'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
                'comuna': 'Santiago', 'region_residencia': '13',
            }},
            'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'pregunta_1': 4}}],
        })
        assert res['ok'], res

        self.client.force_login(self.prof)
        resp = self.client.get(f'/profesional/paciente/{self.paciente.id}/')
        self.assertEqual(resp.status_code, 200)

        rondas = resp.context['rondas']
        self.assertEqual([r['numero'] for r in rondas], [2, 1])  # más reciente primero
        self.assertTrue(rondas[1]['es_actual'] is False)
        self.assertTrue(rondas[0]['es_actual'])

        mrs_ronda_1 = next(s for s in rondas[1]['secciones'] if s['titulo'].startswith('Escala'))
        self.assertEqual(mrs_ronda_1['registro'].pregunta_1, 2)


class MiTableroTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD,
        )

    def test_requiere_login(self):
        resp = self.client.get('/mi-tablero/')
        self.assertEqual(resp.status_code, 302)

    def test_sin_datos_todavia(self):
        self.client.force_login(self.usuaria)
        resp = self.client.get('/mi-tablero/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context['paciente'])
        self.assertEqual(resp.context['rondas'], [])

    def test_profesional_no_usa_este_tablero(self):
        self.client.force_login(self.prof)
        resp = self.client.get('/mi-tablero/')
        self.assertRedirects(resp, '/profesional/buscar/')

    def test_muestra_su_propio_historial(self):
        res = sincronizar_payload(self.usuaria, {
            'identificacion': {'uuid_local': str(uuid4()), 'datos': {
                'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
                'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
                'comuna': 'Santiago', 'region_residencia': '13',
            }},
            'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'pregunta_1': 3}}],
            'finalizar': True,
        })
        assert res['ok'], res

        self.client.force_login(self.usuaria)
        resp = self.client.get('/mi-tablero/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['paciente'].usuario, self.usuaria)

        rondas = resp.context['rondas']
        # Ronda 1 quedó finalizada (con datos); la 2 se abrió automáticamente
        # y todavía está en curso, sin datos.
        self.assertEqual([r['numero'] for r in rondas], [2, 1])
        self.assertTrue(rondas[0]['es_actual'])
        self.assertFalse(rondas[1]['es_actual'])
        mrs_ronda_1 = next(s for s in rondas[1]['secciones'] if s['titulo'].startswith('Escala'))
        self.assertEqual(mrs_ronda_1['registro'].pregunta_1, 3)


class EvaluacionSatisfaccionTest(TestCase):
    """Evaluación de la plataforma, voluntaria, al final del sistema (Fase 22)."""

    RESPUESTAS = {
        'facilidad_uso': 4, 'fatiga_mental': 2, 'comodidad_diseno': 5,
        'recomendaria': 'SI', 'incomodidad': 'NO', 'comentario_incomodidad': '',
    }

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.client.force_login(self.usuaria)

    def _participante(self, finalizar):
        res = sincronizar_payload(self.usuaria, {
            'identificacion': {'uuid_local': str(uuid4()), 'datos': {
                'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
                'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
                'comuna': 'Santiago', 'region_residencia': '13',
            }},
            'secciones': [],
            'finalizar': finalizar,
        })
        assert res['ok'], res
        return Identificacion.objects.get(usuario=self.usuaria)

    def test_sin_ronda_finalizada_redirige_al_tablero(self):
        self._participante(finalizar=False)
        resp = self.client.get('/mi-evaluacion/')
        self.assertRedirects(resp, '/mi-tablero/')
        resp = self.client.get('/mi-tablero/')
        self.assertFalse(resp.context['puede_evaluar'])
        self.assertNotContains(resp, 'Evaluar la plataforma')

    def test_sin_participante_redirige_al_tablero(self):
        self.assertRedirects(self.client.get('/mi-evaluacion/'), '/mi-tablero/')

    def test_guardar_evaluacion(self):
        participante = self._participante(finalizar=True)
        resp = self.client.get('/mi-evaluacion/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['editando'])

        resp = self.client.post('/mi-evaluacion/', self.RESPUESTAS)
        self.assertRedirects(resp, '/mi-tablero/')
        evaluacion = EvaluacionSatisfaccion.objects.get(participante=participante)
        self.assertEqual(evaluacion.facilidad_uso, 4)
        self.assertEqual(evaluacion.recomendaria, 'SI')

    def test_incomodidad_si_exige_comentario(self):
        self._participante(finalizar=True)
        datos = dict(self.RESPUESTAS, incomodidad='SI', comentario_incomodidad='   ')
        resp = self.client.post('/mi-evaluacion/', datos)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('comentario_incomodidad', resp.context['form'].errors)
        self.assertFalse(EvaluacionSatisfaccion.objects.exists())

        datos['comentario_incomodidad'] = 'La pregunta de ingresos.'
        self.assertRedirects(self.client.post('/mi-evaluacion/', datos), '/mi-tablero/')

    def test_faltan_respuestas(self):
        self._participante(finalizar=True)
        resp = self.client.post('/mi-evaluacion/', {'facilidad_uso': 3})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(EvaluacionSatisfaccion.objects.exists())

    def test_volver_a_enviar_actualiza_la_misma_evaluacion(self):
        self._participante(finalizar=True)
        self.client.post('/mi-evaluacion/', self.RESPUESTAS)
        resp = self.client.get('/mi-evaluacion/')
        self.assertTrue(resp.context['editando'])
        self.client.post('/mi-evaluacion/', dict(self.RESPUESTAS, facilidad_uso=1))
        self.assertEqual(EvaluacionSatisfaccion.objects.count(), 1)
        self.assertEqual(EvaluacionSatisfaccion.objects.get().facilidad_uso, 1)

    def test_boton_en_el_tablero(self):
        self._participante(finalizar=True)
        resp = self.client.get('/mi-tablero/')
        self.assertTrue(resp.context['puede_evaluar'])
        self.assertContains(resp, 'Evaluar la plataforma')
        self.client.post('/mi-evaluacion/', self.RESPUESTAS)
        resp = self.client.get('/mi-tablero/')
        self.assertContains(resp, 'Evaluación enviada')

    def test_profesional_no_evalua(self):
        prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD,
        )
        self.client.force_login(prof)
        self.assertRedirects(self.client.get('/mi-evaluacion/'), '/profesional/buscar/')
