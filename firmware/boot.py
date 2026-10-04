#!/bin/python3
# this is specially created for ssd1306

import os, fcntl, socket, json, time
from boot_assets.font import FONT_8X8

I2C_SLAVE = 0x0703
OLED_ADDRESS = 0x3C
SOCKET_PATH = "/tmp/aucboard_boot.sock"
VERSION = "v1.0.1"

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

def draw_progress_bar(bus, percent):
    bar_width = int((percent / 100) * 124)
    outline_byte = 0b00111110
    fill_byte = 0b00011100
    bar_data = []
    for col in range(128):
        if col == 0 or col == 127:
            bar_data.append(outline_byte)
        elif col <= bar_width:
            bar_data.append(fill_byte)
        else:
            bar_data.append(outline_byte & 0b00100010)
    set_cursor(bus, 0, 5)
    write(bus, 0x40, bar_data)

def draw_status(bus, message):
    set_cursor(bus, 0, 6)
    write(bus, 0x40, [0x00] * 128)
    text(bus, message[:16], 0, 6)

def init_display(bus):
    write(bus, 0x00, INIT_SEQ)
    set_cursor(bus, 0, 0)
    write(bus, 0x40, [0x00] * 1024)
    title = "AUCBOARD"
    title_col = (128 - len(title) * 8) // 2
    text(bus, title, col=title_col, page=1)
    ver_col = (128 - len(VERSION) * 8) // 2
    text(bus, VERSION, ver_col, 2)
    draw_progress_bar(bus, 0)
    draw_status(bus, "Waiting...")

def main():
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    try:
        fd = os.open("/dev/i2c-1", os.O_RDWR)

        with os.fdopen(fd, "wb", buffering=0) as bus:
            fcntl.ioctl(fd, I2C_SLAVE, OLED_ADDRESS)
            init_display(bus)
            time.sleep(10)

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as srv:
                srv.bind(SOCKET_PATH)
                srv.listen(1)
                conn, _ = srv.accept()
                with conn:
                    buf = ""
                    while True:
                        data = conn.recv(256).decode("utf-8")
                        if not data:
                            break
                        buf += data
                        while "\n" in buf:
                            line, buf = buf.split("\n",1)
                            try:
                                msg = json.loads(line)
                                draw_progress_bar(bus, msg["percent"])
                                draw_status(bus, msg["status"])
                            except (json.JSONDecodeError, KeyError):
                                pass
    except Exception as e:
        import sys
        print(f"oled text render failed: {e}", file=sys.stderr)
    finally:
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

if __name__ == "__main__": main()