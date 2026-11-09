"""
Fase 37C: examina de qué depende la conclusión por reglas. No cambia ningún criterio ni la decisión: informa qué pasaría con otras lecturas, si la partición es única dentro de su familia,
qué tan cerca de las fronteras está cada participante, y guarda los artefactos reproducibles de las elegibles, siempre como provisionales.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/revision_decision_37c.py
"""
from itertools import combinations

import interpretabilidad_37c as IN
import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'seleccion'


def leer():
    return {'f': pd.read_csv(S / 'finalistas.csv'), 'ev': pd.read_csv(S / 'evaluacion_por_etapa.csv'), 'rep': pd.read_csv(N.BASE / 'sensibilidades' / 's_ord' / 'comparacion_representaciones.csv').set_index('config'), 'nula': pd.read_csv(N.BASE / 'referencias_nulas' / 'comparacion_por_configuracion.csv').set_index('config'),
            'interp': pd.read_csv(N.BASE / 'interpretabilidad' / 'resumen_interpretabilidad.csv').set_index('config'), 'dec': N.leer_json(S / 'decision_preliminar_reglas.json'), 'desc': pd.read_csv(N.BASE / 'sensibilidades' / 's_ord' / 'descomposicion.csv').set_index('config')}


def dependencia(d):
    el = d['dec']['elegibles_B'] + d['dec']['elegibles_A']
    sens = d['ev']
    def s_var(c, s):
        return float(sens[(sens['config'] == c) & (sens['criterio'] == s)]['valor'].iloc[0])
    lecturas = [('Regla del protocolo (regla V: S-SOLAPE no bloquea B)', lambda c: True),
                ('S-SOLAPE bajo 0,40 bloquea la selección', lambda c: s_var(c, 'S-SOLAPE') >= 0.40),
                ('Ridit como codificación: E3 entre ≥ 0,65 y p05 ≥ 0,50', lambda c: d['rep'].loc[c, 'E3_entre_media_ridit'] >= 0.65 and d['rep'].loc[c, 'E3_entre_p05_ridit'] >= 0.50),
                ('Puntuaciones normales: E3 entre ≥ 0,65 y p05 ≥ 0,50', lambda c: d['rep'].loc[c, 'E3_entre_media_normal'] >= 0.65 and d['rep'].loc[c, 'E3_entre_p05_normal'] >= 0.50),
                ('Exigir que la silueta supere a la referencia correlacionada', lambda c: bool(d['nula'].loc[c, 'silueta_supera_todas'])),
                ('Exigir estabilidad E1 sobre la referencia', lambda c: bool(d['nula'].loc[c, 'E1_ari_entre_media_supera_todas'])),
                ('Reconstrucción con 2 variables bajo 0,50, no 0,65', lambda c: d['interp'].loc[c, 'ari_reconstruccion_2'] < 0.50),
                ('S-ORD completa ≥ 0,70, no 0,40', lambda c: s_var(c, 'S-ORD') >= 0.70)]
    filas = []
    for nombre, f in lecturas:
        sigue = [c for c in el if f(c)]
        filas.append({'lectura': nombre, 'siguen': ' | '.join(sigue) if sigue else 'Ninguna', 'conclusion': d['dec']['conclusion'] if sigue else 'C', 'es_el_protocolo': nombre.startswith('Regla del protocolo')})
    return pd.DataFrame(filas)


def familia(d, et, t):
    salida = []
    h = pd.read_csv(N.B37 / 'sensibilidades' / 'comparacion_sensibilidades.csv').pivot_table(index='config_base', columns='sensibilidad', values='ari_ajuste')
    cr = pd.read_csv(S / 'cribado_lista_A.csv').set_index('config')
    for ref in d['dec']['elegibles_B'] + d['dec']['elegibles_A']:
        for c in cr[cr['pasa_todo']].index:
            salida.append({'referencia': ref, 'config': c, 'k': int(N.info_config(c)['k']), 'en_priorizadas': bool(cr.loc[c, 'en_priorizadas']), 'ari_con_referencia': adjusted_rand_score(et[ref], et[c]), 'E3_entre_media': cr.loc[c, 'E3_entre_media'], 'S_ORD': cr.loc[c, 'S_ORD'], 'S_SOLAPE': cr.loc[c, 'S_SOLAPE'], 'fraccion_eje1': cr.loc[c, 'fraccion_eje1']})
    return pd.DataFrame(salida)


def fronteras(d, cad, et):
    filas = []
    for c in d['f']['config']:
        i = N.info_config(c)
        X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
        l = et[c].to_numpy()
        protos = Q.prototipos(X, l, i['k'])
        _, d1, _, m = Q.asignar(protos, X)
        filas.append({'config': c, 'margen_mediano': float(np.median(m)), **{f'pct_margen_bajo_{u}': float(100 * (m < float(u)).mean()) for u in ('0.05', '0.10', '0.15', '0.20')}})
    return pd.DataFrame(filas)


