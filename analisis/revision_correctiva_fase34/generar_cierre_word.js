// Informe de cierre y nota metodológica de la Fase 36, en Word. Lee tablas/ y escribe en informe/.
// Uso, desde la raíz, después de verificar_correccion.py:
//   NODE_PATH=<carpeta con node_modules de docx> node analisis/revision_correctiva_fase34/generar_cierre_word.js
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, AlignmentType,
  HeadingLevel, Footer, PageNumber, LevelFormat, PageOrientation, VerticalAlign, ImageRun } = require('docx');

const C = JSON.parse(fs.readFileSync(path.join(__dirname, 'tablas', 'cierre.json'), 'utf8'));
const AZUL = '1F4E79', CELESTE = 'DCE6F1', BORDE = 'BFBFBF', FUENTE = 'Arial';
const ANCHO = 9360, ANCHO_H = 13460;

function ricos(texto, base = {}) {
  return texto.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((t) => (t.startsWith('**')
    ? new TextRun({ text: t.slice(2, -2), bold: true, ...base }) : new TextRun({ text: t, ...base })));
}
const P = (t, o = {}) => new Paragraph({ children: ricos(t), spacing: { after: 120, line: 276 }, ...o });
const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1 });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2 });
const LI = (t) => new Paragraph({ children: ricos(t), numbering: { reference: 'vinetas', level: 0 }, spacing: { after: 70, line: 264 } });
const NUM = (t, ref) => new Paragraph({ children: ricos(t), numbering: { reference: ref, level: 0 }, spacing: { after: 80, line: 264 } });
const TIT = (t) => new Paragraph({ children: [new TextRun({ text: t, bold: true, size: 18, color: AZUL })], spacing: { before: 160, after: 60 }, keepNext: true });
const NOTA = (t) => new Paragraph({ children: ricos(t, { size: 16, italics: true, color: '595959' }), spacing: { before: 60, after: 160 } });
const ESPACIO = () => new Paragraph({ children: [], spacing: { after: 100 } });

function celda(texto, ancho, o = {}) {
  const b = { style: BorderStyle.SINGLE, size: 4, color: BORDE };
  return new TableCell({
    width: { size: ancho, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 70, right: 70 },
    borders: { top: b, bottom: b, left: b, right: b },
    shading: o.fondo ? { type: ShadingType.CLEAR, color: 'auto', fill: o.fondo } : undefined,
    children: [new Paragraph({ alignment: o.alinear || AlignmentType.LEFT, children: ricos(String(texto), { size: o.tam || 17, bold: o.negrita, color: o.color }) })],
  });
}
function tabla(cabeza, filas, anchos, o = {}) {
  return new Table({
    width: { size: anchos.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: anchos,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: cabeza.map((c, i) => celda(c, anchos[i], { fondo: AZUL, color: 'FFFFFF', negrita: true, tam: o.tam })) }),
      ...filas.map((f) => new TableRow({ cantSplit: true, children: f.map((c, i) => celda(c, anchos[i], { tam: o.tam, fondo: o.resaltar && o.resaltar(f) ? CELESTE : undefined })) })),
    ],
  });
}
function imagen(ruta, ancho) {
  const buf = fs.readFileSync(ruta);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  return new ImageRun({ type: 'png', data: buf, transformation: { width: ancho, height: Math.round(ancho * h / w) } });
}
const estilos = {
  default: { document: { run: { font: FUENTE, size: 20 } } },
  paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FUENTE, size: 28, bold: true, color: AZUL }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FUENTE, size: 23, bold: true, color: AZUL }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
  ],
};
const numeracion = {
  config: [
    { reference: 'vinetas', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] },
    ...['n1', 'n2', 'n3', 'n4'].map((reference) => ({ reference, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 440, hanging: 300 } } } }] })),
  ],
};
const pie = (texto) => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `${texto} · `, size: 15, color: '7F7F7F' }), new TextRun({ children: [PageNumber.CURRENT], size: 15, color: '7F7F7F' })] })] });
const PAG = { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } };
const PAG_H = { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1100, bottom: 1000, left: 1190, right: 1190 } };
const portada = (titulo, sub) => [
  new Paragraph({ children: [new TextRun({ text: titulo, bold: true, size: 40, color: AZUL })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: sub, size: 24, color: '404040' })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: 'AgingWomen · Conjunto sintético de usuarias · 4 de noviembre de 2026 · Documento para revisión', size: 18, color: '595959' })], spacing: { after: 240 } }),
];

