import numpy as np
from scipy.signal import sosfilt

# https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html

class EQBand:
    def __init__(self, freq: float, gain_db: float = 0.0, q: float = 1.4):
        self.freq = freq
        self.gain_db = gain_db
        self.q = q
        self._sos = None
        self._zi = None

    def setup(self, sample_rate:int, nchannels:int):
        self._nchannels = nchannels
        self._build(sample_rate)

    def _build(self, sample_rate:int):
        if self.gain_db == 0.0:
            self._sos = None
            self._zi = None
            return

        A = 10 ** (self.gain_db / 40.0)
        w0 = 2 * np.pi * self.freq / sample_rate
        alpha = np.sin(w0) / (2 * self.q)
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha /A
        self._sos = np.array([[b0/a0, b1/a0, b2/a0, 1.0, a1/a0, a2/a0]])
        self._zi = [np.zeros((1, 2)) for _ in range(self._nchannels)]

    def process(self, samples: np.ndarray) -> np.ndarray:
        if self._sos is None:
            return samples
        out = np.empty_like(samples)
        for ch in range(samples.shape[1]):
            out[:, ch], self._zi[ch] = sosfilt(self._sos, samples[:, ch], zi=self._zi[ch])
        return out