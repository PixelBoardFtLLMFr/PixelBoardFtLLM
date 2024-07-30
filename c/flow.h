#ifndef FLOW_H
#define FLOW_H

#include <sys/socket.h>

/* Initialized a flow management with at most MAX_REQUESTS
   per hour and per client. */
void flow_init(int max_requests);

/* Free flow control resources. */
void flow_destroy(void);

/* Returns zero if the given client is not allowed to perform a request,
   a positive number if it is allowed, and a negative number if an error
   occured. */
int flow_allow(const struct sockaddr *clientaddr);

#endif
