import time

verbose = 7

printLogs = []


def printer(verbosityThreshold: int, msgArgs: list):
    if verbose & verbosityThreshold > 0:
        print(*([time.time_ns(), ":"] + msgArgs))
        printLogs.append(str(time.time_ns())+" : "+str(msgArgs))


def mod(x: int, y: int) -> int:
    return ((x % y) + y) % y


def setVerbose(verboseLevel: int):
    global verbose
    verbose = verboseLevel


def savePrinter():
    with open("logs.txt", "w") as f:
        for log in printLogs:
            f.write(str(log) + "\n")
        f.close()
