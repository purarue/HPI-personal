#!/usr/bin/env bash
# These should work with both bash and zsh
#
# To use these, put 'source /path/to/this/repo/functions.sh'
# in your shell profile

#############
# my.albums
#############

alias albums-history='hpi query my.nextalbums.history'
alias albums-to-listen='hpi query my.nextalbums.to_listen'
# how many albums I have on my list that I havent listened to yet
alias albums-left='albums-to-listen | jq length'
# pipe a list of album blobs to this to describe them
albums-describe() {
	jq -r '"\(.cover_artists) - \(.album_name) (\(.year))"'
}
albums-describe-score() {
	jq -r '"[\(.score) | \(.listened_on)] \(.cover_artists) - \(.album_name) (\(.year))"'
}
# any albums which I can't find/have to order physical copies for to listen to
alias albums-cant-find="hpi query -s my.nextalbums._albums | jq -r 'select(.note==\"cant find\")' | albums-describe"
# list any albums I have yet to listen to, sorted by how many awards they've won
albums-awards() {
	local COUNT="${1:-10}"
	albums-to-listen | jq -r "sort_by(.reasons | length) | reverse | .[0:${COUNT}] | .[] | \"[\(.reasons | length)] \(.album_name) - \(.cover_artists) (\(.year))\""
}
# just the next albums I should listen to chronologically
albums-next() {
	local args=('-s')
	if [[ -n "$1" ]]; then
		args+=('-l' "${1}")
	fi
	albums-to-listen "${args[@]}" | albums-describe
}
alias albums-history-desc='albums-history -s | albums-describe-score'
alias albums-to-listen-desc='albums-next'

########################
# my.location.where_db
########################

alias where_db='python3 -m my.location.where_db'
_wq() {
	local -a args=()
	args+=(-o plain -o google_url)
	wait-for-internet --timeout 1 && args+=(-o geolocate)
	where_db query "$@" "${args[@]}"
}

wq() {
	_wq "$*"
}

alias wq-now='_wq --use-location "$(last-gps-location)" now'

# https://github.com/seanbreckenridge/mapscii-at
wq-mapscii() {
	local data
	data="$(where_db query "$*" -o plain)" || return $?
	mapscii-at "$data" --zoom 12
}

###########
# my.mal
###########

mal() {
	local -a args=(--order-type datetime --reverse)
	if [[ -n "$1" ]]; then
		args+=("$@")
	else
		args+=(--limit 100)
	fi
	hpi query my.mal.export.episodes -s "${args[@]}" | jq -s -r 'reverse | .[] | "\(.at)\t\(.title)\t\(.episode)"' | localize-datetimes | awk 'BEGIN { FS="\t" } {print "# " $2 "\n" $1 " - Episode " $3 }' | glow
}
