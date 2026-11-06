"""
Cierre de las Fases 34 y 35: compara el repositorio antes y después del cierre, y con la línea base de la corrección.

Distingue los cambios previos (corrección controlada) de los nuevos (H11 y H13). Solo lee los archivos protegidos.
Requiere haber ejecutado manifiesto_cierre.py con antes y despues.
Uso, desde analisis/: python cierre_fases_34_35/scripts/verificar_integridad_cierre.py
Escribe en cierre_fases_34_35/tablas/ verificacion_integridad_posterior.csv, cambios_detectados.csv e integridad.json.
"""
import csv
import json
import subprocess
from pathlib import Path

import pandas as pd

ANALISIS = Path(__file__).resolve().parents[2]
RAIZ = ANALISIS.parent
CIERRE = ANALISIS / 'cierre_fases_34_35'
TABLAS = CIERRE / 'tablas'
ANTES = CIERRE / 'integridad' / 'manifiesto_antes.csv'
DESPUES = CIERRE / 'integridad' / 'manifiesto_despues.csv'
BASE = ANALISIS / 'revision_correctiva_fase34' / 'manifiestos' / 'manifiesto_correccion_antes.csv'

NUEVOS_AUTORIZADOS = {'analisis/eda/univariado.py', 'analisis/eda_usuaria.py'}
PREVIOS_AUTORIZADOS = {'analisis/eda/univariado.py', 'analisis/eda_univariado.py', 'analisis/eda/informe_multivariado.py',
                       'analisis/eda/multivariado.py', 'analisis/eda/informe_usuaria.py', 'analisis/eda_usuaria.py',
                       'analisis/eda/variables.py', 'analisis/limpieza/informe.py'}
HEAD_ESPERADO = '745d689937a18c35b62fd25eccc401b169b20e11'

GRUPOS = {
    'Datasets': lambda r: r.startswith('datos/'),
    'Shannon y FCBF, revisión de 33 variables': lambda r: r.startswith('analisis/reunion_2026-11-03/'),
    'Shannon y FCBF, resultados de la Fase 35B': lambda r: r.startswith('analisis/resultados/usuaria/') or r.startswith('analisis/complementario_35b_q10/') or r.startswith('analisis/complementario_cuidados/'),
    'Random Forest': lambda r: r.startswith('analisis/random_forest_revision_35b'),
    'Informes históricos': lambda r: r.startswith('analisis/') and r.endswith(('.md', '.docx')) and 'revision_correctiva_fase34' not in r,
    'Figuras históricas': lambda r: r.startswith('analisis/figuras/'),
    'Entregables de la corrección controlada': lambda r: r.startswith('analisis/revision_correctiva_fase34/'),
}


def leer(ruta):
    return pd.read_csv(ruta, encoding='utf-8').set_index('ruta')['sha256']


