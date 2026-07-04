import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

EXTENSIONS = (
    "cogs.general",
    "cogs.music",
)


class MikiBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # necessário para comandos com prefixo "!"
        intents.voice_states = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="Mayonaka no Door 🎶",
            ),
        )

    async def setup_hook(self):
        for extension in EXTENSIONS:
            await self.load_extension(extension)
        # registra os slash commands (/play, /skip, etc.) no Discord
        await self.tree.sync()

    async def on_ready(self):
        logging.getLogger("miki").info(
            "Miki online como %s (ID %s)", self.user, self.user.id
        )


def main():
    if not TOKEN:
        raise SystemExit(
            "Token não encontrado! Crie um arquivo .env com DISCORD_TOKEN=seu_token "
            "(veja o .env.example)."
        )

    bot = MikiBot()
    bot.run(TOKEN, log_level=logging.INFO)


if __name__ == "__main__":
    main()
