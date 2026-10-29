from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert

from models.BaseDataModel import BaseDataModel
from models.db_schemes.User import User


class UserModel(BaseDataModel):

    async def get_by_discord_id(self, discord_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.discord_id == discord_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, discord_id: int, display_name: str) -> User:
        # single atomic upsert: insert if new, otherwise refresh name + last_seen.
        # two simultaneous first messages can't create a duplicate this way
        stmt = (
            insert(User)
            .values(discord_id=discord_id, display_name=display_name)
            .on_conflict_do_update(
                index_elements=[User.discord_id],
                set_={"display_name": display_name, "last_seen": func.now()},
            )
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def set_roast_intensity(self, discord_id: int, value: int) -> User | None:
        # reject bad values here so the database never sees them
        if not 0 <= value <= 100:
            raise ValueError("roast intensity must be between 0 and 100")
        stmt = (
            update(User)
            .where(User.discord_id == discord_id)
            .values(roast_intensity=value)
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def set_memory_enabled(self, discord_id: int, enabled: bool) -> User | None:
        stmt = (
            update(User)
            .where(User.discord_id == discord_id)
            .values(memory_enabled=enabled)
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def add_protected_topic(self, discord_id: int, topic: str) -> User | None:
        # strip edges and collapse repeated spaces: "  my   work " -> "my work"
        topic = " ".join(topic.split())
        if not topic:
            raise ValueError("topic cannot be empty")
        user = await self.get_by_discord_id(discord_id)
        if user is None:
            return None
        # same topic in a different case counts as already there
        if any(t.casefold() == topic.casefold() for t in user.protected_topics):
            return user
        stmt = (
            update(User)
            .where(User.discord_id == discord_id)
            .values(protected_topics=[*user.protected_topics, topic])
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def remove_protected_topic(self, discord_id: int, topic: str) -> User | None:
        # same cleaning as add: "  my   work " -> "my work"
        topic = " ".join(topic.split())
        user = await self.get_by_discord_id(discord_id)
        if user is None:
            return None
        # keep every topic that doesn't match, ignoring case
        remaining = [
            t for t in user.protected_topics if t.casefold() != topic.casefold()
        ]
        # nothing matched, so there is nothing to save
        if len(remaining) == len(user.protected_topics):
            return user
        stmt = (
            update(User)
            .where(User.discord_id == discord_id)
            .values(protected_topics=remaining)
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    # admin
    async def set_protected_topics(self, discord_id: int, topics: list[str]) -> User | None:
        # clean every topic; drop empty ones and case-insensitive duplicates
        cleaned = []
        seen = set()
        for topic in topics:
            topic = " ".join(topic.split())
            if topic and topic.casefold() not in seen:
                seen.add(topic.casefold())
                cleaned.append(topic)

        # an empty list is valid: it clears every protected topic
        stmt = (
            update(User)
            .where(User.discord_id == discord_id)
            .values(protected_topics=cleaned)
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()