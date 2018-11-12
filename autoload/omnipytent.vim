function! s:runPythonCommands(pythonVersion, ...)
    for l:command in a:000
        if a:pythonVersion == 2
            execute 'python '.l:command
        elseif a:pythonVersion == 3
            execute 'python3 '.l:command
        else
            throw 'Unknown Python version '.a:pythonVersion
        endif
    endfor
endfunction

let s:modulePath = fnameescape(expand('<sfile>:p:h'))
if has('win32')
    let s:modulePath = escape(s:modulePath, '\')
endif
function! s:updatePythonSysPath(pythonVersion)
    call s:runPythonCommands(a:pythonVersion,
                \ 'if "'.s:modulePath.'" not in sys.path: sys.path.append("'.s:modulePath.'")',
                \ 'import omnipytent.vim_plugin',
                \ )
endfunction

if has('python')
    call s:updatePythonSysPath(2)
endif
if has('python3')
    call s:updatePythonSysPath(3)
endif

function! s:guessPythonVersion()
    if has('python')
        if has('python3')
            let l:has2 = filereadable(pyeval('omnipytent.vim_plugin._tasks_file_path()'))
            let l:has3 = filereadable(py3eval('omnipytent.vim_plugin._tasks_file_path()'))
            if l:has2
                if l:has3
                    throw "Can't decide on Python version - task files exist for both"
                else
                    return 2
                endif
            else
                if l:has3
                    return 3
                else
                    let l:defaultPythonVersion = get(g:, 'omnipytent_defaultPythonVersion', 0)
                    if 0 <= index([2, 3], l:defaultPythonVersion)
                        return l:defaultPythonVersion
                    else
                        throw "No task file exist - use :OP2edit or :OP3edit to create them, or see ':help g:omnipytent_defaultPythonVersion'"
                    endif
                endif
            endif
            throw 'bad'
        else
            return 2
        endif
    elseif has('python3')
        return 3
    else
        throw 'This build of Vim does not support Python plugins'
    endif
endfunction

function! s:apiEntryPointCommand(pythonVersion, command)
    let l:pythonVersion = a:pythonVersion
    if l:pythonVersion == 0
        let l:pythonVersion = s:guessPythonVersion()
    endif

    " Put the command for invoking the Python code in a varible, so it if
    " fails Vim won't cry about a missing endif.
    if l:pythonVersion == 2
        let l:baseCmd = 'python '
    elseif l:pythonVersion == 3
        let l:baseCmd = 'python3 '
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
    return printf('%s omnipytent.vim_plugin._api_entry_point(%s)', l:baseCmd, string(a:command))
endfunction

function! omnipytent#invoke(pythonVersion, line1, line2, count, ...)
    execute s:apiEntryPointCommand(a:pythonVersion, 'invoke')
endfunction

function! omnipytent#editTask(pythonVersion, splitMode, ...)
    let l:pythonVersion = a:pythonVersion
    if l:pythonVersion == 0
        let l:pythonVersion = s:guessPythonVersion()
    endif

    if l:pythonVersion == 2
        python omnipytent.vim_plugin._api_entry_point('edit')
    elseif l:pythonVersion == 3
        python3 omnipytent.vim_plugin._api_entry_point('edit')
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#complete(argLead, cmdLine, cursorPos)
    let l:pythonVersion = s:guessPythonVersion()
    if l:pythonVersion == 2
        return omnipytent#complete2(a:argLead, a:cmdLine, a:cursorPos)
    elseif l:pythonVersion == 3
        return omnipytent#complete3(a:argLead, a:cmdLine, a:cursorPos)
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#complete2(argLead, cmdLine, cursorPos)
    return pyeval('omnipytent.vim_plugin._api_complete(include_task_args=False)')
endfunction
function! omnipytent#complete3(argLead, cmdLine, cursorPos)
    return py3eval('omnipytent.vim_plugin._api_complete(include_task_args=False)')
endfunction

function! omnipytent#completeIncludeTaskArgs(argLead, cmdLine, cursorPos)
    let l:pythonVersion = s:guessPythonVersion()
    if l:pythonVersion == 2
        return omnipytent#complete2IncludeTaskArgs(a:argLead, a:cmdLine, a:cursorPos)
    elseif l:pythonVersion == 3
        return omnipytent#complete3IncludeTaskArgs(a:argLead, a:cmdLine, a:cursorPos)
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#complete2IncludeTaskArgs(argLead, cmdLine, cursorPos)
    return pyeval('omnipytent.vim_plugin._api_complete(include_task_args=True)')
endfunction
function! omnipytent#complete3IncludeTaskArgs(argLead, cmdLine, cursorPos)
    return py3eval('omnipytent.vim_plugin._api_complete(include_task_args=True)')
endfunction


function! omnipytent#convertTasksFilePythonVersion()
    if has('python') && has('python3')
        let l:tasksfile2 = pyeval('omnipytent.vim_plugin._tasks_file_path()')
        let l:tasksfile3 = py3eval('omnipytent.vim_plugin._tasks_file_path()')
        let l:has2 = filereadable(l:tasksfile2)
        let l:has3 = filereadable(l:tasksfile3)
        if l:has2 && l:has3
            let l:text = ['Both Python 2 and Python 3 tasks files exist',
                        \ 'Which one to keep?',
                        \ '2) Keep the Python 2 tasks file',
                        \ '3) Keep the Python 3 tasks file']
        elseif l:has2
            let l:text = ['Python 2 tasks file exists',
                        \ 'Do you want to convert it to Python 3?',
                        \ '2) No  - keep it a Python 2 tasks file',
                        \ '3) Yes - convert it to Python 3']
        elseif l:has3
            let l:text = ['Python 3 tasks file exists',
                        \ 'Do you want to convert it to Python 2?',
                        \ '2) Yes - convert it to Python 2',
                        \ '3) No  - keep it a Python 3 tasks file']
        else
            let l:text = ['No tasks file exists',
                        \ 'Do you want to create one?',
                        \ '2) Create a Python 2 tasks file',
                        \ '3) Create a Python 3 tasks file']
        endif
        let l:choice = inputlist(l:text)
        if l:choice == 2
            let l:fileToCreate = l:tasksfile2
            let l:fileToDelete = l:tasksfile3
        elseif l:choice == 3
            let l:fileToCreate = l:tasksfile3
            let l:fileToDelete = l:tasksfile2
        else
            return
        endif
        if filereadable(l:fileToCreate) " We just want to keep the target file
            call delete(l:fileToDelete)
        elseif filereadable(l:fileToDelete) " copy source file to target file
            let l:previousWindow = winnr('#')
            let l:currentWindow = winnr()
            let l:cursorPos = getcurpos()
            call remove(l:cursorPos, 0)
            call rename(l:fileToDelete, l:fileToCreate)
            windo
                        \ if expand('%:p') == fnamemodify(l:fileToDelete, ':p')
                        \ | execute 'edit '.l:fileToCreate
                        \ | endif
            if l:previousWindow
                execute l:previousWindow.'wincmd w'
            endif
            execute l:currentWindow.'wincmd w'
            call cursor(l:cursorPos)
        else " create target file from scratch
            if l:choice == 2
                OP2edit
            else
                OP3edit
            endif
        endif
    elseif has('python')
        throw 'This build of Vim support only Python 2 plugins'
    elseif has('python3')
        throw 'This build of Vim support only Python 3 plugins'
    else
        throw 'This build of Vim does not support Python plugins'
    endif
endfunction

let s:YieldedCommandClass = {}
function! s:YieldedCommandClass.call(method, ...) dict
    let l:idx = self.idx
    let l:method = a:method
    execute s:apiEntryPointCommand(self.pythonVersion, 'call')
    return l:return
endfunction
function! s:YieldedCommandClass.tryCall(method, ...) dict
    let l:idx = self.idx
    let l:method = a:method
    execute s:apiEntryPointCommand(self.pythonVersion, 'try_call')
    return l:return
endfunction

function! omnipytent#_yieldedCommand(pythonVersion, idx)
    let l:obj = copy(s:YieldedCommandClass)
    let l:obj.pythonVersion = a:pythonVersion
    let l:obj.idx = a:idx
    return l:obj
endfunction

function! omnipytent#_typeMap(value)
    let l:type = type(a:value)
    if l:type == type([]) || l:type == type({})
        let l:type = map(copy(a:value), 'omnipytent#_typeMap(v:val)[1]')
    endif
    return [a:value, l:type]
endfunction

let s:nextFrameCommands = []
function! omnipytent#_addNextFrameCommand(yieldedCommand, method, args)
    call add(s:nextFrameCommands, [a:yieldedCommand, a:method, a:args])
endfunction
function! omnipytent#_runNextFrameCommands(...)
    while !empty(s:nextFrameCommands)
        let l:tup = remove(s:nextFrameCommands, 0)
        call call(l:tup[0].tryCall, [l:tup[1]] + l:tup[2], l:tup[0])
    endwhile
endfunction

silent! autocmd! omnipytent
augroup omnipytent
augroup END

if exists('*timer_start')
    try
        call timer_stop(s:timer)
        unlet s:timer
    catch
    endtry
    let s:timer = timer_start(0, function('omnipytent#_runNextFrameCommands'), {'repeat': -1})
else
    augroup omnipytent
        autocmd omnipytent CursorMoved * call omnipytent#_runNextFrameCommands()
        autocmd omnipytent CursorMovedI * call omnipytent#_runNextFrameCommands()
        autocmd omnipytent CursorHold * call omnipytent#_runNextFrameCommands()
        autocmd omnipytent CursorHoldI * call omnipytent#_runNextFrameCommands()
    augroup END
endif

let s:yieldedCommandForJobs = {}

function! omnipytent#_registerYieldedCommandForJob(jobId, yieldedCommand) abort
    let s:yieldedCommandForJobs[a:jobId] = a:yieldedCommand
endfunction

function! omnipytent#_unregisterYieldedCommandForJob(jobId) abort
    call remove(s:yieldedCommandForJobs, a:jobId)
endfunction

function! omnipytent#_nvimTerminalCallback(jobId, data, event) dict abort
    let l:yieldedCommand = get(s:yieldedCommandForJobs, a:jobId)
    if empty(l:yieldedCommand)
        return
    endif
    if a:event == 'stdout'
        echo l:yieldedCommand.tryCall('handle_text_output', 'stdout', a:data)
    elseif a:event == 'stderr'
        call l:yieldedCommand.tryCall('handle_text_output', 'stderr', a:data)
    else
        call l:yieldedCommand.tryCall('handle_exit')
        call omnipytent#_unregisterYieldedCommandForJob(a:jobId)
    endif
endfunction
