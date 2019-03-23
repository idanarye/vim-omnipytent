[![Build Status](https://travis-ci.org/idanarye/vim-omnipytent.svg?branch=develop)](https://travis-ci.org/idanarye/vim-omnipytent)

REQUIREMENTS
============

 * Python installed on your computer
 * Vim compiled with Python support(check with `:echo has('python')` and/or `:echo has('python3')` from Vim)

INTRODUCTION
============

Omnipytent is a plugin for creating and running project-specific, user-specific
tasks. Programmers should know enough about to programming to be able to script
their own workflow - and Omnipytent aims to make this as simple, as accessible
and as out-of-your-way as possible. Omnipytent is the successor to
[Integrake](https://github.com/idanarye/vim-integrake), and follows a similar
design - but in Python, so it could be used in neovim(which did not have Ruby
support at the time)

Blog posts:
* https://dev.to/idanarye/omnipytent-5g5l
* https://dev.to/idanarye/omnipytent-130-async-tasks-and-selection-uis-2e0o

KEY FEATURES
============

 * Tasks run inside the Vim session environment and can interact with it - read
   the line under your cursor, activate commands from other plugins etc.
 * Simple scaffolding for quickly adding new tasks.
 * Helpers for running Vim functions and commands from the Python environment.
 * Tasks file reloaded on demand.
 * Tasks can depend on each other, and pass data up the dependency tree.
 * Autocompletion for tasks and task arguments.
 * Tasks are project-specific. Map your favorite key to run the "build" task,
   and use the it for every project you want to build, regardless of language
   and/or build-system(you'll still need to write individual "build" tasks)
 * Tasks are user-specific. There are many things you need to be considerate
   toward your teammates with - Omnipytent tasks are not one of them!
 * Integration with [Plumbum](https://plumbum.readthedocs.io),
   [fzf](https://github.com/junegunn/fzf),
   [Denite](https://github.com/Shougo/denite.nvim),
   [Unite](https://github.com/Shougo/unite.vim) and
   [CtrlP](https://github.com/ctrlpvim/ctrlp.vim)
 * Define helpers in other plugins and load them from a special
   `omnipytent.ext` module. Also useful for importing common sets of tasks.

GETTING STARTED
===============

Set the file prefix and default python version in your `.vimrc` - something like:

```vim
let g:omnipytent_filePrefix = '.moshecohen' " Replace with your own (user)name
let g:omnipytent_defaultPythonVersion = 3 " Or 2, if you want to use Python 2
```

Open Vim in the root directory of your project - let's assume it's a C project
with a Makefile. To create a tasks file for this project, run:
```vim
:OPedit build
```

This will generate a brand new tasks file that looks like this:

```python
import vim
from omnipytent import *
```

To create your first task, run:

```vim
:OPedit build
```

This will append a new task to the tasks file:
```python
@task
def build(ctx):
    <cursor here in insert mode>
```

Now write the body of the task:

```python
@task
def build(ctx):
    CMD.make('--quiet')
```

Omnipytent's `CMD` object can be used to run Vim commands - so this task will
run the Vim command `:make --quiet` and build your project. To activate it, run:

```vim
:OP build
```

Let's create more tasks. You don't have to use `:OPedit` - you can just
copy-paste the `build` task and modify it:

```python
@task
def run(ctx):
    BANG('./a.out', 'hello', 'world')


@task
def debug(ctx):
    TERMINAL_PANEL('gdb', './a.out')
```

`BANG` can be used to run shell command - so running this task with `:OP run`
is the same as running:
```vim
:!./a.out hello world
```

Because `gdb` is an interactive program, we can't run it with regular `:!` - we
need `:terminal` - so we use `TERMINAL_PANEL`. There is also `TERMINAL_TAB`
that opens the terminal in another tab.

And that's it - you have a tasks file with three tasks to build, run and debug
your code. You can add more tasks that do different things.

Few important usability notes:

* You can run `:OP` without arguments to get a prompt for picking the task you
  want to run.
* You can run `:OPedit` again to go back to the tasks file.
* Running `:OPedit build` will not create a new task - it will jump to the
  existing `build` task instead.

For advanced usage tips, refer to [the wiki](https://github.com/idanarye/vim-omnipytent/wiki).

For more detailed documentation, refer to `:help omnipytent`.
