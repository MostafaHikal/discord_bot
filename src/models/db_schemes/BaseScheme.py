from sqlalchemy.orm import DeclarativeBase

# parent of every table class; Alembic reads its metadata to build migrations
class BaseScheme(DeclarativeBase):
    pass