const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, PageNumber, Footer, Header, TableOfContents, PageBreak,
  LevelFormat, convertMillimetersToTwip, TabStopType, VerticalAlign
} = require('docx');
const fs = require('fs');

const NAVY = '1A3A5C';
const ACCENT = '8A6D3B';
const GREY = '5A6672';
const LIGHT = 'EEF2F6';
const BAND = 'DCE4EC';
const TW = 9638; // usable width DXA (A4 - 2cm margins)

const F = 'Calibri';

// ---------- helpers ----------
const P = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after === undefined ? 120 : o.after, before: o.before || 0, line: o.line || 276 },
  indent: o.indent,
  border: o.border,
  shading: o.shading,
  children: [new TextRun({ text, font: F, size: o.size || 21, color: o.color || '222222', bold: o.bold, italics: o.italics })]
});

// rich paragraph from array of {t, b, i, c}
const RP = (runs, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after === undefined ? 120 : o.after, before: o.before || 0, line: o.line || 276 },
  indent: o.indent,
  border: o.border,
  shading: o.shading,
  children: runs.map(r => new TextRun({
    text: r.t, font: F, size: r.size || o.size || 21,
    color: r.c || o.color || '222222', bold: r.b, italics: r.i
  }))
});

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 380, after: 180 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 6 } },
  children: [new TextRun({ text, font: F, size: 30, bold: true, color: NAVY })]
});

const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 300, after: 130 },
  children: [new TextRun({ text, font: F, size: 24, bold: true, color: NAVY })]
});

const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 220, after: 100 },
  children: [new TextRun({ text, font: F, size: 21, bold: true, color: ACCENT })]
});

const BUL = (text, o = {}) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  spacing: { after: o.after === undefined ? 80 : o.after, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text, font: F, size: 21, color: '222222' })]
});

const BULR = (runs, o = {}) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  spacing: { after: o.after === undefined ? 80 : o.after, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: runs.map(r => new TextRun({ text: r.t, font: F, size: 21, color: r.c || '222222', bold: r.b, italics: r.i }))
});

const NUMP = (runs, o = {}) => new Paragraph({
  numbering: { reference: 'numbers', level: 0 },
  spacing: { after: o.after === undefined ? 110 : o.after, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: runs.map(r => new TextRun({ text: r.t, font: F, size: 21, color: r.c || '222222', bold: r.b, italics: r.i }))
});

// table cell
const TC = (content, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
  margins: { top: 70, bottom: 70, left: 100, right: 100 },
  verticalAlign: VerticalAlign.CENTER,
  children: Array.isArray(content) ? content : [new Paragraph({
    alignment: o.align || AlignmentType.LEFT,
    spacing: { after: 0, line: 250 },
    children: [new TextRun({
      text: String(content), font: F, size: o.size || 18,
      bold: o.bold, color: o.color || (o.head ? 'FFFFFF' : '222222'), italics: o.italics
    })]
  })]
});

const THEAD = (cells, widths) => new TableRow({
  tableHeader: true,
  children: cells.map((c, i) => TC(c, widths[i], { fill: NAVY, head: true, bold: true, align: AlignmentType.LEFT }))
});

const TROW = (cells, widths, o = {}) => new TableRow({
  children: cells.map((c, i) => TC(c, widths[i], {
    fill: o.fill || (o.zebra ? LIGHT : undefined),
    bold: (o.boldFirst && i === 0) || o.bold,
    color: o.color,
    align: o.aligns ? o.aligns[i] : AlignmentType.LEFT,
    size: o.size
  }))
});

const TBL = (rows, widths) => new Table({
  columnWidths: widths,
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    left: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    right: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 3, color: BAND },
    insideVertical: { style: BorderStyle.SINGLE, size: 3, color: BAND }
  },
  rows
});

const SPACER = (h) => new Paragraph({ spacing: { after: h || 120 }, children: [] });

// callout box
const BOX = (title, body, fill) => new Table({
  columnWidths: [TW],
  width: { size: TW, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    left: { style: BorderStyle.SINGLE, size: 24, color: ACCENT },
    right: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    insideHorizontal: { style: BorderStyle.NONE },
    insideVertical: { style: BorderStyle.NONE }
  },
  rows: [new TableRow({
    children: [new TableCell({
      width: { size: TW, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: fill || LIGHT, color: 'auto' },
      margins: { top: 130, bottom: 130, left: 180, right: 180 },
      children: [
        new Paragraph({ spacing: { after: 70 }, children: [new TextRun({ text: title, font: F, size: 20, bold: true, color: NAVY })] }),
        ...body.map(b => new Paragraph({
          alignment: AlignmentType.JUSTIFIED, spacing: { after: 60, line: 264 },
          children: [new TextRun({ text: b, font: F, size: 19, color: '2A3340' })]
        }))
      ]
    })]
  })]
});

