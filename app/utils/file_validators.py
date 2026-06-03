from fastapi import UploadFile

from app.exceptions.http import AppHTTPError

XLSX_MAGIC_BYTES = b"PK\x03\x04"


async def validate_xlsx_file(file: UploadFile) -> UploadFile:
    if file.size == 0:
        raise AppHTTPError.bad_request("File is missing")

    if file.filename and not file.filename.endswith(".xlsx"):
        detail = f"{file.filename} is not an xlsx file"
        raise AppHTTPError.bad_request(detail)

    header = await file.read(4)
    await file.seek(0)

    if header != XLSX_MAGIC_BYTES:
        detail = f"{file.filename} is not a valid xlsx file"
        raise AppHTTPError.bad_request(detail)

    return file


async def validate_sup_file(sup_file: UploadFile) -> UploadFile:
    return await validate_xlsx_file(sup_file)


async def validate_nac_file(nac_file: UploadFile) -> UploadFile:
    return await validate_xlsx_file(nac_file)
