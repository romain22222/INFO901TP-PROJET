from threading import Thread
from time import sleep

from Com import Com
from Utils import printer


class Process(Thread):
    """
    A process

    Example of a process that could use the Com class
    """
    def __init__(self, name, nbProcess):
        Thread.__init__(self)

        self.com = Com(nbProcess)

        self.nbProcess = self.com.getNbProcess()

        self.myId = self.com.getMyId()
        self.name = name

        self.start()

    def criticalAction(self):
        """
        The critical action to do
        :return: None
        """
        if self.com.mailbox.isEmpty():
            printer(self, "Catched !")
            self.com.broadcast("J'ai gagné !!!")
        else:
            printer(self, [self.com.mailbox.getMsg().getSender(), "a eu le jeton en premier"])

    def run(self):
        """
        The main loop of the process
        :return: None
        """
        loop = 0
        while self.com.alive:
            printer(self, [self.name, "Loop:", loop])
            sleep(1)

            if self.myId == 0:
                self.com.sendTo("j'appelle 2 et je te recontacte après", 1)
                self.com.sendToSync("J'ai laissé un message à 2, je le rappellerai après, on se sychronise tous et on attaque la partie ?",2)
                printer(self, self.com.recevFromSync(2))
                self.com.sendToSync("2 est OK pour jouer, on se synchronise et c'est parti!", 1)
                self.com.synchronize()
                self.com.doCriticalAction(self.criticalAction)

            if self.myId == 1:
                if not self.com.mailbox.isEmpty():
                    printer(self, self.com.mailbox.getMsg().getObject())
                    printer(self, self.com.recevFromSync(0))
                    self.com.synchronize()
                    self.criticalAction()

            if self.myId == 2:
                printer(self, self.com.recevFromSync(0))
                self.com.sendToSync("OK", 0)
                self.com.synchronize()
                self.criticalAction()

            loop += 1
        printer(self, [self.name, "stopped"])

    def stop(self):
        """
        Stops the process
        :return: None
        """
        self.com.stop()
        self.join()

    def __str__(self) -> str:
        return f"Process {self.name} (id: {self.myId})"
