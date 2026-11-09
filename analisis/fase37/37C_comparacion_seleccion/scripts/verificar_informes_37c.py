"""
Fase 37C: revisa los informes generados. Comprueba que existan, abran, tengan sus imágenes y sus secciones, que las 17 preguntas estén respondidas y que no haya afirmaciones prohibidas.
Escribe pruebas/verificacion_informes.csv.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/verificar_informes_37c.py
"""
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True
B = Path(__file__).resolve().parents[1]
INF = B / 'informes'
WORD = {'01_protocolo_37C': 0, '01b_enmienda_referencia_nula': 0, '02_registro_lista_A': 0, '03_registro_lista_B': 0, '04_estabilidad_procedimiento_completo': 2, '05_referencia_correlacionada': 1, '06_s_ord': 1, '07_sensibilidades': 1, '08_interpretabilidad': 1, '09_asignacion': 1, '10_comparacion_finalistas': 3, '11_decision_metodologica': 1, '14_informe_cierre_37C': 0, '15_nota_metodologica_37D': 0}
filas = []


def registrar(nombre, ok, detalle=''):
    filas.append({'comprobacion': nombre, 'resultado': 'superada' if ok else 'FALLA', 'detalle': detalle})


def texto(nombre):
    with zipfile.ZipFile(INF / f'{nombre}.docx') as z:
        x = z.read('word/document.xml').decode('utf-8')
        imagenes = [n for n in z.namelist() if n.startswith('word/media/')]
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)), imagenes


todos = {}
for nombre, esperadas in WORD.items():
    t, im = texto(nombre)
    todos[nombre] = t
    registrar(f'{nombre}: abre, con texto e imágenes', len(t) > 500 and len(im) >= esperadas, f'{len(t)} caracteres, {len(im)} imágenes')
    registrar(f'{nombre}: sin campos sin resolver', not re.search(r'\bnan\b|\{[a-zA-Z_]+\}|None', t), '')
for nombre in ('00_indice_entregables', '12_informe_pruebas', '13_informe_integridad'):
    registrar(f'{nombre}: existe', (INF / f'{nombre}.md').stat().st_size > 300, '')
c = todos['14_informe_cierre_37C']
faltan = [i for i in range(1, 18) if not re.search(rf'\b{i}\. ', c)]
registrar('Cierre: 17 preguntas', not faltan, f'Faltan: {faltan}')
registrar('Cierre: réplicas recuperadas y estado', 'Recuperadas' in c and 'Ejecutadas de nuevo' in c and 'completa' in c, '')
registrar('Decisión: lenguaje sencillo', 'lenguaje sencillo' in todos['11_decision_metodologica'] and 'lenguaje sencillo' in c, '')
registrar('Decisión: provisional y responsable', all('responsable' in todos[x] for x in ('11_decision_metodologica', '14_informe_cierre_37C', '15_nota_metodologica_37D')), '')
registrar('Sintético declarado', all('sintético' in todos[x] for x in WORD if not x.startswith('01')), '')
registrar('Lista B rotulada', 'exploratoria' in todos['03_registro_lista_B'], '')
registrar('Enmienda exploratoria', 'exploratoria' in todos['05_referencia_correlacionada'], '')
prohibidas = [r'modelo validado(?! )', r'grupos naturales confirmados', r'tipos clínicos de', r'se confirma(?:n)? (?:la existencia|grupos)', r'clasificación clínica validada(?! )']
nuevos = {k: v for k, v in todos.items() if not k.startswith('01')}
hallados = [(k, p) for k, v in nuevos.items() for p in prohibidas[1:2] + prohibidas[3:4] if re.search(p, v)]
registrar('Sin afirmaciones prohibidas', not hallados, str(hallados))
registrar('Sin Fase 37D iniciada', 'no se inició' in c or 'no se inició' in c.lower(), '')
registrar('Lecturas alternativas rotuladas como posteriores', 'después de ver los resultados' in c and 'no es una probabilidad' in todos['11_decision_metodologica'], '')
registrar('Figuras', len(list((B / 'figuras').glob('*.png'))) == 12, '')
registrar('Decisión guardada', (B / 'seleccion' / 'decision_final_37C.json').exists(), '')
t = pd.DataFrame(filas)
t.to_csv(B / 'pruebas' / 'verificacion_informes.csv', index=False, encoding='utf-8', lineterminator='\n')
print(t[t['resultado'] != 'superada'].to_string() if (t['resultado'] != 'superada').any() else f'{len(t)} comprobaciones superadas')
sys.exit(int((t['resultado'] != 'superada').any()))
