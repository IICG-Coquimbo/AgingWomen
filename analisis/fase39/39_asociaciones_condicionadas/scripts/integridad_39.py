"""
Fase 39: integridad de las fases anteriores (34 a 38), git y plataforma; huellas de las entradas.

Uso, desde la carpeta scripts: python integridad_39.py inicial|final
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import nucleo_39 as N
import pandas as pd

HEAD_ESPERADO = '745d689'
A = N.ANALISIS
MANIFIESTOS = [
    ('Fases 34-35 (cierre)', A / 'cierre_fases_34_35', 'integridad/manifiesto_despues.csv', N.RAIZ, 'ruta'),
    ('Fase 36', A / 'fase36', 'integridad/manifiesto_final_36B.csv', None, 'ruta'),
    ('Fase 37A', A / 'fase37' / '37A_reduccion', 'integridad/manifiesto_final_37A.csv', None, 'ruta'),
    ('Fase 37B', A / 'fase37' / '37B_clustering', 'integridad/manifiesto_final_37B.csv', None, 'ruta'),
    ('Fase 37C', A / 'fase37' / '37C_comparacion_seleccion', 'integridad/manifiesto_final_37C.csv', None, 'ruta'),
    ('Complemento 37C', A / 'fase37' / '37C_complemento_tres_preguntas', 'integridad/manifiesto_final.csv', None, 'ruta'),
    ('Fase 37D', A / 'fase37' / '37D_caracterizacion', 'integridad/manifiesto_final.csv', None, 'archivo'),
    ('Fase 38', N.D38, 'integridad/manifiesto_final.csv', None, 'archivo'),
]
ENTRADAS = [N.N37.LIMPIO, N.N37.F35, A / 'fase36' / 'procedencia' / 'procedencia_celdas.csv', A / 'fase36' / 'matrices' / 'identificadores.csv',
            A / 'fase36' / 'artefactos' / 'P2' / 'esquema_variables.json', N.N37.C37 / 'seleccion' / 'artefactos_provisionales' / 'P2_c12_km_k4' / 'etiquetas.csv',
            N.N37.CMP / 'asignaciones' / 'etiquetas_alternativas.csv', N.N37.CMP / 'definiciones' / 'definicion_B1_B2.json',
            A / 'fase37' / '37D_caracterizacion' / 'scripts' / 'nucleo_37d.py', N.D38 / 'scripts' / 'nucleo_38.py', N.D38 / 'scripts' / 'algoritmos_38.py',
            N.D38 / 'scripts' / 'evaluacion_38.py', N.D38 / 'preparacion' / 'matriz_transaccional_principal.csv', N.RAIZ / 'src' / 'apps' / 'encuestas' / 'models.py',
            N.N37.C37 / 'scripts' / 'md_a_word_37c.js']


def git(*a):
    return subprocess.run(['git', *a], cwd=N.RAIZ, capture_output=True, text=True).stdout


def manifiestos():
    filas = []
    for nombre, base, ruta, rel, col in MANIFIESTOS:
        m = pd.read_csv(Path(base) / ruta)
        malos, sin_verificar = [], []
        for r, h in zip(m[col], m['sha256']):
            p = Path(rel or base) / r
            if any(x in p.name.lower() for x in N.PROHIBIDOS):
                sin_verificar.append(r)
                continue
            if not p.exists() or N.sha(p) != h:
                malos.append(r)
        filas.append({'fase': nombre, 'manifiesto': (Path(base) / ruta).relative_to(N.RAIZ).as_posix(), 'archivos': len(m), 'comparados_por_huella': len(m) - len(sin_verificar),
                      'sin_verificar_por_nombre': len(sin_verificar), 'distintos': len(malos), 'ejemplos': '; '.join(malos[:3] + sin_verificar[:4])})
    return pd.DataFrame(filas)


def pycache():
    return [str(p.relative_to(N.RAIZ)) for _, base, _, _, _ in MANIFIESTOS for p in Path(base).rglob('__pycache__')]


def estado_git():
    fuera = [l for l in git('status', '--porcelain', '--untracked-files=all', '--', '.', ':!analisis').splitlines() if l.strip()]
    plataforma = [l for l in git('status', '--porcelain', '--untracked-files=all', '--', 'src').splitlines() if l.strip()]
    return {'head': git('rev-parse', '--short', 'HEAD').strip(), 'rama': git('rev-parse', '--abbrev-ref', 'HEAD').strip(), 'cambios_fuera_de_analisis': fuera, 'cambios_en_src': plataforma,
            'datos_versionados_modificados': [l for l in git('status', '--porcelain', '--', 'datos').splitlines() if l.strip()]}


def main(momento):
    N.instalar_gancho()
    sello = N.huella_sello()
    m = manifiestos()
    g = estado_git()
    ent = pd.DataFrame([{'archivo': p.relative_to(N.RAIZ).as_posix(), 'sha256': N.sha(p), 'bytes': p.stat().st_size} for p in ENTRADAS])
    D = N.BASE / 'integridad'
    N.a_csv(m, D / f'manifiestos_{momento}.csv')
    N.a_csv(ent, D / f'huellas_entradas_{momento}.csv')
    res = {'momento': momento, 'fecha': datetime.now().isoformat(timespec='seconds'), 'protocolo_sha256': sello['sha256'], 'protocolo_sellado': sello['sellado'],
           'archivos_protegidos': int(m['archivos'].sum()), 'comparados_por_huella': int(m['comparados_por_huella'].sum()), 'archivos_distintos': int(m['distintos'].sum()),
           'pycache_en_fases_protegidas': pycache(), **g}
    if momento == 'final':
        ini = pd.read_csv(D / 'huellas_entradas_inicial.csv')
        res['entradas_iguales_al_inicio'] = ini['sha256'].tolist() == ent['sha256'].tolist()
    N.a_json(res, D / f'integridad_{momento}.json')
    N.registrar(f'integridad {momento}')
    ok = res['archivos_distintos'] == 0 and not res['pycache_en_fases_protegidas'] and res['head'] == HEAD_ESPERADO and not res['cambios_en_src'] and not res['datos_versionados_modificados']
    print(m.drop(columns=['manifiesto']).to_string(index=False))
    print({k: v for k, v in res.items() if k != 'cambios_fuera_de_analisis'}, 'cambios fuera de analisis:', len(g['cambios_fuera_de_analisis']))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'inicial')
