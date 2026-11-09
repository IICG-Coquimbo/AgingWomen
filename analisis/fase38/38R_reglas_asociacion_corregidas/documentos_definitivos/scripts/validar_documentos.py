"""
Fase documental 38R/39R: validación independiente de figuras y documentos. Lee los CSV de resultados y lo que quedó dibujado; solo escribe en documentos_definitivos/validacion/.

Uso: python -B validar_documentos.py
"""
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
D38 = AQUI.parent
B38 = D38.parent
RAIZ = B38.parents[2]
B39 = RAIZ / 'analisis' / 'fase39' / '39R_asociaciones_condicionadas_corregidas'
D39 = B39 / 'documentos_definitivos'
FILAS = []


def ok(grupo, nombre, cond, detalle=''):
    FILAS.append({'grupo': grupo, 'verificacion': nombre, 'resultado': 'superada' if cond else 'FALLA', 'detalle': str(detalle)[:400]})


def cerca(a, b, tol=1e-6):
    return abs(float(a) - float(b)) <= tol


def lista_cerca(a, b, tol=1e-6):
    return len(a) == len(b) and all(cerca(x, y, tol) for x, y in zip(a, b))


# ---------------- figuras 38R
RG = json.loads((D38 / 'validacion' / 'registro_figuras_38r.json').read_text(encoding='utf-8'))
R = pd.read_csv(B38 / 'reglas' / 'reglas_principal.csv')
META = json.loads((B38 / 'reglas' / 'resumen_principal.json').read_text(encoding='utf-8'))
NU = pd.read_csv(B38 / 'referencia_nula' / 'nula_principal.csv')
SB = pd.read_csv(B38 / 'estabilidad' / 'submuestras.csv')
DI = pd.read_csv(B38 / 'preparacion' / 'diccionario_items.csv')
RES = pd.read_csv(B38 / 'sensibilidades' / 'resumen_sensibilidades.csv')
LEC = pd.read_csv(B38 / 'sensibilidades' / 'lectura_resumen.csv').set_index('configuracion')
TOP = pd.read_csv(B38 / 'reglas' / 'reglas_no_destacadas_mayor_z.csv')
G = 'Figuras 38R'
_f01 = RG['f01_items_principal.png']
f = {'barras': [b for ax in _f01 for b in ax['barras']], 'etiquetas_y': [x for ax in _f01 for x in ax['etiquetas_y'] + ax['textos']]}
it = DI[DI['item'] != '(sin ítem)']
ok(G, 'f01: 90 barras y sus valores', len(f['barras']) == 90 and sorted(round(b[2]) for b in f['barras']) == sorted(it['participantes'].tolist()), len(f['barras']))
ok(G, 'f01: mismos límites de escala en los dos paneles', len(_f01) == 2)
ok(G, 'f01: 29 variables', it['variable'].nunique() == 29)
ok(G, 'f01: sin ítems de las variables retiradas', not any(x in ' '.join(f['etiquetas_y']).lower() for x in ('previsión', 'diabetes', 'fonasa', 'isapre')))
f = RG['f02_confianza_frente_a_casos.png']
clases = ['2 asociación débil', '3 redundante', '4 compatible con la referencia nula', '6 asociación relativamente más marcada']
for ax, cons, tot in zip(f, ('severo_mrs=SI', 'severo_mrs=NO'), (5319, 4442)):
    esp = [int(((R['consecuente'] == cons) & (R['clase'] == k)).sum()) for k in clases]
    ok(G, f'f02: puntos por clase {cons}', ax['puntos'] == esp and sum(esp) == tot, (ax['puntos'], esp))
ok(G, 'f02: total 9.761 reglas', sum(sum(a['puntos']) for a in f) == 9761)
f = RG['f03_referencia_nula.png']
ok(G, 'f03: 1.000 permutaciones', round(sum(b[3] for b in f[0]['barras'])) == 1000 and round(sum(b[3] for b in f[1]['barras'])) == 1000)
vl = [x[0][0] for x in f[0]['lineas']]
ok(G, 'f03: máximo z y p95', lista_cerca(vl, [R['z'].abs().max(), META['nula_p95_max_z']]), vl)
vl = [x[0][0] for x in f[1]['lineas']]
ok(G, 'f03: 971 marcadas y media 543,56', lista_cerca(vl, [971, 543.564]), vl)
f = RG['f04_estabilidad.png']
s6 = R[R['clase'].str.startswith('6')].iloc[0]
ok(G, 'f04: 971 marcadas en el título', '971' in f[0]['titulo'])
ok(G, 'f04: línea de la clase 6', cerca(f[0]['lineas'][0][0][0], s6['reaparece_marcada']))
ok(G, 'f04: 200 submuestras', round(sum(b[3] for b in f[1]['barras'])) == 400)
f = RG['f05_exceso_frente_a_nula.png'][0]
filas = [('principal', 971, B38 / 'referencia_nula' / 'nula_principal.csv')] + [(r.configuracion, r.marcadas, B38 / 'sensibilidades' / 'nula' / f'nula_{r.configuracion}.csv') for r in RES.itertuples()]
ok(G, 'f05: 16 configuraciones', len(f['lineas']) == 48 and len(filas) == 16, len(f['lineas']))
for i, (c, m, a) in enumerate(filas):
    nl = pd.read_csv(a)['reglas_marcadas']
    ok(G, f'f05: {c}', cerca(f['lineas'][3 * i + 2][0][0], m / nl.mean()) and f['etiquetas_y'][i].startswith(f'{c} (n = '))
