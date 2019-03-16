import inspect
from collections import OrderedDict

import vim
import re

from .base_task import BaseTask
from .context import InvocationContext
from .hacks import function_locals
from .util import other_windows, flatten_iterator, is_generator_callable


_getargspec = getattr(inspect, 'getfullargspec', inspect.getargspec)


class Task(BaseTask):
    @property
    def _kwargs_for_func(self):
        kwargs = {}
        for name, task in self._special_args.items():
            kwargs[name] = self.dep._get_by_task(task)
        return kwargs

    # def _init__(self, func, alias=[], name=None, doc=None):
        # self.func = func
        # self._subtasks = {}

        # self.name = name or func.__name__
        # self.doc = doc or func.__doc__
        # try:
            # argspec = _getargspec(func)
        # except TypeError:
            # argspec = _getargspec(func.__call__)
        # self._task_ctx_arg_name = argspec.args[0] if argspec.args else None
        # if getattr(func, '__self__', None) is None:
            # self._task_args = argspec.args[1:]  # remove `ctx` from the list
        # else:
            # self._task_args = argspec.args[2:]  # remove `self`/`ctx` and `ctx` from the list
        # if argspec.defaults:
            # self._task_arg_defaults = dict(zip(self._task_args[-len(argspec.defaults):], argspec.defaults))
        # else:
            # self._task_arg_defaults = {}
        # self._task_varargs = argspec.varargs
        # self._special_args = OrderedDict()

        # self.dependencies = []
        # self.completers = []
        # if not alias:
            # self.aliases = []
        # elif isinstance(alias, str):
            # self.aliases = alias.split()
        # else:
            # self.aliases = list(alias)

        # self.__handle_special_args(argspec)

    def gen_doc(self, tasks_file):
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

        result.append(self.doc)
        return '\n\n'.join(str(line) for line in result if line is not None)

    def subtask(self, name, alias=[], doc=None):
        def inner(func):
            self._subtasks[name] = Task(
                func,
                name=self._format_subtask_full_name(self.__name__, name),
                alias=alias,
                doc=doc)

        if isinstance(name, str):
            return inner
        elif callable(name):
            func = name
            name = func.__name__
            inner(func)
        else:
            raise TypeError('Bad paramter for subtask %r' % (name,))

    def __repr__(self):
        return '<Task: %s>' % self.__name__

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


class OptionsTask(Task):
    MULTI = False

    _key = None
    _value = staticmethod(lambda v: v)
    _preview = None
    _score = None

    def key(self, key):
        self._key = key

    def value(self, value):
        self._value = value

    def preview(self, preview):
        self._preview = preview

    def score(self, score):
        self._score = score

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

    # def __init__(self, func, cache_choice_value=False, **kwargs):
    cache_choice_value = False

    @classmethod
    def _cls_init_(cls):
        if 1 < len(cls._task_args):
            raise Exception('Options task %s should have 0 or 1 arg' % cls)

        cls.complete(cls.complete_options)

        # self.subtask('?', doc='Print the current choice for the %r task' % self.__name__)(self.print_choice)
        # self.subtask('!', doc='Clear the choice for the %r task' % self.__name__)(self.clear_choice)

    def print_choice(self, ctx):
        cache = ctx.task_file.get_task_cache(self)
        try:
            chosen_key = cache.chosen_key
        except AttributeError:
            print('%s has no selected value' % (self.__name__,))
            return
        print('Current choice for %s: %s' % (self.__name__, chosen_key))

    def clear_choice(self, ctx):
        cache = ctx.task_file.get_task_cache(self)
        try:
            del cache.chosen_key
        except AttributeError:
            pass
        try:
            del cache.chosen_value
        except AttributeError:
            pass

    def _varname_filter(self, target):
        return all([
            not target.startswith('_'),
            target != self._task_ctx_arg_name,
            target not in self._task_args,
            target not in self._special_args,
        ])

    def _gen_keys_for_completion(self, cctx):
        if not is_generator_callable(self._func_):
            for name in self._func_.__code__.co_varnames:
                if self._varname_filter(name):
                    yield name
            return

        ictx = InvocationContext(cctx.tasks_file, self)
        for key in self._resolve_options().keys():
            yield key

    @classmethod
    def complete_options(cls, ctx):
        if 0 == ctx.arg_index:
            return ctx.task._gen_keys_for_completion(ctx)
        else:
            return []

    def _resolve_options(self):
        if not is_generator_callable(self._func_):
            result = function_locals(self._func_, **self._kwargs_for_func)
            for special_arg in self._special_args.keys():
                result.pop(special_arg, None)
            return result

        items = list(self._func_(**self._kwargs_for_func))
        if not self._key:
            raise Exception('key not set for generator-based options task')
        return OrderedDict((str(self._key(item)), item) for item in items)

    def invoke(self, *args):
        from .async_execution import CHOOSE

        if self.cache_choice_value and not self.is_main:
            try:
                chosen_value = self.cache.chosen_value
            except AttributeError:
                pass
            else:
                self.pass_data(chosen_value)
                return

        options = self._resolve_options()

        if 0 == len(args) or not self.is_main:
            if self._should_repick(options):  # includes the possibility that chosen_key is None
                options_keys = list(filter(self._varname_filter, options.keys()))
                if 0 == len(options):
                    raise Exception('No options set in %s' % self)
                elif 1 == len(options):
                    single_key, = options.keys()
                    single_value = self._pass_choice(options, single_key)
                    if self.cache_choice_value:
                        self.cache.chosen_value = single_value
                    return
                if self._preview:
                    def preview(key):
                        return self._preview(options[key])
                else:
                    preview = None

                if self._score:
                    def score(key):
                        return self._score(options[key])
                else:
                    score = None

                async_cmd = CHOOSE(options_keys, preview=preview, score=score, multi=self.MULTI)
                yield async_cmd
                chosen_key = async_cmd._returned_value
                if chosen_key:
                    self.cache.chosen_key = chosen_key
                    chosen_value = self._pass_choice(options, chosen_key)
                    if self.cache_choice_value:
                        self.cache.chosen_value = chosen_value
            else:
                chosen_key = self._chosen_key

            self._pass_choice(options, chosen_key)
        else:
            self._pass_from_arguments(self, options, args)

    def _pass_from_arguments(self, ctx, options, args):
        if 1 == len(args):
            chosen_key = args[0]
            if self._varname_filter(chosen_key) and chosen_key in options:
                ctx.cache.chosen_key = chosen_key
                if self.cache_choice_value:
                    ctx.cache.chosen_value = options[chosen_key]
                ctx.pass_data(options[chosen_key])
            else:
                raise Exception('%s is not a valid choice for %s' % (chosen_key, self))
        else:
            raise Exception('Too many arguments for %s - expected 1' % self)


