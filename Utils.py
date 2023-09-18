import time

verbose = 7


def printer(verbosityThreshold: int, msgArgs: list):
    if verbose & verbosityThreshold > 0:
        print(*([time.time_ns(), ":"] + msgArgs))


def mod(x: int, y: int) -> int:
    return ((x % y) + y) % y
