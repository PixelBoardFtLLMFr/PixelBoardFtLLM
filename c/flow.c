#include <stdio.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <sys/queue.h>
#include <time.h>

#include "flow.h"

struct stamp {
	time_t s_date;
	SLIST_ENTRY(stamp) s_next;
};

SLIST_HEAD(stamp_slist, stamp);

struct client {
	in_port_t c_port;
	in_addr_t c_addr;
	struct stamp_slist c_stamplist;
	SLIST_ENTRY(client) c_next;
};

SLIST_HEAD(client_list, client);

static int max_requests = -1;
static struct client_list client_list;

void flow_init(int __max_requests)
{
	if (__max_requests < 0) {
		fprintf(stderr, "%s: invalid maximum number of requests (%d)\n",
			__func__, __max_requests);
		exit(EXIT_FAILURE);
	}

	max_requests = __max_requests;
	SLIST_INIT(&client_list);
}

void flow_destroy(void)
{
	
}

int flow_allow(struct sockaddr *clientaddr)
{

	return 1;
}
