import ctypes, sysconfig, logging

try:
    from ..common import *
except Exception as e:
    from common import *

lib_wwqLyParse = None


def init_lib():
    global lib_wwqLyParse
    if sysconfig.get_platform() == "win-amd64":
        lib_wwqLyParse = ctypes.cdll.LoadLibrary(get_real_path("./wwqLyParse64.dll"))
    else:
        lib_wwqLyParse = ctypes.cdll.LoadLibrary(get_real_path("./wwqLyParse32.dll"))
    lib_wwqLyParse.get_uuid.restype = ctypes.c_char_p
    lib_wwqLyParse.get_name.restype = ctypes.c_char_p
    logging.debug("successful load lib_wwqLyParse %s" % lib_wwqLyParse)


init_lib()


def lib_parse(byte_str: bytes):
    length = len(byte_str)
    p = ctypes.create_string_buffer(byte_str, length)
    lib_wwqLyParse.parse(p, length)
    return p.raw
