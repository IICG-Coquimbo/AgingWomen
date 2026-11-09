// Informe de diagnóstico en Word. Solo lee tablas/ y escribe en informe/.
// Uso, desde la raíz: NODE_PATH=<carpeta con node_modules de docx> node analisis/revision_correctiva_fase34/generar_informe_word.js
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, AlignmentType,
  HeadingLevel, Footer, PageNumber, LevelFormat, PageOrientation, VerticalAlign, TableOfContents } = require('docx');

const T = JSON.parse(fs.readFileSync(path.join(__dirname, 'tablas', 'tablas.json'), 'utf8'));
const C = JSON.parse(fs.readFileSync(path.join(__dirname, 'tablas', 'comparacion_manifiestos.json'), 'utf8'));
const R = T.resumen;
const AZUL = '1F4E79', GRIS = 'F2F2F2', CELESTE = 'DCE6F1', BORDE = 'BFBFBF', FUENTE = 'Arial';
const ANCHO = 9360, ANCHO_H = 13460;

const num = (x, d = 1) => (x === null || x === undefined || Number.isNaN(x)) ? '—' : Number(x).toFixed(d).replace('.', ',');
const ent = (x) => (x === null || x === undefined) ? '—' : String(Math.round(x));
const pv = (x) => (x === null || x === undefined) ? '—' : (x < 0.001 ? '< 0,001' : num(x, 3));

function ricos(texto, base = {}) {
  // **negrita** dentro del texto
  return texto.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((t) => t.startsWith('**')
    ? new TextRun({ text: t.slice(2, -2), bold: true, ...base }) : new TextRun({ text: t, ...base }));
}
const P = (t, o = {}) => new Paragraph({ children: ricos(t), spacing: { after: 120, line: 276 }, ...o });
const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1 });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2 });
const LI = (t) => new Paragraph({ children: ricos(t), numbering: { reference: 'vinetas', level: 0 }, spacing: { after: 70, line: 264 } });
const NUM = (t, ref = 'numeros') => new Paragraph({ children: ricos(t), numbering: { reference: ref, level: 0 }, spacing: { after: 80, line: 264 } });
const TIT = (t) => new Paragraph({ children: [new TextRun({ text: t, bold: true, size: 18, color: AZUL })], spacing: { before: 160, after: 60 }, keepNext: true });
const NOTA = (t) => new Paragraph({ children: ricos(t, { size: 16, italics: true, color: '595959' }), spacing: { before: 60, after: 160 } });

function celda(texto, ancho, o = {}) {
  const bordes = { style: BorderStyle.SINGLE, size: 4, color: BORDE };
  return new TableCell({
    width: { size: ancho, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    borders: { top: bordes, bottom: bordes, left: bordes, right: bordes },
    shading: o.fondo ? { type: ShadingType.CLEAR, color: 'auto', fill: o.fondo } : undefined,
    children: [new Paragraph({
      alignment: o.alinear || AlignmentType.LEFT,
      children: ricos(String(texto), { size: o.tam || 16, bold: o.negrita, color: o.color }),
    })],
  });
}
function tabla(cabeza, filas, anchos, o = {}) {
  const total = anchos.reduce((a, b) => a + b, 0);
  const num_ = o.numericas || [];
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: anchos,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: cabeza.map((c, i) => celda(c, anchos[i], { fondo: AZUL, color: 'FFFFFF', negrita: true, tam: o.tam })) }),
      ...filas.map((f) => new TableRow({ cantSplit: true, children: f.map((c, i) => celda(c, anchos[i], {
        alinear: num_.includes(i) ? AlignmentType.RIGHT : AlignmentType.LEFT, tam: o.tam, fondo: o.resaltar && o.resaltar(f) ? CELESTE : undefined,
      })) })),
    ],
  });
}

// ------------------------------------------------------------------ datos
const dd = T.diabetes_tabla_cruzada, dp = T.diabetes_pruebas, D = R.diabetes;
const S = T.sensibilidad_asociaciones;
const sens = (v) => S.filter((x) => x.variable === v).map((x) => [x.escenario, ent(x.n), num(x.rho, 3), pv(x.p_sin_ajustar), x.q_familia_41 == null ? '—' : pv(x.q_familia_41)]);
const SEV = ['Sin síntomas o muy leves', 'Leve', 'Moderada', 'Severa'];
const clases = (x) => SEV.map((s) => `${x[`${s}_n`]} (${num(x[`${s}_pct`])} %)`);

const hijos = [];
const add = (...x) => hijos.push(...x);

// ------------------------------------------------------------------ portada breve
add(new Paragraph({ children: [new TextRun({ text: 'Revisión correctiva de la Fase 34', bold: true, size: 40, color: AZUL })], spacing: { after: 60 } }));
add(new Paragraph({ children: [new TextRun({ text: 'Diagnóstico, tablas de sensibilidad y plan de correcciones mínimas', size: 24, color: '404040' })], spacing: { after: 60 } }));
add(new Paragraph({ children: [new TextRun({ text: 'AgingWomen · Conjunto sintético de usuarias · 4 de noviembre de 2026 · Documento de trabajo para revisión', size: 18, color: '595959' })], spacing: { after: 240 } }));

