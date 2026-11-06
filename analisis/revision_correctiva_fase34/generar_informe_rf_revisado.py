"""
Corrección controlada de la Fase 34: versión documental corregida del informe de Random Forest (H17).

Uso, desde la raíz del proyecto:
    python analisis/revision_correctiva_fase34/generar_informe_rf_revisado.py          # genera
    python analisis/revision_correctiva_fase34/generar_informe_rf_revisado.py verificar # compara con el original

Copia el Word histórico y solo agrega notas y una tabla descriptiva. No lee modelos, no entrena ni recalcula.
La verificación exige que todos los párrafos originales sigan, en el mismo orden, y que las imágenes sean idénticas.
"""
import hashlib
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
ORIGINAL = AQUI.parent / 'random_forest_revision_35b_33_variables' / 'informe' / 'informe_random_forest_33_variables.docx'
REVISADO = AQUI / 'informes_revisados' / 'informe_random_forest_33_variables_revisado.docx'
ESTILO_NOTA = '<w:pPr><w:jc w:val="both"/></w:pPr>'
ESTILO_LISTA = '<w:pPr><w:pStyle w:val="Listaconvietas"/></w:pPr>'
INDICE = re.compile(r'^\d+(\.\d+)?\. .*\d+$|^(Resumen|Referencias|Anexo).*\d+$')


