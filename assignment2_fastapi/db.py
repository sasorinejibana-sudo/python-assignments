from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQL Server Express + Windows Integrated Auth
# If your instance name differs, change localhost\SQLEXPRESS accordingly.
CONN_STR = (
    "mssql+pyodbc://@localhost\\SQLEXPRESS/ProductDbPy"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

engine = create_engine(CONN_STR, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