add(H1('1. Resumen'));
add(P(`**Ningún hallazgo obliga a recalcular Shannon, FCBF ni Random Forest, y los ${C.archivos_antes} archivos protegidos quedaron idénticos.** El análisis de la Fase 34 es aritméticamente correcto en lo revisado. Lo que hay son 4 errores de presentación o de una prueba puntual, 7 decisiones metodológicas discutibles y 5 problemas documentales.`));
add(P('**Una decisión debe tomarse antes de la Fase 36:** cómo tratar los valores `3` que tienen en lugar y estrés laboral las 22 personas con trabajo imputado. Hoy nadie los usa, pero entrarían al análisis si esas columnas se usan con las 529 participantes.'.replace(/`/g, '')));
add(TIT('Tabla 1. Respuestas a las preguntas de la revisión'));
add(tabla(['Pregunta', 'Resultado', 'Conclusión'], [
  ['¿La asociación de diabetes es real?', `Sí. Severas: ${num(dd[0].severas_pct)} % en «Sí» (n = ${dd[0].n}) y ${num(dd[1].severas_pct)} % en «No» (n = ${dd[1].n}). Rho ${num(dp[0].rho_severidad_4, 3)}; q ${num(D.q_familia_principal, 3)}.`, 'Codificación y FDR correctos. La exclusión por dominancia se mantiene.'],
  ['¿Cambia la asociación de trabaja actualmente?', 'Rho 0,102 frente a 0,104 sin las 22 imputadas; q 0,073 en ambos casos.', 'No cambia en esta medida. No se recalculó SU.'],
  ['¿Alguna población quedó mal definida?', 'En la Fase 35, no: 287 y 239 coinciden con el simulador. En 34C y 34D, «quienes trabajan» (309) incluye 12 personas que no trabajan según el simulador.', 'Fase 35B correcta, aunque incompleta. Denominador de 34C y 34D por aclarar.'],
  ['¿Qué pasa con el IMC en categorías?', 'Con «no informado»: p 0,020 y q 0,073. Solo observado: p 0,007 y q 0,038.', 'Error en la prueba de 34C. La Fase 35 no se afecta.'],
  ['¿Las figuras presentan imputados como observados?', `Sí, en ${R.figuras.con_imputadas} de ${R.figuras.evaluadas} variables revisadas; ${R.figuras.faltante_cero_con_imputadas} dicen «faltante = 0».`, 'Error de presentación. Los porcentajes están bien calculados.'],
  ['¿Los resultados de la Fase 35 siguen intactos?', `Sí. ${C.archivos_despues} archivos sin cambios y 17 de 17 comprobaciones correctas.`, 'No hay impacto mientras no se autorice una corrección.'],
], [2500, 3960, 2900]));

add(P(''));
add(H1('2. Cómo se hizo'));
add(LI(`**Imputaciones.** Se repitió la limpieza 34B en memoria y se capturó el conjunto justo antes de imputar. El resultado coincide con el archivo: ${R.reconstruccion.celdas_distintas} celdas distintas en ${R.reconstruccion.filas_disco} filas. Así, cada celda quedó clasificada como respondida, deducida o imputada, sin depender de marcas.`));
add(LI(`**Asociaciones.** Se volvieron a calcular las ${R.familia.n_principal} pruebas de la familia principal de 34C. Coinciden con el archivo guardado salvo redondeo (diferencia máxima en q: ${R.familia.max_dif_q.toExponential(1).replace('.', ',')}).`));
add(LI('**Versión verdadera del simulador.** Se usó solo para saber cuántas imputaciones acertaron. No corrige ni selecciona ninguna respuesta. En datos reales esa información no existiría.'));
add(LI('**Lo que no se hizo.** No se calcularon SU ni permutaciones, no se entrenó Random Forest, no se ejecutó el EDA y no se generaron figuras. Por eso no hay un SU alternativo para trabaja actualmente: su impacto se evalúa con Spearman y chi².'));
add(P('**Cómo leer p y q.** El valor p evalúa una prueba por sí sola. El valor q corrige por haber hecho muchas pruebas (Benjamini-Hochberg). Una q «con reemplazo» cambia solo la p de esa variable y mantiene las otras 40: es una aproximación descriptiva, no un resultado oficial.'));

// ------------------------------------------------------------------ diabetes
add(H1('3. Medicamentos para la diabetes'));
add(P('**Conclusión: la asociación es correcta y no contradice la dominancia.** Son dos preguntas distintas: la dominancia mide cuánto se reparten las respuestas; la asociación mide si los grupos difieren en severidad.'));
add(TIT('Tabla 2. Tabla cruzada con la severidad'));
add(tabla(['Base', 'Grupo', 'n', 'Severas (MRS ≥ 16)', 'Sin síntomas o muy leves', 'Leve', 'Moderada', 'Severa', 'MRS media', 'MRS mediana', 'Obs.', 'Imp.'],
  dd.map((x) => [x.base, x.grupo, ent(x.n), `${x.severas_n} (${num(x.severas_pct)} %)`, ...clases(x), num(x.mrs_media), num(x.mrs_mediana), ent(x.observadas), ent(x.imputadas)]),
  [800, 480, 430, 900, 950, 880, 930, 930, 560, 660, 430, 410], { tam: 14, numericas: [2, 8, 9, 10, 11] }));
add(NOTA('Obs.: respuestas observadas. Imp.: imputadas. En esta variable, «Severas» y la clase «Severa» coinciden porque ambas son MRS ≥ 16.'));
add(TIT('Tabla 3. Pruebas de asociación'));
add(tabla(['Base', 'n', 'Rho con severidad (4 clases)', 'p sin ajustar', 'q (familia de 41)', 'Rho con MRS total', 'Odds ratio de severo', 'p de Fisher'],
  dp.map((x) => [x.base, ent(x.n), num(x.rho_severidad_4, 3), pv(x.p_sin_ajustar), num(x.q_familia_41, 3), num(x.rho_mrs_total, 3), num(x.odds_ratio_severo, 2), pv(x.p_fisher_severo)]),
  [1500, 600, 1350, 1000, 1100, 1160, 1350, 1300], { numericas: [1, 2, 3, 4, 5, 6, 7] }));
add(NOTA('La q de la fila «Solo observadas» es con reemplazo: solo cambia la p de diabetes.'));
add(H2('Comprobaciones'));
add(LI(`**Codificación.** Correcta: «Sí» = ${D.codigo_si} y «No» = ${D.codigo_no}, por lo que un rho positivo significa más severidad con medicamentos. Las variantes escritas del conjunto sucio («sí», «no», «N», «No») quedaron en la categoría correcta.`));
add(LI(`**Familia y FDR.** Benjamini-Hochberg sobre las ${R.familia.n_principal} pruebas de la familia principal. Diabetes tiene el rango ${D.rango_bh}: ${num(D.p_original, 5)} × ${R.familia.n_principal} / ${D.rango_bh} = ${num(D.q_verificado_a_mano, 5)}, igual al valor guardado. Si se uniera la familia secundaria (51 pruebas), q sería ${num(D.q_familia_conjunta_51, 3)}.`));
add(LI(`**Imputadas.** Son ${D.imputadas_529}, todas como «No». La columna del resumen 34D dice ${D.imputados_resumen_34D} porque cuenta sobre 546 filas (hallazgo H11). Según el simulador, ${D.imputadas_erroneas_segun_verdad} de esas ${D.imputadas_529} eran «Sí».`));
add(LI(`**Dominancia.** ${num(D.dominancia_todas, 2)} % con todas y ${num(D.dominancia_observadas, 2)} % solo con observadas: sigue sobre 85 %, así que la exclusión no depende de la imputación.`));
add(LI(`**Shannon.** En la revisión de 34 variables con 50.000 permutaciones: SU ${num(D.su_34, 4)}, p ${num(D.p_shannon_50000, 3)}, q ${num(D.q_shannon_34, 3)}. No llega a q < 0,10. No contradice el q 0,020 del EDA: son otra medida y otra familia.`));
add(H2('En lenguaje sencillo'));
add(P(`Imagine dos grupos: 66 personas que usan estos medicamentos y 463 que no. Que el grupo «Sí» sea pequeño no impide compararlos. Basta con que 66 personas sean suficientes para notar la diferencia: ${num(dd[0].severas_pct, 0)} % de severas frente a ${num(dd[1].severas_pct, 0)} %, y MRS de 20,5 frente a 15,8.`));
add(P('El problema de la dominancia es otro: una variable casi constante aporta poca información para separar grupos en modelos y clústeres, porque casi todas las personas tienen el mismo valor. Una variable puede estar asociada y aun así servir poco para segmentar. Por eso ambos resultados son compatibles.'));
add(P('**Precaución.** El simulador programó este efecto (`diabetes`: 0,38 en el dominio físico, en parametros.py). El resultado muestra que el análisis lo detecta, no que exista como hallazgo clínico. Además, el grupo «Sí» tiene más edad (54,2 frente a 50,5 años), y esta comparación no ajusta por ello.'.replace(/`/g, '')));

