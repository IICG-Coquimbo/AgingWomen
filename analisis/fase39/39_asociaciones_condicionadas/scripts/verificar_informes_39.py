"""Fase 39: verificación de los informes generados (existencia, imágenes, valores vacíos, advertencias obligatorias, 20 preguntas e índice)."""
import re
import sys
import zipfile

import nucleo_39 as N
import pandas as pd

sys.dont_write_bytecode = True
INF = N.BASE / 'informes'
F = INF / 'fuentes'
WORD = ['02_protocolo_39', '04_diccionario_estratos', '05_tamanos_frecuencias_basales', '06_preparacion_matrices_condicionadas', '07_reglas_por_trabajo', '08_reglas_por_pareja',
        '09_reglas_por_ejercicio', '10_reglas_por_cuidado', '11_referencias_nulas_estrato', '12_comparacion_formal_estratos', '13_redundancia', '14_sensibilidades',
        '15_comparacion_exploratoria_A_B1', '16_figuras_tablas', '19_informe_cierre_39', '20_nota_logica_tablero']
MD = ['01_indice_entregables', '03_integridad_inicial', '17_informe_pruebas', '18_informe_integridad_final']
VACIOS = re.compile(r'\b(nan|NaN|None|inf)\b|\{[a-z_]+\}')
TODOS = ['04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '19', '20']
OBLIGATORIAS = {
    'sintético': TODOS,
    'ninguna asociación indica causa': TODOS,
    'exploratorio': TODOS,
    'no permiten recomendaciones de salud': TODOS,
    'no** responde B': ['12'],
    'Westfall-Young': ['11'],
    'no solo a las seleccionadas': ['11'],
    'No demuestra validez': ['12'],
    'No implementa nada ni modifica Django': ['20'],
    'no** en asociaciones estadísticas': ['20'],
    'revisión obligatoria': ['20'],
    'solo como comparación exploratoria secundaria': ['15'],
    'no aporta evidencia': ['15'],
}
filas = []


def ok(nombre, cond, detalle=''):
    filas.append({'verificacion': nombre, 'resultado': 'superada' if cond else 'FALLA', 'detalle': detalle})


textos = {}
for w in WORD:
    md, dx = F / f'{w}.md', INF / f'{w}.docx'
    ok(f'{w}: fuente y Word existen', md.exists() and dx.exists())
    t = md.read_text(encoding='utf-8')
    textos[w[:2]] = textos.get(w[:2], '') + t
    imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', t)
    faltan = [i for i in imgs if not (md.parent / i).resolve().exists()]
    ok(f'{w}: imágenes referidas existen', not faltan, ', '.join(faltan))
    with zipfile.ZipFile(dx) as z:
        media = [x for x in z.namelist() if x.startswith('word/media/')]
        xml = z.read('word/document.xml').decode('utf-8')
    ok(f'{w}: Word contiene las imágenes', len(media) >= len(set(imgs)), f'{len(media)} en Word, {len(set(imgs))} referidas')
    if w != '02_protocolo_39':
        m = VACIOS.findall(re.sub(r'<[^>]+>', ' ', xml))
        ok(f'{w}: sin valores vacíos ni campos sin sustituir', not m, ', '.join(map(str, m[:5])))
for m in MD:
    t = (INF / f'{m}.md').read_text(encoding='utf-8')
    ok(f'{m}: existe y sin valores vacíos', not VACIOS.findall(t))
for frase, docs in OBLIGATORIAS.items():
    falta = [d for d in docs if frase.lower() not in textos[d].lower()]
    ok(f'Advertencia «{frase}»', not falta, ', '.join(falta))
cierre = textos['19']
ok('Cierre responde las 20 preguntas', all(f'**{i}. ' in cierre for i in range(1, 21)))
conc = N.leer_json(N.BASE / 'resultados' / 'conclusion_39.json')
ok('Cierre informa el resultado mecánico', f"Resultado {conc['resultado']}" in cierre)
todo = ' '.join(textos.values()).lower()
ok('Sin lenguaje causal ni clínico afirmativo', not re.search(r'\b(causa[n]? (los|más|menos) síntomas|se recomienda (hacer|evitar|consumir)|factor de riesgo|previene|protege contra)', todo))
idx = (INF / '01_indice_entregables.md').read_text(encoding='utf-8')
ok('Índice enlaza los 20 entregables', all(f'| {i} |' in idx for i in range(1, 21)))
rutas = re.findall(r'`((?:informes|protocolo|preparacion|reglas|estabilidad|referencia_nula|comparacion|redundancia|sensibilidades|ab1|figuras|pruebas|integridad|resultados)/[^`*]*)`', idx)
faltan = [r for r in rutas if not (N.BASE / r).exists()]
ok('Archivos del índice existen', not faltan, ', '.join(faltan))
ok('Resumen JSON existe', (INF / 'resumen_39.json').exists())
d = pd.DataFrame(filas)
d.to_csv(N.BASE / 'pruebas' / 'verificacion_informes.csv', index=False, encoding='utf-8')
print(f"{(d['resultado'] == 'superada').sum()}/{len(d)} verificaciones superadas")
print(d[d['resultado'] != 'superada'].to_string())
sys.exit(int((d['resultado'] != 'superada').any()))
