# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Windows support.
- `TERMINAL_PANEL` and `TERMINAL_TAB` support for Vim 8.
- `omnipytent.ext` for loading module from `omnipytent` directories in Vim plugins.
- Support Plumbum's `with_env()`(Linux+Windows)

## 0.1.0 - 2016-08-26
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
