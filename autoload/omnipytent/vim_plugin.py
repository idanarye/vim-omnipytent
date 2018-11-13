import vim

import os

from .tasks_file import TasksFile, get_tasks_file
from .tasks import invoke_with_dependencies
from .async_execution import AsyncExecutor, AsyncCommand
from .util import vim_eval, vim_repr


def _tasks_file_path():
    return TasksFile.find_tasks_file(TasksFile.default_name())


def _api_entry_point(command):
    if command == 'invoke':
        args = vim.eval('a:000')
        if 0 == len(args):
            prompt_and_invoke()
        else:
            invoke(*args)
    elif command == 'call' or command == 'try_call':
        idx = int(vim.eval('l:idx'))
        method = vim.eval('l:method')
        args = vim_eval('a:000')
        try:
            command = AsyncCommand.yielded[idx]
        except KeyError:
            if command == 'try_call':
                result = 0
            else:
                raise
        else:
            result = command.call(method, args)
        vim.command('let l:return = %s' % vim_repr(result))
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
    executor = AsyncExecutor(invoke_with_dependencies(tasks_file, task, args))
    executor.run_next()


def edit_task(split_mode, taskname):
    tasks_file = get_tasks_file()
    if split_mode:
        vim.command(split_mode)
    tasks_file.open(taskname)


def _api_complete(include_task_args):
    # arg_lead = vim.eval('a:argLead')
    # cmd_line = vim.eval('a:cmdLine')
    # cursor_pos = int(vim.eval('a:cursorPos'))

    tasks_file = get_tasks_file()
    tasks_file.load_if_stale()

    ctx = tasks_file.completion_context(arg_lead=vim.eval('a:argLead'),
                                        cmd_line=vim.eval('a:cmdLine'),
                                        cursor_pos=int(vim.eval('a:cursorPos')))


    if ctx.task is None:  # task name completion
        return sorted(taskname for taskname in tasks_file.tasks.keys() if taskname.startswith(ctx.arg_prefix))
    else:  # arguments completion
        if not include_task_args:
            return []
        return ctx.task.completions(ctx)

