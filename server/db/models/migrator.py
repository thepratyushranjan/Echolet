import os
import glob
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from config.config import Config as AppConfig

def get_latest_migration_file():
    """Get the latest migration file from the versions directory."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    versions_dir = os.path.join(project_root, "alembic", "versions")
    
    # Get all Python files in versions directory
    migration_files = glob.glob(os.path.join(versions_dir, "*.py"))
    
    if not migration_files:
        return None
    
    # Sort by creation time and get the latest
    latest_file = max(migration_files, key=os.path.getctime)
    
    # Extract revision ID from filename (assumes format: revision_description.py)
    filename = os.path.basename(latest_file)
    revision_id = filename.split('_')[0]
    
    return revision_id

def get_all_heads(alembic_cfg):
    """Get all head revisions in the migration tree."""
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        heads = script.get_heads()
        return heads
    except Exception as e:
        print(f"Error getting heads: {e}")
        return []

def merge_heads_if_needed(alembic_cfg):
    """Check for multiple heads and merge them if needed."""
    heads = get_all_heads(alembic_cfg)
    
    if len(heads) > 1:
        print(f"Multiple heads detected: {heads}")
        print("Attempting to merge heads...")
        
        try:
            # Create a merge revision
            merge_message = f"Merge heads: {', '.join(heads)}"
            command.merge(alembic_cfg, heads, message=merge_message)
            print("Heads merged successfully.")
            return True
        except Exception as e:
            print(f"Error merging heads: {e}")
            return False
    
    return False

def check_if_fresh_database():
    """
    Check if this is a fresh database by counting user tables.
    A fresh database should have very few or no user tables.
    """
    try:
        engine = create_engine(AppConfig.POSTGRES_CONNECTION)
        with engine.connect() as conn:
            # Count all user tables (excluding system tables)
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'pg_%'
                AND table_name NOT LIKE 'sql_%'
            """))
            
            table_count = result.scalar()
            is_fresh = table_count <= 1
            
            print(f"Found {table_count} user tables in database. Fresh: {is_fresh}")
            return is_fresh
            
    except Exception as e:
        print(f"Error checking database state: {e}")
        return True # Assume fresh if we can't check

def reset_alembic_version_to_latest():
    """Reset alembic_version table to point to the latest migration file."""
    try:
        engine = create_engine(AppConfig.POSTGRES_CONNECTION)
        latest_revision = get_latest_migration_file()
        
        if not latest_revision:
            print("No migration files found.")
            return
        
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                # Update existing version
                conn.execute(text("""
                    UPDATE alembic_version SET version_num = :version
                """), {"version": latest_revision})
                print(f"Updated alembic_version to: {latest_revision}")
            else:
                # Create table and insert version
                conn.execute(text("""
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """))
                conn.execute(text("""
                    INSERT INTO alembic_version (version_num) VALUES (:version)
                """), {"version": latest_revision})
                print(f"Created alembic_version table with version: {latest_revision}")
            
            conn.commit()
            
    except Exception as e:
        print(f"Error resetting alembic version: {e}")

def migrate_all():
    """
    Runs Alembic migrations to upgrade the database schema to the latest version.
    Automatically handles both fresh databases, existing databases, and multiple heads.
    """
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    
    # Check if this is a fresh database
    is_fresh = check_if_fresh_database()
    
    if is_fresh:
        print("Fresh database detected. Running all migrations from scratch...")
        
        try:
            # Check for multiple heads and merge if needed
            merge_heads_if_needed(alembic_cfg)
            
            # For fresh database, run all migrations from the beginning
            command.upgrade(alembic_cfg, "head")
            
        except Exception as e:
            print(f"Migration error: {e}")
            # If migration fails, ensure we have the right version set
            reset_alembic_version_to_latest()
    
    else:
        print("Existing database detected. Handling multiple heads and updating...")
        
        try:
            # Check for multiple heads and merge if needed
            heads_merged = merge_heads_if_needed(alembic_cfg)
            
            if heads_merged:
                # If heads were merged, upgrade to the new merged head
                command.upgrade(alembic_cfg, "head")
            else:
                # Normal case: update version pointer and run migrations
                reset_alembic_version_to_latest()
                command.upgrade(alembic_cfg, "head")

            
        except Exception as e:
            print(f"Migration error: {e}")
            # Fallback: try to stamp the latest version
            try:
                latest_revision = get_latest_migration_file()
                if latest_revision:
                    command.stamp(alembic_cfg, latest_revision)
                    print(f"Stamped database to version: {latest_revision}")
            except Exception as stamp_error:
                print(f"Stamp error: {stamp_error}")

def fix_multiple_heads():
    """
    Utility function to manually fix multiple heads issue.
    Call this if you want to resolve multiple heads without running full migration.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    
    heads = get_all_heads(alembic_cfg)
    
    if len(heads) > 1:
        print(f"Multiple heads found: {heads}")
        merge_heads_if_needed(alembic_cfg)
        print("Multiple heads resolved.")
    else:
        print("No multiple heads detected.")