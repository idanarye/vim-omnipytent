import vim

import re
import os

from .tasks_file import TasksFile, get_tasks_file
from .tasks import invoke_with_dependencies


def _tasks_file_name():
    return TasksFile.default_name()


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
    # Not sure if this will ever get implemented. In Integrake invoking without
    # command would have popped up the list of tasks and prompted the user to
    # pick one. Since I implemented Vim command line completion for tasks I
    # ended up never using it(it turned out to be quite a nuisance, in fact),
    # so I see no reason to implement in in Omnipytent.
    raise NotImplementedError()


def invoke(taskname, *args):
    tasks_file = get_tasks_file()
    tasks_file.load_if_stale()
    task = tasks_file[taskname]
    invoke_with_dependencies(tasks_file, task, args)


def edit_task(split_mode, taskname):
    tasks_file = get_tasks_file()
    if split_mode:
        vim.command(split_mode)
    tasks_file.open(taskname)


def _api_complete(include_task_args):
    # arg_lead = vim.eval('a:argLead')
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
        task = tasks_file[parts[1]]
        return task.completions(parts)

