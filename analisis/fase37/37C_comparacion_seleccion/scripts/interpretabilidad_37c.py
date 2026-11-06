"""
Fase 37C: interpretabilidad preliminar del conjunto priorizado. Solo las 30 variables generales. Sin MRS, sin nombres de grupos y sin lectura clínica.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/interpretabilidad_37c.py
"""
import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'interpretabilidad'
UMBRAL_EFECTO = 0.06
BLOQUE_EJERCICIO = 'Actividad física'


def numericos(cad):
    """Valores originales por variable: número en cuantitativas (IMC solo observado), código del instrumento en binarias y ordinales, texto en la nominal."""
    defs = {d['variable']: d for d in cad.defs['P1'][0]}
    salida = {}
    for v, d in defs.items():
        s = cad.tabla[v].astype(str)
        if d.get('madre'):
            s = s.where(s != '', d['madre']['estructural'])
        if d['tipo'] == 'cuantitativa':
            salida[v] = pd.to_numeric(s, errors='coerce').to_numpy()
        elif d['tipo'] == 'nominal':
            salida[v] = s.to_numpy()
        else:
            salida[v] = s.map({n: x['codigo'] for n, x in d['niveles'].items()}).astype(float).to_numpy()
    return defs, salida


def eta2(x, l):
    m = ~np.isnan(x)
    x, l = x[m], l[m]
    tot = ((x - x.mean()) ** 2).sum()
    if tot == 0:
        return 0.0
    return float(sum((l == g).sum() * (x[l == g].mean() - x.mean()) ** 2 for g in np.unique(l)) / tot)


def v2(x, l):
    t = pd.crosstab(pd.Series(x), pd.Series(l)).to_numpy().astype(float)
    e = t.sum(axis=1, keepdims=True) * t.sum(axis=0, keepdims=True) / t.sum()
    return float(((t - e) ** 2 / e).sum() / (t.sum() * (min(t.shape) - 1)))


def codificar_para_celdas(defs, vals):
    """Enteros por variable, para las tablas de reconstrucción. Cuantitativas en cuartiles; el IMC sin dato es una categoría más. Sin usar los clústeres."""
    enc = {}
    for v, d in defs.items():
        x = vals[v]
        if d['tipo'] == 'cuantitativa':
            s = pd.Series(x)
            q = pd.qcut(s.rank(method='first'), 4, labels=False) if s.notna().all() else pd.qcut(s, 4, labels=False, duplicates='drop')
            enc[v] = q.fillna(q.max() + 1).astype(int).to_numpy()
        else:
            enc[v] = pd.factorize(x, sort=True)[0]
    return enc


def particiones_cv(n, semilla=(42, 500)):
    rng = np.random.default_rng(list(semilla))
    orden = rng.permutation(n)
    return [orden[i::5] for i in range(5)]


def reconstruir(cod, l, pliegues, k):
    """Asigna a cada celda su clúster mayoritario con 4 pliegues y predice el quinto. Sin impureza ni entropía."""
    pred = np.zeros(len(l), dtype=int)
    m = cod.max() + 1
    for prueba in pliegues:
        en = np.ones(len(l), bool)
        en[prueba] = False
        cuenta = np.zeros((m, k), dtype=int)
        np.add.at(cuenta, (cod[en], l[en]), 1)
        mayor = cuenta.argmax(axis=1)
        vacias = cuenta.sum(axis=1) == 0
        mayor[vacias] = np.bincount(l[en], minlength=k).argmax()
        pred[prueba] = mayor[cod[prueba]]
    return adjusted_rand_score(l, pred)


def clasificar(f):
    if f['n_variables_efecto'] < 3:
        return 'Diferencias muy pequeñas'
    if f['ssb_actividad_fisica'] >= 0.60 or f['fraccion_eje1'] >= 0.80:
        return 'Principalmente gradiente de ejercicio'
    if f['ari_reconstruccion_2'] >= 0.65 or f['ssb_variable_max'] >= 0.40:
        return 'Dominada por pocas variables'
    if f['n_bloques_efecto'] >= 3 and f['n_efectivo_variables'] >= 5:
        return 'Segmentación multivariable'
    return 'Difícil de interpretar'


