from threading import Thread
import typing

class EscapableAndReturningThread(Thread):
    
    class NoValSet: pass

    def __init__(self, target, args = [], kwargs = {}) -> None:
        super().__init__()
        # daemon just in case
        self.daemon: bool = True

        # target and result to be given
        self.target, self.result = target, self.NoValSet
        self.args, self.kwargs = args, kwargs
        self.e = None

    def run(self) -> None:
        # self.return here is the part that
        # is accessable for both main thread
        # And Running thread
        try:
            self.result: typing.Any = self.target(*self.args, *self.kwargs)
        except Exception as e:
            self.result = None
            self.e = e

    def is_finished(self) -> bool:
        # Check if result is defiend
        return self.result != self.NoValSet
    
    def has_exception(self) -> bool:
        # Check if a error occured
        return self.e != None

    def raise_exception(self) -> None:
        # A very crude way to stop a thread form the outside
        # by raising a SystemExit Exception no matter where it is
        import ctypes
        if ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(SystemExit)) > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)