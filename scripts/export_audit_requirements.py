"""Export exact runtime package versions from the Poetry lock for pip-audit."""
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parent.parent
lock = tomllib.loads((root / 'poetry.lock').read_text(encoding='utf-8'))
requirements = sorted({
    f"{package['name']}=={package['version']}"
    for package in lock['package']
    if 'main' in package.get('groups', [])
})
if not requirements:
    raise SystemExit('No runtime dependencies found in poetry.lock')
print('\n'.join(requirements))
