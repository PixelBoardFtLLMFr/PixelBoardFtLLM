__debug = False

def utils_init(debug):
    global __debug
    __debug = debug

def debug(*args):
    if __debug:
        print(*args)
