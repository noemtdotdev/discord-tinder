import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.remove_command("help")
        self.command_prefix = ">"

    def run(self):
        super().run(os.getenv("TOKEN"))

    async def on_ready(self):
        print(f"Logged in as {self.user.name} - {self.user.id}")
        print("------")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Sexy Discord Users"))
    