def escapar(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def parrafo(negrita, texto, estilo=ESTILO_NOTA):
    return (f'<w:p>{estilo}<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escapar(negrita)}</w:t></w:r>'
            f'<w:r><w:t xml:space="preserve"> {escapar(texto)}</w:t></w:r></w:p>')


def textos(xml):
    return [''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)', p)) for p in re.findall(r'<w:p[ >].*?</w:p>', xml, flags=re.S)]


def tabla_h17(xml):
    """Clona la Tabla 4 para conservar su formato: encabezado + una fila por variable."""
    pos = xml.index('>Celdas imputadas<')
    ini = xml.rindex('<w:tbl>', 0, pos)
    fin = xml.index('</w:tbl>', pos) + len('</w:tbl>')
    tbl = xml[ini:fin]
    filas = re.findall(r'<w:tr[ >].*?</w:tr>', tbl, flags=re.S)
    cabeza_tbl = tbl[:tbl.index(filas[0])]

    def fila(molde, valores):
        limpia = re.sub(r' w14:(paraId|textId)="[^"]*"', '', molde)
        trozos = iter(valores)
        return re.sub(r'(<w:t(?: [^>]*)?>)[^<]*', lambda m: m.group(1) + escapar(str(next(trozos))), limpia)

    datos = pd.read_csv(AQUI / 'tablas' / 'rf_identificacion_imputadas.csv', encoding='utf-8-sig')
    etiquetas = pd.read_csv(AQUI.parent / 'resultados' / 'usuaria' / 'eda_univariado_resumen.csv', encoding='utf-8-sig').set_index('variable')['etiqueta']
    assert len(datos) == 10 and (datos['identificadas'] < datos['exactas_529']).all()
    resultado = [fila(filas[0], ['Variable', 'Celdas imputadas (546)', 'Identificadas', 'Exactas (529)', 'Tratamiento en sensibilidad'])]
    for f in datos.itertuples():
        trato = 'Reimputada' if f.tratamiento.startswith('Reimputada') else 'No reimputada'
        resultado.append(fila(filas[1 + (f.Index % (len(filas) - 1))], [etiquetas[f.variable], f.imputadas_34B, f.identificadas, f.exactas_529, trato]))
    return cabeza_tbl + ''.join(resultado) + '</w:tbl>'


def generar():
    entrada = zipfile.ZipFile(ORIGINAL)
    xml = entrada.read('word/document.xml').decode('utf-8')

    def despues_de(frase, nuevo):
        nonlocal xml
        assert xml.count(frase) == 1, frase
        fin = xml.index('</w:p>', xml.index(frase)) + len('</w:p>')
        xml = xml[:fin] + nuevo + xml[fin:]

    despues_de('>Noviembre de 2026<',
               '<w:p><w:pPr><w:spacing w:before="120" w:after="0"/><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="20"/></w:rPr>'
               '<w:t>Versión documental revisada, 04-11-2026: agrega el hallazgo H17 (secciones 5.2, 7.7 y 12). Métricas, importancias, modelos y predicciones no cambian.</w:t></w:r></w:p>')
    h17 = (
        parrafo('Nota de revisión (H17).', 'La auditoría de la Fase 34 comparó estas celdas con una reconstrucción exacta de la limpieza. Este análisis las reconoció por estar vacías en el conjunto sucio, '
                'de modo que no reconoció las respuestas inválidas que la limpieza vació antes de imputar. Eso ocurre en 10 variables, no solo en las cinco de la Tabla 4.')
        + '<w:p><w:pPr><w:pStyle w:val="Descripcin"/><w:keepNext/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t>Tabla 4-bis.</w:t></w:r><w:r><w:t xml:space="preserve"> Variables con identificación incompleta. «Celdas imputadas» cuenta sobre las 546 del conjunto limpio; «Exactas», sobre las 529 analizadas.</w:t></w:r></w:p>'
        + tabla_h17(xml) + '<w:p/>'
        + parrafo('Qué alcanza.', 'Solo a la revisión de esta sección y a la sensibilidad de la sección 7.7. Los modelos principales conservan los valores de la Fase 34B y no usan esta identificación.', ESTILO_LISTA)
        + parrafo('Qué no alcanza.', 'Los valores reconstruidos de IMC (262), lugar de trabajo (16) y estrés laboral (10) coinciden con el recuento exacto.', ESTILO_LISTA)
        + parrafo('Variable reimputada afectada.', 'Entre las cinco reimputadas, solo cantidad_personas_cuida: 6 de 7 celdas. La celda restante conservó su valor global, como ya indicaba la sección 12.', ESTILO_LISTA)
        + parrafo('Otras nueve variables.', 'Se clasificaron sin cambio usando solo las celdas identificadas, y no se reimputaron. No se evaluó si, con la lista exacta, alguna habría cambiado esa clasificación.', ESTILO_LISTA)
        + parrafo('Qué se puede afirmar.', 'Esta revisión es documental: Random Forest no se volvió a ejecutar, por lo que el efecto de esta limitación no está medido.', ESTILO_LISTA))
    despues_de('Los modelos principales conservan los valores originales.', h17)
    despues_de('No hay indicios de que la imputación global haya inflado el rendimiento.',
               parrafo('Nota de revisión (H17).', 'Esta lectura corresponde a lo que se ejecutó: las cinco variables de la Tabla 4, con 6 de 7 celdas en cantidad_personas_cuida. No evalúa las celdas no identificadas de las otras nueve variables (sección 5.2).'))
    despues_de(' no pudo identificarse.',
               parrafo('Identificación incompleta (H17).', 'Las celdas imputadas no identificadas alcanzan a 10 variables (Tabla 4-bis). No afecta a los modelos principales, y su efecto sobre la sensibilidad no se midió.', ESTILO_LISTA))

    REVISADO.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(REVISADO, 'w', zipfile.ZIP_DEFLATED) as salida:
        for item in entrada.infolist():
            salida.writestr(item, xml.encode('utf-8') if item.filename == 'word/document.xml' else entrada.read(item.filename))
    print('Generado:', REVISADO)


def verificar():
    a, b = zipfile.ZipFile(ORIGINAL), zipfile.ZipFile(REVISADO)
    ta, tb = textos(a.read('word/document.xml').decode('utf-8')), textos(b.read('word/document.xml').decode('utf-8'))
    # Las líneas del índice pueden cambiar de número de página; todo lo demás debe seguir igual y en orden.
    def cuerpo(t):
        return [x.replace('\xa0', ' ').strip() for x in t if x.strip() and not INDICE.match(x)]
    pos, faltan = 0, []
    cb = cuerpo(tb)
    for x in cuerpo(ta):
        try:
            pos = cb.index(x, pos) + 1
        except ValueError:
            faltan.append(x[:100])
    media = lambda z: {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
    ha, hb = media(a), media(b)
    agregados = [x for x in cb if x not in set(cuerpo(ta))]
    print('párrafos originales ausentes o desordenados:', faltan)
    print('imágenes:', len(ha), len(hb), 'iguales:', sorted(ha.values()) == sorted(hb.values()))
    print('párrafos agregados:', len(agregados))
    if faltan or sorted(ha.values()) != sorted(hb.values()):
        sys.exit(1)


if __name__ == '__main__':
    verificar() if sys.argv[1:] == ['verificar'] else generar()
