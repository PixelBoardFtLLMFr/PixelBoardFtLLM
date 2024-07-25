#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "request.h"
#include "prompt.h"

static void print_usage(FILE *stream)
{
	fprintf(stream, "Usage: server [OPTIONS]\n");
	fprintf(stream, "OPTIONS:\n");
	fprintf(stream, "  -h, --help\t\t\tprint help and exit\n");
	fprintf(stream,
		"  -p, --port PORT\t\tlisten on port number PORT, defaults to %d\n",
		DEFAULT_PORT);
	fprintf(stream,
		"  -m, --max-requests MAX\tallow only MAXrequests per hour\n");
}

static void print_help(void)
{
	printf("Pixel Penguin Project a.k.a. PPP\n\n");
	print_usage(stdout);
	printf("\nCompiled with :\n");
	printf("  ChatGPT URL\t\t%s\n", CHATGPT_URL);
	printf("  Share Directory\t%s\n", SHAREDIR);
	printf("  Default Port\t\t%d\n", DEFAULT_PORT);
	printf("  Default Key File\t%s\n", DEFAULT_KEY_FILE);
}

int main(int argc, char *argv[])
{
	struct MHD_Daemon *daemon;
	const struct option opts[] = { { "help", no_argument, NULL, 'h' },
				       { "port", required_argument, NULL, 'p' },
				       { "max-requests", required_argument,
					 NULL, 'm' },
				       { NULL, 0, NULL, 0 } };
	int opt, ind, port = DEFAULT_PORT, max_requests = -1;

	while ((opt = getopt_long(argc, argv, ":hp:m:", opts, &ind)) != -1) {
		switch (opt) {
		case 'h':
			print_help();
			exit(EXIT_SUCCESS);
		/* TODO: implement maximum request */
		case 'p':
			port = atoi(optarg);
			break;
		default:
			print_usage(stderr);
			exit(EXIT_FAILURE);
		}
	}

	prompt_init();
	daemon = MHD_start_daemon(MHD_USE_INTERNAL_POLLING_THREAD, port, NULL,
				  NULL, &handle_request, NULL,
				  MHD_OPTION_NOTIFY_COMPLETED, &cleanup_request,
				  NULL, MHD_OPTION_END);

	if (!daemon) {
		fprintf(stderr, "%s: failed to initialize HTTP daemon\n",
			argv[0]);
		exit(1);
	}

	printf("Listening on port %d\n", port);
	getchar();
	prompt_destroy();
	MHD_stop_daemon(daemon);

	return EXIT_SUCCESS;
}
