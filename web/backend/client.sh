#!/bin/sh

# This scrit sends requests to the server in order to test it.

port=5555

# Send an HTTP request and verify the HTTP response's status.
request_assert_status() {
    cmd="curl --output /dev/null --silent --insecure -w %{http_code}\\n --data $1 https://localhost:$port/"
    # manually print the whole command
    echo "$cmd"
    status=$($cmd)
    # echo "debug: status=$status"

    if [ ! "$status" = "$2" ]
    then
	echo "error: expected HTTP status $2, received $status"
	exit 1
    fi
}

# Print the whole command before executing it. Since all the programs'
# outputs are suppressed, this allows seeing what is going on.
exec_cmd() {
    echo "$1"
    sh -c "$1"
}

# wrong method
exec_cmd "curl --silent --insecure --output /dev/null https://localhost:$port/"
# wrong endpoint
exec_cmd "curl --silent --insecure --data test https://localhost:$port/bad/url"
# OPTIONS request
exec_cmd "curl --insecure -X OPTIONS https://localhost:$port/"
# missing input
request_assert_status \{\} 400
# incomplete JSON
request_assert_status \{ 400
# missing key
request_assert_status \{\"input\":\"\"\} 400
# invalid key
request_assert_status \{\"input\":\"\",\"key\":\"invalid_key\"\} 400
# valid requests
request_assert_status \{\"input\":\"dance\",\"key\":\"\"\} 200
request_assert_status \{\"input\":\"love\",\"key\":\"\"\} 200
request_assert_status \{\"input\":\"fly\",\"key\":\"\"\} 200
# maximum number of requests reached
request_assert_status \{\"input\":\"fly\",\"key\":\"\"\} 400
