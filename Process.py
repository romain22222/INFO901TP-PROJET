import random
from time import sleep

from pyeventbus3.pyeventbus3 import *

from Com import Com
from Utils import printer


class Process(Thread):
    nbProcessCreated = 0

    def __init__(self, name: str, nbProcess: int):
        Thread.__init__(self)

        self.nbProcess = nbProcess
        self.myId = Process.nbProcessCreated
        Process.nbProcessCreated += 1
        self.name = name
        self.com = Com()

        PyBus.Instance().register(self, self)

        self.alive = True
        self.start()

    def run(self):
        while self.nbProcess != Process.nbProcessCreated:
            pass
        if self.myId == 0:
            self.com.releaseToken()
        self.com.synchronize()
        loop = 0
        while self.alive:
            printer(2, [self.name, "Loop:", loop, "; Internal Clock:", self.com.horloge])
            sleep(1)

            if self.name == "P1":
                self.com.sendTo("P2", "ga")
                self.com.doCriticalAction(self.criticalActionWarning, ["lol"])
            if self.name == "P2":
                self.com.broadcast("JE SUIS LA, JE M APPELLE P2")
            if self.name == "P3":
                receiver = str(random.randint(0, self.nbProcess - 1))
                self.com.sendTo("P" + receiver, "Je suis un spam, j'adore parler à toi, mon cher P" + receiver)
            loop += 1
        sleep(1)
        printer(2, [self.name, "stopped"])

    def stop(self):
        self.alive = False
        self.join()

    def criticalActionWarning(self, msg: str):
        print("THIS IS A CRITICAL ACTION, TOKEN IN USE BY", self.name, "; A MESSAGE FROM THE LOOP :", msg)
