// Funciones comunes de los documentos Word del cierre de las Fases 34 y 35.
const { Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, AlignmentType,
  HeadingLevel, Footer, PageNumber, LevelFormat, VerticalAlign } = require('docx');

const AZUL = '1F4E79', CELESTE = 'DCE6F1', BORDE = 'BFBFBF', FUENTE = 'Arial';
const ANCHO = 9360;

function ricos(texto, base = {}) {
  return String(texto).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((t) => (t.startsWith('**')
    ? new TextRun({ text: t.slice(2, -2), bold: true, ...base }) : new TextRun({ text: t, ...base })));
}
const P = (t, o = {}) => new Paragraph({ children: ricos(t), spacing: { after: 120, line: 276 }, ...o });
const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1 });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2 });
const LI = (t) => new Paragraph({ children: ricos(t), numbering: { reference: 'vinetas', level: 0 }, spacing: { after: 70, line: 264 } });
const TIT = (t) => new Paragraph({ children: [new TextRun({ text: t, bold: true, size: 18, color: AZUL })], spacing: { before: 160, after: 60 }, keepNext: true });
const NOTA = (t) => new Paragraph({ children: ricos(t, { size: 16, italics: true, color: '595959' }), spacing: { before: 60, after: 160 } });

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
      new TableRow({ tableHeader: true, cantSplit: true, children: cabeza.map((t, i) => celda(t, anchos[i], { fondo: AZUL, color: 'FFFFFF', negrita: true, tam: o.tam })) }),
      ...filas.map((f) => new TableRow({ cantSplit: true, children: f.map((t, i) => celda(t, anchos[i], { tam: o.tam, fondo: o.resaltar && o.resaltar(f) ? CELESTE : undefined })) })),
    ],
  });
}
const estilos = {
  default: { document: { run: { font: FUENTE, size: 20 } } },
  paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FUENTE, size: 27, bold: true, color: AZUL }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FUENTE, size: 22, bold: true, color: AZUL }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
  ],
};
const numeracion = {
  config: [{ reference: 'vinetas', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] }],
};
const pie = (texto) => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `${texto} · `, size: 15, color: '7F7F7F' }), new TextRun({ children: [PageNumber.CURRENT], size: 15, color: '7F7F7F' })] })] });
const PAG = { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } };
const portada = (titulo, sub) => [
  new Paragraph({ children: [new TextRun({ text: titulo, bold: true, size: 36, color: AZUL })], spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: sub, size: 23, color: '404040' })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: 'AgingWomen · Conjunto sintético de usuarias · 4 de noviembre de 2026', size: 18, color: '595959' })], spacing: { after: 240 } }),
];
// Número con coma decimal.
const c = (x, d = 3) => Number(x).toFixed(d).replace('.', ',').replace('-', '−');
module.exports = { ANCHO, P, H1, H2, LI, TIT, NOTA, tabla, estilos, numeracion, pie, PAG, portada, c };
