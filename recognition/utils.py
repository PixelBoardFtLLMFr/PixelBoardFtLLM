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
