let s:uniteKind = {
            \ 'name': 'omnipytent_choice',
            \ 'default_action': 'choose',
            \ 'action_table': {},
            \ }

let s:uniteKind.action_table.choose = {
            \ 'is_selectable': 1,
            \ }

function! s:uniteKind.action_table.choose.func(candidates) dict
    if !empty(a:candidates)
        let l:result = map(copy(a:candidates), 'v:val.idx')
        call a:candidates[0].yieldedCommand.call('set_result', l:result)
    endif
endfunction

function! unite#kinds#omnipytent_choice#define() abort
    return s:uniteKind
endfunction

let s:uniteKind.action_table.preview = {
      \ 'description' : 'preview omnipytent choice',
      \ 'is_quit' : 0,
      \ }
function! s:uniteKind.action_table.preview.func(candidate) abort dict "{{{
  let l:previewFile = a:candidate.yieldedCommand.call('create_preview_file', a:candidate.idx)
  call unite#view#_preview_file(l:previewFile)
endfunction
