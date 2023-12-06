# fastapi定义接口

from fastapi import FastAPI

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
