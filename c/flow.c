#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/queue.h>
#include <time.h>

#include "flow.h"

#define CALL_LOOP 64

struct stamp {
	time_t s_date;
	TAILQ_ENTRY(stamp) s_next;
};

TAILQ_HEAD(stamp_slist, stamp);

struct client {
	/* in_port_t c_port; */
	in_addr_t c_addr;
	int c_stampcount;
	struct stamp_slist c_stamplist;
	TAILQ_ENTRY(client) c_next;
};

TAILQ_HEAD(client_list, client);

static int max_requests = -1;
static struct client_list client_list = { 0 };
/* cache for making fewer calls to time(2) */
static time_t now = 0;
/* trigger a cleaning every CALL_LOOP calls */
static int calls = 0;

/* Refresh the cached result of time(2). */
static void refresh_now(void)
{
	now = time(NULL);
}

/* Return non-zero if STAMP is considered outdated, i.e. was
   created more than an hour ago. */
static int stamp_gone(const struct stamp *stamp)
{
	return now >= stamp->s_date + 60 * 60;
}

static struct stamp *stamp_init(void)
{
	struct stamp *stamp = calloc(1, sizeof(*stamp));

	stamp->s_date = time(NULL);
	return stamp;
}

static void stamp_destroy(struct stamp *stamp)
{
	free(stamp);
}

/* Destroy all the outdated stamps CLIENT has, and update its stamp count. */
static void client_clear_stamps(struct client *client)
{
	struct stamp *stamp;

	refresh_now();

	while (client->c_stampcount > 0) {
		stamp = TAILQ_FIRST(&client->c_stamplist);

		if (stamp_gone(stamp)) {
			TAILQ_REMOVE(&client->c_stamplist, stamp, s_next);
			stamp_destroy(stamp);
			client->c_stampcount--;
		} else {
			break;
		}
	}
}

/* Give CLIENT a new stamp, regardless of the current number of stamps. */
static void client_add_stamp(struct client *client)
{
	struct stamp *stamp = stamp_init();

	TAILQ_INSERT_TAIL(&client->c_stamplist, stamp, s_next);
	client->c_stampcount++;
}

/* Create a new client corresponding to CLIENTADDR_IN
   and add it to client_list. */
static struct client *client_init(const struct sockaddr_in *clientaddr_in)
{
	struct client *client = calloc(1, sizeof(*client));

	client->c_addr = clientaddr_in->sin_addr.s_addr;
	TAILQ_INIT(&client->c_stamplist);

	TAILQ_INSERT_HEAD(&client_list, client, c_next);

	return client;
}

static void client_destroy(struct client *client)
{
	struct stamp *stamp;

	while (client->c_stampcount > 0) {
		stamp = TAILQ_FIRST(&client->c_stamplist);
		TAILQ_REMOVE(&client->c_stamplist, stamp, s_next);
		stamp_destroy(stamp);
		client->c_stampcount--;
	}

	free(client);
}

static void client_clear_all(void)
{
	struct client *client = TAILQ_FIRST(&client_list);

	while (client) {
		client_clear_stamps(client);

		if (client->c_stampcount == 0) {
			struct client *tmp = TAILQ_NEXT(client, c_next);
			TAILQ_REMOVE(&client_list, client, c_next);
			client_destroy(client);
			client = tmp;
		} else {
			client = TAILQ_NEXT(client, c_next);
		}
	}
}

/* Return non-zero if CLIENT matches the IPv4 address ADDR. */
static int client_matches(const struct client *client,
			  const struct sockaddr_in *addr)
{
	return client->c_addr == addr->sin_addr.s_addr;
}

/* If a client corresponding to the given address exists, return it, otherwise,
   create it and return it. */
static struct client *client_get(const struct sockaddr *clientaddr)
{
	struct sockaddr_in *clientaddr_in = (struct sockaddr_in *)clientaddr;
	struct client *client;
	int found = 0;

	if (clientaddr->sa_family != AF_INET) {
		fprintf(stderr, "%s: client with no IPv4\n", __func__);
		return NULL;
	}

	TAILQ_FOREACH(client, &client_list, c_next)
	{
		if (client_matches(client, clientaddr_in)) {
			found = 1;
			break;
		}
	}

	if (found)
		return client;

	return client_init(clientaddr_in);
}

void flow_init(int __max_requests)
{
	if (__max_requests < 0) {
		fprintf(stderr, "%s: invalid maximum number of requests (%d)\n",
			__func__, __max_requests);
		exit(EXIT_FAILURE);
	}

	max_requests = __max_requests;
	TAILQ_INIT(&client_list);
}

void flow_destroy(void)
{
	struct client *client;

	while (!TAILQ_EMPTY(&client_list)) {
		client = TAILQ_FIRST(&client_list);
		TAILQ_REMOVE(&client_list, client, c_next);
		client_destroy(client);
	}
}

int flow_allow(const struct sockaddr *clientaddr)
{
	struct client *client;

	calls = (calls+1)%CALL_LOOP;

	if (calls == 0) {
		client_clear_all();
		client = client_get(clientaddr);
	} else {
		client = client_get(clientaddr);
		client_clear_stamps(client);
	}

	if (!client)
		return -1;

	if (client->c_stampcount >= max_requests)
		return 0;

	client_add_stamp(client);
	return 1;
}
