"""
Fase 37C: aplica las reglas de la sección 10 del protocolo, etapa por etapa y sin puntuación compuesta. Lee tablas guardadas; solo reajusta para comprobar la reproducción de etiquetas.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/seleccion_37c.py
"""
import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'seleccion'
LIM = 0.03
UMBRALES = {'est_crit': 0.65, 'est_adv': 0.80, 'p05_crit': 0.50, 'p05_adv': 0.65, 'cod_crit': 0.40, 'cod_adv': 0.65, 'pob_crit': 0.65, 'pob_adv': 0.80, 'var_crit': 0.40, 'var_adv': 0.65}
COD, POB, VAR = ('S-ORD', 'S-FAMD', 'S-RARA'), ('S-TRA', 'S-CUI', 'S-EJE', 'S-IMPMODA'), ('S-EDAD', 'S-SOLAPE')


def estado(x, adv, crit):
    if pd.isna(x):
        return 'NE'
    return 'CRIT' if x < crit else 'ADV' if x < adv else 'OK'


def reproduccion(configs, et):
    filas = []
    for c in configs:
        i = N.info_config(c)
        X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
        l = Q.ajustar(X, i['algoritmo'], i['k'])[0]
        filas.append({'config': c, 'ari_con_etiquetas_37B': adjusted_rand_score(et[c].to_numpy(), l), 'identicas': bool((l == et[c].to_numpy()).all())})
    return pd.DataFrame(filas)


def cargar():
    d = {'comp': pd.read_csv(N.BASE / 'estabilidad' / 'comparacion_niveles.csv').set_index('config'), 'sens': pd.read_csv(N.BASE / 'sensibilidades' / 'sensibilidades_priorizadas.csv'), 'interp': pd.read_csv(N.BASE / 'interpretabilidad' / 'resumen_interpretabilidad.csv').set_index('config'),
         'nula': pd.read_csv(N.BASE / 'referencias_nulas' / 'comparacion_por_configuracion.csv').set_index('config'), 'busq': pd.read_csv(N.BASE / 'referencias_nulas' / 'busqueda_multiple.csv').set_index('metrica'), 't': N.tabla_37b(), 'asign': pd.read_csv(N.BASE / 'asignacion' / 'evaluacion_asignacion.csv').set_index('config')}
    return d


def criterios(c, d, u=UMBRALES):
    t, comp, sens, interp, nula, busq = d['t'].loc[c], d['comp'].loc[c], d['sens'][d['sens']['config'] == c].set_index('sensibilidad')['ari_ajuste'], d['interp'].loc[c], d['nula'].loc[c], d['busq']
    f = []

    def add(et, cr, val, est):
        cerca = est != 'NE' and any(abs(val - x) < LIM for x in umb_crit.get(cr, [])) if not pd.isna(val) else False
        f.append({'config': c, 'etapa': et, 'criterio': cr, 'valor': val, 'estado': est, 'en_el_limite': cerca})
    umb_crit = {'E3 ari_fuera media': [u['est_crit']], 'E3 ari_fuera p05': [u['p05_crit']], 'E3 ari_entre media': [u['est_crit']], 'E3 ari_entre p05': [u['p05_crit']], 'Ward: prototipos': [0.65], **{s: [u['cod_crit']] for s in COD}, **{s: [u['pob_crit']] for s in POB}, **{s: [u['var_crit']] for s in VAR}}
    add('1. Integridad', 'Etiquetas reproducidas', d['repro'].loc[c, 'ari_con_etiquetas_37B'], 'OK' if d['repro'].loc[c, 'identicas'] else 'CRIT')
    if '_ward_' in c:
        add('2. Asignación', 'Ward: prototipos', t['acuerdo_prototipo_ari'], estado(t['acuerdo_prototipo_ari'], 0.80, 0.65))
    add('2. Asignación', 'E3 ari_fuera media', comp['E3_fuera_media'], estado(comp['E3_fuera_media'], u['est_adv'], u['est_crit']))
    add('2. Asignación', 'E3 ari_fuera p05', comp['E3_fuera_p05'], estado(comp['E3_fuera_p05'], u['p05_adv'], u['p05_crit']))
    add('3. Estabilidad', 'E3 ari_entre media', comp['E3_entre_media'], estado(comp['E3_entre_media'], u['est_adv'], u['est_crit']))
    add('3. Estabilidad', 'E3 ari_entre p05', comp['E3_entre_p05'], estado(comp['E3_entre_p05'], u['p05_adv'], u['p05_crit']))
    for s in COD:
        add('4. Codificación', s, sens.get(s, np.nan), estado(sens.get(s, np.nan), u['cod_adv'], u['cod_crit']))
    for s in POB:
        add('4. Población e imputación', s, sens.get(s, np.nan), estado(sens.get(s, np.nan), u['pob_adv'], u['pob_crit']))
    for s in VAR:
        add('4. Variables', s, sens.get(s, np.nan), estado(sens.get(s, np.nan), u['var_adv'], u['var_crit']))
    sup_s = bool(nula['silueta_supera_todas'])
    sup_e = bool(nula['E1_ari_entre_media_supera_todas'])
    add('5. Nula correlacionada', 'Silueta supera a todas', nula['silueta_p'], 'OK' if sup_s else 'ADV')
    add('5. Nula correlacionada', 'E1 ari_entre supera a todas', nula['E1_ari_entre_media_p'], 'OK' if sup_e else 'ADV')
    ctrl_s = nula['silueta_z'] > busq.loc['silueta', 'z_max_replicas_max']
    ctrl_e = nula['E1_ari_entre_media_z'] > busq.loc['E1_ari_entre_media', 'z_max_replicas_max']
    add('5. Nula correlacionada', 'Supera control de búsqueda múltiple', float(min(nula['silueta_z'], nula['E1_ari_entre_media_z'])), 'OK' if (ctrl_s and ctrl_e) else 'ADV')
    add('6. Tamaños', 'Grupo menor', t['tam_min'], 'ADV' if t['tam_min'] < 27 else 'OK')
    add('7. Separación', 'Silueta negativa (proporción)', t['silueta_negativos'], 'ADV' if t['silueta_negativos'] >= 0.10 else 'OK')
    add('8. Interpretabilidad', interp['clase'], interp['ari_reconstruccion_2'], 'ADV' if interp['clase'] == 'Difícil de interpretar' else 'OK')
    comp_alta = t['componentes'] == 0 or t['componentes'] >= 12
    add('9. Complejidad', 'Componentes', t['componentes'], 'ADV' if comp_alta else 'OK')
    return f


