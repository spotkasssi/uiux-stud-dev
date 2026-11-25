from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
ROOT=Path(__file__).resolve().parent
env=Environment(loader=FileSystemLoader(ROOT),autoescape=select_autoescape(['html']))
for name in ['index','states']:
    (ROOT/f'{name}.html').write_text(env.get_template(f'pages/{name}.html').render(),encoding='utf-8')
print('Сборка готова: index.html, states.html')
