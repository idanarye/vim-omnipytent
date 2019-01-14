from .tasks import Task


class TaskMakerMeta(type):
    def __new__(mcs, name, bases, dct):
        if dct.pop('_is_maker_', False):
            return type.__new__(mcs, name, bases, dct)
        else:
            task_maker, = bases
            return task_maker._make_task(name, dct)


class TaskMaker(TaskMakerMeta('_TaskMakerBaes_', (), dict(_is_maker_=True))):
    _is_maker_ = True
    TaskType = Task

    @classmethod
    def _make_task(cls, name, dct, alias=[]):
        module = dct.pop('__module__', None)
        qualname = dct.pop('__qualname__', None)
        try:
            alias = dct.pop('alias')
        except KeyError:
            pass
        self = cls(**dct)
        self.__name__ = name
        task = self.TaskType(self, alias=alias)
        modified_task = self.modify_task(task)
        if isinstance(modified_task, Task):
            task = Task
        return task

    def __init__(self, **dct):
        self.__dict__.update(dct)

    def __call__(self, ctx):
        pass

    def modify_task(self, task):
        pass
