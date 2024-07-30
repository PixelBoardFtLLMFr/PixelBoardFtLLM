#!/bin/sh

# This script tests the server by invoking it multiple times and
# submitting several requests.

if [ ! -x "./ppp_server" ]
then
    echo 'error: the "./ppp_server" file does not exist or is not executable'
    exit 1
fi

port=5555

# Print the whole command before executing it. Since all the programs'
# outputs are suppressed, this allows seeing what is going on.
exec_cmd() {
    echo "$1"
    sh -c "$1"
}

exec_cmd "./ppp_server --help >/dev/null"
exec_cmd "./ppp_server -D >/dev/null 2>&1"
exec_cmd "./ppp_server --port $port -m 3 >ppp.log 2>ppp_err.log"
