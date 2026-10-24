"""
Paso 2: genera las encuestas simuladas y las guarda como CSV.

Uso:
    python analisis/generar_simulacion.py
    python analisis/generar_simulacion.py --n 200 --n-ronda2 50 --semilla 2026 --salida datos/simulados

Las reglas están en analisis/supuestos_simulacion.md y los números en
analisis/simulacion/parametros.py. Con la misma semilla se obtienen
exactamente los mismos archivos.
"""
import argparse
import csv
import random
from pathlib import Path
from statistics import mean

from simulacion import parametros as P
from simulacion.generador import (
    CAMPOS, CONDICIONES, OBLIGATORIOS, SECCIONES_POR_RONDA, SOLO_PROFESIONAL, _cumple, edad_en,
    generar,
)

RAIZ = Path(__file__).resolve().parent.parent


def escribir_csv(ruta, columnas, filas):
    # utf-8-sig: Excel abre bien los acentos.
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction='raise')
        w.writeheader()
        for fila in filas:
            w.writerow({c: ('' if fila.get(c) is None else fila.get(c)) for c in columnas})


def guardar(personas, encuestas, salida):
    salida.mkdir(parents=True, exist_ok=True)
    por_id = {p['id']: p for p in personas}

    escribir_csv(salida / 'participantes.csv',
                 ['participante', 'rut', 'email', 'aplicada_por', 'fecha_ronda1', 'fecha_ronda2'],
                 [{'participante': p['id'], 'rut': p['rut'], 'email': p['email'],
                   'aplicada_por': p['aplicada_por'], 'fecha_ronda1': p['fecha_ronda1'],
                   'fecha_ronda2': p.get('fecha_ronda2')} for p in personas])

    meta = ['participante', 'ronda', 'fecha_encuesta']
    identificaciones = {}
    for e in encuestas:
        if e['ronda'] == 1:
            identificaciones[e['participante']] = e['secciones']['identificacion']
    escribir_csv(salida / 'identificacion.csv', ['participante'] + CAMPOS['identificacion'],
                 [{'participante': pid, **fila} for pid, fila in identificaciones.items()])

    for seccion in SECCIONES_POR_RONDA:
        filas = [{'participante': e['participante'], 'ronda': e['ronda'],
                  'fecha_encuesta': e['fecha'], **e['secciones'][seccion]}
                 for e in encuestas if e['secciones'][seccion] is not None]
        escribir_csv(salida / f'{seccion}.csv', meta + CAMPOS[seccion], filas)

    # Tabla plana: una fila por encuesta, todas las preguntas + puntajes MRS.
    puntajes = ['mrs_somatico', 'mrs_psicologico', 'mrs_urogenital', 'mrs_total']
    columnas = meta + ['aplicada_por'] + CAMPOS['identificacion']
    for seccion in SECCIONES_POR_RONDA:
        columnas += CAMPOS[seccion]
    columnas += puntajes
    plano = []
    for e in encuestas:
        fila = {'participante': e['participante'], 'ronda': e['ronda'],
                'fecha_encuesta': e['fecha'], 'aplicada_por': e['rol'],
                **identificaciones[e['participante']]}
        for seccion in SECCIONES_POR_RONDA:
            fila.update(e['secciones'][seccion] or {})
        fila.update({f'mrs_{k}': v for k, v in e['mrs'].items()})
        plano.append(fila)
    escribir_csv(salida / 'encuestas_plano.csv', columnas, plano)

    # Variables ocultas: no son respuestas, sirven para evaluar la caracterización.
    escribir_csv(salida / 'latentes.csv',
                 ['participante', 'ronda', 'edad', 'provincia', 'etapa', 'edad_menopausia',
                  'terapia_hormonal', 'hta', 'dm', 'imc', 'imc_categoria', 'activa', 'fuma',
                  'cumple_5_porciones', 'cuida', 'sobrecarga', 'estres_laboral',
                  'nivel_sintomas'] + puntajes,
                 [{'participante': e['participante'], 'ronda': e['ronda'],
                   'edad': edad_en(por_id[e['participante']]['nacimiento'], e['fecha']),
                   'provincia': por_id[e['participante']]['provincia'], 'etapa': e['etapa'],
                   **{k: por_id[e['participante']][k] for k in (
                       'edad_menopausia', 'terapia_hormonal', 'hta', 'dm', 'imc_categoria',
                       'activa', 'fuma', 'cumple_5_porciones', 'cuida', 'sobrecarga')},
                   'imc': round(por_id[e['participante']]['imc'], 1),
                   'estres_laboral': por_id[e['participante']]['estres'],
                   'nivel_sintomas': round(por_id[e['participante']]['g'], 3),
                   **{f'mrs_{k}': v for k, v in e['mrs'].items()}} for e in encuestas])


def pct(valores):
    valores = list(valores)
    return 100 * sum(valores) / len(valores) if valores else 0


