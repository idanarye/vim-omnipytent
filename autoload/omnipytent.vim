function! s:runPythonCommands(pythonVersion, ...)
    for l:command in a:000
        if a:pythonVersion == 2
            execute 'python '.l:command
        else
            throw 'Unknown Python version '.a:pythonVersion
        endif
    endfor
endfunction

let s:modulePath = fnameescape(expand('<sfile>:p:h'))
function! s:updatePythonSysPath(pythonVersion)
    call s:runPythonCommands(a:pythonVersion,
                \ 'if "'.s:modulePath.'" not in sys.path: sys.path.append("'.s:modulePath.'")',
                \ 'import omnipytent.vim_plugin',
                \ )
endfunction

if has('python')
    call s:updatePythonSysPath(2)
endif

function! s:guessPythonVersion()
    return 2
endfunction

function! omnipytent#invoke(pythonVersion, line1, line2, count, ...)
    let l:pythonVersion = a:pythonVersion
    if l:pythonVersion == 0
        let l:pythonVersion = s:guessPythonVersion()
    endif

    if l:pythonVersion == 2
        python omnipytent.vim_plugin._api_entry_point('invoke')
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#editTask(pythonVersion, splitMode, ...)
    let l:pythonVersion = a:pythonVersion
    if l:pythonVersion == 0
        let l:pythonVersion = s:guessPythonVersion()
    endif

    if l:pythonVersion == 2
        python omnipytent.vim_plugin._api_entry_point('edit')
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#complete(argLead, cmdLine, cursorPos)
    let l:pythonVersion = s:guessPythonVersion()
    if l:pythonVersion == 2
        return omnipytent#complete2(a:argLead, a:cmdLine, a:cursorPos)
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#complete2(argLead, cmdLine, cursorPos)
    return pyeval('omnipytent.vim_plugin._api_complete(include_task_args=False)')
endfunction

function! omnipytent#completeIncludeTaskArgs(argLead, cmdLine, cursorPos)
    let l:pythonVersion = s:guessPythonVersion()
    if l:pythonVersion == 2
        return omnipytent#complete2IncludeTaskArgs(a:argLead, a:cmdLine, a:cursorPos)
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#complete2IncludeTaskArgs(argLead, cmdLine, cursorPos)
    return pyeval('omnipytent.vim_plugin._api_complete(include_task_args=True)')
endfunction
