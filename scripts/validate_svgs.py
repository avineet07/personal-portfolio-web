#!/usr/bin/env python3
"""Static checks for the content-card SVG diagrams."""
import glob
import re
import xml.etree.ElementTree as ET

for f in sorted(glob.glob('src/assets/*.svg')):
    t = ET.parse(f).getroot()
    ids = [e.get('id') for e in t.iter() if e.get('id')]
    refs = {m for e in t.iter() for m in re.findall(r'url\(#([^)]+)\)', e.get('') or '')}
    problems = []
    if len(ids) != len(set(ids)):
        problems.append('duplicate ids: ' + str(ids))
    for r in refs:
        if r not in ids:
            problems.append(f'undefined ref #{r}')
    for g in t.iter('g'):
        w = int(g.get('width') or 0)
        h = int(g.get('height') or 0)
        for tx in g.iter('text'):
            s = tx.text or ''
            if not s:
                continue
            fs = float(re.search(r'font-size="([0-9.]+)"', tx.get('')).group(1))
            est = len(s) * fs * 0.52
            x = float(tx.get('x') or 0)
            if x + est > w - 2:
                problems.append(f'overflow x={x} est={est:.0f} w={w}: "{s[:34]}"')
            y = float(tx.get('y') or 0)
            if y > h - 2:
                problems.append(f'overflow-y y={y} h={h}: "{s[:34]}"')
    print(f'{f}: nodes={sum(1 for e in t.iter("g") if e.get("transform"))} ' + ('OK' if not problems else 'ISSUES'))
    for p in problems:
        print('   ', p)