// ====================================================================== informe de cierre
function cierre() {
  const FIG_H = path.join(__dirname, '..', 'figuras', 'eda_univariado', 'univariado_sobrecarga_fisica_emocional.png');
  const FIG_R = path.join(__dirname, 'figuras_34D_revisadas', 'univariado_sobrecarga_fisica_emocional.png');
  const sinBorde = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const imgCelda = (r, t) => new TableCell({
    width: { size: ANCHO / 2, type: WidthType.DXA }, borders: { top: sinBorde, bottom: sinBorde, left: sinBorde, right: sinBorde },
    children: [new Paragraph({ children: [new TextRun({ text: t, bold: true, size: 16 })], spacing: { after: 40 } }), new Paragraph({ children: [imagen(r, 300)] })],
  });
  const uno = [
    ...portada('Informe de cierre', 'Corrección controlada de la Fase 34'),
    H1('1. Resumen'),
    P(`**La corrección terminó sin alterar ningún resultado estadístico histórico y no hace falta recalcular Shannon, FCBF ni Random Forest.** Los ${C.protegidos} archivos protegidos conservan su SHA-256. De los ${C.linea_base} archivos de la línea base solo cambiaron 8 de código, con autorización, y únicamente en rótulos, textos y comentarios.`),
    P('Las correcciones están en versiones separadas: 5 informes revisados y 73 figuras nuevas. Los históricos no se sobrescribieron. No se hizo commit ni push, y las Fases 36 y 37 no comenzaron.'),
    P('**Queda una decisión necesaria antes de la Fase 36:** cómo representar los datos condicionales, incluidos los valores 3 de las 22 participantes con situación laboral imputada. La propuesta está en la nota metodológica aparte.'),
    H1('2. Respuestas a las preguntas de cierre'),
    H2('¿Qué errores se corrigieron?'),
    tabla(['Error', 'Antes', 'Ahora'], [
      ['H05. Denominador de «quienes trabajan»', '309, sin aclarar que incluye 22 imputadas', '309 = 287 con situación respondida o deducida + 22 imputadas, explicado en 34B, 34C, 34D y 34E'],
      ['H07. IMC por categoría', 'q = 0,073, mezclando «no informado» con categorías nutricionales', 'q histórico conservado, más cuadro complementario: solo observado, q por reemplazo = 0,038'],
      ['H10. Rótulos de 34D', '41 de las 46 figuras con imputadas decían «faltante = 0»', 'Rótulos que separan observadas, deducidas, imputadas, faltantes reales y no aplicables'],
      ['H11. Recuento de imputados', 'Cota sobre 546; difiere en 9 variables', 'Recuento exacto publicado como anexo. El código aún calcula la cota: ver las limitaciones'],
    ], [2700, 3000, 3660]),
    ESPACIO(),
    P('También se corrigieron los problemas documentales H12, H14, H15 y H16, en parte H13, y un hallazgo adicional, **A1**: la figura y el texto de horas sentada decían «valores observados» e incluían 27 imputadas. Este hallazgo no estaba entre los 17 y no altera su clasificación.'),
    H2('¿Qué decisiones metodológicas se conservaron?'),
    LI('**H02 y H03.** Las 22 imputaciones de trabajo y las 21 de cuidado se mantienen y quedan documentadas. No se reemplazó ningún valor por el del simulador.'),
    LI('**H04.** `doble_carga` sigue excluida; su dependencia de imputadas en 43 filas queda documentada.'.replace(/`/g, '')),
    LI('**H08.** La regla de mínimo 5 casos por grupo se mantiene; se declara que dejó fuera a bajo peso (n = 2).'),
    LI('**H09.** La codificación con 0 de la sobrecarga en 34C se mantiene y se explica: rho = 0,069 con las 529 y 0,156 entre cuidadoras.'),
    LI('**H01, ya verificado.** La exclusión de medicamentos para la diabetes del conjunto de 33 sigue vigente, igual que las de doble carga y previsión.'),
    LI('**Poblaciones.** Shannon y Random Forest siguen usando 287 y 239; el IMC numérico de la Fase 35 no cambia.'),
    H2('¿Qué hallazgos permanecen como limitaciones?'),
    tabla(['Limitación', 'Situación', 'Qué haría falta'], [
      ['H06. Valor 3 en lugar y estrés de las 22', 'Hoy no se usa, pero sigue en el conjunto de la Fase 35', 'Decidir su tratamiento antes de la Fase 36'],
      ['H17. Identificación incompleta en Random Forest', 'Documentada; su efecto sobre la sensibilidad no se midió', 'Medirlo exigiría reejecutar la sensibilidad, lo que no se autorizó'],
      ['H13. Rótulo de la etapa en el script de 34C', 'Sigue como «control» en el código. No entra al cálculo', 'Autorizar el cambio del rótulo si 34C vuelve a ejecutarse'],
      ['H11. Cota en el código de 34D', 'La columna imputados_34B sigue calculándose igual', 'Autorizar el cambio si 34D vuelve a ejecutarse'],
      ['H14. Figura de 34E', 'Sigue diciendo «38 predictoras»; el código adaptado de 34E no se ha ejecutado completo', 'Regenerarla exigiría ejecutar 34E'],
      ['A1. Forma de horas sentada', 'Asimetría y curtosis incluyen 27 imputadas; no se recalcularon', 'Decidir si se informa una versión solo observada'],
      ['Shannon sin imputadas', 'No se puede afirmar que trabaja_actualmente siga con q < 0,10 (hoy 0,089)', 'Exigiría calcular SU y permutaciones; no es necesario para conservar la decisión'],
      ['Informe de la Fase 35A', 'Sigue llamando «trabajadoras» a las 22: la corrección autorizada no lo incluía', 'Agregar una nota si se autoriza'],
      ['Figuras de frecuencias de 34C', 'Siguen mostrando «n trabaja = 298»; lo aclara el informe revisado', 'Solo si se quisiera regenerarlas'],
    ], [3000, 3400, 2960]),
    H2('¿Se alteró algún resultado estadístico?'),
    P(`**No.** Datos, coeficientes, valores p y q, SU, selección FCBF, métricas e importancias tienen el mismo SHA-256 que antes. Lo agregado son resultados complementarios del diagnóstico, identificados como tales: los q por reemplazo cambian una prueba y mantienen fijas las otras 40, y no son una nueva ejecución oficial.`),
    H2('¿Es necesario recalcular Shannon, FCBF o Random Forest?'),
    P('**No.** Las correcciones son de presentación y documentación, y ninguna cambia los datos ni las poblaciones que usan esos análisis. Solo sería necesario si se decidiera tratar las imputadas de trabajo o cuidado como faltantes, algo que no se propone. Las asociaciones casi no cambian sin ellas: 0,102 a 0,104 en trabajo y 0,016 a 0,018 en cantidad cuidada.'),
    H2('¿Qué falta resolver antes de la Fase 36?'),
    NUM('**Tratamiento de los datos condicionales.** Aprobar o cambiar la propuesta de segmentación general más módulos laboral y de cuidado.', 'n1'),
    NUM('**Población de sobrecarga.** Definir si el módulo usa 239 observadas (propuesta) o 251.', 'n1'),
    NUM('**IMC.** Decidir cómo probar su efecto en la segmentación, con 49,5 % imputado por la media.', 'n1'),
    NUM('**Validación con la profesora.** Las decisiones anteriores, la regla de etapa menopáusica y las dos familias de FDR.', 'n1'),
    NUM('**Cómo guardar esta corrección en Git.** Ver el aviso de la sección 5.', 'n1'),
  ];

  const tres = [
    H1('3. Diferencias principales entre la versión histórica y la corregida'),
    tabla(['Tema', 'Versión histórica', 'Versión corregida', 'Resultado'], [
      ['Limpieza, sección 6.3', '«Cambió por error 1», con una tabla que lista 197 celdas', '1 celda alterada por error y 196 por una regla de aplicabilidad', 'No hay 197 errores'],
      ['Imputaciones de trabajo y cuidado', 'Solo un recuento en la tabla general', 'Sección propia, con efectos sobre cantidad, doble carga y poblaciones', 'Valores sin cambios'],
      ['Diabetes', 'Una fila más entre los resultados', 'Nota: 66 y 463; 66,7 % y 51,2 %; rho +0,129; dominancia 87,5 %; fuera de las 33', 'Figura y coeficientes sin cambios'],
      ['IMC', 'Solo q = 0,073', 'Se agregan las alternativas: q entre 0,032 y 0,064 por categorías, 0,008 ordenado', 'q histórico conservado'],
      ['Sobrecarga', 'rho = 0,069, sin explicar', 'Se agrega 0,156 entre cuidadoras, con explicación', 'Shannon sin cambios'],
      ['Figura de sobrecarga', '«n válido = 251 · faltante = 0»', '«n = 251 cuidadoras: 239 respuestas observadas y 12 imputadas»', 'Barras iguales'],
      ['Informe 34E', '«Sin imputaciones»', 'Sin imputaciones nuevas, pero con las de la limpieza', 'Matrices sin cambios'],
      ['Listas de variables', '38 y 35, sin aclarar la lista vigente', '38 exploratorias, 35 de una versión previa, 33 vigentes', 'Sin cambios en las 33'],
      ['Random Forest', 'Mencionaba una celda no identificada', 'Identificación incompleta en 10 variables, con su alcance', 'Métricas sin cambios'],
    ], [2100, 2600, 3060, 1600]),
    ESPACIO(),
    TIT('Figura de sobrecarga: las barras no cambian, solo el rótulo'),
    new Table({ width: { size: ANCHO, type: WidthType.DXA }, columnWidths: [ANCHO / 2, ANCHO / 2], rows: [new TableRow({ children: [imgCelda(FIG_H, 'Histórica'), imgCelda(FIG_R, 'Revisada')] })] }),
    NOTA('Comprobación: con el rótulo antiguo, el código y las frecuencias históricas reproducen píxel a píxel las 71 figuras de barras. En las nuevas, cada barra se comparó con su frecuencia histórica.'),
  ];

  const cuatro = [
    H1('4. Hallazgos H01 a H17: estado antes y después'),
    tabla(['ID', 'Clase', 'Antes', 'Acción', 'Después'], C.hallazgos.map((h) => [h.id, h.clase, h.estado_antes, h.accion, h.estado_despues]), [620, 2050, 3500, 4090, 3200], { tam: 16 }),
    NOTA('La clasificación original se respeta: 4 errores comprobados, 7 decisiones metodológicas discutibles, 5 problemas documentales y 1 hallazgo verificado sin error. A1 se detectó durante la corrección.'),
  ];

  const catalogo = { 'Figura revisada': 'figuras_34D_revisadas/', 'Informe revisado': 'informes_revisados/ (4 .md y 1 .docx)', 'Entregable Word': 'informe/', Tabla: 'tablas/', Manifiesto: 'manifiestos/', 'Script de la corrección': 'carpeta principal de la revisión' };
  const cinco = [
    H1('5. Archivos modificados y creados'),
    TIT('Archivos de código modificados, con autorización'),
    tabla(['Archivo', 'Qué cambió'], C.codigo.map((x) => [x.ruta.replace('analisis/', ''), x.motivo]), [4400, 4960]),
    NOTA('Fuera de eda/univariado.py, los cambios son textos y comentarios. En univariado.py se agregó la construcción del rótulo; describir() y todo el cálculo no cambian. Ninguno se ejecutó en su flujo completo.'),
    TIT('Archivos creados, todos dentro de analisis/revision_correctiva_fase34/'),
    tabla(['Tipo', 'Cantidad', 'Ubicación'], Object.entries(C.creados).map(([k, v]) => [k, v, catalogo[k] || ''] ), [3400, 1100, 4860]),
    NOTA('La lista completa, con la relación entre cada original y su versión revisada, está en tablas/relacion_archivos.csv, tablas/relacion_figuras_34D.csv y tablas/relacion_correcciones.csv.'),
    TIT('Avisos antes de volver a ejecutar o de hacer un commit'),
    LI('**eda_univariado.py borra las figuras históricas** antes de redibujarlas. Por eso las nuevas se generaron con otro programa. Tampoco deben ejecutarse eda_usuaria.py ni limpiar_dataset.py sin revisar: regeneran informes históricos.'),
    LI('**complementario_fase35b.py exige que los archivos versionados no tengan cambios y que HEAD sea 745d689.** Con estos 8 archivos modificados, y también tras un commit, se detendría antes de ejecutar. Ese programa no necesita volver a correr; si alguna vez hiciera falta, habría que ajustar esa condición con autorización.'),
    H1('6. Verificación de integridad'),
    P(`Se distinguen dos grupos: **${C.protegidos} archivos protegidos**, que no cambian, y **8 archivos de código** cuya actualización se autorizó. No todo el repositorio está intacto: también existen los archivos nuevos de la carpeta de revisión, que el manifiesto excluye a propósito.`),
    tabla(['Comprobación', 'Resultado', 'Detalle'], C.integridad.map((x) => [x.comprobacion, x.resultado, x.detalle.length > 70 ? `${x.detalle.split(',').length} archivos` : x.detalle]), [5500, 900, 2960], { tam: 16 }),
    NOTA(`SHA-256 de dataset_fase35_33_variables.csv: ${C.hash33}. Conjunto limpio: ${C.hash_limpio}. HEAD: ${C.head}.`),
    P('**Pruebas.** Pasan las 8 pruebas nuevas de esta corrección (rótulos, recuentos, tamaño de los textos y enlaces) y las 108 de Shannon, FCBF y revisión de 33 variables. La verificación visual fue por muestra: 6 figuras nuevas y parte de las páginas modificadas del Word de Random Forest. Los rótulos de las 71 figuras de barras se comprobaron por programa. El Word de Random Forest conserva todos sus párrafos originales y sus 10 imágenes; su índice se actualizó.'),
    H1('7. Cómo reproducir'),
    P('Desde la raíz del proyecto, en analisis/revision_correctiva_fase34/: origen_respuestas.py, generar_figuras_34D.py, generar_informes_revisados.py, generar_informe_rf_revisado.py y verificar_correccion.py. Ninguno modifica datos, entrena modelos ni ejecuta el EDA completo.'),
  ];
  return new Document({
    creator: 'AgingWomen', title: 'Informe de cierre: corrección controlada de la Fase 34', styles: estilos, numbering: numeracion,
    sections: [
      { properties: { page: PAG }, footers: { default: pie('Cierre de la corrección de la Fase 34') }, children: [...uno, ...tres] },
      { properties: { page: PAG_H }, footers: { default: pie('Cierre de la corrección de la Fase 34') }, children: cuatro },
      { properties: { page: PAG }, footers: { default: pie('Cierre de la corrección de la Fase 34') }, children: cinco },
    ],
  });
}

// ====================================================================== nota de la Fase 36
function nota36() {
  const hijos = [
    ...portada('Nota metodológica para la Fase 36', 'Propuesta de tratamiento de los datos condicionales'),
    P('**Esta nota es una propuesta para decidir; no implementa la Fase 36.** No se eliminaron variables ni se generaron matrices de modelado.'),
    H1('1. Recomendación'),
    P('**Formar los perfiles con las 30 variables generales de las 529 participantes, y tratar las 2 variables laborales y la de sobrecarga como módulos aparte, solo en su población.** Así, un valor que significa «no aplica» nunca se usa como si fuera una respuesta, y toda usuaria nueva puede recibir un perfil, trabaje o no y cuide o no.'),
    H1('2. El problema'),
    tabla(['Variable', 'Valor', 'Qué significa realmente', 'Riesgo'], [
      ['Lugar y estrés laboral', '0 en 220 mujeres que no trabajan', 'No aplica; está fuera de la escala 1 a 5', 'PCA o K-means lo leerían como el extremo más bajo de la escala'],
      ['Lugar y estrés laboral', '3 en las 22 con situación laboral imputada', 'Mediana asignada: no respondieron', 'Parecería una respuesta «neutral» real'],
      ['Lugar y estrés laboral', '16 y 10 imputados dentro de las 287', 'Imputación de la limpieza, también en 3', 'En lugar, 38 de los 130 valores 3 no son respuestas'],
      ['Sobrecarga', '12 imputadas; no está en dataset_fase35_33_variables.csv', 'Solo aplica a cuidadoras; se toma del conjunto limpio', 'Hay que definir su población y su unión con el resto'],
      ['Cantidad de personas que cuida', '0 en 278', 'Valor real de la escala, salvo 21 con «No cuida» imputado', 'Se conserva, pero depende de imputadas'],
      ['Frecuencias de ejercicio', '0', 'Valor real: no lo realiza', 'No es «no aplica»; no debe tratarse igual'],
    ], [2300, 2360, 2500, 2200]),
    ESPACIO(),
    P('Además, el archivo de 33 variables contiene las columnas prevision y doble_carga, que no son elegibles. La Fase 36 debe seleccionar columnas por una lista explícita, nunca «todas las del archivo».'),
    H1('3. Alternativas comparadas'),
    tabla(['Alternativa', 'Qué hace', 'A favor', 'En contra', 'Evaluación'], [
      ['A. Una matriz con las 33 y los códigos actuales', 'Usa los 0 y 3 tal como están', 'Es lo más simple', 'Trata «no aplica» como cantidad; los perfiles pueden separar solo a quien trabaja o cuida; incluye respuestas no observadas', 'Descartar'],
      ['B. 30 generales + módulos', 'Perfiles con las 30. Laboral en 287 y sobrecarga en 239, por separado', 'Respeta la aplicabilidad; usa las 529; simple para la plataforma', 'Las 3 variables no ayudan a formar perfiles. trabaja_actualmente mantiene 22 imputadas', 'Recomendada'],
      ['C. «No aplica» como categoría, con FAMD', 'Las 3 variables pasan a categóricas, con niveles «no aplica» y, para las 22, «sin respuesta»', 'Conserva las 33 y es explícita', 'Repite la información de trabajar o cuidar; un nivel raro (n = 22) pesa mucho en FAMD; no sirve para PCA', 'Sensibilidad'],
      ['D. Segmentar por separado cada población', 'Perfiles distintos para trabajadoras, cuidadoras y resto', 'Usa todas las variables en cada grupo', 'Las poblaciones se solapan (130 en ambas); grupos más pequeños y perfiles difíciles de comparar y asignar', 'No como principal'],
    ], [1900, 2100, 1760, 2600, 1000], { tam: 16 }),
    H1('4. Cómo funcionaría la propuesta'),
    LI('**Capa general.** Las 30 variables, en las 529. Es la capa donde se comparan PCA y FAMD, y luego K-means y jerárquico aglomerativo.'),
    LI('**Módulo laboral.** Lugar y estrés, solo en las 287, con 263 de ambas respuestas observadas como sensibilidad. Las 22 participan en los perfiles generales, pero no en este módulo.'),
    LI('**Módulo de cuidado.** Sobrecarga, solo en las 239 observadas, con 251 como sensibilidad.'),
    LI('**Uso de los módulos.** Con 1 o 2 variables no conviene formar clústeres. Se describen dentro de cada perfil y sirven para reglas de asociación condicionadas a esa población en la Fase 38.'),
    LI('**MRS.** No forma los perfiles. Queda reservado para caracterizarlos y para las reglas, sujeto al protocolo de la Fase 36.'),
    H1('5. Cómo garantizar una representación correcta'),
    TIT('Reglas para PCA y FAMD'),
    tabla(['Tipo de variable', 'PCA', 'FAMD'], [
      ['Numérica (edad, IMC, horas)', 'Escalada; robusta si hay asimetría o colas pesadas', 'Cuantitativa, escalada'],
      ['Ordinal (hábitos)', 'Numérica ordenada, supuesto que debe declararse', 'Cuantitativa o categórica: decisión previa, igual en todos los análisis'],
      ['Binaria', '0 y 1', 'Categórica'],
      ['Nominal (quién prepara las comidas)', 'One-hot, cuidando su peso total', 'Categórica'],
    ], [3200, 3200, 2960]),
    ESPACIO(),
    TIT('Controles antes de aceptar una matriz'),
    NUM('Lista de 30 variables comprobada contra la lista de la Fase 35B; sin prevision, doble_carga, medicamentos para la diabetes ni MRS.', 'n2'),
    NUM('Ninguna columna con un código de «no aplica» tratado como cantidad: lugar y estrés quedan fuera de la capa general.', 'n2'),
    NUM('Indicadores de auditoría e imc_fue_imputado fuera de la matriz.', 'n2'),
    NUM('Parámetros de imputación, codificación y escalado ajustados una vez y guardados, para aplicarlos sin cambios a usuarias nuevas.', 'n2'),
    NUM('Misma matriz y mismas participantes para comparar K-means y aglomerativo.', 'n2'),
    TIT('Sensibilidades que conviene planificar'),
    LI('**IMC.** 262 de 529 valores (49,5 %) son la misma media: comparar los perfiles con y sin IMC.'),
    LI('**Trabajo y cuidado imputados.** Comparar los perfiles con y sin las 22 y las 21 participantes, de forma descriptiva y usando solo indicadores de auditoría.'),
    LI('**Alternativa C.** Comprobar si los perfiles cambian al incluir los niveles de «no aplica» en FAMD.'),
    H1('6. Compatibilidad con lo que sigue'),
    tabla(['Requisito', 'Cómo lo cumple la propuesta'], [
      ['Comparar K-means y aglomerativo', 'Ambos usan la misma matriz y las mismas métricas: silueta, Davies-Bouldin, Calinski-Harabasz, estabilidad y coherencia de perfiles.'],
      ['Asignar perfil a una usuaria nueva', 'Se aplican los parámetros guardados y la proyección de PCA o FAMD. Con K-means, se elige el centroide más cercano.'],
      ['Aglomerativo sin predicción directa', 'Se calcula el centro de cada clúster y se asigna al más cercano. Debe evaluarse si esa regla reproduce los clústeres antes de elegir este método.'],
      ['Preguntas condicionales en la plataforma', 'Quien no trabaja o no cuida no responde esos módulos, y su perfil general se calcula igual.'],
      ['Respuestas vacías en la plataforma', 'Usa los valores de imputación guardados y deja registro de cuáles se imputaron.'],
      ['Sin GMM', 'La propuesta no los usa.'],
    ], [3200, 6160]),
    H1('7. Decisiones que se necesitan'),
    NUM('**¿Se aprueba la alternativa B como principal y la C como sensibilidad?** Recomendado. Es el cambio con mayor efecto sobre la Fase 36.', 'n3'),
    NUM('**¿La sobrecarga se analiza en 239 o en 251?** Se propone 239, igual que Shannon y Random Forest, con 251 como sensibilidad.', 'n3'),
    NUM('**¿Las 22 siguen en los perfiles generales?** Se propone que sí: sus demás variables siguen el mismo tratamiento que las del resto. Su situación laboral imputada queda identificada en los indicadores de auditoría.', 'n3'),
    NUM('**¿Las ordinales se tratan como cuantitativas en FAMD?** Se propone definirlo en el protocolo de la Fase 36, antes de ver los resultados.', 'n3'),
    NOTA('Limitación: en un conjunto sintético, buena parte de los hábitos se generó de forma casi independiente (34E), así que PCA y FAMD podrían explicar poca varianza con pocas componentes. Eso se comprobará en la Fase 37A, no aquí.'),
  ];
  return new Document({ creator: 'AgingWomen', title: 'Nota metodológica para la Fase 36', styles: estilos, numbering: numeracion,
    sections: [{ properties: { page: PAG }, footers: { default: pie('Nota metodológica para la Fase 36') }, children: hijos }] });
}

(async () => {
  const dir = path.join(__dirname, 'informe');
  fs.writeFileSync(path.join(dir, 'informe_cierre_correccion_fase34.docx'), await Packer.toBuffer(cierre()));
  fs.writeFileSync(path.join(dir, 'nota_metodologica_fase36.docx'), await Packer.toBuffer(nota36()));
  console.log('Generados en', dir);
})();
