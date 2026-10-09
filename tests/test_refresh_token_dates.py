from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from api_certify.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.mark.asyncio
@pytest.mark.parametrize('aware', [False, True])
@pytest.mark.parametrize('expired', [False, True])
async def test_refresh_token_expiration_with_mongo_dates(aware, expired):
    expires = datetime.now(timezone.utc) + timedelta(days=-1 if expired else 1)
    if not aware:
        expires = expires.replace(tzinfo=None)
    document = {'expires_at': expires, 'revoked': False}
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=document)
    collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    database = MagicMock()
    database.get_collection.return_value = collection
    repository = RefreshTokenRepository(database)

    result = await repository.find_valid_token('test-token')

    if expired:
        assert result is None
        collection.update_one.assert_awaited_once()
    else:
        assert result is document
        collection.update_one.assert_not_awaited()
