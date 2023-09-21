from Message import Message


class Mailbox:
    """
    Mailbox class

    The mailbox is a FIFO queue of messages to be processed by the process
    """
    def __init__(self):
        self.messages = []

    def isEmpty(self) -> bool:
        """
        Check if the mailbox is empty
        :return: True if the mailbox is empty, False otherwise
        """
        return len(self.messages) == 0

    def addMessage(self, msg: Message):
        """
        Add a message to the mailbox
        :param msg: Message to add
        :return: None
        """
        self.messages.append(msg)

    def getMsg(self) -> Message:
        """
        Get the first message of the mailbox
        :return: The first message of the mailbox
        """
        return self.messages.pop(0)
