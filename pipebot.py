from __future__ import annotations

import disnake
import os
from disnake.ext import commands
from dotenv import load_dotenv

from cogs import AvatarRandomizer, GithubCmds, Webserver

load_dotenv()

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.InteractionBot(intents=intents)
bot.add_cog(AvatarRandomizer(bot))  # type: ignore[arg-type]
bot.add_cog(GithubCmds(bot))  # type: ignore[arg-type]
bot.add_cog(Webserver(bot))  # type: ignore[arg-type]


@bot.event
async def on_ready() -> None:
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message: disnake.Message) -> None:
    if message.author == bot.user:
        return

    if "blender" in message.content.lower():
        await message.add_reaction("blender:1166462167571238922")
        await message.add_reaction("👀")


bot.run(os.getenv("CLIENT_TOKEN"))
