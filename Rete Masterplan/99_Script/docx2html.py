#!/usr/bin/env python3
"""Converte un .docx generato da build.js in HTML semantico, adatto
all'import di Google Drive (che lo trasforma in un Documento Google).
Preserva titoli, grassetto, corsivo, colori, tabelle ed elenchi."""
import sys, zipfile, html
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def numbering_map(z):
    """numId -> 'ul' | 'ol'"""
    out = {}
    try:
        num = ET.fromstring(z.read('word/numbering.xml'))
    except KeyError:
        return out
    abstract = {}
    for a in num.iter(W + 'abstractNum'):
        aid = a.get(W + 'abstractNumId')
        lvl = a.find(f'{W}lvl')
        fmt = lvl.find(f'{W}numFmt').get(W + 'val') if lvl is not None and lvl.find(f'{W}numFmt') is not None else 'bullet'
        abstract[aid] = 'ul' if fmt == 'bullet' else 'ol'
    for n in num.iter(W + 'num'):
        nid = n.get(W + 'numId')
        ref = n.find(f'{W}abstractNumId')
        if ref is not None:
            out[nid] = abstract.get(ref.get(W + 'val'), 'ul')
    return out

def runs_html(par):
    parts = []
    for r in par.findall(f'{W}r'):
        text = ''.join(t.text or '' for t in r.findall(f'{W}t'))
        if not text:
            if r.find(f'{W}br') is not None:
                parts.append('<br>')
            continue
        s = html.escape(text)
        rpr = r.find(f'{W}rPr')
        if rpr is not None:
            col = rpr.find(f'{W}color')
            c = col.get(W + 'val') if col is not None else None
            if c and c.lower() not in ('222222', 'auto', '000000'):
                s = f'<span style="color:#{c}">{s}</span>'
            if rpr.find(f'{W}i') is not None:
                s = f'<em>{s}</em>'
            if rpr.find(f'{W}b') is not None:
                s = f'<strong>{s}</strong>'
        parts.append(s)
    return ''.join(parts)

def par_info(par, nmap):
    ppr = par.find(f'{W}pPr')
    style, listkind = None, None
    if ppr is not None:
        st = ppr.find(f'{W}pStyle')
        if st is not None:
            style = st.get(W + 'val')
        npr = ppr.find(f'{W}numPr')
        if npr is not None:
            nid = npr.find(f'{W}numId')
            if nid is not None:
                listkind = nmap.get(nid.get(W + 'val'), 'ul')
    return style, listkind

def cell_html(tc, nmap):
    out = []
    for child in tc:
        if child.tag == W + 'p':
            inner = runs_html(child)
            if inner.strip():
                out.append(inner)
        elif child.tag == W + 'tbl':
            out.append(table_html(child, nmap))
    return '<br>'.join(out) if out else '&nbsp;'

def table_html(tbl, nmap):
    rows = tbl.findall(f'{W}tr')
    out = ['<table>']
    for i, tr in enumerate(rows):
        header = tr.find(f'{W}trPr/{W}tblHeader') is not None
        out.append('<tr>')
        for tc in tr.findall(f'{W}tc'):
            shd = tc.find(f'{W}tcPr/{W}shd')
            fill = shd.get(W + 'fill') if shd is not None else None
            style = f' style="background:#{fill}"' if fill and fill.lower() not in ('auto', 'ffffff') else ''
            tag = 'th' if header else 'td'
            out.append(f'<{tag}{style}>{cell_html(tc, nmap)}</{tag}>')
        out.append('</tr>')
    out.append('</table>')
    return ''.join(out)

def convert(path, title):
    z = zipfile.ZipFile(path)
    nmap = numbering_map(z)
    root = ET.fromstring(z.read('word/document.xml'))
    bodyel = root.find(f'{W}body')
    out, openlist = [], None

    def close_list():
        nonlocal openlist
        if openlist:
            out.append(f'</{openlist}>')
            openlist = None

    for el in bodyel:
        if el.tag == W + 'tbl':
            close_list()
            out.append(table_html(el, nmap))
        elif el.tag == W + 'p':
            style, listkind = par_info(el, nmap)
            inner = runs_html(el)
            if listkind:
                if openlist != listkind:
                    close_list()
                    out.append(f'<{listkind}>')
                    openlist = listkind
                out.append(f'<li>{inner}</li>')
                continue
            close_list()
            if not inner.strip():
                continue
            if style in ('Heading1', 'Heading2', 'Heading3'):
                lvl = style[-1]
                out.append(f'<h{lvl}>{inner}</h{lvl}>')
            else:
                out.append(f'<p>{inner}</p>')
    close_list()

    css = (
        'body{font-family:Calibri,Arial,sans-serif;font-size:11pt;color:#222;line-height:1.45}'
        'h1{font-size:19pt;color:#1A3A5C;border-bottom:1.5pt solid #1A3A5C;padding-bottom:4pt;margin-top:22pt}'
        'h2{font-size:14pt;color:#1A3A5C;margin-top:16pt}'
        'h3{font-size:12pt;color:#8A6D3B;margin-top:12pt}'
        'table{border-collapse:collapse;width:100%;margin:10pt 0;font-size:9.5pt}'
        'th,td{border:0.5pt solid #DCE4EC;padding:5pt 7pt;vertical-align:top;text-align:left}'
        'th{background:#1A3A5C;color:#fff;font-weight:bold}'
        'ul,ol{margin:6pt 0 6pt 18pt}li{margin-bottom:4pt}'
        'p{margin:5pt 0;text-align:justify}'
    )
    return (f'<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">'
            f'<title>{html.escape(title)}</title><style>{css}</style></head>'
            f'<body>{"".join(out)}</body></html>')

if __name__ == '__main__':
    sys.stdout.write(convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'Documento'))
