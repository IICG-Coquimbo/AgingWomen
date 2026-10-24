"""Informe de limpieza en Markdown (informe_limpieza_usuaria.md o, para el anexo, informe_limpieza.md)."""
from datetime import date

import pandas as pd

from . import reglas as R


def _tabla(encabezado, filas):
    lineas = ['| ' + ' | '.join(encabezado) + ' |', '|' + '---|' * len(encabezado)]
    lineas += ['| ' + ' | '.join(str(x) for x in fila) + ' |' for fila in filas]
    return '\n'.join(lineas)


def _pct(n, total):
    return f'{100 * n / total:.1f} %' if total else '-'


def generar(limpio, excluidas, diccionario, bit, entrada, salida, archivo, titulo, evaluacion=None):
    n = len(limpio)
    out = [
        f'# {titulo}',
        '',
        f'Generado por `analisis/limpiar_dataset.py` el {date.today().isoformat()}. '
        'Volver a ejecutar el script regenera este informe y los archivos de salida.',
        '',
        f'- Entrada: `{entrada}` — {bit.filas_entrada} filas.',
        f'- Salida: `{salida}/{archivo}` — **{n} filas**.',
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
        '**Fecha de última menstruación vacía:** las preguntas que dependen de ella (regularidad,',
        'sangrado, anticonceptivo) no se imputan, porque no se sabe si aplicaban.',
    ]
    sin_imc = int((limpio['imc_categoria'] == 'no informado').sum())
    if sin_imc:
        out += [
            '',
            f'**IMC:** peso y talla no se imputan cuando faltan más del {R.UMBRAL_EXCLUIR:g} %; el IMC queda',
            f'como `imc_categoria` con el nivel "no informado" ({sin_imc} filas, {_pct(sin_imc, n)}).',
            'Inventar el peso de tantas participantes cambiaría justamente el factor más fuerte.',
        ]
    profesional = int((limpio['origen_registro'] != 'AUTO').sum())
    if profesional:
        out += [
            '',
            '**Ámbito "subgrupo profesional":** laboratorio, presión, tamizaje y talla máxima solo los',
            'registra el personal de salud (`campos_por_rol.SOLO_PROFESIONAL`). Aplican a las '
            f'{profesional} encuestas con origen MEDICO o API, y se',
            'analizan en ese subgrupo, no en el modelado general.',
        ]
    else:
        out += ['', 'Todas las encuestas son autoaplicadas: los campos solo para personal de salud',
                '(laboratorio, presión, tamizaje, talla máxima) son "no aplica" en todas las filas.']

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
        '  y `mrs_severidad` con los cortes de `MRS.SEVERIDAD_TOTAL` (confirmados por la profesora el 20-10).',
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
        '- La definición de etapa menopáusica (los cortes del MRS los confirmó el 20-10).',
        '- `cambio_relacion_pareja_menopausia` se trata como "no aplica" sin pareja (regla propia del',
        '  análisis: la plataforma muestra la pregunta a todas).',
        '- Correcciones de unidad: talla en metros (×100) y presión en cmHg (×10).',
        '- IMC sin imputar, como categoría con "no informado".',
        '',
    ]
    if evaluacion:
        out += _seccion_evaluacion(evaluacion)
    return '\n'.join(out)


def _seccion_evaluacion(ev):
    """Sección 6: comparación con el conjunto verdadero (solo conjunto sintético)."""
    tipos = ev['tipos']
    total = tipos['Total'].sum()
    recuperado = tipos['recuperado'].sum()
    errores = tipos[~tipos['Tipo de error'].str.startswith('omitida')]
    rec_err = errores['recuperado'].sum() / errores['Total'].sum()
    out = [
        '## 6. Evaluación contra el conjunto verdadero',
        '',
        'El conjunto sintético trae su versión sin errores y una bitácora de cada error agregado, así que',
        'se puede medir qué tan bien funciona la limpieza. Cada celda ensuciada termina en uno de estos',
        'estados: **recuperado** (la limpieza devolvió el valor verdadero), **imputado** (quedó un valor',
        'estimado, distinto del verdadero), **vacío** (quedó sin dato) o **fila excluida**.',
        '',
        '### 6.1 Filas excluidas',
        '',
        _tabla(list(ev['filas'].columns), ev['filas'].itertuples(index=False)),
        '',
        '### 6.2 Celdas ensuciadas, por tipo de error',
        '',
        _tabla(list(tipos.columns), tipos.itertuples(index=False)),
        '',
        f'De {total} celdas ensuciadas, {recuperado} ({_pct(recuperado, total)}) recuperaron su valor',
        'verdadero (en las omisiones, "recuperado" significa que la imputación o la deducción coincidió',
        'con el valor real). Sin contar las omisiones, que no se pueden recuperar con certeza, la',
        f'limpieza recupera el **{100 * rec_err:.0f} %** de los errores. Los centinelas se imputan',
        'porque el valor verdadero se perdió.',
        '',
        '### 6.3 Celdas correctas que la limpieza cambió',
        '',
        f'Se revisaron {ev["celdas_revisadas"]} celdas que venían bien; la limpieza cambió por error '
        f'**{ev["cambios_error"]}** ({_pct(ev["cambios_error"], ev["celdas_revisadas"])}).',
        '',
    ]
    if len(ev['cambios']):
        out += [_tabla(list(ev['cambios'].columns), ev['cambios'].itertuples(index=False)), '']
    return out
