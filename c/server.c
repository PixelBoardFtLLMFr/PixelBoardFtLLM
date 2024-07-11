#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "request.h"

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
			print_usage(stdout);
			exit(EXIT_SUCCESS);
		case 'p':
			port = atoi(optarg);
			break;
		default:
			print_usage(stderr);
			exit(EXIT_FAILURE);
		}
	}

	daemon = MHD_start_daemon(MHD_USE_INTERNAL_POLLING_THREAD, port, NULL,
				  NULL, &handle_request, NULL,
				  MHD_OPTION_NOTIFY_COMPLETED, &cleanup_request,
				  NULL, MHD_OPTION_END);

	if (!daemon)
		exit(1);

	printf("Listening on port %d\n", port);
	getchar();
	MHD_stop_daemon(daemon);

	return EXIT_SUCCESS;
}
