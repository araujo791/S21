"""Gera o manual HTML independente e um ZIP para leitura offline/impressão."""
import argparse
import base64
from html import escape
from pathlib import Path
import re
import zipfile

from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='ZIP de saída do manual.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    app = QApplication.instance() or QApplication([])
    document = QTextDocument()
    document.setMarkdown((root / 'MANUAL.md').read_text(encoding='utf-8'))
    markup = document.toHtml()
    picture = base64.b64encode((root / 'docs/janela.png').read_bytes()).decode('ascii')
    markup = markup.replace('src="docs/janela.png"', 'src="data:image/png;base64,' + picture + '"')
    markup = markup.replace('<head>', '<head><meta name="viewport" content="width=device-width, initial-scale=1">'
                            '<title>' + escape('Manual — Covenant Graphics Studio 0.1.1') + '</title>')
    style = '''<style>
body { max-width: 1000px; margin: 2em auto; padding: 0 1.2em; color: #172130;
       background: white; font-family: Arial, sans-serif; line-height: 1.6; }
h1, h2, h3 { color: #163c55; line-height: 1.25; }
h2 { margin-top: 2em; border-bottom: 1px solid #ccd4dc; padding-bottom: .3em; }
img { max-width: 100%; height: auto; }
table { width: 100%; border-collapse: collapse; margin: 1em 0; }
td, th { border: 1px solid #ccd4dc; padding: .45em .6em; vertical-align: top; }
pre { background: #f1f4f7; padding: 1em; overflow-x: auto; white-space: pre-wrap; }
a { color: #175a9c; }
@media print {
  body { max-width: none; margin: 0; padding: 0; font-size: 10pt; }
  h1, h2, h3 { break-after: avoid; } tr, img, pre { break-inside: avoid; }
  thead { display: table-header-group; }
}
</style>'''
    markup = markup.replace('</head>', style + '</head>')
    markup = re.sub(r'<body[^>]*>', '<body>', markup, count=1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('Manual-Covenant-Graphics-Studio/ABRA-ME.txt',
                         'Abra MANUAL.html para ler o manual offline.\n'
                         'Para salvar em PDF, use Ctrl+P e escolha Salvar como PDF ou Microsoft Print to PDF.\n'
                         'MANUAL.md e docs/janela.png são a versão em Markdown e sua ilustração.\n')
        archive.writestr('Manual-Covenant-Graphics-Studio/MANUAL.html', markup.encode('utf-8'))
        for relative in ('MANUAL.md', 'docs/janela.png'):
            archive.write(root / relative, 'Manual-Covenant-Graphics-Studio/' + relative)
    print(args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
