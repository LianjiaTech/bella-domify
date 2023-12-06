# fastapi定义接口

from fastapi import FastAPI
from fastapi import File, UploadFile

from pdf2docx import Converter

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/actuator/health/liveness")
async def health_liveness():
    return {"status": "UP"}


@app.get("/actuator/health/readiness")
async def health_readiness():
    return {"status": "UP"}

# 上传文件接口
@app.post("/pdf/parse/test")
async def create_upload_file(file: UploadFile = File(...)):
    # 读取file字节流
    contents = await file.read()
    converter = Converter(stream=contents)
    tables = converter.extract_tables(
        start=0, end=1,
        # extract_table_with_cell_pos=True,
        # remove_watermark=True,
        # debug=True,
        # debug_file_name=test_dir + "frt-debug.pdf",
        sematic_parse=True,
        # parse_stream_table=False
    )

    return {"filename": file.filename}
