
# The brain of the Discord side: takes a verified interaction and decides the reply. It knows nothing about
# HTTP or FastAPI (dict in, dict out), so it is easy to unit test. Every new command is added here.

PING = 1
APPLICATION_COMMAND = 2

PONG = 1
CHANNEL_MESSAGE = 4

# Makes a reply visible only to the user who triggered it.
EPHEMERAL = 64


class InteractionController:
    def handle(self, interaction: dict) -> dict:
        """
        Top-level dispatcher on the interaction type.
        * PING -> PONG (this is what lets Discord accept the endpoint URL).
        * Slash command -> `handle_command`.
        * Anything else (buttons, dropdowns, modals) -> private "unsupported" reply, for now.
        """
        kind = interaction.get("type")

        if kind == PING:
            return {"type": PONG}

        if kind == APPLICATION_COMMAND:
            return self.handle_command(interaction)

        return self.message("Unsupported interaction.", private=True)

    def handle_command(self, interaction: dict) -> dict:
        # Routes by command name. `.get` with defaults means a malformed payload gives "unknown command", not a KeyError.
        name = interaction.get("data", {}).get("name")

        if name == "ping":
            return self.message("🏓 Pong! ADAM is alive.")

        return self.message("Unknown command.", private=True)

    def message(self, content: str, private: bool = False) -> dict:
        # Builds the reply shape Discord requires; `private` adds the EPHEMERAL flag. Centralised so all replies match.
        data = {"content": content}
        if private:
            data["flags"] = EPHEMERAL
        return {"type": CHANNEL_MESSAGE, "data": data}