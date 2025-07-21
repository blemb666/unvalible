import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask, request, jsonify
import threading
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
ROLE_IDS = "<@&1182947880168861727> <@&1182732063221231616>"

media_name = os.getenv("MEDIA_NAME", "DefaultMedia")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)

@bot.tree.command(name="media_name", description="Изменить MEDIA_name")
@app_commands.describe(name="Новое значение MEDIA_name")
async def media_name_cmd(interaction: discord.Interaction, name: str):
    global media_name
    media_name = name
    await interaction.response.send_message(f"✅ MEDIA_name изменено на: **{media_name}**", ephemeral=True)

@app.route("/report", methods=["POST"])
def receive_report():
    data = request.json
    asyncio.run_coroutine_threadsafe(post_to_discord(data), bot.loop)
    return jsonify({"status": "ok"})

async def post_to_discord(data):
    global media_name
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        message = (
            f"{media_name}\n"
            f"{data['form_id']} - {data['reason']}\n"
            f"{data['clip_url']}\n"
            f"{ROLE_IDS}\n"
            f"{data['messageby']}"
        )
        msg = await channel.send(message)
        await msg.add_reaction("🔄")  # Эмодзи для редактирования

        # Сохраняем msg_id и data, если нужно обрабатывать изменения

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Discord bot запущен как {bot.user}")

def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
