import inspect
from collections import OrderedDict
import sys

import vim

from .base_task import Task
from .context import InvocationContext
from .hacks import function_locals
from .util import other_windows, is_generator_callable, bare_func_wrapper, vim_repr


class OptionsTask(Task):
    _CONCRETE_ = False

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
        if self.MULTI:
            if not self._chosen_key:
                return True
            return not set(self._chosen_key).issubset(options)
        else:
            return self._chosen_key not in options

    def _pass_choice(self, options, chosen_key):
        if self.MULTI:
            values = map(options.get, chosen_key)
            values = map(self._value, values)
            values = list(values)
            self.pass_data(values)
            return values
        else:
            value = options.get(chosen_key, None)
            value = self._value(value)
            self.pass_data(value)
            return value

    cache_choice_value = False

    @classmethod
    def _cls_init_(cls):
        if not cls._CONCRETE_:
            return

        if 1 < len(cls._task_args):
            raise Exception('Options task %s should have 0 or 1 arg' % cls)

        cls.complete(cls.complete_options)

        cls.subtask('?', doc='Print the current choice for the %r task' % cls.__name__)(bare_func_wrapper(cls.print_choice))
        cls.subtask('!', doc='Clear the choice for the %r task' % cls.__name__)(bare_func_wrapper(cls.clear_choice))

    @classmethod
    def print_choice(cls, self):
        cache = self.task_file.get_task_cache(cls)
        try:
            chosen_key = cache.chosen_key
        except AttributeError:
            print('%s has no selected value' % (cls.__name__,))
            return
        print('Current choice for %s: %s' % (cls.__name__, chosen_key))

    @classmethod
    def clear_choice(cls, self):
        cache = self.task_file.get_task_cache(cls)
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
        if cls.MULTI:
            already_picked = set(ctx.prev_args)
            return [key for key in ctx.task._gen_keys_for_completion(ctx)
                    if key not in already_picked]
        else:
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
        if self.MULTI:
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
            self.cache.chosen_key = chosen_key
            self._pass_choice(options, chosen_key)
        else:
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
    _CONCRETE_ = False

    MULTI = True


