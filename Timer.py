import threading
import time

"""Genera un Timer que llama a la funcion 'target' cada 'milisec' milisegundos
la funcion no recibe argumentos""" 
class Timer(threading.Thread):
    def __init__(self, milisec, target, args=(), kwargs={}):
        super(Timer, self).__init__(group=None, target=target, name=None, args=(), kwargs={})
        self.daemon=True
        self.milisec = milisec
        self.target = target
        self.started = True
        self.wasstarted = False

    def start(self):
        if not self.wasstarted:
            self.wasstarted = True
            super(Timer, self).start()
        self.started = True
        
    def run(self):
        while True:
            if self.started:
                self.target()
                time.sleep(self.milisec/1000.0)


    def stop(self):
        self.started = False

