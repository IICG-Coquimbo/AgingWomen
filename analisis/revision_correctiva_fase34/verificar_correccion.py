"""
Corrección controlada de la Fase 34: verificación final, tabla H01-H17 y relación de archivos.

Uso, desde la raíz del proyecto, después de generar todos los productos:
    python analisis/revision_correctiva_fase34/verificar_correccion.py

Compara el manifiesto SHA-256 de la línea base con uno nuevo. Solo pueden cambiar los archivos de código
autorizados. Termina con error si cambió cualquier otro archivo, o si falla una comprobación.
Escribe en manifiestos/ y tablas/.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))

import manifiesto as MANIFIESTO  # noqa: E402

TABLAS = AQUI / 'tablas'
AUTORIZADOS = {
    'analisis/eda/univariado.py': 'Rótulos reproducibles de las figuras (H10)',
    'analisis/eda_univariado.py': 'Textos del informe y docstring (H10, A1)',
    'analisis/eda/informe_multivariado.py': 'Textos del informe (H05, H12, H14)',
    'analisis/eda/multivariado.py': 'Comentarios (H05, H14)',
    'analisis/eda/informe_usuaria.py': 'Textos del informe (H13, H15)',
    'analisis/eda_usuaria.py': 'Comentarios (H13)',
    'analisis/eda/variables.py': 'Comentarios (H13, H15)',
    'analisis/limpieza/informe.py': 'Texto de la sección 6.3 (H16)',
}
GRUPOS = [
    ('Conjuntos sintéticos verdadero y sucio', 'datos/sintetico/'),
    ('Conjunto limpio de 546 registros', 'datos/limpio_usuaria/'),
    ('Conjuntos analíticos, incluido el de 529 y 33 variables', 'datos/analitico/'),
    ('Shannon y FCBF: revisión del 03-11', 'analisis/reunion_2026-11-03/'),
    ('Shannon y FCBF: complementarios', 'analisis/complementario'),
    ('Resultados del EDA y de la Fase 35', 'analisis/resultados/'),
    ('Random Forest', 'analisis/random_forest'),
    ('Figuras históricas', 'analisis/figuras/'),
    ('Informes Word de la Fase 35B', 'analisis/informes_fase35b/'),
]
ACCIONES = {
    'H01': ('Asociación verificada; sin nota de contexto', 'Nota en 34C con cifras, dominancia, exclusión y alcance no clínico', 'Verificado; nota agregada'),
    'H02': ('22 imputaciones sin documentar', 'Documentadas en 34B; indicadores solo de auditoría', 'Conservado y documentado'),
    'H03': ('21 imputaciones sin documentar', 'Documentadas en 34B, con su efecto sobre cantidad', 'Conservado y documentado'),
    'H04': ('Dependencia de doble carga sin documentar', 'Documentada; sigue excluida', 'Conservado y documentado'),
    'H05': ('«Quienes trabajan» = 309 sin aclarar', 'Denominadores aclarados en 34B, 34C, 34D y 34E; rótulos nuevos', 'Corregido en versiones revisadas; texto de 35A sin tocar'),
    'H06': ('Valor 3 en las 22, sin tratamiento definido', 'Propuesta en la nota para la Fase 36; datos intactos', 'Limitación pendiente: requiere decisión'),
    'H07': ('Solo q = 0,073, con «no informado»', 'Cuadro complementario; q histórico conservado', 'Corregido con resultado complementario'),
    'H08': ('Bajo peso excluido sin aviso', 'Exclusión y alternativas documentadas', 'Conservado y documentado'),
    'H09': ('Diferencia 529 / cuidadoras sin explicar', 'Explicación agregada en 34C', 'Conservado y documentado'),
    'H10': ('41 figuras con «faltante = 0», sin separar imputadas', '73 figuras nuevas y código actualizado; históricas intactas', 'Corregido'),
    'H11': ('imputados_34B es una cota', 'Tabla exacta publicada; columna histórica y su código sin cambios', 'Corregido por anexo; el código aún calcula la cota'),
    'H12': ('«Sin imputaciones» en 34E', 'Frase corregida en la versión revisada y en el generador', 'Corregido'),
    'H13': ('Etapa como control en script y textos', 'Textos y comentarios alineados; rótulo del script sin cambiar', 'Corrección parcial: rótulo pendiente de autorización'),
    'H14': ('38, 35 y 33 sin distinguir', 'Distinción agregada; figura histórica sin regenerar', 'Corregido en texto; figura histórica conservada'),
    'H15': ('34C decía que el IMC no se imputa', 'Nota sobre la decisión del 27-10 en 34B y 34C', 'Corregido'),
    'H16': ('Tabla 6.3 sumaba error y regla', '1 error y 196 por regla, separados', 'Corregido'),
    'H17': ('Identificación incompleta sin alcance claro', 'Versión documental de Random Forest; sin reejecutar', 'Documentado; efecto sin medir'),
}


def leer_manifiesto(etapa):
    with (AQUI / 'manifiestos' / f'manifiesto_{etapa}.csv').open(encoding='utf-8') as f:
        return {r['ruta']: r['sha256'] for r in csv.DictReader(f)}


def git(*args):
    return subprocess.run(['git', *args], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout


def tabla_hallazgos():
    matriz = pd.read_csv(TABLAS / 'matriz_impacto.csv', encoding='utf-8-sig')
    filas = [{'id': m.id, 'clase': m.clase, 'hallazgo': m.hallazgo, 'estado_antes': ACCIONES[m.id][0],
              'accion': ACCIONES[m.id][1], 'estado_despues': ACCIONES[m.id][2]} for m in matriz.itertuples()]
    filas.append({'id': 'A1', 'clase': 'Adicional (fuera de los 17)',
                  'hallazgo': 'La figura e informe de horas sentada decían «valores observados» e incluían 27 imputadas.',
                  'estado_antes': 'Sin detectar en el diagnóstico', 'accion': 'Título y texto corregidos; cifras históricas sin recalcular', 'estado_despues': 'Corregido'})
    t = pd.DataFrame(filas)
    t.to_csv(TABLAS / 'hallazgos_antes_despues.csv', index=False, encoding='utf-8-sig')
    return matriz


def relacion_archivos(linea_base_fecha, modificados):
    filas = [{'ruta': r, 'categoria': 'Código modificado con autorización', 'motivo': AUTORIZADOS[r], 'original_relacionado': 'versión en HEAD 745d689'} for r in modificados]
    historico = {'informe_limpieza_usuaria_revisado.md': 'analisis/informe_limpieza_usuaria.md', 'informe_eda_usuaria_revisado.md': 'analisis/informe_eda_usuaria.md',
                 'informe_eda_univariado_revisado.md': 'analisis/informe_eda_univariado.md', 'informe_eda_multivariado_revisado.md': 'analisis/informe_eda_multivariado.md',
                 'informe_random_forest_33_variables_revisado.docx': 'analisis/random_forest_revision_35b_33_variables/informe/informe_random_forest_33_variables.docx'}
    for r in sorted(AQUI.rglob('*')):
        if not r.is_file() or '__pycache__' in r.parts or r.stat().st_mtime < linea_base_fecha or r.name.startswith('~$'):
            continue
        rel = r.relative_to(RAIZ).as_posix()
        carpeta = r.parent.name
        categoria = {'figuras_34D_revisadas': 'Figura revisada', 'informes_revisados': 'Informe revisado', 'informe': 'Entregable Word',
                     'tablas': 'Tabla', 'manifiestos': 'Manifiesto'}.get(carpeta, 'Script de la corrección')
        original = historico.get(r.name, f'analisis/figuras/eda_univariado/{r.name}' if carpeta == 'figuras_34D_revisadas' else '')
        filas.append({'ruta': rel, 'categoria': categoria, 'motivo': 'Creado en esta corrección', 'original_relacionado': original})
    t = pd.DataFrame(filas)
    t.to_csv(TABLAS / 'relacion_archivos.csv', index=False, encoding='utf-8-sig')
    return t


def main():
    fecha_base = (AQUI / 'manifiestos' / 'manifiesto_correccion_antes.csv').stat().st_mtime
    MANIFIESTO.main('correccion_despues')
    antes, despues = leer_manifiesto('correccion_antes'), leer_manifiesto('correccion_despues')
    cambiados = sorted(r for r in antes if r in despues and antes[r] != despues[r])
    faltan, nuevos = sorted(set(antes) - set(despues)), sorted(set(despues) - set(antes))
    no_autorizados = [r for r in cambiados if r not in AUTORIZADOS]
    versionados = [r for r in git('diff', '--name-only', 'HEAD').split() if r]
    head_a = (AQUI / 'manifiestos' / 'head_correccion_antes.txt').read_text().strip()
    head_d = (AQUI / 'manifiestos' / 'head_correccion_despues.txt').read_text().strip()

    filas = []

    def comprobar(nombre, ok, detalle=''):
        filas.append({'comprobacion': nombre, 'resultado': 'OK' if ok else 'FALLA', 'detalle': detalle})

    comprobar('Archivos fuera de la carpeta de revisión: ninguno nuevo ni eliminado', not faltan and not nuevos, f'faltan {len(faltan)}; nuevos {len(nuevos)}')
    comprobar('Solo cambió código autorizado', not no_autorizados, f'{len(cambiados)} modificados; no autorizados: {no_autorizados}')
    comprobar('Git: versionados modificados = código autorizado', set(versionados) == set(cambiados), ', '.join(versionados))
    comprobar('HEAD sin cambios: sin commit', head_a == head_d, head_d[:7])
    for nombre, prefijo in GRUPOS:
        rutas = [r for r in antes if r.startswith(prefijo)]
        distintos = [r for r in rutas if despues.get(r) != antes[r]]
        comprobar(f'SHA-256 idéntico: {nombre}', bool(rutas) and not distintos, f'{len(rutas)} archivos')
    informes = [r for r in antes if r.startswith('analisis/') and r.count('/') == 1 and r.endswith('.md')]
    comprobar('SHA-256 idéntico: informes históricos .md', all(despues.get(r) == antes[r] for r in informes), f'{len(informes)} archivos')
    protegidos = [r for r in antes if r not in AUTORIZADOS]
    comprobar('SHA-256 idéntico: todo lo protegido', all(despues.get(r) == antes[r] for r in protegidos), f'{len(protegidos)} archivos')

    d33 = pd.read_csv(RAIZ / 'datos' / 'analitico' / 'dataset_fase35_33_variables.csv', encoding='utf-8-sig')
    comprobar('Conjunto analítico: 529 registros', len(d33) == 529, str(len(d33)))
    limpio = pd.read_csv(RAIZ / 'datos' / 'limpio_usuaria' / 'dataset_usuaria_limpio.csv', dtype=str, encoding='utf-8-sig')
    comprobar('Conjunto limpio: 546 registros', len(limpio) == 546, str(len(limpio)))
    for b in (10000, 50000):
        rel = pd.read_csv(RAIZ / 'analisis' / 'reunion_2026-11-03' / 'revision_33_variables' / f'permutaciones_{b}' / 'relevancia_33.csv', encoding='utf-8-sig')
        pob = rel['poblacion'].value_counts().to_dict()
        comprobar(f'Shannon {b}: 33 variables, 30 generales, 2 laborales y 1 de cuidadoras', len(rel) == 33 and pob == {'general': 30, 'laboral': 2, 'cuidadoras': 1}, str(pob))
        fuera = {'usa_medicamentos_diabetes', 'doble_carga', 'prevision'} & set(rel['variable'])
        comprobar(f'Shannon {b}: siguen excluidas diabetes, doble carga y previsión', not fuera, str(sorted(fuera)))
    t_integ = pd.DataFrame(filas)
    t_integ.to_csv(TABLAS / 'verificacion_integridad.csv', index=False, encoding='utf-8-sig')

    matriz = tabla_hallazgos()
    conteo = matriz['clase'].value_counts().to_dict()
    relacion = relacion_archivos(fecha_base, cambiados)
    (TABLAS / 'comparacion_correccion.json').write_text(json.dumps({
        'archivos_linea_base': len(antes), 'modificados_autorizados': cambiados, 'no_autorizados': no_autorizados, 'nuevos_fuera_de_revision': nuevos, 'faltan': faltan,
        'protegidos_identicos': len(protegidos), 'head': head_d, 'clases': conteo, 'archivos_creados': int((relacion['motivo'] == 'Creado en esta corrección').sum()),
        'claves': {c: antes[c] for c in ['datos/analitico/dataset_fase35_33_variables.csv', 'datos/limpio_usuaria/dataset_usuaria_limpio.csv',
                                         'datos/sintetico/dataset_usuaria_verdad.csv', 'datos/sintetico/dataset_usuaria_sucio.csv']},
    }, ensure_ascii=False, indent=1), encoding='utf-8')
    (TABLAS / 'cierre.json').write_text(json.dumps({
        'hallazgos': json.loads(pd.read_csv(TABLAS / 'hallazgos_antes_despues.csv', encoding='utf-8-sig').to_json(orient='records', force_ascii=False)),
        'integridad': json.loads(t_integ.to_json(orient='records', force_ascii=False)),
        'codigo': [{'ruta': r, 'motivo': AUTORIZADOS[r]} for r in cambiados],
        'creados': relacion[relacion['motivo'] == 'Creado en esta corrección']['categoria'].value_counts().to_dict(),
        'protegidos': len(protegidos), 'linea_base': len(antes), 'head': head_d[:7], 'hash33': antes['datos/analitico/dataset_fase35_33_variables.csv'],
        'hash_limpio': antes['datos/limpio_usuaria/dataset_usuaria_limpio.csv'],
    }, ensure_ascii=False, indent=1), encoding='utf-8')
    print(t_integ.to_string())
    print('clases:', conteo)
    print('creados:', relacion['categoria'].value_counts().to_dict())
    sys.exit(1 if (t_integ['resultado'] == 'FALLA').any() else 0)


if __name__ == '__main__':
    main()
