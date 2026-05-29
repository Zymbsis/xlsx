from fastapi import HTTPException, UploadFile

XLSX_MAGIC_BYTES = b"PK\x03\x04"


async def validate_xlsx_file(file: UploadFile):
    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is missing")

    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400, detail=f"{file.filename} is not an xlsx file"
        )

    header = await file.read(4)
    await file.seek(0)

    if header != XLSX_MAGIC_BYTES:
        raise HTTPException(
            status_code=400, detail=f"{file.filename} is not a valid xlsx file"
        )

    return file


async def validate_sup_file(sup_file: UploadFile) -> UploadFile:
    return await validate_xlsx_file(sup_file)


async def validate_nac_file(nac_file: UploadFile) -> UploadFile:
    return await validate_xlsx_file(nac_file)