f = RG['f06_lectura_sensibilidades.png'][0]
cats = ['se mantiene', 'se debilita', 'cambia de dirección', 'desaparece por falta de casos', 'no evaluable']
L6 = LEC.reindex(columns=cats, fill_value=0)
anch = np.array([b[2] for b in f['barras']]).reshape(len(cats), len(L6))
ok(G, 'f06: anchos iguales a la lectura', np.allclose(anch.T, L6.to_numpy()))
ok(G, 'f06: cada fila suma 971', (L6.sum(axis=1) == 971).all() and '971' in f['ejex'])
f = RG['f07_reglas_mayor_z.png']
for ax, cons in zip(f, ('severo_mrs=SI', 'severo_mrs=NO')):
    t = TOP[TOP['consecuente'] == cons].reset_index(drop=True)
    conf = [x[0][0] for x in ax['lineas'] if len(x[0]) == 1 and x[1][0] == x[1][0]]
    ok(G, f'f07: 10 reglas {cons}', len(t) == 10 and lista_cerca(conf[:10], t['confianza'].tolist()), len(conf))
ok(G, 'f07: una sola regla de clase 6', int(TOP['clase'].str.startswith('6').sum()) == 1)
f = RG['f08_umbrales.png']
ok(G, 'f08: reglas evaluadas', lista_cerca([b[3] for b in f[0]['barras']], [23025, 9761, 4938]))
ok(G, 'f08: marcadas', lista_cerca([b[3] for b in f[1]['barras'][:3]], [4519, 971, 278]))
for nombre in ('f01_items_principal', 'f02_confianza_frente_a_casos', 'f03_referencia_nula', 'f04_estabilidad', 'f05_exceso_frente_a_nula', 'f06_lectura_sensibilidades', 'f07_reglas_mayor_z', 'f08_umbrales'):
    ok(G, f'{nombre}: archivo', (D38 / 'figuras' / f'{nombre}.png').stat().st_size > 10000)

# ---------------- figuras 39R
RG = json.loads((D39 / 'validacion' / 'registro_figuras_39r.json').read_text(encoding='utf-8'))
G = 'Figuras 39R'
D = pd.read_csv(B39 / 'preparacion' / 'diccionario_estratos.csv')
RE = pd.read_csv(B39 / 'reglas' / 'resumen_estratos.csv')
AB = pd.read_csv(B39 / 'ab1' / 'resumen_grupos_A_B1.csv')
DIMS = ('trabajo', 'pareja', 'ejercicio', 'cuidado')
Hs = {g: pd.read_csv(B39 / 'comparacion' / f'comparacion_{g}.csv') for g in DIMS}
NH = {g: pd.read_csv(B39 / 'comparacion' / f'nula_comparacion_{g}.csv') for g in DIMS}
LC = pd.read_csv(B39 / 'sensibilidades' / 'lectura_comparaciones_principal.csv')
H = pd.read_csv(B39.parent / '39_asociaciones_condicionadas' / 'preparacion' / 'diccionario_estratos.csv')
col = ['grupo', 'estrato', 'participantes', 'severas', 'no_severas', 'frecuencia_basal_si', 'ic_basal_inf', 'ic_basal_sup']
ok(G, 'f01: datos idénticos a los que dibujó la figura histórica', D[col].equals(H[col]))
f = RG['f01_tamanos_basales.png'][0]
ok(G, 'f01: 17 puntos con las basales', lista_cerca([p[1] for p in f['puntos'][-1]], D['frecuencia_basal_si'].tolist()), len(f['puntos'][-1]))
f = RG['f02_marcadas_frente_a_nula.png'][0]
t = pd.concat([RE, AB], ignore_index=True)
ok(G, 'f02: marcadas', lista_cerca([b[3] for b in f['barras'][:17]], t['marcadas'].tolist()))
ok(G, 'f02: media nula', lista_cerca([b[3] for b in f['barras'][17:]], t['nula_media_marcadas'].tolist()))
ok(G, 'f02: 9 estratos suman 9.085 marcadas y 47.912 reglas', int(RE['marcadas'].sum()) == 9085 and int(RE['reglas'].sum()) == 47912)
f = RG['f03_heterogeneidad_frente_a_nula.png']
for ax, g in zip(f, DIMS):
    ok(G, f'f03: {g}', lista_cerca([x[0][0] for x in ax['lineas']], [Hs[g]['Q'].max(), NH[g]['max_Q'].quantile(0.95)]) and round(sum(b[3] for b in ax['barras'])) == 1000)
    ok(G, f'f03: {g} queda bajo el p95 nulo', Hs[g]['Q'].max() < NH[g]['max_Q'].quantile(0.95))
f = RG['f04_comparaciones_mayor_Q.png']
for ax, g in zip(f, DIMS):
    tt = Hs[g][~Hs[g]['redundante']].sort_values('Q', ascending=False).head(6).iloc[::-1]
    p_txt = [x.split('p ajust. ')[1].rstrip(')') for x in ax['etiquetas_y']]
    ok(G, f'f04: {g} p ajustados', p_txt == [f'{v:.2f}'.replace('.', ',') for v in tt['p_ajustado_dimension']], p_txt)
    ok(G, f'f04: {g} ninguna supera', not Hs[g]['supera_nula_dimension'].any())
