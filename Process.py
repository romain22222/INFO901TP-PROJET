import random
from time import sleep
from typing import Callable

from pyeventbus3.pyeventbus3 import *

from Message import Message, BroadcastMessage, MessageTo, Token, TokenState, SyncingMessage


def mod(x: int, y: int) -> int:
    return ((x % y) + y) % y


class Process(Thread):
    nbProcessCreated = 0

    def __init__(self, name: str, nbProcess: int, verbose: int):
        Thread.__init__(self)

        self.nbProcess = nbProcess
        self.myId = Process.nbProcessCreated
        Process.nbProcessCreated += 1
        self.name = name

        PyBus.Instance().register(self, self)

        self.alive = True
        self.horloge = 0
        self.verbose = verbose
        self.token_state = TokenState.Null
        self.nbSync = 0
        self.isSyncing = False
        self.start()

    def run(self):
        while self.nbProcess != Process.nbProcessCreated:
            pass
        if self.myId == 0:
            self.releaseToken()
        self.synchronize()
        loop = 0
        while self.alive:
            self.printer(2, [self.name, "Loop:", loop, "; Internal Clock:", self.horloge])
            sleep(1)

            if self.name == "P1":
                self.sendTo("P2", "ga")
                self.doCriticalAction(self.criticalActionWarning, ["lol"])
            if self.name == "P2":
                self.broadcast("JE SUIS LA, JE M APPELLE P2")
            if self.name == "P3":
                receiver = str(random.randint(0, self.nbProcess - 1))
                self.sendTo("P" + receiver, "Je suis un spam, j'adore parler à toi, mon cher P" + receiver)
            loop += 1
        sleep(1)
        self.printer(2, [self.name, "stopped"])

    def stop(self):
        self.alive = False
        self.join()

    def sendMessage(self, message: Message, verbosityThreshold=1):
        self.horloge += 1
        message.horloge = self.horloge
        self.printer(verbosityThreshold, [self.name, "sends:", message.getObject()])
        PyBus.Instance().post(message)

    def receiveMessage(self, message: Message, verbosityThreshold=1):
        self.printer(verbosityThreshold, [self.name, "Processes event:", message.getObject()])
        self.horloge = max(self.horloge, message.horloge) + 1

    def sendAll(self, obj: any):
        self.sendMessage(Message(obj))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Message)
    def process(self, event: Message):
        self.receiveMessage(event)

    def broadcast(self, obj: any):
        self.sendMessage(BroadcastMessage(obj, self.name))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, event: BroadcastMessage):
        if event.from_process != self.name:
            self.receiveMessage(event)

    def sendTo(self, dest: str, obj: any):
        self.sendMessage(MessageTo(obj, self.name, dest))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, event: MessageTo):
        if event.to_process == self.name:
            self.receiveMessage(event)

    def releaseToken(self):
        self.printer(8, [self.myId, "release token to", mod(self.myId + 1, Process.nbProcessCreated)])
        if self.token_state == TokenState.SC:
            self.token_state = TokenState.Release
        token = Token()
        token.from_process = self.myId
        token.to_process = mod(self.myId + 1, Process.nbProcessCreated)
        token.nbSync = self.nbSync
        self.sendMessage(token, verbosityThreshold=8)
        self.token_state = TokenState.Null

    def requestToken(self):
        self.token_state = TokenState.Requested
        self.printer(4, [self.name, "awaits the token"])
        while self.token_state == TokenState.Requested:
            if not self.alive:
                return
        self.token_state = TokenState.SC
        self.printer(4, [self.name, "has the token that it requested"])

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event: Token):
        """
        Ici le token est en mouvement continu. Il s'arrête lorsqu'un processus le demande sur une section critique.
        self.isSyncing est la afin de savoir si un processus est en attente de synchronisation, mais n'a pas encore reçu le token.
        self.nbSync est la pour savoir combien de processus sont en attente de synchronisation actuellement. S'il vaut 0, alors on
        peut envoyer un message de synchronisation s'il était en attente de synchronisation.
        self.token_state est la pour connaître la possession du token. Cf TokenState.
        """
        if event.to_process == self.myId:
            self.receiveMessage(event, verbosityThreshold=8)
            if not self.alive:
                return
            if self.token_state == TokenState.Requested:
                self.token_state = TokenState.SC
                return
            if self.isSyncing:
                self.isSyncing = False
                self.nbSync = mod(event.nbSync + 1, Process.nbProcessCreated)
                if self.nbSync == 0:
                    self.sendMessage(SyncingMessage(self.myId))
            self.releaseToken()

    def doCriticalAction(self, funcToCall: Callable, args: list):
        """
        Afin de faire une action critique, on demande le token, on fait l'action, puis on le relâche.
        Ici l'action critique est une fonction passée en paramètre avec la liste des arguments.
        """
        self.requestToken()
        if self.alive:
            funcToCall(*args)
            self.releaseToken()

    def criticalActionWarning(self, msg: str):
        """
        Ici l'action critique est un print d'un message, mais on pourrait imaginer que ce soit un accès à une ressource partagée comme un fichier.
        """
        print("THIS IS A CRITICAL ACTION, TOKEN IN USE BY", self.name, "; A MESSAGE FROM THE LOOP :", msg)

    def synchronize(self):
        self.isSyncing = True
        self.printer(2, [self.myId, "is syncing"])
        while self.isSyncing:
            if not self.alive:
                return
        while self.nbSync != 0:
            if not self.alive:
                return
        self.printer(2, [self.myId, "synced"])

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncingMessage)
    def onSyncing(self, event: SyncingMessage):
        if event.from_process != self.myId:
            self.receiveMessage(event)
            self.nbSync = 0

    def printer(self, verbosityThreshold: int, msgArgs: list):
        if self.verbose & verbosityThreshold > 0:
            print(*([time.time_ns(), ":"] + msgArgs))
