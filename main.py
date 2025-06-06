import asyncio
import os
import discord
import pandas as pd
from dotenv import load_dotenv
from datetime import timedelta
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import format_embed_message, get_csv_path, get_logger, get_now, parse_race_time, validate_dataframe


load_dotenv()

log = get_logger("discord-bot")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", 10))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()


@bot.event
async def on_ready():
    log.info(f"Bot is ready: {bot.user}")
    await schedule_races()

async def monitor_jobs(interval=1800):
    """Wait for all jobs to finish and then shut down the bot and scheduler."""
    while True:
        if not scheduler.get_jobs():
            log.info("Scheduled jobs completed.")
            await bot.close()
            break
        await asyncio.sleep(interval)

async def send_discord_message(message, row_id: str, channel_id: str):
    """Sends a message to the Discord channel."""
    channel = None
    try:
        log.info(f"Sending message for row ID: {row_id}")
        if channel_id:
            channel = bot.get_channel(int(channel_id))
            if not channel:
                log.warning(f"Channel with ID {channel_id} not found, falling back to default.")

        if not channel:
            channel = bot.get_channel(CHANNEL_ID)
            if not channel:
                log.error(f"Default channel with ID {CHANNEL_ID} not found.")
                return
            
        await channel.send(embed=message)
        log.info(f"Message sent for row ID: {row_id}")
    except Exception as e:
        log.error(f"Failed to send message for row ID {row_id}: {e}")


async def schedule_races():
    try:
        csv_path = get_csv_path()
        if not csv_path:
            log.error("CSV file missing or invalid path.")
            await bot.close()
            return
        
        df = pd.read_csv(csv_path)
        df = validate_dataframe(df)

        if df is None or df.empty:
            log.info("No valid data in the CSV file.")
            return
        
        for idx, row in df.iterrows():

            race_time = parse_race_time(row)
            if not race_time:
                continue

            send_time = race_time - timedelta(minutes=ALERT_THRESHOLD)
            if send_time < get_now():
                continue

            embed = discord.Embed(color=0x808080)
            embed.description = format_embed_message(row)
            
            log.info(f"Scheduling message of {race_time.strftime('%H:%M')} for {send_time.strftime('%H:%M')} — {row['First Selection Name']}")

            row_id = f"{row['Track']}_{row['Race Time']}_{row['Selection']}"
            scheduler.add_job(
                send_discord_message,
                'date',
                run_date=send_time,
                args=[embed, row_id, row['Channel Id']],
                id=f"race_{idx}",
                misfire_grace_time=60
            )

        scheduler.start()
        log.info("Scheduled all alerts.")
        asyncio.create_task(monitor_jobs())
        
    except Exception as e:
        log.error(f"Error scheduling: {e}")
        return
                  
if __name__ == "__main__":
    if not TOKEN or not CHANNEL_ID:
        log.error("Discord bot token or channel id is missing.")
        exit(1)
    bot.run(TOKEN)
