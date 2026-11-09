// Fase 36A: genera protocolo_metodologico_fase36.docx. Las tablas salen de los CSV del diseño; no calcula nada.
// Uso, desde analisis/: NODE_PATH=<carpeta con node_modules de docx> node fase36_diseno/scripts/generar_protocolo.js
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun } = require('docx');
const { P, H1, H2, LI, NOTA, tabla, estilos, numeracion, pie, PAG } = require('../../cierre_fases_34_35/scripts/word_comun');

const DISENO = path.resolve(__dirname, '..');
function leerCsv(ruta) {
  const t = fs.readFileSync(ruta, 'utf8').replace(/^﻿/, '');
  const filas = []; let f = [], c = '', q = false;
  for (let i = 0; i < t.length; i++) {
    const x = t[i];
    if (q) { if (x === '"' && t[i + 1] === '"') { c += '"'; i++; } else if (x === '"') q = false; else c += x; }
    else if (x === '"') q = true;
    else if (x === ',') { f.push(c); c = ''; }
    else if (x === '\n') { f.push(c.replace(/\r$/, '')); filas.push(f); f = []; c = ''; }
    else c += x;
  }
  const cab = filas.shift();
  return filas.filter((r) => r.length === cab.length).map((r) => Object.fromEntries(cab.map((k, i) => [k, r[i]])));
}
const M = leerCsv(path.join(DISENO, 'matriz_decisiones_variables.csv'));
const E = leerCsv(path.join(DISENO, 'apoyo', 'distribuciones_para_escalado.csv'));
const coma = (x, d) => Number(x).toFixed(d).replace('.', ',').replace('-', '−');
const G = M.filter((x) => x.capa === 'general');
const CAPA = { general: 'General', laboral: 'Laboral', cuidadoras: 'Cuidados' };
const corto = { cuantitativa: 'Cuantitativa', binaria: 'Binaria', nominal: 'Nominal', ordinal: 'Ordinal' };

