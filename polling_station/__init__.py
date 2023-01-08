import time
from .function_timeout import func_timeout, FunctionTimeout

import typing
T = typing.TypeVar("T")

class PollTimeout(Exception): pass

def poll(
        f: typing.Callable[..., T],
        timeout: int | float | None = 15,
        step: int | float | None = 0.5,
        return_val: str = "returnval",
        validation: str = "expected_outcome",
        expected_outcome: typing.Any = ...,
        determiner: typing.Callable = ...,
        error_logging: bool = True,
        error_logger: typing.Callable = print,
        error_handling_type: str = "except_all",
        ignore_errors: list = [],
        on_failer: typing.Callable = ..., 
        step_function: typing.Callable = ...,
        generated: bool = False,
    ) -> T | bool:
    def _error_logger(log):
        if error_logging:
            error_logger(log)

    if error_handling_type == "except_all":
        ignore_errors.append(Exception)
    else:
        ignore_errors.append(FunctionTimeout)
    
    while True:
        try:
            if (timeout == None):
                res = f()
            else:
                st = time.time()
                res = func_timeout(f, timeout, step)
            
            if generated: res = list(res)
            
            return_val = return_val == "returnval"

            if return_val:
                return res
            else:
                if (validation == "determiner"):
                    if (determiner()):
                        return res
                    else:
                        _error_logger(f"""Determiner gave: False. Restarting..""")
                        continue
                else:
                    if res == expected_outcome:
                        return True
                    else:
                        _error_logger(f"""function: {f.__name__} Gave Unexpected Result: {res} the expected outcome is: {expected_outcome}, Restarting..""")
                        continue
            
        except ignore_errors as e:
            if isinstance(e, FunctionTimeout):
                raise PollTimeout(f"function: {f.__name__} Timed out.")
            _error_logger(f"""function: {f.__name__} Gave Error: {e} with Args: {e.args}""")
            if on_failer != ...: on_failer()

            if timeout <= 0:
                raise PollTimeout(f"function {f.__name__} Timed out.")
            
            if step != None:
                if step_function != ...: step_function()
                time.sleep(step)

            if timeout != None:
                timeout -= (time.time() - st)

def poll_decorator(*pargs, **pkwargs):
    def decorator(f):
        def wrapper(*args, **kwargs):
            return poll(lambda: f(*args, **kwargs), *pargs, **pkwargs)
        return wrapper
    return decorator