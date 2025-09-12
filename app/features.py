import numpy as np

class Rolling:
    def __init__(self, window=120):
        self.window = window
        self.prices = []

    def push(self, px: float):
        self.prices.append(px)
        if len(self.prices) > self.window:
            self.prices.pop(0)

    def ready(self):
        return len(self.prices) >= self.window

    def zret(self):
        # simple return z-score over window
        if len(self.prices) < 3:
            return 0.0
        rets = np.diff(self.prices) / np.array(self.prices[:-1])
        if len(rets) < 5:
            return 0.0
        mu = np.mean(rets)
        sd = np.std(rets) + 1e-9
        return float((rets[-1] - mu) / sd)
