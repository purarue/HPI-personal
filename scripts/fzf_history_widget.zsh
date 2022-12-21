# override the CTRL+R widget using my hpi zsh history
# combines/merges (w/ a cache) zsh history from all my machines

# this assumes you've already sourced the fzf key-bindings.zsh file
# (e.g. at /usr/share/fzf/key-bindings.zsh)
# See https://github.com/junegunn/fzf:

fzf-history-widget() {
	local selected num
	setopt localoptions noglobsubst noposixbuiltins pipefail no_aliases 2>/dev/null
	selected="$(fc-all-zsh-history | awk '{ cmd=$0; sub(/^[ \t]*[0-9]+\**[ \t]+/, "", cmd); if (!seen[cmd]++) print $0 }' |
    FZF_DEFAULT_OPTS="--height ${FZF_TMUX_HEIGHT:-40%} ${FZF_DEFAULT_OPTS-} -n2..,.. --scheme=history --bind=ctrl-r:toggle-sort,ctrl-z:ignore ${FZF_CTRL_R_OPTS} --query=${(qqq)LBUFFER} +m" $(__fzfcmd))"
	local ret=$?
	if [[ -n "$selected" ]]; then
		# use jq -r to expand newlines
		BUFFER="$(jq -r <<<"$selected")"
	fi
	zle end-of-line
	zle reset-prompt
	return $ret
}
zle     -N             fzf-cd-widget
bindkey -M emacs '\ec' fzf-cd-widget
bindkey -M vicmd '\ec' fzf-cd-widget
bindkey -M viins '\ec' fzf-cd-widget
