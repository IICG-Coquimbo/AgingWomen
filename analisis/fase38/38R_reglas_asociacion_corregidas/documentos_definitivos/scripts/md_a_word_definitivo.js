// Fase documental 38R/39R. Deriva de analisis/fase37/37C_comparacion_seleccion/scripts/md_a_word_37c.js y usa word_comun.js; ninguno de los dos se modifica.
// Añade: secciones apaisadas (<!-- apaisada --> y <!-- vertical -->), viñetas de dos niveles, anchos de columna según el contenido,
// títulos unidos a su contenido, filas finales juntas y porcentajes sin partir.
// Uso: node md_a_word_definitivo.js entrada.md salida.docx "Título" "Subtítulo" (requiere NODE_PATH; lo fija scripts/entorno_word.py).
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, LevelFormat, PageOrientation, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, VerticalAlign } = require('docx');
const W = require(path.resolve(__dirname, '../../../../cierre_fases_34_35/scripts/word_comun'));

const [entrada, salida, titulo, subtitulo] = process.argv.slice(2);
const FECHA = 'AgingWomen · Conjunto sintético de usuarias · Versión correctiva · 8 de noviembre de 2026';
const AZUL = '1F4E79';
const BORDE = 'BFBFBF';
const VERTICAL = { ancho: 9360, alto: 800, pagina: W.PAG };
const APAISADA = {
  ancho: 13680,
  alto: 600,
  pagina: { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1000, bottom: 1000, left: 1080, right: 1080 } },
};
const limpiar = (t) => t.replace(/`/g, '').replace(/\\\|/g, '|').replace(/(\d) %/g, '$1 %');
const lineas = fs.readFileSync(entrada, 'utf8').split(/\r?\n/);
const numeracion = {
  config: [{
    reference: 'vinetas_jerarquia',
    levels: [
      { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } },
      { level: 1, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 800, hanging: 220 } } } },
    ],
  }],
};

function ricos(texto, base = {}) {
  return String(texto).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((t) => (t.startsWith('**')
    ? new TextRun({ text: t.slice(2, -2), ...base, bold: true }) : new TextRun({ text: t, ...base })));
}

const vineta = (t, nivel, unir) => new Paragraph({ children: ricos(t), numbering: { reference: 'vinetas_jerarquia', level: nivel }, spacing: { after: 70, line: 264 }, keepNext: unir });

function anchos(cabeza, filas, ancho, tam) {
  const pt = tam / 2;
  const porCaracter = pt * 20 * 0.56;
  const margen = 170;
  const indivisible = (t) => Math.max(...String(t).replace(/\*\*/g, '').split(/[ \-]+/).map((x) => x.length), 1);
  const largoFila = (t) => Math.min(String(t).replace(/\*\*/g, '').length, 95);
  const minimo = cabeza.map((c, i) => Math.max(Math.ceil(indivisible(c) * porCaracter * 1.1) + margen, ...filas.map((f) => Math.ceil(indivisible(f[i] ?? '') * porCaracter) + margen), 420));
  const deseado = cabeza.map((c, i) => Math.max(minimo[i], Math.ceil(Math.max(largoFila(c) * 0.6, ...filas.map((f) => largoFila(f[i] ?? ''))) * porCaracter) + margen));
  const sumaMin = minimo.reduce((a, b) => a + b, 0);
  const holgura = deseado.reduce((a, b, i) => a + b - minimo[i], 0);
  let a;
  if (sumaMin >= ancho) {
    a = minimo.map((m) => Math.floor((m * ancho) / sumaMin));
  } else if (sumaMin + holgura <= ancho) {
    const extra = (ancho - sumaMin - holgura) / cabeza.length;
    a = deseado.map((d) => Math.floor(d + extra));
  } else {
    const f = (ancho - sumaMin) / holgura;
    a = minimo.map((m, i) => Math.floor(m + (deseado[i] - m) * f));
  }
  a[a.length - 1] += ancho - a.reduce((x, y) => x + y, 0);
  return a;
}

function celda(texto, ancho, o) {
  const b = { style: BorderStyle.SINGLE, size: 4, color: BORDE };
  return new TableCell({
    width: { size: ancho, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 70, right: 70 },
    borders: { top: b, bottom: b, left: b, right: b },
    shading: o.fondo ? { type: ShadingType.CLEAR, color: 'auto', fill: o.fondo } : undefined,
    children: [new Paragraph({ keepNext: o.unir, children: ricos(String(texto), { size: o.tam, bold: o.negrita, color: o.color }) })],
  });
}

function tabla(cabeza, filas, medidas, tam) {
  const n = filas.length;
  const unirFila = (i) => n <= 6 ? i < n - 1 : (i === 0 || i >= n - 3 && i < n - 1);
  return new Table({
    width: { size: medidas.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: medidas,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: cabeza.map((t, i) => celda(t, medidas[i], { fondo: AZUL, color: 'FFFFFF', negrita: true, tam, unir: true })) }),
      ...filas.map((f, j) => new TableRow({ cantSplit: true, children: f.map((t, i) => celda(t, medidas[i], { tam, unir: unirFila(j) })) })),
    ],
  });
}

let seccion = VERTICAL;

function imagen(ruta, pie) {
  const datos = fs.readFileSync(path.resolve(path.dirname(entrada), ruta));
  const ancho = datos.readUInt32BE(16);
  const alto = datos.readUInt32BE(20);
  const w = Math.round(seccion.ancho / 15);
  const h = Math.min(Math.round((w * alto) / ancho), seccion.alto);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 }, children: [new ImageRun({ type: 'png', data: datos, transformation: { width: Math.round((h * ancho) / alto), height: h }, altText: { title: pie, description: pie, name: path.basename(ruta) } })] }),
    W.NOTA(limpiar(pie)),
  ];
}

const secciones = [];
let hijos = [
  new Paragraph({ children: [new TextRun({ text: titulo, bold: true, size: 36, color: AZUL })], spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: subtitulo, size: 23, color: '404040' })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: FECHA, size: 18, color: '595959' })], spacing: { after: 240 } }),
];
let terminoEnTabla = false;

function cerrarSeccion() {
  if (!hijos.length) return;
  if (terminoEnTabla) hijos[hijos.length - 1] = new Paragraph({ children: [], spacing: { before: 0, after: 0, line: 20, lineRule: 'exact' } });
  secciones.push({ properties: { page: seccion.pagina }, footers: { default: W.pie(titulo) }, children: hijos });
  hijos = [];
  terminoEnTabla = false;
}

function siguiente(i) {
  for (let j = i + 1; j < lineas.length; j += 1) if (lineas[j].trim()) return lineas[j].startsWith('<!--') ? '' : lineas[j];
  return '';
}

for (let i = 0; i < lineas.length; i += 1) {
  const l = lineas[i];
  if (!l.trim()) continue;
  const prox = siguiente(i);
  if (l.trim() === '<!-- apaisada -->') {
    if (secciones.length || hijos.length > 3) cerrarSeccion();
    seccion = APAISADA;
    continue;
  }
  if (l.trim() === '<!-- vertical -->') {
    cerrarSeccion();
    seccion = VERTICAL;
    continue;
  }
  terminoEnTabla = false;
  const img = l.match(/^!\[(.*)\]\((.*)\)\s*$/);
  if (img) {
    hijos.push(...imagen(img[2], img[1]));
  } else if (l.startsWith('```')) {
    i += 1;
    while (i < lineas.length && !lineas[i].startsWith('```')) {
      hijos.push(new Paragraph({ children: [new TextRun({ text: lineas[i], font: 'Consolas', size: 16 })], spacing: { after: 0 } }));
      i += 1;
    }
    hijos.push(new Paragraph({ children: [], spacing: { after: 100 } }));
  } else if (l.startsWith('### ')) {
    hijos.push(W.H2(limpiar(l.slice(4))));
  } else if (l.startsWith('## ')) {
    hijos.push(W.H2(limpiar(l.slice(3))));
  } else if (l.startsWith('# ')) {
    hijos.push(W.H1(limpiar(l.slice(2))));
  } else if (/^\s*- /.test(l)) {
    const nivel = /^\s{2,}- /.test(l) ? 1 : 0;
    hijos.push(vineta(limpiar(l.replace(/^\s*- /, '')), nivel, nivel === 0 && /^\s{2,}- /.test(prox)));
  } else if (l.startsWith('|')) {
    const fila = (x) => x.trim().replace(/^\||\|$/g, '').split(/(?<!\\)\|/).map((c) => limpiar(c.trim()));
    const cabeza = fila(l);
    i += 2;
    const filas = [];
    while (i < lineas.length && lineas[i].startsWith('|')) {
      filas.push(fila(lineas[i]));
      i += 1;
    }
    i -= 1;
    if (filas.some((f) => f.length !== cabeza.length)) throw new Error(`Tabla con columnas desiguales: ${l.slice(0, 120)}`);
    const tam = cabeza.length > 5 ? (seccion === APAISADA ? 16 : 15) : 17;
    hijos.push(tabla(cabeza, filas, anchos(cabeza, filas, seccion.ancho, tam), tam));
    hijos.push(new Paragraph({ children: [], spacing: { after: 120 } }));
    terminoEnTabla = true;
  } else if (l.startsWith('> ')) {
    hijos.push(W.NOTA(limpiar(l.slice(2))));
  } else {
    const soloNegrita = /^\*\*[^*]+\*\*:?$/.test(l.trim());
    const anuncia = /^\s*(- |\||!\[)/.test(prox);
    hijos.push(W.P(limpiar(l), soloNegrita || anuncia ? { keepNext: true } : {}));
  }
}
cerrarSeccion();

const doc = new Document({ styles: W.estilos, numbering: numeracion, sections: secciones });
Packer.toBuffer(doc).then((b) => fs.writeFileSync(salida, b));
