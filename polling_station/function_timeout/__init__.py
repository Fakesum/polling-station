import typing
import time
from .thread import EscapableAndReturningThread

T = typing.TypeVar("T")

class FunctionTimeout: pass

def func_timeout(
        function: typing.Callable[..., T],
        timeout: int | float,
        step: int | float | None = 0.5,
        stepbefore: bool = True
    ) -> T:

    thread = EscapableAndReturningThread(function)
    thread.start()

    timer = time.time()

    while True:
        if thread.is_finished():
            return thread.result

        if thread.has_exception():
            raise Exception(f"In Function: {function.__name__} "+str(thread.e))
        
        if (stepbefore) and step: time.sleep(step)

        timeout -= (timer - time.time())
        if (timeout <= 0):
            thread.raise_exception()
            raise FunctionTimeout(f"Function: {function.__name__} Timed out.")
        
        if (not (stepbefore)) and step: time.sleep(step)