f = RG['f05_sensibilidades_comparaciones.png'][0]
tt = LC.groupby(['sensibilidad', 'lectura']).size().unstack(fill_value=0).reindex(columns=['se mantiene', 'se debilita', 'cambia de dirección', 'no evaluable'], fill_value=0)
ok(G, 'f05: anchos iguales a la lectura', np.allclose(np.array([b[2] for b in f['barras']]).reshape(4, len(tt)).T, tt.to_numpy()))
f = RG['f06_estabilidad_comparaciones.png'][0]
for serie, g in zip(f['puntos'], DIMS):
    tt = Hs[g][Hs[g]['marcada'] & ~Hs[g]['redundante']]
    ok(G, f'f06: {g}', len(serie) == len(tt) and lista_cerca([p[1] for p in serie], tt['reaparece_marcada'].tolist()), len(serie))

# ---------------- indicadores
G = 'Coherencia 38R'
inf38 = (B38 / 'informes' / 'informe_comparativo_38R.md').read_text(encoding='utf-8')
cl = R['clase'].value_counts()
E38 = pd.read_csv(B38 / 'estabilidad' / 'estabilidad_reglas.csv')
NUP = ((NU['reglas_marcadas'] >= 971).sum() + 1) / (len(NU) + 1)
Ctab = [('Reglas', len(R), 9761, '9.761'), ('Hacia severos', (R['consecuente'] == 'severo_mrs=SI').sum(), 5319, '5.319'), ('Hacia no severos', (R['consecuente'] == 'severo_mrs=NO').sum(), 4442, '4.442'),
        ('Marcadas', R['marcada'].sum(), 971, '971'), ('Marcadas no redundantes', (R['marcada'] & ~R['redundante'].fillna(False).astype(bool)).sum(), 184, '184'),
        ('Nula media', NU['reglas_marcadas'].mean(), 543.564, '543,56'), ('Nula p95', NU['reglas_marcadas'].quantile(0.95), 811.25, '811,25'), ('p exceso', NUP, 0.012987, '0,0130'),
        ('Clase 2', cl['2 asociación débil'], 8790, '8.790'), ('Clase 3', cl['3 redundante'], 787, '787'), ('Clase 4', cl['4 compatible con la referencia nula'], 183, '183'), ('Clase 6', cl['6 asociación relativamente más marcada'], 1, None),
        ('Estables', E38['estable'].sum(), 480, '480'), ('Supera la nula', R['supera_nula'].sum(), 1, None)]
for nom, v, esp, txt in Ctab:
    ok(G, f'{nom}: {v}', cerca(v, esp, 1e-3) and (txt is None or txt in inf38), esp)
ok(G, 'Regla clase 6: n, confianza, p', s6['n_antecedente'] == 57 and s6['n_conjunto'] == 46 and cerca(s6['confianza'], 46 / 57) and cerca(s6['p_ajustado_busqueda'], 0.033, 0.0005))
ROB = pd.read_csv(B38 / 'comparacion' / 'evaluacion_robustez.csv').iloc[0]
ok(G, 'Regla clase 6 no robusta (4 de 8)', (not bool(ROB['robusta'])) and ROB['evaluables'] == 8 and ROB['se_mantiene'] == 4 and ROB['supera_nula_en'] == 1)
S2 = pd.read_csv(B38 / 'sensibilidades' / 'superan_nula_sensibilidades.csv')
ok(G, 'S2b: dos reglas superan su nula', (S2['configuracion'] == 'S2b').sum() == 2)
sens_esp = {'S1': (7542, 889, 0), 'S2a': (9269, 853, 1), 'S2b': (13639, 1386, 2), 'S3-bajo': (23025, 4519, 0), 'S3-alto': (4938, 278, 0), 'S4-1': (77, 3, 0), 'S4-2': (1401, 91, 0), 'S5': (6955, 657, 0), 'S6': (7072, 716, 0),
            'S7a': (10435, 2700, 0), 'S7a-309': (10178, 2568, 0), 'S7b': (11315, 3249, 1), 'S7b-251': (10747, 2942, 1), 'S8a': (9808, 2359, 0), 'S8b': (10798, 2855, 0)}
for r in RES.itertuples():
    ok(G, f'Sensibilidad {r.configuracion}', (r.reglas, r.marcadas, r.supera_nula) == sens_esp[r.configuracion], (r.reglas, r.marcadas, r.supera_nula))

G = 'Coherencia 39R'
inf39 = (B39 / 'informes' / 'informe_comparativo_39R.md').read_text(encoding='utf-8')
CONC = json.loads((B39 / 'resultados' / 'conclusion_39R.json').read_text(encoding='utf-8'))
T = pd.read_csv(B39 / 'reglas' / 'reglas_todos_estratos.csv', usecols=['consecuente', 'marcada', 'redundante', 'clase', 'supera_nula_estrato', 'p_ajustado_estrato'])
ctab = [('Reglas', len(T), 47912, '47.912'), ('Severos', (T['consecuente'] == 'severo_mrs=SI').sum(), 25807, '25.807'), ('No severos', (T['consecuente'] == 'severo_mrs=NO').sum(), 22105, '22.105'), ('Marcadas', T['marcada'].sum(), 9085, '9.085'),
        ('Marcadas no redundantes', (T['marcada'] & ~T['redundante'].fillna(False).astype(bool)).sum(), 1998, '1.998'), ('Comparables (suma de las cuatro dimensiones del informe)', sum(len(h) for h in Hs.values()), 1348 + 1129 + 363 + 1496, None),
        ('Superan la nula del estrato', T['supera_nula_estrato'].sum(), 0, None), ('Menor p estrato', T['p_ajustado_estrato'].min(), 0.054945, '0,0549')]
