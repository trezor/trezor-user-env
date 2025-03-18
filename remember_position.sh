#!/bin/bash

WINDOW_NAME="Trezor\^emu"

WINDOW_IDS=$(xdotool search --name "$WINDOW_NAME")
echo "Window IDs: $WINDOW_IDS"

for WINDOW_ID in $WINDOW_IDS; do
    NAME=$(xdotool getwindowname "$WINDOW_ID")
    echo "ID: $WINDOW_ID, Name: \"$NAME\""
    GEOMETRY=$(xdotool getwindowgeometry --shell $WINDOW_ID | grep -E 'X=|Y=')
    echo "$GEOMETRY"
done
