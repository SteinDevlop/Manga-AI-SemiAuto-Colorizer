from fastapi import FastAPI

app = FastAPI(title="Manga Colorizer API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check placeholder."""
    return {"status": "ok"}
