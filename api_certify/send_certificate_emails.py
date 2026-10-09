"""Process pending certificate notifications; suitable for a scheduled job."""

import asyncio

from api_certify.core.database.mongodb import (
    db_mongo,
    mongodb_connect,
    mongodb_disconnect,
)
from api_certify.repositories.auth_repository import AuthRepository
from api_certify.service.certificate_email_service import (
    CertificateEmailService,
)


async def main():
    await mongodb_connect()
    try:
        database = await db_mongo.get_database()
        service = CertificateEmailService(
            database.get_collection('certificates'), AuthRepository(database)
        )
        await service.dispatch_pending()
    finally:
        await mongodb_disconnect()


if __name__ == '__main__':
    asyncio.run(main())
