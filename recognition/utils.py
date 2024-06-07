_debug = False

def init(debug):
    global _debug
    _debug = debug

def debug(*args):
    if _debug:
        print(*args)
