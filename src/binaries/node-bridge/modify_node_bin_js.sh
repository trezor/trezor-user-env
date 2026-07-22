#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "Please supply the path to the file to modify"
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "Error: File '$1' not found."
  exit 1
fi

# Getting rid of USB import, which is not needed when we will spawn in with UDP argument
string_to_comment='^var import_usb[0-9]* ='
if grep -q "$string_to_comment" "$1"; then
  sed -i "/$string_to_comment/ s/^/\/\//" "$1"
  echo "Success: line matching '$string_to_comment' was commented out."
else
  echo "Error: no line matching '$string_to_comment' found in '$1'."
  exit 1
fi

# Replace if (isOriginAllowed) with if (true)
if grep -q "if (isOriginAllowed)" "$1"; then
  sed -i 's/if (isOriginAllowed)/if (true)/g' "$1"
  echo "Success: replaced 'if (isOriginAllowed)' with 'if (true)'."
else
  echo "Error: no line matching 'if (isOriginAllowed)' found in '$1'."
  exit 1
fi


# Replace bridge bind host from 127.0.0.1 to 0.0.0.0.
# This is a server-side bind choice so Docker/macOS host traffic can reach it.
# Client-side checks must still connect to a concrete host (127.0.0.1 or service DNS),
# not to 0.0.0.0.
if grep -q 'var ADDRESS = new import_url.URL("http://127.0.0.1")' "$1"; then
  sed -i 's|var ADDRESS = new import_url.URL("http://127.0.0.1")|var ADDRESS = new import_url.URL("http://0.0.0.0")|g' "$1"
  echo "Success: replaced 'var ADDRESS = new import_url.URL("http://127.0.0.1")' with 'var ADDRESS = new import_url.URL("http://0.0.0.0")'."
else
  echo "Error: no line matching 'var ADDRESS = new import_url.URL("http://127.0.0.1")' found in '$1'."
  exit 1
fi