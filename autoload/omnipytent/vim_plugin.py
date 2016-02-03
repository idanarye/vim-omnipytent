import vim

from .tasks_file import get_tasks_file


def _vim_api(command):
    vimargs = vim.bindeval('a:')
    if command == 'invoke':
        args = vimargs['000']
        ctx = None
        if 0 == len(args):
            prompt_and_invoke(ctx)
        else:
            invoke(ctx, *args)
    elif command == 'edit':
        args = vimargs['000']
        edit_task(args[0])
    else:
        raise NotImplementedError()


def prompt_and_invoke(ctx):
    raise NotImplementedError()


def invoke(ctx, taskname, *args):
    tasks_file = get_tasks_file()
    if tasks_file.is_stale:
        tasks_file.load()
    task = tasks_file[taskname]
    task.invoke(ctx, *args)


def edit_task(taskname):
    tasks_file = get_tasks_file()
    tasks_file.open(taskname)
