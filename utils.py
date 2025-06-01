import os
import json
import logging
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime 
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

CSV_FIELD_MAP = {
    "horse_name": "First Selection Name",
    "track": "Track",
    "race": "Race",
    "number": "Selection",
    "race_time": "Race Time",
    "units": "Units"
}

DIR = Path(__file__).parent

def get_logger(name: str, log_file: str = "log.log"):
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", log_file)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s — %(name)s — %(levelname)s — %(message)s'
    )

    file_handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger

def get_csv_path():
    CSV_PATH = Path(os.getenv("CSV_PATH", DIR))
    DATE = datetime.now().strftime("%Y-%m-%d")

    if not CSV_PATH.is_file():
        CSV_PATH = CSV_PATH / f"{DATE}.csv"

    if not CSV_PATH.exists():
        return None

    return CSV_PATH.resolve()

def get_now():
    try:
        TIMEZONE = os.getenv("TIMEZONE", "Australia/Sydney")
        tz = ZoneInfo(TIMEZONE)
    except Exception as e:
        tz = ZoneInfo("Australia/Sydney")
    return datetime.now(tz=tz)

def safe_get(row, key):
    return str(row.get(key, "")).strip()

def validate_dataframe(df):
    required = ["Track", "Race Time", "First Selection Name", "Selection", "Units"]
    try:
        df = df.dropna(subset=required)
        df = df[
            df["Units"].apply(lambda x: isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) &
            df["Selection"].apply(lambda x: str(x).isdigit())
        ]
        return df
    except Exception as e:
        return None
    

def parse_race_time(row):
    try:
        TIMEZONE = os.getenv("TIMEZONE", "Australia/Sydney")
        tz = ZoneInfo(TIMEZONE)
    except Exception as e:
        tz = ZoneInfo("Australia/Sydney")
    try:
        time_str = str(row.get("Race Time", "")).strip()
        race_time = datetime.strptime(time_str, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        ).replace(tzinfo=tz)
        return race_time
    except Exception as e:
        return None
    
def get_message_config():
    config_path = Path("config.json")
    if not config_path.exists():
        return {
            "format_template": [
                {
                "emoji": "🏇",
                "label": "",
                "field": "horse_name"
                },
                {
                "emoji": "📍",
                "label": "Track",
                "fields": ["track", "race", "number"]
                },
                {
                "emoji": "🕐",
                "label": "Race Time",
                "field": "race_time"
                },
                {
                "emoji": "💰",
                "label": "Units",
                "field": "units"
                }
            ]
            }
    
    with open(config_path, 'r') as f:
        return json.load(f)
    
def format_embed_message(row):
    message_config = get_message_config()
    lines = []
    for block in message_config["format_template"]:
        emoji = block.get("emoji", "")
        label = block.get("label", "")
        if "field" in block:
            field_name = block["field"]
            csv_key = CSV_FIELD_MAP.get(field_name, field_name)
            value = safe_get(row, csv_key)
            if field_name == "units":
                value = f"{float(value):.1f}u"
            if label:
                value = f"{label}: {value}"
            line = f"{emoji} {value}"
        elif "fields" in block:
            parts = []
            for field_name in block["fields"]:
                csv_key = CSV_FIELD_MAP.get(field_name, field_name)
                val = safe_get(row, csv_key)
                if field_name == "race":
                    val = f"R{val}"
                elif field_name == "number":
                    val = f"#{val}"
                parts.append(val)
            value = " ".join(parts)
            if label:
                value = f"{label}: {value}"
            line = f"{emoji} {value}"
        else:
            continue
        lines.append(line)
    return "\n".join(lines)
