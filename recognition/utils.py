_debug = False

def init(debug):
    """
    If DEBUG is True, enable debugging.
    """
    global _debug
    _debug = debug

def debug(*args):
    """
    Print ARGS, forwarding all of them to the 'print' function, but only if
    debug is enabled.
    """
    if _debug:
        print(*args)

def tuple_to_hex(pixel):
    """
    Convert pixel to (R, G, B) format to '#RRGGBB' format.
    """
    res = "#"

    for i in range(3):
        suffix = hex(pixel[i])[2:]

        if len(suffix) == 1:
            res += "0" + suffix
        else:
            res += suffix

    return res
