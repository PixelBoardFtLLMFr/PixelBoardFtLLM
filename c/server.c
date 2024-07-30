#include <getopt.h>
#include <netdb.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include "flow.h"
#include "prompt.h"
#include "request.h"
#include "trace.h"

#define TLSKEYFILE SHAREDIR "/tls/server.key"
#define TLSCERTFILE SHAREDIR "/tls/server.pem"

struct server {
	/* epoll(7) main file descriptor */
	int epfd;
	/* listening socket file descriptor */
	int sockfd;
	/* listening port */
	int port;
	/* daemon that manages requests */
	struct MHD_Daemon *daemon;
	/* TLS */
	char *key_pem;
	char *cert_pem;
};

static struct server server = { 0 };
extern char *default_key;

static void print_usage(FILE *stream)
{
	fprintf(stream, "Usage: server [OPTIONS]\n");
	fprintf(stream, "OPTIONS:\n");
	fprintf(stream, "  -h, --help\t\t\tprint help and exit\n");
	fprintf(stream,
		"  -p, --port PORT\t\tlisten on port number PORT, defaults to %s\n",
		DEFAULT_PORT);
	fprintf(stream,
		"  -m, --max-requests MAX\tallow only MAX requests per hour, \
defaults to 20\n");
}

static void print_help(void)
{
	printf("Pixel Penguin Project a.k.a. PPP\n\n");
	print_usage(stdout);
	printf("\nCompiled with :\n");
	printf("  ChatGPT URL\t\t%s\n", CHATGPT_URL);
	printf("  Share Directory\t%s\n", SHAREDIR);
	printf("  Default Port\t\t%s\n", DEFAULT_PORT);
	printf("  Default Key File\t%s\n", DEFAULT_KEY_FILE);
}

static void epoll_add_fd(int fd)
{
	int ret;
	struct epoll_event epevent = { 0 };

	epevent.events = EPOLLIN;
	epevent.data.fd = fd;

	ret = epoll_ctl(server.epfd, EPOLL_CTL_ADD, fd, &epevent);

	if (ret == -1) {
		perror("epoll_ctl");
		close(fd);
		exit(EXIT_FAILURE);
	}
}

static void server_destroy(void)
{
	prompt_destroy();
	flow_destroy();

	if (default_key)
		free(default_key);

	if (server.sockfd)
		close(server.sockfd);

	if (server.epfd)
		close(server.epfd);

	if (server.daemon)
		MHD_stop_daemon(server.daemon);

	if (server.key_pem)
		free(server.key_pem);

	if (server.cert_pem)
		free(server.cert_pem);
}

/* Return a heap-allocated string having the content of PATH,
   or NULL if an error occurred. */
static char *load_file(const char *path)
{
	FILE *stream = fopen(path, "r");
	char buf[1 << 16] = { 0 };

	if (!stream)
		goto load_file_err;

	fread(buf, 1, sizeof(buf) - 1, stream);

	if (!feof(stream))
		goto load_file_err;

	fclose(stream);
	return strdup(buf);

load_file_err:
	perror(path);

	if (stream)
		fclose(stream);

	return NULL;
}

