"""Gera uma coleção importável e um ambiente sem segredos reais."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
items = []

def request(name, method, path, body=None, token=None, code=200, script=''):
    req = {'method': method, 'header': [], 'url': '{{server_url}}' + path}
    req['auth'] = ({'type': 'bearer', 'bearer': [{'key': 'token', 'value': '{{' + token + '}}', 'type': 'string'}]} if token else {'type': 'noauth'})
    if body is not None:
        req['header'] = [{'key': 'Content-Type', 'value': 'application/json'}]
        req['body'] = {'mode': 'raw', 'raw': json.dumps(body, indent=2), 'options': {'raw': {'language': 'json'}}}
    tests = f"pm.test('HTTP {code}', () => pm.response.to.have.status({code}));\n"
    tests += "const body = pm.response.json();\n"
    if code < 300 and path != '/health':
        tests += "pm.test('Operacao bem-sucedida', () => pm.expect(body.success).to.eql(true));\n"
    tests += script
    items.append({'name': name, 'request': req, 'event': [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': tests.splitlines()}}]})

def save_id(obj, variable):
    return f"pm.collectionVariables.set('{variable}', body.data.{obj}._id || body.data.{obj}.id);"

def tokens(prefix):
    return f"pm.test('Token recebido', () => pm.expect(body.data.access_token).to.be.a('string').and.not.empty);\npm.collectionVariables.set('{prefix}_token', body.data.access_token);\npm.collectionVariables.set('{prefix}_refresh', body.data.refresh_token);"

request('01 - Saude da API', 'GET', '/health', script="pm.test('API saudavel', () => pm.expect(body.status).to.eql('healthy'));")
request('02 - Cadastrar participante', 'POST', '/api/v1/auth/signup', {'fullname': 'Participante Postman', 'email': '{{student_email}}', 'password': '{{test_password}}', 'role': 'user'}, code=201, script=save_id('auth', 'student_id'))
request('03 - Login participante', 'POST', '/api/v1/auth/login', {'email': '{{student_email}}', 'password': '{{test_password}}'}, script=tokens('student'))
request('04 - Meu perfil', 'GET', '/api/v1/auth/me', token='student_token', script="pm.test('Conta correta', () => pm.expect(body.data.auth._id || body.data.auth.id).to.eql(pm.collectionVariables.get('student_id')));")
request('05 - Cadastrar empresa', 'POST', '/api/v1/auth/signup/company', {'razao_social': 'Empresa Teste Postman', 'cnpj': '{{test_cnpj}}', 'email': '{{company_email}}', 'password': '{{test_password}}'}, code=201, script=save_id('auth', 'company_id'))
request('06 - Login empresa', 'POST', '/api/v1/auth/login', {'email': '{{company_email}}', 'password': '{{test_password}}'}, script=tokens('company'))
request('07 - Criar evento', 'POST', '/api/v1/events', {'name': 'Curso Teste Postman', 'institution': 'Empresa Teste Postman', 'description': 'Evento criado para verificacao local', 'workload': 8, 'start_date': '2026-10-05T12:00:00Z', 'end_date': '2026-10-05T20:00:00Z'}, token='company_token', code=201, script=save_id('event', 'event_id'))
request('08 - Consultar evento', 'GET', '/api/v1/events/{{event_id}}')
request('09 - Editar evento', 'PUT', '/api/v1/events/{{event_id}}', {'description': 'Evento atualizado pelo Postman'}, token='company_token')
request('10 - Emitir certificado', 'POST', '/api/v1/certificate/{{student_id}}', {'fullname': 'Participante Postman', 'email': '{{student_email}}', 'access_key': '{{access_key_system}}', 'event_id': '{{event_id}}', 'status': 'available'}, token='company_token', code=201, script=save_id('certificate', 'certificate_id') + "\npm.collectionVariables.set('certificate_key', body.data.certificate.access_key);")
request('11 - Validacao publica', 'GET', '/api/v1/certificate/validate/{{certificate_key}}')
request('12 - Certificados do participante', 'GET', '/api/v1/certificate/users/{{student_id}}', token='student_token', script="pm.test('Certificado listado', () => pm.expect(body.data.items.map(c => c._id || c.id)).to.include(pm.collectionVariables.get('certificate_id')));")
request('13 - Consultar certificado', 'GET', '/api/v1/certificate/{{certificate_id}}', token='student_token')
request('14 - Renovar sessao', 'POST', '/api/v1/auth/refresh', {'refresh_token': '{{student_refresh}}'}, script=tokens('student'))
request('15 - Perfil apos renovacao', 'GET', '/api/v1/auth/me', token='student_token')
request('16 - Logout participante', 'POST', '/api/v1/auth/logout', {'refresh_token': '{{student_refresh}}'}, token='student_token')

pre = """const suffix = Date.now().toString() + Math.floor(Math.random() * 10000);
pm.collectionVariables.set('student_email', 'student.' + suffix + '@example.com');
pm.collectionVariables.set('company_email', 'company.' + suffix + '@example.com');
let digits = Array.from({length: 12}, () => Math.floor(Math.random() * 10));
function check(weights) { const s = digits.reduce((sum, d, i) => sum + d * weights[i], 0); const r = s % 11; return r < 2 ? 0 : 11 - r; }
digits.push(check([5,4,3,2,9,8,7,6,5,4,3,2]));
digits.push(check([6,5,4,3,2,9,8,7,6,5,4,3,2]));
pm.collectionVariables.set('test_cnpj', digits.join(''));
"""
items[0]['event'].insert(0, {'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': pre.splitlines()}})
collection = {'info': {'name': 'Certify - Teste local completo', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json', 'description': 'Execute em ordem. Cria contas, evento e certificado de teste no MongoDB local. Tokens e IDs sao capturados automaticamente. Configure access_key_system no ambiente local.'}, 'variable': [{'key': 'server_url', 'value': 'http://localhost:8000'}, {'key': 'test_password', 'value': 'PostmanTeste123!'}], 'item': items}
environment = {'name': 'Certify Local', 'values': [{'key': 'server_url', 'value': 'http://localhost:8000', 'enabled': True}, {'key': 'access_key_system', 'value': '', 'type': 'secret', 'enabled': True}], '_postman_variable_scope': 'environment'}
ROOT.mkdir(exist_ok=True)
for filename, value in [('Certify-Local.postman_collection.json', collection), ('Certify-Local.postman_environment.json', environment)]:
    (ROOT / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
