import json
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from datetime import datetime 
import logging

CSV_FIELD_MAP = {
    "horse_name": "First Selection Name",
    "track": "Track",
    "race": "Race",
    "number": "Selection",
    "race_time": "Race Time",
    "units": "Units"
}
DIR = Path(__file__).parent
SENT_CACHE_PATH = DIR / 'logs' / Path("sent_races.json")

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

def load_sent_cache():
    if SENT_CACHE_PATH.exists():
        with open(SENT_CACHE_PATH, 'r') as f:
            return set(json.load(f))
    return set()

def save_sent_cache(sent_id):
    sent_ids = []
    if SENT_CACHE_PATH.exists():
        with open(SENT_CACHE_PATH, 'r') as f:
            sent_ids = json.load(f)
    sent_ids.append(sent_id)
    with open(SENT_CACHE_PATH, 'w') as f:
        json.dump(list(set(sent_ids)), f)

def safe_get(row, key):
    return str(row.get(key, "")).strip()

def validate_dataframe(df):
    """ Validates the DataFrame to ensure it contains the required columns and valid data types."""
    required = ["Track", "Race Time", "First Selection Name", "Selection", "Units"]
    df = df.dropna(subset=required)
    df = df[
        df["Units"].apply(lambda x: isinstance(x, (int, float)) or str(x).replace('.', '', 1).isdigit()) &
        df["Selection"].apply(lambda x: str(x).isdigit())
    ]
    return df

def parse_race_time(row):
    try:
        time_str = str(row.get("Race Time", "")).strip()
        race_time = datetime.strptime(time_str, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        return race_time
    except Exception as e:
        return None
def get_message_config():
    """Loads the message configuration from a JSON file."""
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
    """Formats the message for Discord embed based on the row data."""
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
