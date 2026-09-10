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
    EvaluacionTrabajo,
    HabitosAlimenticios,
    Identificacion,
    MRS,
    SegmentoEMPA,
    TareasCuidado,
    meses_desde_texto_fecha,
)
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
                                     'mas_de_una_persona_a_cargo': 'NO'}}],
        }
        sincronizar_payload(self.usuaria, payload)
        payload['secciones'][0]['datos']['mas_de_una_persona_a_cargo'] = 'SI'
        res = sincronizar_payload(self.usuaria, payload)
        self.assertEqual(TareasCuidado.objects.count(), 1)
        self.assertEqual(res['resultados'][1]['estado'], 'actualizado')
        self.assertEqual(TareasCuidado.objects.get().mas_de_una_persona_a_cargo, 'SI')

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
            'empa', 'actividad_fisica', 'habitos_alimenticios', 'conocimiento_sistema',
        ])

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


class PaginaEncuestaTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')

    def test_requiere_login(self):
        resp = self.client.get('/encuesta/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/cuenta/ingresar/', resp.url)

    def test_pagina_carga_con_el_script(self):
        self.client.force_login(self.usuaria)
        resp = self.client.get('/encuesta/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'js/encuesta.js')
        self.assertContains(resp, 'name="csrf-token"')

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
                    ('habitos_alimenticios', {'vasos_agua_dia': 6}),
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
        self.assertEqual(ident.evaluaciones_habitos_alimenticios.count(), 1)
        self.assertEqual(ident.evaluaciones_conocimiento_sistema.count(), 1)
        self.assertEqual(ActividadFisica.objects.get().dias_ejercicio_semana, 3)
        self.assertEqual(HabitosAlimenticios.objects.get().vasos_agua_dia, 6)
        self.assertEqual(ConocimientoSistema.objects.get().conoce_sistema_publico_climaterio, 'NO')
