
from .tasks import Task


def task(*args, **kwargs):
    if len(kwargs) == 0 and len(args) == 1 and args[0].__class__ == task.__class__:
        return Task(args[0])

    def wrapper(func):
        result = Task(func)

        result.send_context = kwargs.get('send_context', False)

        for arg in args:
            if isinstance(arg, Task) or isinstance(arg, str):
                result.dependencies.append(arg)

        return result

    return wrapper


def ctask(*args, **kwargs):
    if len(kwargs) == 0 and len(args) == 1 and args[0].__class__ == task.__class__:
        result = Task(args[0])
        result.send_context = True
        return result
    else:
        return task(*args, send_context=True, **kwargs)

