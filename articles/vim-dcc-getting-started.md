---
title: "ddc.vimをdein.vimでインストールしてvimで補完が効くように設定する"
emoji: "📝"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["vim", "vimrc", "ddc", "dein"]
published: false
---

久々にdotfilesからvimの設定をしたら補完が効かなくなっていたので、最新のpluginに変更するなどしました。  
元々はneocomplete.vimを使っていたのですが、vim 8.2.1066までしか動かなくなっているみたいなので、最近のpluginであるddc.vimに移行することにしました。  

- https://github.com/Shougo/neocomplete.vim
- https://github.com/Shougo/ddc.vim

いつもの手元の環境は複雑になっているので、docker上にある空のubuntuにインストールしてみる手順をメモがてら書いています。  

# vimのインストール

https://github.com/vim/vim

## ubuntu22.04にソースコードからddcが使えるバージョンのvimをインストール

ubuntu22.04でapt installした際にvim8系が入ったり、PPAリポジトリを追加してもddcが使えるバージョンが入らなかったので、ソースコードからビルドしました。  
以下がDockerでビルドした手順です。  
特に意図はなく試した時点の最新リリースタグのv9.1.0304を使用しています。  
/optディレクトリにcloneし、ビルドしてPATHを通します。  

```sh
#docker run -ti ubuntu:22.04 bash

$apt update && apt upgrade -y
$apt install -y curl git unzip make build-essential
$cd /opt
$git clone --depth 1 https://github.com/vim/vim.git -b v9.1.0304 
$apt install -y libncurses-dev
$cd /opt/vim
$./configure --with-features=huge --prefix=/opt/vim
$make
$make install
$echo 'export PATH="/opt/vim/bin:$PATH"' >> ~/.bashrc
```

# dein.vimの設定

https://github.com/Shougo/dein.vim

## vim plugin managerのdein.vimをインストール

個人的にdein.vimをplugin managerとして使っていたので、思い出しがてら使っています。  


```sh
$curl -fsSL https://raw.githubusercontent.com/Shougo/dein-installer.vim/master/installer.sh > /opt/install.dein.vim.sh
$cd /root
$mkdir ./config
$sh /opt/install.dein.vim.sh --overwrite-config ./config/dein.vim --use-vim-config
```

## 自動生成されるvimrc +αの変更

pluginのリストをファイルで分割したり、ddcの設定を別ファイルに切り出したりしています。  
また、dein_base、dein_srcのパスがカレントディレクトからになっているとうまく動かなかったので、$HOMEからのパスに変更しています。  

```vim
" Ward off unexpected things that your distro might have made, as
" well as sanely reset options when re-sourcing .vimrc
set nocompatible

" [変更点] baseのPATHを./から~/に変更 
" Set Dein base path (required)
let s:dein_base = '~/config/dein.vim'

" Set Dein source path (required)
let s:dein_src = '~/config/dein.vim/repos/github.com/Shougo/dein.vim'

" Set Dein runtime path (required)
execute 'set runtimepath+=' . s:dein_src

" Call Dein initialization (required)
call dein#begin(s:dein_base)

call dein#add(s:dein_src)

" [変更点] pluginのリストを別ファイルに分離
" Your plugins go here:
source ./dein.plugins.vimrc

" Finish Dein initialization (required)
call dein#end()

" Attempt to determine the type of a file based on its name and possibly its
" contents. Use this to allow intelligent auto-indenting for each filetype,
" and for plugins that are filetype specific.
filetype indent plugin on

" Enable syntax highlighting
syntax enable

" Uncomment if you want to install not-installed plugins on startup.
if dein#check_install()
 call dein#install()
endif

" ddcの設定を変更する部分を別ファイルに分離
source ./ddc.vimrc
```

dein.plugins.vimrc

