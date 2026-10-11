"""
Fase 32 (OB1, Actividad 2): limpia el dataset entregado por la profesora.

Uso:
    python analisis/limpiar_dataset.py
    python analisis/limpiar_dataset.py --entrada datos/dataset_menopausia_sucio.csv --salida datos/limpio

Las reglas están en analisis/limpieza/reglas.py y el resultado se explica en
analisis/informe_limpieza.md. Siempre produce los mismos archivos para la
misma entrada.
"""
import argparse
from pathlib import Path

import pandas as pd

from limpieza import informe
from limpieza.reglas import limpiar

RAIZ = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description='Limpia el dataset de la encuesta (Fase 32).')
    parser.add_argument('--entrada', type=Path, default=RAIZ / 'datos' / 'dataset_menopausia_sucio.csv')
    parser.add_argument('--salida', type=Path, default=RAIZ / 'datos' / 'limpio')
    parser.add_argument('--informe', type=Path, default=RAIZ / 'analisis' / 'informe_limpieza.md')
    args = parser.parse_args()

    crudo = pd.read_csv(args.entrada, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    limpio, excluidas, diccionario, bit = limpiar(crudo)

    args.salida.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: Excel abre bien los acentos.
    limpio.to_csv(args.salida / 'dataset_menopausia_limpio.csv', index=False, encoding='utf-8-sig')
    excluidas.to_csv(args.salida / 'excluidas.csv', index=False, encoding='utf-8-sig')
    diccionario.to_csv(args.salida / 'diccionario_variables.csv', index=False, encoding='utf-8-sig')

    relativo = lambda p: p.resolve().relative_to(RAIZ).as_posix()
    texto = informe.generar(limpio, excluidas, diccionario, bit,
                            relativo(args.entrada), relativo(args.salida))
    args.informe.write_text(texto, encoding='utf-8')

    print(f'{len(crudo)} filas → {len(limpio)} limpias, {len(excluidas)} excluidas')
    print(f'Informe: {relativo(args.informe)}')


if __name__ == '__main__':
    main()
