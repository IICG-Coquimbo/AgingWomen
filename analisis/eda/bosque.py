"""
Random Forest para rankear variables (Fase 33 — OB2, Actividad 1).

La importancia se mide por permutación en cada partición de prueba de una
validación cruzada de 5 particiones: cuánto empeora el modelo al desordenar
una variable en datos que no vio al entrenar. Una variable queda
"seleccionada" por el bosque si su importancia es positiva en al menos
MINIMO_PARTICIONES de las 5 particiones (y positiva en promedio).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import balanced_accuracy_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold

SEMILLA = 2026
PARTICIONES = 5
# Con relaciones débiles, una variable útil puede no aportar en alguna partición
# solo por azar; por eso basta con 4 de 5 (decisión de la usuaria, 2026-10-11).
MINIMO_PARTICIONES = 4
REPETICIONES = 20              # permutaciones por variable y partición
PARAMETROS = dict(n_estimators=500, min_samples_leaf=5, max_features='sqrt',
                  random_state=SEMILLA, n_jobs=-1)


def evaluar(X, y, tarea):
    """
    tarea = 'regresion' (y = MRS total) o 'clasificacion' (y = 1 si severa).
    Devuelve (metricas por partición, importancia por variable).
    """
    if tarea == 'regresion':
        cv = KFold(PARTICIONES, shuffle=True, random_state=SEMILLA)
        modelo = RandomForestRegressor(**PARAMETROS)
        puntaje = 'r2'
    else:
        cv = StratifiedKFold(PARTICIONES, shuffle=True, random_state=SEMILLA)
        modelo = RandomForestClassifier(class_weight='balanced', **PARAMETROS)
        puntaje = 'roc_auc'

    metricas, perm, impureza = [], [], []
    for k, (ent, pru) in enumerate(cv.split(X, y)):
        modelo.fit(X.iloc[ent], y.iloc[ent])
        Xp, yp = X.iloc[pru], y.iloc[pru]
        if tarea == 'regresion':
            pred = modelo.predict(Xp)
            metricas.append({'particion': k + 1, 'R2': r2_score(yp, pred),
                             'MAE': mean_absolute_error(yp, pred)})
        else:
            prob = modelo.predict_proba(Xp)[:, 1]
            metricas.append({'particion': k + 1, 'AUC': roc_auc_score(yp, prob),
                             'exactitud_balanceada': balanced_accuracy_score(yp, prob >= 0.5)})
        # Predecir con un solo proceso y paralelizar por variable: lanzar el
        # paralelismo del bosque en cada una de miles de predicciones es lentísimo.
        modelo.set_params(n_jobs=1)
        r = permutation_importance(modelo, Xp, yp, scoring=puntaje, n_repeats=REPETICIONES,
                                   random_state=SEMILLA + k, n_jobs=-1)
        modelo.set_params(n_jobs=-1)
        perm.append(r.importances_mean)
        impureza.append(modelo.feature_importances_)

    perm, impureza = np.array(perm), np.array(impureza)
    importancia = pd.DataFrame({
        'variable': X.columns,
        'perm_media': perm.mean(axis=0), 'perm_de': perm.std(axis=0),
        'perm_positiva_en': (perm > 0).sum(axis=0),
        'impureza_media': impureza.mean(axis=0),
    }).sort_values('perm_media', ascending=False)
    importancia['seleccionada'] = ((importancia['perm_positiva_en'] >= MINIMO_PARTICIONES)
                                   & (importancia['perm_media'] > 0))
    return pd.DataFrame(metricas), importancia.reset_index(drop=True)
