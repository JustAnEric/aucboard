from gpiozero import Button, OutputDevice
from gpiozero.pins.native import NativeFactory
from player import Player

from luma.core.interface.serial import spi, i2c
from luma.core.render import ImageDraw, canvas
from luma.oled.device import ssd1306, device

import os, pathlib, sys, logging, shutil, time, threading, socket, json

BASE_DIR = pathlib.Path(os.path.dirname(__file__))

#gpio
TOP_BUTTON = Button("BOARD29")
RIGHT_BUTTON = Button("BOARD31")
LEFT_BUTTON = Button("BOARD33")
BOTTOM_BUTTON = Button("BOARD37")

FLT_DAC = OutputDevice("BOARD13") # or gp 27 
DEMP_DAC = OutputDevice("BOARD15") # or gp 22
XSMT_DAC = OutputDevice("BOARD11") # or gp 17 | softmute
FMT_DAC = OutputDevice("BOARD16") # or gp 23

#display
DISP1_PORT = 1
DISP1_ADDRESS = 0x3c
DISP1 = ssd1306(i2c(port=DISP1_PORT, address=DISP1_ADDRESS))

class PlayerState:
    def __init__(self):
        self.player = Player()
        self.last_tick = 0
        self.queue = []
        self.queue_index = 0

        self._track_ended = threading.Event()

        @self.player.on_end
        def on_player_end():
            print('track ended')

            self._track_ended.set()

    @property
    def playing(self):
        return self.player.is_playing

    @playing.setter
    def playing(self, value: bool):
        if value == True:
            self.player.resume()
        elif value == False:
            self.player.pause()
        else:
            logger.warning("Unintentional set on PlayerState.playing? (not a bool value!)")

    @property
    def position(self):
        return self.player.current_track.current_time

    @position.setter
    def position(self, value: float):
        self.player.current_track.current_time = value

    @property
    def duration(self):
        return self.player.duration

    def advance_track(self):
        if not self.queue:
            return

        if self.queue_index == len(self.queue) - 1:
            self.queue_index = 0
        else:
            self.queue_index += 1
        self.position = 0.0
        self.playing = True

    def rewind_track(self):
        if not self.queue:
            return

        if self.queue_index == 0:
            self.queue_index = len(self.queue) - 1
        else:
            self.queue_index -= 1
        self.position = 0.0

def update_playback(state: PlayerState, delta):
    if not state.playing:
        return
    state.position += delta
    #if state.position >= state.duration:
    #    state.advance_track()
    #    state.playing = True # set new state

def enum_tracks(dir="./music"):
    for dirp,dirn,filn in os.walk(dir):
        for f in filn:
            fullpath = os.path.join(dirp, f)
            froot,fext = os.path.splitext(f)
            if fext.lower() in [".mp3",".flac",".mp4"]:
                print("Found:",fullpath)
                state.queue.append({ "path": fullpath, "filename": f, "metadata": {} })

def update_boot(sock, percent, status):
    msg = json.dumps({"percent": percent, "status": status}) + "\n"
    sock.sendall(msg.encode())

def main(device: device, state: PlayerState, boot_s: socket.socket):
    # mainloop
    logger.info("Mainloop started")

    update_boot(boot_s, 100, "Ready!")
    boot_s.close()

    enum_tracks(BASE_DIR / "music")

    state.player.play(state.queue[state.queue_index]['path'])

    while True:
        with canvas(device) as cv:
            now = time.monotonic()
            delta = now - state.last_tick
            state.last_tick = now
            if state._track_ended.is_set():
                state._track_ended.clear()
                state.advance_track()
                state.player.play(state.queue[state.queue_index]['path'])
            else:
                update_playback(state, delta)

        time.sleep(0.05)

if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger("aucboard")

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/tmp/aucboard_boot.sock")
    update_boot(s, 25, "Starting audio...")

    logger.info("Aucboard is starting...")

    if not os.path.exists(BASE_DIR / "music"):
        logger.warning("Aucboard music directory was not found, creating...")
        os.makedirs(BASE_DIR / "music", exist_ok=True)

    state = PlayerState()

    main(
        DISP1, 
        state,
        s
    )