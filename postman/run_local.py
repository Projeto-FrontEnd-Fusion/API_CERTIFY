"""Executa Postman CLI sem gravar a chave real na coleção versionada."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
from dotenv import dotenv_values

env = json.loads((ROOT / 'Certify-Local.postman_environment.json').read_text(encoding='utf-8'))
key = dotenv_values(ROOT.parent / '.env').get('ACCESS_KEY')
if not key:
    raise SystemExit('Configure ACCESS_KEY em API_CERTIFY/.env antes de executar.')
for variable in env['values']:
    if variable['key'] == 'access_key_system':
        variable['value'] = key
cli = shutil.which('postman')
if not cli:
    raise SystemExit('Postman CLI nao encontrado no PATH.')
with tempfile.TemporaryDirectory(prefix='certify-postman-') as directory:
    path = Path(directory) / 'local.environment.json'
    path.write_text(json.dumps(env), encoding='utf-8')
    result = subprocess.run([cli, 'collection', 'run', str(ROOT / 'Certify-Local.postman_collection.json'), '-e', str(path), '--no-report-events', '--timeout-request', '15000'])
raise SystemExit(result.returncode)
