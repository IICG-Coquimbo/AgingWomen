"""Informe del análisis exploratorio en Markdown (analisis/informe_exploratorio.md)."""
from datetime import date

import pandas as pd

from . import bosque
from . import variables as V


def _tabla(encabezado, filas):
    lineas = ['| ' + ' | '.join(encabezado) + ' |', '|' + '---|' * len(encabezado)]
    lineas += ['| ' + ' | '.join(str(x) for x in fila) + ' |' for fila in filas]
    return '\n'.join(lineas)


def _f(x, d=1):
    return '-' if pd.isna(x) else f'{x:.{d}f}'


def _p(p):
    return '< 0,001' if p < 0.001 else f'{p:.3f}'


def _metricas(m):
    return ', '.join(f'{c} = {m[c].mean():.2f} ± {m[c].std():.2f}' for c in m.columns if c != 'particion')


def _tabla_cruces(t):
    return _tabla(['Variable', 'Rol', 'n', 'Prueba', 'Efecto', 'p', 'p ajustado (FDR)'],
                  [(V.etiqueta(r.variable), r.rol, r.n, r.prueba, f'{r.medida} = {r.efecto:+.2f}',
                    _p(r.p), _p(r.p_ajustado)) for r in t.itertuples()])


def _tabla_importancia(imp, maximo=15):
    return _tabla(['Variable', 'Importancia (perm.)', 'Positiva en', 'Impureza', 'Útil para el bosque'],
                  [(V.etiqueta(r.variable), f'{r.perm_media:.4f} ± {r.perm_de:.4f}',
                    f'{r.perm_positiva_en}/{bosque.PARTICIONES}', f'{r.impureza_media:.3f}',
                    'sí' if r.seleccionada else 'no') for r in imp.head(maximo).itertuples()])


