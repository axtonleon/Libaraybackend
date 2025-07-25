import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from app.database import Base
from app import models  # Import models to ensure they are registered with Base.metadata
import subprocess
import sys

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL)

def reset_database():
    print("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")

def populate_database():
    print("Populating database with initial data...")
    try:
        # Run populate_db.py as a subprocess
        result = subprocess.run([sys.executable, "app/populate_db.py"], check=True, capture_output=True, text=True)
        print("Populate script output:")
        print(result.stdout)
        if result.stderr:
            print("Populate script errors:")
            print(result.stderr)
        print("Database population complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error populating database: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: app/populate_db.py not found. Make sure the path is correct.")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()
    populate_database()
