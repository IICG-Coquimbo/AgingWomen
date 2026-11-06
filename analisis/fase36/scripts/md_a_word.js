// Convierte un Markdown sencillo (títulos, párrafos, viñetas, tablas y bloques de código) en Word, con el estilo de los informes del proyecto.
// Uso: node md_a_word.js entrada.md salida.docx "Título" "Subtítulo"
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun } = require('docx');
const W = require(path.resolve(__dirname, '../../cierre_fases_34_35/scripts/word_comun'));

const [entrada, salida, titulo, subtitulo] = process.argv.slice(2);
const FECHA = 'AgingWomen · Conjunto sintético de usuarias · 5 de noviembre de 2026';
const limpiar = (t) => t.replace(/`/g, '');
const lineas = fs.readFileSync(entrada, 'utf8').split(/\r?\n/);

function anchos(cabeza, filas) {
  const n = cabeza.length;
  const largo = cabeza.map((c, i) => Math.max(c.length, ...filas.map((f) => Math.min(String(f[i] ?? '').length, 70))));
  const raices = largo.map((x) => Math.sqrt(Math.max(x, 3)));
  const suma = raices.reduce((a, b) => a + b, 0);
  const a = raices.map((x) => Math.max(Math.round((W.ANCHO * x) / suma), 700));
  a[n - 1] += W.ANCHO - a.reduce((x, y) => x + y, 0);
  return a;
}

const hijos = [
  new Paragraph({ children: [new TextRun({ text: titulo, bold: true, size: 36, color: '1F4E79' })], spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: subtitulo, size: 23, color: '404040' })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: FECHA, size: 18, color: '595959' })], spacing: { after: 240 } }),
];

for (let i = 0; i < lineas.length; i += 1) {
  const l = lineas[i];
  if (!l.trim()) continue;
  if (l.startsWith('```')) {
    i += 1;
    while (i < lineas.length && !lineas[i].startsWith('```')) {
      hijos.push(new Paragraph({ children: [new TextRun({ text: lineas[i], font: 'Consolas', size: 16 })], spacing: { after: 0 } }));
      i += 1;
    }
    hijos.push(new Paragraph({ children: [], spacing: { after: 100 } }));
  } else if (l.startsWith('## ')) {
    hijos.push(W.H2(limpiar(l.slice(3))));
  } else if (l.startsWith('# ')) {
    hijos.push(W.H1(limpiar(l.slice(2))));
  } else if (l.startsWith('- ')) {
    hijos.push(W.LI(limpiar(l.slice(2))));
  } else if (l.startsWith('|')) {
    const fila = (x) => x.trim().replace(/^\||\|$/g, '').split('|').map((c) => limpiar(c.trim()));
    const cabeza = fila(l);
    i += 2;
    const filas = [];
    while (i < lineas.length && lineas[i].startsWith('|')) {
      filas.push(fila(lineas[i]));
      i += 1;
    }
    i -= 1;
    hijos.push(W.tabla(cabeza, filas, anchos(cabeza, filas), { tam: cabeza.length > 5 ? 15 : 17 }));
    hijos.push(new Paragraph({ children: [], spacing: { after: 120 } }));
  } else if (l.startsWith('> ')) {
    hijos.push(W.NOTA(limpiar(l.slice(2))));
  } else {
    hijos.push(W.P(limpiar(l)));
  }
}

const doc = new Document({
  styles: W.estilos, numbering: W.numeracion,
  sections: [{ properties: { page: W.PAG }, footers: { default: W.pie(titulo) }, children: hijos }],
});
Packer.toBuffer(doc).then((b) => fs.writeFileSync(salida, b));