for nom, v, esp, txt in ctab:
    ok(G, f'{nom}: {v}', cerca(v, esp, 1e-3) and (txt is None or txt in inf39), esp)
for g, c_, m_ in zip(DIMS, (1348, 1129, 363, 1496), (569, 435, 234, 582)):
    ok(G, f'{g}: comparables y marcadas', len(Hs[g]) == c_ and int(Hs[g]['marcada'].sum()) == m_ and not Hs[g]['supera_nula_dimension'].any() and not Hs[g]['supera_nula_conjunta'].any())
ok(G, 'Comparables por dimensión presentes en el informe comparativo', all(x in inf39 for x in ('1.348', '1.129', '363', '1.496')))
ok(G, 'Conclusión C', CONC['resultado'] == 'C' and CONC['diferencias_consistentes'] == 0 and CONC['reglas_superan_nula_estrato'] == 0)
SU = pd.read_csv(B39 / 'sensibilidades' / 'reglas_superan_nula_sensibilidades.csv')
a = SU[SU['sensibilidad'] == 'S3-alto'].iloc[0]
ok(G, 'S3-alto: p 0,04995, redundante, no supera la conjunta', cerca(a['p_ajustado_estrato'], 0.04995, 1e-4) and bool(a['redundante']) and a['p_ajustado_conjunto'] >= 0.05)
s3b = pd.read_csv(B39 / 'sensibilidades' / 'comparacion' / 'S3-bajo' / 'comparacion_ejercicio.csv')
s3b = s3b[s3b['supera_nula_dimension']].iloc[0]
ok(G, 'S3-bajo: p conjunto 0,048 y no comparable en la principal', cerca(s3b['p_ajustado_conjunto'], 0.048, 0.001) and s3b['nA_3_o_mas_dias'] < 20 and s3b['antecedente'] not in set(Hs['ejercicio']['antecedente']), (s3b['nA_3_o_mas_dias'], s3b['p_ajustado_conjunto']))
b = SU[SU['sensibilidad'] == 'S7b'].iloc[0]
ok(G, 'S7b: regla de aeróbico, agua y sobrecarga', b['antecedente'].startswith('aerobico=') and 'agua=' in b['antecedente'] and 'sobrecarga=' in b['antecedente'] and b['n_antecedente'] == 34)
SR = pd.read_csv(B39 / 'sensibilidades' / 'resumen_sensibilidades_estratos.csv').groupby('sensibilidad')[['reglas', 'marcadas', 'supera_nula_estrato']].sum()
esp39 = {'S1': (37913, 7903, 1), 'S2a': (45275, 8162, 0), 'S3-bajo': (70715, 16852, 0), 'S3-alto': (25091, 3152, 1), 'S4-1': (619, 63, 3), 'S4-2': (9918, 1497, 0), 'S5': (33833, 6523, 0), 'S6': (34624, 6647, 1), 'S7a': (10178, 2568, 0), 'S7b': (9785, 2666, 1)}
for s, x in esp39.items():
    ok(G, f'Sensibilidad {s}', tuple(int(v) for v in SR.loc[s]) == x, tuple(SR.loc[s]))

# ---------------- documentos
ANTIGUAS = {'38R': [r'12\.201', r'1\.119', r'649,98', r'(?<![,\d])650\b', r'6\.275', r'5\.926', r'52\.685', r'12\.325', r'11\.082', r'94 ítems', r'31 variables', r'13 sensibilidades', r'970,05', r'1\.595', r'16\.126', r'27\.767', r'5\.389'],
            '39R': [r'59\.672', r'10\.739', r'4\.873', r'30\.600', r'29\.072', r'2\.129', r'5\.525', r'94 ítems', r'31 variables', r'12\.201', r'1\.119']}
