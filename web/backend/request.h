#ifndef REQUEST_H
#define REQUEST_H

#include <microhttpd.h>

/* Callback for handling any incoming HTTP request. */
enum MHD_Result handle_request(void *cls, struct MHD_Connection *con,
			       const char *url, const char *method,
			       const char *version, const char *data,
			       size_t *data_size, void **req_cls);

/* Callback for cleaning up resources used for replying to request. */
void cleanup_request(void *cls, struct MHD_Connection *con, void **req_cls,
		     enum MHD_RequestTerminationCode toe);

#endif
