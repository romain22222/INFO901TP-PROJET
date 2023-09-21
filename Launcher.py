from threading import Thread
from time import sleep
from typing import List

from Process import Process
import sys
from Utils import setVerbose, savePrinter, printer, VerbosityType


def launch(nbProcessToCreate: int, runningTime: int):
    """
    Launches the several processes
    :param nbProcessToCreate: the number of processes to create
    :param runningTime: the time to run the processes
    :return: None
    """
    def createProcess(x: int):
        """
        Creates a process
        :param x: the position of the process (only visual)
        :return: None
        """
        printer("MAIN", ["Creating process", x], VerbosityType.MAIN)
        processes.append(Process("P" + str(x), nbProcessToCreate))
        printer("MAIN", ["Process", x, "created"], VerbosityType.MAIN)

    processes = []

    processes_launches: List[Thread] = []

    for i in range(nbProcessToCreate):
        processes_launches.append(Thread(target=createProcess, args=(i,)))

    for p in processes_launches:
        p.start()
    for p in processes_launches:
        p.join()

    sleep(runningTime)

    for p in processes:
        printer("MAIN", ["Stopping process", p], VerbosityType.MAIN)
        p.stop()
        printer("MAIN", ["Process", p, "stopped"], VerbosityType.MAIN)

    savePrinter()


def getParam(pos: int, default: int, base=10) -> int:
    """
    Gets a numeric parameter from the command line
    :param pos: the position of the parameter
    :param default: the default value if the parameter is not found
    :param base: the base of the parameter (default: 10)
    :return:
    """
    if len(sys.argv) > pos:
        return int(sys.argv[pos], base)
    return default


if __name__ == '__main__':
    setVerbose(getParam(3, 0, 2))
    launch(getParam(1, 3), getParam(2, 15))
