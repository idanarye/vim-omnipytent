" Load guard
if ( exists('g:loaded_ctrlp_omnipytent') && g:loaded_ctrlp_omnipytent )
    \ || v:version < 700 || &cp
    finish
endif
let g:loaded_ctrlp_omnipytent = 1

call add(g:ctrlp_ext_vars, {
    \ 'init': 'ctrlp#omnipytent#init()',
    \ 'accept': 'ctrlp#omnipytent#accept',
    \ 'type': 'line',
    \ 'opmul': 0,
    \ })


" Provide a list of strings to search in
"
" Return: a Vim's List
"
function! ctrlp#omnipytent#init()
    return s:yieldedCommand.call('get_source')
endfunction

function! ctrlp#omnipytent#accept(mode, str)
    call ctrlp#exit()
    let l:yieldedCommand = s:yieldedCommand
    unlet s:yieldedCommand
    call l:yieldedCommand.call('finish', a:str)
endfunction

function! ctrlp#omnipytent#remove(entries)
    throw 'bad bad bad'
endfunction

let s:id = g:ctrlp_builtins + len(g:ctrlp_ext_vars)

function! ctrlp#omnipytent#start(yieldedCommand)
    let s:yieldedCommand = a:yieldedCommand
    call ctrlp#init(s:id)
endfunction
