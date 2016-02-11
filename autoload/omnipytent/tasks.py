import inspect

from .context import InvocationContext
from .hacks import function_locals
from .util import input_list


class Task(object):
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.dependencies = []
        self.completers = []

    def invoke(self, ctx, *args):
        self.func(ctx.for_task(self), *args)

    def __repr__(self):
        return '<Task: %s>' % self.name

    def completions(self, parts):
        result = set()
        for completer in self.completers:
            result.update(completer(parts))
        return sorted(result)

    def complete(self, func):
        def completer(parts):
            result = func(parts)
            result = (item for item in result if item.startswith(parts[-1]))
            return result
        self.completers.append(completer)


class OptionsTask(Task):
    def __init__(self, func):
        super(OptionsTask, self).__init__(func)

        self.__func_args_set = set(inspect.getargspec(func).args)
        if 1 < len(self.__func_args_set):
            raise Exception('Options task %s should have 0 or 1 arg' % self)

        self.complete(self.complete_options)

    def __varname_filter(self, target):
        return not target.startswith('_') and target not in self.__func_args_set

    def complete_options(self, parts):
        return filter(self.__varname_filter, self.func.__code__.co_varnames)

    def invoke(self, ctx, *args):
        ctx = ctx.for_task(self)
        if len(self.__func_args_set) == 0:
            options = function_locals(self.func)
        else:
            options = function_locals(self.func, ctx)

        # options = {k: v for k, v in options.items() if self.__varname_filter(k)}

        if 0 == len(args):
            if ctx.is_main:
                chosen_item = None
            else:
                chosen_item = getattr(ctx.cache, 'chosen_item', None)

            options_keys = list(filter(self.__varname_filter, options.keys()))
            if chosen_item not in options_keys:  # includes the possibility that chosen_item is None
                if 0 == len(options):
                    raise Exception('No options set in %s' % self)
                elif 1 == len(options):
                    ctx.pass_data(next(iter(options.values())))
                    return
                chosen_item = input_list('Choose %s' % self, options_keys)
                if chosen_item:
                    ctx.cache.chosen_item = chosen_item

            ctx.pass_data(options.get(chosen_item, None))
        elif 1 == len(args):
            chosen_item = args[0]
            if self.__varname_filter(chosen_item) and chosen_item in options:
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

