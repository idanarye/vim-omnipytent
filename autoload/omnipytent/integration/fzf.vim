function! omnipytent#integration#fzf#finish(result) dict abort
    let l:indices = map(copy(a:result), 'str2nr(split(v:val)[0])')
    call self.yieldedCommand.call('finish', l:indices)
endfunction
