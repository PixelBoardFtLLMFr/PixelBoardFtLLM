CC ?= gcc
CFLAGS ?= -O2
PORT ?= 4444
CURL_CFLAGS ?= $(shell pkg-config --cflags libcurl)
CURL_LDFLAGS ?= $(shell pkg-config --libs libcurl)
MHD_CFLAGS = $(shell pkg-config --cflags libmicrohttpd)
MHD_LDFLAGS = $(shell pkg-config --libs libmicrohttpd)
LDFLAGS ?= 

__CFLAGS = -Wall -Wextra -DPORT=$(PORT)
__LDFLAGS = 

server: server.o
	$(CC) $(__LDFLAGS) $(CURL_LDFLAGS) $(MHD_LDFLAGS) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) -c $(__CFLAGS) $(CURL_CFLAGS) $(MHD_CFLAGS) $(CFLAGS) -o $@ $<
