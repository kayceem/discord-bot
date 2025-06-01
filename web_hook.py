import asyncio
import os
import time
import json
import httpx
import logging
import discord
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from discord.ext import commands

from utils import format_embed_message, parse_race_time, save_sent_cache, validate_dataframe

load_dotenv()

log = logging.getLogger("discord-webhook")

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DATE = datetime.now().strftime("%Y-%m-%d")
CSV_PATH = Path(os.getenv("CSV_PATH", "."))

TIMEOUT = 10


def send_message(message: dict, row_id: str):
    """Send the message to Discord."""
    try:
        response = httpx.post(WEBHOOK_URL, json=message, timeout=TIMEOUT)
        if response.status_code != 204:
            log.warning(f"Failed to send message. Status: {response.status_code} — {response.text}")
        else:
            log.info("Message sent successfully.")
            save_sent_cache(row_id)
    except httpx.RequestError as e:
        log.error(f"Request failed: {e}")
        
    
def schedule_messages(df: pd.DataFrame, scheduler: BackgroundScheduler):
    for idx, row in df.iterrows():
        race_time = parse_race_time(row)
        if not race_time:
            continue

        send_time = race_time - timedelta(minutes=6)

        if send_time < datetime.now():
            continue

        message = format_embed_message(row)
        embed = {
            "title": "",
            "color": 808080,
            "description": message
        }
        row_id = f"{row['Track']}_{row['Race Time']}_{row['Selection']}"

        log.info(f"Scheduling message for {send_time.strftime('%H:%M')} — {row['First Selection Name']}")

        scheduler.add_job(
            send_message,
            'date',
            next_run_time=send_time,
            args=[embed, row_id],
            id=f"race_{idx}",
            misfire_grace_time=60
        )


def main():
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        log.error(f"Error reading CSV: {e}")
        return

    valid_df = validate_dataframe(df)
    if valid_df.empty:
        log.warning("No valid rows found.")
        return
    scheduler = BackgroundScheduler()
    scheduler.start()

    schedule_messages(valid_df, scheduler)
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == "__main__":
    if not WEBHOOK_URL:
        log.error("DISCORD_WEBHOOK_URL not set in environment variables.")
        exit(1)

    if not CSV_PATH.is_file():
        CSV_PATH = CSV_PATH / f"{DATE}.csv"

    if not CSV_PATH.exists():
        log.error("CSV file missing.")
        exit(1)


    main()
