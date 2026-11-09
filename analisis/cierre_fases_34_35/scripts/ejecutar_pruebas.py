"""
Cierre de las Fases 34 y 35: ejecuta solo pruebas localizadas y registra también las que no se ejecutan.
Uso, desde analisis/: python cierre_fases_34_35/scripts/ejecutar_pruebas.py
Escribe cierre_fases_34_35/tablas/registro_pruebas.csv y pruebas.json.
"""
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ANALISIS = Path(__file__).resolve().parents[2]
TABLAS = ANALISIS / 'cierre_fases_34_35' / 'tablas'
S = 'cierre_fases_34_35/scripts'

UNITARIAS = [
    ('H11 y H13: recuento en la población analítica y ausencia de cambios estadísticos', f'{S}/test_h11_h13.py'),
    ('Corrección controlada: rótulos y figuras revisadas, en carpeta temporal', 'revision_correctiva_fase34/test_correccion_fase34.py'),
    ('Entropía, SU y FCBF: funciones con datos de prueba', 'preprocesamiento/test_entropia.py'),
    ('Revisión de 33 variables: lista, poblaciones y resultados guardados', 'preprocesamiento/test_revision_33_variables.py'),
    ('Documentales: 33 variables, 35A revisada y estructura de los Word', f'{S}/test_documental_cierre.py'),
]
VERIFICADORES = [
    ('Cifras de la Fase 35 contra los archivos', f'{S}/verificar_fase35.py', r'(\d+) de (\d+) comprobaciones OK'),
]
NO_EJECUTADAS = [
    ('eda_univariado.py completo', 'Borra figuras históricas al iniciarse. Se probó describir() en memoria.'),
    ('eda_usuaria.py completo', 'Regenera informes y figuras históricos. Se probaron en memoria las familias FDR y el rótulo.'),
    ('Análisis multivariado completo (34E)', 'Prohibido en este cierre.'),
    ('Generación sintética y limpieza completa', 'Prohibidas en este cierre.'),
    ('preprocesar_fase35.py', 'Regeneraría conjuntos e informes de la Fase 35.'),
    ('seleccionar_fase35b.py, revision_33_variables.py y análisis complementarios', 'Repetirían Shannon, permutaciones y FCBF.'),
    ('rf_33_variables.py y random_forest_fase35b.py', 'Reentrenarían Random Forest.'),
    ('random_forest_revision_35b_33_variables/test_rf_33_variables.py y preprocesamiento/test_random_forest_35b.py', 'Pueden entrenar modelos de control; quedan fuera por precaución.'),
    ('test_complementario_35b, test_complementario_cuidados, test_revision_35b, test_revision_35b_50000', 'Corresponden a etapas previas ya cerradas y este cierre no cambió su código; no se revisó si son seguros de ejecutar.'),
    ('test_informe_integrado_35b, test_informe_word_33, test_informe_word_rf_33', 'Corresponden a generadores de informes históricos que no cambiaron.'),
    ('Ejecución real del rótulo H13 y del recuento H11 en el flujo completo', 'Queda sin probar de extremo a extremo; requiere copia aislada del repositorio y autorización.'),
    ('Suite de Django de la plataforma', 'No se relaciona con estos cambios.'),
]


def main():
    TABLAS.mkdir(parents=True, exist_ok=True)
    entorno = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    filas = []
    for descripcion, ruta in UNITARIAS:
        p = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', ruta], cwd=ANALISIS, env=entorno,
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        salida = p.stderr + p.stdout
        m = re.search(r'Ran (\d+) tests?', salida)
        n = int(m.group(1)) if m else 0
        falla = re.search(r'FAILED \((.*)\)', salida)
        estado = 'Correcta' if p.returncode == 0 and n else 'Falló'
        filas.append({'tipo': 'Prueba unitaria', 'prueba': descripcion, 'ruta': ruta, 'estado': estado, 'casos': n,
                      'detalle': falla.group(1) if falla else ('Sin fallos' if n else salida[-300:])})
    for descripcion, ruta, patron in VERIFICADORES:
        p = subprocess.run([sys.executable, '-W', 'ignore', ruta], cwd=ANALISIS, env=entorno, capture_output=True, text=True, encoding='utf-8', errors='replace')
        m = re.search(patron, p.stdout)
        correcto = p.returncode == 0 and m and m.group(1) == m.group(2)
        filas.append({'tipo': 'Verificación', 'prueba': descripcion, 'ruta': ruta, 'estado': 'Correcta' if correcto else 'Falló',
                      'casos': int(m.group(2)) if m else 0, 'detalle': m.group(0) if m else p.stderr[-300:]})
    integridad = json.loads((TABLAS / 'integridad.json').read_text(encoding='utf-8')) if (TABLAS / 'integridad.json').exists() else None
    if integridad:
        filas.append({'tipo': 'Verificación', 'prueba': 'Integridad de archivos protegidos, comparando manifiestos', 'ruta': f'{S}/verificar_integridad_cierre.py',
                      'estado': 'Correcta' if integridad['cumple'] else 'Falló', 'casos': len(integridad['filas']),
                      'detalle': f"{sum(x['resultado'] == 'OK' for x in integridad['filas'])} de {len(integridad['filas'])} comprobaciones OK"})
    filas += [{'tipo': 'No ejecutada', 'prueba': a, 'ruta': '', 'estado': 'No ejecutada', 'casos': 0, 'detalle': b} for a, b in NO_EJECUTADAS]
    with (TABLAS / 'registro_pruebas.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    (TABLAS / 'pruebas.json').write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in filas:
        if x['tipo'] != 'No ejecutada':
            print(x['estado'], x['casos'], '|', x['prueba'], '|', x['detalle'][:200])


if __name__ == '__main__':
    main()
