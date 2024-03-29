# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Refactor the tasks architecture:
  - **NOTE**: this change could _potentially break_ task files that were
    messing with the internal structure, but _should not affect_ code that was
    only accessing the documented features.
  - Each task is a type now.
  - Tasks get instantiated when you run them.
  - The instantiated tasks serve as their own context.

### Added
- Sugar for task dependencies (using argument defaults)
- Task aliases.
- `cache_choice_value`
- `ctx.value` for options tasks.
- `CombineSources`
- `score` for `CHOOSE` and for options tasks (`ctx.score`)
- `Terminal.alive`
- Subtasks:
  - For options task - `<task>?` to print the choice and `<task>!` to clear it.
  - For windows task - `<task>.close` to close the window.
- Bare `:OP` to open a selection UI for picking tasks.
- `CombineSources` task for combining multiple options tasks.
- `JOB` for running shell commands in the background.
- `add_alias` and `add_subtask_alias` for adding aliases to existing tasks.
- `DataCellTask` for creating a buffer that holds cached data.
- `WAIT_FOR_AUTOCMD` for yielding until we get an autocommand.
- `complete` (and `complete_findstart`) arguments for `INPUT_BUFFER`.
- `buffer_command` method for `INPUT_BUFFER`.

### Fixed
- Package structure in `omnipytent.ext`.
- CtrlP selection UI with `fmt` and multiple entries that have the same `fmt`.
- A weird `bytes`/`str` problem with `CHOOSE`.
- FZF not always starting in insert mode in Neovim.
- Weird behaviors (mostly swallowed `echo`s/`print`s) when resuming async operations.
- Match Plumbum's `envvar` -> `env` change.

## 1.3.0 - 2018-11-16
### Added
- Add `ctx.proj_dir`, `ctx.task_dir`, `ctx.cur_dir` and `ctx.file_dir`.
- Add `g:omnipytent_projectRootMarkers` for picking a parent directory as
  project root when there is no tasks file.
- Async tasks mechanism.
  - `INPUT_BUFFER` - creates a buffer, and when the user finishes with it -
    returns the buffer lines and resumes the command.
  - `CHOOSE` - runs a selection UI on the source list. Supports
    [FZF](https://github.com/junegunn/fzf),
    [Unite](https://github.com/Shougo/unite.vim),
    [Denite](https://github.com/Shougo/denite.nvim) and
    [CtrlP](https://github.com/ctrlpvim/ctrlp.vim). Reverts to `inputlist` if
    none is available.
    - FZF, Unite and Denite support multiple choices and selection preview.
- `@task.options_multi` - like `task.options` but allows multiple choices.
- Generator style for `@task.options`.

### Changed
- Look the directory tree for a tasks file.
- Options tasks use the chosen selection UI.

### Fixed
- `vim_eval` for lists and dicts.
- Input mode handling when starting terminal.

## 1.2.0 - 2017-12-19
### Added
- Add the `OPT` helper for easy access to options.
- Add the `del` operator for `VAR`.
- Add the `in` operator for `VAR` and `OPT`.
- Add the `changed` context manager for `VAR` and `OPT`.
- Add utils for working with Vim windows - `grep_windows`, `grep_window` and
  `other_windows`.
- Add `window` tasks.
- Add terminal shell executor(returned from `TERMINAL_PANEL` and
  `TERMINAL_TAB`)
- Add `<<` operator for shell executors to send raw text.
- Tests(about time)
- A cheat sheet in the doc

### Fixed
- Fix a doc problem where `:!` was defining a tag instead of refering to it
- Fix binary-vs-string problem with Python3 and Vim
- Fix Python type problems by making all `execution.py` classes subclass
  `object`.
- Fix bug when cleaning tasks cache.

## 1.1.0 - 2017-12-01
### Added
- Windows support.
- `TERMINAL_PANEL` and `TERMINAL_TAB` support for Vim 8.
- `omnipytent.ext` for loading module from `omnipytent` directories in Vim plugins.
- Support Plumbum's `with_env()`(Linux+Windows)
- `g:omnipytent_defaultPythonVersion` for picking Python2 or Python3 as the
  default Python version for new tasks files.
- Support (named) parameters in shell executors.
  - Add the `size` parameter to `TERMINAL_PANEL` for setting the number of lines.

### Changed
- Don't put blank line at the end of the file - Vim already adds a linefeed...

## 1.0.0 - 2016-08-26
### Added
- Syntax for defining tasks and dependencies.
- Task running commands with completion.
- Shell executors:
  - `BANG`.
  - `TERMINAL_PANEL` and `TERMINAL_TAB` for Neovim only.
  - Users can easily define their own.
- [Plumbum](https://plumbum.readthedocs.io) integration.
- `FN`, `CMD` and `VAR` for easy access to the Vim environment.
- Task arguments with custom completion.
- Task cache.
- Tasks can pass data up the dependency tree.
- `options` tasks.