def git(*a):
    return subprocess.run(['git', *a], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout.strip()


def comparar(a, b):
    comunes = a.index.intersection(b.index)
    return {'agregados': sorted(set(b.index) - set(a.index)), 'eliminados': sorted(set(a.index) - set(b.index)),
            'modificados': sorted(comunes[a[comunes] != b[comunes]])}


def main():
    TABLAS.mkdir(parents=True, exist_ok=True)
    a, d, base = leer(ANTES), leer(DESPUES), leer(BASE)
    nuevo = comparar(a, d)
    previo = comparar(base, d)
    filas = []

    def anotar(num, que, ok, detalle):
        filas.append({'punto': num, 'comprobacion': que, 'resultado': 'OK' if ok else 'NO CUMPLE', 'detalle': detalle})

    relevancia = pd.read_csv(ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables' / 'permutaciones_50000' / 'relevancia_33.csv', encoding='utf-8-sig')
    limpio = pd.read_csv(RAIZ / 'datos' / 'analitico' / 'dataset_fase35.csv', encoding='utf-8-sig', usecols=['participante_id'])
    anotar(1, 'Permanecen 529 participantes analíticas', len(limpio) == 529, f'{len(limpio)} filas en dataset_fase35.csv')
    anotar(2, 'Permanecen 33 variables elegibles', len(relevancia) == 33, f'{len(relevancia)} filas en relevancia_33.csv')

    def grupo(nombre):
        filtro = GRUPOS[nombre]
        rutas = [r for r in d.index if filtro(r)]
        cambios = [r for lista in nuevo.values() for r in lista if filtro(r)]
        return len(rutas), cambios

    conteos = {}
    for num, nombre, texto in ((3, 'Datasets', 'No cambiaron los datasets'),
                               (4, 'Shannon y FCBF, revisión de 33 variables', 'No cambiaron los resultados de Shannon ni de FCBF de la revisión de 33 variables'),
                               (5, 'Shannon y FCBF, resultados de la Fase 35B', 'No cambiaron los resultados de Shannon y FCBF previos'),
                               (6, 'Random Forest', 'No cambiaron los resultados de Random Forest'),
                               (7, 'Informes históricos', 'No se sobrescribieron informes históricos'),
                               (8, 'Figuras históricas', 'No se sobrescribieron figuras históricas'),
                               ('8b', 'Entregables de la corrección controlada', 'Se conservaron los entregables de la corrección controlada')):
        n, cambios = grupo(nombre)
        conteos[nombre] = n
        anotar(num, texto, not cambios, f'{n} archivos revisados; {len(cambios)} con cambios')
    todos_nuevos = set(nuevo['agregados']) | set(nuevo['eliminados']) | set(nuevo['modificados'])
    anotar(9, 'Los cambios de código del cierre se limitan a H11 y H13', todos_nuevos == NUEVOS_AUTORIZADOS,
           'Cambiaron: ' + ', '.join(sorted(todos_nuevos)))
    fuera = sorted((set(previo['modificados']) | set(previo['eliminados'])) - PREVIOS_AUTORIZADOS)
    anotar('9b', 'Respecto de la línea base de la corrección, solo difieren los 8 scripts autorizados', not fuera,
           f'{len(previo["modificados"])} modificados; {len(previo["eliminados"])} eliminados; {len(fuera)} fuera de lo autorizado; línea base de {len(base)} archivos')
    n_figuras = sum(r.startswith('analisis/figuras/') for r in d.index)
    n_figuras_a = sum(r.startswith('analisis/figuras/') for r in a.index)
    anotar(10, 'No se ejecutaron procesos destructivos', not nuevo['eliminados'] and n_figuras == n_figuras_a,
           f'0 archivos eliminados esperados, {len(nuevo["eliminados"])} detectados; figuras: {n_figuras_a} antes y {n_figuras} después')
    posteriores = [r for r in nuevo['agregados'] if any(p in r.lower() for p in ('fase36', 'fase_36', 'fase37', 'pca', 'famd', 'kmeans', 'clust'))]
    anotar(11, 'No se inició ninguna fase posterior', not posteriores, f'{len(posteriores)} archivos nuevos de fases posteriores')
    head = git('rev-parse', 'HEAD')
    remoto = git('rev-parse', '--verify', '--quiet', 'origin/datos-simulados')
    indice = git('diff', '--cached', '--name-only')
    anotar(12, 'No se realizó commit ni push', head == HEAD_ESPERADO and not indice,
           f'HEAD {head[:7]}; área de preparación vacía: {not indice}; rama remota: {remoto[:7] if remoto else "no existe"}')
    versionados = {x.split(maxsplit=1)[1] for x in git('status', '--short', '--untracked-files=no').splitlines()}
    anotar('12b', 'Los archivos versionados modificados siguen siendo los 8 autorizados', versionados == PREVIOS_AUTORIZADOS,
           f'{len(versionados)} archivos modificados frente a HEAD')

    with (TABLAS / 'verificacion_integridad_posterior.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    with (TABLAS / 'cambios_detectados.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['comparacion', 'tipo', 'ruta'])
        for nombre, comp in (('antes y después del cierre', nuevo), ('línea base de la corrección y después del cierre', previo)):
            for tipo, lista in comp.items():
                w.writerows([nombre, tipo, r] for r in lista)
    resumen = {'n_antes': len(a), 'n_despues': len(d), 'n_base': len(base), 'nuevo': nuevo,
               'previo_modificados': previo['modificados'], 'previo_eliminados': previo['eliminados'], 'n_previo_agregados': len(previo['agregados']),
               'conteos': conteos, 'filas': filas, 'cumple': all(x['resultado'] == 'OK' for x in filas),
               'protegidos_sin_cambio': len(a.index.intersection(d.index)) - len(nuevo['modificados']),
               'base_sin_cambio': int((base.reindex(d.index.intersection(base.index)) == d.reindex(d.index.intersection(base.index))).sum())}
    (TABLAS / 'integridad.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in filas:
        print(x['punto'], x['resultado'], '|', x['comprobacion'], '|', x['detalle'])
    print('sin cambio frente a antes:', resumen['protegidos_sin_cambio'], '| sin cambio frente a línea base:', resumen['base_sin_cambio'])


if __name__ == '__main__':
    main()
