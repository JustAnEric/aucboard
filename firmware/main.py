from gpiozero import Button, OutputDevice

#gpio
TOP_BUTTON = Button("BOARD29")
RIGHT_BUTTON = Button("BOARD31")
LEFT_BUTTON = Button("BOARD33")
BOTTOM_BUTTON = Button("BOARD37")

FLT_DAC = OutputDevice("BOARD13") # or gp 27 
DEMP_DAC = OutputDevice("BOARD15") # or gp 22
XSMT_DAC = OutputDevice("BOARD11") # or gp 17 | softmute
FMT_DAC = OutputDevice("BOARD16") # or gp 23

