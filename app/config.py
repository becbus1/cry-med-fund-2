import os

class Config:
    MODE: str = os.getenv("MODE", "paper")  # paper | prod
    VENUE: str = os.getenv("VENUE", "bybit")
    SYMBOL: str = os.getenv("SYMBOL", "BTCUSDT")
    USE_TESTNET: bool = os.getenv("USE_TESTNET", "true").lower() == "true"
    API_KEY: str | None = os.getenv("API_KEY")
    API_SECRET: str | None = os.getenv("API_SECRET")
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")  # Postgres; else SQLite fallback
    DAILY_MAX_DD_BPS: int = int(os.getenv("DAILY_MAX_DD_BPS", "150"))
    KILL_SWITCH_TOKEN: str = os.getenv("KILL_SWITCH_TOKEN", "changeme")
    WINDOW_SIZE: int = int(os.getenv("WINDOW_SIZE", "120"))  # number of trades in rolling window
    ENTRY_Z: float = float(os.getenv("ENTRY_Z", "2.0"))
    TP_BPS: float = float(os.getenv("TP_BPS", "8.0"))
    SL_BPS: float = float(os.getenv("SL_BPS", "5.0"))
    TIME_STOP_SEC: int = int(os.getenv("TIME_STOP_SEC", "60"))
    NOTIONAL_USDT: float = float(os.getenv("NOTIONAL_USDT", "25"))  # paper sizing
    FEES_BPS: float = float(os.getenv("FEES_BPS", "4.0"))
    SLIP_BPS: float = float(os.getenv("SLIP_BPS", "2.0"))
    HEARTBEAT_SEC: int = int(os.getenv("HEARTBEAT_SEC", "15"))
