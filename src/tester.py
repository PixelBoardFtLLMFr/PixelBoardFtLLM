import serial
import argparse
import time

def light_up_tile(ser, index, color):
    out = ""
    for i in range(20):
        out += f"{index*20 + i},{color}\n"
    ser.write(out.encode('ascii'))

def light_up_column(ser, index, color, delay):
    for j in range(5):
        light_up_tile(ser, index*5 + j, color)
        time.sleep(delay)

def display_france(ser, delay):
    blue = "#0000ff"
    white = "#ffffe0"
    red = "#ff0000"

    for i in range(2):
        light_up_column(ser, i, blue, delay)

    light_up_column(ser, 2, white, delay)

    for i in range(3, 5):
        light_up_column(ser, i, red, 1.5*delay)

def light_off(ser, delay):
    for i in range(5):
        light_up_column(ser, i, "#000000", delay)

arg_parser = argparse.ArgumentParser(prog="tester", description="Test the pixel board.")
arg_parser.add_argument("-p", "--port", action='store', default="/dev/ttyACM0",
                        help="pixel board serial port")
arg_parser.add_argument("-c", "--color", action='store', default="#ffffff",
                        help="color to give the pixels")
arg_parser.add_argument("-i", "--index", action='store', default=None,
                        help="indices of tiles to light up, can be either"
                        + "a single index like 0 or an interval like 0-4")
arg_parser.add_argument("-f", "--france", action='store_true', default=False,
                        help="display the French flag")
arg_parser.add_argument("-o", "--off", action='store_true', default=False,
                        help="turn off the pixel board")
arg_parser.add_argument("-d", "--delay", action='store', default=0,
                        type=float, help="delay between tiles")

args = arg_parser.parse_args()

ser = serial.Serial(args.port)
ser.baudrate = 9600

if args.off:
    light_off(ser, args.delay)
    exit(0)

if args.france:
    display_france(ser, args.delay)
    exit(0)

indices = [int(x) for x in args.index.split("-")]
length = len(indices)

if length == 1:
    light_up_tile(ser, indices[0] - 1, args.color)
else:
    for i in range(indices[0] - 1, indices[1]):
        light_up_tile(ser, i, args.color)
