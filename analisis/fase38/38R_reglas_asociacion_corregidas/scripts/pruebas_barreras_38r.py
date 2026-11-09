"""
Fase 38R: pruebas específicas de las barreras. Cada control introduce un error en memoria o en una copia temporal y exige que la barrera detenga el proceso.
Además comprueba que las 16 configuraciones correctas pasan todas las barreras. Nada se calcula sobre el MRS salvo verificar el consecuente.

Uso, desde la carpeta scripts: python -B pruebas_barreras_38r.py
"""
import copy
import csv
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import barreras_38r as B  # noqa: E402
import nucleo_38r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
PQ = N.cargar()
SALIDA = N.BASE / 'pruebas' / 'resultados_barreras.csv'
filas = []


def debe_detener(nombre, f):
    try:
        f()
    except B.Incumplimiento as e:
        filas.append({'control': nombre, 'esperado': 'detiene', 'resultado': 'detuvo', 'correcto': True, 'detalle': str(e)[:200]})
    else:
        filas.append({'control': nombre, 'esperado': 'detiene', 'resultado': 'NO DETUVO', 'correcto': False, 'detalle': ''})


def debe_pasar(nombre, f):
    try:
        det = f()
    except Exception as e:  # noqa: BLE001
        filas.append({'control': nombre, 'esperado': 'pasa', 'resultado': 'FALLA', 'correcto': False, 'detalle': f'{type(e).__name__}: {e}'[:200]})
    else:
        filas.append({'control': nombre, 'esperado': 'pasa', 'resultado': 'pasó', 'correcto': True, 'detalle': det or ''})


dec = PQ.dec
L = list(N.PRINCIPAL)
debe_pasar('Lista de 29 autorizada', lambda: B.verificar_lista_principal(L, dec))
debe_detener('Agrega prevision', lambda: B.verificar_lista_principal(L + ['prevision'], dec))
debe_detener('Agrega usa_medicamentos_diabetes', lambda: B.verificar_lista_principal(L + ['usa_medicamentos_diabetes'], dec))
debe_detener('Agrega doble_carga', lambda: B.verificar_lista_principal(L + ['doble_carga'], dec))
debe_detener('Agrega imc reservada', lambda: B.verificar_lista_principal(L + ['imc'], dec))
debe_detener('Quita una variable', lambda: B.verificar_lista_principal(L[:-1], dec))
debe_detener('Cambia una autorizada por prevision', lambda: B.verificar_lista_principal(L[:-1] + ['prevision'], dec))
debe_detener('Variable repetida', lambda: B.verificar_lista_principal(L[:-1] + [L[0]], dec))


def fuente_alterada(clave, cambio):
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / B.FUENTES[clave].name
        cambio(B.FUENTES[clave], p)
        B.decisiones({clave: p})


def eleg_con_prevision(o, p):
    filas_ = list(csv.DictReader(open(o, encoding='utf-8-sig', newline='')))
    filas_[0] = {**filas_[0], 'variable': 'prevision'}
    with open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, list(filas_[0]))
        w.writeheader()
        w.writerows(filas_)


def texto_sin(o, p, quitar):
    p.write_text(Path(o).read_text(encoding='utf-8').replace(quitar, 'X'), encoding='utf-8')


debe_detener('Lista de la Fase 35 alterada con prevision', lambda: fuente_alterada('elegibles_33', eleg_con_prevision))
debe_detener('Protocolo 33 sin la exclusión de diabetes', lambda: fuente_alterada('protocolo_revision_33', lambda o, p: texto_sin(o, p, 'queda fuera de todo el modelado')))
debe_detener('Configuración 36 sin la exclusión de previsión', lambda: fuente_alterada('configuracion_36', lambda o, p: texto_sin(o, p, "'prevision'")))
debe_detener('Protocolo 36 sin la población 239', lambda: fuente_alterada('protocolo_36_ajustado', lambda o, p: texto_sin(o, p, '239 con sobrecarga observada')))

aut = B.permitidas('principal', dec)
vd = N.variable_de_item
for it in ('med_diabetes=SI', 'prevision=FONASA', 'seguro_fonasa=SI', 'ISAPRE=SI', 'tiene_diabetes=NO', 'doble_carga=SI', 'doblecarga=1', 'pregunta_3=alta', 'mrs_total=alto', 'severo_mrs=SI',
           'severidad_mrs=alta', 'consecuencias_laborales=SI', 'segmento=2', 'grupo_a=1', 'B1=2', 'etapa_menopausica=post'):
    debe_detener(f'Ítem prohibido por nombre: {it}', lambda it=it: B.verificar_items([it], vd, aut))
debe_detener('Ítem de variable no autorizada (imc en la principal)', lambda: B.verificar_items(['imc=30_o_mas'], vd, aut))
debe_detener('Ítem sin variable conocida', lambda: B.verificar_items(['desconocida=1'], vd, aut))

