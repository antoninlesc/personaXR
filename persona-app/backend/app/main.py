from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import parser, chat
from core.config import settings

app = FastAPI(title=settings.app_name)

# Autorise le frontend Vite (localhost:5173) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include the routers
app.include_router(parser.router)
app.include_router(chat.router)


@app.get("/")
async def health_check():
    return {"status": "ok"}

