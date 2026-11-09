"""
Complemento de la Fase 37C: revisa los informes generados. Existen, abren, tienen sus imágenes y secciones, responden las 15 preguntas y no contienen afirmaciones prohibidas.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/verificar_informes_complemento.py
"""
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True
B = Path(__file__).resolve().parents[1]
INF = B / 'informes'
WORD = {'01_protocolo_complemento': 0, '02_reproduccion_ari': 1, '03_definicion_B1_B2': 1, '04_correspondencia_segmentos': 1, '05_fuera_de_muestra': 1, '06_estabilidad': 1, '07_informacion_por_bloques': 2, '08_complejidad_interpretabilidad': 0, '09_sin_segmentacion': 1, '10_limitaciones_imputaciones': 0, '11_ventajas_desventajas': 0, '12_informe_metodologico_final': 1, '15_preparacion_decision_37D': 0}
filas = []


def registrar(nombre, ok, detalle=''):
    filas.append({'comprobacion': nombre, 'resultado': 'superada' if ok else 'FALLA', 'detalle': detalle})


def texto(nombre):
    with zipfile.ZipFile(INF / f'{nombre}.docx') as z:
        x = z.read('word/document.xml').decode('utf-8')
        im = [n for n in z.namelist() if n.startswith('word/media/')]
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)), im


t = {}
for nombre, esperadas in WORD.items():
    x, im = texto(nombre)
    t[nombre] = x
    registrar(f'{nombre}: abre, con texto e imágenes', len(x) > 500 and len(im) >= esperadas, f'{len(x)} caracteres, {len(im)} imágenes')
    registrar(f'{nombre}: sin campos sin resolver', not re.search(r'\bnan\b|\{[a-zA-Z_]+\}|\bNone\b', x), '')
for nombre in ('00_indice_entregables', '13_informe_pruebas', '14_informe_integridad'):
    registrar(f'{nombre}: existe', (INF / f'{nombre}.md').stat().st_size > 300, '')
f = t['12_informe_metodologico_final']
faltan = [i for i in range(1, 16) if not re.search(rf'\b{i}\. ¿', f)]
registrar('Final: 15 preguntas', not faltan, f'Faltan: {faltan}')
registrar('Final: lenguaje sencillo', 'lenguaje sencillo' in f, '')
registrar('Final: recomendación no vinculante', 'no vinculante' in f.lower() and 'responsable del proyecto' in f, '')
registrar('Final: Fase 37D no iniciada', 'la Fase 37D no se inició' in f, '')
nuevos = {k: v for k, v in t.items() if not k.startswith('01')}
registrar('Sintético declarado', all('sintético' in v for v in nuevos.values()), '')
registrar('ARI no es porcentaje', '68 % de aciertos' in t['02_reproduccion_ari'] and 'no significa' in t['02_reproduccion_ari'].lower().replace('**', ''), '')
registrar('B1 no es validación independiente', 'no una validación independiente' in t['03_definicion_B1_B2'], '')
registrar('B2 no es del todo independiente', all('tampoco es del todo independiente' in t[k] for k in ('03_definicion_B1_B2', '12_informe_metodologico_final')), '')
registrar('Estabilidad con advertencia estructural', 'estructural' in t['06_estabilidad'], '')
registrar('Circularidad declarada', 'circular' in t['07_informacion_por_bloques'], '')
registrar('Comprobación posterior rotulada', 'posterior al sellado' in t['07_informacion_por_bloques'], '')
registrar('Moda sin afirmar corrección', 'No se afirma que la moda de 529 sea más correcta' in t['10_limitaciones_imputaciones'], '')
prohibidas = [r'grupos naturales confirmados', r'tipos clínicos de', r'se confirma(?:n)? (?:la existencia|grupos)', r'modelo validado', r'clasificación clínica validada']
hallados = [(k, p) for k, v in nuevos.items() for p in prohibidas if re.search(p, v)]
registrar('Sin afirmaciones prohibidas', not hallados, str(hallados))
registrar('Figuras', len(list((B / 'figuras').glob('*.png'))) == 8, '')
registrar('Tabla final y recomendación guardadas', (B / 'comparacion_final' / 'ventajas_desventajas.csv').exists() and (B / 'comparacion_final' / 'recomendacion_no_vinculante.json').exists(), '')
d = pd.DataFrame(filas)
d.to_csv(B / 'pruebas' / 'verificacion_informes.csv', index=False, encoding='utf-8', lineterminator='\n')
print(d[d['resultado'] != 'superada'].to_string() if (d['resultado'] != 'superada').any() else f'{len(d)} comprobaciones superadas')
sys.exit(int((d['resultado'] != 'superada').any()))