const hijos = [
  new Paragraph({ children: [new TextRun({ text: 'Protocolo metodológico de la Fase 36', bold: true, size: 36, color: '1F4E79' })], spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: 'Fase 36A: diseño de la codificación y el escalado para PCA, FAMD, K-means y clustering aglomerativo', size: 23, color: '404040' })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: 'AgingWomen · Conjunto sintético de usuarias · 5 de noviembre de 2026 · Propuesta para revisión', size: 18, color: '595959' })], spacing: { after: 240 } }),
  H1('1. Resumen'),
  P('Este protocolo define cómo representar las 33 variables elegibles antes de reducir dimensiones y formar clústeres. **Es solo diseño:** no se generaron matrices, no se ajustaron escaladores ni modelos, y no se modificaron datos.'),
  LI('**Capa general:** 529 participantes y 30 variables forman los clústeres. El MRS queda fuera.'),
  LI('**Módulos:** las 2 variables laborales (287) y la sobrecarga (239, con 251 como sensibilidad) caracterizan los clústeres, sin formarlos.'),
  LI('**Dos rutas:** PCA con todas las columnas numéricas, y FAMD con 19 variables cuantitativas y 11 categóricas.'),
  LI('**Escalado:** StandardScaler, salvo dos casos justificados: IMC y la nominal en PCA.'),
  LI('**Sensibilidades:** IMC, ordinales, edad e imputaciones de trabajo, cuidados y ejercicio, variando un factor por vez.'),
  P('Hay 15 decisiones con una recomendación fundamentada (sección 12). Las cinco primeras por revisar son D-01, D-03, D-05, D-07 y D-08.'),
  H1('2. Fuentes revisadas'),
  tabla(['Fuente', 'Uso'], [
    ['analisis/reunion_2026-11-03/revision_33_variables/permutaciones_50000/relevancia_33.csv', 'Lista definitiva y poblaciones'],
    ['analisis/resultados/usuaria/diccionario_datos_fase35.csv', 'Tipo final, valores y tratamiento; no incluye la sobrecarga'],
    ['analisis/limpieza/catalogo.py', 'Opciones del instrumento y reglas condicionales de la plataforma'],
    ['analisis/preprocesamiento/configuracion.py', 'Semilla, filtros y exclusiones de la Fase 35'],
    ['analisis/resultados/usuaria/eda_univariado_resumen.csv', 'Secciones y distribuciones de la Fase 34'],
    ['analisis/revision_correctiva_fase34/tablas/origen_respuestas_34D.csv', 'Observadas, deducidas e imputadas'],
    ['datos/analitico/dataset_fase35.csv y datos/limpio_usuaria/dataset_usuaria_limpio.csv', 'Frecuencias y marcas, solo en lectura'],
    ['analisis/cierre_fases_34_35/informes/', 'Decisiones y limitaciones de los cierres'],
  ], [5600, 3760], { tam: 16 }),
  P('**dataset_fase35_33_variables.csv no se usa como entrada:** contiene columnas no elegibles y no incluye la sobrecarga.'),
  H1('3. Variables y clasificación'),
  P('**Clasificación de las 33:** 24 ordinales, 5 binarias, 3 cuantitativas y 1 nominal. En la capa general: 21 ordinales, 5 binarias, 3 cuantitativas y 1 nominal. El detalle completo, con valores, significados, procedencia y justificación, está en matriz_decisiones_variables.csv, y cada nivel en diccionario_codificacion_fase36.csv.'),
  tabla(['Variable', 'Capa', 'Tipo', 'Imputadas', 'Rol en FAMD', 'Sensibilidades'],
    M.map((x) => [x.variable, CAPA[x.capa], corto[x.tipo_original], x.imputadas, x.rol_famd === 'no participa' ? 'Fuera' : x.rol_famd, x.sensibilidades]), [3100, 900, 1100, 880, 1180, 2200], { tam: 15 }),
  NOTA('Las imputadas son directas. No incluyen los 262 valores de IMC imputados por la media en la Fase 35 ni los ceros que dependen de una pregunta previa imputada.'),
  H2('Exclusiones'),
  P('Quedan fuera del modelado: usa_medicamentos_diabetes, doble_carga, prevision, etapa_menopausica y las preguntas menstruales; cuida_otras_personas y las variables realiza_*; el objetivo y las derivadas del MRS; las consecuencias de los síntomas; los identificadores y las marcas de auditoría. Shannon y FCBF **no recortan** la lista: una variable sin respaldo univariado puede aportar a un perfil.'),
  H1('4. Reglas condicionales y ceros'),
  P('El protocolo separa tres situaciones que los datos pueden confundir:'),
  tabla(['Situación', 'Ejemplos', 'Tratamiento'], [
    ['Cero válido', 'Cantidad = 0 (no cuida); frecuencia de ejercicio = 0 (no lo realiza); códigos 1 de «Nunca» o «No consumo»', 'Forma parte de la escala'],
    ['No aplicable', '0 en lugar y estrés de quienes no trabajan; sobrecarga de quienes no cuidan', 'No es un valor de escala; queda fuera del módulo'],
    ['Relleno', '3 en lugar y estrés de las 22 con situación laboral imputada', 'No es una opinión; queda fuera del módulo'],
  ], [1800, 4760, 2800]),
  P('**Frecuencias de ejercicio.** El instrumento admite 1 = «Nunca», pero ninguna participante lo tiene: quien no realiza el ejercicio no ve la pregunta. Los códigos son 0, 2, 3, 4 y 5. Se recomienda la escala consecutiva 0 a 4, para quitar el salto. No agrega categorías (D-02).'),
  H1('5. Ruta PCA'),
  tabla(['Tipo', 'Decisión', 'Justificación'], [
    ['Cuantitativa', 'Valor estandarizado', 'Tiene una escala real'],
    ['Binaria', 'Una columna 0/1 estandarizada', 'Equivale al bloque de dos indicadoras con varianza total 1'],
    ['Nominal', '5 indicadoras centradas, divididas por √Σp(1−p)', 'Toda pareja de categorías queda a la misma distancia (4,11) y la variable suma varianza 1. Con la estandarización común, OTRO quedaría en z = 8,6'],
    ['Ordinal', 'Código en el orden del instrumento, estandarizado', 'Conserva el orden con una sola columna'],
  ], [1400, 3360, 4600]),
  P('**Ordinales: recomendación.** La principal son los códigos consecutivos, y la sensibilidad es ridit, cuyos pasos reflejan cuántas personas hay entre niveles. Ambas conservan el orden. La equidistancia de la principal es un **supuesto de trabajo**, y S-ORD permite comprobar si los perfiles dependen de él. Se descartan one-hot (pierde el orden y sobrepondera), puntos medios (obligan a inventar valores para categorías abiertas) y correlación policórica (poco directa con ceros estructurales y usuarias nuevas).'),
  P('**Correlación.** 424 de 435 pares están bajo |0,2| y solo 4 superan |0,4|. No se eliminan variables. Hay que esperar poca varianza por eje y **admitir la posibilidad de que no haya clústeres marcados**, sin forzar el resultado.'),
  P('**Bloques.** Alimentación tiene 13 de 30 variables y, con varianzas iguales, pesa en esa proporción. Se recomienda no ponderar en la base, porque la lista se definió por variable, y contrastar con S-BLOQUE (D-07).'),
  P('**Tamaño esperado:** 34 columnas con IMC y 33 sin IMC; varianza total de 29,505 y 29.'),
  H1('6. Ruta FAMD'),
  P('FAMD trata una categórica por sus niveles y **no conserva por sí mismo el orden**. Por eso una ordinal solo pasa a categórica si tiene un motivo explícito: un nivel estructural de «no realiza» o «no cuida», o bimodalidad.'),
  tabla(['Rol', 'n', 'Variables'], [
    ['Cuantitativa', '19', G.filter((x) => x.rol_famd === 'cuantitativa').map((x) => x.variable).join(', ')],
    ['Categórica', '11', G.filter((x) => x.rol_famd === 'categórica').map((x) => x.variable).join(', ')],
  ], [1400, 500, 7460], { tam: 16 }),
  P('**Binarias.** Son categóricas de dos niveles, con inercia 1: equivalen a la columna estandarizada de PCA.'),
  P('**Niveles raros.** FAMD divide por √p, y eso amplifica lo infrecuente. Solo en esta ruta, los niveles bajo 5 % se unen al vecino menor, sin unir nunca el nivel estructural. En la nominal se unen COMPRO y OTRO. El 5 % es una convención y se contrasta con S-RARA.'),
  tabla(['Variable', 'Niveles finales'], G.filter((x) => x.rol_famd === 'categórica' && x.tipo_original !== 'binaria').map((x) => [x.variable, x.propuesta_famd]), [3200, 6160], { tam: 16 }),
  P('**Equilibrio.** Cada cuantitativa aporta inercia 1, y cada categórica K − 1. En un mismo eje, ninguna variable contribuye más de 1. **Tamaño esperado:** 50 columnas con IMC y 49 sin IMC; inercia de 38,505 y 38.'),
  H2('Diferencias esperadas respecto de PCA'),
  tabla(['Aspecto', 'PCA', 'FAMD'], [
    ['Ordinal con quiebre', 'Escala lineal', 'Niveles separados; capta relaciones no lineales'],
    ['Orden', 'Se conserva por construcción', 'No garantizado en 5 ordinales; se comprueba después'],
    ['Categorías raras', 'No se amplifican', 'Pesan más; por eso se agrupan'],
    ['Peso de la nominal', 'Total 1', 'Inercia total 3'],
    ['Ejercicio y cuidado', 'Una dimensión de «cuánto»', 'Puede separar «hacer o no hacer» de «cuánto»'],
  ], [2600, 3000, 3760]),
  H1('7. Escalado'),
  P('**Recomendación:** StandardScaler. RobustScaler no está definido en 9 de las 29 columnas numéricas, porque su rango intercuartílico es 0. No se proponen logaritmos ni recortes: la asimetría de las cuantitativas es baja y sus extremos son plausibles.'),
  tabla(['Variable', 'Rango', 'Asimetría', 'Curtosis', 'Atípicos', 'z máximo', 'Decisión'],
    E.filter((x) => x.tipo === 'cuantitativa').map((x) => [x.variable, `${coma(x.minimo, 1)} a ${coma(x.maximo, 1)}`, coma(x.asimetria, 2), coma(x.curtosis_exceso, 2), x.atipicos_tukey, coma(x.z_max_abs, 2), x.variable === 'imc' ? 'Parámetros de las 267' : 'StandardScaler']),
    [2300, 1300, 950, 950, 860, 900, 2100], { tam: 16 }),
  NOTA('La forma del IMC se mide en las 267 observadas. La de horas sentada incluye 27 imputadas (limitación A1). Tabla completa: apoyo/distribuciones_para_escalado.csv.'),
  P('**IMC.** Se usan la media y la DE de las 267 observadas (29,23 y 6,26). Con la DE de las 529 (4,45), las diferencias reales se amplificarían 1,41 veces por efecto de la imputación. Así, el IMC aporta varianza 0,505, coherente con que la mitad de la muestra no informa sobre él (D-05).'),
  P('**Variables constantes.** Ninguna lo es. Una DE igual a 0 detiene el proceso con error, para no cambiar la lista en silencio.'),
  P('**Nuevas usuarias.** Los parámetros se calculan una vez, se guardan y no se ajustan de nuevo. Los de sensibilidad nunca llegan a la plataforma.'),
  H1('8. Imputaciones y sensibilidades'),
  P('Cada celda debe distinguir entre observada, deducida, imputada y no aplicable. Nunca se usa la verdad del simulador. En las generales hay 665 celdas imputadas de 15.870 (4,2 %) y 100 valores estructurales que dependen de una pregunta previa imputada.'),
  P('**Vacío de trazabilidad.** Solo 15 de las 30 generales tienen marca _imputado. Se recomienda reconstruir la máscara por celda en memoria, sin leer la verdad del simulador, y exigir que coincida con los recuentos históricos (D-08).'),
  tabla(['Tema', 'Principal', 'Sensibilidad'], [
    ['IMC (262 imputados)', 'Escenarios con y sin IMC; ninguna fila se elimina', 'Acuerdo entre escenarios en las 529 y en las 267; IMC imputado por clúster'],
    ['Trabajo (22 imputadas)', 'Permanecen en la capa general con valor 1 y procedencia «imputado». Sus 3 y los 0 no entran', 'S-TRA: ajustar con 507 y proyectar a las 22; opcional, punto de quiebre con valor 0'],
    ['Cuidados (21 imputadas)', 'Cantidad = 0 se mantiene. No significa sobrecarga cero', 'S-CUI: ajustar con 508 y proyectar a las 21; opcional, punto de quiebre con cantidad 1'],
    ['Ejercicio (29, 22 y 28)', 'Se mantienen los ceros. **No estaba en el encargo**', 'S-EJE: mismo diseño de proyección'],
  ], [2200, 3700, 3460], { tam: 16 }),
  P('Se varía un factor por vez respecto de la configuración base. Los puntos de quiebre son hipotéticos y no son datos. Los umbrales para considerar relevante un cambio no se fijan aquí, y deben acordarse antes de ejecutar la Fase 37 (D-13).'),
  H1('9. Módulos complementarios'),
  P('**No se forman clústeres con una o dos variables.** Los módulos se leen sobre los clústeres ya formados, sin cambiarlos.'),
  tabla(['Módulo', 'Principal', 'Sensibilidad', 'Fuente', 'Cuidado'], [
    ['Laboral: lugar y estrés', '287', '263 con ambas observadas', 'Conjunto limpio', 'Sin los 3 de las 22 ni los 0 de las 220. Incluye 16 y 10 imputadas'],
    ['Cuidados: sobrecarga', '239 observadas', '251 cuidadoras', 'Conjunto limpio', 'Sin dato no es cero. 99 de las 239 no trabajan y la pregunta menciona el trabajo'],
  ], [2000, 1000, 1700, 1300, 3360], { tam: 16 }),
  H2('Caracterización de los clústeres (Fase 37)'),
  LI('Distribución por clúster, con mediana y proporciones, siempre con el denominador del módulo.'),
  LI('Porcentaje de cada clúster que tiene dato de cada módulo, porque un clúster puede tener pocas participantes en él.'),
  LI('Comparación con tamaño de efecto y corrección por pruebas múltiples, sin mostrar grupos de menos de 5.'),
  H2('Reglas de asociación (Fases 38 y 39)'),
  LI('Una regla con un ítem laboral se evalúa solo en las 287, y una con sobrecarga, en las 239. El soporte declara su denominador.'),
  LI('«No aplica» no se convierte en un ítem de la escala. trabaja_actualmente y cantidad_personas_cuida ya son ítems de la capa general.'),
  LI('Una regla con ambos módulos usa la intersección de 130 participantes y debe informarse como subpoblación pequeña.'),
  LI('La forma de agrupar las escalas en ítems se define antes de esas fases (D-15).'),
  H1('10. Compatibilidad con la Fase 37 y con la plataforma'),
  tabla(['ID', 'Ruta', 'IMC', 'Algoritmos'], [
    ['P1 / P2', 'PCA', 'Con / sin', 'K-means y Ward sobre coordenadas'],
    ['F1 / F2', 'FAMD', 'Con / sin', 'K-means y Ward sobre coordenadas'],
    ['R0', 'Sin reducción, matriz PCA', 'Con y sin', 'K-means y Ward: referencia comparable'],
    ['R-G', 'Gower, opcional', 'Con y sin', 'Aglomerativo con enlace promedio; no compatible con K-means ni Ward'],
  ], [1200, 3000, 1200, 3960]),
  P('**Artefactos.** Cada escenario guarda en JSON el esquema, el orden de columnas, los codificadores, los parámetros de escalado, la regla para valores desconocidos, la procedencia esperada, el entorno (versiones y semilla 42) y las huellas SHA-256. Se evita pickle como formato principal, para que sobreviva a cambios de versión.'),
  P('**Nueva usuaria (Fase 40).** Validar el esquema, aplicar las reglas condicionales, codificar, escalar y proyectar con los parámetros guardados, y asignar el perfil. Un nivel que el instrumento no admite produce error. K-means asigna por centroide cercano; el aglomerativo no tiene esa función, y se propone la misma regla, informando su concordancia.'),
  P('**Edad.** La referencia va de 36 a 65 y la plataforma admite 40 a 65, o menos con excepción. Son compatibles. Una usuaria bajo 36 quedaría fuera de la referencia y debe recibir un aviso.'),
  H1('11. Pruebas para la Fase 36B'),
  P('plan_pruebas_fase36.md detalla las 13 pruebas solicitadas y 12 adicionales, con resultados esperados: entre otras, ausencia de relleno laboral, confusión de ceros, parámetros del IMC, distancia de la nominal y lectura de la verdad del simulador. **Ninguna se ha ejecutado.**'),
  H1('12. Decisiones para revisar'),
  tabla(['ID', 'Decisión', 'Recomendación'], [
    ['D-01', 'Ordinales en PCA', 'Códigos consecutivos; ridit como sensibilidad'],
    ['D-02', 'Frecuencias de ejercicio', 'Escala 0 a 4; «Nunca» se une a «No lo realiza»'],
    ['D-03', 'Ordinales en FAMD', '16 cuantitativas y 5 categóricas'],
    ['D-04', 'Niveles raros en FAMD', 'Agrupar bajo 5 %; contrastar sin agrupar'],
    ['D-05', 'Parámetros del IMC', 'Las 267 observadas'],
    ['D-06', 'Nominal en PCA', 'Indicadoras centradas con varianza total 1'],
    ['D-07', 'Peso de los bloques', 'Sin ponderar; contraste S-BLOQUE'],
    ['D-08', 'Procedencia por celda', 'Reconstrucción en memoria, verificada contra recuentos'],
    ['D-09', 'Ausencias en la Fase 40', 'Valor congelado con aviso y un límite por fijar'],
    ['D-10', 'Actividad sexual y distensión', 'Mantener y contrastar con S-SOLAPE'],
    ['D-11', 'Referencia sin reducción', 'R0, y Gower como adicional'],
    ['D-12', 'Implementación de FAMD', 'Transformación propia y PCA de scikit-learn'],
    ['D-13', 'Reglas de la Fase 37', 'Fijarlas antes de ver resultados'],
    ['D-14', 'Edad', 'Base con edad; comparar sin ella'],
    ['D-15', 'Ítems de módulos en las reglas', 'Agrupar según el sentido de la escala'],
  ], [800, 3400, 5160]),
  H1('13. Implementación posterior (Fase 36B)'),
  P('Una vez aprobado este protocolo, en la carpeta nueva analisis/fase36/:'),
  LI('Construir el esquema y los codificadores desde el diccionario.'),
  LI('Obtener la procedencia por celda y verificarla.'),
  LI('Generar y guardar las matrices PCA y FAMD, con y sin IMC, y los parámetros.'),
  LI('Preparar las tablas de módulos y las poblaciones de sensibilidad.'),
  LI('Implementar la transformación de una participante nueva.'),
  LI('Ejecutar el plan de pruebas y comparar el manifiesto.'),
  P('La Fase 36B no ajusta clústeres. Eso corresponde a la Fase 37.'),
  H1('14. Límites y trazabilidad'),
  P('Esta etapa no modificó datos, no repitió las Fases 34 ni 35, no ejecutó Shannon, FCBF ni Random Forest, no generó matrices, no ajustó PCA ni FAMD, no ejecutó clustering, no creó reglas y no tocó la plataforma. Sin commit ni push; HEAD 745d689. Las comprobaciones de cobertura e integridad están en apoyo/verificacion_diseno.csv. Fecha: 5 de noviembre de 2026.'),
];
(async () => {
  const doc = new Document({ styles: estilos, numbering: numeracion, sections: [{ properties: { page: PAG }, footers: { default: pie('Protocolo metodológico de la Fase 36') }, children: hijos }] });
  fs.writeFileSync(path.join(DISENO, 'protocolo_metodologico_fase36.docx'), await Packer.toBuffer(doc));
  console.log('protocolo_metodologico_fase36.docx');
})();
