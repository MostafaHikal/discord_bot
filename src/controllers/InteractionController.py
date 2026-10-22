PING = 1
APPLICATION_COMMAND = 2

PONG = 1
CHANNEL_MESSAGE = 4

EPHEMERAL = 64


class InteractionController:
    def handle(self, interaction: dict) -> dict:
        kind = interaction.get("type")

        if kind == PING:
            return {"type": PONG}

        if kind == APPLICATION_COMMAND:
            return self.handle_command(interaction)

        return self.message("Unsupported interaction.", private=True)

    def handle_command(self, interaction: dict) -> dict:
        name = interaction.get("data", {}).get("name")

        if name == "ping":
            return self.message("🏓 Pong! ADAM is alive.")

        return self.message("Unknown command.", private=True)

    def message(self, content: str, private: bool = False) -> dict:
        data = {"content": content}
        if private:
            data["flags"] = EPHEMERAL
        return {"type": CHANNEL_MESSAGE, "data": data}