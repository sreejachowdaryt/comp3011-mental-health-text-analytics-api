from fastapi import FastAPI

app = FastAPI(
    title="Mental Health Text Analytics API",
    version="0.1.0",
)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}