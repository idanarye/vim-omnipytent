import vim

from contextlib import contextmanager
import json
import re
import os.path
import inspect


class RawVim(str):
    @classmethod
    def fmt(cls, fmt, *args):
        return cls(fmt % args)


def vim_repr(value):
    if value is None:
        return '0'

    if isinstance(value, RawVim):
        return value

    if hasattr(value, '_to_raw_vim_'):
        return value._to_raw_vim_()

    if isinstance(value, bool):
        return str(int(value))  # 0 or 1

    # Python 2 only types
    try:
        if isinstance(value, long):
            return str(value)
        if isinstance(value, unicode):
            value = str(value)
            pass
    except NameError:
        pass

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        result = str(value)
        if 'e' in result and '.' not in result:
            result = result.replace('e', '.0e')
        return result

    if isinstance(value, (str, bytes)):
        return json.dumps(value)

    if isinstance(value, (list, set, tuple)):
        return '[%s]' % ', '.join(map(vim_repr, value))

    if isinstance(value, dict):
        try:
            value_iteritems = value.iteritems()
        except AttributeError:
            value_iteritems = value.items()
        return '{%s}' % ', '.join('%s: %s' % (vim_repr(k), vim_repr(v)) for k, v in value_iteritems)


__number_type = vim.eval('type(0)')
__float_type = vim.eval('type(0.0)')


def __apply_type_map(value, type_map):
    if type_map == __number_type:
        return int(value)
    elif type_map == __float_type:
        return float(value)
    elif isinstance(type_map, list):
        assert isinstance(value, list)
        assert len(value) == len(type_map)
        return [__apply_type_map(v, t) for v, t in zip(value, type_map)]
    elif isinstance(type_map, dict):
        assert isinstance(value, dict)
        assert value.keys() == type_map.keys()
        return {k: __apply_type_map(v, type_map[k]) for k, v in value.items()}
    else:
        return value


def vim_eval(expr):
    """Like vim.eval, but deals with numbers correctly"""
    # expr_type, expr_value = vim.eval('map([%s], "[type(v:val), v:val]")[0]' % expr)
    return __apply_type_map(*vim.eval('omnipytent#_typeMap(%s)' % (expr,)))


def input_list(prompt, options, fmt=str):
    take_from = 0
    while take_from < len(options):
        take_this_time = int(vim.eval('&lines')) - 2
        more_items_remaining = take_from + take_this_time < len(options)
        if more_items_remaining:
            take_this_time -= 1

        options_slice = options[take_from:(take_from + take_this_time)]
        take_from += take_this_time

        number_length = len(str(len(options_slice)))

        def iteration_items_generator():
            for option in options_slice:
                yield option
            if more_items_remaining:
                yield '*MORE*'

        def list_for_input_query_generator():
            yield prompt
            for index, option in enumerate(iteration_items_generator()):
                index_text = str(index + 1)
                yield '%s)%s %s' % (index_text,
                                    ' ' * (number_length - len(index_text)),
                                    fmt(option))
        list_for_input_query = list(list_for_input_query_generator())
        chosen_option_number = int(vim.eval("inputlist(%s)" % vim_repr(list_for_input_query)))

        if more_items_remaining and chosen_option_number == len(options_slice) + 1:
            print(' ')
        elif chosen_option_number < 1 or len(options_slice) < chosen_option_number:
            return None
        else:
            return options_slice[chosen_option_number - 1]


@contextmanager
def __populate_vimlist(function_start, action=' '):
    items = []

    def adder(filename=None, lnum=None, text=None, col=None, vcol=None, bufnr=None, pattern=None, nr=None, type=None):
        item = {}
        if filename is not None:
            item['filename'] = filename
        if lnum is not None:
            item['lnum'] = lnum
        if text is not None:
            item['text'] = text
        if col is not None:
            item['col'] = col
        if vcol is not None:
            item['vcol'] = vcol
        if bufnr is not None:
            item['bufnr'] = bufnr
        if pattern is not None:
            item['pattern'] = pattern
        if nr is not None:
            item['nr'] = nr
        if type is not None:
            item['type'] = type
        items.append(item)

    yield adder
    vim.command('call %s%s, %s)' % (function_start, vim_repr(items), vim_repr(action)))


def populate_quickfix():
    return __populate_vimlist('setqflist(')


def populate_loclist(window=0):
    return __populate_vimlist('setloclist(%s, ' % window)


def grep_windows(matcher):
    matcher = re.compile(matcher)

    for window in vim.windows:
        if matcher.search(window.buffer.name):
            yield window


def grep_window(matcher):
    window, = grep_windows(matcher)
    return window


@contextmanager
def other_windows(window=None):
    original_window = vim.current.window
    original_mode = vim.eval('mode()')
    if window:
        vim.current.window = window
    try:
        yield
    finally:
        vim.current.window = original_window
        if original_mode == 'n':
            vim.command(r'call feedkeys("\<C-\>\<C-n>")')


def load_companion_vim_file(source_file):
    """
    Load a companion Vim file with the same name of a Python file.

    For example, from ``foo.py`` call::

        load_companion_vim_file(__name__)

    To load ``foo.vim`` in the same directory.
    """

    path, ext = os.path.splitext(os.path.abspath(source_file))
    path += '.vim'
    vim.command('source ' + path)


def flatten_iterator(it):
    try:
        item = next(it)
        while True:
            if inspect.isgenerator(item):
                item = flatten_iterator(item)
                try:
                    subitem = next(item)
                    while True:
                        send = yield subitem
                        subitem = item.send(send)
                except StopIteration:
                    pass
            else:
                send = yield item
            item = it.send(send)
    except StopIteration:
        pass


def is_generator_callable(obj):
    if inspect.isgeneratorfunction(obj):
        return True
    try:
        call = obj.__call__
    except AttributeError:
        return False
    else:
        return inspect.isgeneratorfunction(call)
