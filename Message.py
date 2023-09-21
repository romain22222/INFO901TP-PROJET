from enum import Enum


class Message:
    """
    Message class
    """
    def __init__(self, obj: any, is_system=False):
        self.object = obj
        self.is_system = is_system
        self.horloge = None

    def getObject(self):
        return self.object

    def __str__(self) -> str:
        return "sending: " + str(self.object)


class InitIdMessage(Message):
    """
    Message to initialize the id of a process
    """
    def __init__(self, randomNb: int):
        super().__init__(randomNb, True)


class ShareRandomNbListMessage(Message):
    """
    Message to share the list of random numbers
    """
    def __init__(self, listRandomNb: list):
        super().__init__(listRandomNb, True)


class BroadcastMessage(Message):
    """
    Message to broadcast
    """
    def __init__(self, obj: any, from_id: int, is_system=False):
        super().__init__(obj, is_system)
        self.from_id = from_id

    def getSender(self):
        return self.from_id

    def __str__(self) -> str:
        return str(self.from_id) + " broadcasts: " + str(self.object)


class MessageTo(Message):
    """
    Message to send to a specific process
    """
    def __init__(self, obj: any, from_id: int, to_id: int, is_system=False):
        super().__init__(obj, is_system)
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self) -> str:
        return str(self.from_id) + " sends to " + str(self.to_id) + " : " + self.object

    def getSender(self):
        return self.from_id


class Token(MessageTo):
    """
    Token message
    """
    def __init__(self, from_id: int, to_id: int, nbSync: int, tokenId: int):
        super().__init__(None, from_id, to_id, True)
        self.currentTokenId = tokenId
        self.nbSync = nbSync

    def __str__(self) -> str:
        return str(self.from_id) + " sends token to " + str(self.to_id) + " with nbSync: " + str(
            self.nbSync) + " and tokenId: " + str(self.currentTokenId)


class TokenState(Enum):
    """
    Token state : Gives the state of the token for a com
    """
    Null = 1
    Requested = 2
    SC = 3
    Release = 4


class AcknowledgementMessage(MessageTo):
    """
    Acknowledgement message
    """
    def __init__(self, from_id: int, to_id: int):
        super().__init__(None, from_id, to_id, True)

    def __str__(self) -> str:
        return str(self.from_id) + " sends an acknoledgment to " + str(self.to_id)


class MessageToSync(MessageTo):
    """
    Message to send to a specific process, synchroneously
    """
    def __init__(self, obj: any, from_id: int, to_id: int):
        super().__init__(obj, from_id, to_id)

    def __str__(self) -> str:
        return str(self.from_id) + " sends synchroneously to " + str(self.to_id) + " : " + self.object


class HeartbeatMessage(BroadcastMessage):
    """
    Heartbeat message
    """
    def __init__(self, from_id: int):
        super().__init__(None, from_id, True)

    def __str__(self) -> str:
        return str(self.from_id) + " sends a heartbeat"


class StartHeartbeatMessage(MessageTo):
    """
    Message to start the heartbeat of a com
    """
    def __init__(self, from_id: int):
        super().__init__(None, from_id, from_id, True)

    def __str__(self) -> str:
        return str(self.from_id) + " starts its heartbeat"
