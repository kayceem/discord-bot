import os
import time
import httpx
import pandas as pd
from dotenv import load_dotenv
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from utils import format_embed_message, get_csv_path, get_logger, get_now, parse_race_time, validate_dataframe


load_dotenv()

log = get_logger("discord-webhook")

TIMEOUT = 10
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", 10))

def wait_until_done(scheduler, poll_interval=300):
    try:
        while True:
            if len(scheduler.get_jobs()) == 0:
                log.info("Scheduled jobs completed.")
                scheduler.shutdown()
                break
            time.sleep(poll_interval)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("Scheduler shut down manually.")


def send_message(message, row_id):
    try:
        print(message)
        response = httpx.post(WEBHOOK_URL, json=message, timeout=TIMEOUT)
        if response.status_code != 204:
            log.warning(f"Failed to send message for {row_id}. Status: {response.status_code} — {response.text}")
            return
        log.info(f"Message sent for row ID: {row_id}")
    except httpx.RequestError as e:
        log.error(f"Request failed: {e}")
        
    
def schedule_messages(df):
    scheduler = BackgroundScheduler()

    for idx, row in df.iterrows():
        race_time = parse_race_time(row)
        if not race_time:
            continue

        send_time = race_time - timedelta(minutes=ALERT_THRESHOLD)
        if send_time < get_now():
            continue

        message = format_embed_message(row)
        embed = {
            "title": "",
            "color": 808080,
            "description": message
        }
        embeds = {}
        embeds['embeds'] = [embed]
        row_id = f"{row['Track']}_{row['Race Time']}_{row['Selection']}"

        log.info(f"Scheduling message of {race_time.strftime('%H:%M')} for {send_time.strftime('%H:%M')} — {row['First Selection Name']}")

        scheduler.add_job(
            send_message,
            'date',
            next_run_time=send_time,
            args=[embeds, row_id],
            id=f"race_{idx}",
            misfire_grace_time=60
        )
    scheduler.start()
    log.info("Scheduled all alerts.")
    wait_until_done(scheduler)


def main():
    try:
        csv_path = get_csv_path()
        if not csv_path:
            log.error("CSV file missing or invalid path.")
            return
        df = pd.read_csv(csv_path)
        df = validate_dataframe(df)

        if df is None or df.empty:
            log.info("No valid data in the CSV file.")
            return
        schedule_messages(df)
    except Exception as e:
        log.error(f"Error scheduling: {e}")
        return

if __name__ == "__main__":
    if not WEBHOOK_URL:
        log.error("DISCORD_WEBHOOK_URL not set in environment variables.")
        exit(1)
    main()
