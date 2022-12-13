# override the CTRL+R widget using my hpi zsh history
# combines/merges (w/ a cache) zsh history from all my machines

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
