CC ?= gcc
CFLAGS ?= -O2 -DNDEBUG
DEFAULT_PORT ?= 4444
CHATGPT_URL ?= \"https://api.openai.com/v1/chat/completions\"
DEFAULT_KEY_FILE ?= \"$(shell realpath ./default_key.txt)\"

CURL_CFLAGS ?= $(shell pkg-config --cflags libcurl)
CURL_LDFLAGS ?= $(shell pkg-config --libs libcurl)

MHD_CFLAGS = $(shell pkg-config --cflags libmicrohttpd)
MHD_LDFLAGS = $(shell pkg-config --libs libmicrohttpd)

JSON_CFLAGS = $(shell pkg-config --cflags json-c)
JSON_LDFLAGS = $(shell pkg-config --libs json-c)
LDFLAGS ?= 

SRC = server.c llm.c request.c prompt.c
OBJ = $(subst .c,.o,$(SRC))
__CFLAGS = -Wall -Wextra -Wno-unused-parameter -Wno-unused-variable -DDEFAULT_PORT=$(DEFAULT_PORT) -DCHATGPT_URL=$(CHATGPT_URL) -DDEFAULT_KEY_FILE=$(DEFAULT_KEY_FILE) -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE
__LDFLAGS =

ppp_server: $(OBJ)
	@echo -e "  LD\t$@"; $(CC) $(__LDFLAGS) $(CURL_LDFLAGS) $(MHD_LDFLAGS) $(JSON_LDFLAGS) $(LDFLAGS) -o $@ $^

%.o: %.c
	@echo -e "  CC\t$@"; $(CC) -c $(CFLAGS) $(__CFLAGS) $(CURL_CFLAGS) $(MHD_CFLAGS) $(JSON_CFLAGS) -o $@ $<

llm_tester: llm.o llm_tester.o
	@echo -e "  LD\t$@"; $(CC) $(LDFLAGS) $(__LDFLAGS) $(CURL_LDFLAGS) $(JSON_LDFLAGS) -o $@ $^

fmt:
	clang-format -i *.c *.h

ppp_code.tar.gz: $(SRC) Makefile
	tar czf $@ $^

dist: ppp_code.tar.gz

.PHONY: fmt dist
