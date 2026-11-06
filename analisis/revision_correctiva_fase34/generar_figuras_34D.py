"""
Corrección controlada de la Fase 34: figuras de la 34D con el rótulo corregido, en una carpeta nueva.

Uso, desde la raíz del proyecto:
    python analisis/revision_correctiva_fase34/generar_figuras_34D.py

Dibuja las barras con las frecuencias históricas (frecuencias_univariado.csv), sin recalcular ni tocar
eda_univariado.py, que borraría las figuras históricas. Comprueba tres cosas y se detiene si alguna falla:
  1. Con el rótulo antiguo, el código y las frecuencias reproducen cada figura histórica píxel a píxel.
  2. Cada barra nueva vale lo mismo que la frecuencia histórica.
  3. Los estadísticos de horas sentada coinciden con el resumen histórico.
Escribe solo en figuras_34D_revisadas/ y tablas/. La reproducción con el rótulo antiguo queda en una carpeta temporal.
"""
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

from eda import univariado as U  # noqa: E402
from eda import variables as V  # noqa: E402

RES = AQUI.parent / 'resultados' / 'usuaria'
HISTORICAS = AQUI.parent / 'figuras' / 'eda_univariado'
SALIDA = AQUI / 'figuras_34D_revisadas'
TABLAS = AQUI / 'tablas'


def subtitulo_historico(f, _ancho=95):
    texto = f'n válido = {f.n_valido} · faltante = {f.n_faltante} ({U._pct(f.porcentaje_faltante)}) · {f.tipo}'
    return texto + (f'\n% sobre {f.denominador}' if f.n_no_aplica else '')


def barras_iguales(frec, f, ruta):
    """Dibuja y lee del eje las alturas y rótulos antes de cerrar la figura."""
    capturado = {}
    cerrar = plt.close

    def espiar(fig=None):
        ax = fig.axes[0]
        capturado['alturas'] = [b.get_height() for b in ax.patches]
        capturado['rotulos'] = [t.get_text() for t in ax.texts if '%\n(n = ' in t.get_text()]
        capturado['subtitulo'] = next(t.get_text() for t in ax.texts if t.get_text().startswith('n'))
        cerrar(fig)

    plt.close = espiar
    try:
        U.figura(frec, f, ruta)
    finally:
        plt.close = cerrar
    ok_alturas = np.allclose(capturado['alturas'], frec['pct'].to_numpy(), atol=1e-9)
    ok_rotulos = capturado['rotulos'] == [U._rotulo(p, n) for p, n in zip(frec['pct'], frec['n'])]
    return ok_alturas and ok_rotulos, capturado['subtitulo']


def main():
    resumen = pd.read_csv(RES / 'eda_univariado_resumen.csv', encoding='utf-8-sig')
    frecuencias = pd.read_csv(RES / 'frecuencias_univariado.csv', encoding='utf-8-sig', dtype={'categoria': str},
                              keep_default_na=False)
    frecuencias['n'] = frecuencias['n'].astype(int)
    frecuencias['pct'] = frecuencias['pct'].astype(float)
    SALIDA.mkdir(exist_ok=True)
    filas, distintas = [], []

    rotulo_nuevo = U.subtitulo
    with tempfile.TemporaryDirectory() as tmp:
        for f in resumen.itertuples():
            frec = frecuencias[frecuencias['variable'] == f.variable].copy()
            # El CSV guarda 4 decimales; n / n válido da el mismo % sin redondeo, como en la figura original.
            exacto = 100 * frec['n'] / f.n_valido
            if (exacto - frec['pct']).abs().max() > 5.1e-5:
                raise SystemExit(f'{f.variable}: los % guardados no corresponden a n / n válido')
            frec['pct'] = exacto
            nombre = f'univariado_{f.variable}.png'
            U.subtitulo = subtitulo_historico
            copia = Path(tmp) / nombre
            U.figura(frec, f, copia)
            U.subtitulo = rotulo_nuevo
            a, b = mpimg.imread(copia), mpimg.imread(HISTORICAS / nombre)
            reproduce = a.shape == b.shape and float(np.abs(a - b).max()) == 0
            if not reproduce:
                distintas.append(f.variable)
            ok, rotulo = barras_iguales(frec, f, SALIDA / nombre)
            if not ok:
                raise SystemExit(f'{f.variable}: las barras nuevas no coinciden con las frecuencias históricas')
            filas.append({'variable': f.variable, 'figura_historica': f'analisis/figuras/eda_univariado/{nombre}',
                          'figura_revisada': f'analisis/revision_correctiva_fase34/figuras_34D_revisadas/{nombre}',
                          'reproduce_historica_con_rotulo_antiguo': reproduce, 'barras_iguales_a_frecuencias': ok,
                          'rotulo_historico': subtitulo_historico(f).replace('\n', ' | '), 'rotulo_revisado': rotulo.replace('\n', ' | ')})

    # Numéricas: solo cambia lo que tiene imputadas (horas sentada); las otras cinco distribuciones siguen vigentes.
    df, _ = V.cargar(V.LIMPIO_USUARIA, 'dataset_usuaria_limpio.csv')
    mrs = U.preparar(df)
    numericas = [(V.numerica(mrs[f.variable]).dropna(), f) for f in resumen.itertuples() if f.tipo.startswith('numérica')]
    for x, f in numericas:
        if f.variable == 'horas_sedentarismo':
            forma = U.forma_distribucion(x)
            for k in ('media', 'desviacion_estandar', 'mediana', 'asimetria', 'curtosis'):
                if abs(forma[k] - getattr(f, k)) > 1e-4:
                    raise SystemExit(f'horas_sedentarismo: {k} no coincide con el resumen histórico')
            nombre = 'univariado_horas_sedentarismo_distribucion.png'
            U.figura_distribucion(x, f, SALIDA / nombre)
            filas.append({'variable': f.variable, 'figura_historica': f'analisis/figuras/eda_univariado/{nombre}',
                          'figura_revisada': f'analisis/revision_correctiva_fase34/figuras_34D_revisadas/{nombre}',
                          'rotulo_historico': 'distribución (valores observados)', 'rotulo_revisado': 'distribución (incluye 27 imputadas)'})
    nombre = 'univariado_numericas_puntos.png'
    U.figura_puntos(numericas, SALIDA / nombre)
    filas.append({'variable': 'numéricas', 'figura_historica': f'analisis/figuras/eda_univariado/{nombre}',
                  'figura_revisada': f'analisis/revision_correctiva_fase34/figuras_34D_revisadas/{nombre}',
                  'rotulo_historico': 'Horas (n = 529; atípicos)', 'rotulo_revisado': 'Horas (n = 529; imputadas: 27; atípicos)'})

    pd.DataFrame(filas).to_csv(TABLAS / 'relacion_figuras_34D.csv', index=False, encoding='utf-8-sig')
    print(len(filas), 'figuras revisadas; no reproducen píxel a píxel:', distintas)


if __name__ == '__main__':
    main()
