from threading import Thread
from time import sleep

from Com import Com


class Process(Thread):

    def __init__(self, name, nbProcess):
        Thread.__init__(self)

        self.com = Com(nbProcess)

        self.nbProcess = self.com.getNbProcess()

        self.myId = self.com.getMyId()
        self.name = name

        self.start()

    def run(self):
        loop = 0
        while self.com.alive:
            print(self.name + " Loop: " + str(loop))
            sleep(1)

            if self.myId == 0:
                self.com.sendTo("j'appelle 2 et je te recontacte après", 1)

                self.com.sendToSync(
                    "J'ai laissé un message à 2, je le rappellerai après, on se sychronise tous et on attaque la partie ?",
                    2)
                self.com.recevFromSync(2)

                self.com.sendToSync("2 est OK pour jouer, on se synchronise et c'est parti!", 1)

                self.com.synchronize()

                self.com.requestSC()
                if self.com.mailbox.isEmpty():
                    print("Catched !")
                    self.com.broadcast("J'ai gagné !!!")
                else:
                    msg = self.com.mailbox.getMsg()
                    print(msg.getSender(), "a eu le jeton en premier")
                self.com.releaseSC()

            if self.myId == 1:
                if not self.com.mailbox.isEmpty():
                    self.com.mailbox.getMsg()
                    self.com.recevFromSync(0)

                    self.com.synchronize()

                    self.com.requestSC()
                    if self.com.mailbox.isEmpty():
                        print("Catched !")
                        self.com.broadcast("J'ai gagné !!!")
                    else:
                        msg = self.com.mailbox.getMsg()
                        print(msg.getSender(), "a eu le jeton en premier")
                    self.com.releaseSC()

            if self.myId == 2:
                self.com.recevFromSync(0)
                self.com.sendToSync("OK", 0)

                self.com.synchronize()

                self.com.requestSC()
                if self.com.mailbox.isEmpty():
                    print("Catched !")
                    self.com.broadcast("J'ai gagné !!!")
                else:
                    msg = self.com.mailbox.getMsg()
                    print(msg.getSender(), "a eu le jeton en premier")
                self.com.releaseSC()

            loop += 1
        print(self.name + " stopped")

    def stop(self):
        self.com.stop()
        self.join()
