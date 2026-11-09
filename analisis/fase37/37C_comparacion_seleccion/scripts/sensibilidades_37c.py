"""
Fase 37C: sensibilidades del conjunto priorizado. Reutiliza los ajustes y etiquetas de la Fase 37B; solo calcula S-IMPMODA, que es nueva.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/sensibilidades_37c.py
"""
import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'sensibilidades'
FAMILIAS = {'S-ORD': 'Codificación', 'S-FAMD': 'Codificación', 'S-RARA': 'Codificación', 'S-TRA': 'Población e imputación', 'S-CUI': 'Población e imputación', 'S-EJE': 'Población e imputación', 'S-IMPMODA': 'Población e imputación',
            'S-EDAD': 'Variables', 'S-SOLAPE': 'Variables', 'S-BLOQUE': 'Ponderación', 'S-BLOQUE-SA': 'Ponderación'}


def impmoda(cad, pri):
    """Las 30 celdas imputadas de tiene_actividad_sexual toman la moda de las 529. Sin tocar la Fase 36."""
    t, nuevos = cad.tabla_imputada()
    dif = (t.astype(str) != cad.tabla.astype(str))
    cambios = dif.sum()
    cambios = cambios[cambios > 0]
    if list(cambios.index) != ['tiene_actividad_sexual'] or int(cambios.iloc[0]) != 30:
        raise SystemExit(f'S-IMPMODA debía cambiar solo 30 celdas de tiene_actividad_sexual; cambió {cambios.to_dict()}')
    idx = np.arange(Q.N)
    et = N.etiquetas_37b()
    filas, etiquetas = [], {'participante_id': cad.ids}
    coords = {}
    for e in Q.ESPACIOS:
        Z = cad.calibrada(e, t, idx).to_numpy()
        coords[e] = (Z, N.coordenadas_cadena(Z, idx)[0])
    for c in pri:
        i = N.info_config(c)
        Z, F = coords[i['base']]
        X = Z if i['componentes'] == 0 else F[:, :i['componentes']]
        l = Q.ajustar(X, i['algoritmo'], i['k'])[0]
        etiquetas[c] = l
        filas.append({'sensibilidad': 'S-IMPMODA', 'familia': FAMILIAS['S-IMPMODA'], 'config': c, 'ari_ajuste': adjusted_rand_score(et[c].to_numpy(), l), 'ari_proyeccion': np.nan, 'tam_min': int(np.bincount(l).min()), 'tamanos': ' '.join(map(str, np.bincount(l, minlength=i['k'])))})
    N.a_csv(pd.DataFrame(etiquetas), S / 's_impmoda_etiquetas.csv')
    return pd.DataFrame(filas)


def main():
    N.huella_sello()
    Q.instalar_gancho()
    cad = N.Cadena()
    pri = list(N.priorizadas())
    h = pd.read_csv(N.B37 / 'sensibilidades' / 'comparacion_sensibilidades.csv')
    t = []
    for c in pri:
        i = N.info_config(c)
        d = h[h['config_base'] == c]
        for x in d.itertuples():
            t.append({'sensibilidad': x.sensibilidad, 'familia': FAMILIAS[x.sensibilidad], 'config': c, 'ari_ajuste': x.ari_ajuste, 'ari_proyeccion': x.ari_proyeccion, 'tam_min': x.tam_min, 'tamanos': x.tamanos})
    tabla = pd.concat([pd.DataFrame(t), impmoda(cad, pri)], ignore_index=True)
    N.a_csv(tabla, S / 'sensibilidades_priorizadas.csv')
    # IMC y algoritmo, desde la Fase 37B
    comp = pd.read_csv(N.B37 / 'resultados' / 'comparaciones_ari.csv')
    et = N.etiquetas_37b()
    imput = cad.imputadas['imc'].to_numpy()
    filas = []
    for c in pri:
        i = N.info_config(c)
        fila = {'config': c}
        par = None
        if i['espacio'].startswith('R0'):
            par = ('R0P2' if i['espacio'] == 'R0P1' else 'R0P1') + c[len(i['espacio']):]
        else:
            otro = {'P1': 'P2', 'P2': 'P1', 'F1': 'F2', 'F2': 'F1'}[i['espacio']]
            par = otro + c[2:]
        fila['par_imc'] = par
        fila['ari_con_sin_imc_529'] = adjusted_rand_score(et[c], et[par])
        fila['ari_con_sin_imc_267'] = adjusted_rand_score(et[c][~imput], et[par][~imput])
        if '_km_' in c or '_ward_' in c:
            otro_alg = c.replace('_km_', '_ward_') if '_km_' in c else c.replace('_ward_', '_km_')
            fila['config_otro_algoritmo'] = otro_alg
            fila['ari_km_ward'] = adjusted_rand_score(et[c], et[otro_alg])
        if not i['espacio'].startswith('R0'):
            otro = {'P1': 'F1', 'P2': 'F2', 'F1': 'P1', 'F2': 'P2'}[i['espacio']] + c[2:]
            fila['ari_pca_famd'] = adjusted_rand_score(et[c], et[otro])
        filas.append(fila)
    N.a_csv(pd.DataFrame(filas), S / 'comparaciones_imc_algoritmo.csv')
    # Tablas de transición (alineadas solo para leerlas)
    tr = []
    for sid in ('S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-EDAD', 'S-SOLAPE'):
        for e in Q.ESPACIOS:
            ruta = N.B37 / 'sensibilidades' / 'etiquetas' / f'{sid}_{e}.csv'
            if not ruta.exists():
                continue
            d = pd.read_csv(ruta, dtype={'participante_id': str}).set_index('participante_id')
            for c in pri:
                i = N.info_config(c)
                if i['espacio'] != e or c not in d.columns:
                    continue
                aj = d['rol'] == 'ajuste'
                base = et.loc[d.index[aj], c].to_numpy()
                m = N.transicion(base, d.loc[aj, c].to_numpy()).stack().reset_index()
                m.columns = ['grupo_base', 'grupo_variante_alineado', 'n']
                m.insert(0, 'sensibilidad', sid)
                m.insert(0, 'config', c)
                tr.append(m)
    N.a_csv(pd.concat(tr, ignore_index=True), S / 'transiciones_sensibilidades.csv')
    print('Filas', len(tabla), '| transiciones', sum(len(x) for x in tr))
    imp = tabla[tabla['sensibilidad'] == 'S-IMPMODA'].set_index('config')['ari_ajuste']
    print(imp.loc[N.lista_b()].round(2).to_string())
    N.registrar('sensibilidades', [('sensibilidades', 'completa', 0.0, Q.leidos())])


if __name__ == '__main__':
    main()
