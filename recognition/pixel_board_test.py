import serial

ser = serial.Serial("/dev/ttyACM0")
print(ser.name)

def write_color(index, color):
    ser.write(f"{index},{color}\n".encode("ascii"))

write_color(1, "#ff0000")
write_color(2, "#00ff00")
write_color(3, "#0000ff")
write_color(4, "#000000")

for i in range(9):
    write_color(20*i, "#ffffff")
    write_color(20*(i+1) - 1, "#ffffff")
