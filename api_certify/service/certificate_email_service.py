import asyncio
import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from html import escape
from urllib.parse import quote, urlparse

from pymongo import ReturnDocument


class SMTPTransport:
    def __init__(self):
        self.host = os.getenv('SMTP_HOST', '')
        self.port = int(os.getenv('SMTP_PORT', '587'))
        self.sender = os.getenv('SMTP_FROM', '')
        self.username = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.security = os.getenv('SMTP_SECURITY', 'starttls')

    def send(self, message: EmailMessage):
        if self.security not in {'ssl', 'starttls', 'none'}:
            raise ValueError('Invalid SMTP_SECURITY')
        client = smtplib.SMTP_SSL if self.security == 'ssl' else smtplib.SMTP
        kwargs = {'timeout': 30}
        if self.security == 'ssl':
            kwargs['context'] = ssl.create_default_context()
        with client(self.host, self.port, **kwargs) as connection:
            if self.security == 'starttls':
                connection.starttls(context=ssl.create_default_context())
            if self.username:
                connection.login(self.username, self.password)
            refused = connection.send_message(message)
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)


class CertificateEmailService:
    def __init__(
        self, collection, auth_repository, transport=None, frontend_url=None
    ):
        self.collection = collection
        self.auth_repository = auth_repository
        self.transport = transport or SMTPTransport()
        self.frontend_url = (
            frontend_url or os.getenv('FRONTEND_URL', '')
        ).rstrip('/')

    def _message(self, certificate, audience, recipient):
        event = certificate['event_name']
        participant = certificate['participant_name']
        validation_url = f'{self.frontend_url}/validar-certificado/{quote(certificate["access_key"], safe="")}'
        portal_url = f'{self.frontend_url}/meus-certificados'
        if audience == 'student':
            subject = 'Seu certificado está disponível'
            text = f'Olá, {participant}!\nSeu certificado de {event} foi emitido por {certificate["institution_name"]}.\n'
        else:
            subject = 'Confirmação de emissão de certificado'
            text = f'O certificado de {participant} para {event} foi emitido com sucesso.\n'
        text += f'Carga horária: {certificate["workload"]}\nValidar certificado: {validation_url}\nAcessar certificados (aluno cadastrado): {portal_url}\n'
        message = EmailMessage()
        message['From'] = self.transport.sender
        message['To'] = recipient
        message['Subject'] = subject
        domain = parseaddr(self.transport.sender)[1].rsplit('@', 1)[-1]
        message['Message-ID'] = (
            f'<certificate-{certificate["_id"]}-{audience}@{domain}>'
        )
        message.set_content(text)
        message.add_alternative(
            '<html><body><p>'
            + escape(text).replace('\n', '<br>')
            + '</p>'
            + f'<a href="{escape(validation_url, quote=True)}">Validar certificado</a></body></html>',
            subtype='html',
        )
        return message

    async def dispatch_pending(self, limit=200):
        parsed = urlparse(self.frontend_url)
        if (
            not self.transport.host
            or not self.transport.sender
            or parsed.scheme not in {'http', 'https'}
            or not parsed.netloc
        ):
            return
        for audience in ('student', 'company'):
            prefix = f'notifications.{audience}'
            for _ in range(limit):
                now = datetime.now(timezone.utc)
                eligible = {
                    '$or': [
                        {f'{prefix}.status': 'pending'},
                        {
                            f'{prefix}.status': 'failed',
                            f'{prefix}.retry_at': {'$lte': now},
                        },
                        {
                            f'{prefix}.status': 'sending',
                            f'{prefix}.claimed_at': {
                                '$lte': now - timedelta(minutes=5)
                            },
                        },
                    ]
                }
                certificate = await self.collection.find_one_and_update(
                    eligible,
                    {
                        '$set': {
                            f'{prefix}.status': 'sending',
                            f'{prefix}.claimed_at': now,
                        },
                        '$inc': {f'{prefix}.attempts': 1},
                    },
                    return_document=ReturnDocument.AFTER,
                )
                if not certificate:
                    break
                try:
                    if audience == 'student':
                        recipient = certificate['participant_email']
                    else:
                        issuer = await self.auth_repository.get_user_by_id(
                            certificate['issuer_id']
                        )
                        recipient = issuer.email
                    message = self._message(certificate, audience, recipient)
                    await asyncio.to_thread(self.transport.send, message)
                except Exception as error:
                    fields = {
                        f'{prefix}.status': 'failed',
                        f'{prefix}.error': type(error).__name__,
                        f'{prefix}.retry_at': datetime.now(timezone.utc)
                        + timedelta(minutes=5),
                    }
                else:
                    fields = {
                        f'{prefix}.status': 'sent',
                        f'{prefix}.sent_at': datetime.now(timezone.utc),
                        f'{prefix}.error': None,
                    }
                await self.collection.update_one(
                    {
                        '_id': certificate['_id'],
                        f'{prefix}.status': 'sending',
                        f'{prefix}.claimed_at': now,
                    },
                    {'$set': fields},
                )