// ------------------------------------------------------------------ imputaciones
add(H1('4. Imputaciones de trabajo y cuidados'));
add(P('**Conclusión: las imputaciones casi no mueven las asociaciones y no definen mal ninguna población de la Fase 35.** El problema real es de transparencia: no llevan marca porque faltaba menos del 5 %, la regla de la limpieza.'));
add(TIT('Tabla 4. Situación de cada respuesta entre las 529'));
const ig = T.imputacion_grupos;
add(tabla(['Variable', 'Situación · valor', 'n', 'Severas', 'MRS media', 'Coincide con simulador', 'Distinta'],
  ig.map((x) => [x.variable === 'trabaja_actualmente' ? 'Trabaja' : 'Cuida', x.grupo, ent(x.n), `${x.severas_n} (${num(x.severas_pct)} %)`, num(x.mrs_media), ent(x.coincide_con_verdad), ent(x.distinta_de_verdad)]),
  [1100, 2500, 700, 1560, 1000, 1500, 1000], { numericas: [2, 4, 5, 6], resaltar: (f) => f[1].startsWith('Imputada') }));
add(NOTA('Deducida: estaba vacía, pero la persona respondió preguntas que solo se muestran a quien trabaja o cuida. Es lógica, no imputación. La columna del simulador es solo diagnóstico.'));
add(TIT('Tabla 5. Sensibilidad de trabaja actualmente: asociación con severidad (4 clases)'));
add(tabla(['Escenario', 'n', 'Rho', 'p sin ajustar', 'q con reemplazo'], sens('trabaja_actualmente'), [4560, 800, 1000, 1400, 1600], { numericas: [1, 2, 3, 4] }));
add(TIT('Tabla 6. Sensibilidad de trabaja actualmente: comparación de grupos'));
add(tabla(['Escenario', 'n trabaja', 'n no trabaja', 'Severas trabaja', 'Severas no trabaja', 'MRS trabaja', 'MRS no trabaja', 'p de chi² sin ajustar'],
  T.sensibilidad_trabaja_grupos.map((x) => [x.escenario, ent(x.n_trabaja), ent(x.n_no_trabaja), `${num(x.severas_trabaja_pct)} %`, `${num(x.severas_no_trabaja_pct)} %`, num(x.mrs_media_trabaja), num(x.mrs_media_no_trabaja), pv(x.chi2_p_sin_ajustar)]),
  [2560, 800, 900, 1000, 1000, 900, 1000, 1200], { numericas: [1, 2, 3, 4, 5, 6, 7] }));