def elegibles(tab):
    malos = tab[(tab['estado'] == 'CRIT') & tab['etapa'].isin(['1. Integridad', '2. Asignación', '3. Estabilidad', '4. Codificación', '4. Población e imputación'])]['config'].unique()
    r0 = [c for c in tab['config'].unique() if c.startswith('R0')]
    return [c for c in tab['config'].unique() if c not in set(malos) and c not in r0]


def concluir(tab, d, et):
    """Finalistas y conclusión, sección 10.1 y 10.2."""
    fin = elegibles(tab)
    n_adv = tab[tab['estado'] == 'ADV'].groupby('config').size()
    orden = sorted(fin, key=lambda c: (n_adv.get(c, 0), bool(d['t'].loc[c, 'con_imc']), d['t'].loc[c, 'componentes']))
    reps, cubiertas = [], {}
    for c in orden:
        par = next((r for r in reps if adjusted_rand_score(et[c], et[r]) >= 0.95), None)
        if par is None:
            reps.append(c)
            cubiertas[c] = [c]
        else:
            cubiertas[par].append(c)
    salida = []
    for c in reps:
        x = tab[tab['config'] == c]
        crit = x[x['estado'] == 'CRIT']['criterio'].tolist()
        clase = d['interp'].loc[c, 'clase']
        multi = clase == 'Segmentación multivariable'
        nula_ok = (x[x['etapa'] == '5. Nula correlacionada']['estado'] == 'OK').all()
        var_crit = [s for s in crit if s in VAR]
        conclusion = 'A' if (not crit and nula_ok and multi) else 'B' if multi else 'No elegible'
        salida.append({'config': c, 'representa_a': ' | '.join(cubiertas[c]), 'clase': clase, 'n_adv': int(n_adv.get(c, 0)), 'crit': ' | '.join(crit), 'regla_v': ' | '.join(var_crit), 'supera_nula': bool(nula_ok), 'elegible_para': conclusion,
                       'motivo_no_elegible': '' if multi else f'Clase «{clase}»: preguntar directamente esas variables es más simple'})
    f = pd.DataFrame(salida)
    if len(f) and (f['elegible_para'] == 'A').any():
        conc = 'A'
    elif len(f) and (f['elegible_para'] == 'B').any():
        conc = 'B'
    else:
        conc = 'C'
    return f, conc


