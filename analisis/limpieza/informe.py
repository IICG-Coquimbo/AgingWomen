"""Informe de limpieza en Markdown (analisis/informe_limpieza.md)."""
from datetime import date

import pandas as pd

from . import reglas as R


def _tabla(encabezado, filas):
    lineas = ['| ' + ' | '.join(encabezado) + ' |', '|' + '---|' * len(encabezado)]
    lineas += ['| ' + ' | '.join(str(x) for x in fila) + ' |' for fila in filas]
    return '\n'.join(lineas)


def _pct(n, total):
    return f'{100 * n / total:.1f} %' if total else '-'


def generar(limpio, excluidas, diccionario, bit, entrada, salida):
    n = len(limpio)
    out = [
        '# Informe de limpieza del dataset (Fase 32)',
        '',
        f'Generado por `analisis/limpiar_dataset.py` el {date.today().isoformat()}. '
        'Volver a ejecutar el script regenera este informe y los archivos de salida.',
        '',
        f'- Entrada: `{entrada}` — {bit.filas_entrada} filas.',
        f'- Salida: `{salida}/dataset_menopausia_limpio.csv` — **{n} filas**.',
        f'- Excluidas: {len(excluidas)} filas (`{salida}/excluidas.csv`, con el motivo).',
        f'- Diccionario: `{salida}/diccionario_variables.csv` (faltantes y tratamiento por variable).',
        '',
        'Los códigos válidos, la lógica condicional y los campos solo para personal de salud se',
        'leen del código de la plataforma (`models.py`, `condicionales.py`, `campos_por_rol.py`),',
        'así la limpieza nunca contradice lo que la encuesta acepta.',
        '',
        '## 1. Filas excluidas',
        '',
        _tabla(['Motivo', 'Filas'],
               excluidas['motivo_exclusion'].value_counts().items()),
        '',
        '## 2. Correcciones por paso',
        '',
        'Una fila por (paso, variable, motivo). "Ejemplos" muestra valores originales.',
        '',
    ]
    filas = []
    for (paso, col, motivo), cant in sorted(bit.conteo.items(), key=lambda x: (int(x[0][0].split()[0]), x[0][1])):
        if paso.startswith(('2', '7')):
            continue                      # ya están en la tabla de exclusiones
        ej = ', '.join(sorted(bit.ejemplos.get((paso, col, motivo), [])))
        filas.append((paso, f'`{col}`', motivo, cant, ej[:80]))
    out.append(_tabla(['Paso', 'Variable', 'Motivo', 'Celdas', 'Ejemplos'], filas))
    if bit.notas:
        out += ['', '**Notas:**', ''] + [f'- {x}' for x in bit.notas]

    # --- Faltantes y tratamiento ---
    d = diccionario
    con_falta = d[d['faltantes'] > 0].sort_values('pct_faltante', ascending=False)
    out += [
        '',
        '## 3. Datos faltantes y tratamiento',
        '',
        'Un vacío es **"no aplica"** cuando la encuesta no habría mostrado la pregunta (lógica',
        'condicional, sección Trabajo sin trabajo, campos solo para personal de salud en encuestas',
        'autoaplicadas, encuesta de satisfacción no respondida). Esos vacíos no se imputan. El %',
        'faltante se calcula solo sobre las filas donde la pregunta aplica.',
        '',
        f'Reglas: < {R.UMBRAL_IMPUTAR:g} % se imputa; {R.UMBRAL_IMPUTAR:g}-{R.UMBRAL_EXCLUIR:g} % se imputa y se',
        f'agrega la columna `<variable>_imputado` (1 = imputado); > {R.UMBRAL_EXCLUIR:g} % no se usa para modelar.',
        'Moda para categóricas, mediana para ordinales y continuas. El MRS nunca se imputa.',
        '',
        _tabla(['Variable', 'Ámbito', 'Aplica a', 'Faltan', '%', 'Tratamiento'],
               [(f'`{r.variable}`', r.ambito, r.filas_aplica, r.faltantes, r.pct_faltante, r.tratamiento)
                for r in con_falta.itertuples()]),
        '',
        f'Las {len(d) - len(con_falta)} variables restantes no tienen faltantes reales.',
        '',
        '**Ámbito "subgrupo profesional":** laboratorio, presión, tamizaje y talla máxima solo los',
        'registra el personal de salud (`campos_por_rol.SOLO_PROFESIONAL`). Aplican a las '
        f'{int((limpio["origen_registro"] != "AUTO").sum())} encuestas con origen MEDICO o API, y se',
        'analizan en ese subgrupo, no en el modelado general.',
    ]

    # --- Resultado ---
    sev = limpio['mrs_severidad'].value_counts()
    orden = [nombre for _, nombre in bit.severidad]
    mrs = limpio[limpio['mrs_completo'] == 1]
    out += [
        '',
        '## 4. Variables derivadas',
        '',
        '- `edad` y `tramo_edad` a la fecha de evaluación.',
        '- `mrs_somatico` (p1-p4), `mrs_psicologico` (p5-p8), `mrs_urogenital` (p9-p11), `mrs_total`',
        '  y `mrs_severidad` con los cortes de `MRS.SEVERIDAD_TOTAL` (pendientes de confirmar).',
        '- `meses_desde_fum` y `etapa_menopausica` (STRAW+10 simplificado: ovario = NO → quirúrgica;',
        '  ≥ 12 meses → posmenopausia; < 12 meses y regular → premenopausia; si no → perimenopausia).',
        '- `imc`, `imc_categoria` (OMS), `perdida_talla_cm`, `presion_elevada` (≥ 140/90),',
        '  `doble_carga` (trabaja y cuida a otras personas).',
        '',
        f'MRS completo en {len(mrs)} de {n} filas. Media del total: {mrs["mrs_total"].mean():.1f} '
        f'± {mrs["mrs_total"].std():.1f} (somático {mrs["mrs_somatico"].mean():.1f}, psicológico '
        f'{mrs["mrs_psicologico"].mean():.1f}, urogenital {mrs["mrs_urogenital"].mean():.1f}).',
        '',
        _tabla(['Severidad MRS', 'Filas', '%'],
               [(s, int(sev.get(s, 0)), _pct(int(sev.get(s, 0)), len(mrs))) for s in orden]),
        '',
        _tabla(['Etapa', 'Filas', '%'],
               [(e, c, _pct(c, n)) for e, c in limpio['etapa_menopausica'].value_counts().items()]),
        '',
        _tabla(['Tramo de edad', 'Filas'],
               [(t, int(c)) for t, c in limpio['tramo_edad'].value_counts().sort_index().items()]),
        '',
        '## 5. Decisiones que conviene validar con la profesora',
        '',
        '- Cortes de severidad del MRS (0-4 / 5-8 / 9-15 / 16+) y la definición de etapa menopáusica.',
        '- `cambio_relacion_pareja_menopausia` se trata como "no aplica" sin pareja (regla propia del',
        '  análisis: la plataforma muestra la pregunta a todas).',
        '- Las opciones de selección múltiple del dataset (p. ej. "Largas listas de espera",',
        '  "Hijos/as") no son las mismas que ofrece hoy la plataforma (`esquema.OPCIONES_MULTISELECCION`).',
        '  Se conservaron tal como vienen.',
        '- Correcciones de unidad: talla en metros (×100) y presión en cmHg (×10).',
        '',
    ]
    return '\n'.join(out)
