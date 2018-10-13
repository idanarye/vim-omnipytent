let s:uniteKind = {
            \ 'name': 'omnipytent',
            \ 'default_action': 'choose',
            \ 'action_table': {},
            \ }

let s:uniteKind.action_table.choose = {
            \ 'is_selectable': 1,
            \ }

function! s:uniteKind.action_table.choose.func(candidates) dict
    if !empty(a:candidates)
        let l:result = map(copy(a:candidates), 'v:val.word')
        call a:candidates[0].yieldedCommand.call('set_result', l:result)
    endif
endfunction

function! unite#kinds#omnipytent#define() abort
    return s:uniteKind
endfunction