def pocas_variables(d, cad, et):
    """Exploratorio, fuera del protocolo: mejor trío exhaustivo y cuarteto por adición. No cambia la clase sellada, que se define con 1 y 2 variables."""
    defs, vals = IN.numericos(cad)
    enc = IN.codificar_para_celdas(defs, vals)
    variables = list(defs)
    pliegues = IN.particiones_cv(Q.N)
    filas = []
    for c in d['dec']['elegibles_B'] + d['dec']['elegibles_A']:
        l = et[c].to_numpy()
        k = N.info_config(c)['k']
        mejor, trio = -1.0, None
        for a, b, e in combinations(variables, 3):
            cod = pd.factorize(enc[a] * 10000 + enc[b] * 100 + enc[e])[0]
            r = IN.reconstruir(cod, l, pliegues, k)
            if r > mejor:
                mejor, trio = r, (a, b, e)
        base = pd.factorize(enc[trio[0]] * 10000 + enc[trio[1]] * 100 + enc[trio[2]])[0]
        mejor4, cuarta = -1.0, None
        for v in variables:
            if v not in trio:
                r = IN.reconstruir(pd.factorize(base * 100 + enc[v])[0], l, pliegues, k)
                if r > mejor4:
                    mejor4, cuarta = r, v
        filas.append({'config': c, 'mejor_trio': ' + '.join(trio), 'ari_3': mejor, 'cuarta_variable': cuarta, 'ari_4': mejor4})
        print(c, filas[-1], flush=True)
    return pd.DataFrame(filas)


def artefactos(d, cad, et):
    """Guarda lo necesario para reproducir cada partición elegible, sin copiar artefactos de la Fase 36 ni de la 37A: los cita por huella."""
    for c in d['dec']['elegibles_B'] + d['dec']['elegibles_A']:
        i = N.info_config(c)
        carpeta = S / 'artefactos_provisionales' / c
        X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
        l, ajuste, centros = Q.ajustar(X, i['algoritmo'], i['k'])
        if not (l == et[c].to_numpy()).all():
            raise SystemExit(f'{c}: no reproduce sus etiquetas')
        N.a_json({'configuracion': c, 'estado': 'PROVISIONAL: sujeto a la Fase 37D y a fases posteriores. No es un modelo clínico.', 'reduccion': 'PCA' if i['espacio'][0] == 'P' else 'FAMD', 'con_imc': i['espacio'][1] == '1', 'componentes': i['componentes'], 'algoritmo': 'K-means', 'k': i['k'], 'parametros': {'n_init': 50, 'random_state': 42, 'algorithm': 'lloyd'},
                  'centroides': centros.tolist(), 'inercia': ajuste['inercia'], 'tamanos': np.bincount(l).tolist(), 'transformador': {'carpeta': f'analisis/fase36/artefactos/{i["base"]}', **{p.name: N.sha(p) for p in sorted((N.F36 / 'artefactos' / i['base']).glob('*.json')) if p.name != 'huellas.json'}},
                  'reduccion_modelo': {'archivo': f'analisis/fase37/37A_reduccion/artefactos/{i["base"]}/modelo.json', 'sha256': N.sha(N.A37 / 'artefactos' / i['base'] / 'modelo.json')}, 'flujo': ['Transformador congelado de la Fase 36', 'proyectar de la Fase 37A', 'centroide más cercano', 'señal de incertidumbre (provisional)']}, carpeta / 'modelo_segmentacion.json')
        N.a_csv(pd.DataFrame({'participante_id': cad.ids, 'grupo': l}), carpeta / 'etiquetas.csv')


def perfiles(d):
    desc = pd.read_csv(N.BASE / 'interpretabilidad' / 'descriptivos_por_grupo.csv')
    ef = pd.read_csv(N.BASE / 'interpretabilidad' / 'efecto_por_variable.csv')
    filas = []
    for c in d['f']['config']:
        top = ef[ef['config'] == c].sort_values('efecto', ascending=False).head(10)
        for x in top.itertuples():
            q = desc[(desc['config'] == c) & (desc['variable'] == x.variable)]
            fila = {'config': c, 'variable': x.variable, 'bloque': x.bloque, 'efecto': x.efecto, 'medida': x.medida, 'parte_ssb': x.parte_ssb}
            for y in q.itertuples():
                fila[f'grupo_{y.grupo}'] = y.moda if y.tipo == 'nominal' else y.media
            filas.append(fila)
    return pd.DataFrame(filas)


def main():
    N.huella_sello()
    Q.instalar_gancho()
    d = leer()
    cad = N.Cadena()
    et = N.etiquetas_37b()
    t = N.tabla_37b()
    dep = dependencia(d)
    N.a_csv(dep, S / 'dependencia_conclusion.csv')
    fam = familia(d, et, t)
    N.a_csv(fam, S / 'familia_cribado.csv')
    fr = fronteras(d, cad, et)
    N.a_csv(fr, S / 'cercania_fronteras.csv')
    artefactos(d, cad, et)
    per = perfiles(d)
    N.a_csv(per, S / 'variables_que_mas_separan.csv')
    N.a_csv(pocas_variables(d, cad, et), S / 'reconstruccion_tres_cuatro_variables.csv')
    pd.set_option('display.width', 230, 'display.max_columns', 30, 'display.max_colwidth', 70)
    print(dep.drop(columns='es_el_protocolo').to_string())
    print(fam[(fam['k'] >= 3)].round(2).sort_values(['referencia', 'ari_con_referencia'], ascending=[True, False]).to_string())
    print(fr.round(1).to_string())
    print(per[per['config'] == 'P2_c12_km_k4'].round(2).drop(columns=['config', 'medida']).to_string())
    N.registrar('revision de la decision', [('revision', 'completa', 0.0, Q.leidos())])


if __name__ == '__main__':
    main()