VETADAS = re.compile(r'previsi[oó]n|usa_medicamentos_diabetes|med_diabetes|fonasa|isapre|diabetes|ffaa', re.I)
CAUSAL = re.compile(r'\b(causa[n]? (los|más|menos) síntomas|se recomienda (hacer|evitar|consumir)|factor de riesgo|previene|protege contra|validad[oa] clínicamente(?! ni)|clínicamente validad[oa]s?)', re.I)
NEG_CLIN = re.compile(r'(no|ni|sin)\b[^.]{0,80}(validad[oa] clínicamente|clínicamente validad[oa]s?)', re.I)
VACIOS = re.compile(r'\b(nan|NaN|None|inf)\b|\{[a-z_]+\}')
OBLIG = ('sintético', 'validación externa', 'exploratorio', 'Versión correctiva')
for fase, D_, proto in (('38R', D38, '01_protocolo_38R'), ('39R', D39, '02_protocolo_39R')):
    G = f'Word {fase}'
    fuentes = sorted((D_ / 'fuentes').glob('*.md'))
    nombres = {p.stem for p in fuentes}
    salida_vetadas = []
    numeros = {re.match(r'\d+', x).group() for x in nombres}
    for md in fuentes:
        t = md.read_text(encoding='utf-8')
        dx = D_ / 'word' / f'{md.stem}.docx'
        ok(G, f'{md.stem}: Word existe', dx.exists())
        with zipfile.ZipFile(dx) as z:
            ok(G, f'{md.stem}: ZIP íntegro', z.testzip() is None)
            xml = z.read('word/document.xml')
            raiz = ET.fromstring(xml)
            ok(G, f'{md.stem}: documento XML válido', raiz is not None)
            media = [x for x in z.namelist() if x.startswith('word/media/')]
            rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
            txt = re.sub(r'<[^>]+>', ' ', xml.decode('utf-8'))
        imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', t)
        ok(G, f'{md.stem}: imágenes de la fuente existen', all((md.parent / i).resolve().exists() for i in imgs))
        ok(G, f'{md.stem}: imágenes insertadas', len(media) == len(set(imgs)) and rels.count('relationships/image') == len(set(imgs)) and xml.decode('utf-8').count('<a:blip') == len(imgs), (len(media), len(set(imgs))))
        ok(G, f'{md.stem}: sin valores vacíos', md.stem == proto or not VACIOS.findall(txt), VACIOS.findall(txt)[:4])
        filas_tabla = xml.decode('utf-8').count('<w:tr>') + xml.decode('utf-8').count('<w:tr ')
        fmd = [x for x in t.split('\n') if x.startswith('|')]
        sep = sum(1 for x in fmd if re.match(r'^\|[-:| ]+\|$', x))
        ok(G, f'{md.stem}: filas de tablas iguales en fuente y Word', filas_tabla == len(fmd) - sep, (filas_tabla, len(fmd) - sep))
        if md.stem != proto:
            cuerpo = re.sub(r'^<!-- apaisada -->\s*', '', t).split('\n', 2)[2]
            for pat in ANTIGUAS[fase]:
                m = re.findall(pat, cuerpo)
                ok(G, f'{md.stem}: sin cifra antigua {pat}', not m, m[:2])
            for w in OBLIG:
                ok(G, f'{md.stem}: contiene «{w}»', (w in t) if md.stem not in ('06_equivalencia_apriori_fpgrowth', '13_figuras_tablas', '16_figuras_tablas', '06_preparacion_matrices_condicionadas', '17_nota_fase_39R', '20_nota_logica_tablero') or w == 'Versión correctiva' else True)
            for lin in cuerpo.split('\n'):
                if VETADAS.search(lin):
                    salida_vetadas.append((md.stem, lin[:220]))
            clin = [m.group(0) for m in CAUSAL.finditer(cuerpo) if not NEG_CLIN.search(cuerpo[max(0, m.start() - 90):m.end()])]
            ok(G, f'{md.stem}: sin lenguaje causal ni clínico afirmativo', not clin, clin[:3])
            ref = {x.zfill(2) for x in re.findall(r'informes? (\d{1,2})\b', cuerpo)}
            ok(G, f'{md.stem}: referencias a informes existen', ref <= numeros, sorted(ref))
        # los pies de figura numerados coinciden con su archivo
        for pie, ruta in re.findall(r'!\[Figura (\d+)[^\]]*\]\(\.\./figuras/f0(\d)', t):
            ok(G, f'{md.stem}: figura {pie} corresponde a f0{ruta}', pie == ruta)
    # columnas, encabezados, jerarquía y referencias, en la fuente y en el Word
    for md in fuentes:
        t = md.read_text(encoding='utf-8')
        lineas = t.split('\n')
        i = 0
        bloques = []
        while i < len(lineas):
            if lineas[i].startswith('|'):
                j = i
                while j < len(lineas) and lineas[j].startswith('|'):
                    j += 1
                bloques.append(lineas[i:j])
                i = j
            else:
                i += 1
        celdas = lambda x: re.split(r'(?<!\\)\|', x.strip()[1:-1])
        desiguales = [b[0][:80] for b in bloques if len({len(celdas(x)) for x in b}) != 1]
        ok(G, f'{md.stem}: misma cantidad de columnas en cada fila de cada tabla (fuente)', not desiguales, desiguales[:3])
        W_ = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with zipfile.ZipFile(D_ / 'word' / f'{md.stem}.docx') as z:
            raiz = ET.fromstring(z.read('word/document.xml'))
            numer = z.read('word/numbering.xml').decode('utf-8') if 'word/numbering.xml' in z.namelist() else ''
        tablas_w = list(raiz.iter(W_ + 'tbl'))
        ok(G, f'{md.stem}: tantas tablas en Word como en la fuente', len(tablas_w) == len(bloques), (len(tablas_w), len(bloques)))
        distintas, texto_dist = [], []
        for b, tw in zip(bloques, tablas_w):
            filas_w = [[''.join(x.text or '' for x in c.iter(W_ + 't')).strip() for c in f_.findall(W_ + 'tc')] for f_ in tw.findall(W_ + 'tr')]
            filas_md = [celdas(x) for x in b if not re.match(r'^\|[-:| ]+\|$', x)]
            if len({len(x) for x in filas_w}) != 1 or len(filas_w[0]) != len(filas_md[0]) or len(tw.find(W_ + 'tblGrid').findall(W_ + 'gridCol')) != len(filas_md[0]):
                distintas.append(b[0][:80])
            limpia = lambda x: x.strip().replace('`', '').replace('**', '').replace('\\|', '|').replace('\u00a0', ' ')
            for fm, fw in zip(filas_md, filas_w):
                if [limpia(x) for x in fm] != [x.replace('\u00a0', ' ') for x in fw]:
                    texto_dist.append(fm[0][:50])
        ok(G, f'{md.stem}: columnas iguales en filas, cuadrícula y fuente (Word)', not distintas, distintas[:3])
        ok(G, f'{md.stem}: el texto de cada celda del Word es el de su columna en la fuente', not texto_dist, texto_dist[:3])
        ind_md = sum(1 for x in lineas if re.match(r'^\s{2,}- ', x))
        ind_w = sum(1 for x in raiz.iter(W_ + 'ilvl') if x.get(W_ + 'val') == '1')
        ok(G, f'{md.stem}: viñetas anidadas conservan su nivel', ind_md == ind_w, (ind_md, ind_w))
        xml_txt = ' '.join(x.text or '' for x in raiz.iter(W_ + 't'))
        ok(G, f'{md.stem}: porcentajes con espacio indivisible', md.stem == proto or not re.search(r'\d %', xml_txt), re.findall(r'.{12}\d %', xml_txt)[:3])
        ok(G, f'{md.stem}: sin |z| mal representado', '/z/' not in t)
        ok(G, f'{md.stem}: sin expresión ambigua «6 supera»', '6 supera' not in t)
        ok(G, f'{md.stem}: sin «informe 17» inexistente', fase == '38R' or 'informe 17' not in t)
        ok(G, f'{md.stem}: sin referencias ambiguas a una tabla numerada', md.stem == proto or not re.search(r'\bTabla \d', t), re.findall(r'.{20}Tabla \d', t)[:2])
        for pie, _archivo in re.findall(r'!\[([^\]]*)\]\((\.\./figuras/[^)]+)\)', t):
            ok(G, f'{md.stem}: pie de figura descriptivo: {pie[:45]}', pie.startswith('Figura ') and ' ' in pie and not re.match(r'^f0\d', pie))
    ok(G, 'Variables retiradas: solo en el motivo de la corrección', all(('Exclus' in l or 'exclus' in l or 'retirada' in l) for _, l in salida_vetadas), salida_vetadas[:8])
    pd.DataFrame(salida_vetadas, columns=['documento', 'linea']).to_csv(D_ / 'validacion' / 'menciones_variables_retiradas.csv', index=False, encoding='utf-8')
    usados = set()
    for md in fuentes:
        usados |= {Path(i).name for i in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md.read_text(encoding='utf-8'))}
    ok(G, 'Todas las figuras están insertadas en algún documento', usados == {p.name for p in (D_ / 'figuras').glob('*.png')}, usados ^ {p.name for p in (D_ / 'figuras').glob('*.png')})

