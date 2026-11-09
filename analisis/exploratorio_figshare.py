"""
Análisis exploratorio del dataset figshare 20822032 ("Data Set Menopause Women",
Assaf et al., Jordania, CC BY 4.0). Uso: python analisis/exploratorio_figshare.py
Imprime los resultados que resumen el informe para la profesora.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

RUTA = Path(__file__).resolve().parent.parent / 'datos' / 'referencia' / 'data_set_menopause.xlsx'
SUBESCALAS = ['emotional', 'sexual', 'health', 'occupational']
SI = 1  # en el dataset 1 = sí, 2 = no

df = pd.read_excel(RUTA)

# --- Variables derivadas (codificación inferida del cuestionario) ---
# 'Loss menstuartion' solo la responden las que están en menopausia (≥12 meses):
# 1 natural, 2 quirúrgica, 3 por tratamiento. Vacío ⇒ pre/perimenopausia.
df['etapa'] = df['Loss menstuartion'].map({1: 'Posmenopausia natural', 2: 'Menopausia quirúrgica',
                                           3: 'Menopausia por tratamiento'}).fillna('Pre/perimenopausia')
df['posmenopausia'] = df['Loss menstuartion'].notna()
df['hipertension'] = df['Increase Bp Thyroid gland'] == SI
df['tiroides'] = df['Unnamed: 5'] == SI
df['diabetes'] = df['DM'] == SI
df['cardiopatia'] = df['Heart disease'] == SI
df['dolor_espalda'] = df['Back pain'] == SI
df['trabaja'] = df['profession working'] == SI
df['ejercicio'] = df['I practice exercise 3 times at least'] >= 2
df['n_cronicas'] = (df[['Increase Bp Thyroid gland', 'Unnamed: 5', 'Back pain', 'DM', 'Heart disease',
                        'Varcoise', 'Constipation', 'Respiratory', 'Tumors']] == SI).sum(axis=1)


def seccion(titulo):
    print(f'\n=== {titulo} ===')


seccion('Muestra')
print(f'n = {len(df)}; edad {df.Age.mean():.1f} ± {df.Age.std():.1f} (rango {df.Age.min()}-{df.Age.max()})')
print(df['etapa'].value_counts().to_string())
print('Faltantes:', df.isna().sum()[df.isna().sum() > 0].to_dict(), '(solo la pregunta condicional)')

seccion('Calidad de vida UQOL (mayor = mejor)')
print(df[SUBESCALAS + ['totalqol']].describe().round(1).T[['mean', 'std', 'min', 'max']].to_string())

seccion('Factores asociados a la calidad de vida total (Mann-Whitney)')
filas = []
for var in ['posmenopausia', 'hipertension', 'diabetes', 'tiroides', 'dolor_espalda', 'trabaja', 'ejercicio']:
    g1, g0 = df.loc[df[var], 'totalqol'], df.loc[~df[var], 'totalqol']
    u, p = stats.mannwhitneyu(g1, g0)
    filas.append((var, len(g1), g1.mean(), len(g0), g0.mean(), g1.mean() - g0.mean(), p))
print(pd.DataFrame(filas, columns=['factor', 'n_si', 'qol_si', 'n_no', 'qol_no', 'dif', 'p'])
      .round(3).to_string(index=False))
rho, p = stats.spearmanr(df.Age, df.totalqol)
print(f'Edad vs QoL total: rho={rho:.2f} p={p:.3f}')
rho, p = stats.spearmanr(df.n_cronicas, df.totalqol)
print(f'N° enfermedades crónicas vs QoL total: rho={rho:.2f} p={p:.3f}')
for var in ['Educational degree', 'income', 'How do you evaluate your health status']:
    rho, p = stats.spearmanr(df[var], df.totalqol)
    print(f'{var} vs QoL total: rho={rho:.2f} p={p:.3f}')

seccion('Subescalas por etapa (pre/peri vs posmenopausia)')
for s in SUBESCALAS:
    a, b = df.loc[~df.posmenopausia, s], df.loc[df.posmenopausia, s]
    print(f'{s:13s} pre/peri {a.mean():5.1f}  pos {b.mean():5.1f}  p={stats.mannwhitneyu(a, b)[1]:.3f}')

seccion('Agrupamiento exploratorio (k-means sobre las 4 subescalas estandarizadas)')
X = StandardScaler().fit_transform(df[SUBESCALAS])
for k in range(2, 6):
    km = KMeans(n_clusters=k, n_init=20, random_state=0).fit(X)
    print(f'k={k} silhouette={silhouette_score(X, km.labels_):.3f} tamaños={np.bincount(km.labels_).tolist()}')
km = KMeans(n_clusters=3, n_init=20, random_state=0).fit(X)
df['grupo'] = km.labels_
print(df.groupby('grupo')[SUBESCALAS + ['totalqol', 'Age', 'n_cronicas']].mean().round(1).to_string())
print(pd.crosstab(df.grupo, df.posmenopausia, normalize='index').round(2).to_string())

seccion('Regresión lineal múltiple sobre QoL total (efectos ajustados)')
df['educ_superior'] = df['educationcat'] == 2
df['cronicas_2mas'] = df['n_cronicas'] >= 2
predictores = ['Age', 'posmenopausia', 'trabaja', 'ejercicio', 'cronicas_2mas', 'educ_superior']
X = np.column_stack([np.ones(len(df))] + [df[c].astype(float) for c in predictores])
y = df['totalqol'].to_numpy(float)
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
resid = y - X @ beta
gl = len(y) - X.shape[1]
ee = np.sqrt(np.diag(resid @ resid / gl * np.linalg.inv(X.T @ X)))
pvals = 2 * stats.t.sf(np.abs(beta / ee), gl)
r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
for nombre, b, e, pv in zip(['intercepto'] + predictores, beta, ee, pvals):
    print(f'{nombre:15s} coef={b:7.2f}  EE={e:5.2f}  p={pv:.3f}')
print(f'R² = {r2:.3f}, n = {len(y)}')
