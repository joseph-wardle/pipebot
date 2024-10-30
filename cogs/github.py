from __future__ import annotations

import disnake
import os
from disnake.ext import commands
from dotenv import load_dotenv
from enum import Enum
from github import Auth, Github
from hashlib import sha1
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Awaitable, Optional, Type


load_dotenv()


PipeCategory: Type[Enum] = commands.option_enum(  # type: ignore[assignment]
    {
        "Discord": "discord",
        "Farm": "renderfarm",
        "Houdini": "houdini",
        "Maya": "maya",
        "Nuke": "nuke",
        "Other": "misc",
        "ShotGrid": "shotgrid",
        "Substance": "substance",
        "Unreal": "unreal",
    }
)

Severity: Type[Enum] = commands.option_enum(  # type: ignore[assignment]
    {
        "Bug": "bug",
        "Critical Bug": "critical",
        "Feature Request": "feature",
    }
)


class BugModal(disnake.ui.Modal):
    def __init__(
        self,
        category: PipeCategory,  # type: ignore[valid-type]
        severity: Severity,  # type: ignore[valid-type]
        image1: Optional[disnake.Attachment] = None,
        image2: Optional[disnake.Attachment] = None,
    ) -> None:
        authtoken = Auth.Token(os.getenv("GITHUB_ACCESS_TOKEN", ""))
        self.g = Github(auth=authtoken)
        self.repo = self.g.get_repo(os.getenv("GITHUB_REPO", ""))

        self.category = category
        self.severity = severity

        self.image1Url: Awaitable[Optional[str]] = self.uploadImageToGithub(image1)
        self.image2Url: Awaitable[Optional[str]] = self.uploadImageToGithub(image2)

        components = [
            disnake.ui.TextInput(
                label="Summary",
                placeholder="Title or Summary of the issue",
                custom_id="title",
                style=disnake.TextInputStyle.short,
                min_length=10,
                max_length=200,
            ),
            disnake.ui.TextInput(
                label="Description",
                placeholder="Describe your issue in detail. You may use GitHub-flavored markdown where desired",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Bug Report/Feature Request",
            components=components,
            custom_id="bug_modal",
            timeout=1200,
        )

    async def uploadImageToGithub(self, image: disnake.Attachment | None) -> str | None:
        """Upload an image to Github as a commit to the `pipebot-issues-assets` branch"""
        BRANCH = "pipebot-issues-assets"
        if (
            (not image)
            or (not image.content_type)
            or ("image" not in image.content_type)
        ):
            return None

        image_bytes = await image.read()
        ext = image.filename.split(".")[-1]
        name = sha1(image_bytes).hexdigest() + "." + ext
        path = f"issues/{name}"

        try:
            self.repo.get_contents(path=path, ref=BRANCH)
        except Exception:
            self.repo.create_file(
                path=path,
                content=image_bytes,
                branch=BRANCH,
                message=f"supporting image ({image.filename})",
            )

        return f"https://github.com/{os.getenv('GITHUB_REPO')}/blob/{BRANCH}/{path}?raw=true"

    async def callback(self, inter: disnake.ModalInteraction) -> None:  # type: ignore[name-defined]
        title = inter.text_values["title"]
        description = inter.text_values["description"]

        body = (
            "***Issue submitted via [PipeBot](https://github.com/scottdmilner/pipebot)***\n"
            f"**Reporting user:** {inter.user.display_name}\n"
            "\n"
            "---\n"
            "\n"
            f"{description}\n"
        )

        if image1 := await self.image1Url:
            body += f"\n\nImage 1:\n![image 1]({image1})"

        if image2 := await self.image2Url:
            body += f"\n\nImage 2:\n![image 2]({image2})"

        self.repo.create_issue(
            title=title,
            body=body,
            labels=[self.repo.get_label(n) for n in [self.severity, self.category]],
        )
        await inter.response.send_message(body, ephemeral=True)


class GithubCmds(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def report(self, inter: disnake.ApplicationCommandInteraction):  # type: ignore[name-defined]
        pass

    @report.sub_command()
    async def bug(
        self,
        inter: disnake.ApplicationCommandInteraction,  # type: ignore[name-defined]
        category: PipeCategory,  # type: ignore[valid-type]
        severity: Severity,  # type: ignore[valid-type]
        image1: disnake.Attachment = None,  # type: ignore[assignment]
        image2: disnake.Attachment = None,  # type: ignore[assignment]
    ) -> None:
        """
        Report a bug to the pipeline team. Please be detailed!

        Parameters
        ----------
        category: What are you having an issue with?
        severity: How important is this issue
        description: A detailed description of the issue
        image1: Attach an image of the issue (optional)
        image2: Attach an image of the issue (optional)
        """
        await inter.response.send_modal(
            modal=BugModal(category, severity, image1, image2)
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(GithubCmds(bot))
