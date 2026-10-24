"""
Fase 34A: genera el conjunto de datos sintético de la usuaria común.

Uso:
    python analisis/generar_sintetico.py
    python analisis/generar_sintetico.py --n 550 --semilla 2026 --salida datos/sintetico

Pedido de la profesora (reunión 20-10): solo usuaria común y primera encuesta,
coherente con Chile, con los efectos sobre el MRS que ella validó, y SUCIO para
limpiarlo en el EDA. Los campos del servicio de salud quedan vacíos.

Salida (mismas 128 columnas que dataset_menopausia_sucio.csv):
    dataset_usuaria_sucio.csv   el conjunto que se entrega a la limpieza (Fase 34B)
    dataset_usuaria_verdad.csv  las mismas encuestas sin errores ni omisiones
    bitacora_suciedad.csv       cada celda o fila ensuciada, con su valor verdadero
y el informe de validación analisis/informe_sintetico.md.

Las reglas están en analisis/supuestos_simulacion.md (§13 y §14) y los números en
analisis/simulacion/parametros.py. Con la misma semilla se obtienen exactamente
los mismos archivos.
"""
import argparse
import csv
import hashlib
import hmac
import random
import uuid
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from simulacion import parametros as P
from simulacion.ensuciar import META, MRS_ITEMS, ensuciar
from simulacion.generador import CAMPOS, generar

RAIZ = Path(__file__).resolve().parent.parent
# Clave ficticia: el rut_hash imita al de la plataforma, pero no se puede cruzar con ella.
PEPPER_SINTETICO = b'conjunto-sintetico-34A'

# Mismo orden de columnas que el conjunto de la profesora.
COLUMNAS = (
    ['participante_id', 'uuid_local', 'rut_hash', 'usuario_id', 'ronda', 'sincronizado_en',
     'creado_en', 'ronda_actual', 'ultima_finalizacion_en', 'fecha_evaluacion']
    + CAMPOS['identificacion'][:5] + ['comuna', 'region_residencia', 'trabaja_actualmente',
                                      'excepcion_edad']
    + CAMPOS['mrs']
    + ['fecha_registro', 'fecha_ultimo_empa', 'origen_registro']
    + [c for c in CAMPOS['empa'] if c not in ('origen_registro', 'fecha_ultimo_empa')]
    + CAMPOS['conocimiento_sistema'] + CAMPOS['trabajo'] + CAMPOS['tareas_cuidado']
    + CAMPOS['actividad_fisica'] + CAMPOS['habitos_de_vida'] + CAMPOS['satisfaccion']
)


def texto(valor):
    if valor is None:
        return ''
    if isinstance(valor, float):
        return f'{valor:.1f}'
    return str(valor)


def hora_azar(rng, dia, desde=8, hasta=22):
    return datetime(dia.year, dia.month, dia.day, rng.randint(desde, hasta - 1), rng.randint(0, 59))


def filas_verdad(rng, personas, encuestas):
    """Una fila por encuesta, en el orden en que se sincronizaron, todo como texto."""
    por_id = {p['id']: p for p in personas}
    encuestas = sorted(encuestas, key=lambda e: e['fecha'])
    filas = []
    for k, e in enumerate(encuestas, start=1):
        p = por_id[e['participante']]
        sincronizado = hora_azar(rng, e['fecha'])
        creado = hora_azar(rng, e['fecha'] - timedelta(days=rng.randint(0, 7)), 0, 24)
        if creado > sincronizado:
            creado = sincronizado - timedelta(minutes=rng.randint(15, 90))
        rut = p['rut'].replace('.', '').replace('-', '').upper()
        fila = {
            'participante_id': k,
            'uuid_local': uuid.UUID(int=rng.getrandbits(128), version=4),
            'rut_hash': hmac.new(PEPPER_SINTETICO, rut.encode(), hashlib.sha256).hexdigest(),
            'usuario_id': 1000 + k,
            'ronda': 1,
            'sincronizado_en': sincronizado.strftime('%Y-%m-%d %H:%M:%S'),
            'creado_en': creado.strftime('%Y-%m-%d %H:%M:%S'),
            'ronda_actual': 2,                     # ya finalizó la primera encuesta
            'ultima_finalizacion_en': sincronizado.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_evaluacion': e['fecha'].isoformat(),
            'fecha_registro': e['fecha'].isoformat(),
        }
        for seccion in e['secciones'].values():
            fila.update(seccion or {})
        filas.append({c: texto(fila.get(c)) for c in COLUMNAS})
    return filas


