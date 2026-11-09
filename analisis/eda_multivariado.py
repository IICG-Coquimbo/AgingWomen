"""
Fase 34E (OB2): análisis multivariado exploratorio (plan aprobado 2026-10-30).

Uso:
    python analisis/eda_multivariado.py

Necesita las Fases 34B (datos/limpio_usuaria/dataset_usuaria_limpio.csv), 34C
(datos/analitico/conjunto_eda_usuaria.csv) y 35A (datos/analitico/dataset_fase35.csv,
resultados/usuaria/diccionario_datos_fase35.csv).
Escribe:
  - analisis/figuras/eda_multivariado/: matriz de asociación, grupos
    (dendrograma + matriz reordenada) y una figura por tríada
  - analisis/resultados/usuaria/{matriz_asociacion_mixta,pares_asociacion_mixta,
    grupos_variables,triadas_estratificadas,triadas_modelos,triadas_resumen}.csv
  - analisis/informe_eda_multivariado.md

No imputa: usa el IMC observado, deja fuera del par a quien no le aplica una
pregunta y usa las respuestas laborales originales (no las imputadas en 35A).
"""
import pandas as pd
from statsmodels.stats.multitest import multipletests

from eda import multivariado as M
from eda import variables as V
from eda.informe_multivariado import generar

ANALISIS = V.RAIZ / 'analisis'
FIGURAS = ANALISIS / 'figuras' / 'eda_multivariado'
RESULTADOS = ANALISIS / 'resultados' / 'usuaria'
GUARDAR = dict(index=False, encoding='utf-8-sig', float_format='%.4f')


def main():
    FIGURAS.mkdir(parents=True, exist_ok=True)
    for viejo in FIGURAS.glob('*.png'):
        viejo.unlink()
    datos, tipos, exploratorias = M.cargar()

    # 1. Matriz de asociación mixta (exploratorias + severidad como referencia)
    variables = [M.SEVERIDAD, *exploratorias]
    pares, matriz = M.matriz_mixta(datos, variables, tipos)
    M.figura_matriz(matriz, FIGURAS / 'matriz_asociacion.png',
                    f'Matriz de asociación de {len(exploratorias)} variables exploratorias y la severidad')

    # 2. Grupos de variables (sin severidad: es la referencia, no se agrupa)
    m_expl = matriz.loc[exploratorias, exploratorias]
    enlace, grupo, orden = M.agrupar(m_expl)
    con_severidad = matriz[M.SEVERIDAD].abs().to_dict()
    grupos = M.tabla_grupos(m_expl, grupo, orden, con_severidad)
    M.figura_grupos(m_expl, enlace, orden, grupo, FIGURAS / 'grupos_variables.png')

    # 3. Tríadas
    estratos, modelos, resumen = [], [], []
    for t in M.TRIADAS:
        d, orden_a, orden_b = M.preparar_triada(datos, t)
        tabla = M.estratificar(d, orden_a, orden_b)
        M.figura_triada(t, tabla, orden_a, orden_b, FIGURAS / f'triada_{t["clave"]}.png')
        efectos, prueba = M.modelar(d, orden_a, orden_b)
        va, vb = t['a'][0], t['b'][0]
        rho_a, parcial_a, p_a = M.spearman_parcial(d, va, vb)
        rho_b, parcial_b, p_b = M.spearman_parcial(d, vb, va)
        estratos.append(tabla.assign(triada=t['clave']))
        modelos.append(efectos.assign(triada=t['clave']))
        resumen.append({'triada': t['clave'], 'titulo': t['titulo'], 'variable_a': va, 'variable_b': vb,
                        **prueba, 'rho_a': rho_a, 'rho_a_parcial': parcial_a, 'p_a_parcial': p_a,
                        'rho_b': rho_b, 'rho_b_parcial': parcial_b, 'p_b_parcial': p_b})
    resumen = pd.DataFrame(resumen)
    resumen['p_interaccion_ajustado'] = multipletests(resumen['p_interaccion'], method='fdr_bh')[1]
    estratos, modelos = pd.concat(estratos, ignore_index=True), pd.concat(modelos, ignore_index=True)

    # 4. Salidas
    matriz.rename_axis('variable').reset_index().to_csv(RESULTADOS / 'matriz_asociacion_mixta.csv', **GUARDAR)
    pares.to_csv(RESULTADOS / 'pares_asociacion_mixta.csv', **GUARDAR)
    grupos.to_csv(RESULTADOS / 'grupos_variables.csv', **GUARDAR)
    estratos.to_csv(RESULTADOS / 'triadas_estratificadas.csv', **GUARDAR)
    modelos.to_csv(RESULTADOS / 'triadas_modelos.csv', **GUARDAR)
    resumen.to_csv(RESULTADOS / 'triadas_resumen.csv', **GUARDAR)
    r = {'datos': datos, 'tipos': tipos, 'exploratorias': exploratorias, 'pares': pares, 'matriz': matriz,
         'grupo': grupo, 'grupos': grupos, 'orden': orden, 'estratos': estratos, 'modelos': modelos,
         'resumen': resumen}
    (ANALISIS / 'informe_eda_multivariado.md').write_text(generar(r), encoding='utf-8')
    print(f'{len(pares)} pares; {len(grupos)} grupos de 2 o más variables; {len(resumen)} tríadas')
    print('Informe: analisis/informe_eda_multivariado.md')


if __name__ == '__main__':
    main()
