import abc

from .tasks import Task


def _fluent(func):
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

    def _dup_if_orig(self):
        if self is self._orig:
            return self.__class__()
        else:
            return self

    def _adjust_task(self, task):
        task.dependencies.extend(self._dependencies)

    def _decorate(self, func):
        result = self._task_class(func)
        self._adjust_task(result)
        return result

    def __call__(self, *args):
        if len(args) == 1 and args[0].__class__ == abc.types.FunctionType:
            return self._decorate(args[0])
        return self._deps(*args)

    @_fluent
    def _deps(self, *deps):
        self._dependencies.extend(deps)


task = TaskDeclarator()
TaskDeclarator._orig = task

