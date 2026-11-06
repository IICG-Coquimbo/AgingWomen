"""
Cierre de la Fase 35: versión documental revisada del informe de la Fase 35A.

Lee analisis/informe_preprocesamiento_fase35.md sin modificarlo y escribe una copia con la descripción de poblaciones
corregida y con notas de revisión. No cambia ninguna tabla ni resultado: test_documental_cierre.py lo comprueba.
Uso, desde analisis/: python cierre_fases_34_35/scripts/generar_35A_revisado.py
"""
from pathlib import Path

ANALISIS = Path(__file__).resolve().parents[2]
ORIGEN = ANALISIS / 'informe_preprocesamiento_fase35.md'
DESTINO = ANALISIS / 'cierre_fases_34_35' / 'informes' / 'informe_preprocesamiento_fase35_revisado.md'

ENCABEZADO = """> **Versión documental revisada (4 de noviembre de 2026).** La versión histórica se conserva sin cambios en `analisis/informe_preprocesamiento_fase35.md`. Esta revisión corrige la descripción de la población laboral y agrega notas marcadas como *[Revisión 35A]*. No cambia ninguna tabla, cifra, dato ni resultado, y no se volvió a ejecutar `preprocesar_fase35.py`.

"""

FRASE_22 = ('22 trabajadoras sin respuesta en lugar de trabajo comprensivo, 22 trabajadoras sin respuesta en estrés '
            'del entorno laboral reciben la mediana de las trabajadoras.')
FRASE_22_NUEVA = (
    'Entre las 529 participantes, **309 quedan clasificadas como trabajadoras: 287 con situación laboral respondida o '
    'deducida y 22 clasificadas así por imputación** de `trabaja_actualmente` en la Fase 34B. El valor imputado no es '
    'una respuesta observada: estas 22 participantes no confirmaron que trabajan. Tampoco tienen datos de lugar de '
    'trabajo comprensivo ni de estrés del entorno laboral, y el conjunto de esta fase les asigna en ambas la mediana '
    '(valor 3). Ese 3 es un valor de relleno, no una opinión neutral real.')

NOTA_POBLACIONES = """

*[Revisión 35A] Poblaciones. Los tamaños usados en Shannon y Random Forest no cambian: 529 en la capa general y 287 en el módulo laboral. Las 22 quedan fuera de las 287, de modo que sus valores 3 no entraron en esos análisis laborales; sí permanecen en `datos/analitico/dataset_fase35.csv` y `dataset_fase35_33_variables.csv`, que no se modifican. Quien use esas columnas debe excluirlos o tratarlos como no observados. Las 287 tampoco son todas respuestas directas: la Fase 34B imputó 16 valores de lugar de trabajo y 10 de estrés dentro de ese grupo, y 263 participantes tienen ambas respuestas observadas.*"""

NOTAS = [
    ('Todo umbral o excepción está en el archivo de configuración: si la profesora pide cambiar algo, se edita ese '
     'archivo y se vuelve a correr el script.',
     '\n\n*[Revisión 35A] Este texto describe el procedimiento de ese momento. Las decisiones metodológicas vigentes se revisan con la responsable del proyecto.*'),
    ('Peso y talla siguen en el conjunto limpio; solo salen del conjunto para el modelado. La cantidad de personas que '
     'cuida vale 0 para quienes no cuidan y mide intensidad de cuidado, no la sobrecarga percibida.',
     '\n\n*[Revisión 35A] Decisión posterior. Esta tabla registra la decisión del 27-10. La revisión del 03-11 volvió a evaluar `sobrecarga_fisica_emocional` como módulo de cuidados (239 cuidadoras con sobrecarga observada; 251 como sensibilidad), de modo que hoy es una de las 33 variables elegibles. No está en `dataset_fase35_33_variables.csv`; se toma del conjunto limpio.*'),
    ('La dominancia se mide sobre la variable tal como entra al modelo (con el 0 de "no realiza" y la categoría "no '
     'aplica").',
     ' *[Revisión 35A] Decisión posterior: la excepción de la fila «Medicamentos para la diabetes» ya no está vigente. Con 87,5 % de dominancia supera el umbral y la variable quedó fuera de las elegibles.*'),
    ('Se compara lo observado con los efectos que la simulación puso a propósito.',
     ' *[Revisión 35A] En esta tabla, «quienes trabajan» con n = 287 corresponde a la situación laboral respondida o deducida; no incluye a las 22 imputadas.*'),
    ('**Edad.** Se mantiene como candidata:',
     '*[Revisión 35A] La regla de la etapa menopáusica sigue siendo una aproximación propia y no está validada; la etapa se mantiene fuera de las variables elegibles. Su revisión corresponde a la responsable del proyecto.*\n\n'),
    ('Archivo: `datos/analitico/dataset_fase35.csv`',
     '*[Revisión 35A] Lista vigente. Estas 35 predictoras son el conjunto de esa fecha. La lista vigente tiene 33 variables elegibles (30 generales, 2 laborales y 1 de sobrecarga): salen `prevision`, `doble_carga` y `usa_medicamentos_diabetes`, y entra `sobrecarga_fisica_emocional`.*\n\n'),
    ('- ✔ predictoras sin vacíos',
     ' *[Revisión 35A] Sin vacíos porque los faltantes ya están imputados o codificados; no significa que todos los valores sean respuestas observadas.*'),
]
ANTEPONER = {'**Edad.** Se mantiene como candidata:', 'Archivo: `datos/analitico/dataset_fase35.csv`'}


def reemplazar(texto, ancla, nuevo):
    if texto.count(ancla) != 1:
        raise ValueError(f'El anclaje debe aparecer una vez: {ancla[:60]}')
    return texto.replace(ancla, nuevo)


def anotar_fin_de_parrafo(texto, ancla, nota):
    """Agrega la nota al final de la línea que contiene el anclaje."""
    if texto.count(ancla) != 1:
        raise ValueError(f'El anclaje debe aparecer una vez: {ancla[:60]}')
    inicio = texto.index(ancla)
    fin = texto.find('\n', inicio)
    fin = len(texto) if fin < 0 else fin
    return texto[:fin] + nota + texto[fin:]


def main():
    t = ORIGEN.read_text(encoding='utf-8')
    titulo, resto = t.split('\n', 1)
    t = f'{titulo}\n\n{ENCABEZADO}{resto.lstrip()}'
    t = anotar_fin_de_parrafo(t, FRASE_22, NOTA_POBLACIONES)
    t = reemplazar(t, FRASE_22, FRASE_22_NUEVA)
    for ancla, nota in NOTAS:
        t = reemplazar(t, ancla, nota + ancla) if ancla in ANTEPONER else anotar_fin_de_parrafo(t, ancla, nota)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(t, encoding='utf-8')
    print(DESTINO.relative_to(ANALISIS.parent).as_posix())


if __name__ == '__main__':
    main()