def main():
    N.huella_sello()
    Q.instalar_gancho()
    cad = N.Cadena()
    defs, vals = numericos(cad)
    bloques = {v: d['seccion'] for v, d in defs.items()}
    enc = codificar_para_celdas(defs, vals)
    variables = list(defs)
    pliegues = particiones_cv(Q.N)
    et = N.etiquetas_37b()
    t37 = N.tabla_37b()
    pri = N.priorizadas()
    resumen, por_var, desc, recon = [], [], [], []
    for c in pri:
        i = N.info_config(c)
        l = et[c].to_numpy()
        k = i['k']
        Z = cad.congelada(i['base'])
        esc = N.leer_json(N.F36 / 'artefactos' / i['base'] / 'escaladores.json')
        ssb = {}
        media = Z.mean()
        for col in Z.columns:
            x = Z[col].to_numpy()
            v = esc[col]['variable']
            ssb[v] = ssb.get(v, 0.0) + sum((l == g).sum() * (x[l == g].mean() - media[col]) ** 2 for g in range(k))
        total = sum(ssb.values())
        share = {v: x / total for v, x in ssb.items()}
        efecto = {}
        for v in variables:
            d = defs[v]
            e = v2(vals[v], l) if d['tipo'] == 'nominal' else eta2(vals[v], l)
            efecto[v] = e
            por_var.append({'config': c, 'variable': v, 'bloque': bloques[v], 'efecto': e, 'medida': 'V²' if d['tipo'] == 'nominal' else 'η²', 'efecto_moderado': e >= UMBRAL_EFECTO, 'parte_ssb': share.get(v, 0.0)})
            for g in range(k):
                m = l == g
                if d['tipo'] == 'nominal':
                    s = pd.Series(vals[v][m]).value_counts(normalize=True)
                    desc.append({'config': c, 'grupo': g, 'n': int(m.sum()), 'variable': v, 'tipo': d['tipo'], 'media': np.nan, 'de': np.nan, 'moda': s.index[0], 'prop_moda': float(s.iloc[0]), 'n_validos': int(m.sum())})
                else:
                    x = vals[v][m].astype(float)
                    x = x[~np.isnan(x)]
                    desc.append({'config': c, 'grupo': g, 'n': int(m.sum()), 'variable': v, 'tipo': d['tipo'], 'media': float(x.mean()), 'de': float(x.std(ddof=1)), 'moda': '', 'prop_moda': np.nan, 'n_validos': len(x)})
        # Reconstrucción con 1 y 2 variables
        unos = sorted(((reconstruir(enc[v], l, pliegues, k), v) for v in variables), reverse=True)
        mejor2, par2 = -1.0, None
        for a_i, a in enumerate(variables):
            for b in variables[a_i + 1:]:
                cod = enc[a] * (enc[b].max() + 1) + enc[b]
                cod = pd.factorize(cod)[0]
                r = reconstruir(cod, l, pliegues, k)
                if r > mejor2:
                    mejor2, par2 = r, (a, b)
        recon.append({'config': c, 'mejor_variable': unos[0][1], 'ari_1': unos[0][0], 'mejor_par': ' + '.join(par2), 'ari_2': mejor2})
        s_bl = {}
        for v, x in share.items():
            s_bl[bloques[v]] = s_bl.get(bloques[v], 0.0) + x
        con_efecto = [v for v in variables if efecto[v] >= UMBRAL_EFECTO]
        top = sorted(share.items(), key=lambda x: -x[1])
        fila = {'config': c, 'motivo': pri[c], 'k': k, 'fraccion_eje1': t37.loc[c, 'fraccion_eje1'], 'ssb_actividad_fisica': s_bl.get(BLOQUE_EJERCICIO, 0.0), 'ssb_variable_max': top[0][1], 'variable_mayor_ssb': top[0][0], 'segunda_variable_ssb': top[1][0], 'parte_segunda_ssb': top[1][1],
                'n_variables_efecto': len(con_efecto), 'variables_efecto': ' | '.join(sorted(con_efecto, key=lambda v: -efecto[v])), 'n_bloques_efecto': len({bloques[v] for v in con_efecto}), 'n_efectivo_variables': 1 / sum(x ** 2 for x in share.values()), 'n_efectivo_bloques': 1 / sum(x ** 2 for x in s_bl.values()),
                'efecto_max': max(efecto.values()), 'ari_reconstruccion_1': unos[0][0], 'mejor_variable_1': unos[0][1], 'ari_reconstruccion_2': mejor2, 'mejor_par_2': ' + '.join(par2), **{f'ssb_{b}': x for b, x in sorted(s_bl.items())}}
        fila['clase'] = clasificar(fila)
        resumen.append(fila)
        print(c, fila['clase'], round(fila['ssb_actividad_fisica'], 2), round(mejor2, 2), flush=True)
    N.a_csv(pd.DataFrame(resumen), S / 'resumen_interpretabilidad.csv')
    N.a_csv(pd.DataFrame(por_var), S / 'efecto_por_variable.csv')
    N.a_csv(pd.DataFrame(desc), S / 'descriptivos_por_grupo.csv')
    N.a_csv(pd.DataFrame(recon), S / 'reconstruccion_pocas_variables.csv')
    N.registrar('interpretabilidad', [('interpretabilidad', 'completa', 0.0, Q.leidos())])


if __name__ == '__main__':
    main()
