from fastapi import UploadFile

from app.exceptions.http import AppHTTPError
from app.exceptions.messages import FILE_MISSING, INVALID_XLSX_FILE, NOT_XLSX_FILE

XLSX_MAGIC_BYTES = b"PK\x03\x04"


async def validate_xlsx_file(file: UploadFile) -> UploadFile:
    if file.size == 0:
        raise AppHTTPError.bad_request(FILE_MISSING)

    if file.filename and not file.filename.endswith(".xlsx"):
        raise AppHTTPError.bad_request(NOT_XLSX_FILE.format(filename=file.filename))

    header = await file.read(4)
    await file.seek(0)

    if header != XLSX_MAGIC_BYTES:
        raise AppHTTPError.bad_request(INVALID_XLSX_FILE.format(filename=file.filename))

    return file


async def validate_sup_file(sup_file: UploadFile) -> UploadFile:
    return await validate_xlsx_file(sup_file)


async def validate_nac_file(nac_file: UploadFile) -> UploadFile:
    return await validate_xlsx_file(nac_file)
