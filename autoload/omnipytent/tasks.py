import abc
from collections import OrderedDict

from context import InvocationContext
from util import input_list


class Task:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.dependencies = []

    def invoke(self, ctx, *args):
        raise NotImplementedError()

    def __repr__(self):
        return '<Task: %s>' % self.name

    @classmethod
    def _dsl(cls, *args):
        if len(args) == 1 and args[0].__class__ == abc.types.FunctionType:
            return cls(args[0])

        def wrapper(func):
            result = cls(func)

            for arg in args:
                if isinstance(arg, Task) or isinstance(arg, str):
                    result.dependencies.append(arg)

            return result

        return wrapper


class SimpleTask(Task):
    def invoke(self, ctx, *args):
        self.func(*args)


class ContextTask(Task):
    def invoke(self, ctx, *args):
        self.func(ctx.for_task(self), *args)

class OptionsTask(Task):
    def invoke(self, ctx, *args):
        ctx = ctx.for_task(self)
        options = OrderedDict()
        ctx.opt = self.OptionAdder(options.__setitem__)
        self.func(ctx, *args)

        if ctx.is_main:
            chosen_item = None
        else:
            chosen_item = getattr(ctx.cache, 'chosen_item', None)

        if chosen_item not in options:  # includes the possibility that chosen_item is None
            if 0 == len(options):
                raise Exception('No options set in %s' % self)
            elif 1 == len(options):
                ctx.pass_data(next(iter(options.values())))
                return
            chosen_item = input_list('Choose %s' % self, options.keys())
            if chosen_item:
                ctx.cache.chosen_item = chosen_item

        ctx.pass_data(options.get(chosen_item, None))

    class OptionAdder:
        __setter = [None]
        def __init__(self, setter):
            self.__setter[0] = setter

        def __setattr__(self, name, value):
            if name.startswith('_'):
                raise KeyError(name)
            self.__setter[0](name, value)


def invoke_with_dependencies(tasks_file, task, args):
    ctx = InvocationContext(tasks_file, task)

    stack = [task]
    run_order = []
    while stack:
        popped_task = stack.pop()
        run_order.insert(0, popped_task)
        stack += popped_task.dependencies

    already_invoked = set()
    for task in run_order:
        if task not in already_invoked:
            already_invoked.add(task)
            task.invoke(ctx, *args)

