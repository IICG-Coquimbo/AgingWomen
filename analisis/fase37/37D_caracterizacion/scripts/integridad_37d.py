"""
Fase 37D: integridad de las fases anteriores. Compara cada archivo protegido con su manifiesto, revisa git y la plataforma, y guarda la huella de las entradas.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/integridad_37d.py inicial|final
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import nucleo_37d as N
import pandas as pd

HEAD_ESPERADO = '745d689'
MANIFIESTOS = [
    ('Fases 34-35 (cierre)', N.ANALISIS / 'cierre_fases_34_35', 'integridad/manifiesto_despues.csv', N.RAIZ),
    ('Fase 36', N.F36, 'integridad/manifiesto_final_36B.csv', None),
    ('Fase 37A', N.A37, 'integridad/manifiesto_final_37A.csv', None),
    ('Fase 37B', N.B37, 'integridad/manifiesto_final_37B.csv', None),
    ('Fase 37C', N.C37, 'integridad/manifiesto_final_37C.csv', None),
    ('Complemento 37C', N.CMP, 'integridad/manifiesto_final.csv', None),
]
ENTRADAS = [N.LIMPIO, N.F35, N.F36 / 'procedencia' / 'procedencia_celdas.csv', N.F36 / 'matrices' / 'identificadores.csv', N.F36 / 'artefactos' / 'P2' / 'esquema_variables.json',
            N.C37 / 'seleccion' / 'artefactos_provisionales' / N.CONFIG / 'etiquetas.csv', N.CMP / 'asignaciones' / 'etiquetas_alternativas.csv', N.CMP / 'definiciones' / 'definicion_B1_B2.json',
            N.B37 / 'etiquetas' / 'etiquetas_principales.csv', N.B37 / 'sensibilidades' / 'etiquetas' / 'S-SOLAPE_P2.csv', N.B37 / 'sensibilidades' / 'etiquetas' / 'S-ORD_P2.csv']


def git(*a):
    return subprocess.run(['git', *a], cwd=N.RAIZ, capture_output=True, text=True).stdout


def manifiestos(leer=pd.read_csv, sha=N.sha):
    """Los archivos con nombre del simulador no se abren en este proceso: se verifican con git (versionados y sin cambios) y se cuentan aparte."""
    filas = []
    for nombre, base, ruta, rel in MANIFIESTOS:
        m = leer(Path(base) / ruta)
        malos, por_git, sin_verificar = [], 0, []
        for r, h in zip(m['ruta'], m['sha256']):
            p = Path(rel or base) / r
            if any(x in p.name.lower() for x in N.PROHIBIDOS):
                rel_raiz = p.resolve().relative_to(N.RAIZ.resolve()).as_posix()
                versionado = bool(git('ls-files', '--', rel_raiz).strip())
                if versionado and not git('status', '--porcelain', '--', rel_raiz).strip():
                    por_git += 1
                else:
                    sin_verificar.append(r)
                continue
            if not p.exists() or sha(p) != h:
                malos.append(r)
        filas.append({'fase': nombre, 'manifiesto': (Path(base) / ruta).relative_to(N.RAIZ).as_posix(), 'archivos': len(m), 'comparados_por_huella': len(m) - por_git - len(sin_verificar),
                      'verificados_con_git': por_git, 'sin_verificar_por_nombre': len(sin_verificar), 'distintos': len(malos), 'ejemplos': '; '.join(malos[:3] + sin_verificar[:3])})
    return pd.DataFrame(filas)


def pycache():
    return [str(p.relative_to(N.RAIZ)) for _, base, _, _ in MANIFIESTOS for p in Path(base).rglob('__pycache__')]


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
    D = N.INTEGRIDAD = BASE = N.BASE / 'integridad'
    N.a_csv(m, D / f'manifiestos_{momento}.csv')
    N.a_csv(ent, D / f'huellas_entradas_{momento}.csv')
    res = {'momento': momento, 'fecha': datetime.now().isoformat(timespec='seconds'), 'protocolo_sha256': sello['sha256'], 'protocolo_sellado': sello['sellado'],
           'archivos_protegidos': int(m['archivos'].sum()), 'archivos_distintos': int(m['distintos'].sum()), 'pycache_en_fases_protegidas': pycache(), **g}
    if momento == 'final':
        ini = pd.read_csv(D / 'huellas_entradas_inicial.csv')
        res['entradas_iguales_al_inicio'] = bool((ini['sha256'].tolist() == ent['sha256'].tolist()))
    N.a_json(res, D / f'integridad_{momento}.json')
    N.registrar(f'integridad {momento}')
    ok = res['archivos_distintos'] == 0 and not res['pycache_en_fases_protegidas'] and res['head'] == HEAD_ESPERADO and not res['cambios_en_src'] and not res['datos_versionados_modificados']
    print(m.to_string(index=False))
    print({k: v for k, v in res.items() if k not in ('cambios_fuera_de_analisis',)}, 'cambios fuera de analisis:', len(g['cambios_fuera_de_analisis']))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'inicial')
