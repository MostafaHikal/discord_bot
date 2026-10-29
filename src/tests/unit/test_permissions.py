from helpers.permissions import is_admin


def test_administrator_is_admin():
    assert is_admin({"member": {"permissions": "8"}}) is True


def test_administrator_among_other_permissions():
    # 1032 = 1024 (view channel) + 8 (administrator)
    assert is_admin({"member": {"permissions": "1032"}}) is True


def test_regular_member_is_not_admin():
    # 1024 = view channel only
    assert is_admin({"member": {"permissions": "1024"}}) is False


def test_dm_is_not_admin():
    # DMs carry "user" instead of "member"
    assert is_admin({"user": {"id": "123"}}) is False


def test_missing_or_bad_permissions_is_not_admin():
    assert is_admin({"member": {}}) is False
    assert is_admin({"member": {"permissions": "abc"}}) is False