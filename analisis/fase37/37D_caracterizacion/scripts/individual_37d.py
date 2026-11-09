"""
Fase 37D, etapa 2: características individuales frente al MRS (análisis principal). Familias F1 a F4 del protocolo y sensibilidades S-OBS y S-SIN9.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/individual_37d.py
"""
import nucleo_37d as N
import numpy as np
import pandas as pd

S = N.BASE / 'resultados' / 'individual'


def familia(D, X, resultados, tipo_y, nombre, con_ic=False):
    filas = []
    for j, r in enumerate(resultados):
        y = D.M[r].to_numpy()
        for i, v in enumerate(N.CARACTERISTICAS):
            t = N.tipo_de(v, D.defs)
            x = N.para_prueba(X, v).to_numpy()
            a = N.asociacion(x, y, t, tipo_y)
            fila = {'familia': nombre, 'resultado': r, 'variable': v, 'etiqueta': N.ETIQUETA[v], 'bloque': N.BLOQUE_DE[v], 'usada_por_A': v in N.EN_A, 'tipo': t, **a}
            if con_ic:
                fila['ic_inf'], fila['ic_sup'] = N.bootstrap(x, y, t, semilla_extra=100 * j + i)
            filas.append(fila)
    d = pd.DataFrame(filas)
    d['q'] = N.bh(d['p'].to_numpy())
    d['banda'] = [N.banda(e, m) for e, m in zip(d['efecto'], d['medida'])]
    d['destacada'] = (d['q'] < N.ALFA) & ~d['banda'].isin(['despreciable', 'sin dato'])
    return d


def detalle_binarias(D, X):
    """Medianas y medias del MRS total por nivel, para leer el sentido de cada efecto."""
    filas = []
    for v in N.CARACTERISTICAS:
        t = N.tipo_de(v, D.defs)
        if t not in ('binaria', 'nominal'):
            continue
        x = N.para_prueba(X, v)
        for c in sorted(x.dropna().unique(), key=str):
            y = D.M['mrs_total'][x == c]
            filas.append({'variable': v, 'nivel': c, 'n': len(y), 'media_total': y.mean(), 'mediana_total': y.median(), 'pct_severo': 100 * D.M['severo_mrs'][x == c].mean()})
    return pd.DataFrame(filas)


def main():
    N.instalar_gancho()
    N.huella_sello()
    D = N.cargar()
    X = D.X
    f1 = familia(D, X, ['mrs_total'], 'continua', 'F1', con_ic=True)
    N.a_csv(f1, S / 'F1_total.csv')
    f2 = familia(D, X, ['mrs_somatico', 'mrs_psicologico', 'mrs_urogenital'], 'continua', 'F2')
    N.a_csv(f2, S / 'F2_dimensiones.csv')
    f3 = familia(D, X, ['severo_mrs'], 'binaria', 'F3')
    N.a_csv(f3, S / 'F3_severo.csv')
    f4 = familia(D, X, N.ITEMS, 'continua', 'F4')
    N.a_csv(f4, S / 'F4_items.csv')
    N.a_csv(detalle_binarias(D, X), S / 'detalle_por_nivel.csv')
    # S-OBS: celdas imputadas como faltantes. Se corrige con su propia familia de 36, solo para comparar con F1.
    obs = familia(D, N.solo_observado(X, D.estado, D.heredada), ['mrs_total'], 'continua', 'S-OBS')
    comp = f1[['variable', 'etiqueta', 'medida', 'efecto', 'n', 'q', 'destacada']].merge(obs[['variable', 'efecto', 'n', 'q', 'destacada']], on='variable', suffixes=('', '_obs'))
    comp['cambio_efecto'] = comp['efecto_obs'] - comp['efecto']
    comp['misma_conclusion'] = comp['destacada'] == comp['destacada_obs']
    N.a_csv(comp, S / 'S-OBS_comparacion.csv')
    # S-SIN9: pareja y actividad sexual frente al total y la urogenital sin el ítem 9.
    filas = []
    for v in ('tiene_pareja', 'tiene_actividad_sexual'):
        for r in ('mrs_total', 'mrs_total_sin9', 'mrs_urogenital', 'mrs_urogenital_sin9', 'pregunta_9'):
            filas.append({'variable': v, 'resultado': r, **N.asociacion(X[v].to_numpy(), D.M[r].to_numpy(), 'binaria')})
    N.a_csv(pd.DataFrame(filas), S / 'S-SIN9_individual.csv')
    N.registrar('individual')
    print(f1.sort_values('p')[['variable', 'prueba', 'efecto', 'ic_inf', 'ic_sup', 'n', 'q', 'banda', 'destacada']].to_string(index=False))
    for d in (f2, f3, f4):
        print(d['familia'].iloc[0], int(d['destacada'].sum()), 'destacadas de', len(d))
    print(f2[f2['destacada']][['resultado', 'variable', 'efecto', 'q']].to_string(index=False))
    print(f3[f3['destacada']][['variable', 'prueba', 'efecto', 'q']].to_string(index=False))
    print(comp[['variable', 'efecto', 'efecto_obs', 'n_obs', 'destacada', 'destacada_obs']].to_string(index=False))
    print(pd.DataFrame(filas)[['variable', 'resultado', 'efecto', 'p']].to_string(index=False))


if __name__ == '__main__':
    main()
