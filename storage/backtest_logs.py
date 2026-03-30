import sqlite3
import json
from datetime import datetime
from pathlib import Path


class BacktestStorage:
    """
    Stores backtest results, optimization parameters, metrics,
    and research metadata in a dedicated backtests.db file.
    """

    def __init__(self, db_path="storage/backtests.db"):
        project_root = Path(__file__).resolve().parents[1]
        self.db_path = project_root / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    # ---------------------------------------------------------
    # Connection helper
    # ---------------------------------------------------------
    # def _connect(self):
    #     return sqlite3.connect(self.db_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------------------------------------------------
    # Create tables (extended schema)
    # ---------------------------------------------------------
    def _create_tables(self):
        conn = self._connect()
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS backtests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Core identifiers
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,

            -- Strategy parameters (JSON)
            parameters TEXT NOT NULL,

            -- Optimization metadata
            optimization_id TEXT,
            trial_number INTEGER,
            is_best INTEGER DEFAULT 0,
            notes TEXT,

            -- Backtest metadata
            start_timestamp INTEGER,
            end_timestamp INTEGER,
            num_candles INTEGER,
            version TEXT,
            data_hash TEXT,

            -- Performance metrics
            trades INTEGER NOT NULL,
            winrate REAL NOT NULL,
            expectancy REAL NOT NULL,
            profit_factor REAL NOT NULL,
            max_drawdown REAL NOT NULL,
            rr REAL NOT NULL,
            avg_win REAL NOT NULL,
            avg_loss REAL NOT NULL,

            -- Extended metrics
            long_winrate REAL,
            short_winrate REAL,
            long_expectancy REAL,
            short_expectancy REAL,
            max_consecutive_losses INTEGER,
            max_consecutive_wins INTEGER,
            avg_holding_time REAL,
            median_holding_time REAL,

            -- Pattern-level stats (JSON)
            pattern_stats TEXT,

            -- Optimization context
            optimizer TEXT,
            search_space TEXT,
            random_seed INTEGER,

            -- Deployment flags
            approved_for_live INTEGER DEFAULT 0,
            live_parameters TEXT,
            live_deployment_timestamp TEXT
        )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS best_trials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                parameters TEXT NOT NULL,

                optimization_id TEXT,
                trial_number INTEGER,
                is_best INTEGER DEFAULT 1,
                notes TEXT,

                start_timestamp TEXT,
                end_timestamp TEXT,
                num_candles INTEGER,
                version TEXT,
                data_hash TEXT,

                trades INTEGER NOT NULL,
                winrate REAL NOT NULL,
                expectancy REAL NOT NULL,
                profit_factor REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                rr REAL NOT NULL,
                avg_win REAL NOT NULL,
                avg_loss REAL NOT NULL,

                long_winrate REAL,
                short_winrate REAL,
                long_expectancy REAL,
                short_expectancy REAL,
                max_consecutive_losses INTEGER,
                max_consecutive_wins INTEGER,
                avg_holding_time REAL,
                median_holding_time REAL,

                pattern_stats TEXT,

                optimizer TEXT,
                search_space TEXT,
                random_seed INTEGER,

                approved_for_live INTEGER DEFAULT 0,
                live_parameters TEXT,
                live_deployment_timestamp TEXT,

                -- New fields for best-trial tracking
                selected_at TEXT,
                source_trial_id INTEGER
            )
            """)

        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    # Save a backtest result
    # ---------------------------------------------------------
    def save_result(
        self,
        symbol,
        timeframe,
        symbol_cfg,
        metrics,
        optimization_id=None,
        trial_number=None,
        is_best=False,
        notes=None,
        start_timestamp=None,
        end_timestamp=None,
        num_candles=None,
        version=None,
        data_hash=None,
        pattern_stats=None,
        optimizer=None,
        search_space=None,
        random_seed=None,
        approved_for_live=False,
        live_parameters=None,
        live_deployment_timestamp=None
    ):
        conn = self._connect()
        c = conn.cursor()

        params_json = json.dumps(symbol_cfg, sort_keys=True)
        pattern_stats_json = json.dumps(pattern_stats, sort_keys=True) if pattern_stats else None
        search_space_json = json.dumps(search_space, sort_keys=True) if search_space else None
        live_params_json = json.dumps(live_parameters, sort_keys=True) if live_parameters else None

        c.execute("""
        INSERT INTO backtests (
            timestamp, symbol, timeframe, parameters,
            optimization_id, trial_number, is_best, notes,
            start_timestamp, end_timestamp, num_candles, version, data_hash,
            trades, winrate, expectancy, profit_factor,
            max_drawdown, rr, avg_win, avg_loss,
            long_winrate, short_winrate, long_expectancy, short_expectancy,
            max_consecutive_losses, max_consecutive_wins,
            avg_holding_time, median_holding_time,
            pattern_stats,
            optimizer, search_space, random_seed,
            approved_for_live, live_parameters, live_deployment_timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            symbol,
            timeframe,
            params_json,

            optimization_id,
            trial_number,
            1 if is_best else 0,
            notes,

            start_timestamp,
            end_timestamp,
            num_candles,
            version,
            data_hash,

            int(metrics["trades"]),
            float(metrics["winrate"]),
            float(metrics["expectancy"]),
            float(metrics["profit_factor"]),
            float(metrics["max_drawdown"]),
            float(metrics["rr"]),
            float(metrics["avg_win"]),
            float(metrics["avg_loss"]),

            metrics.get("long_winrate"),
            metrics.get("short_winrate"),
            metrics.get("long_expectancy"),
            metrics.get("short_expectancy"),
            metrics.get("max_consecutive_losses"),
            metrics.get("max_consecutive_wins"),
            metrics.get("avg_holding_time"),
            metrics.get("median_holding_time"),

            pattern_stats_json,

            optimizer,
            search_space_json,
            random_seed,

            1 if approved_for_live else 0,
            live_params_json,
            live_deployment_timestamp
        ))

        conn.commit()
        conn.close()

    def save_best_trial(self, row):
        conn = self._connect()
        c = conn.cursor()

        c.execute("""
            INSERT INTO best_trials (
                timestamp, symbol, timeframe, parameters,
                optimization_id, trial_number, is_best, notes,
                start_timestamp, end_timestamp, num_candles, version, data_hash,
                trades, winrate, expectancy, profit_factor,
                max_drawdown, rr, avg_win, avg_loss,
                long_winrate, short_winrate, long_expectancy, short_expectancy,
                max_consecutive_losses, max_consecutive_wins,
                avg_holding_time, median_holding_time,
                pattern_stats,
                optimizer, search_space, random_seed,
                approved_for_live, live_parameters, live_deployment_timestamp,
                selected_at, source_trial_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row["timestamp"], row["symbol"], row["timeframe"], row["parameters"],
            row["optimization_id"], row["trial_number"], 1, row["notes"],
            row["start_timestamp"], row["end_timestamp"], row["num_candles"], row["version"], row["data_hash"],
            row["trades"], row["winrate"], row["expectancy"], row["profit_factor"],
            row["max_drawdown"], row["rr"], row["avg_win"], row["avg_loss"],
            row["long_winrate"], row["short_winrate"], row["long_expectancy"], row["short_expectancy"],
            row["max_consecutive_losses"], row["max_consecutive_wins"],
            row["avg_holding_time"], row["median_holding_time"],
            row["pattern_stats"],
            row["optimizer"], row["search_space"], row["random_seed"],
            row["approved_for_live"], row["live_parameters"], row["live_deployment_timestamp"],
            datetime.utcnow().isoformat(), row["id"]
        ))

        conn.commit()
        conn.close()

    def get_trial(self, optimization_id, trial_number):
        conn = self._connect()
        c = conn.cursor()

        c.execute("""
            SELECT * FROM backtests
            WHERE optimization_id = ? AND trial_number = ?
        """, (optimization_id, trial_number))

        row = c.fetchone()
        conn.close()

        if row is None:
            return None

        # Convert sqlite Row to dict
        return dict(row)