class OptionsTaskMulti(OptionsTask):
    MULTI = True

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

    @classmethod
    def complete_options(cls, ctx):
        already_picked = set(ctx.prev_args)
        return [key for key in ctx.task._gen_keys_for_completion(ctx)
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
    def __init__(self, *args, **kwargs):
        super(WindowTask, self).__init__(*args, **kwargs)
        self.subtask(self.close, doc='Close the window opened by the %r task' % self.__name__)

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

    def close(self, ctx):
        cache = ctx.task_file.get_task_cache(self)
        try:
            window = cache.window
        except AttributeError:
            return
        if window.valid:
            vim.command('%swincmd c' % window.number)
        del cache.window
        try:
            del cache.pass_data
        except AttributeError:
            pass


def invoke_with_dependencies(tasks_file, task, args):
    invocation_context = InvocationContext(tasks_file, task)

    stack = [task(invocation_context)]
    run_order = []
    while stack:
        popped_task = stack.pop()
        run_order.insert(0, popped_task)
        stack.extend(d(invocation_context) for d in popped_task.all_dependencies())

    already_invoked = set()
    with tasks_file.in_tasks_dir_context():
        for task in run_order:
            if type(task) not in already_invoked:
                already_invoked.add(type(task))
                for yielded in task.invoke(*args):
                    yield yielded


__MRU_ACTION_NAMES = []


def prompt_and_invoke_with_dependencies(tasks_file):
    from .async_execution import CHOOSE
    pickable_tasks = ((k, v) for (k, v) in tasks_file.tasks.items()
                      if len(v._task_arg_defaults) == len(v._task_args))

    last_actions_indices = {n: i for i, n in enumerate(__MRU_ACTION_NAMES)}

    choose = CHOOSE(
        pickable_tasks,
        fmt=lambda p: p[0],
        preview=lambda p: p[1].gen_doc(tasks_file),
        score=lambda p: last_actions_indices.get(p[0], -1),
    )
    yield choose
    task = choose._returned_value[1]
    task_name = choose._returned_value[0]
    if task_name in last_actions_indices:
        __MRU_ACTION_NAMES.remove(task_name)
    __MRU_ACTION_NAMES.append(choose._returned_value[0])
    while 20 < len(__MRU_ACTION_NAMES):
        __MRU_ACTION_NAMES.pop(0)

    for yielded in invoke_with_dependencies(tasks_file, task, []):
        yield yielded
