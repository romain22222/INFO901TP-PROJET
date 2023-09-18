from typing import Callable
from pyeventbus3.pyeventbus3 import *
from Message import Message, BroadcastMessage, MessageTo, Token, TokenState, SyncingMessage
from Process import Process
from Utils import printer, mod


# Cette classe doit gérer les communications de la classe Process
class Com:
    def __init__(self, process: Process):
        self.process = process
        self.horloge = 0
        self.isSyncing = False
        self.nbSync = 0

    def sendMessage(self, message: Message, verbosityThreshold=1):
        self.horloge += 1
        message.horloge = self.horloge
        printer(verbosityThreshold, [self.process.name, "sends:", message.getObject()])
        PyBus.Instance().post(message)

    def receiveMessage(self, message: Message, verbosityThreshold=1):
        printer(verbosityThreshold, [self.process.name, "Processes event:", message.getObject()])
        self.horloge = max(self.horloge, message.horloge) + 1

    def sendAll(self, obj: any):
        self.sendMessage(Message(obj))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Message)
    def process(self, event: Message):
        self.receiveMessage(event)

    def broadcast(self, obj: any):
        self.sendMessage(BroadcastMessage(obj, self.process.name))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, event: BroadcastMessage):
        if event.from_process != self.process.name:
            self.receiveMessage(event)

    def sendTo(self, dest: str, obj: any):
        self.sendMessage(MessageTo(obj, self.process.name, dest))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, event: MessageTo):
        if event.to_process == self.process.name:
            self.receiveMessage(event)

    def releaseToken(self):
        printer(8, [self.process.myId, "release token to", mod(self.process.myId + 1, Process.nbProcessCreated)])
        if self.process.token_state == TokenState.SC:
            self.process.token_state = TokenState.Release
        token = Token()
        token.from_process = self.process.myId
        token.to_process = mod(self.process.myId + 1, Process.nbProcessCreated)
        token.nbSync = self.nbSync
        self.sendMessage(token, verbosityThreshold=8)
        self.process.token_state = TokenState.Null

    def requestToken(self):
        self.process.token_state = TokenState.Requested
        printer(4, [self.process.name, "awaits the token"])
        while self.process.token_state == TokenState.Requested:
            if not self.process.alive:
                return
        self.process.token_state = TokenState.SC
        printer(4, [self.process.name, "has the token that it requested"])

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event: Token):
        if event.to_process == self.process.myId:
            self.receiveMessage(event, verbosityThreshold=8)
            if not self.process.alive:
                return
            if self.process.token_state == TokenState.Requested:
                self.process.token_state = TokenState.SC
                return
            if self.process.isSyncing:
                self.process.isSyncing = False
                self.process.nbSync = mod(event.nbSync + 1, Process.nbProcessCreated)
                if self.process.nbSync == 0:
                    self.sendMessage(SyncingMessage(self.process.myId))
            self.releaseToken()

    def doCriticalAction(self, funcToCall: Callable, args: list):
        self.requestToken()
        if self.process.alive:
            funcToCall(*args)
            self.releaseToken()

    def synchronize(self):
        self.process.isSyncing = True
        printer(2, [self.process.myId, "is syncing"])
        while self.process.isSyncing:
            if not self.process.alive:
                return
        while self.nbSync != 0:
            if not self.process.alive:
                return
        printer(2, [self.process.myId, "synced"])

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncingMessage)
    def onSyncing(self, event: SyncingMessage):
        if event.from_process != self.process.myId:
            self.receiveMessage(event)
            self.process.nbSync = 0
