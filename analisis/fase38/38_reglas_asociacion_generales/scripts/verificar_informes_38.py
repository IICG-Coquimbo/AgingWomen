"""Fase 38: verificación de los informes generados (existencia, imágenes, valores vacíos y advertencias obligatorias)."""
import re
import sys
import zipfile

import nucleo_38 as N
import pandas as pd

sys.dont_write_bytecode = True
INF = N.BASE / 'informes'
F = INF / 'fuentes'
WORD = ['01_protocolo_38', '03_diccionario_variables_categorias', '04_agrupacion_categorias_escasas', '05_matriz_transaccional_trazabilidad', '06_equivalencia_apriori_fpgrowth',
        '07_reglas_generales', '08_soporte_confianza_lift_cobertura', '09_redundancia', '10_estabilidad', '11_referencia_nula', '12_sensibilidades', '13_figuras_tablas',
        '16_informe_cierre_38', '17_nota_fase_39']
MD = ['00_indice_entregables', '02_integridad_inicial', '14_informe_pruebas', '15_informe_integridad_final']
VACIOS = re.compile(r'\b(nan|NaN|None|inf)\b|\{[a-z_]+\}')
OBLIGATORIAS = {
    'sintético': ['03', '04', '05', '07', '08', '09', '10', '11', '12', '13', '16', '17'],
    'ninguna asociación indica causa': ['07', '16', '17'],
    'no permiten recomendaciones de salud': ['07', '16'],
    'no confirma nada': ['11'],
    'Westfall-Young': ['11'],
    'no solo a las seleccionadas': ['11'],
    'No demuestra validez': ['10'],
    'no las confirma de forma independiente': ['07', '16'],
    'No ejecuta ninguna comparación': ['17'],
    'siempre con su denominador': ['17'],
    'nunca como base obligatoria': ['17'],
    'no hay reglas suficientemente sólidas': ['16'],
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
    if w != '01_protocolo_38':
        m = VACIOS.findall(re.sub(r'<[^>]+>', ' ', xml))
        ok(f'{w}: sin valores vacíos ni campos sin sustituir', not m, ', '.join(map(str, m[:5])))
for m in MD:
    t = (INF / f'{m}.md').read_text(encoding='utf-8')
    ok(f'{m}: existe y sin valores vacíos', not VACIOS.findall(t))
for frase, docs in OBLIGATORIAS.items():
    falta = [d for d in docs if frase.lower() not in textos[d].lower()]
    ok(f'Advertencia «{frase}»', not falta, ', '.join(falta))
cierre = textos['16']
ok('Cierre responde las 20 preguntas', all(f'**{i}. ' in cierre for i in range(1, 21)))
todo = ' '.join(textos.values()).lower()
ok('Sin lenguaje causal ni clínico afirmativo', not re.search(r'\b(causa[n]? (los|más|menos) síntomas|se recomienda (hacer|evitar|consumir)|factor de riesgo|previene|protege contra)', todo))
idx = (INF / '00_indice_entregables.md').read_text(encoding='utf-8')
ok('Índice enlaza los 18 entregables', all(f'| {i} |' in idx for i in range(1, 19)))
rutas = re.findall(r'`((?:informes|protocolo|preparacion|reglas|estabilidad|referencia_nula|sensibilidades|figuras|pruebas|integridad)/[^`*]+)`', idx)
faltan = [r for r in rutas if not (N.BASE / r).exists()]
ok('Archivos del índice existen', not faltan, ', '.join(faltan))
ok('Resumen JSON existe', (INF / 'resumen_38.json').exists())
d = pd.DataFrame(filas)
d.to_csv(N.BASE / 'pruebas' / 'verificacion_informes.csv', index=False, encoding='utf-8')
print(f"{(d['resultado'] == 'superada').sum()}/{len(d)} verificaciones superadas")
print(d[d['resultado'] != 'superada'].to_string())
sys.exit(int((d['resultado'] != 'superada').any()))
