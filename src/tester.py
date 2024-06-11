import serial
import argparse

def light_up_tile(ser, index, color):
    out = ""
    for i in range(20):
        out += f"{index*20 + i},{color}\n"
    ser.write(out.encode('ascii'))

arg_parser = argparse.ArgumentParser(prog="tester", description="Test the pixel board.")
arg_parser.add_argument("-p", "--port", action='store', default="/dev/ttyACM0",
                        help="pixel board serial port")
arg_parser.add_argument("-c", "--color", action='store', default="#ffffff",
                        help="color to give the pixels")
arg_parser.add_argument("indices", help="indices of tiles to light up, can be either"
                        + "a single index like 0 or an interval like 0-4")
args = arg_parser.parse_args()

ser = serial.Serial(args.port)

indices = [int(x) for x in args.indices.split("-")]
length = len(indices)

if length == 1:
    light_up_tile(ser, indices[0] - 1, args.color)
else:
    for i in range(indices[0] - 1, indices[1]):
        light_up_tile(ser, i, args.color)
