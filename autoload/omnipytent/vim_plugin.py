import vim

import re

from .tasks_file import get_tasks_file
from .tasks import invoke_with_dependencies


def _api_entry_point(command):
    if command == 'invoke':
        args = vim.eval('a:000')
        if 0 == len(args):
            prompt_and_invoke()
        else:
            invoke(*args)
    elif command == 'edit':
        split_mode = vim.eval('a:splitMode')
        args = vim.eval('a:000')
        edit_task(split_mode, args[0])
    else:
        raise NotImplementedError()


def prompt_and_invoke():
    raise NotImplementedError()


def invoke(taskname, *args):
    tasks_file = get_tasks_file()
    tasks_file.load_if_stale()
    task = tasks_file[taskname]
    invoke_with_dependencies(tasks_file, task, args)
    # task.invoke(ctx, *args)


def edit_task(split_mode, taskname):
    tasks_file = get_tasks_file()
    if split_mode:
        vim.command(split_mode)
    tasks_file.open(taskname)


def _api_complete(include_task_args):
    arg_lead = vim.eval('a:argLead')
    cmd_line = vim.eval('a:cmdLine')
    cursor_pos = int(vim.eval('a:cursorPos'))

    cmd_line_before_cursor = cmd_line[:cursor_pos]
    parts = re.findall(r'(?:[^\\\s]|(?:\\\\)|(?:\\\s))+', cmd_line_before_cursor)
    if cmd_line_before_cursor.endswith(' '):
        parts.append('')

    tasks_file = get_tasks_file()
    tasks_file.load_if_stale()

    if len(parts) == 2:  # task name completion
        return sorted(taskname for taskname in tasks_file.tasks.keys() if taskname.startswith(parts[-1]))
    else:  # arguments completion
        if not include_task_args:
            return []
        raise NotImplementedError()