base = N.construir(PQ, 'principal')
n = 529


def T_con(nombre, m):
    T = pd.DataFrame(np.zeros((n, 1), bool), columns=['relleno'])
    T[nombre] = np.asarray(m, bool)
    return T


X, Mx, E = PQ.d.X, PQ.d.M, PQ.d.E
dc = pd.read_csv(N.RAIZ / 'datos/analitico/dataset_fase35.csv', dtype=str).set_index('participante_id').reindex(PQ.d.ids)['doble_carga']
casos = {
    'Disfraz de diabetes (sí)': (X['usa_medicamentos_diabetes'] == 1).to_numpy(), 'Disfraz de diabetes (complemento)': (X['usa_medicamentos_diabetes'] != 1).to_numpy(),
    'Disfraz de previsión FONASA': (X['prevision'] == 'FONASA').to_numpy(), 'Disfraz de doble carga': (dc == dc.dropna().unique()[0]).to_numpy(),
    'Consecuente como ítem': Mx['severo_mrs'].to_numpy() == 1, 'Ítem 3 del MRS binarizado': Mx['pregunta_3'].to_numpy() >= 2, 'Severidad del MRS': (Mx['severidad'] == 'Severa').to_numpy(),
    'Segmento A': (E['A'] == 0).to_numpy(), 'Segmento B1': (E['B1'] == 0).to_numpy()}
for nombre, m in casos.items():
    debe_detener(f'Contenido vetado con nombre inocuo: {nombre}', lambda nombre=nombre, m=m: B.verificar_contenido(T_con('x=1', m), PQ.vetadas))


def con_poblacion(nombre, cambio):
    c = N.construir(PQ, nombre)
    c2 = copy.copy(c)
    cambio(c2)
    B.verificar_poblacion(nombre, c2, PQ.d)


def recorta(c):
    c.n, c.ids, c.T = c.n - 1, c.ids[:-1], c.T.iloc[:-1]


debe_detener('Principal con una participante menos', lambda: con_poblacion('principal', recorta))
debe_detener('S7a con la población de 309', lambda: B.verificar_poblacion('S7a', N.construir(PQ, 'S7a-309'), PQ.d))
debe_detener('S7a-309 con la población de 287', lambda: B.verificar_poblacion('S7a-309', N.construir(PQ, 'S7a'), PQ.d))
debe_detener('S7b con las 12 imputadas', lambda: B.verificar_poblacion('S7b', N.construir(PQ, 'S7b-251'), PQ.d))
debe_detener('S7b-251 sin las imputadas', lambda: B.verificar_poblacion('S7b-251', N.construir(PQ, 'S7b'), PQ.d))
debe_detener('S8 en toda la muestra', lambda: B.verificar_poblacion('S8a', N.construir(PQ, 'principal'), PQ.d))
debe_detener('S1 con imputados', lambda: B.verificar_poblacion('S1', N.construir(PQ, 'principal'), PQ.d) or (_ for _ in ()).throw(B.Incumplimiento('S1 sin restricción no detectado')))


def s1_con_imputados():
    c = N.construir(PQ, 'S1')
    T = c.T.copy()
    imp = PQ.d.estado['tiene_pareja'].isin(['imputada', 'deducida']).to_numpy()
    T.loc[imp, 'pareja=SI'] = True
    c2 = copy.copy(c)
    c2.T = T
    B.verificar_poblacion('S1', c2, PQ.d)


debe_detener('S1 con ítem en una celda imputada', s1_con_imputados)
R_mala = pd.DataFrame({'antecedente': ['trabaja=SI & med_diabetes=NO'], 'variables': ['trabaja_actualmente & usa_medicamentos_diabetes'], 'consecuente': ['severo_mrs=SI']})
debe_detener('Regla con un ítem excluido', lambda: B.verificar_reglas(R_mala, vd, aut, N.CONSECUENTES))
R_mala2 = pd.DataFrame({'antecedente': ['trabaja=SI'], 'variables': ['prevision'], 'consecuente': ['severo_mrs=SI']})
debe_detener('Regla con variable excluida en su columna', lambda: B.verificar_reglas(R_mala2, vd, aut, N.CONSECUENTES))
for nombre in N.CONFIGS:
    debe_pasar(f'Configuración correcta: {nombre}', lambda nombre=nombre: (lambda c: f'n={c.n}, variables={len(c.variables)}, ítems={c.T.shape[1]}, umbrales={c.min_ant}/{c.min_conj}')(N.construir(PQ, nombre)))

R = pd.DataFrame(filas)
N.a_csv(R, SALIDA)
print(R[['control', 'resultado', 'correcto', 'detalle']].to_string(index=False, max_colwidth=90))
print(f"{int(R['correcto'].sum())}/{len(R)} correctos")
sys.exit(0 if R['correcto'].all() else 1)
