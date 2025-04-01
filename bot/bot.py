import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from data.db import Database

load_dotenv()

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.remove_command("help")
        self.command_prefix = ">"
        self.db = Database("data/bot.db")

        for file in os.listdir("bot/cogs"):
            if file.endswith(".py"):
                self.load_extension(f"bot.cogs.{file[:-3]}")

    def run(self):
        super().run(os.getenv("TOKEN"))

    async def on_ready(self):
        print(f"Logged in as {self.user.name} - {self.user.id}")
        print("------")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Sexy Discord Users"))
        await self.db.connect()
        print("Database connected")
        await self.db.initialize_schema()
    