from gpiozero import Button, OutputDevice
from gpiozero.pins.native import NativeFactory
from player import Player

from luma.core.interface.serial import spi, i2c
from luma.core.render import ImageDraw, canvas
from luma.oled.device import ssd1306, device

import os, pathlib, sys, logging, shutil

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
        self.playing = False
        self.player = Player()

def main():
    # mainloop
    logger.info("Mainloop started")
    main_canvas = canvas()
    pass

if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger("aucboard")

    logger.info("Aucboard is starting...")

    if not os.path.exists(BASE_DIR / "songs"):
        logger.warning("Aucboard songs directory was not found, creating...")
        os.makedirs(BASE_DIR / "songs", exist_ok=True)

    main()