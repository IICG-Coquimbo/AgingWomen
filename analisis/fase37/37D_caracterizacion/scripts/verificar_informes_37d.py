"""Fase 37D: verificación de los informes generados (existencia, imágenes, valores vacíos y advertencias obligatorias)."""
import re
import sys
import zipfile

import nucleo_37d as N
import pandas as pd

sys.dont_write_bytecode = True
INF = N.BASE / 'informes'
F = INF / 'fuentes'
WORD = ['01_protocolo_37D', '01b_nota_posterior', '03_diccionario_variables', '04_caracterizacion_general', '05_caracterizacion_segmentos_A', '06_caracterizacion_segmentos_B1',
        '07_individual_frente_a_MRS', '08_mrs_por_segmento_A', '09_mrs_por_segmento_B1', '10_comparacion_tres_perspectivas', '11_sensibilidades_limitaciones',
        '12_figuras_tablas', '15_informe_final_37D', '16_nota_fases_38_39']
MD = ['00_indice_entregables', '02_integridad_inicial', '13_informe_pruebas', '14_informe_integridad_final']
VACIOS = re.compile(r'\b(nan|NaN|None|inf)\b|\{[a-z_]+\}')
OBLIGATORIAS = {
    'sintético': ['04', '05', '06', '07', '08', '09', '10', '11', '15', '16'],
    'no constituye una validación independiente': ['05'],
    'no es un modelo clínico': ['06'],
    'El ARI no es un porcentaje': ['10'],
    'No se usa para elegir': ['10'],
    'No ejecuta Apriori': ['16'],
    'no por haber resultado asociadas': ['16'],
    'No se elige ningún modelo': ['15'],
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
    if w not in ('01_protocolo_37D', '01b_nota_posterior'):
        m = VACIOS.findall(re.sub(r'<[^>]+>', ' ', xml))
        ok(f'{w}: sin valores vacíos ni campos sin sustituir', not m, ', '.join(map(str, m[:5])))
for m in MD:
    t = (INF / f'{m}.md').read_text(encoding='utf-8')
    ok(f'{m}: existe y sin valores vacíos', not VACIOS.findall(t))
for frase, docs in OBLIGATORIAS.items():
    falta = [d for d in docs if frase.lower() not in textos[d].lower()]
    ok(f'Advertencia «{frase}»', not falta, ', '.join(falta))
todo = ' '.join(textos.values()).lower()
ok('Sin nombres clínicos para los grupos', not re.search(r'grupo \d \((sedentari|activ|trabajador|soltera|cuidadora)', todo))
ok('Índice enlaza los 16 entregables', all(f'| {i} |' in (INF / '00_indice_entregables.md').read_text(encoding='utf-8') for i in range(1, 17)))
ok('Resumen JSON existe', (N.BASE / 'resultados' / 'resumen_37D.json').exists())
d = pd.DataFrame(filas)
d.to_csv(N.BASE / 'pruebas' / 'verificacion_informes.csv', index=False, encoding='utf-8')
print(f"{(d['resultado'] == 'superada').sum()}/{len(d)} verificaciones superadas")
print(d[d['resultado'] != 'superada'].to_string())
sys.exit(int((d['resultado'] != 'superada').any()))