def resumen(personas, encuestas):
    r1 = [e for e in encuestas if e['ronda'] == 1]
    r2 = [e for e in encuestas if e['ronda'] == 2]
    adultas = [p for p in personas if not p['excepcion']]
    filas = [
        ('Encuestas (ronda 1 + ronda 2)', f'{len(r1)} + {len(r2)}',
         f'{P.N_PARTICIPANTES} + {P.N_RONDA2}'),
        ('Días mínimos entre rondas', min(((p['fecha_ronda2'] - p['fecha_ronda1']).days
                                           for p in personas if 'fecha_ronda2' in p), default='-'),
         f'≥ {P.DIAS_ENTRE_RONDAS}'),
        ('% aplicadas por personal de salud', f'{pct(p["aplicada_por"] == "PROFESIONAL" for p in personas):.0f}', '30'),
        ('% excepción de edad (<40)', f'{pct(bool(p["excepcion"]) for p in personas):.1f}', '5'),
        ('Edad media (40-60)', f'{mean(p["edad"] for p in adultas):.1f}', '~49-50'),
        ('% Coquimbo + La Serena', f'{pct(p["comuna"] in ("Coquimbo", "La Serena") for p in personas):.0f}', '~62'),
        ('% trabaja', f'{pct(p["trabaja"] for p in personas):.0f}', '~58'),
        ('% Fonasa', f'{pct(p["prevision"] == "FONASA" for p in personas):.0f}', '~81'),
        ('% posmenopausia (natural + quirúrgica)',
         f'{pct(p["etapa"] in ("post", "quirurgica") for p in personas):.0f}', '~61'),
        ('% hipertensión', f'{pct(p["hta"] for p in personas):.0f}', '~30'),
        ('% diabetes', f'{pct(p["dm"] for p in personas):.0f}', '~13'),
        ('% obesidad (IMC ≥ 30)', f'{pct(p["imc"] >= 30 for p in personas):.0f}', '~41'),
        ('% fuma', f'{pct(p["fuma"] for p in personas):.0f}', '~27'),
        ('% ejercicio ≥ 3 días', f'{pct(p["activa"] for p in personas):.0f}', '~13'),
        ('% ≥ 5 porciones frutas/verduras', f'{pct(p["cumple_5_porciones"] for p in personas):.0f}', '~16'),
        ('% cuida a otras personas', f'{pct(p["cuida"] for p in personas):.0f}', '~50'),
    ]
    for dom in ('somatico', 'psicologico', 'urogenital', 'total'):
        valores = [e['mrs'][dom] for e in r1]
        de = (sum((v - mean(valores)) ** 2 for v in valores) / (len(valores) - 1)) ** 0.5
        objetivo = P.OBJETIVO_MRS[dom]
        filas.append((f'MRS {dom} (media ± DE, ronda 1)', f'{mean(valores):.1f} ± {de:.1f}', f'{objetivo}'))

    # Controles de estructura: blancos y condicionales.
    opcionales = blancos = violaciones = 0
    for e in encuestas:
        for seccion, fila in e['secciones'].items():
            if fila is None:
                continue
            for campo, valor in fila.items():
                if campo not in OBLIGATORIOS[e['rol']]:
                    opcionales += 1
                    blancos += valor is None
                if e['rol'] != 'PROFESIONAL' and campo in SOLO_PROFESIONAL:
                    violaciones += 1
                if campo in CONDICIONES:
                    madre, op, esperado = CONDICIONES[campo]
                    if not _cumple(fila.get(madre), op, esperado, e['fecha']):
                        violaciones += 1
    filas.append(('% blancos en preguntas opcionales', f'{100 * blancos / opcionales:.1f}', '~5'))
    filas.append(('Respuestas que la encuesta no mostraría', violaciones, '0'))

    ancho = max(len(f[0]) for f in filas)
    print(f'\n{"Indicador".ljust(ancho)}  {"Obtenido":>14}  {"Objetivo":>10}')
    print('-' * (ancho + 28))
    for nombre, obtenido, objetivo in filas:
        print(f'{nombre.ljust(ancho)}  {str(obtenido):>14}  {str(objetivo):>10}')


def main():
    parser = argparse.ArgumentParser(description='Genera las encuestas simuladas (Paso 2).')
    parser.add_argument('--n', type=int, default=P.N_PARTICIPANTES, help='participantes (ronda 1)')
    parser.add_argument('--n-ronda2', type=int, default=P.N_RONDA2, help='participantes con ronda 2')
    parser.add_argument('--semilla', type=int, default=P.SEMILLA)
    parser.add_argument('--salida', type=Path, default=RAIZ / 'datos' / 'simulados')
    args = parser.parse_args()

    P.N_PARTICIPANTES, P.N_RONDA2 = args.n, args.n_ronda2
    personas, encuestas = generar(random.Random(args.semilla), args.n, args.n_ronda2)
    guardar(personas, encuestas, args.salida)
    print(f'{len(encuestas)} encuestas de {len(personas)} participantes → {args.salida}')
    resumen(personas, encuestas)


if __name__ == '__main__':
    main()