class WindowTask(Task):
    _CONCRETE_ = False

    @classmethod
    def _cls_init_(cls):
        if not cls._CONCRETE_:
            return

        cls.subtask(bare_func_wrapper(cls.close), doc='Close the window opened by the %r task' % cls.__name__)

    def invoke(self, *args):
        try:
            window = self.cache.window
        except AttributeError:
            pass
        else:
            if window.valid:
                if self.is_main:
                    with other_windows(window):
                        vim.command('bdelete!')
                else:
                    try:
                        passed_data = self.cache.passed_data
                    except AttributeError:
                        self.pass_data(window)
                    else:
                        self.pass_data(passed_data)
                    return

        try:
            del self.cache.window
        except AttributeError:
            pass
        try:
            del self.cache.pass_data
        except AttributeError:
            pass

        with other_windows():
            for yielded in super(WindowTask, self).invoke(*args):
                yield yielded
            window = vim.current.window
        self.cache.window = window
        if self.has_passed_data:
            self.cache.passed_data = self.passed_data
        else:
            self.pass_data(window)

    @classmethod
    def close(cls, self):
        cache = self.task_file.get_task_cache(cls)
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

    pickable_tasks = list(pickable_tasks)

    invocation_context = InvocationContext(tasks_file, None)

    choose = CHOOSE(
        pickable_tasks,
        fmt=lambda p: p[0],
        preview=lambda p: p[1](invocation_context).gen_doc(),
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


class CombineSources(OptionsTask):
    _CONCRETE_ = False

    @classmethod
    def _cls_init_(cls):
        if not cls._CONCRETE_:
            return
        super(CombineSources, cls)._cls_init_()

        if not hasattr(cls, 'sources'):
            raise TypeError('No sources defined for %s' % cls)

    def all_dependencies(self):
        for source in self.sources:
            for dependency in source(self.invocation_context).all_dependencies():
                yield dependency
        for dependency in super(CombineSources, self).all_dependencies():
            yield dependency

    def _func_(self):
        for source in self.sources:
            source = source(self.invocation_context)
            for value in source._resolve_options().values():
                yield source, value

    def __redirector(self, target, item):
        source, value = item
        func = getattr(source, target)
        if target == '_preview' and func is None:
            return 'No preview for %s' % source.name
        return func(value)

    def _key(self, item):
        return self.__redirector('_key', item)

    def _value(self, item):
        return self.__redirector('_value', item)

    # TODO: - add `_score()`?


class DataCellTask(Task):
    _CONCRETE_ = False

    _transform = staticmethod(lambda txt: txt)
    default_content = ''

    @classmethod
    def transform(cls, transform):
        cls._transform = staticmethod(transform)

    @staticmethod
    def _cls_modify_dct_(dct):
        try:
            transform = dct.pop('transform')
        except KeyError:
            pass
        else:
            dct['_transform'] = staticmethod(transform)

    @classmethod
    def _cls_init_(cls):
        if not cls._CONCRETE_:
            return

        cls.subtask(bare_func_wrapper(cls.update_cache))
        cls.subtask(bare_func_wrapper(cls.clear))

    @classmethod
    def update_cache(cls, self):
        cache = self.task_file.get_task_cache(cls)
        assert vim.current.buffer == cache.already_opened_buffer
        cache.textual_content = '\n'.join(vim.current.buffer)

    @classmethod
    def clear(cls, self):
        cache = self.task_file.get_task_cache(cls)
        try:
            del cache.textual_content
        except AttributeError:
            pass

    def invoke(self, *args):
        if self.is_main:
            window = self.__get_window_of_buffer()
            if window:
                self.__go_to_window(window)
            else:
                for yielded_value in self.__open_buffer(*args):
                    yield yielded_value
        else:
            textual_content = self.__get_textual_content()
            if textual_content is None:
                for yielded_value in self.__open_buffer(*args):
                    yield yielded_value

                # Return from yield doesn't work here, and it's easier to use a cell than to add that support
                cell = [None]

                def set_cell():
                    cell[0] = '\n'.join(vim.current.buffer)
                from .async_execution import WAIT_FOR_AUTOCMD
                yield WAIT_FOR_AUTOCMD('BufDelete <buffer>', set_cell)
                textual_content, = cell

            self.pass_data(self._transform(textual_content))

    def __get_textual_content(self):
        window = self.__get_window_of_buffer()
        if window:
            return '\n'.join(window.buffer)
        try:
            return self.cache.textual_content
        except AttributeError:
            return None

    def __get_window_of_buffer(self):
        try:
            already_opened_buffer = self.cache.already_opened_buffer
        except AttributeError:
            return None
        matching_windows = [
            window
            for window in vim.windows
            if window.buffer == already_opened_buffer]
        if not matching_windows:
            return None
        assert already_opened_buffer.options['buftype'] == 'nofile'
        matching_windows.sort(key=lambda w: w.tabpage == vim.current.tabpage, reverse=True)
        return matching_windows[0]

    def __go_to_window(self, window):
        if window.tabpage != vim.current.tabpage:
            vim.command('tabnext %d' % window.tabpage.number)
        vim.command('%dwincmd w' % window.number)

    def __open_buffer(self, *args):
        try:
            already_opened_buffer = self.cache.already_opened_buffer
        except AttributeError:
            already_opened_buffer = None
        else:
            matching_windows = [
                window
                for window in vim.windows
                if window.buffer == already_opened_buffer ]
            if not matching_windows:
                already_opened_buffer = None
            else:
                assert already_opened_buffer.options['buftype'] == 'nofile'
                matching_windows.sort(key=lambda w: w.tabpage == vim.current.tabpage, reverse=True)
                window = matching_windows[0]
                if window.tabpage != vim.current.tabpage:
                    vim.command('tabnext %d' % window.tabpage.number)
                vim.command('%dwincmd w' % window.number)
                return

        try:
            textual_content = self.cache.textual_content
        except AttributeError:
            textual_content = self.default_content

        for yielded_value in super(DataCellTask, self).invoke(*args):
            yield yielded_value

        assert vim.current.buffer[:] == [''], 'created buffer is not empty'
        buftype = vim.current.buffer.options['buftype']
        if buftype != 'nofile':
            assert buftype == '', 'expected regular or nofile buffer - got %s' % (buftype,)
            assert not vim.current.buffer.name, 'created buffer attached to a file'
            vim.current.buffer.options['buftype'] = 'nofile'

        vim.command('autocmd omnipytent BufDelete <buffer> call omnipytent#invoke(%s, line("."), line("."), -1, %s)' % (
            sys.version_info.major,
            vim_repr(self._subtasks['update_cache'].__name__),
        ))

        vim.current.buffer[:] = textual_content.splitlines()
        self.cache.already_opened_buffer = vim.current.buffer

    def __invoke_dep(self, *args):
        self.pass_data('hello')
        if False:
            yield
