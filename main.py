import os
import json
import logging
import discord
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import format_embed_message, get_logger, parse_race_time, save_sent_cache, validate_dataframe


load_dotenv()

log = get_logger("discord-bot")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DATE = datetime.now().strftime("%Y-%m-%d")
CSV_PATH = Path(os.getenv("CSV_PATH", "."))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", 10))
TIMEOUT = 10

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    log.info(f"Bot is ready: {bot.user}")
    await schedule_races()



async def send_discord_message(message, row_id: str):
    log.info(f"Sending message for row ID: {row_id}")
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        log.error("Channel not found")
        return
    await channel.send(embed=message)
    save_sent_cache(row_id)

async def schedule_races():
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        log.error(f"Failed to load data: {e}")
        return

    df = validate_dataframe(df)
    for idx, row in df.iterrows():
        race_time = parse_race_time(row)
        if not race_time:
            continue
        send_time = race_time - timedelta(minutes=4)
        if send_time < datetime.now():
            continue

        embed = discord.Embed(color=0x808080)
        embed.description = format_embed_message(row)
        
        row_id = f"{row['Track']}_{row['Race Time']}_{row['Selection']}"
        scheduler.add_job(
            send_discord_message,
            'date',
            run_date=send_time,
            args=[embed, row_id],
            id=f"race_{idx}",
            misfire_grace_time=60
        )

    scheduler.start()
    log.info("All messages scheduled.")

if __name__ == "__main__":
    if not TOKEN or not CHANNEL_ID:
        log.error("Discord bot token or channel id is missing.")
        exit(1)

    if not CSV_PATH.is_file():
        CSV_PATH = CSV_PATH / f"{DATE}.csv"
        
    if not CSV_PATH.exists():
        log.error("CSV file missing.")
        exit(1)

    bot.run(TOKEN)
