"""
Fase 36A: comprobaciones del diseño. Revisa la cobertura de las tablas y que ningún archivo histórico haya cambiado.

No construye matrices ni ejecuta las pruebas de la Fase 36B.
Uso, desde analisis/: python fase36_diseno/scripts/verificar_diseno.py
Escribe solo fase36_diseno/apoyo/verificacion_diseno.csv.
"""
import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd

ANALISIS = Path(__file__).resolve().parents[2]
RAIZ = ANALISIS.parent
DISENO = ANALISIS / 'fase36_diseno'
sys.path.insert(0, str(ANALISIS / 'revision_correctiva_fase34'))

from manifiesto import huella  # noqa: E402

MANIFIESTO = ANALISIS / 'cierre_fases_34_35' / 'integridad' / 'manifiesto_despues.csv'
RELEVANCIA = ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables' / 'permutaciones_50000' / 'relevancia_33.csv'
EXCLUIDAS = ['usa_medicamentos_diabetes', 'doble_carga', 'prevision', 'etapa_menopausica', 'cuida_otras_personas', 'severo_mrs', 'mrs_total', 'severidad_mrs_4', 'participante_id', 'imc_fue_imputado']
ENTREGABLES = ['protocolo_metodologico_fase36.docx', 'diccionario_codificacion_fase36.csv', 'matriz_decisiones_variables.csv', 'estrategia_escalado.md',
               'estrategia_imputaciones_y_sensibilidades.md', 'estrategia_pca_famd.md', 'plan_pruebas_fase36.md', 'resumen_decisiones_pendientes.md']
FILAS = []


def anotar(que, ok, detalle=''):
    FILAS.append({'comprobacion': que, 'resultado': 'OK' if ok else 'NO CUMPLE', 'detalle': detalle})


def main():
    r = pd.read_csv(RELEVANCIA, encoding='utf-8-sig')
    m = pd.read_csv(DISENO / 'matriz_decisiones_variables.csv', encoding='utf-8-sig')
    d = pd.read_csv(DISENO / 'diccionario_codificacion_fase36.csv', encoding='utf-8-sig', dtype=str)
    anotar('La matriz cubre exactamente las 33 variables', set(m['variable']) == set(r['variable']) and len(m) == 33, f'{len(m)} filas')
    anotar('Reparto 30 + 2 + 1', m['capa'].value_counts().to_dict() == {'general': 30, 'laboral': 2, 'cuidadoras': 1}, str(m['capa'].value_counts().to_dict()))
    anotar('El diccionario cubre las 33 variables', set(d['variable']) == set(r['variable']), f'{len(d)} filas')
    anotar('Sin variables excluidas', not (set(EXCLUIDAS) & set(m['variable'])), '')
    anotar('Roles de FAMD en la capa general', m[m['capa'] == 'general']['rol_famd'].value_counts().to_dict() == {'cuantitativa': 19, 'categórica': 11}, '19 cuantitativas; 11 categóricas')
    anotar('Módulos fuera de la matriz general', (m[m['capa'] != 'general']['rol_famd'] == 'no participa').all(), '')
    columnas = ['nombre_legible', 'seccion_encuesta', 'tipo_original', 'valores_admitidos', 'orden_natural', 'cero_valido', 'codigo_no_aplica', 'imputadas', 'transformacion_previa', 'propuesta_pca', 'propuesta_famd', 'justificacion']
    anotar('Campos completos en la matriz', not m[columnas].isna().any().any(), f'{len(columnas)} campos')
    faltan = [e for e in ENTREGABLES if not (DISENO / e).exists()]
    anotar('Ocho entregables presentes', not faltan, ', '.join(faltan))

    base = pd.read_csv(MANIFIESTO, encoding='utf-8').set_index('ruta')['sha256']
    # Solo se revisa lo registrado al cerrar; analisis/fase36_diseno no figura en ese manifiesto.
    distintos = [ruta for ruta, h in base.items() if not (RAIZ / ruta).exists() or huella(RAIZ / ruta) != h]
    anotar('Archivos históricos sin cambios frente al manifiesto de cierre', not distintos, f'{len(base)} revisados; {len(distintos)} distintos: {distintos[:5]}')

    def git(*a):
        return subprocess.run(['git', *a], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout.strip()
    anotar('Sin commit ni archivos preparados', git('rev-parse', '--short', 'HEAD') == '745d689' and not git('diff', '--cached', '--name-only'), f"HEAD {git('rev-parse', '--short', 'HEAD')}")
    nuevos = [p for p in (ANALISIS / 'fase36').rglob('*')] if (ANALISIS / 'fase36').exists() else []
    anotar('No existe carpeta de implementación de la Fase 36B', not nuevos, '')

    with (DISENO / 'apoyo' / 'verificacion_diseno.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(FILAS[0]))
        w.writeheader()
        w.writerows(FILAS)
    for x in FILAS:
        print(x['resultado'], '|', x['comprobacion'], '|', x['detalle'][:120])


if __name__ == '__main__':
    main()
