from tinytag import TinyTag
from modules.equalizer import EQBand

import dataclasses, time, subprocess, threading, miniaudio, array, numpy as np, os

@dataclasses.dataclass
class TrackState:
    name: str = "Untitled Track"
    album_name: str = "Untitled Album"
    file_name: str = ""
    duration_s: float = 0.0
    current_time: float = 0.0
    bitrate: float = 0.0
    volume: int = 100
    quality_str: str = "0 Hz"

class Player:
    def __init__(self):
        self.current_track = TrackState()
        self.end_event_hooks = []
        self.is_running = True
        self.is_paused = False
        self.eq_bands = [
            EQBand(32), EQBand(64),
            EQBand(125),EQBand(250),
            EQBand(500),EQBand(1000),
            EQBand(2000),EQBand(4000),
            EQBand(8000),EQBand(16000)
        ]

        self.device = miniaudio.PlaybackDevice(output_format=miniaudio.SampleFormat.SIGNED32)
        self.audio = None

        self.track_ended = False # mainloop flag

        for band in self.eq_bands:
            band.setup(self.device.sample_rate, self.device.nchannels)
        
    def on_end(self, func):
        self.end_event_hooks.append(func)
    
    @property
    def is_playing(self):
        if not self.audio:
            return False
        if not self.is_paused:
            return True
        return False

    def play(self, fn: str | None = None):
        if fn:
            self.current_track.file_name = fn

        if self.audio:
            self.device.stop()

        td = self.get_audio_duration_and_bitrate(fn or self.current_track.file_name)
        self.current_track.duration_s = td[0]
        self.current_track.bitrate = td[1]
        ttd = TinyTag.get(fn or self.current_track.file_name)
        self.current_track.album_name = ttd.album or "Untitled Album"
        self.current_track.name = ttd.title or "Untitled Track"

        self.audio = self.stream_audio_with_callback(fn or self.current_track.file_name, self._on_track_end, self.device.nchannels, self.device.sample_rate)
        next(self.audio)
        self.device.start(self.audio)

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def volume(self, value: int | None = None):
        if value is not None:
            self.current_track.volume = value
        else:
            return self.current_track.volume

    @property
    def duration(self):
        return self.current_track.duration_s

    def get_audio_duration_and_bitrate(self, file_path):
        cmd = [
            'ffprobe',
            '-i', file_path,
            '-show_entries', 'format=duration:stream=bit_rate,sample_fmt',
            '-of', 'default=noprint_wrappers=1:nokey=1'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.splitlines()
            duration = float(lines[-1])

            quality = lines[0].strip()
            bitrate_raw = lines[1].strip()
            duration = float(lines[2].strip())
            
            # Calculate bitrate manually instead
            if bitrate_raw == "N/A" or not bitrate_raw.isdigit():
                file_size_bytes = os.path.getsize(file_path)
                # Bits per second = bytes * 8 / duration
                # Kilobits per second (kbps) = bits per second / 1000
                bitrate = int((file_size_bytes * 8) / (duration * 1000))
            else:
                bitrate = int(bitrate_raw)
            
            return duration, bitrate, quality
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return None, None, None

    def stream_audio_with_callback(self, fp, callback, nchannels, sample_rate):
        source_stream = miniaudio.stream_file(fp, output_format=miniaudio.SampleFormat.SIGNED32, nchannels=nchannels, sample_rate=sample_rate)
        required_frames = yield b""

        while True:
            try:
                if self.is_paused:
                    silence = b"\x00" * (required_frames * 2 * 4) 
                    required_frames = yield silence
                    continue

                data = source_stream.send(required_frames)
                if not data:
                    break

                samples = np.frombuffer(data, dtype=np.float32).copy()
                samples = samples.reshape(-1, nchannels)

                for band in self.eq_bands:
                    samples = band.process(samples)

                curr_vol = self.volume() / 100.00
                if curr_vol != 1.0:
                    samples *= curr_vol
                    np.clip(samples, -1.0, 1.0, out=samples)

                data = samples.astype(np.float32).tobytes()
                required_frames = yield data

            except StopIteration:
                break

        callback()

    def _on_track_end(self):
        for i in self.end_event_hooks:
            i()