t12 = (D38 / 'fuentes' / '12_sensibilidades.md').read_text(encoding='utf-8')
t14 = (D39 / 'fuentes' / '14_sensibilidades.md').read_text(encoding='utf-8')
G = 'Explicaciones'
for frase in ('dos reglas superan su referencia nula', 'no cumple los criterios de robustez', 'S7a (287)', 'S7b (239)', 'S7a-309', 'S7b-251', 'no son evidencia confirmatoria'):
    ok(G, f'38R 12: «{frase}»', frase.lower() in t12.lower())
for frase in ('0,04995', 'no supera la referencia nula conjunta', 'no cumple la comparabilidad mínima', '0,048', 'no es un hallazgo robusto ni una recomendación clínica', 'Estratos pequeños', 'no son evidencia confirmatoria'):
    ok(G, f'39R 14: «{frase}»', frase.lower() in t14.lower())

# ---------------- correspondencia y contenido corregido
G = 'Tabla 39R-11'
t11 = (D39 / 'fuentes' / '11_referencias_nulas_estrato.md').read_text(encoding='utf-8').split('\n')
cab_i = next(i for i, x in enumerate(t11) if x.startswith('| Dimensión | Estrato | Antecedentes evaluados'))
cab11 = [x.strip().replace('\\|', '|') for x in re.split(r'(?<!\\)\|', t11[cab_i].strip()[1:-1])]
esperada = ['Dimensión', 'Estrato', 'Antecedentes evaluados', 'Marcadas', 'Nula: media', 'Nula: p95', 'p de exceso', 'Máximo |z|: p95 nulo', 'Menor p ajustado', 'Superan la nula del estrato']
ok(G, 'Diez encabezados, en orden, con Máximo |z| en una sola columna', cab11 == esperada, cab11)
T11 = pd.read_csv(B39 / 'reglas' / 'reglas_todos_estratos.csv', usecols=['dimension', 'estrato', 'p_ajustado_estrato'])
filas11 = [[x.strip() for x in re.split(r'(?<!\\)\|', l.strip()[1:-1])] for l in t11[cab_i + 2:cab_i + 2 + len(RE)]]
num = lambda x: float(x.replace('.', '').replace(',', '.'))
for r, f_ in zip(RE.itertuples(), filas11):
    pmin = T11[(T11['dimension'] == r.dimension) & (T11['estrato'] == r.estrato)]['p_ajustado_estrato'].min()
    ok(G, f'{r.estrato}: valores bajo su encabezado', len(f_) == 10 and int(f_[2].replace('.', '')) == r.antecedentes_evaluados and int(f_[3].replace('.', '')) == r.marcadas and cerca(num(f_[7]), round(r.nula_p95_max_z, 2), 0.006) and cerca(num(f_[8]), pmin, 0.0006), f_)

