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

function! omnipytent#invoke(pythonVersion, count, ...) range
    let l:pythonVersion = a:pythonVersion
    if l:pythonVersion == 0
        let l:pythonVersion = s:guessPythonVersion()
    endif

    if l:pythonVersion == 2
        python omnipytent.vim_plugin._vim_api('invoke')
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction

function! omnipytent#editTask(pythonVersion, ...)
    let l:pythonVersion = a:pythonVersion
    if l:pythonVersion == 0
        let l:pythonVersion = s:guessPythonVersion()
    endif

    if l:pythonVersion == 2
        python omnipytent.vim_plugin._vim_api('edit')
    else
        throw 'Unknown Python version '.a:pythonVersion
    endif
endfunction
