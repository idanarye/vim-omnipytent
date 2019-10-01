import inspect
import os
from collections import OrderedDict
import re

from .util import flatten_iterator

_getargspec = getattr(inspect, 'getfullargspec', inspect.getargspec)


class TaskMeta(type):
    def __new__(mcs, name, bases, dct):
        dct.setdefault('_CONCRETE_', True)
        dct.setdefault('dependencies', [])
        dct.setdefault('completers', [])
        dct.setdefault('alias', [])

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

        cls.__handle_special_args(argspec)

        cls._cls_init_()
        return cls

    @property
    def aliases(cls):
        try:
            alias = cls.alias
        except AttributeError:
            return []
        else:
            if isinstance(alias, str):
                return alias.split()
            else:
                return list(alias)

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
        return isinstance(default, type) and issubclass(default, Task)


class Task(object):
    _CONCRETE_ = False

    @classmethod
    def _cls_init_(cls):
        """Override to initialize the task class"""

    @classmethod
    def get_definition_location(cls):
        code = cls._func_.__code__
        return code.co_filename, code.co_firstlineno

    def all_dependencies(self):
        for dependency in self.dependencies:
            yield dependency
        for dependency in self._special_args.values():
            yield dependency

    @classmethod
    def add_alias(cls, *aliases):
        if isinstance(cls.alias, str):
            cls.alias = cls.alias.split()
        elif not isinstance(cls.alias, list):
            cls.alias = list(cls.alias)
        cls.alias.extend(
            alias
            for joind_alias in aliases
            for alias in joind_alias.split())

    @classmethod
    def subtask(cls, name, alias=None, doc=None):
        def inner(func):
            cls._subtasks[name] = type(Task)(
                cls._format_subtask_full_name(cls.__name__, name),
                (Task,),
                dict(
                    _func_=func,
                    # NOTE: If we had [] as default argument, appending aliases
                    # to it would be global (for all tasks)...
                    alias=alias or [],
                    __doc__=doc,
                ))

        if isinstance(name, str):
            return inner
        elif callable(name):
            func = name
            name = func.__name__
            inner(func)
        else:
            raise TypeError('Bad paramter for subtask %r' % (name,))


    @classmethod
    def add_subtask_alias(cls, subtask_name, *aliases):
        try:
            subtask = cls._subtasks[subtask_name]
        except KeyError:
            raise Exception('%r has no subtask named %r' % (cls.__name__, subtask_name))
        else:
            subtask.add_alias(*aliases)


    def completions(self, ctx):
        result = set()
        for completer in self.completers:
            result.update(completer(ctx))
        return sorted(result)

    @classmethod
    def complete(cls, func):
        def completer(ctx):
            result = func(ctx)
            result = (item for item in result if item.startswith(ctx.arg_prefix))
            return result
        cls.completers.append(completer)

    __STARTS_WITH_WORD_CHARACTER_PATTERN = re.compile(r'^\w')

    @classmethod
    def _format_subtask_full_name(ctx, prefix, name):
        if not prefix:
            return name
        elif ctx.__STARTS_WITH_WORD_CHARACTER_PATTERN.match(name):
            return '%s.%s' % (prefix, name)
        else:
            return '%s%s' % (prefix, name)

    @classmethod
    def gen_self_with_subtasks(cls, ident):
        yield ident, cls
        for subtask_ident, subtask in cls._subtasks.items():
            subtask_ident = cls._format_subtask_full_name(ident, subtask_ident)
            for pair in subtask.gen_self_with_subtasks(ident=subtask_ident):
                yield pair

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

    @property
    def _doc_(self):
        if type(self).__doc__ is not None:
            return type(self).__doc__
        else:
            return self._func_.__doc__

    def _func_(self):
        pass

    def gen_doc(self):
        result = []

        if False:  # TODO: Enable when allowing arguments in selection UI
            def args():
                for arg in self._task_args:
                    if arg in self._task_arg_defaults:
                        yield '[%s]' % arg
                    else:
                        yield arg
                if self._task_varargs:
                    yield '[%s...]' % self._task_varargs
            args = ' '.join(args())
            if args:
                result.append('Arguments: ' + args)

        deps = ', '.join(d.__name__ for d in self.all_dependencies())
        if deps:
            result.append('Dependencies: ' + deps)

        result.append(self._doc_)
        return '\n\n'.join(str(line) for line in result if line is not None)

    def __repr__(self):
        return '<Task: %s>' % self.__name__

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


Task = TaskMeta(Task.__name__, Task.__bases__, dict(Task.__dict__))


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
