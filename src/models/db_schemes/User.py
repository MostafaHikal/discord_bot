import json
from datetime import datetime
from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from models.db_schemes.BaseScheme import BaseScheme
from helpers.constants import PROTECTED_TOPICS

class User(BaseScheme):
    __tablename__ = "users"
    __table_args__ = (
        # the database itself rejects values outside 0-100
        CheckConstraint(
            "roast_intensity BETWEEN 0 AND 100",
            name="ck_users_roast_intensity_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    display_name: Mapped[str] = mapped_column(String(100))

    roast_intensity: Mapped[int] = mapped_column(server_default=text("50"))
    memory_enabled: Mapped[bool] = mapped_column(server_default=text("true"))
    protected_topics: Mapped[list[str]] = mapped_column(
        JSONB,
        # default comes from helpers/constants.py
        server_default=text(f"'{json.dumps(PROTECTED_TOPICS)}'::jsonb"),
    )

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # the database only sets this once; UserModel updates it on every interaction
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )