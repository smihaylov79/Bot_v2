import sqlite3
import yaml
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "storage", "backtests.db")
DB_PATH = os.path.abspath(DB_PATH)

OUTPUT_PATH = "live_settings.yaml"

# NEW: load symbols.yaml to get bullish/bearish/neutral lists
SYMBOLS_YAML_PATH = os.path.join(BASE_DIR, "..", "config", "symbols.yaml")
with open(SYMBOLS_YAML_PATH, "r") as f:
    SYMBOLS_CFG = yaml.safe_load(f)


def get_best_per_symbol():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    symbols = [row["symbol"] for row in c.execute("SELECT DISTINCT symbol FROM best_trials")]

    best = {}

    for symbol in symbols:
        row = c.execute("""
            SELECT *
            FROM best_trials
            WHERE symbol = ?
            ORDER BY expectancy DESC
            LIMIT 1
        """, (symbol,)).fetchone()

        if row is None:
            continue

        params = yaml.safe_load(row["parameters"])

        # Extract pattern groups from symbols.yaml
        pattern_groups = SYMBOLS_CFG[symbol]["patterns"]

        best[symbol] = {
            "timeframe": row["timeframe"],
            "pattern_weights": params["pattern_weights"],
            "bullish": pattern_groups["bullish"],
            "bearish": pattern_groups["bearish"],
            "neutral": pattern_groups["neutral"],
            "trend": params["trend"],
            "volatility": params["volatility"],
            "zones": params["zones"],
            "strategy": params["strategy"],
        }

    conn.close()
    return best


def write_yaml(settings):
    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "symbols": settings
    }

    with open(OUTPUT_PATH, "w") as f:
        yaml.dump(output, f, sort_keys=False)

    print(f"Saved live settings to {OUTPUT_PATH}")


if __name__ == "__main__":
    settings = get_best_per_symbol()
    write_yaml(settings)