add(NOTA('«Hipótesis: imputadas = No» es una cota para probar la dirección contraria. No es una corrección.'));
add(TIT('Tabla 7. Sensibilidad de las variables vinculadas'));
const vinc = ['cuida_otras_personas', 'doble_carga', 'cantidad_personas_cuida', 'sobrecarga_fisica_emocional', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral'];
const nombreV = { cuida_otras_personas: 'Cuida', doble_carga: 'Doble carga', cantidad_personas_cuida: 'Cantidad que cuida', sobrecarga_fisica_emocional: 'Sobrecarga', lugar_trabajo_comprensivo: 'Lugar comprensivo', estres_entorno_laboral: 'Estrés laboral' };
add(tabla(['Variable', 'Escenario', 'n', 'Rho', 'p sin ajustar', 'q con reemplazo'],
  vinc.flatMap((v) => sens(v).map((f) => [nombreV[v], ...f])), [1500, 3760, 600, 900, 1100, 1500], { numericas: [2, 3, 4, 5] }));
add(NOTA('«—» en q: esa prueba no forma parte de la familia de 41 de la Fase 34C, así que no se le asigna un q.'));
add(TIT('Tabla 8. Poblaciones y diagnóstico con el simulador'));
add(tabla(['Población', 'n', 'Simulador: Sí', 'Simulador: No', 'Uso'],
  T.poblaciones.map((x) => [x.poblacion.trim(), ent(x.n), ent(x.segun_simulador_si), ent(x.segun_simulador_no), x.nota || '']),
  [3660, 700, 1000, 1000, 3000], { numericas: [1, 2, 3], resaltar: (f) => /Imputada|No imputada/.test(f[0]) }));
add(H2('Qué significan estos resultados'));
const I = R.imputacion;
add(LI('**Trabaja actualmente.** Sin las 22 imputadas, rho pasa de 0,102 a 0,104 y q sigue en 0,073. Aun suponiendo que todas valieran «No», rho es 0,097 y q 0,093. La dirección se mantiene en todos los escenarios.'));
add(LI('**Población laboral (287).** Las 287 trabajan según el simulador. Quedan fuera 10 personas que sí trabajan y no respondieron esa sección: está incompleta, no mal definida.'));
add(LI('**Población de cuidadoras (251 y 239).** Todas cuidan según el simulador. Las 14 cuidadoras imputadas como «No» quedan fuera. Describe a quienes se identifican como cuidadoras y respondieron.'));
add(LI(`**Cantidad de personas que cuida.** Las 21 imputadas tienen cantidad 0; según el simulador, 14 sí cuidan. Otras ${I.cantidad_imputadas} tienen cantidad imputada. Rho pasa de 0,016 a 0,018, sin asociación en ningún escenario.`));
add(LI(`**Doble carga.** ${I.doble_con_alguna_imputada} filas dependen de una imputada: 22 de trabajo y 21 de cuidado, sin solapamiento. Difiere del simulador en ${I.doble_distinta_de_verdad}: ${I.doble1_mal} valores 1 y ${I.doble0_mal} valores 0. Sigue fuera de las 33.`));
add(LI('**Sobrecarga.** Es el único caso donde la forma de codificar sí cambia la lectura. Con las 529, y 0 para quien no cuida, rho es 0,069. Entre cuidadoras es 0,156 (p sin ajustar 0,013). Ese cambio no viene de las imputadas: con 239 observadas sigue en 0,156. Shannon ya la evalúa en 239, sin este efecto.'));
add(P('**Un riesgo para la Fase 36.** En dataset_fase35_33_variables.csv, las 22 personas tienen lugar = 3 y estrés = 3, y las 220 que no trabajan tienen 0. La Fase 35B y Random Forest usan esas columnas solo en las 287, por lo que no les afecta. Si la Fase 36 las usa con las 529, habría 22 valores «neutral» sin respuesta, y 12 de esas personas no trabajan según el simulador.'));
add(P('**Random Forest.** Trabaja actualmente, con sus imputadas, entra en A, B, D0, D1 y sus derivados. La sensibilidad de imputación ya hecha no cubre esta variable. No se recomienda repetir modelos: la asociación descriptiva casi no cambia y Random Forest es complementario.'));

// ------------------------------------------------------------------ IMC
add(H1('5. IMC en la Fase 34C'));
add(P('**Conclusión: la prueba mezcló dos preguntas y por eso pareció no significativa.** «¿Faltar el dato se relaciona con la severidad?» y «¿la categoría nutricional se relaciona con la severidad?» deben responderse por separado. La Fase 35 usa IMC numérico imputado por la media y no se toca.'));
add(H2('Pregunta 1: los datos faltantes'));
add(TIT('Tabla 9. Severidad según si informó peso y talla'));
const fila4 = (x) => [x.grupo, ent(x.n), `${x.severas_n} (${num(x.severas_pct)} %)`, ...clases(x), num(x.mrs_media), num(x.mrs_mediana)];
const cab4 = ['Grupo', 'n', 'Severas', 'Sin síntomas o muy leves', 'Leve', 'Moderada', 'Severa', 'MRS media', 'MRS mediana'];
const anch4 = [1400, 500, 1100, 1250, 1050, 1050, 1110, 900, 1000];
add(tabla(cab4, T.imc_faltante_descriptivo.map(fila4), anch4, { tam: 15, numericas: [1, 7, 8] }));
add(NOTA(`p de chi² sin ajustar ${num(R.imc.chi_faltante_p, 3)}; p de Mann-Whitney sin ajustar ${num(R.imc.mw_faltante_p, 3)}. Quien no informó tiene una severidad casi igual a quien sí informó. Esto es una descripción, no una prueba de que los faltantes sean al azar.`));
add(H2('Pregunta 2: las categorías nutricionales'));
add(TIT('Tabla 10. Severidad por categoría'));
add(tabla(cab4, T.imc_categorias.map(fila4), anch4, { tam: 15, numericas: [1, 7, 8], resaltar: (f) => f[0] === 'bajo peso' }));
add(TIT('Tabla 11. Pruebas, separando p sin ajustar y q corregido'));
add(tabla(['Análisis', 'Prueba', 'n', 'Efecto', 'p sin ajustar', 'q'],
  T.imc_pruebas.map((x) => [x.analisis, x.prueba, ent(x.n), `${x.medida} = ${num(x.efecto, 3)}`, pv(x.p_sin_ajustar), pv(x.q_familia_41)]),
  [3860, 1300, 600, 1400, 1100, 1100], { numericas: [2, 4, 5], resaltar: (f) => f[0].startsWith('Original') }));
add(NOTA('q con reemplazo en la familia de 41, salvo el análisis original y el IMC numérico, cuyos q son los guardados. Con el reemplazo, ninguna otra variable cambia de lado de q = 0,05: las significativas pasarían de 8 a 9.'));
add(TIT('Tabla 12. Comparaciones entre categorías (solo observado)'));
add(tabla(['Comparación', 'n', 'p sin ajustar', 'q entre estos 3 pares'],
  T.imc_pares.map((x) => [x.comparacion, `${x.n_a} y ${x.n_b}`, pv(x.p_sin_ajustar), pv(x.q_entre_3_pares)]), [4060, 1500, 1800, 2000], { numericas: [2, 3] }));
add(NOTA('Este q corrige solo los 3 pares. No es comparable con el q de la familia de 41.'));
add(H2('Qué significan estos resultados'));
add(LI('**El error.** Las 262 personas con «no informado» tienen severidad intermedia (16,4). Esa mitad de la muestra, tratada como una categoría más, diluye la diferencia y lleva a q 0,073, lo que parece decir que la categoría de IMC no se asocia.'));
add(LI('**Qué aparece sin la mezcla.** La severidad sube de normal (39 % severas) a sobrepeso (50 %) y obesidad (65 %). La diferencia está sobre todo en obesidad: normal frente a sobrepeso no se distingue.'));
add(LI('**Bajo peso.** Son 2 personas: IMC 18,2 y 18,4; MRS 12 y 10; ambas en clase moderada. La regla de 34C exige al menos 5 por grupo, así que salieron sin aviso (por eso n = 527). No permiten concluir nada. Incluirlas o unirlas a «normal» cambia poco el efecto, aunque con 4 categorías q queda en 0,064: el resultado depende de esa elección.'));
add(LI('**Coherencia.** El IMC numérico observado ya era significativo en 34C (rho 0,219; q 0,004), así que la categoría no aporta una conclusión nueva: corrige una aparente contradicción.'));

// ------------------------------------------------------------------ figuras
add(H1('6. Auditoría de figuras e informes'));
add(H2('Figuras de la Fase 34D'));
add(P(`**Los porcentajes y denominadores están bien calculados, pero el subtítulo oculta qué parte es imputada.** ${R.figuras.con_imputadas} de ${R.figuras.evaluadas} variables revisadas tienen imputadas, y ${R.figuras.faltante_cero_con_imputadas} de ellas dicen «faltante = 0». Se abrieron y compararon las figuras de sobrecarga, trabaja y lugar; las demás se auditaron con el código que escribe el subtítulo y con sus datos.`));
add(TIT('Tabla 13. Sobrecarga física y emocional: 251 cuidadoras, 239 observadas y 12 imputadas'));
add(tabla(['Categoría', 'n en la figura', 'Observadas', 'Imputadas', '% sobre 251 (figura)', '% sobre 239'],
  T.sobrecarga_251_239.map((x) => [x.categoria, ent(x.n_251), ent(x.observadas), ent(x.imputadas), `${num(x.pct_sobre_251)} %`, `${num(x.pct_sobre_239)} %`]),
  [2760, 1200, 1200, 1200, 1600, 1400], { numericas: [1, 2, 3, 4, 5], resaltar: (f) => f[3] !== '0' }));
add(NOTA('La figura histórica dice «n válido = 251 · faltante = 0». La copia corregida en informe_integrado/figuras/ dice lo correcto, pero eda/univariado.py volvería a generar el subtítulo antiguo.'));
add(LI('**Título, porcentajes y denominador de sobrecarga.** Correctos: 106 de 251 es 42,2 %. Lo incorrecto es «faltante = 0». Las 12 imputadas están todas en «A veces».'));
add(LI(`**Lugar de trabajo comprensivo.** «Neutral» (n = ${R.figuras.lugar_neutral_total}) incluye ${R.figuras.lugar_neutral_imputadas} imputadas. «Faltante = 22» trata como trabajadoras a personas sin respuesta laboral, y 12 de ellas no trabajan según el simulador.`));
add(LI(`**Efecto sobre la dominancia.** El cambio máximo es de ${num(R.figuras.max_dif_puntos)} puntos (tipo de método anticonceptivo), con una mediana de 1,3. Tres variables cruzan el 80 %: operada para no tener más hijos, aeróbico y verduras. El informe 34D ya lo avisa. Ninguna cruza el 85 %, así que no cambia ninguna exclusión.`));
add(LI(`**Columna imputados_34B.** En ${R.figuras.resumen_distinto_de_exacto} variables sobreestima por 1 a 3 celdas, porque sin marca usa el total sobre 546. Tabla completa en auditoria_figuras_34D.csv.`));
add(H2('Diferencias entre informes y scripts'));
add(TIT('Tabla 14. Referencias desactualizadas'));
add(tabla(['Fase', 'Dónde', 'Qué dice', 'Situación vigente'], [
  ['34C', 'eda/variables.py, eda_usuaria.py', 'Etapa menopáusica en «Variables de control»', 'Descriptiva desde el 01-11. Informe y CSV se corrigieron a mano. Volver a ejecutar reintroduce el texto antiguo.'],
  ['34C', 'informe_eda_usuaria.md, líneas 772 y 1157', 'IMC como categoría con «no informado»; no se imputa', 'En la Fase 35 se imputa por la media (27-10).'],
  ['34E', 'matriz_asociacion.png', '«38 predictoras»', 'Son 38 exploratorias. El informe ya lo advierte.'],
  ['34E', 'informe_eda_multivariado.md, línea 138, y eda/multivariado.py', 'El modelado usa 35 predictoras', 'Conjunto inicial vigente: 33.'],
  ['34E', 'informe_eda_multivariado.md §2', '«Sin imputaciones»', 'Falso en general: carga dataset_fase35.csv con las imputaciones de 34B, salvo IMC y laborales.'],
  ['34E', 'informe_eda_multivariado.md §2', '«Las 22 trabajadoras»', 'Tienen situación laboral imputada; 12 no trabajan según el simulador.'],
  ['34E', 'eda_multivariado.py', 'Código adaptado', 'No se ha ejecutado completo; resultados del 30-10.'],
], [650, 2910, 2500, 3300]));
add(NOTA('Dos casos que parecen errores y no lo son: la línea 1171 del informe 34C dice «34 variables», pero se refiere a las no significativas; y la Figura 89, «Variables de control», no muestra la etapa, porque esa variable se prueba con Kruskal-Wallis y no entra en ese panel.'));
add(H2('La celda correcta y las 196 de la regla de pareja'));
add(P('La sección 6.3 del informe de limpieza dice que la limpieza cambió por error 1 celda, pero su tabla lista 197. Ambas cifras son correctas y miden cosas distintas:'));
add(tabla(['Variable', 'Celdas', 'Qué ocurrió', 'Clasificación'], [
  ['circunferencia_cintura_cm', '1', 'Un valor correcto (75) quedó vacío. La variable no se usa en el análisis de la usuaria.', '**Error** de la limpieza'],
  ['cambio_relacion_pareja_menopausia', '196', 'Se vació a propósito en quienes no tienen pareja: «no aplica». La plataforma muestra la pregunta a todas.', '**Regla** del análisis, no un error'],
], [3000, 700, 3860, 1800], { numericas: [1] }));
add(P(''));

const secciones = [];
const pie = { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Revisión correctiva de la Fase 34 · Página ', size: 15, color: '7F7F7F' }), new TextRun({ children: [PageNumber.CURRENT], size: 15, color: '7F7F7F' })] })] }) };
secciones.push({ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } } }, footers: pie, children: hijos.splice(0) });