def columnas_numericas(filas):
    """Columnas de respuesta cuyos valores verdaderos son todos números."""
    numericas = []
    for c in COLUMNAS:
        if c in META or c in MRS_ITEMS:
            continue
        valores = [f[c] for f in filas if f[c] != '']
        if valores and all(v.replace('.', '', 1).isdigit() for v in valores):
            numericas.append(c)
    return numericas


def escribir_csv(ruta, columnas, filas):
    # utf-8-sig: Excel abre bien los acentos.
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)


# --- Validación ------------------------------------------------------------------------------
# Factores validados por la profesora: (columna o derivada, sentido esperado, rango |rho|).
FACTORES = [
    ('IMC', 'imc', +1, (0.25, 0.35)),
    ('Diabetes (medicamentos)', 'diabetes', +1, (0.10, 0.25)),
    ('Doble carga (trabaja y cuida)', 'doble_carga', +1, (0.10, 0.25)),
    ('Sobrecarga (quien cuida)', 'sobrecarga_fisica_emocional', +1, (0.10, 0.25)),
    ('Estrés laboral (quien trabaja)', 'estres_entorno_laboral', +1, (0.10, 0.25)),
    ('Lugar de trabajo comprensivo', 'lugar_trabajo_comprensivo', -1, (0.10, 0.25)),
    ('Días de ejercicio', 'dias_ejercicio_semana', -1, (0.10, 0.25)),
    ('Vasos de agua', 'vasos_agua_dia', -1, (0.10, 0.25)),
    ('Tabaco', 'tabaco_frecuencia', +1, (0.10, 0.25)),
    ('Alcohol', 'alcohol_frecuencia', +1, (0.10, 0.25)),
    ('Marihuana', 'marihuana_frecuencia', +1, (0.0, 0.25)),
]
# Alimentación: efecto chico positivo o nulo; nunca protector.
ALIMENTOS = ['panes_dia', 'golosinas_semana', 'jugos_gaseosas_dia', 'bebidas_energeticas_dia',
             'platos_verduras_dia', 'frutas_dia', 'lacteos_dia', 'pescado_semana', 'legumbres_semana',
             'carnes_semana']


def tabla_analisis(filas):
    df = pd.DataFrame(filas).replace('', None)
    num = lambda c: pd.to_numeric(df[c], errors='coerce')
    out = pd.DataFrame({'mrs': sum(num(c) for c in MRS_ITEMS)})
    out['imc'] = num('peso_kg') / (num('talla_actual_cm') / 100) ** 2
    out['diabetes'] = (df['usa_medicamentos_diabetes'] == 'SI').astype(int)
    out['doble_carga'] = ((df['trabaja_actualmente'] == 'True')
                          & (df['cuida_otras_personas'] == 'SI')).astype(int)
    for c in [f[1] for f in FACTORES[3:]] + ALIMENTOS:
        out[c] = num(c)
    return out


