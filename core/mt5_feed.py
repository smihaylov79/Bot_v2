# core/mt5_feed.py

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz


class MT5Feed:
    def __init__(self, timezone="Europe/Sofia"):
        self.tz = pytz.timezone(timezone)

    def initialize(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")

    def shutdown(self):
        mt5.shutdown()

    def get_ohlcv(self, symbol, timeframe, n_bars=2000):
        """
        Unified function to fetch OHLCV data from MT5.
        Returns a pandas DataFrame with timezone-aware timestamps.
        """

        # MT5 timeframes are integers, so user passes mt5.TIMEFRAME_M5 etc.
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)

        if rates is None or len(rates) == 0:
            raise RuntimeError(f"Failed to get data for {symbol}: {mt5.last_error()}")

        df = pd.DataFrame(rates)

        # Convert MT5 timestamp to timezone-aware datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # If broker server time is already BG time (or what terminal shows):
        df['time'] = df['time'].dt.tz_localize(self.tz)

        df = df.rename(columns={
            'time': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        })

        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    def get_last_candle(self, symbol, timeframe):
        df = self.get_ohlcv(symbol, timeframe, n_bars=1)
        return df.iloc[-1]
