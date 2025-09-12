import time
from sqlalchemy import text
from ..common.config import Config
from ..common.db import SessionLocal

class PaperExecutor:
    def __init__(self):
        self.position = 0.0
        self.entry_px = None

    def _bps(self, px, bps):
        return px * (bps / 10000.0)

    def _now_ms(self):
        return int(time.time()*1000)

    def maybe_enter(self, side: str, px: float):
        if self.position != 0.0:
            return
        qty = Config.NOTIONAL_USDT / px
        # record order
        with SessionLocal() as s:
            s.execute(text("INSERT INTO orders(ts, side, px, qty, status) VALUES(:ts, :side, :px, :qty, 'filled')"),
                      {'ts': self._now_ms(), 'side': side, 'px': px, 'qty': qty})
            s.commit()
        # immediate fill (paper)
        self.position = qty if side == 'long' else -qty
        self.entry_px = px

    def maybe_exit(self, px: float):
        if self.position == 0.0 or self.entry_px is None:
            return
        side = 'sell' if self.position > 0 else 'buy'
        with SessionLocal() as s:
            s.execute(text("INSERT INTO orders(ts, side, px, qty, status) VALUES(:ts, :side, :px, :qty, 'filled')"),
                      {'ts': self._now_ms(), 'side': side, 'px': px, 'qty': abs(self.position)})
            s.commit()
        # PnL calc with simple fees/slippage
        fees = (Config.FEES_BPS + Config.SLIP_BPS) / 10000.0
        gross = (px - self.entry_px) * self.position
        realized = gross - abs(self.entry_px * self.position) * fees - abs(px * self.position) * fees
        with SessionLocal() as s:
            s.execute(text("INSERT INTO fills(order_id, ts, px, qty) VALUES(NULL, :ts, :px, :qty)"),
                      {'ts': self._now_ms(), 'px': px, 'qty': abs(self.position)})
            s.execute(text("INSERT INTO pnl(ts, realized, unrealized) VALUES(:ts, :realized, 0.0)"),
                      {'ts': self._now_ms(), 'realized': realized})
            s.commit()
        self.position = 0.0
        self.entry_px = None

    def exit_rules(self, px: float):
        if self.position == 0.0 or self.entry_px is None:
            return False
        # take profit / stop loss in bps
        tp = self._bps(self.entry_px, Config.TP_BPS)
        sl = self._bps(self.entry_px, Config.SL_BPS)
        if self.position > 0:
            if px >= self.entry_px + tp or px <= self.entry_px - sl:
                return True
        else:
            if px <= self.entry_px - tp or px >= self.entry_px + sl:
                return True
        return False
