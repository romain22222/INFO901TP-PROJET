import random
from time import sleep
from typing import Callable, List

from Mailbox import Mailbox

from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode

from Message import *
from Utils import printer, mod, VerbosityType


class Com:
    """
    The communication class

    Allow processes to communicate with each other
    """
    def __init__(self, nbProcess):
        self.nbProcess = nbProcess
        self.myId = None
        self.listInitId = []

        self.aliveProcesses = []
        self.maybeAliveProcesses = []
        self.beatCheck = None

        PyBus.Instance().register(self, self)
        sleep(1)

        self.mailbox = Mailbox()
        self.clock = 0

        self.nbSync = 0
        self.isSyncing = False

        self.tokenState = TokenState.Null
        self.currentTokenId = None

        self.isBlocked = False
        self.awaitingFrom = []
        self.recvObj = None

        self.alive = True
        if self.getMyId() == self.nbProcess - 1:
            self.currentTokenId = random.randint(0, 10000 * (self.nbProcess - 1))
            self.sendToken()
        self.startHeartbeat()

    def getNbProcess(self) -> int:
        """
        Get the number of process
        :return: the number of process
        """
        return self.nbProcess

    def getMyId(self) -> int:
        """
        Get the id of the process
        :return: the id of the process
        """
        if self.myId is None:
            self.initMyId()
        return self.myId

    def initMyId(self):
        """
        Initialize the id of the process
        :return: None
        """
        # 1 : Get a random id between 0 and 10000 * (nbProcess - 1)
        # 2 : Send to all process a message with this id
        # 3 : Wait for a given time to receive all ids
        # 4 : if there is a conflict, restart from 1
        # 5 : else, sort the ids and take the index of the id in the list as the id of the process
        randomNb = random.randint(0, 10000 * (self.nbProcess - 1))
        printer(self, ["My random id is:", randomNb], VerbosityType.INIT_ID)
        self.sendMessage(InitIdMessage(randomNb), VerbosityType.INIT_ID)
        sleep(2)
        if len(set(self.listInitId)) != self.nbProcess:
            printer(self, "Conflict, retrying", VerbosityType.INIT_ID)
            self.listInitId = []
            return self.initMyId()
        self.listInitId.sort()
        self.myId = self.listInitId.index(randomNb)
        printer(self, ["My id is :", self.myId, "and my list is :", self.listInitId, "and my random is :", randomNb], VerbosityType.INIT_ID)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=InitIdMessage)
    def onReceiveInitIdMessage(self, message: InitIdMessage):
        """
        Receive an InitIdMessage
        :param message: the InitIdMessage received
        :return: None
        """
        printer(self, ["Received init id message with random equal to", message.getObject()], VerbosityType.INIT_ID)
        self.listInitId.append(message.getObject())

    def sendMessage(self, message: Message, verbosityThreshold=VerbosityType.USER_MESSAGES):
        """
        Send a message to the bus
        :param message: message to send
        :param verbosityThreshold: the verbosity threshold
        :return: None
        """
        if not message.is_system:
            self.incClock()
            message.horloge = self.clock
        printer(self, message, verbosityThreshold)
        PyBus.Instance().post(message)

    def sendTo(self, obj: any, com_to: int):
        """
        Send an object to a process
        :param obj: object to send
        :param com_to: id of the process to send the object
        :return: None
        """
        self.sendMessage(MessageTo(obj, self.getMyId(), com_to))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, message: MessageTo):
        """
        Receive a MessageTo
        :param message: the MessageTo received
        :return: None
        """
        if message.to_id != self.getMyId() or type(message) in [MessageToSync, Token, AcknowledgementMessage]:
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        printer(self, ["Received MessageTo from", message.from_id, ":", message.getObject()], VerbosityType.USER_MESSAGES)
        self.mailbox.addMessage(message)

    def sendToSync(self, obj: any, com_to: int, verbosityThreshold=VerbosityType.USER_MESSAGES):
        """
        Send an object to a process synchroneously
        :param obj: object to send
        :param com_to: id of the process to send the object
        :param verbosityThreshold: the verbosity threshold
        :return: None
        """
        self.awaitingFrom = com_to
        self.sendMessage(MessageToSync(obj, self.getMyId(), com_to), verbosityThreshold)
        while com_to == self.awaitingFrom:
            if not self.alive:
                return

    def recevFromSync(self, com_from: int) -> any:
        """
        Receive an object from a process synchroneously
        :param com_from: id of the process to receive the object
        :return: the object received
        """
        self.awaitingFrom = com_from
        while com_from == self.awaitingFrom:
            if not self.alive:
                return
        ret = self.recvObj
        self.recvObj = None
        return ret

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageToSync)
    def onReceiveSync(self, message: MessageToSync):
        """
        Receive a MessageToSync
        :param message: the MessageToSync received
        :return: None
        """
        if message.to_id != self.getMyId():
            return
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        while message.from_id != self.awaitingFrom:
            if not self.alive:
                return
        self.awaitingFrom = -1
        self.recvObj = message.getObject()
        self.sendMessage(AcknowledgementMessage(self.getMyId(), message.from_id), VerbosityType.ACKNOWLEDGEMENT)

    def broadcastSync(self, com_from: int, obj: any = None) -> any:
        """
        Broadcast an object to all process synchroneously
        :param obj: object to broadcast (not used if the process is the initiator)
        :param com_from: id of the process to broadcast the object from
        :return: None
        """
        if self.getMyId() == com_from:
            printer(self, ["Broadcasting synchroneously", obj], VerbosityType.USER_MESSAGES)
            for i in range(self.nbProcess):
                if i != self.getMyId():
                    self.sendToSync(obj, i, 99)
        else:
            return self.recevFromSync(com_from)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=AcknowledgementMessage)
    def onAckSync(self, event: AcknowledgementMessage):
        """
        Receive an AcknowledgementMessage
        :param event: the AcknowledgementMessage received
        :return: None
        """
        if self.getMyId() == event.to_id:
            printer(self, ["Received AcknowledgementMessage from", event.from_id], VerbosityType.ACKNOWLEDGEMENT)
            self.awaitingFrom = -1

    def synchronize(self):
        """
        Synchronize the processes
        :return: None
        """
        self.isSyncing = True
        printer(self, "Synchronizing", VerbosityType.SYNCHRONISATION)
        while self.isSyncing:
            sleep(0.1)
            printer(self, "Synchronizing in", VerbosityType.SYNCHRONISATION)
            if not self.alive:
                return
        while self.nbSync != 0:
            sleep(0.1)
            printer(self, "Synchronizing out", VerbosityType.SYNCHRONISATION)
            if not self.alive:
                return
        printer(self, "Synchronized", VerbosityType.SYNCHRONISATION)

    def requestSC(self):
        """
        Request the critical section
        :return: None
        """
        printer(self, "Requesting SC", VerbosityType.CRITICAL_SECTION)
        self.tokenState = TokenState.Requested
        while self.tokenState == TokenState.Requested:
            if not self.alive:
                return
        printer(self, "Received SC", VerbosityType.CRITICAL_SECTION)

    def broadcast(self, obj: any):
        """
        Broadcast an object to all process
        :param obj: object to broadcast
        :return: None
        """
        self.sendMessage(BroadcastMessage(obj, self.getMyId()))

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcast(self, message: BroadcastMessage):
        """
        Receive a BroadcastMessage
        :param message: the BroadcastMessage received
        :return: None
        """
        if message.from_id == self.getMyId() or type(message) in [HeartbeatMessage]:
            return
        printer(self, ["Received broadcasted message from", message.from_id, ":", message.getObject()], VerbosityType.USER_MESSAGES)
        if not message.is_system:
            self.clock = max(self.clock, message.horloge) + 1
        self.mailbox.addMessage(message)

    def sendToken(self):
        """
        Send the token to the next process
        :return: None
        """
        if self.currentTokenId is None:
            return
        sleep(0.1)
        self.sendMessage(Token(self.getMyId(), mod(self.getMyId() + 1, self.nbProcess), self.nbSync, self.currentTokenId), VerbosityType.TOKEN)
        self.currentTokenId = None

    def releaseSC(self):
        """
        Release the critical section
        :return: None
        """
        printer(self, "Releasing SC", VerbosityType.CRITICAL_SECTION)
        if self.tokenState == TokenState.SC:
            self.tokenState = TokenState.Release
        self.sendToken()
        self.tokenState = TokenState.Null
        printer(self, "Released SC", VerbosityType.CRITICAL_SECTION)

    def incClock(self):
        """
        Increment the clock
        :return: None
        """
        self.clock += 1

    def getClock(self) -> int:
        """
        Get the clock
        :return: the clock
        """
        return self.clock

    def stop(self):
        """
        Stop the process
        :return: None
        """
        self.alive = False

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onToken(self, event: Token):
        """
        Receive a Token
        :param event: the Token received
        :return: None
        """
        if event.to_id != self.getMyId() or not self.alive:
            return
        printer(self, ["Received token from", event.from_id], VerbosityType.TOKEN)
        self.currentTokenId = event.currentTokenId
        self.nbSync = mod(event.nbSync + int(self.isSyncing), self.nbProcess)
        self.isSyncing = False
        if self.tokenState == TokenState.Requested:
            self.tokenState = TokenState.SC
        else:
            self.sendToken()

    def doCriticalAction(self, funcToCall: Callable, *args: List[any]) -> any:
        """
        Do a critical action
        :param funcToCall: critical function to call
        :param args: arguments of the function to call
        :return: the return of the function
        """
        self.requestSC()
        ret = None
        if self.alive:
            if args is None:
                ret = funcToCall()
            else:
                ret = funcToCall(*args)
            self.releaseSC()
        return ret

    def startHeartbeat(self):
        """
        Start the heartbeat of the com
        :return: None
        """
        self.sendMessage(StartHeartbeatMessage(self.getMyId()), VerbosityType.HEARTBEAT)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=StartHeartbeatMessage)
    def onStartHeartbeat(self, event: StartHeartbeatMessage):
        """
        Receive a StartHeartbeatMessage
        :param event: the StartHeartbeatMessage received
        :return: None
        """
        if event.from_id != self.getMyId():
            return
        self.heartbeat()

    def heartbeat(self):
        """
        Do the heartbeat
        :return: None
        """
        printer(self, "Starting heartbeat", VerbosityType.HEARTBEAT)
        while self.alive:
            self.sendMessage(HeartbeatMessage(self.getMyId()), VerbosityType.HEARTBEAT)
            sleep(0.1)

            self.beatCheck = True
            printer(self, "Checking heartbeat", VerbosityType.HEARTBEAT)
            printer(self, ["Alive processes", self.aliveProcesses], VerbosityType.HEARTBEAT)
            printer(self, ["Dead processes", self.maybeAliveProcesses], VerbosityType.HEARTBEAT)
            tmpMaybeAliveProcesses = [idMaybeDead for idMaybeDead in range(self.nbProcess) if idMaybeDead != self.getMyId() and idMaybeDead not in self.aliveProcesses]
            printer(self, ["Maybe alive processes", tmpMaybeAliveProcesses], VerbosityType.HEARTBEAT)
            self.aliveProcesses = []
            for idDeadProcess in self.maybeAliveProcesses:
                if idDeadProcess < self.getMyId():
                    self.myId -= 1
                    printer(self, ["My id changed from ", self.getMyId()+1, "to", self.getMyId()], VerbosityType.HEARTBEAT)
                tmpMaybeAliveProcesses = [(idMaybeDead - 1 if idMaybeDead > idDeadProcess else idMaybeDead) for idMaybeDead in tmpMaybeAliveProcesses]
                self.nbProcess -= 1
            self.maybeAliveProcesses = tmpMaybeAliveProcesses
            printer(self, "Heartbeat Checked", VerbosityType.HEARTBEAT)
            self.beatCheck = False

    @subscribe(threadMode=Mode.PARALLEL, onEvent=HeartbeatMessage)
    def onHeartbeat(self, event: HeartbeatMessage):
        """
        Receive a HeartbeatMessage
        :param event: the HeartbeatMessage received
        :return: None
        """
        while self.beatCheck:
            pass
        if event.from_id == self.getMyId():
            return
        printer(self, ["Received heartbeat from", event.from_id], VerbosityType.HEARTBEAT)
        if event.from_id in self.maybeAliveProcesses:
            self.maybeAliveProcesses.remove(event.from_id)
        if event.from_id not in self.aliveProcesses:
            self.aliveProcesses.append(event.from_id)

    def __str__(self) -> str:
        return f"Com {self.myId} / clock : {self.clock} / nbAwaitingMessages : {len(self.mailbox.messages)} / tokenState : {self.tokenState} / isSyncing : {self.isSyncing} / isAlive : {self.alive} / isBlocked : {self.isBlocked} / awaitingFrom : {self.awaitingFrom} / listInitId : {self.listInitId}"
