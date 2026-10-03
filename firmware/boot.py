#!/bin/python3
# this is specially created for ssd1306

import os
import fcntl
from boot_assets.font import FONT_8X8

I2C_SLAVE = 0x0703
OLED_ADDRESS = 0x3C

INIT_SEQ = [0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 
            0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 
            0xDB, 0x40, 0xA4, 0xA6, 0xAF]

def write(bus, control_byte, data_list):
    chunk_size = 16
    for i in range(0, len(data_list), chunk_size):
        chunk = data_list[i:i + chunk_size]
        bus.write(bytes([control_byte] + chunk))

def set_cursor(bus, col: int, page: int):
    # col is 0 to 127
    # page is 0 to 7
    commands = [0x21, col, 127, 0x22, page, 7]
    write(bus, 0x00, commands)

def text(bus, text: str, col: int, page: int):
    set_cursor(bus, col, page)
    pixel_buffer = []

    for char in text.upper():
        char_bb = FONT_8X8.get(char, FONT_8X8[' '])
        pixel_buffer.extend(char_bb)

    write(bus, 0x40, pixel_buffer)

def main():
    try:
        fd = os.open("/dev/i2c-1", os.O_RDWR)

        with os.fdopen(fd, "wb", buffering=0) as bus:
            fcntl.ioctl(fd, I2C_SLAVE, OLED_ADDRESS)

            write(bus, 0x00, INIT_SEQ)
            set_cursor(bus, 0, 0)
            write(bus, 0x40, [0x00] * 1024)
            text(bus, "AUCBOARD", col=4, page=1)
    except Exception as e:
        import sys
        print(f"oled text render failed: {e}", file=sys.stderr)

if __name__ == "__main__": main()