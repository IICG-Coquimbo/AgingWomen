"""
Fase 38R: sella el protocolo, las fuentes de decisiones y el código de análisis con SHA-256. Se niega si ya hay sello o si existen resultados de reglas.

Uso, desde la carpeta scripts: python -B sellar_protocolo_38r.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import barreras_38r as B  # noqa: E402

BASE = AQUI.parent
P = BASE / 'protocolo'
SELLO = P / 'sello_protocolo.json'
CODIGO = ['barreras_38r.py', 'nucleo_38r.py', 'etapa_a_preparacion.py', 'etapa_b_reglas.py', 'etapa_c_robustez.py']
if SELLO.exists():
    raise SystemExit('Ya existe un sello: no se reemplaza.')
for carpeta in ('reglas', 'referencia_nula', 'sensibilidades', 'estabilidad', 'comparacion', 'preparacion'):
    if (BASE / carpeta).exists() and any((BASE / carpeta).iterdir()):
        raise SystemExit(f'Ya hay resultados en {carpeta}: no se puede sellar antes de calcular.')
archivo = P / '01_protocolo_38R.md'
dec = B.decisiones()
s = {'archivo': archivo.name, 'sha256': B.sha(archivo), 'bytes': archivo.stat().st_size, 'sellado': datetime.now().isoformat(timespec='seconds'),
     'protocolo_historico_sha256': '9f9614115801805f9cde6c1586a8d7571ee44116c18ac7638025a645ee7f5a82', 'fuentes_decisiones': dec['huellas'], 'codigo': {c: B.sha(AQUI / c) for c in CODIGO}}
SELLO.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print(s)
