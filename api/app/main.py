from fastapi import FastAPI

app = FastAPI(title="ChatterBox API")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
