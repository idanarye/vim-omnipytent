import inspect

from context import InvocationContext
from hacks import function_locals


class Task(object):
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.dependencies = []
        self._completers = []

    def invoke(self, ctx, *args):
        self.func(ctx.for_task(self), *args)

    def __repr__(self):
        return '<Task: %s>' % self.name

    def completions(self, parts):
        result = set()
        for completer in self._completers:
            result.update(completer(parts))
        return sorted(result)

    def complete(self, func):
        def completer(parts):
            result = func(parts)
            result = (item for item in result if item.startswith(parts[-1]))
            return result
        self._completers.append(completer)


class OptionsTask(Task):
    def __init__(self, func):
        super(OptionsTask, self).__init__(func)

        self.__arg_len = len(inspect.getargspec(func).args)
        if 1 < self.__arg_len:
            raise Exception('Options task %s should have 0 or 1 arg' % self)

        self.complete(self.complete_options)

    @staticmethod
    def __filter_hidden(target):
        if isinstance(target, dict):
            return target.__class__((k, v) for k, v in target.items() if not k.startswith('_'))
        else:
            return (name for name in target if not name.startswith('_'))

    def complete_options(self, parts):
        return self.__filter_hidden(self.func.func_code.co_varnames)

    def invoke(self, ctx, *args):
        ctx = ctx.for_task(self)
        if self.__arg_len == 0:
            options = function_locals(self.func)
        else:
            options = function_locals(self.func, ctx)

        options = self.__filter_hidden(options)

        if 0 == len(args):
            with ctx.user_choose() as opts:
                for key, value in options.items():
                    opts.__setattr__(key, value)
        elif 1 == len(args):
            chosen_item = args[0]
            if chosen_item in options:
                ctx.cache.chosen_item = chosen_item
                ctx.pass_data(options[chosen_item])
            else:
                raise Exception('%s is not a valid choice for %s' % (chosen_item, self))
        else:
            raise Exception('Too many arguments for %s - expected 1' % self)


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

