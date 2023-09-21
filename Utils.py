import inspect
import time
from enum import Enum
from typing import List

verbose = 0

printLogs = []


class VerbosityType(Enum):
    """
    The verbosity types
    """
    NONE = -1
    USER_MESSAGES = 0
    SYNCHRONISATION = 1
    ACKNOWLEDGEMENT = 2
    CRITICAL_SECTION = 3
    TOKEN = 4
    HEARTBEAT = 5
    INIT_ID = 6
    MAIN = 7


def printer(sender: any, msgArgs: any | List[any], verbosityThreshold: VerbosityType = VerbosityType.NONE):
    """
    Prints a message if the verbosity type is included in the current verbosity
    :param sender: who prints the log (either MAIN, a process or a com)
    :param msgArgs: the message to print, can be a list of arguments or a single argument (will be converted to a list)
    :param verbosityThreshold: the verbosity threshold of the message
    :return: None
    """
    if verbosityThreshold == VerbosityType.NONE or (2 ** verbosityThreshold.value) & verbose > 0:
        if type(msgArgs) != list:
            msgArgs = [msgArgs]
        message = " ".join(["{", str(time.time_ns()), "}[", inspect.stack()[1][3], "](", str(sender), "):"] + [str(v) for v in msgArgs])
        print(message)
        printLogs.append(message)


def mod(x: int, y: int) -> int:
    """
    Modulo function
    :param x: the number to mod
    :param y: the modulo
    :return: x mod y
    """
    return ((x % y) + y) % y


def setVerbose(verboseLevel: int):
    """
    Sets the verbosity level
    :param verboseLevel: the new verbosity level
    :return: None
    """
    global verbose
    verbose = verboseLevel


def savePrinter():
    """
    Saves the printer logs to a file
    :return: None
    """
    with open("logs.txt", "w") as f:
        printLogs.sort()
        for log in printLogs:
            f.write(log + "\n")
        f.close()
