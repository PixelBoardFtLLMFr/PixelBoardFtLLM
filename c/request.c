#include <json_object.h>
#include <json_tokener.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdarg.h>

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

/* Create a JSON object of the form {"error": MSG}. */
static struct json_object *json_error(const char *msg)
{
	struct json_object *obj = json_object_new_object();
	struct json_object *txt = json_object_new_string(msg);
	json_object_object_add(obj, "error", txt);
	return obj;
}


/* Verify the content of the json object OBJ. */
static enum MHD_Result process_request(struct coninfo *coninfo,
				       struct json_object *obj)
{
	/* TODO: send to LLM */
	printf("%s: processing valid JSON\n", __func__);

	struct json_object *input;
	json_bool ret;

	ret = json_object_object_get_ex(obj, "input", &input);

	if (!ret) {
		struct json_object *json_err = json_error("the given JSON object does not have an 'input' value");
		coninfo->http_status = MHD_HTTP_BAD_REQUEST;
		coninfo->answer = strdup(json_object_to_json_string(json_err));
		json_object_put(json_err);
		json_object_put(obj);
		return MHD_NO;
	}

	/* char reply[128] = { 0 }; */
	/* int length = json_object_object_length(obj); */
	/* json_object_put(obj); */
	/* sprintf(reply, "Length of JSON object: %d\n", length); */
	/* coninfo->answer = strdup(reply); */
	/* coninfo->http_status = MHD_HTTP_OK; */
	exit(2);

	return MHD_YES;
}

/* Handle the chunks of data. Only take care of the JSON
   parsing, not of the JSON content. */
static enum MHD_Result handle_chunk(struct coninfo *coninfo, const char *data,
				    size_t data_size)
{
	printf("trace: %s\n", __func__);

	struct json_object *obj =
		json_tokener_parse_ex(coninfo->tok, data, data_size);

	if (obj)
		return process_request(coninfo, obj);

	if (json_tokener_get_error(coninfo->tok) != json_tokener_continue) {
		printf("%s: invalid JSON detected\n", __func__);
		struct json_object *json_err =
			json_error(json_tokener_error_desc(
				json_tokener_get_error(coninfo->tok)));
		coninfo->answer = strdup(json_object_to_json_string(json_err));
		coninfo->http_status = MHD_HTTP_BAD_REQUEST;
		json_object_put(json_err);
		return MHD_NO;
	}

	return MHD_NO;
}

void cleanup_request(void *cls, struct MHD_Connection *con, void **req_cls,
		     enum MHD_RequestTerminationCode toe)
{
	printf("trace: %s\n", __func__);

	if (toe != MHD_REQUEST_TERMINATED_COMPLETED_OK) {
		printf("warning: connection error %d\n", toe);
	}

	struct coninfo *coninfo = *req_cls;

	if (!coninfo) {
		printf("warning: cleaning up a connection that has no coninfo\n");
		return;
	}

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

/* Reply to the pending request of CON, using the answer and the
   HTTP status of CONINFO. */
static enum MHD_Result reply_request(struct MHD_Connection *con,
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

/* Reply to the pending request of CON. No coninfo
   has to be associated with it yet. */
static enum MHD_Result reply_request_error(struct MHD_Connection *con,
					   const char *fmt, ...)
{
	va_list ap;
	int ret;
	struct json_object *json_err;
	char msg[512], *json_msg;

	printf("trace: %s\n", __func__);

	va_start(ap, fmt);
	vsprintf(msg, fmt, ap);

	json_err = json_error(msg);
	json_msg = strdup(json_object_to_json_string_ext(
		json_err, JSON_C_TO_STRING_NOSLASHESCAPE));
	json_object_put(json_err);

	struct MHD_Response *response = MHD_create_response_from_buffer(
		strlen(json_msg), (void *)json_msg, MHD_RESPMEM_MUST_FREE);

	ret = MHD_queue_response(con, MHD_HTTP_BAD_REQUEST, response);
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
		return reply_request_error(con, "bad method (%s)", method);
	}

	if (strcmp(url, "/") != 0) {
		return reply_request_error(con, "bad URL (%s)", url);
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
