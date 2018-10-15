let s:uniteSource = {
            \ 'name': 'omnipytent_choice',
            \ 'hooks': {},
            \ }

function! s:uniteSource.gather_candidates(args, context) abort
    let l:cmd = a:context.omnipytent__yieldedCommand
    let l:source = l:cmd.call('get_source')
    for l:item in l:source
        let l:item.yieldedCommand = l:cmd
    endfor
    return l:source
endfunction

function! s:uniteSource.hooks.on_close(args, context) abort
    let l:cmd = a:context.omnipytent__yieldedCommand
    call l:cmd.call('finish')
endfunction

function! unite#sources#omnipytent_choice#define() abort
    return s:uniteSource
endfunction
