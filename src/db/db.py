from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Use default values if .env variables are missing
DB_USER = os.getenv("user", "root")
DB_PASS = os.getenv("password", "neel1705")
DB_HOST = os.getenv("host", "localhost")
DB_PORT = os.getenv("port", "3306")
DB_NAME = os.getenv("database", "b2b")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()