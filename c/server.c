#include <microhttpd.h>
#include <json_object.h>
#include <json_tokener.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>

/* 16KB */
#define BUFSIZE (1 << 16)

/* Information regarding a request being currently processed.  For each
   request, a pointer to a coninfo structure is used by the handle_request
   and handle_chunk functions to process the request. */
struct coninfo {
	/* JSON parser */
	struct json_tokener *tok;
	/* answer to the request, non-NULL if processing is done */
	char *answer;
};

static enum MHD_Result handle_chunk(struct coninfo *coninfo, const char *data,
				    size_t data_size)
{
	printf("trace: %s\n", __func__);

	struct json_object *obj =
		json_tokener_parse_ex(coninfo->tok, data, data_size);

	if (obj) {
		char reply[128] = { 0 };
		int length = json_object_object_length(obj);
		json_object_put(obj);
		sprintf(reply, "Length of JSON object: %d\n", length);
		coninfo->answer = strdup(reply);

		if (!coninfo->answer)
			return MHD_NO;

		return MHD_YES;
	}

	if (json_tokener_get_error(coninfo->tok) != json_tokener_continue) {
		fprintf(stderr, "json_tokener_parse_ex: %s\n",
			json_tokener_error_desc(
				json_tokener_get_error(coninfo->tok)));
		return MHD_NO;
	}

	return MHD_NO;
}

static void cleanup_request(void *cls, struct MHD_Connection *con,
			    void **req_cls, enum MHD_RequestTerminationCode toe)
{
	printf("trace: %s\n", __func__);

	struct coninfo *coninfo = *req_cls;

	free(coninfo->answer);
	json_tokener_free(coninfo->tok);
	free(coninfo);
}

static struct coninfo *coninfo_init(void)
{
	struct coninfo *coninfo = calloc(1, sizeof(*coninfo));

	if (!coninfo) {
		perror("malloc");
		goto coninfo_init_err;
	}

	/* coninfo->buf = malloc(BUFSIZE); */

	/* if (!coninfo->buf) { */
	/* 	perror("malloc"); */
	/* 	goto coninfo_init_err; */
	/* } */

	coninfo->tok = json_tokener_new();

	if (!coninfo->tok) {
		fprintf(stderr, "%s: failed to initialize JSON tokener\n",
			__func__);
		goto coninfo_init_err;
	}

	return coninfo;

coninfo_init_err:
	/* if (coninfo->buf) */
	/* 	free(coninfo->buf); */

	if (coninfo)
		free(coninfo);

	return NULL;
}

/* Called several times per request. The first time, *REQ_CLS is NULL, the
   other times, it is set to what we set it to the first time, namely a
   pointer to a coninfo structure. */
static enum MHD_Result handle_request(void *cls, struct MHD_Connection *con,
				      const char *url, const char *method,
				      const char *version, const char *data,
				      size_t *data_size, void **req_cls)
{
	if (strcmp(method, "POST") != 0) {
		fprintf(stderr, "error: bad method (%s)\n", method);
		/* TODO: send error to client */
		return MHD_queue_response(con, MHD_HTTP_METHOD_NOT_ALLOWED,
					  NULL);
	}

	if (strcmp(url, "/") != 0) {
		fprintf(stderr, "error: bad URL (%s)\n", url);
		/* TODO: send error to client */
		return MHD_queue_response(con, MHD_HTTP_FORBIDDEN, NULL);
	}

	if (*req_cls == NULL) {
		/* first iteration */
		printf("info: initializing handler\n");

		struct coninfo *coninfo = coninfo_init();

		if (!coninfo) {
			fprintf(stderr, "%s: failed to initalize handler\n",
				__func__);
			return MHD_queue_response(
				con, MHD_HTTP_INTERNAL_SERVER_ERROR, NULL);
		}

		*req_cls = (void *)coninfo;
		return MHD_YES;
	}

	/* other iterations */
	printf("info: other iteration\n");
	struct coninfo *coninfo = *req_cls;

	if (*data_size != 0) {
		/* process chunk of data */
		printf("info: processing data chunk :\n");
		printf("==begin==\n");
		fwrite(data, 1, *data_size, stdout);
		printf("\n===end===\n");

		int ret = handle_chunk(coninfo, data, *data_size);

		if (ret == MHD_NO)
			return MHD_NO;

		*data_size = 0;
		return MHD_YES;
	} else if (coninfo->answer != NULL) {
		/* reply */
		printf("info: replying\n");

		int ret;
		struct MHD_Response *response = MHD_create_response_from_buffer(
			strlen(coninfo->answer), (void *)coninfo->answer,
			MHD_RESPMEM_PERSISTENT);

		ret = MHD_queue_response(con, MHD_HTTP_OK, response);
		MHD_destroy_response(response);

		return ret;
	}

	/* should never be reached */
	printf("error: fell through %s\n", __func__);
	return MHD_NO;
}

int main(void)
{
	struct MHD_Daemon *daemon;
	daemon = MHD_start_daemon(MHD_USE_INTERNAL_POLLING_THREAD, PORT, NULL,
				  NULL, &handle_request, NULL,
				  MHD_OPTION_NOTIFY_COMPLETED, &cleanup_request,
				  NULL, MHD_OPTION_END);

	if (!daemon)
		exit(1);

	printf("Listening on port %d\n", PORT);
	getchar();
	MHD_stop_daemon(daemon);

	return 0;
}