def main():
    N.huella_sello()
    Q.instalar_gancho()
    S.mkdir(parents=True, exist_ok=True)
    d = cargar()
    et = N.etiquetas_37b()
    pri = list(N.priorizadas())
    d['repro'] = reproduccion(pri, et).set_index('config')
    N.a_csv(d['repro'].reset_index(), N.BASE / 'integridad' / 'reproduccion_etiquetas.csv')
    tab = pd.DataFrame([x for c in pri for x in criterios(c, d)])
    N.a_csv(tab, S / 'evaluacion_por_etapa.csv')
    mat = tab.pivot_table(index='config', columns='etapa', values='estado', aggfunc=lambda s: 'CRIT' if (s == 'CRIT').any() else 'ADV' if (s == 'ADV').any() else 'NE' if (s == 'NE').all() else 'OK').reindex(pri)
    mat.insert(0, 'motivo', pd.Series(N.priorizadas()))
    mat['clase'] = d['interp']['clase']
    N.a_csv(mat.reset_index(), S / 'matriz_estados.csv')
    fin, conc = concluir(tab, d, et)
    N.a_csv(fin, S / 'finalistas.csv')
    # Cuáles cambiarían con otros umbrales: la conclusión no debe depender de un solo número
    escenarios = {'Protocolo': {}, 'Estabilidad más exigente (+0,05)': {'est_crit': 0.70, 'p05_crit': 0.55}, 'Estabilidad más laxa (−0,05)': {'est_crit': 0.60, 'p05_crit': 0.45}, 'Estabilidad mucho más laxa (−0,10)': {'est_crit': 0.55, 'p05_crit': 0.40},
                  'Codificación laxa (CRIT 0,30)': {'cod_crit': 0.30}, 'Codificación exigente (CRIT 0,50)': {'cod_crit': 0.50}, 'Población laxa (CRIT 0,55)': {'pob_crit': 0.55}, 'Población exigente (CRIT 0,75)': {'pob_crit': 0.75}, 'Todo laxo': {'est_crit': 0.55, 'p05_crit': 0.40, 'cod_crit': 0.30, 'pob_crit': 0.55}}
    filas = []
    for nombre, cambio in escenarios.items():
        u = {**UMBRALES, **cambio}
        t2 = pd.DataFrame([x for c in pri for x in criterios(c, d, u)])
        f2, c2 = concluir(t2, d, et)
        filas.append({'escenario': nombre, 'cambios': str(cambio), 'n_sin_crit_etapas_1_4': len(elegibles(t2)), 'n_particiones_distintas': len(f2), 'finalistas': ' | '.join(f2['config']) if len(f2) else '', 'clases': ' | '.join(f2['clase']) if len(f2) else '', 'conclusion': c2})
    u = pd.DataFrame(filas)
    N.a_csv(u, S / 'sensibilidad_umbrales.csv')
    # Cribado de la Lista A completa, con lo que existe para todas: estabilidad E3 y sensibilidades de la Fase 37B
    comp = d['comp']
    h = pd.read_csv(N.B37 / 'sensibilidades' / 'comparacion_sensibilidades.csv').pivot_table(index='config_base', columns='sensibilidad', values='ari_ajuste')
    filas = []
    for c in N.lista_a():
        x = comp.loc[c]
        p = h.loc[c] if c in h.index else pd.Series(dtype=float)
        pasa3 = x['E3_entre_media'] >= 0.65 and x['E3_entre_p05'] >= 0.50 and x['E3_fuera_media'] >= 0.65 and x['E3_fuera_p05'] >= 0.50
        pasa_cod = all(pd.isna(p.get(s, np.nan)) or p.get(s) >= 0.40 for s in COD)
        pasa_pob = all(pd.isna(p.get(s, np.nan)) or p.get(s) >= 0.65 for s in ('S-TRA', 'S-CUI', 'S-EJE'))
        filas.append({'config': c, 'en_priorizadas': c in pri, 'k': x['k'], 'algoritmo': x['algoritmo'], 'componentes': x['componentes'], 'pasa_estabilidad_y_asignacion_E3': bool(pasa3), 'pasa_codificacion': bool(pasa_cod), 'pasa_poblacion_sin_impmoda': bool(pasa_pob), 'pasa_todo': bool(pasa3 and pasa_cod and pasa_pob), 'fraccion_eje1': d['t'].loc[c, 'fraccion_eje1'], 'S_SOLAPE': p.get('S-SOLAPE', np.nan), 'S_ORD': p.get('S-ORD', np.nan), 'E3_entre_media': x['E3_entre_media']})
    cr = pd.DataFrame(filas)
    N.a_csv(cr, S / 'cribado_lista_A.csv')
    dec = {'conclusion': conc, 'finalistas': fin['config'].tolist(), 'elegibles_A': fin[fin['elegible_para'] == 'A']['config'].tolist(), 'elegibles_B': fin[fin['elegible_para'] == 'B']['config'].tolist(), 'protocolo_sha256': N.huella_sello()}
    N.a_json(dec, S / 'decision_preliminar_reglas.json')
    print(mat.drop(columns='motivo').to_string())
    print(fin.drop(columns=['motivo_no_elegible']).to_string())
    print(u[['escenario', 'n_sin_crit_etapas_1_4', 'n_particiones_distintas', 'clases', 'conclusion']].to_string())
    print('Lista A: pasan todo', int(cr['pasa_todo'].sum()), '| fuera de priorizadas:', cr[cr['pasa_todo'] & ~cr['en_priorizadas']]['config'].tolist())
    print('CONCLUSIÓN POR REGLAS:', conc)
    N.registrar('seleccion', [('seleccion', 'completa', 0.0, Q.leidos())])


if __name__ == '__main__':
    main()