```vim
call dein#add('vim-denops/denops.vim')
call dein#add('Shougo/ddc.vim')
call dein#add('Shougo/ddc-around')
call dein#add('Shougo/ddc-matcher_head')
call dein#add('Shougo/ddc-sorter_rank')
call dein#add('Shougo/ddc-ui-pum')
call dein#add('Shougo/pum.vim')
```

# ddc.vimの設定

https://github.com/Shougo/ddc.vim

## 自動補完ライブラリのddc.vimの設定を追加

参考に載せた作者の記事からアップデートがいくつかあり、そのままだと動かなかったので、
上のpluginのインストールリストに `Shougo/ddc-ui-pum` を追加したり、下でuiの設定を記述したりしています。  
元々はcompletionMenuというオプションを使うとよかったみたいですが、2022/10/21のアップデートでuiというオプションを使うようになったみたいですね。  
https://github.com/Shougo/ddc.vim/blob/aea08e43b602fae21e103ab8217810dc29f93ea6/doc/ddc.txt#L1728-L1734  

## 依存のdenoをインストール

denoに依存しているらしいので、denoをインストールしてPATHを通しておきます。  
https://deno.com/

```sh
$curl -fsSL https://deno.land/x/install/install.sh | sh
$echo 'export PATH="/root/.deno/bin:$PATH"' >> ~/.bashrc
```

## pum.vimで補完する設定を追加

Tabで補完の次に行くようにしたりしています。  

```vim
call ddc#custom#patch_global('sources', ['around'])
call ddc#custom#patch_global('sourceOptions', {
            \ '_': {
            \   'matchers': ['matcher_head'],
            \   'sorters': ['sorter_rank'],
            \ },
            \ 'around': {
            \   'mark': 'A',
            \   'minAutoCompleteLength': 1,
            \ }
            \ })
call ddc#custom#patch_global(#{
            \   ui: 'pum',
            \   autoCompleteEvents: [
            \     'InsertEnter', 'TextChangedI', 'TextChangedP',
            \   ],
            \ })
call ddc#enable()

inoremap <Tab> <Cmd>call pum#map#insert_relative(+1)<CR>
inoremap <S-Tab> <Cmd>call pum#map#insert_relative(-1)<CR>
inoremap <expr> <CR> pumvisible() ? "\<C-y>" : "\<CR>"
```

# まとめ

まとめたコード類はこちら  
https://gist.github.com/ara-ta3/9e38a41dcbb0a0baeba11c7e98f4ed13  

## Dockerでのまとめ

gistに置いてある、vimrc、dein.plugins.vimrc、ddc.vimrcファイルがDockerfileと同じディレクトにある前提です。  

```dockerfile
FROM ubuntu:22.04
RUN apt update && apt upgrade -y
RUN apt install -y curl git unzip make build-essential
WORKDIR /opt
RUN git clone --depth 1 https://github.com/vim/vim.git -b v9.1.0304 
RUN apt install -y libncurses-dev
WORKDIR /opt/vim
RUN ./configure --with-features=huge --prefix=/opt/vim
RUN make
RUN make install
RUN echo 'export PATH="/opt/vim/bin:$PATH"' >> ~/.bashrc

WORKDIR /root
RUN curl -fsSL https://raw.githubusercontent.com/Shougo/dein-installer.vim/master/installer.sh > /opt/install.dein.vim.sh
RUN mkdir config
RUN sh /opt/install.dein.vim.sh --overwrite-config ./config/dein.vim --use-vim-config

RUN curl -fsSL https://deno.land/x/install/install.sh | sh
RUN echo 'export PATH="/root/.deno/bin:$PATH"' >> ~/.bashrc

COPY vimrc /root/.vimrc
COPY dein.plugins.vimrc /root/
COPY ddc.vimrc /root/
```

# 感想

- 久々にvim触ったら動かなくなってたので補完が効くようにした
    - 動いてよかった
- vim-lspなども動かせるのでもう少しカスタマイズしていきたい

## 参考

- https://zenn.dev/shougo/articles/ddc-vim-beta
- https://zenn.dev/shougo/articles/ddc-vim-pum-vim