G = 'Tablas 38R-03 y 38R-04'
_MP = pd.read_csv(B38 / 'preparacion' / 'matriz_transaccional_principal.csv', dtype={'participante_id': str}).set_index('participante_id')
_MS2 = pd.read_csv(B38 / 'preparacion' / 'sensibilidades' / 'matriz_S2a.csv', dtype={'participante_id': str}).set_index('participante_id')
_MS1 = pd.read_csv(B38 / 'preparacion' / 'sensibilidades' / 'matriz_S1.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(_MP.index)
t03 = (D38 / 'fuentes' / '03_diccionario_variables_categorias.md').read_text(encoding='utf-8')
t04 = (D38 / 'fuentes' / '04_agrupacion_categorias_escasas.md').read_text(encoding='utf-8')


def bloque_tras(texto, titulo):
    ls = texto[texto.index(titulo):].split('\n')
    i = next(k for k, x in enumerate(ls) if x.startswith('|'))
    j = i
    while ls[j].startswith('|'):
        j += 1
    return [[c.strip() for c in re.split(r'(?<!\\)\|', x.strip()[1:-1])] for x in ls[i + 2:j]]


obs = bloque_tras(t03, '# Variables observadas e imputadas')
ok(G, '03: 29 variables observadas/imputadas', len(obs) == 29, len(obs))
eti = it.groupby('etiqueta', sort=False)['item'].apply(list)
mal = []
for f_ in obs:
    its = [i_ for i_ in eti[f_[0]] if i_ in _MP.columns]
    p_ = int(_MP[its].any(axis=1).sum())
    s_ = int(_MS1[[i_ for i_ in its if i_ in _MS1.columns]].any(axis=1).sum())
    if (p_, s_, p_ - s_) != (int(f_[5]), int(f_[6]), int(f_[7])) or int(f_[7]) != int(f_[2]) + int(f_[3]) + int(f_[4]):
        mal.append(f_[0])
ok(G, '03: columnas de ítem y pérdida en S1 iguales a las matrices; pérdida = imputadas + deducidas + heredadas', not mal, mal)
ok(G, '03: variables con imputaciones heredadas', sum(1 for f_ in obs if f_[4] != '0') == 4)
res = bloque_tras(t03, '# Variables reservadas para sensibilidades')
ok(G, '03: cuatro reservadas con sus cifras', [f_[2] for f_ in res] == ['267 / 262 / 0', '271 / 16 / 22', '277 / 10 / 22', '239 / 12 / 21'], [f_[2] for f_ in res])
for cfg, pref, f_, total in (('S8b', 'imc=', res[0], 267), ('S7a', 'lugar_comprensivo=', res[1], 287), ('S7a', 'estres_laboral=', res[2], 287), ('S7b', 'sobrecarga=', res[3], 239)):
    M_ = pd.read_csv(B38 / 'preparacion' / 'sensibilidades' / f'matriz_{cfg}.csv')
    cc = [c for c in M_.columns if c.startswith(pref)]
    nums = [int(x) for x in re.findall(r'\((\d+)\)', f_[4])]
    ok(G, f'03: ítems de {pref[:-1]} iguales a la matriz {cfg}', nums == [int(M_[c].sum()) for c in cc] and sum(nums) == total, nums)
dist = bloque_tras(t03, '# Distribución de categorías originales')
ok(G, '03: distribución de 29 variables, cada una suma como máximo 529', len(dist) == 29 and all(sum(int(x.replace('.', '')) for x in re.findall(r'\(([\d.]+)\)', f_[1])) == 529 for f_ in dist), [f_[0] for f_ in dist if sum(int(x.replace('.', '')) for x in re.findall(r'\(([\d.]+)\)', f_[1])) != 529])
adv = bloque_tras(t03, '# Variables\n')
ok(G, '03: advertencias presentes', len(adv) == 29 and sum(1 for f_ in adv if f_[5] != '—') == 6, sum(1 for f_ in adv if f_[5] != '—'))
for frase in ('Imputaciones heredadas de preguntas madre', '# Advertencias metodológicas'):
    ok(G, f'03: «{frase}»', frase in t03)
esc = bloque_tras(t04, '# Categorías originales con menos del 5 %')
cero = bloque_tras(t04, '**Categorías con n = 0**')
ok(G, '04: 27 categorías escasas y 10 con n = 0', len(esc) == 27 and len(cero) == 10, (len(esc), len(cero)))
ok(G, '04: n = 0 todas con cero', all(f_[2] == '0' and 'Ninguna participante' in f_[3] for f_ in cero))
ok(G, '04: n entre 1 y 26 y porcentaje sobre 529', all(1 <= int(f_[2]) <= 26 and f_[3] == f'{100 * int(f_[2]) / 529:.1f} %'.replace('.', ',') for f_ in esc))
ok(G, '04: filas R3 con nombres legibles', 'Sin ítem: compro comida preparada' in t04 and 'Sin ítem: otro' in t04 and '«COMPRO»' not in t04)
ok(G, '03 y 04: variables retiradas nunca como vigentes', not re.search(r'previsi[oó]n|FONASA|ISAPRE|diabetes', '\n'.join(x_ for x_ in t04.splitlines() if not x_.startswith('> ')), re.I) and all(not re.search(r'previsi[oó]n|diabetes', ' '.join(f_), re.I) for f_ in obs + dist + res))

G = 'Textos corregidos'
t16 = (D38 / 'fuentes' / '16_informe_cierre_38R.md').read_text(encoding='utf-8')
ok(G, '38R-16: precisa S3-bajo', 'se mantiene, pero no supera su referencia nula' in t16 and 'ni con otros umbrales' not in t16)
ok(G, '38R-12: clase sin ambigüedad', 'no es la clase 6 del protocolo' in t12)
ok(G, '38R-17: en pasado', 'Conviene' not in (D38 / 'fuentes' / '17_nota_fase_39R.md').read_text(encoding='utf-8'))
t19 = (D39 / 'fuentes' / '19_informe_cierre_39R.md').read_text(encoding='utf-8')
t20 = (D39 / 'fuentes' / '20_nota_logica_tablero.md').read_text(encoding='utf-8')
for frase in ('Clasificación de severidad utilizada en el análisis estadístico', 'Información MRS que presenta actualmente la plataforma', 'Aspectos de visualización pendientes de validación clínica', 'Resultado histórico no verificable', 'Puntaje MRS: X de 44', 'Sin categoría de severidad'):
    ok(G, f'39R-20: «{frase}»', frase in t20)
for texto, nom in ((t19, '39R-19'), (t20, '39R-20')):
    ok(G, f'{nom}: sin afirmar que la plataforma muestra una categoría', not re.search(r'categoría «Severa»|su categoría de severidad|cortes de severidad confirmados', texto))
ok(G, '39R-19: distingue los tres planos', all(x in t19 for x in ('Clasificación usada en el análisis estadístico', 'Información MRS que presenta hoy la plataforma', 'Pendiente de validación clínica')))
for texto, nom in ((t14, '39R-14'), (t19, '39R-19')):
    for fase_, sens_, n_ in (('38R', 'S7a', '287'), ('38R', 'S7a-309', '309'), ('38R', 'S7b', '239'), ('38R', 'S7b-251', '251'), ('39R', 'S7a', '309'), ('39R', 'S7b', '251')):
        ok(G, f'{nom}: población {fase_} {sens_} = {n_}', re.search(rf'^\| {fase_} \| {sens_}( \(ampliada\))? \|[^\n]*\| {n_} \|$', texto, re.M) is not None)

G = 'Protocolos'
for md_, orig, sello_, cuerpo_ in ((D38 / 'fuentes' / '01_protocolo_38R.md', B38 / 'protocolo' / '01_protocolo_38R.md', B38 / 'protocolo' / 'sello_protocolo.json', False), (D39 / 'fuentes' / '02_protocolo_39R.md', B39 / 'protocolo' / '01_protocolo_39R.md', B39 / 'protocolo' / 'sello_protocolo.json', True)):
    o_ = orig.read_text(encoding='utf-8')
    o_ = o_.split('\n', 1)[1] if cuerpo_ else o_
    t_ = md_.read_text(encoding='utf-8')
    h_ = hashlib.sha256(orig.read_bytes()).hexdigest()
    ok(G, f'{md_.stem}: contiene íntegro el texto sellado', o_.strip() in t_)
    ok(G, f'{md_.stem}: la huella del archivo coincide con el sello', h_ == json.loads(sello_.read_text(encoding='utf-8'))['sha256'] and h_ in t_, h_)
    ok(G, f'{md_.stem}: nota de versión fuera del texto sellado', t_.startswith('> **Nota de versión (fuera del texto sellado).**'))

G = 'Fuente efectiva de las figuras'
for carp, reg_, ancho_px, dpi_ in ((D38, 'registro_figuras_38r.json', None, 170), (D39, 'registro_figuras_39r.json', None, 160)):
    r_ = json.loads((carp / 'validacion' / reg_).read_text(encoding='utf-8')).get('_fuente_minima', {})
    for fn, fmin in r_.items():
        w_ = Image.open(carp / 'figuras' / fn).size[0] / dpi_
        esc_ = min(1, 6.5 / w_)
        ok(G, f'{carp.parent.name[:3]} {fn}: texto efectivo ≥ 5 pt', fmin * esc_ >= 5, round(fmin * esc_, 2))

G = 'Maquetación'
for fase, carp in (('38R', D38), ('39R', D39)):
    c_ = carp / 'validacion' / 'control_maquetacion.csv'
    if not c_.exists():
        ok(G, f'{fase}: control de maquetación ejecutado', False)
        continue
    m_ = pd.read_csv(c_)
    ok(G, f'{fase}: un registro por Word', len(m_) == len(list((carp / 'word').glob('*.docx'))) and pd.to_numeric(m_['paginas'], errors='coerce').notna().all(), len(m_))
    vac_ = [x for d_ in m_['detalle_vacias'].dropna() for x in str(d_).split(', ') if float(x.split('=')[1]) < 0.20]
    ok(G, f'{fase}: sin páginas con solo unas líneas (ocupación menor que 20 %)', not vac_, vac_)
    for col_ in ('unidos_separados', 'filas_finales_aisladas', 'cabeceras_separadas', 'imagenes_fuera_de_margen'):
        ok(G, f'{fase}: {col_} = 0', int(m_[col_].sum()) == 0, m_[m_[col_] != 0][['documento', col_]].to_dict('records'))
d = pd.DataFrame(FILAS)
for D_ in (D38, D39):
    d.to_csv(D_ / 'validacion' / 'validacion_documentos.csv', index=False, encoding='utf-8')
print(f"{(d['resultado'] == 'superada').sum()}/{len(d)} superadas")
print(d.groupby('grupo')['resultado'].value_counts().to_string())
print(d[d['resultado'] != 'superada'].to_string(max_colwidth=330))
