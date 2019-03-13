import inspect
import os
from collections import OrderedDict

from .util import flatten_iterator

_getargspec = getattr(inspect, 'getfullargspec', inspect.getargspec)


class TaskMeta(type):
    def __new__(mcs, name, bases, dct):
        dct.setdefault('dependencies', [])
        dct.setdefault('completers', [])

        cls = super(TaskMeta, mcs).__new__(mcs, name, bases, dct)

        cls._subtasks = {}

        # try:
        argspec = _getargspec(cls._func_)
        # except TypeError:
        # argspec = _getargspec(func.__call__)

        cls._task_ctx_arg_name = argspec.args[0] if argspec.args else None
        if getattr(cls._func_, '__self__', None) is None:
            cls._task_args = argspec.args[1:]  # remove `ctx` from the list
        else:
            cls._task_args = argspec.args[2:]  # remove `self`/`ctx` and `ctx` from the list
        if argspec.defaults:
            cls._task_arg_defaults = dict(zip(cls._task_args[-len(argspec.defaults):], argspec.defaults))
        else:
            cls._task_arg_defaults = {}
        cls._task_varargs = argspec.varargs
        cls._special_args = OrderedDict()

        # if not alias:
        cls.aliases = []
        # elif isinstance(alias, str):
        # cls.aliases = alias.split()
        # else:
        # cls.aliases = list(alias)

        cls.__handle_special_args(argspec)

        cls._cls_init_()
        return cls

    def __handle_special_args(self, argspec):
        special_defaults = list(self.__split_special_defaults(argspec))
        if special_defaults:
            special_args = argspec.args[-len(special_defaults):]
            self._special_args.update(zip(special_args, special_defaults))
            assert special_args == self._task_args[-len(special_args):]
            self._task_args = self._task_args[:-len(special_args)]
            for arg in special_args:
                del self._task_arg_defaults[arg]
        if getattr(argspec, 'kwonlydefaults', None):
            for k, v in argspec.kwonlydefaults.items():
                if not self.__is_default_special(v):
                    raise SyntaxError('Non-special argument %s=%s' % (k, v))
                self._special_args[k] = v

    @classmethod
    def __split_special_defaults(cls, argspec):
        if not argspec.defaults:
            return
        found_first_special = False
        for default in argspec.defaults:
            if cls.__is_default_special(default):
                found_first_special = True
                yield default
            elif found_first_special:
                raise SyntaxError('Non-special default %s after special defaults' % (default,))

    @classmethod
    def __is_default_special(cls, default):
        return isinstance(default, type) and issubclass(default, BaseTask)


class BaseTask(object):
    @classmethod
    def _cls_init_(cls):
        pass

    @classmethod
    def _is_concrete_(cls):
        return True

    @classmethod
    def all_dependencies(cls):
        for dependency in cls.dependencies:
            yield dependency
        for dependency in cls._special_args.values():
            yield dependency

    def __init__(self, invocation_context):
        self.invocation_context = invocation_context
        self.dep = DepDataFetcher(self)

    @property
    def __name__(self):
        return type(self).__name__

    def _run_func_as_generator(self, *args, **kwargs):
        result = self._func_(*args, **kwargs)
        if inspect.isgenerator(result):
            result = flatten_iterator(result)
            try:
                yielded = next(result)
                while True:
                    yield yielded
                    yielded = result.send(yielded._returned_value)
            except StopIteration:
                pass

    @property
    def _kwargs_for_func(self):
        kwargs = {}
        for name, task in self._special_args.items():
            kwargs[name] = self.dep._get_by_task(task)
        return kwargs

    def invoke(self, *args):
        if not self.is_main:
            args = ()
        for yielded in self._run_func_as_generator(*args, **self._kwargs_for_func):
            yield yielded

    def _func_(self):
        pass

    def __repr__(self):
        return '<TaskContext: %s>' % self.task.__name__

    @property
    def task_file(self):
        return self.invocation_context.task_file

    @property
    def has_passed_data(self):
        return type(self) in self.invocation_context.dep_data

    @property
    def passed_data(self):
        return self.invocation_context.dep_data[type(self)]

    def pass_data(self, data):
        self.invocation_context.dep_data[type(self)] = data

    @property
    def cache(self):
        return self.task_file.get_task_cache(type(self))

    @property
    def is_main(self):
        return self.invocation_context.main_task == type(self)

    @property
    def task_dir(self):
        return self.task_file.tasks_dir

    proj_dir = task_dir

    @property
    def file_dir(self):
        filename = self.invocation_context.start_buffer.name
        if filename:
            return os.path.dirname(filename)
        else:
            return self.cur_dir

    @property
    def cur_dir(self):
        return self.invocation_context.start_dir


BaseTask = TaskMeta(BaseTask.__name__, BaseTask.__bases__, dict(BaseTask.__dict__))


class DepDataFetcher:
    def __init__(self, task):
        self.__task = task

    def __getattr__(self, name):
        for dependency in self.__task.dependencies:
            if dependency.__name__ == name:
                try:
                    return self.__task.invocation_context.dep_data[dependency]
                except KeyError:
                    raise AttributeError('%s did not pass data' % dependency)
        raise AttributeError('%s has no dependency named "%s"' % (self.__task, name))

    def _get_by_task(self, task):
        # print(self.__task.invocation_context.dep_data)
        return self.__task.invocation_context.dep_data[task]

    def _get_indirect(self, name):
        for task, value in self.__task.invocation_context.dep_data.items():
            if task.__name__ == name:
                return value
        raise KeyError('task %r did not pass data' % (name,))