static void server_init(const char *port)
{
	server.sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (server.sockfd == -1) {
		perror("socket");
		server_destroy();
		exit(EXIT_FAILURE);
	}

	int ret;
	int bind_done = 0;
	struct addrinfo *result, *rp;
	struct addrinfo hints = { 0 };
	hints.ai_flags = AI_PASSIVE;
	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_STREAM;

	ret = getaddrinfo(NULL, port, &hints, &result);

	if (ret != 0) {
		fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(ret));
		server_destroy();
		exit(EXIT_FAILURE);
	}

	for (rp = result; rp != NULL; rp = rp->ai_next) {
		ret = bind(server.sockfd, rp->ai_addr, rp->ai_addrlen);

		if (ret == 0) {
			bind_done = 1;
			break;
		}
	}

	freeaddrinfo(result);

	if (!bind_done) {
		fprintf(stderr, "bind: failure, try using another port\n");
		server_destroy();
		exit(EXIT_FAILURE);
	}

	ret = listen(server.sockfd, 4);

	if (ret == -1) {
		perror("listen");
		server_destroy();
		exit(EXIT_FAILURE);
	}

	printf("Listening on port %s\n", port);

	server.epfd = epoll_create(1);

	if (server.epfd == -1) {
		perror("epoll_create");
		server_destroy();
		exit(EXIT_FAILURE);
	}

	epoll_add_fd(server.sockfd);

	server.key_pem = load_file(TLSKEYFILE);
	server.cert_pem = load_file(TLSCERTFILE);

	if ((!server.key_pem) || (!server.cert_pem)) {
		server_destroy();
		exit(EXIT_FAILURE);
	}

	/* clang-format off */
	server.daemon = MHD_start_daemon(MHD_USE_EPOLL
					 | MHD_USE_NO_LISTEN_SOCKET
					 | MHD_USE_TLS,
					 atoi(port),
					 NULL, NULL,
					 &handle_request, NULL,
					 MHD_OPTION_NOTIFY_COMPLETED,
					 &cleanup_request, NULL,
					 MHD_OPTION_HTTPS_MEM_KEY, server.key_pem,
					 MHD_OPTION_HTTPS_MEM_CERT, server.cert_pem,
					 MHD_OPTION_END);
	/* clang-format on */

	if (!server.daemon) {
		fprintf(stderr, "MHD_start_daemon: initialization failed\n");
		server_destroy();
		exit(EXIT_FAILURE);
	}
}

static void new_connection(void)
{
	int clientfd;
	struct sockaddr clientaddr;
	socklen_t clientaddrlen = sizeof(clientaddr);

	TRACE;
	clientfd = accept(server.sockfd, &clientaddr, &clientaddrlen);

	if (clientfd == -1) {
		perror("accept");
		server_destroy();
		exit(EXIT_FAILURE);
	}

	epoll_add_fd(clientfd);
	MHD_add_connection(server.daemon, clientfd, &clientaddr, clientaddrlen);
}

static void handle_data(struct epoll_event *epevent)
{
	TRACE;
	MHD_run(server.daemon);
}

static void server_loop(void)
{
	int fdcount;
	struct epoll_event epevent;

	while (1) {
		fdcount = epoll_wait(server.epfd, &epevent, 1, -1);

		if (fdcount <= 0)
			break;

		if (epevent.data.fd == server.sockfd)
			new_connection();
		else
			handle_data(&epevent);
	}

	server_destroy();

	if (fdcount == -1) {
		perror("epoll_wait");
		server_destroy();
		exit(EXIT_FAILURE);
	}

	exit(EXIT_SUCCESS);
}

/* Very basic--not to say useless--signal management, mainly for making
   Valgrind happy during tests. */
static void handle_sigint(int signum)
{
	printf("%s received, exiting\n", strsignal(signum));
	server_destroy();
	exit(EXIT_SUCCESS);
}

static void sighandler_init(void)
{
	struct sigaction act;

	sigaction(SIGINT, NULL, &act);
	act.sa_handler = handle_sigint;
	sigaction(SIGINT, &act, NULL);
}

int main(int argc, char *argv[])
{
	char *port = DEFAULT_PORT;
	int opt, ind;
	int max_requests = 20;
	const struct option opts[] = { { "help", no_argument, NULL, 'h' },
				       { "port", required_argument, NULL, 'p' },
				       { "max-requests", required_argument,
					 NULL, 'm' },
				       { NULL, 0, NULL, 0 } };

	while ((opt = getopt_long(argc, argv, ":hp:m:", opts, &ind)) != -1) {
		switch (opt) {
		case 'h':
			print_help();
			exit(EXIT_SUCCESS);
		case 'm':
			max_requests = atoi(optarg);
			break;
		case 'p':
			port = optarg;
			break;
		default:
			print_usage(stderr);
			exit(EXIT_FAILURE);
		}
	}

	prompt_init();
	flow_init(max_requests);
	server_init(port);
	sighandler_init();
	server_loop();
	/* should not be reached */
	return EXIT_FAILURE;
}
