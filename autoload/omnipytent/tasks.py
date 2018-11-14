import inspect
from collections import OrderedDict

import vim

from .context import InvocationContext
from .hacks import function_locals
from .util import input_list, other_windows, flatten_iterator


class Task(object):
    from .context import TaskContext

    def __init__(self, func):
        self.func = func

        self.name = func.__name__
        argspec = inspect.getargspec(func)
        self._task_args = argspec.args[1:]  # remove `ctx` from the list
        self._task_varargs = argspec.varargs

        self.dependencies = []
        self.completers = []

    def _run_func_as_generator(self, *args, **kwargs):
        result = self.func(*args, **kwargs)
        if inspect.isgenerator(result):
            result = flatten_iterator(result)
            try:
                yielded = next(result)
                while True:
                    yield yielded
                    yielded = result.send(yielded._returned_value)
            except StopIteration:
                pass

    def invoke(self, ctx, *args):
        ctx = ctx.for_task(self)
        if not ctx.is_main:
            args = ()
        for yielded in self._run_func_as_generator(ctx, *args):
            yield yielded

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
    MULTI = False

    class TaskContext(Task.TaskContext):
        _preview = None
        _key = None

        def key(self, key):
            self._key = key

        def preview(self, preview):
            self._preview = preview

        @property
        def _chosen_key(self):
            return getattr(self.cache, 'chosen_key', None)

        def _should_repick(self, options):
            if self.is_main:
                return True
            return self._chosen_key not in options

        def _pass_choice(self, options, chosen_key):
            self.pass_data(options.get(chosen_key, None))

        def _pass_from_arguments(self, options, args):
            pass

    def __init__(self, func):
        super(OptionsTask, self).__init__(func)

        self.__func_args_set = set(inspect.getargspec(func).args)
        if 1 < len(self.__func_args_set):
            raise Exception('Options task %s should have 0 or 1 arg' % self)

        self.complete(self.complete_options)

    def _varname_filter(self, target):
        return not target.startswith('_') and target not in self.__func_args_set

    def _gen_keys_for_completion(self, cctx):
        if not inspect.isgeneratorfunction(self.func):
            for name in self.func.__code__.co_varnames:
                if self._varname_filter(name):
                    yield name
            return

        ictx = InvocationContext(cctx.tasks_file, self)
        tctx = ictx.for_task(self)
        for key in self._resolve_options(tctx).keys():
            yield key

    def complete_options(self, ctx):
        if 0 == ctx.arg_index:
            return self._gen_keys_for_completion(ctx)
        else:
            return []

    def _resolve_options(self, ctx):
        if len(self.__func_args_set) == 0:
            args = ()
        else:
            args = (ctx,)

        if not inspect.isgeneratorfunction(self.func):
            return function_locals(self.func, *args)

        items = list(self.func(*args))
        if not ctx._key:
            raise Exception('ctx.key not set for generator-based options task')
        return OrderedDict((str(ctx._key(item)), item) for item in items)

    def invoke(self, ctx, *args):
        from .async_execution import CHOOSE
        if False:
            yield  # force this into a genrator
        ctx = ctx.for_task(self)
        options = self._resolve_options(ctx)

        if 0 == len(args) or not ctx.is_main:
            if ctx._should_repick(options):  # includes the possibility that chosen_key is None
                options_keys = list(filter(self._varname_filter, options.keys()))
                if 0 == len(options):
                    raise Exception('No options set in %s' % self)
                elif 1 == len(options):
                    ctx.pass_data(next(iter(options.values())))
                    return
                if ctx._preview:
                    def preview(key):
                        return ctx._preview(options[key])
                else:
                    preview = None
                async_cmd = CHOOSE(options_keys, preview=preview, multi=self.MULTI)
                yield async_cmd
                chosen_key = async_cmd._returned_value
                if chosen_key:
                    ctx.cache.chosen_key = chosen_key
            else:
                chosen_key = ctx._chosen_key

            ctx._pass_choice(options, chosen_key)
        else:
            self._pass_from_arguments(ctx, options, args)

    def _pass_from_arguments(self, ctx, options, args):
        if 1 == len(args):
            chosen_key = args[0]
            if self._varname_filter(chosen_key) and chosen_key in options:
                ctx.cache.chosen_key = chosen_key
                ctx.pass_data(options[chosen_key])
            else:
                raise Exception('%s is not a valid choice for %s' % (chosen_key, self))
        else:
            raise Exception('Too many arguments for %s - expected 1' % self)


class OptionsTaskMulti(OptionsTask):
    MULTI = True

    class TaskContext(OptionsTask.TaskContext):
        _preview = None

        def _should_repick(self, options):
            if self.is_main:
                return True
            if not self._chosen_key:
                return True
            return not set(self._chosen_key).issubset(options)

        def _pass_choice(self, options, chosen_key):
            self.pass_data(list(map(options.get, chosen_key)))

    def complete_options(self, ctx):
        already_picked = set(ctx.prev_args)
        return [key for key in self._gen_keys_for_completion(ctx)
                if key not in already_picked]

    def _pass_from_arguments(self, ctx, options, args):
        def generator():
            dup = set()
            for chosen_key in args:
                if chosen_key in dup:
                    raise Exception('%s picked more than once' % (chosen_key,))
                elif self._varname_filter(chosen_key) and chosen_key in options:
                    dup.add(chosen_key)
                    yield chosen_key
                else:
                    raise Exception('%s is not a valid choice for %s' % (chosen_key, self))
        chosen_key = list(generator())
        ctx.cache.chosen_key = chosen_key
        ctx._pass_choice(options, chosen_key)


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
            for yielded in super(WindowTask, self).invoke(ctx, *args):
                yield yielded
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
    with tasks_file.in_tasks_dir_context():
        for task in run_order:
            if task not in already_invoked:
                already_invoked.add(task)
                for yielded in task.invoke(ctx, *args):
                    yield yielded
