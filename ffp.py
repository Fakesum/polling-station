# Import with __ at the start to denote internals
# threading for func_timeout and general typing
import threading as __threading
import typing as __typing

T = __typing.TypeVar("T")

def __timeit(f: __typing.Callable[[__typing.Any], T]) -> tuple(T, float):
    """Time the execution of a function and return the result of the
    function and the time taken.

    Args:
        f (__typing.Callable[[__typing.Any], T]): A Function with return type T

    Returns:
        tuple(T, float): a tuple containg the return value of the function and the
        time it took to execute.
    """
    import time
    st: float = time.time()
    res: T = f()
    et: float = time.time() - st
    return (res,et)

def __xor(*orands) -> bool:
    """XOR Gate with truth table(for two imputs):
        # 1 1 -> 0
        # 0 1 -> 1
        # 1 0 -> 1
        # 0 0 -> 0
    
    Args: <Any Number of bools>

    Returns:
        bool: Output
    """
    return sum(bool(x) for x in orands) == 1

# A internal None of sorts to diffrentiat the result: None
# and the <no-result given state>
class __NoValSet: pass

# A Stoppable thread with a return val
class ThreadWithReturn(__threading.Thread):
    def __init__(self, target) -> None:
        super().__init__()
        # daemon just in case
        self.daemon: bool = True

        # need to use globals()["__NoValSet"] since it thinks
        # __NoValSet means _ThreadWithReturn__NoValSet due to private
        # variables
        self.target, self.result = target, globals()["__NoValSet"]
        self.e = None

    def run(self) -> None:
        # self.return here is the part that
        # is accessable for both main thread
        # And Running thread
        try:
            self.result: __typing.Any = self.target()
        except Exception as e:
            self.result = None
            self.e = e

    def is_finished(self) -> None:
        # Check if result is defiend
        return self.result != globals()["__NoValSet"]

    def raise_exception(self) -> None:
        # A very crude way to stop a thread form the outside
        # by raising a SystemExit Exception no matter where it is
        import ctypes
        if ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(SystemExit)) > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)

class FuncTimeout(Exception): pass

