import pytest
from helpers.constants import PROTECTED_TOPICS
from models.UserModel import UserModel
from sqlalchemy import func, select, update
from models.db_schemes.User import User

pytestmark = pytest.mark.asyncio


async def test_new_member_gets_defaults(session):
    user = await UserModel(session).get_or_create(123, "Ahmed")

    assert user.discord_id == 123
    assert user.display_name == "Ahmed"
    assert user.roast_intensity == 50
    assert user.memory_enabled is True
    assert user.protected_topics == PROTECTED_TOPICS


async def test_same_member_is_not_duplicated(session):
    model = UserModel(session)
    first = await model.get_or_create(123, "Ahmed")
    # save the values now, in case the second call hands back the same object
    first_id, first_last_seen = first.id, first.last_seen

    second = await model.get_or_create(123, "Ahmed Ali")

    count = await session.scalar(select(func.count()).select_from(User))
    assert count == 1
    assert second.id == first_id
    assert second.display_name == "Ahmed Ali"
    assert second.last_seen > first_last_seen

async def test_update_keeps_first_seen_and_settings(session):
    model = UserModel(session)
    first = await model.get_or_create(123, "Ahmed")
    first_seen = first.first_seen

    # simulate the member changing a setting
    await session.execute(
        update(User).where(User.discord_id == 123).values(roast_intensity=80)
    )
    await session.commit()

    second = await model.get_or_create(123, "Ahmed")

    assert second.first_seen == first_seen
    assert second.roast_intensity == 80

# =====================
async def test_set_roast_intensity_changes_value(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.set_roast_intensity(123, 80)
    assert user.roast_intensity == 80

    # 0 and 100 are the edges of the allowed range
    assert (await model.set_roast_intensity(123, 0)).roast_intensity == 0
    assert (await model.set_roast_intensity(123, 100)).roast_intensity == 100


async def test_set_roast_intensity_rejects_bad_value(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    with pytest.raises(ValueError):
        await model.set_roast_intensity(123, 150)
    with pytest.raises(ValueError):
        await model.set_roast_intensity(123, -1)

    # the stored value must still be the default
    user = await model.get_by_discord_id(123)
    assert user.roast_intensity == 50


async def test_set_roast_intensity_unknown_member(session):
    result = await UserModel(session).set_roast_intensity(999, 80)
    assert result is None

# /////////

async def test_set_memory_enabled_changes_value(session):
    model = UserModel(session)
    user = await model.get_or_create(123, "Ahmed")
    assert user.memory_enabled is True

    user = await model.set_memory_enabled(123, False)
    assert user.memory_enabled is False

    # setting the same value twice must give the same result
    user = await model.set_memory_enabled(123, False)
    assert user.memory_enabled is False

    user = await model.set_memory_enabled(123, True)
    assert user.memory_enabled is True


async def test_set_memory_enabled_unknown_member(session):
    result = await UserModel(session).set_memory_enabled(999, False)
    assert result is None

# ==================================
async def test_add_protected_topic_adds_new_topic(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.add_protected_topic(123, "Politics")
    assert user.protected_topics == [*PROTECTED_TOPICS, "Politics"]

    # a second topic is added after the first, not instead of it
    user = await model.add_protected_topic(123, "Work")
    assert user.protected_topics == [*PROTECTED_TOPICS, "Politics", "Work"]


async def test_add_protected_topic_ignores_duplicate_in_other_case(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.add_protected_topic(123, "  health ")
    assert user.protected_topics == PROTECTED_TOPICS


async def test_add_protected_topic_cleans_spaces(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.add_protected_topic(123, "  my   work ")
    assert user.protected_topics[-1] == "my work"


async def test_add_protected_topic_rejects_empty(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    with pytest.raises(ValueError):
        await model.add_protected_topic(123, "   ")

    # the list must be untouched
    user = await model.get_by_discord_id(123)
    assert user.protected_topics == PROTECTED_TOPICS


async def test_add_protected_topic_unknown_member(session):
    result = await UserModel(session).add_protected_topic(999, "Politics")
    assert result is None

# ===================================
async def test_remove_protected_topic_removes_in_other_case(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.remove_protected_topic(123, "  HEALTH ")
    assert user.protected_topics == [t for t in PROTECTED_TOPICS if t != "Health"]

    # the change must be saved, not just returned
    saved = await model.get_by_discord_id(123)
    assert "Health" not in saved.protected_topics


async def test_remove_protected_topic_not_in_list(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.remove_protected_topic(123, "Politics")
    assert user.protected_topics == PROTECTED_TOPICS


async def test_remove_protected_topic_empty_text_changes_nothing(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.remove_protected_topic(123, "   ")
    assert user.protected_topics == PROTECTED_TOPICS


async def test_remove_protected_topic_unknown_member(session):
    result = await UserModel(session).remove_protected_topic(999, "Health")
    assert result is None

# ================================
async def test_set_protected_topics_replaces_whole_list(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    # one empty item, one duplicate in another case, one with extra spaces
    user = await model.set_protected_topics(123, ["  Gaming ", "gaming", "", "My   Work"])
    assert user.protected_topics == ["Gaming", "My Work"]

    # the old defaults are gone and the change is saved
    saved = await model.get_by_discord_id(123)
    assert saved.protected_topics == ["Gaming", "My Work"]


async def test_set_protected_topics_empty_list_clears(session):
    model = UserModel(session)
    await model.get_or_create(123, "Ahmed")

    user = await model.set_protected_topics(123, [])
    assert user.protected_topics == []


async def test_set_protected_topics_unknown_member(session):
    result = await UserModel(session).set_protected_topics(999, ["Gaming"])
    assert result is None