// ------------------------------------------------------------------ matriz (horizontal)
add(H1('7. Matriz de impacto sobre Shannon y Random Forest'));
add(P('**Con las correcciones recomendadas, ninguna fila requiere recalcular SU, p, q o FCBF ni repetir Random Forest.** Solo H02 y H03 lo requerirían, y únicamente si se decide tratar esas celdas como faltantes.'));
add(LI('**Errores comprobados (4):** H05, H07, H10 y H11. **Decisiones metodológicas discutibles (7):** H02, H03, H04, H06, H08, H09 y H17. **Problemas documentales (5):** H12 a H16. **Verificado sin error (1):** H01.'));
add(tabla(['ID', 'Clase', 'Error o limitación', 'Archivos y variables', '¿Solo presentación?', '¿Cálculos del EDA?', '¿Datos o poblaciones de la Fase 35?', '¿Recalcular SU, p, q o FCBF?', '¿Repetir Random Forest?', 'Corrección mínima'],
  T.matriz_impacto.map((x) => [x.id, x.clase, x.hallazgo, x.archivos_variables, x.solo_presentacion, x.calculos_eda, x.datos_poblaciones_f35, x.recalcular_su_p_q_fcbf, x.repetir_rf, x.correccion_minima]),
  [480, 900, 2900, 1900, 650, 1000, 1250, 1400, 1100, 1880], { tam: 13 }));
