"""
Fase 40D: genera el catálogo versionado que lee la plataforma
(src/apps/encuestas/orientaciones_catalogo.json) a partir de los borradores
40D-1_catalogo_borrador.md y 40D-1_fuentes.md, para que el contenido tenga una
sola fuente. Uso (desde la raíz del repositorio):

    python analisis/fase40/40D_orientaciones/generar_catalogo_json.py

El estado del catálogo queda en 'borrador_no_validado' hasta que una revisión
clínica lo cambie a 'aprobado' (y registre quién y cuándo).
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
SALIDA = RAIZ / 'src' / 'apps' / 'encuestas' / 'orientaciones_catalogo.json'
VERSION = 'catalogo-40D1-borrador-2026-11-06'
FECHA_CONSULTA = '2026-11-06'

REF = re.compile(r'\s*\[(F\d{2}(?:,\s*F\d{2})*)\]')


def limpiar(texto):
    """Quita marcas de Markdown y de redacción; devuelve (texto, [fuentes])."""
    fuentes = []
    for grupo in REF.findall(texto):
        fuentes += [f.strip() for f in grupo.split(',')]
    texto = REF.sub('', texto)
    texto = re.sub(r'\*\(.*?\)\*', '', texto)      # notas internas del borrador, en cursiva
    texto = texto.replace('**[redacción]** ', '').replace('**', '').replace('\\*', '*')
    texto = re.sub(r'`([^`]*)`', r'\1', texto)
    return texto.strip(), fuentes


def secciones_de(bloque):
    """{nombre de sección: [(texto, fuentes)]} a partir de los encabezados en negrita."""
    secciones, actual = {}, None
    for linea in bloque.splitlines():
        m = re.match(r'^\*\*(.+?)\*\*(.*)$', linea.strip())
        if m and not linea.startswith('- '):
            actual = m.group(1).strip()
            secciones[actual] = {'nota': limpiar(m.group(2))[0], 'items': []}
            continue
        if actual is None or not linea.strip() or linea.startswith('*('):
            continue
        texto = linea.strip()
        if linea.startswith('  - '):                     # sub-viñeta de la anterior
            secciones[actual]['items'].append(limpiar(texto[2:]) + (True,))
        elif texto.startswith('- '):
            secciones[actual]['items'].append(limpiar(texto[2:]) + (False,))
        else:
            secciones[actual]['items'].append(limpiar(texto) + (False,))
    return secciones


def item(secciones, prefijo):
    for nombre, contenido in secciones.items():
        if nombre.startswith(prefijo):
            return nombre, contenido
    raise ValueError(f'falta la sección {prefijo!r}')


def lista(contenido):
    return [{'texto': t, 'fuentes': f, 'sub': sub} for t, f, sub in contenido['items'] if t]


def orientaciones(md):
    salida = []
    for bloque in re.split(r'\n(?=## O-\d{2} · )', md)[1:]:
        cab = re.match(r'## (O-\d{2}) · (.+)', bloque)
        pregunta = re.search(r'`(pregunta_\d+)`', bloque).group(1)
        cuerpo = bloque.split('\n---')[0]
        secs = secciones_de(cuerpo.split('\n', 2)[2])
        _, que_es = item(secs, '¿Qué es?')
        _, relacion = item(secs, 'Relación con la menopausia')
        _, cuidado = item(secs, 'Lo que puedes hacer')
        nombre_consulta, consulta = item(secs, '¿Cuándo consultar')
        nombre_alerta, alertas = item(secs, 'Señales de alerta')
        alertas_lista = lista(alertas)
        sin_alertas = (len(alertas_lista) == 1 and alertas_lista[0]['texto'].startswith('No se identificaron'))
        salida.append({
            'id': cab.group(1), 'titulo': cab.group(2).strip(), 'pregunta': pregunta,
            'que_es': lista(que_es), 'relacion': lista(relacion), 'autocuidado': lista(cuidado),
            'cuando_consultar': {'titulo': '¿Cuándo consultar a un profesional de salud?',
                                 'nota': consulta['nota'].strip(' ()'), 'items': lista(consulta)},
            'senales_alerta': {'titulo': nombre_alerta.split(':')[0].strip(),
                               'nota': (nombre_alerta.split(':', 1)[1].strip() if ':' in nombre_alerta else ''),
                               'items': [] if sin_alertas else alertas_lista,
                               'sin_alertas_texto': alertas_lista[0]['texto'] if sin_alertas else ''},
        })
    return salida


def aviso(md):
    bloque = md.split('## Aviso general')[1].split('**Cómo se muestra')[0]
    lineas = [l[1:].strip() for l in bloque.splitlines() if l.startswith('>')]
    parrafos = [limpiar(l)[0] for l in lineas if l and not l.startswith('**Sobre estas')]
    return {'titulo': 'Sobre estas orientaciones', 'parrafos': parrafos}


def fuentes(md):
    salida = {}
    for bloque in re.split(r'\n(?=### F\d{2} · )', md)[1:]:
        cab = re.match(r'### (F\d{2}) · (.+)', bloque)
        urls = re.findall(r'https?://[^\s)·]+', bloque.split('- **Respalda')[0])
        fecha = re.search(r'\*\*Fecha(?: de la página)?:\*\* (.+)', bloque)
        salida[cab.group(1)] = {'referencia': cab.group(2).strip(), 'url': urls[0] if urls else '',
                                'fecha_fuente': fecha.group(1).replace('**', '').strip() if fecha else '',
                                'fecha_consulta': FECHA_CONSULTA}
    return salida


def main():
    catalogo_md = (AQUI / '40D-1_catalogo_borrador.md').read_text(encoding='utf-8')
    fuentes_md = (AQUI / '40D-1_fuentes.md').read_text(encoding='utf-8')
    datos = {
        'version': VERSION,
        'estado': 'borrador_no_validado',
        'aprobacion': None,
        'aviso': aviso(catalogo_md),
        'orientaciones': orientaciones(catalogo_md),
        'fuentes': fuentes(fuentes_md),
    }
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f"{SALIDA.relative_to(RAIZ)}: {len(datos['orientaciones'])} orientaciones, "
          f"{len(datos['fuentes'])} fuentes, versión {VERSION}")


if __name__ == '__main__':
    main()
