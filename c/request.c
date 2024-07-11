#include <json_object.h>
#include <json_tokener.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>

#include "request.h"
#include "prompt.h"
#include "llm.h"

/* 1KB */
#define BUFSIZE (1 << 10)

/* Information regarding a request being currently processed.  For each
   request, a pointer to a coninfo structure is used by the handle_request
   and handle_chunk functions to process the request. */
struct coninfo {
	/* JSON parser */
	struct json_tokener *tok;
	/* answer to the request, non-NULL if processing is done */
	char *answer;
	int http_status;
};

static enum MHD_Result handle_chunk(struct coninfo *coninfo, const char *data,
				    size_t data_size)
{
	printf("trace: %s\n", __func__);

	struct json_object *obj =
		json_tokener_parse_ex(coninfo->tok, data, data_size);

	if (obj) {
		printf("%s: parsing valid JSON\n", __func__);
		/* TODO: sanitize JSON input */
		/* TODO: send to LLM */
		char reply[128] = { 0 };
		int length = json_object_object_length(obj);
		json_object_put(obj);
		sprintf(reply, "Length of JSON object: %d\n", length);
		coninfo->answer = strdup(reply);
		coninfo->http_status = MHD_HTTP_OK;
		return MHD_YES;
	}

	if (json_tokener_get_error(coninfo->tok) != json_tokener_continue) {
		printf("%s: invalid JSON detected\n", __func__);
		const char *msg = json_tokener_error_desc(json_tokener_get_error(coninfo->tok));
		struct json_object *json_err = json_object_new_object();
		json_object_object_add(json_err, "error", json_object_new_string(msg));
		coninfo->answer = strdup(json_object_to_json_string(json_err));
		coninfo->http_status = MHD_HTTP_BAD_REQUEST;
		json_object_put(json_err);
		return MHD_NO;
	}

	return MHD_NO;
}

void cleanup_request(void *cls, struct MHD_Connection *con,
			    void **req_cls, enum MHD_RequestTerminationCode toe)
{
	printf("trace: %s\n", __func__);

	if (toe != MHD_REQUEST_TERMINATED_COMPLETED_OK) {
		printf("warning: connection error %d\n", toe);
	}

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
		return NULL;
	}

	coninfo->tok = json_tokener_new();

	if (!coninfo->tok) {
		fprintf(stderr, "%s: failed to initialize JSON tokener\n",
			__func__);
		free(coninfo);
		return NULL;
	}

	return coninfo;
}

static enum  MHD_Result reply_request(struct MHD_Connection *con,
				      struct coninfo *coninfo)
{
	printf("trace: %s\n", __func__);
	printf("%s: reply text '%s'\n", __func__, coninfo->answer);
	printf("%s: reply HTTP code '%d'\n", __func__, coninfo->http_status);

	int ret;
	struct MHD_Response *response = MHD_create_response_from_buffer(
		strlen(coninfo->answer), (void *)coninfo->answer,
		MHD_RESPMEM_PERSISTENT);

	ret = MHD_queue_response(con, coninfo->http_status, response);
	MHD_destroy_response(response);

	printf("trace: %s done\n", __func__);
	return ret;
}

/* Called several times per request. The first time, *REQ_CLS is NULL, the
   other times, it is set to what we set it to the first time, namely a
   pointer to a coninfo structure. */
enum MHD_Result handle_request(void *cls, struct MHD_Connection *con,
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

		handle_chunk(coninfo, data, *data_size);

		*data_size = 0;
		return MHD_YES;
	}

	if (coninfo->answer != NULL) {
		/* reply success */
		return reply_request(con, coninfo);
	}

	/* should never be reached */
	printf("error: fell through %s\n", __func__);
	return MHD_NO;
}