secciones.push({ properties: { page: { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1000, bottom: 900, left: 1190, right: 1190 } } }, footers: pie, children: hijos.splice(0) });

// ------------------------------------------------------------------ integridad y plan
add(H1('8. Verificación de que la Fase 35 sigue intacta'));
add(P(`**Resultado: ${C.cambiados.length} archivos cambiados, ${C.faltan.length} faltantes y ${C.nuevos.length} nuevos entre los ${C.archivos_antes} protegidos.** HEAD sigue en ${C.head_despues.slice(0, 7)}, sin cambios en archivos versionados. La huella cubre analisis/ (salvo esta carpeta y __pycache__), datos/analitico, datos/limpio_usuaria y datos/sintetico.`));
add(TIT('Tabla 15. Huellas SHA-256 de los archivos clave'));
add(tabla(['Archivo', 'SHA-256 (inicio)', '¿Igual?'], C.claves.map((c) => [c.ruta, `${c.sha256.slice(0, 16)}…`, c.igual ? 'Sí' : 'No']), [6060, 2300, 1000], { tam: 14 }));
add(TIT('Tabla 16. Comprobaciones automáticas'));
add(tabla(['Comprobación', 'Resultado'], T.integridad_fase35.map((x) => [x.comprobacion, x.resultado]), [8160, 1200]));
add(NOTA('Las comparaciones de p y q toleran hasta 0,00001 porque los CSV guardan valores redondeados. En Shannon, las diferencias encontradas son menores que 0,000001; en la familia del EDA, menores que 0,000005.'));

