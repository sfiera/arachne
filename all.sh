#!/bin/zsh

set -o errexit
set -o nounset

./arachne.py forum 15 17 23 24 25 33 34 64 88 90 102
./arachne.py addons ares avara cythera harry
