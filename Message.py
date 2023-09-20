from enum import Enum


class Message:
    def __init__(self, obj: any, is_system=False):
        self.object = obj
        self.is_system = is_system
        self.horloge = None

    def getObject(self):
        return self.object

    def toString(self) -> str:
        return "sending: " + str(self.object)


class InitIdMessage(Message):
    def __init__(self, randomNb: int):
        super().__init__(randomNb, True)


class ShareRandomNbListMessage(Message):
    def __init__(self, listRandomNb: list):
        super().__init__(listRandomNb, True)


class BroadcastMessage(Message):
    def __init__(self, obj: any, from_id: int, is_system=False):
        super().__init__(obj, is_system)
        self.from_id = from_id

    def getSender(self):
        return self.from_id


class MessageTo(Message):
    def __init__(self, obj: any, from_id: int, to_id: int, is_system=False):
        super().__init__(obj, is_system)
        self.from_id = from_id
        self.to_id = to_id

    def toString(self) -> str:
        return str(self.from_id) + "sends: " + self.object + " to " + str(self.to_id)

    def getSender(self):
        return self.from_id


class Token(MessageTo):
    def __init__(self, from_id: int, to_id: int, nbSync: int):
        super().__init__(None, from_id, to_id, True)
        self.nbSync = nbSync

    def toString(self) -> str:
        return str(self.from_id) + " sends to " + str(self.to_id) + " with nbSync: " + str(self.nbSync)


class TokenState(Enum):
    Null = 1
    Requested = 2
    SC = 3
    Release = 4


class SyncingMessage(BroadcastMessage):
    def __init__(self, from_id: int):
        super().__init__(None, from_id, True)

    def toString(self) -> str:
        return str(self.from_id) + " sends a synchronize message"


class AcknowledgementMessage(MessageTo):
    def __init__(self, from_id: int, to_id: int):
        super().__init__(None, from_id, to_id, True)

    def toString(self) -> str:
        return str(self.from_id) + " sends " + str(self.to_id) + " an ack"


class MessageSync(MessageTo):
    def __init__(self, obj: any, from_id: int, to_id: int):
        super().__init__(obj, from_id, to_id)

    def toString(self) -> str:
        return str(self.from_id) + " sends: " + self.object + " to " + str(self.to_id) + " synchroneously"
