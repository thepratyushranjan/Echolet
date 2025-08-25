from fastapi import FastAPI,Request, APIRouter
from rest_api import router_api
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from db.models.migrator import migrate_all

# app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(migrate_all)
        print("Database migration completed successfully.", flush=True)
        print("Starting Application...", flush=True)
        yield
    except Exception as e:
        print(f"Error during startup: {e}", flush=True)
        raise
    finally:
        print("Shutting down application...", flush=True)

app = FastAPI(title="Research Paper Chat-bot", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

research_agent = APIRouter(prefix="/research-agent")


research_agent.include_router(
    router_api.router, 
    tags=[
        "File Upload"
    ]
)

# Include the grouped router in the main app
app.include_router(research_agent)



@app.get("/")
async def root():
    return {"message": "Hello World"}