def validar(verdad, sucio, bitacora, salida_md):
    df = tabla_analisis(verdad)
    lineas = []
    mrs = df['mrs']
    sev = pd.cut(mrs, [-1, 4, 8, 15, 44], labels=['0-4', '5-8', '9-15', '16-44'])
    lineas += [
        '# Validación del conjunto sintético (Fase 34A)', '',
        f'Generado por `analisis/generar_sintetico.py` el {datetime.now():%Y-%m-%d}. Compara el '
        'conjunto **verdadero** (sin errores) con lo pedido por la profesora el 20-10. Las '
        'correlaciones son de Spearman con el puntaje MRS total.', '',
        '## 1. Tamaño y MRS', '',
        f'- Participantes: **{len(verdad)}** (solo usuaria común, solo primera encuesta).',
        f'- Filas del conjunto sucio: **{len(sucio)}** (incluye duplicados y versiones antiguas).',
        f'- MRS total: **{mrs.mean():.1f} ± {mrs.std():.1f}** (objetivo chileno {P.OBJETIVO_MRS["total"]}).',
        '', '| Severidad | n | % |', '|---|---|---|',
    ]
    for k, v in sev.value_counts().sort_index().items():
        lineas.append(f'| {k} | {v} | {100 * v / len(mrs):.1f} |')

    lineas += ['', '## 2. Factores validados por la profesora', '',
               '| Factor | n | rho | Sentido esperado | Rango pedido | Cumple |', '|---|---|---|---|---|---|']
    fallas = 0
    for nombre, col, signo, (lo, hi) in FACTORES:
        par = df[['mrs', col]].dropna()
        rho, pval = spearmanr(par[col], par['mrs'])
        ok = rho * signo > 0 and lo <= abs(rho) <= hi + 0.03
        fallas += not ok
        lineas.append(f'| {nombre} | {len(par)} | {rho:+.2f} | {"+" if signo > 0 else "−"} | '
                      f'{lo:.2f}-{hi:.2f} | {"sí" if ok else "**no**"} |')
    lineas += ['', 'Marihuana: el 94 % nunca consume, así que su rho queda bajo aunque el efecto '
               'por consumidora es el mayor; solo se exige que sea positivo.', '',
               '## 3. Alimentación: ninguna protectora', '',
               '| Variable | rho | p | Protectora significativa |', '|---|---|---|---|']
    for col in ALIMENTOS:
        par = df[['mrs', col]].dropna()
        rho, pval = spearmanr(par[col], par['mrs'])
        protectora = rho < 0 and pval < 0.05
        fallas += protectora
        lineas.append(f'| {col} | {rho:+.2f} | {pval:.3f} | {"**sí**" if protectora else "no"} |')

    lineas += ['', '## 4. Suciedad agregada', '', '| Tipo de error | Celdas o filas |', '|---|---|']
    for tipo, n in Counter(b['tipo'] for b in bitacora).most_common():
        lineas.append(f'| {tipo} | {n} |')
    imc_faltante = 100 * sum(1 for f in sucio if f['peso_kg'] == '' or f['talla_actual_cm'] == '') / len(sucio)
    lineas += ['', f'IMC no calculable en el conjunto sucio (sin peso o sin talla): **{imc_faltante:.0f} %**.',
               '', f'**Resultado:** {"todos los controles se cumplen" if not fallas else f"{fallas} controles no se cumplen"}.']
    salida_md.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    return fallas, '\n'.join(lineas)


def main():
    parser = argparse.ArgumentParser(description='Genera el conjunto sintético de la usuaria (Fase 34A).')
    parser.add_argument('--n', type=int, default=P.N_PARTICIPANTES)
    parser.add_argument('--semilla', type=int, default=P.SEMILLA)
    parser.add_argument('--salida', type=Path, default=RAIZ / 'datos' / 'sintetico')
    args = parser.parse_args()

    rng = random.Random(args.semilla)
    personas, encuestas = generar(rng, args.n, 0, blancos=False)
    verdad = filas_verdad(rng, personas, encuestas)
    sucio, bitacora = ensuciar(random.Random(args.semilla + 1), verdad, columnas_numericas(verdad))

    args.salida.mkdir(parents=True, exist_ok=True)
    escribir_csv(args.salida / 'dataset_usuaria_verdad.csv', COLUMNAS, verdad)
    escribir_csv(args.salida / 'dataset_usuaria_sucio.csv', COLUMNAS, sucio)
    escribir_csv(args.salida / 'bitacora_suciedad.csv',
                 ['participante_id', 'uuid_local', 'columna', 'valor_verdadero', 'valor_sucio', 'tipo'],
                 bitacora)
    fallas, informe = validar(verdad, sucio, bitacora, RAIZ / 'analisis' / 'informe_sintetico.md')
    print(f'{len(verdad)} participantes, {len(sucio)} filas sucias, {len(bitacora)} cambios → {args.salida}')
    print(informe)
    raise SystemExit(1 if fallas else 0)


if __name__ == '__main__':
    main()
