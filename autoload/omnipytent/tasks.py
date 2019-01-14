import inspect
from collections import OrderedDict

import vim

from .context import InvocationContext
from .hacks import function_locals
from .util import input_list, other_windows, flatten_iterator, is_generator_callable


_getargspec = getattr(inspect, 'getfullargspec', inspect.getargspec)


class Task(object):
    from .context import TaskContext

    class TaskContext(TaskContext):
        @property
        def _kwargs_for_func(self):
            kwargs = {}
            for name, task in self.task._special_args.items():
                kwargs[name] = self.dep._get_by_task(task)
            return kwargs

    def __init__(self, func, alias=[]):
        self.func = func

        self.name = func.__name__
        try:
            argspec = _getargspec(func)
        except TypeError:
            argspec = _getargspec(func.__call__)
        self._task_ctx_arg_name = argspec.args[0] if argspec.args else None
        self._task_args = argspec.args[1:]  # remove `ctx` from the list
        self._task_varargs = argspec.varargs
        self._special_args = OrderedDict()

        self.dependencies = []
        self.completers = []
        if not alias:
            self.aliases = []
        elif isinstance(alias, str):
            self.aliases = alias.split()
        else:
            self.aliases = list(alias)

        self.__handle_special_args(argspec)

    def __handle_special_args(self, argspec):
        special_defaults = list(self.__split_special_defaults(argspec))
        if special_defaults:
            special_args = argspec.args[-len(special_defaults):]
            self._special_args.update(zip(special_args, special_defaults))
            assert special_args == self._task_args[-len(special_args):]
            self._task_args = self._task_args[:-len(special_args)]
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
        return isinstance(default, Task)

    def all_dependencies(self, tasks_file):
        for dependency in self.dependencies:
            yield dependency
        for dependency in self._special_args.values():
            yield dependency

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
        for yielded in self._run_func_as_generator(ctx, *args, **ctx._kwargs_for_func):
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
        _key = None
        _value = staticmethod(lambda v: v)
        _preview = None

        def key(self, key):
            self._key = key

        def value(self, value):
            self._value = value

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
            value = options.get(chosen_key, None)
            value = self._value(value)
            self.pass_data(value)
            return value

        def _pass_from_arguments(self, options, args):
            pass

    def __init__(self, func, cache_choice_value=False, **kwargs):
        self._cache_choice_value = cache_choice_value
        super(OptionsTask, self).__init__(func, **kwargs)

        if 1 < len(self._task_args):
            raise Exception('Options task %s should have 0 or 1 arg' % self)

        self.complete(self.complete_options)

    def _varname_filter(self, target):
        return all([
            not target.startswith('_'),
            target != self._task_ctx_arg_name,
            target not in self._task_args,
            target not in self._special_args,
        ])

    def _gen_keys_for_completion(self, cctx):
        if not is_generator_callable(self.func):
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
        if self._task_ctx_arg_name:
            args = (ctx,)
        else:
            args = ()

        if not is_generator_callable(self.func):
            result = function_locals(self.func, *args, **ctx._kwargs_for_func)
            for special_arg in self._special_args.keys():
                result.pop(special_arg, None)
            return result

        items = list(self.func(*args, **ctx._kwargs_for_func))
        if not ctx._key:
            raise Exception('ctx.key not set for generator-based options task')
        return OrderedDict((str(ctx._key(item)), item) for item in items)

    def invoke(self, ctx, *args):
        from .async_execution import CHOOSE
        if False:
            yield  # force this into a genrator
        ctx = ctx.for_task(self)

        if self._cache_choice_value and not ctx.is_main:
            try:
                chosen_value = ctx.cache.chosen_value
            except AttributeError:
                pass
            else:
                ctx.pass_data(chosen_value)
                return

        options = self._resolve_options(ctx)

        if 0 == len(args) or not ctx.is_main:
            if ctx._should_repick(options):  # includes the possibility that chosen_key is None
                options_keys = list(filter(self._varname_filter, options.keys()))
                if 0 == len(options):
                    raise Exception('No options set in %s' % self)
                elif 1 == len(options):
                    single_key, = options.keys()
                    single_value = ctx._pass_choice(options, single_key)
                    if self._cache_choice_value:
                        ctx.cache.chosen_value = single_value
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
                    chosen_value = ctx._pass_choice(options, chosen_key)
                    if self._cache_choice_value:
                        ctx.cache.chosen_value = chosen_value
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
                if self._cache_choice_value:
                    ctx.cache.chosen_value = options[chosen_key]
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
            values = map(options.get, chosen_key)
            values = map(self._value, values)
            values = list(values)
            self.pass_data(values)
            return values

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
        stack += popped_task.all_dependencies(tasks_file)

    already_invoked = set()
    with tasks_file.in_tasks_dir_context():
        for task in run_order:
            if task not in already_invoked:
                already_invoked.add(task)
                for yielded in task.invoke(ctx, *args):
                    yield yielded
