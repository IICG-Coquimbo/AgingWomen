"""
Fase 37D, etapa 1: diccionario de variables usadas y descripción general de las 529 participantes y del MRS. No calcula asociaciones.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/descripcion_37d.py
"""
import nucleo_37d as N
import numpy as np
import pandas as pd

S = N.BASE / 'resultados' / 'descripcion'


def significado(v, D):
    d = D.defs.get(v)
    if d and d.get('niveles'):
        return {str(x['codigo'] if x['codigo'] is not None else n): x['significado'] for n, x in d['niveles'].items()}
    return {}


def diccionario(D):
    filas = []
    for v in N.CARACTERISTICAS:
        t = N.tipo_de(v, D.defs)
        niv = significado(v, D)
        if v in D.estado.columns:
            e = D.estado[v].value_counts().to_dict()
            her = int((D.heredada[v].astype(str) == '1').sum())
        else:
            e, her = {}, 0
        fuente = 'fase36/procedencia/procedencia_celdas.csv' if v in D.estado.columns else 'datos/limpio_usuaria/dataset_usuaria_limpio.csv'
        cod = '; '.join(f'{k} = {s}' for k, s in sorted(set(niv.items()), key=lambda x: str(x[0]))) if niv else ('valor numérico' if t == 'cuantitativa' else 'código del instrumento' if t == 'ordinal' else 'texto' if t == 'nominal' else '0 = No; 1 = Sí')
        filas.append({'variable': v, 'etiqueta': N.ETIQUETA[v], 'bloque': N.BLOQUE_DE[v], 'usada_por_A': v in N.EN_A, 'tipo': t, 'poblacion': N.POBLACION.get(v, 'Las 529'),
                      'codificacion': cod, 'observadas': e.get('observada', np.nan), 'imputadas': e.get('imputada', np.nan), 'deducidas': e.get('deducida', np.nan), 'no_aplica': e.get('no_aplicable', np.nan),
                      'faltantes': e.get('faltante', np.nan), 'pregunta_madre_imputada': her, 'n_analisis': int(D.X[v].notna().sum()), 'fuente': fuente})
    for it in N.ITEMS:
        filas.append({'variable': it, 'etiqueta': f'MRS ítem {it.split("_")[1]}: {N.NOMBRE_ITEM[it]}', 'bloque': 'MRS', 'usada_por_A': False, 'tipo': 'ordinal', 'poblacion': 'Las 529',
                      'codificacion': '0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa', 'observadas': 529, 'imputadas': 0, 'deducidas': 0, 'no_aplica': 0, 'faltantes': 0,
                      'pregunta_madre_imputada': 0, 'n_analisis': 529, 'fuente': 'datos/limpio_usuaria/dataset_usuaria_limpio.csv'})
    for r, txt in [('mrs_somatico', 'Suma de los ítems 1 a 4 (0 a 16)'), ('mrs_psicologico', 'Suma de los ítems 5 a 8 (0 a 16)'), ('mrs_urogenital', 'Suma de los ítems 9 a 11 (0 a 12)'),
                   ('mrs_total', 'Suma de los 11 ítems (0 a 44)'), ('severidad', '0-4 sin síntomas o muy leves; 5-8 leve; 9-15 moderada; 16 o más severa'), ('severo_mrs', '1 si el total es 16 o más'),
                   ('mrs_total_sin9', 'Total sin el ítem 9, solo para la sensibilidad S-SIN9'), ('mrs_urogenital_sin9', 'Urogenital sin el ítem 9, solo para S-SIN9')]:
        filas.append({'variable': r, 'etiqueta': N.RESULTADOS.get(r, r), 'bloque': 'MRS (derivada)', 'usada_por_A': False, 'tipo': 'cuantitativa' if r not in ('severidad', 'severo_mrs') else 'ordinal' if r == 'severidad' else 'binaria',
                      'poblacion': 'Las 529', 'codificacion': txt, 'observadas': 529, 'imputadas': 0, 'deducidas': 0, 'no_aplica': 0, 'faltantes': 0, 'pregunta_madre_imputada': 0, 'n_analisis': 529,
                      'fuente': 'Recalculada desde los ítems y comparada con la limpieza'})
    return pd.DataFrame(filas)


