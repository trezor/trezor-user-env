#!/usr/bin/env bash
set -e

HERE=$(dirname $(readlink -f $0))

FILE_NAME="bin.js"
FILE_LOCATION="$HERE/$FILE_NAME"
BRANCH="develop"
URL="https://dev.suite.sldev.cz/transport-bridge/$BRANCH/dist/$FILE_NAME"

# Downloading and modifying node bridge bin.js file
if ! curl -L "$URL" -o "$FILE_LOCATION"; then
	echo "Failed to download $FILE_NAME" >&2
	exit 1
fi
if ! "$HERE/modify_node_bin_js.sh" "$FILE_LOCATION"; then
	echo "Failed to modify $FILE_NAME" >&2
	exit 1
fi

# Downloading index.html file
FILE_NAME="ui/index.html"
FILE_LOCATION="$HERE/$FILE_NAME"
URL="https://dev.suite.sldev.cz/transport-bridge/$BRANCH/dist/$FILE_NAME"
mkdir -p "$HERE/ui"
if ! curl -L "$URL" -o "$FILE_LOCATION"; then
	echo "Failed to download $FILE_NAME" >&2
	exit 1
fi
