import discord
from discord.ext import commands

from tinder.ui import create_tinder_image

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="profile",
        description="Shows a Tinder-style profile card for your profile."
    )
    async def profile(self, ctx: discord.ApplicationContext):

        avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url

        age = (discord.utils.utcnow() - ctx.author.created_at).days // 365
        
        bio = "This is a sample bio. You can customize it as "

        image = await create_tinder_image(avatar_url, ctx.author.name, age, bio)

        await ctx.send(file=discord.File(image, filename="profile.png"), ephemeral=True)


def setup(bot):
    bot.add_cog(Profile(bot))