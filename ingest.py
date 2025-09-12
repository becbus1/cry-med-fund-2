import asyncio
import time
from pybit.unified_trading import WebSocket
from ..common.config import Config
from ..common.db import SessionLocal
from sqlalchemy import text

class Ingestor:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ws = None
        self.last_heartbeat = time.time()

    def _on_trade(self, message):
        # message example contains data list with {T: ts, p: price, v: size}
        if 'data' not in message:
            return
        rows = message['data']
        if not isinstance(rows, list):
            rows = [rows]
        with SessionLocal() as s:
            for r in rows:
                ts = int(r.get('T') or r.get('tradeTime') or int(time.time()*1000))
                px = float(r.get('p') or r.get('price'))
                qty = float(r.get('v') or r.get('size') or 0)
                s.execute(text("INSERT INTO trades(ts, px, qty) VALUES(:ts, :px, :qty)"), {'ts': ts, 'px': px, 'qty': qty})
            s.commit()
        self.last_heartbeat = time.time()

    async def run(self):
        endpoint = "wss://stream-testnet.bybit.com/v5/public" if Config.USE_TESTNET else "wss://stream.bybit.com/v5/public"
        self.ws = WebSocket(testnet=Config.USE_TESTNET, channel_type="linear" if "USDT" in self.symbol else "spot")
        # Subscribe to public trade stream
        self.ws.trade_stream(symbol=self.symbol, callback=self._on_trade)
        # Heartbeat loop
        while True:
            if time.time() - self.last_heartbeat > Config.HEARTBEAT_SEC * 2:
                # basic reconnect by re-creating ws
                try:
                    self.ws.exit()
                except Exception:
                    pass
                self.ws = WebSocket(testnet=Config.USE_TESTNET, channel_type="linear" if "USDT" in self.symbol else "spot")
                self.ws.trade_stream(symbol=self.symbol, callback=self._on_trade)
                self.last_heartbeat = time.time()
            await asyncio.sleep(1)
