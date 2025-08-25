from fastapi import FastAPI
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

app = FastAPI(title="Documentation Scraper API", version="1.0", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}