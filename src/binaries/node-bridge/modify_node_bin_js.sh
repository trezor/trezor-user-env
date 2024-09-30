#!/bin/bash

if [ -z "$1" ]; then
  echo "Please supply the path to the file to modify"
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "Error: File '$1' not found."
  exit 1
fi

# Getting rid of USB import, which is not needed when we will spawn in with UDP argument
string_to_comment='^var import_usb ='
if grep -q "$string_to_comment" "$1"; then
  sed -i "/$string_to_comment/ s/^/\/\//" "$1"
  echo "Success: line matching '$string_to_comment' was commented out."
else
  echo "Error: no line matching '$string_to_comment' found in '$1'."
  exit 1
fi
