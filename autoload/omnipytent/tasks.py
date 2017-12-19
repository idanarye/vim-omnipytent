import inspect

import vim

from .context import InvocationContext
from .hacks import function_locals
from .util import input_list, other_windows


class Task(object):
    def __init__(self, func):
        self.func = func

        self.name = func.__name__
        argspec = inspect.getargspec(func)
        self._task_args = argspec.args[1:]  # remove `ctx` from the list
        self._task_varargs = argspec.varargs

        self.dependencies = []
        self.completers = []

    def invoke(self, ctx, *args):
        ctx = ctx.for_task(self)
        if ctx.is_main:
            self.func(ctx, *args)
        else:
            self.func(ctx)

    def __repr__(self):
        return '<Task: %s>' % self.name

    def completions(self, ctx):
        result = set()
        for completer in self.completers:
            result.update(completer(ctx))
        return sorted(result)

    def complete(self, func):
        def completer(ctx):
            result = func(ctx)
            result = (item for item in result if item.startswith(ctx.arg_prefix))
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

    def complete_options(self, ctx):
        if 0 == ctx.arg_index:
            return filter(self.__varname_filter, self.func.__code__.co_varnames)
        else:
            return []

    def invoke(self, ctx, *args):
        ctx = ctx.for_task(self)
        if len(self.__func_args_set) == 0:
            options = function_locals(self.func)
        else:
            options = function_locals(self.func, ctx)

        # options = {k: v for k, v in options.items() if self.__varname_filter(k)}

        if 0 == len(args) or not ctx.is_main:
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


class WindowTask(Task):
    def invoke(self, ctx, *args):
        task_ctx = ctx.for_task(self)
        try:
            window = task_ctx.cache.window
        except AttributeError:
            pass
        else:
            if window.valid:
                if task_ctx.is_main:
                    with other_windows(window):
                        vim.command('bdelete!')
                else:
                    try:
                        passed_data = task_ctx.cache.passed_data
                    except AttributeError:
                        task_ctx.pass_data(window)
                    else:
                        task_ctx.pass_data(passed_data)
                    return

        try:
            del task_ctx.cache.window
        except AttributeError:
            pass
        try:
            del task_ctx.cache.pass_data
        except AttributeError:
            pass

        with other_windows():
            super(WindowTask, self).invoke(ctx, *args)
            window = vim.current.window
        task_ctx.cache.window = window
        if task_ctx.has_passed_data:
            task_ctx.cache.passed_data = task_ctx.passed_data
        else:
            task_ctx.pass_data(window)


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