add(H1('9. Plan de correcciones mínimas'));
add(P('**Nada de esto se ha aplicado.** El orden va de menor a mayor intervención, y cada paso necesita tu autorización. Ninguno cambia datos ni resultados de la Fase 35.'));
add(TIT('Tabla 17. Correcciones propuestas'));
add(tabla(['Paso', 'Qué se haría', 'Cubre', 'Archivos', 'Cambia resultados'], [
  ['1', 'Agregar una nota de erratas al inicio de los informes 34B, 34C, 34D y 34E, y actualizar sus Word solo en texto.', 'H05, H08, H09, H12 a H16', 'Informes .md y Word', 'No'],
  ['2', 'Agregar a 34C un cuadro complementario de IMC con las Tablas 9 a 12, conservando el valor histórico de q 0,073.', 'H07, H08', 'informe_eda_usuaria.md y Word', 'Agrega un resultado; no borra'],
  ['3', 'Publicar como anexos los indicadores de auditoría y la tabla exacta de imputadas, en esta carpeta.', 'H02, H03, H04, H11', 'Archivos ya generados aquí', 'No'],
  ['4', 'Cambiar el subtítulo a «n = 251: 239 observadas y 12 imputadas» y generar copias de las figuras con imputadas en una carpeta nueva. Las históricas no se sobrescriben.', 'H05, H10', 'eda/univariado.py y carpeta nueva', 'No: mismas barras'],
  ['5', 'Mencionar en el informe de Random Forest la limitación de identificación de imputadas.', 'H17', 'Informe Word de Random Forest', 'No'],
  ['6', 'Alinear los scripts de 34C y 34E con los informes, sin ejecutarlos, o dejarlo registrado como pendiente.', 'H13, H14', 'eda/variables.py, eda_usuaria.py', 'No, si no se ejecutan'],
], [550, 4210, 1500, 1800, 1300]));
add(P(''));
add(P('**Precaución con el paso 4 y el paso 6.** Algunos programas de la Fase 35 exigen que HEAD siga en 745d689 y se detienen si cambia. Antes de editar código versionado o hacer commit, conviene comprobar cuáles se verían afectados.'));
add(H2('Decisiones que necesito de ti'));
add(NUM('**Las 22 imputadas de trabajo y las 21 de cuidado.** Recomiendo conservarlas y documentarlas: las asociaciones casi no cambian y evita recalcular. La alternativa es tratarlas como faltantes y recalcular SU, p y q de esas variables, BH de las 33, y Random Forest si cambia algo.'));
add(NUM('**Lugar y estrés en la Fase 36.** Recomiendo no usar el valor 3 de las 22 como respuesta real: en un análisis general, tratarlas igual que «no aplica» o sin dato. Conviene definirlo con la profesora, porque depende de cómo se plantee la segmentación.'));
add(NUM('**Qué pasos del plan autorizas.** Recomiendo los pasos 1, 2, 3 y 5 ahora. El 4 y el 6 pueden esperar a resolver el tema de HEAD.'));

