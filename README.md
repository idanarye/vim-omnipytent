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

Blog post: https://dev.to/idanarye/omnipytent-5g5l

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
 * Integration with [Plumbum](https://plumbum.readthedocs.io)
 * Define helpers in other plugins and load them from a special
   `omnipytent.ext` module.

