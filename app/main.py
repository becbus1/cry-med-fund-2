
import asyncio
import time
from fastapi import FastAPI, HTTPException, Query

from app.common.db import init_db, SessionLocal
from app.common.config import Config
from sqlalchemy import text
from app.orchestrator.ingest import Ingestor
from app.orchestrator.features import Rolling
from app.live.executor import PaperExecutor

app = FastAPI(title="Crypto Edge Paper MVP")

# globals for in-process monolith behavior
roll = Rolling(window=Config.WINDOW_SIZE)
ex = PaperExecutor()
last_trade_ts = 0
killswitch = False

@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(run_pipeline())

@app.get("/health")
async def health():
    return {"ok": True, "mode": Config.MODE, "symbol": Config.SYMBOL, "killswitch": killswitch}

@app.get("/killswitch")
async def toggle(token: str = Query(...)):
    global killswitch
    if token != Config.KILL_SWITCH_TOKEN:
        raise HTTPException(status_code=401, detail="bad token")
    killswitch = True
    # flatten position (paper)
    with SessionLocal() as s:
        s.execute(text("INSERT INTO pnl(ts, realized, unrealized) VALUES(:ts, 0.0, 0.0)"),
                  {'ts': int(time.time()*1000)})
        s.commit()
    return {"ok": True, "killswitch": killswitch}

@app.get("/metrics")
async def metrics():
    with SessionLocal() as s:
        trades = s.execute(text("SELECT COUNT(*) as c FROM trades")).scalar()
        orders = s.execute(text("SELECT COUNT(*) as c FROM orders")).scalar()
        pnl = s.execute(text("SELECT COALESCE(SUM(realized),0) FROM pnl")).scalar()
    return {"trades": trades or 0, "orders": orders or 0, "realized_pnl": pnl or 0.0}

async def run_pipeline():
    # Start ingest
    ing = Ingestor(Config.SYMBOL)
    asyncio.create_task(ing.run())
    await asyncio.sleep(2)

    # Main loop: poll latest trade from DB, compute feature, make paper decisions
    while True:
        if killswitch:
            await asyncio.sleep(1)
            continue
        # fetch the last N trades for price
        with SessionLocal() as s:
            row = s.execute(text("SELECT ts, px FROM trades ORDER BY id DESC LIMIT 1")).fetchone()
        if row:
            ts, px = row
            if ts != None:
                roll.push(float(px))
                if roll.ready():
                    z = roll.zret()
                    # Simple detector: enter long if z > ENTRY_Z, short if z < -ENTRY_Z
                    if ex.position == 0.0:
                        if z > Config.ENTRY_Z:
                            ex.maybe_enter('long', float(px))
                        elif z < -Config.ENTRY_Z:
                            ex.maybe_enter('short', float(px))
                    else:
                        if ex.exit_rules(float(px)):
                            ex.maybe_exit(float(px))
        await asyncio.sleep(0.25)