def func_timeout(timeout: int | float, func: __typing.Callable, poll_time: float=0.5) -> __typing.Any:
    """function to timout if a function takes more than given amount of time.

    Raises:
        waiter_inst.e: If an Error Occurs while runing the function it will forward it
        to the main thread.
        FuncTimeout: If the function takes more than allocated timeout to exececute then 
        the function thread is termenated and funcTimeout is raised.

    Returns:
        __typing.Any: the return of the function.
    """
    import time

    waiter_inst: ThreadWithReturn = ThreadWithReturn(func)
    waiter_inst.start()
    
    for _ in range(round(timeout//poll_time)):
        if waiter_inst.result != __NoValSet:
            if waiter_inst.e != None:
                raise waiter_inst.e
            return waiter_inst.result
        time.sleep(poll_time)

    waiter_inst.raise_exception()
    raise FuncTimeout("Function(%s) Timed out" % func.__name__)

def poll(
        timeout: int | float | None, 
        func: __typing.Callable,
        expected_outcome: __typing.Type | __typing.Any=__NoValSet,
        validity_determiner: __typing.Type | __typing.Callable = __NoValSet,
        per_func_poll_time: int | float = 0.5,
        return_val: bool=False,
        per_func_timeout: int | float | None = None,
        poll: int | float | None= 0.5,
        error_logging: bool = True,
        error_logger: __typing.Callable = print,
        true_timing: bool=False,
        fast: bool = False,
        generator: bool = False,
        on_failer: __typing.Callable | __typing.Type = __NoValSet
    ) -> bool | __typing.Any:
    """This function does too many things to explain, Just understand that this is
        By far the best method of adding reliability and speed to the code. specially
        for selenium for which this was created. use @wrap_poll decorator if you want
        something much netter.

    Args:
        timeout (int | float | None): The Timeout of the function
        func (__typing.Callable): The function that is to be repeated
        expected_outcome (__typing.Type | __typing.Any, optional): the expected outcome if there is one. Defaults to __NoValSet.

        validity_determiner(__typing.Type | __typing.Callable, optional): funciton, if specified the output of the given function will be run 
        throw the validity function specified in order to verify that the result was valid. The validity function must return either True or False 
        for  valid and invalid result respectivly.

        per_func_poll_time (int | float, optional): if per_func_timeout is set then this will check on if the function has
                                                    completed every this many seconds. Defaults to 0.5.
        return_val (bool, optional): if this is set then the function will return the result of the function. Defaults to 
                                     False.
        per_func_timeout (int | float | None, optional): this will run the function in a func_timeout in order to not allow
                                                         Each individual function call to not exceed the given amount of time
                                                         . Defaults to None.
        poll (int | float | None, optional): The amount of time between each attempt. Defaults to 0.5.
        error_logging (bool, optional): this will print the error if the passed function has raised one. Defaults to True.
        error_logger (__typing.Callable, optional): The function which is to be run to log the error. Defaults to print.
        true_timing (bool, optional): by defualt it does not take the time taken by the function into a account when
                                      calculating timeout, this uses func_timeout in order to more accurately measure
                                      that. Defaults to False.
        fast (bool, optional): the poll function works in O(1) time with a constant overhead, this will reduce that from
                               ~8 * 10^-5 seconds to ~4 * 10^-7. this is such a small difference that it only matters when
                               dealing with tiny passed functions. **the poll function will Not check for any mistakes if this
                               is True**. Defaults to False.
        generator (bool, optional): if the passed function yields then it might be a good idea to pass this argument as True
                                    since it pre-gens the function and checks for Exceptions before returning the returned val
                                    Defaults to False.
        on_failer (__typing.Callbale): If defined, it runs when the function incounters a problem. Defaults to (lambda: __NoValSet)

    Raises:
        SyntaxError: Timout Must be higher than poll
        SyntaxError: Only Provide one return_val or expected_outcome
        SyntaxError: The Timeout cannot be None when true_timing is specified
        SyntaxError: The per_func_timeout cannot be specified with the true_timing argument.

    Returns:
        bool | __typing.Any: either return False if failed, True if expected outcome or the return value if the return_val argument.
    """

    if not fast:
        # if the poll and timrout are specified check that the timeout is more than the poll
        # time otherwise it will wait for more than the timeout allows for
        if (poll != None) and (timeout != None) and (timeout < poll): raise SyntaxError("Timout Must be higher than poll")

        # Check that only one of the expected_outcome or return_val is provided
        if not (__xor((expected_outcome != __NoValSet), return_val, (validity_determiner != __NoValSet))): raise SyntaxError("Only Provide ONLY one return_val or expected_outcome or validity_determiner")
        
        # The True timing and pre_func_timeout cannot be given at once
        if (true_timing and (timeout == None)): raise SyntaxError("The Timeout cannot be None when true_timing is specified")
        if (true_timing and per_func_timeout != None): raise SyntaxError("The per_func_timeout cannot be specified with the true_timing argument.")
    """
    if timeout is None run forever, else if poll is None then run for timeout, if both
    are given the run for timeout//poll
    """
    import time, itertools
    for _ in ((range(int(timeout//poll)) if (poll != None) else range(timeout)) if (timeout != None) else (itertools.count(start=1))):
        try:
            if true_timing:
                res = __timeit(lambda: (func_timeout(timeout, func, per_func_poll_time)))
                timeout -= res[1]
                res = res[0]
            elif per_func_timeout != None:
                res = func_timeout(per_func_timeout, func, per_func_poll_time)
            else:
                res = func()
            
            if generator:
                res = [i for i in res]

            if (((res != expected_outcome)) if (validity_determiner == __NoValSet) else (validity_determiner(res) != True)) if (not return_val) else False:
                raise RuntimeError("Unexpected OutCome")
            else:
                return (res if (return_val or validity_determiner != __NoValSet) else True)
            
        except Exception as e:
            if error_logging:
                error_logger(f"Error: {type(e).__name__} was Triggered, Args: {e.args}")
            if (true_timing) and (isinstance(e,FuncTimeout)):
                break
            if on_failer() == True: break
            (time.sleep(poll) if poll != None else None)
    return False

def wrap_func_timeout(timeout: int | float, poll: int | float=0.5) -> __typing.Callable:
    def decorator(f) -> __typing.Callable:
        def wrapper(*args, **kwargs):
            return func_timeout(timeout, (lambda: f(*args, **kwargs)), poll)
        return wrapper
    return decorator

def wrap_poll( timeout: int | float | None, *pargs, **pkwargs ) -> __typing.Callable: 
    def decorator(f) -> __typing.Callable:
        def wrapper(*args, **kwargs) -> (bool | __typing.Any):
            return poll(timeout,(lambda: f(*args, **kwargs)),*pargs,**pkwargs)
        return wrapper
    return decorator