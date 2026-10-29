# Discord's permission bit for Administrator
ADMINISTRATOR = 1 << 3


def is_admin(interaction: dict) -> bool:
    member = interaction.get("member")
    # no member = the command came from a DM, where server permissions don't exist
    if not member:
        return False

    try:
        permissions = int(member.get("permissions", 0))
    except (TypeError, ValueError):
        return False

    return bool(permissions & ADMINISTRATOR)