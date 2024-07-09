#include <microhttpd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>

enum MHD_Result answer(void *cls, struct MHD_Connection *con, const char *url,
		       const char *method, const char *version,
		       const char *data, size_t *data_size, void **req_cls)
{
	(void)cls;
	(void)url;
	(void)method;
	(void)version;
	(void)data;
	(void)data_size;
	(void)req_cls;

	const char *page = "<html><body>Hello, browser !</body></html>";
	struct MHD_Response *response;
	int ret;

	response = MHD_create_response_from_buffer(strlen(page), (void *)page,
						   MHD_RESPMEM_PERSISTENT);

	ret = MHD_queue_response(con, MHD_HTTP_OK, response);
	MHD_destroy_response(response);

	return ret;
}

int main(void)
{
	struct MHD_Daemon *daemon;
	daemon = MHD_start_daemon(MHD_USE_INTERNAL_POLLING_THREAD, PORT, NULL,
				  NULL, &answer, NULL, MHD_OPTION_END);

	if (!daemon)
		exit(1);

	getchar();
	MHD_stop_daemon(daemon);

	return 0;
}
