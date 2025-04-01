import discord
from discord.ext import commands
from discord import SlashCommandGroup, option, ButtonStyle
from discord.ui import View, Button
from bot.bot import Bot
import io
import constants
import random

from data.db import User

from tinder.ui import create_tinder_image

class Profile(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    dating = SlashCommandGroup("dating", "Commands related to dating.", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})

    async def create_profile_message(self, user_id: int) -> tuple:
        """
        Creates a profile embed and file from a user ID.
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            tuple: (embed, file) for the user's profile
        """
        # Get the Discord user object
        user = await self.bot.fetch_user(user_id)
        if not user:
            return None, None
        
        # Get user avatar
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        
        # Calculate age based on account creation
        age = (discord.utils.utcnow() - user.created_at).days // 365
        
        # Get bio from database
        db_user = await self.bot.db.fetchone("SELECT * FROM users WHERE id = ?", user_id)
        if db_user:
            db_user = User(*db_user)
        else:
            db_user = User(user_id, "No bio set.", 0)
        
        # Create the image
        image = await create_tinder_image(avatar_url, user.name, age, db_user.bio)
        
        # Convert to binary
        image_binary = io.BytesIO()
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        
        # Create file and embed
        file = discord.File(image_binary, filename="profile.png")
        
        # Create embed with proper color based on VIP status
        embed = discord.Embed(color=discord.Color.embed_background() if db_user.vip == 0 else discord.Color.gold())
        embed.set_image(url="attachment://profile.png")
        embed.set_footer(text=str(user_id))
        
        return embed, file

    @dating.command(
        name="profile",
        description="Shows your Dinder profile card for your profile.",
    )
    async def profile(self, ctx: discord.ApplicationContext):
        embed, file = await self.create_profile_message(ctx.author.id)
        await ctx.respond(embed=embed, file=file, ephemeral=True)

    @dating.command(
        name="bio",
        description="Set your Dinder bio.",
    )
    @option(
        name="bio",
        description="Your Dinder bio.",
        required=True,
    )
    async def set_bio(self, ctx: discord.ApplicationContext, bio: str):
        if ctx.author.id in constants.VIP_LIST:
            vip = 1
        else:
            vip = 0
        await self.bot.db.execute("INSERT OR REPLACE INTO users (id, bio, vip) VALUES (?, ?, ?)", ctx.author.id, bio, vip)
        await ctx.respond(f"Your bio has been set to: `{bio}`", ephemeral=True)
    
    @dating.command(
        name="start",
        description="Start swiping on Dinder profiles.",
    )
    async def start_swiping(self, ctx: discord.ApplicationContext):
        """Start swiping on random profiles you haven't disliked yet."""
        
        disliked = await self.bot.db.fetchall(
            "SELECT target_id FROM interactions WHERE user_id = ? AND interaction = 'dislike'",
            ctx.author.id
        )
        disliked_ids = set(user[0] for user in disliked)
        
        disliked_ids.add(ctx.author.id)
        
        potential_matches = set()
        
        for guild in ctx.author.mutual_guilds:
            try:
                members = guild.members
                for member in members:
                    if not member.bot and member.id not in disliked_ids:
                        potential_matches.add(member.id)
            except Exception as e:
                print(f"Error getting members from guild {guild.id}: {e}")
        
        if not potential_matches:
            await ctx.respond("No potential matches found! You've gone through all available profiles.", ephemeral=True)
            return
        
        target_id = random.choice(list(potential_matches))
        
        class SwipeView(View):
            def __init__(self, cog):
                super().__init__(timeout=60)
                self.cog = cog
            
            @discord.ui.button(label="💙 Like", style=ButtonStyle.primary) 
            async def like(self, button: Button, interaction: discord.Interaction):
                await self.cog.bot.db.execute(
                    "INSERT OR REPLACE INTO interactions (user_id, target_id, interaction) VALUES (?, ?, ?)",
                    interaction.user.id, target_id, "like"
                )
                match = await self.cog.bot.db.fetchone(
                    "SELECT * FROM interactions WHERE user_id = ? AND target_id = ? AND interaction = 'like'",
                    target_id, interaction.user.id
                )
                
                if match:
                    target_user = await self.cog.bot.fetch_user(target_id)
                    match_embed = discord.Embed(
                        title="❤️ It's a Match!",
                        description=f"You and {target_user.mention} liked each other!",
                        color=discord.Color.brand_red()
                    )
                    await interaction.response.send_message(embed=match_embed, ephemeral=True)
                    
                    try:
                        user_embed = discord.Embed(
                            title="❤️ It's a Match!",
                            description=f"You and {interaction.user.mention} liked each other!",
                            color=discord.Color.brand_red()
                        )
                        await target_user.send(embed=user_embed)
                    except:
                        pass
                else:
                    await interaction.response.defer()
                    await self.cog.start_swiping(await self.cog.bot.get_application_context(interaction))

            @discord.ui.button(label="❌ Nope", style=ButtonStyle.danger)
            async def dislike(self, button: Button, interaction: discord.Interaction):
                await self.cog.bot.db.execute(
                    "INSERT OR REPLACE INTO interactions (user_id, target_id, interaction) VALUES (?, ?, ?)",
                    interaction.user.id, target_id, "dislike"
                )
                await interaction.response.defer()
                await self.cog.start_swiping(await self.cog.bot.get_application_context(interaction))
        
        embed, file = await self.create_profile_message(target_id)
        view = SwipeView(self)
        await ctx.respond(embed=embed, file=file, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(Profile(bot))