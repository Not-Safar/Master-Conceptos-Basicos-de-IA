"""Integra los módulos JS en el HTML para poder abrirlo como archivo único.

Ejecutar después de modificar route_search.js o route_ui.js:
    python sync_map.py
No genera ni modifica el grafo.
"""
from pathlib import Path

folder = Path(__file__).resolve().parent
path = folder / 'mexico_map.html'
html = path.read_text(encoding='utf-8')
for name in ['route_search.js', 'route_ui.js']:
    start = f'<!-- BEGIN INLINE {name} -->'
    end = f'<!-- END INLINE {name} -->'
    code = (folder / name).read_text(encoding='utf-8').replace('</script', '<\\/script')
    block = f'{start}\n<script>\n{code}\n</script>\n{end}'
    if start in html:
        left = html.index(start)
        right = html.index(end, left) + len(end)
        html = html[:left] + block + html[right:]
    else:
        external = f'<script src="{name}"></script>'
        if external not in html:
            raise ValueError(f'No se encontró el punto de inserción de {name}')
        html = html.replace(external, block)
path.write_text(html, encoding='utf-8')
print('HTML autónomo actualizado; grafo conservado.')