def numerica(x):
    x = pd.Series(x, dtype=float).dropna()
    return {'n': len(x), 'media': x.mean(), 'de': x.std(ddof=1), 'mediana': x.median(), 'q1': x.quantile(0.25), 'q3': x.quantile(0.75), 'minimo': x.min(), 'maximo': x.max()}


def describir(D):
    num, cat = [], []
    for v in N.CARACTERISTICAS:
        t = N.tipo_de(v, D.defs)
        x = D.X[v]
        if t in ('cuantitativa', 'ordinal', 'binaria'):
            num.append({'variable': v, 'etiqueta': N.ETIQUETA[v], 'bloque': N.BLOQUE_DE[v], 'usada_por_A': v in N.EN_A, 'tipo': t, **numerica(x)})
        if t != 'cuantitativa':
            niv = significado(v, D)
            vc = x.value_counts(dropna=True)
            for c, k in vc.sort_index().items():
                clave = str(int(c)) if isinstance(c, float) else str(c)
                txt = niv.get(clave, {'0': 'No', '1': 'Sí'}.get(clave, clave) if t == 'binaria' else clave)
                if v in ('frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza') and clave == '0':
                    txt = 'No realiza o nunca (incluye 0 estructural)'
                if v == 'cantidad_personas_cuida' and clave == '0':
                    txt = 'No cuida (0 estructural)'
                cat.append({'variable': v, 'etiqueta': N.ETIQUETA[v], 'categoria': clave, 'significado': txt, 'n': int(k), 'pct': 100 * k / vc.sum(), 'n_validos': int(vc.sum())})
    return pd.DataFrame(num), pd.DataFrame(cat)


def describir_mrs(D):
    M = D.M
    filas = [{'resultado': r, 'etiqueta': N.RESULTADOS.get(r, N.NOMBRE_ITEM.get(r, r)), 'maximo': N.MAXIMO.get(r, 4), **numerica(M[r])} for r in list(N.RESULTADOS) + N.ITEMS]
    sev = M['severidad'].value_counts().reindex(N.ORDEN_SEVERIDAD)
    sev = pd.DataFrame({'severidad': sev.index, 'n': sev.to_numpy(), 'pct': 100 * sev.to_numpy() / 529})
    items = pd.DataFrame([{'item': it, 'etiqueta': N.NOMBRE_ITEM[it], 'nivel': k, 'n': int((M[it] == k).sum()), 'pct': 100 * (M[it] == k).mean()} for it in N.ITEMS for k in range(5)])
    corr = M[list(N.RESULTADOS)].corr(method='spearman').reset_index().rename(columns={'index': 'resultado'})
    return pd.DataFrame(filas), sev, items, corr


def main():
    N.instalar_gancho()
    N.huella_sello()
    D = N.cargar()
    dic = diccionario(D)
    N.a_csv(dic, N.BASE / 'diccionario' / 'diccionario_variables_37D.csv')
    num, cat = describir(D)
    N.a_csv(num, S / 'caracteristicas_numericas.csv')
    N.a_csv(cat, S / 'caracteristicas_categorias.csv')
    imp = D.estado[[v for v in N.EN_A]].eq('imputada')
    resumen = {'n': 529, 'con_alguna_imputacion_en_A': int(imp.any(axis=1).sum()), 'pct_con_alguna_imputacion_en_A': float(100 * imp.any(axis=1).mean()),
               'con_imputacion_en_las_tres_preguntas': int(imp[list(N.TRIO)].any(axis=1).sum()), 'celdas_imputadas_en_A': int(imp.to_numpy().sum()),
               'celdas_A': int(imp.size), 'etapa': D.X['etapa_menopausica'].value_counts().to_dict(), 'prevision': D.X['prevision'].value_counts().to_dict()}
    N.a_json(resumen, S / 'resumen_imputacion.json')
    m, sev, items, corr = describir_mrs(D)
    N.a_csv(m, S / 'mrs_descripcion.csv')
    N.a_csv(sev, S / 'mrs_severidad.csv')
    N.a_csv(items, S / 'mrs_items_niveles.csv')
    N.a_csv(corr, S / 'mrs_correlacion_dimensiones.csv')
    N.registrar('descripcion')
    print(num[['variable', 'n', 'media', 'mediana']].to_string(index=False))
    print(m[['resultado', 'media', 'de', 'mediana', 'q1', 'q3']].to_string(index=False))
    print(sev.to_string(index=False), resumen)


if __name__ == '__main__':
    main()
