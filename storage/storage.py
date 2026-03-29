# storage/storage.py

import sqlite3
import pandas as pd
from pathlib import Path


class MarketDataStorage:
    # def __init__(self, db_path="storage/market_data.db"):
    #
    #     self.db_path = Path(db_path)
    #     self.db_path.parent.mkdir(parents=True, exist_ok=True)
    #     self._create_tables()
    def __init__(self, db_path="storage/market_data.db"):
        # Resolve absolute path relative to project root
        project_root = Path(__file__).resolve().parents[1]
        self.db_path = project_root / db_path

        # Ensure folder exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create tables if needed
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        conn.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT,
            timeframe TEXT,
            timestamp INTEGER,
            timestamp_dt TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (symbol, timeframe, timestamp)
        )
        """)
        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    # Incremental loading helper
    # ---------------------------------------------------------
    def get_last_timestamp(self, symbol, timeframe):
        conn = self._connect()
        row = conn.execute("""
            SELECT MAX(timestamp) FROM candles
            WHERE symbol = ? AND timeframe = ?
        """, (symbol, timeframe)).fetchone()
        conn.close()

        return int(row[0]) if row and row[0] is not None else None

    # ---------------------------------------------------------
    # Insert candles (with dedupe + timestamp normalization)
    # ---------------------------------------------------------
    def insert_candles(self, symbol, timeframe, df):
        conn = self._connect()
        df_to_save = df.copy()

        # Just ensure integer seconds
        df_to_save["timestamp"] = df_to_save["timestamp"].astype("int64")

        # Ensure timestamp_dt is string (for readability)
        df_to_save["timestamp_dt"] = pd.to_datetime(
            df_to_save["timestamp"], unit="s", utc=True
        ).astype(str)

        df_to_save["symbol"] = symbol
        df_to_save["timeframe"] = timeframe

        allowed_cols = [
            "symbol", "timeframe",
            "timestamp", "timestamp_dt",
            "open", "high", "low", "close", "volume"
        ]
        df_to_save = df_to_save[allowed_cols]

        df_to_save = df_to_save.drop_duplicates(
            subset=["symbol", "timeframe", "timestamp"]
        )

        df_to_save.to_sql("candles", conn, if_exists="append", index=False)
        conn.close()

    # ---------------------------------------------------------
    # Load candles for analysis/backtesting
    # ---------------------------------------------------------
    def load_candles(self, symbol, timeframe):
        conn = self._connect()
        df = pd.read_sql("""
            SELECT timestamp, timestamp_dt, open, high, low, close, volume
            FROM candles
            WHERE symbol = ? AND timeframe = ?
            ORDER BY timestamp ASC
        """, conn, params=(symbol, timeframe))
        conn.close()

        if df.empty:
            return df

        df = df.set_index("timestamp")
        return df

    def drop_candles_table(self):
        conn = self._connect()
        conn.execute("DROP TABLE IF EXISTS candles")
        conn.commit()
        conn.close()





class TradingDataStorage:
    """
    Handles trades, logs, equity curve, and backtest results.
    Stored in trading_data.db
    """

    def __init__(self, db_path="storage/trading_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        c = conn.cursor()

        # Trades table
        c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            direction TEXT,
            entry_price REAL,
            exit_price REAL,
            sl REAL,
            tp REAL,
            entry_time INTEGER,
            exit_time INTEGER,
            profit REAL,
            metadata TEXT
        )
        """)

        # Equity curve
        c.execute("""
        CREATE TABLE IF NOT EXISTS equity_curve (
            timestamp INTEGER PRIMARY KEY,
            equity REAL
        )
        """)

        # Logs
        c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            level TEXT,
            message TEXT
        )
        """)

        conn.commit()
        conn.close()

    # -----------------------------
    # Trades
    # -----------------------------
    def insert_trade(self, trade_dict):
        conn = self._connect()
        df = pd.DataFrame([trade_dict])
        df.to_sql("trades", conn, if_exists="append", index=False)
        conn.close()

    def load_trades(self):
        conn = self._connect()
        df = pd.read_sql("SELECT * FROM trades ORDER BY id ASC", conn)
        conn.close()
        return df

    # -----------------------------
    # Equity curve
    # -----------------------------
    def insert_equity_point(self, timestamp, equity):
        conn = self._connect()
        conn.execute(
            "INSERT OR REPLACE INTO equity_curve (timestamp, equity) VALUES (?, ?)",
            (timestamp, equity)
        )
        conn.commit()
        conn.close()

    def load_equity_curve(self):
        conn = self._connect()
        df = pd.read_sql("SELECT * FROM equity_curve ORDER BY timestamp ASC", conn)
        conn.close()
        return df

    # -----------------------------
    # Logs
    # -----------------------------
    def log(self, timestamp, level, message):
        conn = self._connect()
        conn.execute(
            "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
            (timestamp, level, message)
        )
        conn.commit()
        conn.close()

    def load_logs(self):
        conn = self._connect()
        df = pd.read_sql("SELECT * FROM logs ORDER BY id ASC", conn)
        conn.close()
        return df
