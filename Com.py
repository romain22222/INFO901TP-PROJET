import random
from time import sleep

from Mailbox import Mailbox

from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode

from Message import *
from Utils import printer, mod


class Com:
    def __init__(self, nbProcess):
        self.nbProcess = nbProcess
        self.myId = None
        self.listInitId = []

        PyBus.Instance().register(self, self)
        sleep(1)

        self.mailbox = Mailbox()
        self.clock = 0

        self.nbSync = 0
        self.isSyncing = False

        self.tokenState = TokenState.Null

        self.isBlocked = False
        self.awaitingFrom = []
        self.recvObj = None

        self.alive = True
        if self.getMyId() == self.nbProcess - 1:
            self.releaseSC()

    def getNbProcess(self):
        return self.nbProcess

    def getMyId(self):
        if self.myId is None:
            self.initMyId()
        return self.myId

    def initMyId(self):
        # 1 : Get a random id between 0 and 10000 * (nbProcess - 1)
        # 2 : Send to all process a message with this id
        # 3 : Wait for a given time to receive all ids
        # 4 : if there is a conflict, go to 1
        # 5 : else, sort the ids and take the index of the id in the list as the id of the process
        randomNb = random.randint(0, 10000 * (self.nbProcess - 1))
        printer(32, ["randomNb:", randomNb])
        self.sendMessage(InitIdMessage(randomNb))
        sleep(2)
        if len(set(self.listInitId)) != self.nbProcess:
            self.listInitId = []
            return self.initMyId()
        self.listInitId.sort()
        self.myId = self.listInitId.index(randomNb)
        printer(32, ["myId:", self.myId, "myRandomNb:", randomNb, "listInitId:", self.listInitId])

    @subscribe(threadMode=Mode.PARALLEL, onEvent=InitIdMessage)
    def onReceiveInitIdMessage(self, message: InitIdMessage):
        self.listInitId.append(message.getObject())

    def sendMessage(self, message: Message, verbosityThreshold=1):
        if not message.is_system:
            self.inc_clock()
            message.horloge = self.clock
        printer(verbosityThreshold, [message.toString()])
        PyBus.Instance().post(message)

    def sendTo(self, obj: any, com_to: int):
        self.sendMessage(MessageTo(obj, self.getMyId(), com_to))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, message: MessageTo):
        if message.to_id != self.getMyId():
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        printer(1, [self.getMyId(), "received:", message.getObject()])
        self.mailbox.addMessage(message)

    def sendToSync(self, obj: any, com_to: int):
        self.awaitingFrom = com_to
        self.sendMessage(MessageSync(obj, self.getMyId(), com_to))
        while com_to == self.awaitingFrom:
            if not self.alive:
                return
        printer(1, [self.getMyId(), "sent:", obj, "to", com_to])

    def recevFromSync(self, com_from: int) -> any:
        self.awaitingFrom = com_from
        while com_from == self.awaitingFrom:
            if not self.alive:
                return
        ret = self.recvObj
        printer(1, [self.getMyId(), "received:", ret, "from", com_from])
        self.recvObj = None
        return ret

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageSync)
    def onReceiveSync(self, message: MessageSync):
        if message.to_id != self.getMyId():
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        while message.from_id != self.awaitingFrom:
            if not self.alive:
                return
        self.awaitingFrom = -1
        self.recvObj = message.getObject()
        self.sendMessage(AcknowledgementMessage(self.getMyId(), message.from_id))

    def broadcastSync(self, obj: any, com_from: int):
        if self.getMyId() == com_from:
            for i in range(self.nbProcess):
                if i != self.getMyId():
                    self.sendToSync(obj, i)
        else:
            return self.recevFromSync(com_from)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=AcknowledgementMessage)
    def onAckSync(self, event: AcknowledgementMessage):
        if self.getMyId() == event.to_id:
            self.awaitingFrom = -1

    def synchronize(self):
        self.isSyncing = True
        printer(1, [self.getMyId(), "is syncing"])
        while self.isSyncing:
            printer(2, [self.getMyId(), "is syncing in"])
            if not self.alive:
                return
        while self.nbSync != 0:
            printer(2, [self.getMyId(), "is syncing out"])
            if not self.alive:
                return
        printer(2, [self.getMyId(), "synced"])

    def requestSC(self):
        self.tokenState = TokenState.Requested
        printer(4, [self.getMyId(), "awaits the token"])
        while self.tokenState == TokenState.Requested:
            if not self.alive:
                return
        printer(4, [self.getMyId(), "has the token that it requested"])

    def broadcast(self, obj: any):
        self.sendMessage(BroadcastMessage(obj, self.getMyId()))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, message: BroadcastMessage):
        if message.from_id == self.getMyId():
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        printer(1, [self.getMyId(), "received:", message.getObject()])
        self.mailbox.addMessage(message)

    def releaseSC(self):
        printer(8, [self.getMyId(), "release token to", mod(self.getMyId() + 1, self.nbProcess)])
        if self.tokenState == TokenState.SC:
            self.tokenState = TokenState.Release
        self.sendMessage(Token(self.getMyId(), mod(self.getMyId() + 1, self.nbProcess), self.nbSync), verbosityThreshold=8)
        self.tokenState = TokenState.Null

    def inc_clock(self):
        self.clock += 1

    def stop(self):
        self.alive = False

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event: Token):
        if event.to_id != self.getMyId() or not self.alive:
            return
        self.nbSync = event.nbSync
        if self.isSyncing:
            self.isSyncing = False
            self.nbSync = mod(event.nbSync + 1, self.nbProcess)
            if self.nbSync == 0:
                self.sendMessage(SyncingMessage(self.getMyId()))
        if self.tokenState == TokenState.Requested:
            self.tokenState = TokenState.SC
        else:
            self.releaseSC()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncingMessage)
    def onSyncingMessage(self, event: SyncingMessage):
        if event.from_id != self.getMyId():
            self.nbSync = 0
