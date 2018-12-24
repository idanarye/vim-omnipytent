import types
from functools import wraps

from .tasks import Task, OptionsTask, WindowTask, OptionsTaskMulti


def _fluent(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self is self._orig:
            result = self.__class__()
        else:
            result = self
        func(result, *args, **kwargs)
        return result
    return wrapper


class TaskDeclarator:
    _task_class = Task
    _orig = None

    def __init__(self):
        self._dependencies = []
        self._completers = []
        self._params = {}

    def _dup_if_orig(self):
        if self is self._orig:
            return self.__class__()
        else:
            return self

    def _adjust_task(self, task):
        task.dependencies.extend(self._dependencies)
        task.completers.extend(self._completers)

    def _decorate(self, func):
        result = self._task_class(func, **self._params)
        self._adjust_task(result)
        return result

    @_fluent
    def _call_impl(self, *deps, **kwargs):
        self._dependencies.extend(deps)
        self._params.update(**kwargs)

    @wraps(_call_impl)
    def __call__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and args[0].__class__ == types.FunctionType:
            return self._decorate(args[0])
        return self._call_impl(*args, **kwargs)

    @_fluent
    def complete(self, completer):
        self._completers.append(completer)

    @property
    @_fluent
    def options(self):
        self._task_class = OptionsTask

    @property
    @_fluent
    def options_multi(self):
        self._task_class = OptionsTaskMulti

    @property
    @_fluent
    def window(self):
        self._task_class = WindowTask


task = TaskDeclarator()
TaskDeclarator._orig = task

