#ifndef FLOW_H
#define FLOW_H

#include <sys/socket.h>

/* Initialized a flow management with at most MAX_REQUESTS
   per hour and per client. */
void flow_init(int max_requests);

/* Free flow control resources. */
void flow_destroy(void);

/* Returns non-zero if the given client is allowed
   to perform a request. */
int flow_allow(struct sockaddr *clientaddr);

#endif
