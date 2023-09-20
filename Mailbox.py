class Mailbox:
    def __init__(self):
        self.messages = []

    def isEmpty(self):
        return len(self.messages) == 0

    def addMessage(self, msg):
        self.messages.append(msg)

    def getMsg(self):
        return self.messages.pop(0)
