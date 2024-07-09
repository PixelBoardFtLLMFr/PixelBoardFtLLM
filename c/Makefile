CC ?= gcc
CFLAGS ?= -O2 -DNDEBUG
PORT ?= 4444
CHATGPT_URL ?= \"https://api.openai.com/v1/chat/completions\"

CURL_CFLAGS ?= $(shell pkg-config --cflags libcurl)
CURL_LDFLAGS ?= $(shell pkg-config --libs libcurl)

MHD_CFLAGS = $(shell pkg-config --cflags libmicrohttpd)
MHD_LDFLAGS = $(shell pkg-config --libs libmicrohttpd)

JSON_CFLAGS = $(shell pkg-config --cflags json-c)
JSON_LDFLAGS = $(shell pkg-config --libs json-c)
LDFLAGS ?= 

__CFLAGS = -Wall -Wextra -DPORT=$(PORT) -DCHATGPT_URL=$(CHATGPT_URL) -D_POSIX_C_SOURCE=200809L
__LDFLAGS = 

server: server.o llm.o
	$(CC) $(__LDFLAGS) $(CURL_LDFLAGS) $(MHD_LDFLAGS) $(JSON_LDFLAGS) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) -c $(__CFLAGS) $(CURL_CFLAGS) $(MHD_CFLAGS) $(JSON_CFLAGS) $(CFLAGS) -o $@ $<

llm_tester: llm.o llm_tester.o
	$(CC) $(__LDFLAGS) $(CURL_LDFLAGS) $(JSON_LDFLAGS) $(LDFLAGS) -o $@ $^

fmt:
	clang-format -i *.c *.h

.PHONY: fmt