add(H1('10. Limitaciones'));
add(LI('**Sensibilidad descriptiva.** Spearman y chi² orientan, pero no reemplazan a SU. No puedo afirmar numéricamente que trabaja actualmente seguiría con q < 0,10 en Shannon sin las imputadas (hoy q = 0,089), porque recalcularlo está fuera de esta revisión.'));
add(LI('**q con reemplazo.** Son aproximaciones: cambian una prueba a la vez y mantienen las demás.'));
add(LI('**Conjunto sintético.** Los efectos fueron programados en el simulador, y la comparación con él solo existe porque los datos son simulados. Nada de esto es evidencia clínica ni causal.'));
add(LI('**Auditoría de figuras.** La revisión visual fue de cuatro imágenes; las demás se auditaron por el código y los datos, y las figuras de 34C solo por su código.'));
add(H2('Archivos de esta revisión'));
add(P('Todo está en analisis/revision_correctiva_fase34/, sin commit: los programas auditoria_fase34.py, matriz_impacto.py, manifiesto.py, comparar_manifiestos.py y generar_informe_word.js; las tablas de sensibilidad y los indicadores en tablas/; y las huellas en manifiestos/.'));
secciones.push({ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } } }, footers: pie, children: hijos.splice(0) });

const doc = new Document({
  creator: 'AgingWomen', title: 'Revisión correctiva de la Fase 34',
  styles: {
    default: { document: { run: { font: FUENTE, size: 20 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FUENTE, size: 28, bold: true, color: AZUL }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FUENTE, size: 22, bold: true, color: '2E74B5' }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: 'vinetas', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 240 } } } }] },
    { reference: 'numeros', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 280 } } } }] },
  ] },
  sections: secciones,
});
const salida = path.join(__dirname, 'informe', 'diagnostico_revision_fase34.docx');
fs.mkdirSync(path.dirname(salida), { recursive: true });
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(salida, b); console.log(salida, b.length); });
