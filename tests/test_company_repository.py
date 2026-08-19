import pytest
from mongomock_motor import AsyncMongoMockClient

from api_certify.repositories.auth_repository import AuthRepository
from api_certify.models.auth_model import CompanyUser


@pytest.mark.asyncio
async def test_create_company_success():
    client = AsyncMongoMockClient()
    db = client["CERTIFY"]

    repo = AuthRepository(db)

    payload = CompanyUser(
        razao_social="Empresa Teste Ltda",
        cnpj="12.345.678/0001-95",
        email="contato@empresa.com",
        password="SenhaSegura123!",
        phone="(11) 99999-8888",
    )

    result = await repo.create_company(payload)

    assert result.email == "contato@empresa.com"
    assert result.razao_social == "Empresa Teste Ltda"
    assert result.cnpj == "12345678000195"
    assert result.role == "empresa"


@pytest.mark.asyncio
async def test_create_company_invalid_cnpj():
    client = AsyncMongoMockClient()
    db = client["CERTIFY"]

    repo = AuthRepository(db)

    payload = CompanyUser(
        razao_social="Empresa Teste Ltda",
        cnpj="11.111.111/1111-11",
        email="contato@empresa.com",
        password="SenhaSegura123!",
    )

    with pytest.raises(Exception, match="CNPJ inválido"):
        await repo.create_company(payload)


@pytest.mark.asyncio
async def test_create_company_duplicate_cnpj_and_email():
    client = AsyncMongoMockClient()
    db = client["CERTIFY"]

    # Pre-insert a company with same cnpj and email
    await db.auth_database.insert_one({
        "razao_social": "Outra",
        "cnpj": "12345678000195",
        "email": "contato@empresa.com",
        "password": "x",
    })

    repo = AuthRepository(db)

    payload = CompanyUser(
        razao_social="Empresa Teste Ltda",
        cnpj="12.345.678/0001-95",
        email="contato@empresa.com",
        password="SenhaSegura123!",
    )

    # Expect CNPJ duplicate first
    with pytest.raises(Exception, match="CNPJ já cadastrado"):
        await repo.create_company(payload)

    # Remove the existing cnpj but keep email to test email duplicate
    await db.auth_database.delete_many({"cnpj": "12345678000195"})
    await db.auth_database.insert_one({
        "razao_social": "Outra",
        "cnpj": "99999999000100",
        "email": "contato@empresa.com",
        "password": "x",
    })

    with pytest.raises(Exception, match="Email já cadastrado"):
        await repo.create_company(payload)
