from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_light_migrations():
    """Add any newly-introduced columns to an existing sqlite file (no-op on a fresh DB)."""
    inspector = inspect(engine)
    if "movies" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("movies")}
    new_columns = {
        "recap_status": "VARCHAR NOT NULL DEFAULT 'none'",
        "recap_error": "TEXT",
        "recap_vertical_filename": "VARCHAR",
        "recap_horizontal_filename": "VARCHAR",
    }
    with engine.begin() as conn:
        for name, ddl_type in new_columns.items():
            if name not in existing_columns:
                conn.execute(text(f"ALTER TABLE movies ADD COLUMN {name} {ddl_type}"))
