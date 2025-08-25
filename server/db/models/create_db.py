# Create Db

from config.config import Config 
from sqlalchemy import create_engine, inspect, text
from models import Base, DocumentChunk

engine = create_engine(Config.POSTGRES_CONNECTION)

def create_extension():
    """
    Create the vector extension if it does not exist.
    """
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

def create_tables():
    """
    Check if the document_chunks table exists.
    If it does, print an error message; if not, create the table.
    """
    create_extension()
    
    inspector = inspect(engine)
    if inspector.has_table(DocumentChunk.__tablename__):
        print(f"Error: Table '{DocumentChunk.__tablename__}' already exists!")
    else:
        Base.metadata.create_all(engine)
        print(f"Table '{DocumentChunk.__tablename__}' created successfully!")

if __name__ == "__main__":
    create_tables()
