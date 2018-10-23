function! omnipytent#integration#fzf#finish(result) dict abort
    if type(a:result) == type([])
        let l:result = copy(a:result)
    else
        let l:result = [a:result]
    endif
    let l:indices = map(l:result, 'str2nr(split(v:val)[0])')
    call self.yieldedCommand.call('finish', l:indices)
endfunction
