import time
from .function_timeout import func_timeout, FunctionTimeout

import typing
T = typing.TypeVar("T")

class PollTimeout(Exception): pass

def poll(
        f: typing.Callable[..., T],
        args: list = [],
        kwargs: dict = {},
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
    class PollRestart(Exception): pass
    def _error_logger(*args):
        log = " ".join(args)
        if error_logging:
            error_logger(log)

    if error_handling_type == "except_all":
        ignore_errors.append(Exception)
    else:
        ignore_errors.extend([FunctionTimeout, PollRestart])
    
    while True:
        try:
            if (timeout == None):
                res = f(*args, **kwargs)
            else:
                st = time.time()
                res = func_timeout(f, timeout, args, kwargs, step)
            
            if generated: res = list(res)
            
            return_val = return_val == "returnval"

            if return_val:
                return res
            else:
                if (validation == "determiner"):
                    if (determiner(res)):
                        return res
                    else:
                        raise PollRestart("Determiner Returned False")
                else:
                    if res == expected_outcome:
                        return True
                    else:
                        raise PollRestart(f"""function Gave Unexpected Result: {res} the expected outcome is: {expected_outcome}, Restarting..""")
            
        except tuple(ignore_errors) as e:
            if isinstance(e, FunctionTimeout):
                raise PollTimeout(f"function: {f.__name__} Timed out.")
            
            import traceback
            _error_logger(f"""function: {f.__name__} Gave Error: """, *traceback.format_exception(type(e), e, e.__traceback__))

            if on_failer != ...: on_failer()

            if timeout and (timeout <= 0):
                raise PollTimeout(f"function {f.__name__} Timed out.")
            
            if step != None:
                if step_function != ...: step_function()
                time.sleep(step)

            if timeout != None:
                timeout -= (time.time() - st)

def poll_decorator(
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
    ) -> typing.Callable:
    def decorator(f: typing.Callable) -> typing.Callable:
        def wrapper(*args, **kwargs):
            return poll(
                f,
                args,
                kwargs,
                timeout,
                step,
                return_val,
                validation,
                expected_outcome,
                determiner,
                error_logging,
                error_logger,
                error_handling_type,
                ignore_errors,
                on_failer,
                step_function,
                generated
            )
        return wrapper
    return decorator