def generar(r):
    """`r` es el diccionario de resultados que arma analisis/exploratorio.py."""
    n, n_mrs = r['n'], r['n_mrs']
    sig = r['cruces'][r['cruces']['p_ajustado'] < 0.05]
    out = [
        '# Análisis exploratorio de datos (Fase 33)',
        '',
        f'Generado por `analisis/exploratorio.py` el {date.today().isoformat()} a partir de',
        '`datos/limpio/dataset_menopausia_limpio.csv` (Fase 32). Corresponde a OB2, Actividad 1',
        'del documento del seminario.',
        '',
        f'- Participantes: **{n}**; con MRS completo: **{n_mrs}**.',
        f'- Encuestas aplicadas por personal de salud (MEDICO o API): {r["n_profesional"]}.',
        f'- Trabajan actualmente y respondieron la sección Trabajo: {r["n_trabajan"]}'
        + (f' (quedan fuera del modelo de trabajadoras los participante_id '
           f'{", ".join(r["trabajan_sin_seccion"])}: "¿trabaja?" venía vacío, se imputó "sí" en la '
           'limpieza y no respondieron la sección).' if r['trabajan_sin_seccion'] else '.'),
        '- Frecuencias completas de todas las variables: [`resultados/frecuencias.md`](resultados/frecuencias.md).',
        '',
        '## 1. Variables continuas',
        '',
        _tabla(['Variable', 'n', 'Media ± DE', 'Mediana [Q1-Q3]', 'Mín-Máx'],
               [(V.etiqueta(x.variable), x.n, f'{_f(x.media)} ± {_f(x.de)}',
                 f'{_f(x.mediana)} [{_f(x.q1)}-{_f(x.q3)}]', f'{_f(x.min)}-{_f(x.max)}')
                for x in r['continuas'].itertuples()]),
        '',
        '## 2. Perfil sintomático',
        '',
        '![Distribución del MRS total](figuras/eda/mrs_total.png)',
        '',
        '![Síntomas en grado moderado o mayor](figuras/eda/sintomas.png)',
        '',
        _tabla(['Síntoma (ítem MRS)', '% moderado o mayor', 'Media (0-4)'],
               [(x.sintoma, _f(x.pct_moderado_o_mas), _f(x.media, 2)) for x in r['perfil'].itertuples()]),
        '',
        '### Severidad según etapa y edad',
        '',
        '![Severidad por etapa menopáusica](figuras/eda/severidad_etapa.png)',
        '',
    ]
    for titulo, tabla in (('Etapa menopáusica', r['sev_etapa']), ('Tramo de edad', r['sev_edad']),
                          ('Trabaja actualmente', r['sev_trabaja'])):
        out += [_tabla([titulo, 'n', 'MRS medio'] + V.ORDEN_SEVERIDAD,
                       [(i, int(f['n']), _f(f['mrs_medio'])) + tuple(f'{f[s]:.0f} %' for s in V.ORDEN_SEVERIDAD)
                        for i, f in tabla.iterrows()]), '']

    out += [
        '## 3. Relación de cada variable con el MRS total',
        '',
        'Spearman para variables ordinales, continuas y binarias (rho > 0: más síntomas); Kruskal-Wallis',
        'para categóricas de más de dos valores (ε² = tamaño de efecto). Los valores p se ajustan por',
        f'comparaciones múltiples (Benjamini-Hochberg) sobre las {len(r["cruces"])} pruebas. Las variables de',
        'rol **impacto** son consecuencias de los síntomas: se muestran para describir su efecto en la',
        'vida laboral y de pareja, no como causas.',
        '',
        '![Variables asociadas al MRS](figuras/eda/correlaciones.png)',
        '',
        f'**{len(sig)} asociaciones significativas** (p ajustado < 0,05):',
        '',
        _tabla_cruces(sig),
        '',
        f'Sin asociación significativa: {", ".join(V.etiqueta(v) for v in r["cruces"].loc[r["cruces"]["p_ajustado"] >= 0.05, "variable"])}.',
        '',
        '## 4. Valores atípicos (regla de Tukey, 1,5 × RIC)',
        '',
        'Se informan y **no se eliminan**: los valores imposibles ya se trataron en la limpieza, así que',
        'estos son extremos plausibles.',
        '',
        _tabla(['Variable', 'n', 'Rango esperado', 'Atípicos', '%', 'Valores'],
               [(V.etiqueta(x.variable), x.n, f'{_f(x.limite_inferior)} a {_f(x.limite_superior)}',
                 x.atipicos, _f(x.pct), x.valores) for x in r['atipicos'].itertuples()]),
        '',
        '## 5. Random Forest: importancia de las variables',
        '',
        f'Bosques de {bosque.PARAMETROS["n_estimators"]} árboles (hojas de al menos '
        f'{bosque.PARAMETROS["min_samples_leaf"]} casos, semilla {bosque.SEMILLA}), validación cruzada de',
        f'{bosque.PARTICIONES} particiones. La importancia es por **permutación** en cada partición de prueba',
        f'({bosque.REPETICIONES} repeticiones): cuánto empeora el modelo al desordenar la variable en datos que',
        'no vio. También se informa la importancia por impureza, que tiende a favorecer variables',
        'continuas con muchos valores.',
        '',
        '**Criterio de selección.** Una variable entra a la selección final si cumple cualquiera de:',
        '',
        f'1. el bosque de regresión la encuentra útil (importancia positiva) en al menos '
        f'{bosque.MINIMO_PARTICIONES} de las {bosque.PARTICIONES} particiones, o',
        '2. tiene relación significativa con el MRS en el análisis bivariado (sección 3, p ajustado < 0,05).',
        '',
        'Con relaciones débiles, una variable útil puede no aportar en alguna partición solo por qué',
        'participantes cayeron en ella; combinar las dos fuentes evita perderla por azar. Al final se',
        'quitan las redundantes (|rho| ≥ 0,8 entre sí).',
        '',
        'Entradas: **predictores** (hábitos, actividad física, alimentación, sustancias, cuidado) y',
        '**variables de control** (edad, etapa, IMC, terapia hormonal, educación, previsión, trabajo).',
        'Las variables de impacto no entran.',
        '',
    ]
    for clave, titulo in (('general', 'Modelo general'), ('trabajadoras', 'Modelo de trabajadoras')):
        m = r['modelos'][clave]
        out += [
            f'### {titulo} (n = {m["n"]}, {m["X"].shape[1]} variables)',
            '',
            f'- Regresión sobre el MRS total: {_metricas(m["met_reg"])}.',
            f'- Clasificación severa (MRS ≥ {V.CORTE_SEVERA}) vs. no severa '
            f'({m["prop_severa"]:.0f} % severas): {_metricas(m["met_cla"])}.',
            '',
            f'![Importancia — {titulo}](figuras/eda/importancia_{clave}.png)',
            '',
            '**Regresión (MRS total):**',
            '',
            _tabla_importancia(m['imp_reg']),
            '',
            '**Clasificación (severa / no severa):**',
            '',
            _tabla_importancia(m['imp_cla']),
            '',
        ]
        if len(m['redundantes']):
            out += ['Pares redundantes (|rho| ≥ 0,8) entre las seleccionadas; se descarta la menos importante:', '',
                    _tabla(['Variable A', 'Variable B', '|rho|', 'Descartada'],
                           [(V.etiqueta(x.a), V.etiqueta(x.b), _f(x.rho, 2), V.etiqueta(x.descartada))
                            for x in m['redundantes'].itertuples()]), '']
        else:
            out += ['No hay pares redundantes (|rho| ≥ 0,8) entre las variables seleccionadas.', '']
        out += [f'**Selección final ({len(m["final"])} variables):**', '',
                _tabla(['Variable', 'Seleccionada por'],
                       [(V.etiqueta(v), m['motivo'][v]) for v in m['final']]), '']

    out += [
        'La lista completa está en `analisis/resultados/importancia_variables.csv` y es la entrada de',
        'la Fase 34 (codificación, escalado y PCA).',
        '',
        '## 6. Subgrupo de personal de salud',
        '',
        f'Laboratorio, presión y tamizaje solo existen en las {r["n_profesional"]} encuestas aplicadas por',
        'personal de salud. Se analizan aparte (FDR propio) y no entran al Random Forest principal.',
        '',
        _tabla(['Variable', 'n', 'Media ± DE', 'Mediana [Q1-Q3]'],
               [(V.etiqueta(x.variable), x.n, f'{_f(x.media)} ± {_f(x.de)}',
                 f'{_f(x.mediana)} [{_f(x.q1)}-{_f(x.q3)}]') for x in r['continuas_prof'].itertuples()]),
        '',
        _tabla_cruces(r['cruces_prof']),
        '',
        '## 7. Limitaciones',
        '',
        '- Diseño transversal (una sola ronda): las asociaciones no prueban causalidad.',
        '- Los cortes de severidad del MRS y la definición de etapa están pendientes de validar con la profesora.',
        '- La importancia por permutación se reparte entre variables correlacionadas (p. ej. tipos de',
        '  ejercicio entre sí); por eso se revisan también las asociaciones bivariadas.',
        '',
    ]
    return '\n'.join(out)


def frecuencias_md(frec):
    out = ['# Frecuencias de todas las variables (Fase 33)', '',
           'Porcentajes sobre las filas con dato (los "no aplica" no cuentan).', '']
    for v, t in frec.groupby('variable', sort=False):
        out += [f'## {V.etiqueta(v)} (`{v}`)', '',
                _tabla(['Valor', 'n', '%'], [(x.valor, x.n, _f(x.pct)) for x in t.itertuples()]), '']
    return '\n'.join(out)
