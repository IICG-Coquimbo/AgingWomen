"""
Limpieza reproducible de la encuesta (OB1).

Uso:
    python analisis/limpiar_dataset.py                 # conjunto sintético de la usuaria (Fase 34B)
    python analisis/limpiar_dataset.py --entrada datos/dataset_menopausia_sucio.csv \
        --salida datos/limpio --informe analisis/informe_limpieza.md   # conjunto de la profesora (anexo)

Las reglas están en analisis/limpieza/reglas.py y el resultado se explica en el
informe. El archivo limpio se llama como la entrada, con "sucio" cambiado por
"limpio". Si junto a la entrada están el conjunto verdadero y la bitácora del
ensuciado (conjunto sintético), el informe agrega la evaluación de la limpieza.
Siempre produce los mismos archivos para la misma entrada.
"""
import argparse
from pathlib import Path

import pandas as pd

from limpieza import informe
from limpieza.evaluacion import evaluar
from limpieza.reglas import limpiar

RAIZ = Path(__file__).resolve().parent.parent


def leer(ruta):
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def main():
    parser = argparse.ArgumentParser(description='Limpia el conjunto de datos de la encuesta.')
    parser.add_argument('--entrada', type=Path,
                        default=RAIZ / 'datos' / 'sintetico' / 'dataset_usuaria_sucio.csv')
    parser.add_argument('--salida', type=Path, default=RAIZ / 'datos' / 'limpio_usuaria')
    parser.add_argument('--informe', type=Path, default=RAIZ / 'analisis' / 'informe_limpieza_usuaria.md')
    args = parser.parse_args()

    crudo = leer(args.entrada)
    limpio, excluidas, diccionario, bit = limpiar(crudo)

    archivo = args.entrada.name.replace('sucio', 'limpio')
    if archivo == args.entrada.name:
        archivo = f'{args.entrada.stem}_limpio.csv'
    args.salida.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: Excel abre bien los acentos.
    limpio.to_csv(args.salida / archivo, index=False, encoding='utf-8-sig')
    excluidas.to_csv(args.salida / 'excluidas.csv', index=False, encoding='utf-8-sig')
    diccionario.to_csv(args.salida / 'diccionario_variables.csv', index=False, encoding='utf-8-sig')

    verdad = args.entrada.with_name(args.entrada.name.replace('sucio', 'verdad'))
    bitacora = args.entrada.with_name('bitacora_suciedad.csv')
    evaluacion = None
    if verdad != args.entrada and verdad.exists() and bitacora.exists():
        evaluacion = evaluar(limpio, excluidas, leer(verdad), leer(bitacora))
        titulo = 'Informe de limpieza del conjunto sintético de la usuaria (Fase 34B)'
    else:
        titulo = 'Informe de limpieza del dataset de la profesora (Fase 32, anexo)'

    def relativo(p):
        p = p.resolve()
        return p.relative_to(RAIZ).as_posix() if p.is_relative_to(RAIZ) else p.as_posix()

    texto = informe.generar(limpio, excluidas, diccionario, bit, relativo(args.entrada),
                            relativo(args.salida), archivo, titulo, evaluacion)
    args.informe.write_text(texto, encoding='utf-8')

    print(f'{len(crudo)} filas → {len(limpio)} limpias, {len(excluidas)} excluidas')
    if evaluacion:
        print(f'Evaluación: {evaluacion["cambios_error"]} celdas correctas cambiadas por error')
    print(f'Informe: {relativo(args.informe)}')


if __name__ == '__main__':
    main()
