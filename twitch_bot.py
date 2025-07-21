import os
import aiohttp
from twitchio.ext import commands
from datetime import datetime, timezone

TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")  # OAuth с нужными скоупами
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
MEDIA_NAME = os.getenv("MEDIA_NAME", "DefaultMedia")
ROLE_IDS = "<@&1182947880168861727> <@&1182732063221231616>"

class ReportBot(commands.Bot):

    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, prefix="!", initial_channels=[TWITCH_CHANNEL])

    async def event_ready(self):
        print(f"✅ Twitch bot запущен как {self.nick}")

    @commands.command(name="report")
    async def report(self, ctx):
        args = ctx.message.content.split(maxsplit=2)
        if len(args) < 3:
            await ctx.send("❌ Использование: !report <ID> <причина>")
            return

        form_id = args[1]
        reason = args[2]
        user = ctx.author.name

        clip_url = await self.get_stream_url_with_offset()
        if not clip_url:
            await ctx.send("❌ Стрим не активен или не удалось получить ссылку.")
            return

        message = (
            f"{MEDIA_NAME}\n"
            f"{form_id} - {reason}\n"
            f"{clip_url}\n"
            f"{ROLE_IDS}\n"
            f"{user}"
        )

        await self.send_to_discord(message)
        await ctx.send("✅ Жалоба отправлена в Discord.")

    async def get_stream_url_with_offset(self):
        headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {TWITCH_TOKEN}"
        }

        url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_CHANNEL}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                streams = data.get("data", [])
                if not streams:
                    return None  # Нет текущей трансляции

                started_at = streams[0]["started_at"]  # ISO8601
                started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                elapsed_sec = int((now - started_dt).total_seconds()) - 60
                elapsed_sec = max(elapsed_sec, 0)

                return f"https://www.twitch.tv/{TWITCH_CHANNEL}?t={elapsed_sec}s"

    async def send_to_discord(self, message):
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json={"content": message})

if __name__ == "__main__":
    bot = ReportBot()
    bot.run()
