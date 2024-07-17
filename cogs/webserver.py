from __future__ import annotations

import disnake
import hmac
import json
import os
from aiohttp import web
from datetime import datetime
from disnake.ext import commands, tasks
from hashlib import sha1
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()


class Webserver(commands.Cog):
    # see https://stackoverflow.com/a/62481294
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.webserver_port = int(os.getenv("LISTEN_PORT", ""))
        self.app = web.Application()
        routes = web.RouteTableDef()

        self.web_server.start()

        @routes.get("/")
        async def welcome(request: web.Request) -> web.Response:
            return web.Response(body="", status=400)

        @routes.post("/shotgrid")
        async def shotgrid(request: web.Request) -> web.Response:
            raw = await request.read()
            hashcheck = (
                "sha1="
                + hmac.new(
                    os.getenv("SHOTGRID_SECRET", "").encode(), raw, sha1
                ).hexdigest()
            )
            if hashcheck != request.headers["x-sg-signature"]:
                print("Error: hashes do not match")
                return web.Response(body="", status=401)

            data = await request.json()
            pprint(data)
            await self.testing_channel.send("```json\n" + json.dumps(data) + "\n```")
            return web.Response(status=200)

        @routes.post("/model_checker")
        async def model_checker(request: web.Request) -> web.Response:
            raw = await request.read()
            hashcheck = (
                "sha1="
                + hmac.new(
                    os.getenv("PIPEBOT_SECRET", "").encode(), raw, sha1
                ).hexdigest()
            )
            if hashcheck != request.headers["x-pipebot-signature"]:
                print("Error: hashes do not match")
                return web.Response(body="", status=401)

            data = await request.json()
            pprint(data)
            embed = disnake.Embed(
                title="Model Publish Override",
                description=f"Notice! The model **{data['asset']}** was "
                f"exported without passing the model checker by user "
                f"**{data['user']}**. File saved to path: `{data['path']}`.",
                color=disnake.Color.yellow(),
                timestamp=datetime.now(),
            )
            embed.set_thumbnail(url="")
            await self.leads_channel.send(embed=embed)
            return web.Response(status=200)

        self.app.add_routes(routes)

    @tasks.loop()
    async def web_server(self) -> None:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=self.webserver_port)
        await site.start()
        print(f"Webserver running on port {self.webserver_port}")

    @web_server.before_loop
    async def web_server_before_loop(self) -> None:
        await self.bot.wait_until_ready()

        # for some reason `get_channel` doesn't work but `fetch_channel` does
        testing_channel = await self.bot.fetch_channel(
            int(os.getenv("TESTING_CHANNEL_ID", ""))
        )
        if not isinstance(testing_channel, disnake.TextChannel):
            raise TypeError("Testing channel is invalid")

        self.testing_channel = testing_channel

        leads_channel = await self.bot.fetch_channel(
            int(os.getenv("LEADS_CHANNEL_ID", ""))
        )
        if not isinstance(leads_channel, disnake.TextChannel):
            raise TypeError("Leads channel is invaleid")

        self.leads_channel = leads_channel


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Webserver(bot))
