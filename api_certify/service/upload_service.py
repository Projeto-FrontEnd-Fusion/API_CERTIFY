import os
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).parent.parent.parent / "uploads")))
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


class UploadService:

    @staticmethod
    def _validate_file(file: UploadFile):
        # Validar extensão
        ext = Path(file.filename).suffix.lower() if file.filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Formato não suportado. Aceitos: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        return ext

    @staticmethod
    async def _validate_size(file: UploadFile):
        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo excede o tamanho máximo de 2MB",
            )

        # Voltar o cursor para o início
        await file.seek(0)
        return content

    @staticmethod
    async def _remove_old_file(directory: Path, user_id: str):
        for ext in ALLOWED_EXTENSIONS:
            old_file = directory / f"{user_id}{ext}"
            if old_file.exists():
                os.remove(old_file)

    async def upload_logo(self, user_id: str, file: UploadFile) -> str:
        ext = self._validate_file(file)
        content = await self._validate_size(file)

        logo_dir = UPLOAD_DIR / "logos"
        logo_dir.mkdir(parents=True, exist_ok=True)

        # Remover logo anterior
        await self._remove_old_file(logo_dir, user_id)

        filename = f"{user_id}{ext}"
        filepath = logo_dir / filename

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        return f"/static/uploads/logos/{filename}"

    async def upload_signature(self, user_id: str, file: UploadFile) -> str:
        ext = self._validate_file(file)
        content = await self._validate_size(file)

        sig_dir = UPLOAD_DIR / "signatures"
        sig_dir.mkdir(parents=True, exist_ok=True)

        # Remover assinatura anterior
        await self._remove_old_file(sig_dir, user_id)

        filename = f"{user_id}{ext}"
        filepath = sig_dir / filename

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        return f"/static/uploads/signatures/{filename}"

    async def upload_avatar(self, user_id: str, file: UploadFile) -> str:
        from uuid import uuid4
        ext = Path(file.filename or "").suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg"} or file.content_type not in {"image/png", "image/jpeg"}:
            raise HTTPException(status_code=415, detail="Envie uma imagem PNG ou JPG")
        content = await file.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="A imagem deve ter no máximo 5MB")
        if not content or not (content.startswith(b"\x89PNG\r\n\x1a\n") or content.startswith(b"\xff\xd8\xff")):
            raise HTTPException(status_code=415, detail="Imagem inválida")
        directory = UPLOAD_DIR / "avatars"
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{user_id}_{uuid4().hex}{ext}"
        async with aiofiles.open(directory / filename, "wb") as output:
            await output.write(content)
        return f"/static/uploads/avatars/{filename}"
