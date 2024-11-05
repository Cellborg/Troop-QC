from .util import get_settings
from fastapi import FastAPI
from .routes import router

app = FastAPI(title="Cellborg QC API")

# Register routes
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Welcome to Cellborg's QC API!"}


@app.on_event("startup")
def startup_event():
    settings = get_settings()
    print(
        f"Cellborg QCProcessing Python container running in environment: {settings.environment}"
    )
