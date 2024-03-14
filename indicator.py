import pandas as pd

class MovingAverageCalculator:
    def __init__(self, window_size):
        self.window_size = window_size
        self.data = []

    def add_data_point(self, value):
        self.data.append(value)
        if len(self.data) > self.window_size:
            self.data.pop(0)

    def calculate_sma(self):
        if len(self.data) < self.window_size:
            return None
        return sum(self.data) / len(self.data)

    def calculate_ema(self, smoothing_factor):
        if len(self.data) == 0:
            return None
        ema = self.data[0]
        for i in range(1, len(self.data)):
            ema = smoothing_factor * self.data[i] + (1 - smoothing_factor) * ema
        return ema