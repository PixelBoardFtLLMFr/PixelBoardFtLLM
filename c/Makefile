DEFAULT_PORT ?= \"4444\"
CHATGPT_URL ?= \"https://api.openai.com/v1/chat/completions\"

CURL_CFLAGS ?= $(shell pkg-config --cflags libcurl)
CURL_LDFLAGS ?= $(shell pkg-config --libs libcurl)

MHD_CFLAGS = $(shell pkg-config --cflags libmicrohttpd)
MHD_LDFLAGS = $(shell pkg-config --libs libmicrohttpd)

JSON_CFLAGS = $(shell pkg-config --cflags json-c)
JSON_LDFLAGS = $(shell pkg-config --libs json-c)

CC ?= gcc
CFLAGS ?= -O2 -DNDEBUG
LDFLAGS ?=
PREFIX ?= $(HOME)/.local
SERVICEDIR ?= /etc/systemd/user
SHAREDIR ?= $(PREFIX)/share/ppp_server

SRC = server.c llm.c request.c prompt.c flow.c
OBJ = $(subst .c,.o,$(SRC))
TXT = angle_base.txt arm_example.txt arm_spec.txt eye.txt face.txt head_example.txt head_spec.txt height.txt leg_example.txt leg_spec.txt particle.txt 
__CFLAGS = -Wall -Wextra -Wno-unused-parameter -Wno-unused-variable -DDEFAULT_PORT=$(DEFAULT_PORT) -DCHATGPT_URL=$(CHATGPT_URL) -DDEFAULT_KEY_FILE=$(DEFAULT_KEY_FILE) -DSHAREDIR=\"$(SHAREDIR)\" -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE
DEFAULT_KEY_FILE ?= \"$(SHAREDIR)/default_key.txt\"
__LDFLAGS =

compile: ppp_server ppp_start.sh ppp.service

ppp_server: $(OBJ) tls/server.key tls/server.pem
	@printf "  LD\t$@\n"; $(CC) -o $@ $(OBJ) $(__LDFLAGS) $(CURL_LDFLAGS) $(MHD_LDFLAGS) $(JSON_LDFLAGS) $(LDFLAGS)

%.o: %.c
	@printf "  CC\t$@\n"; $(CC) -c $(CFLAGS) $(__CFLAGS) $(CURL_CFLAGS) $(MHD_CFLAGS) $(JSON_CFLAGS) -o $@ $<

llm_tester: llm.o llm_tester.o
	@printf "  LD\t$@\n"; $(CC) -o $@ $^ $(LDFLAGS) $(__LDFLAGS) $(CURL_LDFLAGS) $(JSON_LDFLAGS)

fmt:
	clang-format -i *.c *.h

ppp_code.tar.gz: $(SRC) Makefile $(TXT) ppp.service.in ppp_start.sh.in llm.h prompt.h request.h trace.h flow.h apt_deps.txt client.sh spammer.sh covtest.sh
	tar czf $@ $^

dist: ppp_code.tar.gz

tls:
	@mkdir -p $@

tls/server.key: tls
	@printf "  GEN\t$@\n"
	@test -f $@ || openssl genrsa -out $@ 1024

tls/server.pem: tls/server.key tls
	@printf "  GEN\t$@\n"
	@test -f $@ || openssl req -days 365 -out $@ -new -x509 -key $<

ppp_start.sh: ppp_start.sh.in
	@printf "  SED\t$@\n"; sed 's:@PREFIX@:$(PREFIX):g' <$< | sed 's:@HOME@:$(HOME):g' >$@

ppp.service: ppp.service.in
	@printf "  SED\t$@\n"; sed 's:@PREFIX@:$(PREFIX):g' <$< >$@

install: ppp_server ppp_start.sh $(TXT)
	mkdir -p $(PREFIX)/bin
	cp ppp_server $(PREFIX)/bin/
	mkdir -p $(PREFIX)/libexec
	cp ppp_start.sh $(PREFIX)/libexec/
	chmod +x $(PREFIX)/libexec/ppp_start.sh
	mkdir -p $(SHAREDIR)
	cp $(TXT) $(SHAREDIR)/
	cp -r ./tls $(SHAREDIR)/
	@printf "\n\n"
	@printf "Installation done. Make sure to copy the default ChatGPT API "
	@printf "key at\n$(DEFAULT_KEY_FILE).\nIf you happen to forget the "
	@printf "default key location, run \"ppp_server --help\".\n"

service_install: ppp.service
	cp ppp.service $(SERVICEDIR)/

uninstall:
	rm -rf $(PREFIX)/bin/ppp_server $(PREFIX)/libexec/ppp_start.sh $(SERVICEDIR)/ppp.service $(SHAREDIR)

clean:
	rm -rf ppp_server llm_tester ppp_start.sh ppp.service ppp_code.tar.gz *.o *.gcno *.gcov *.gcda tls 

.PHONY: fmt dist install compile clean install service_install uninstall
