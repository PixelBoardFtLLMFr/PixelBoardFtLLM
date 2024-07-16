#include <json_object.h>
#include <json_tokener.h>
#include <linkhash.h>
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

struct array_dim {
	int width;
	int height;
	enum json_type type;
};

/* Create a JSON object of the form {"error": MSG}. */
static struct json_object *json_error(const char *msg)
{
	struct json_object *obj = json_object_new_object();
	struct json_object *txt = json_object_new_string(msg);
	json_object_object_add(obj, "error", txt);
	return obj;
}

/* Read the file containing the default key and return it. The returned
   string is heap-allocated. */
static char *get_default_key(void)
{
	char *key = NULL;
	size_t key_size = 0;
	ssize_t bytes_read;
	FILE *stream;

	stream = fopen(DEFAULT_KEY_FILE, "r");

	if (!stream) {
		perror(DEFAULT_KEY_FILE);
		exit(EXIT_FAILURE);
	}

	bytes_read = getline(&key, &key_size, stream);

	if (bytes_read == -1) {
		perror(DEFAULT_KEY_FILE);
		fclose(stream);
		exit(EXIT_FAILURE);
	}

	if (bytes_read < 2) {
		fprintf(stderr, "getline: suspicious key length (%zu)\n",
			bytes_read);
		fclose(stream);
		exit(EXIT_FAILURE);
	}

	key[bytes_read - 1] = '\0';
	fclose(stream);

	return key;
}

static void forward_llm_error(struct coninfo *coninfo,
			      struct json_object *json_err)
{
	json_bool ret;
	struct json_object *json_buf;
	struct json_object *json_reply;

	coninfo->http_status = MHD_HTTP_BAD_REQUEST;
	ret = json_object_object_get_ex(json_err, "message", &json_buf);

	if (!ret) {
		coninfo->answer = strdup(
			"{\"error\":\"failed to forward ChatGPT error\"}");
		return;
	}

	json_reply = json_object_new_object();
	json_object_object_add(json_reply, "error", json_buf);
	coninfo->answer = strdup(json_object_to_json_string(json_reply));
	json_object_put(json_reply);
}

static void reply_parsing_failed(struct coninfo *coninfo)
{
	coninfo->http_status = MHD_HTTP_INTERNAL_SERVER_ERROR;
	coninfo->answer =
		strdup("{\"error\":\"failed to parse ChatGPT response\"}");
}

static void print_big_json(const char *start, struct json_object *obj)
{
	printf("==%s==\n", start);
	printf("%s\n", json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PRETTY));
	printf("==end==\n");
}

/* The ChatGPT API returns complex JSON objects, this function isolate the
   actual text generated for each key.

   Input:
   {
     "ARM": {
       "choices": [
	 {
	   "message": {
	     "content": "<LLM response content>"
	   }
	 }
       ]
     },
     ...
   }

   Output:
   {
     "ARM": "<LLM response content>",
     ...
   }

   The "LLM response content" is not parsed, it may
   contain bullshit even after this function returns.

   ChatGPT errors are forwarded to the client.
   Input:
   {
     "ARM": {
       "error": {
	 "message": "<LLM error message>"
       }
     },
     ...
   }
   
   In this case, the "LLM error message" is forwarded as-is to
   the client, see the forward_llm_error function.
*/
static struct json_object *isolate_llm_responses(struct coninfo *coninfo,
						 const struct json_object *raw)
{
	struct json_object *res = json_object_new_object();
	struct json_object *json_err, *json_buf;

	json_object_object_foreach(raw, key, val)
	{
		/* check for error */
		json_bool found =
			json_object_object_get_ex(val, "error", &json_err);
		/* TODO: verify memory integrity */

		if (found) {
			forward_llm_error(coninfo, json_err);
			json_object_put(res);
			return NULL;
		}

		/* no error, retrieve information */
		found = json_object_object_get_ex(val, "choices", &json_buf);

		if (!found)
			goto isolate_parse_err;

		json_buf = json_object_array_get_idx(json_buf, 0);

		if (!json_buf)
			goto isolate_parse_err;

		found = json_object_object_get_ex(json_buf, "message",
						  &json_buf);

		if (!found)
			goto isolate_parse_err;

		found = json_object_object_get_ex(json_buf, "content",
						  &json_buf);

		if (!found)
			goto isolate_parse_err;

		json_object_object_add(res, key, json_buf);
	}

	print_big_json("LLM isolated reply", res);
	return res;

isolate_parse_err:
	reply_parsing_failed(coninfo);
	json_object_put(res);
	return NULL;
}

/* Convert the JSON string OBJ representing an array to a JSON array.
 Return NULL is the given JSON string does not represent an array. */
static json_object *json_string_to_json_array(struct json_object *obj)
{
	struct json_tokener *tok = json_tokener_new();
	struct json_object *arr = json_tokener_parse(json_object_to_json_string(obj));

	json_tokener_free(tok);

	if (!arr)
		return NULL;

	if (json_object_get_type(arr) != json_type_array) {
		json_object_put(arr);
		return NULL;
	}

	return arr;
}

/* Get the dimension of the JSON array OBJ, which is actually a JSON string
   we have to parse like "[[1], [2]]". Return NULL if an error occured,
   usually because OBJ does not have a valid shape or is not an array at all. */
static struct array_dim *json_array_get_dim(struct json_object *obj)
{
	struct json_object *elem;
	struct json_object *arr = json_string_to_json_array(obj);
	struct array_dim *dim = NULL;

	if (!arr)
		goto array_get_dim_err;

	dim = malloc(sizeof(*dim));
	dim->height = json_object_array_length(arr);

	if (dim->height == 0)
		goto array_get_dim_err;

	elem = json_object_array_get_idx(arr, 0);

	if (json_object_get_type(elem) != json_type_array)
		goto array_get_dim_err;

	dim->width = json_object_array_length(elem);

	/* TODO: verify that every row has same width */
	/* TODO: verify that every element has same type */

	json_object_put(arr);
	return dim;

array_get_dim_err:
	/* LLM returned bullshit */
	if (arr)
		json_object_put(arr);

	if (dim)
		free(dim);

	return NULL;
}

/* Return the maximum of the given COUNT numbers,
   which COUNT itself is not part of.

   Example: vmax(2, 45, 67) >>> 67
*/
static int vmax(int count, ...)
{
	va_list ap;
	va_start(ap, count);
	int res = 0;

	while (count > 0) {
		int next = va_arg(ap, int);

		if (next > res)
			res = next;

		count--;
	}

	va_end(ap);
	return res;
}

/* Lengthen the JSON array OBJ to FINAL_LEN by repeating its last element. */
static void json_array_add_padding(struct json_object **obj, int final_len)
{
	struct json_tokener *tok;
	struct json_object *arr;
	int current_len;
	struct json_object *last;

	tok = json_tokener_new();
	arr = json_tokener_parse(json_object_to_json_string(*obj));
	json_tokener_free(tok);
	current_len = json_object_array_length(arr);
	last = json_object_array_get_idx(arr, current_len-1);

	while (current_len < final_len) {
		json_object_array_add(arr, last);
		current_len++;
	}

	json_object_put(*obj);
	*obj = arr;
}

/* Write an array containing one line of zeros of width WANTED_WIDTH to
   ARR_DEST, and write its dimension to DIM_DEST. */
static void fill_zeros(struct json_object **arr_dest, struct array_dim **dim_dest,
		       int wanted_width)
{
		print_big_json("LLM bullshit", *arr_dest);
		struct json_object *line = json_object_new_array_ext(wanted_width);

		for (int i = 0; i < wanted_width; i++)
			json_object_array_put_idx(line, i, json_object_new_int(0));

		*arr_dest = json_object_new_array_ext(1);
		json_object_array_put_idx(*arr_dest, 0, line);
		*dim_dest = json_array_get_dim(*arr_dest);
}

/* Retrieve the value of KEY in OBJ. If it is an array of width WANTED_WIDTH,
   it is returned. Else, if it is either not a array or an array of bad width,
   an array containing a single line of zeros of width WANTED_WIDTH is
   returned. */
static void sanitize_array(struct json_object *obj,
			   const char *key,
			   struct json_object **arr_dest,
			   struct array_dim **dim_dest,
			   int wanted_width)
{
	json_object_object_get_ex(obj, "ARM", arr_dest);
	*dim_dest = json_array_get_dim(*arr_dest);

	if (!dim_dest) {
		/* OBJ["ARM"] is not a valid array or not an array at all */
		fill_zeros(arr_dest, dim_dest, wanted_width);
		return;
	}

	if ((*dim_dest)->width != wanted_width) {
		free(*dim_dest);
		fill_zeros(arr_dest, dim_dest, wanted_width);
	}
}

/* Convert the ChatGPT raw response RAW to the format the front-end expects. */
static struct json_object *
translate_llm_responses(struct coninfo *coninfo, const struct json_object *raw)
{
	struct array_dim *arm_dim, *leg_dim, *head_dim, *height_dim;
	int frame_count;
	struct json_object *arm, *leg, *head, *height;
	struct json_object *isl = isolate_llm_responses(coninfo, raw);

	if (!isl)
		return NULL;

	sanitize_array(isl, "ARM", &arm, &arm_dim, 2);
	sanitize_array(isl, "LEG", &leg, &leg_dim, 2);
	sanitize_array(isl, "HEAD", &head, &head_dim, 1);
	sanitize_array(isl, "HEIGHT", &height, &height_dim, 1);

	frame_count = vmax(4, arm_dim->height, leg_dim->height,
			   head_dim->height, height_dim->height);

	json_array_add_padding(&arm, frame_count);
	json_array_add_padding(&leg, frame_count);
	json_array_add_padding(&head, frame_count);
	json_array_add_padding(&height, frame_count);

	return NULL;
}

/* Verify the content of the json object OBJ. */
static enum MHD_Result process_request(struct coninfo *coninfo,
				       struct json_object *obj)
{
	printf("%s: processing valid JSON\n", __func__);

	struct json_object *json_buf;
	json_bool ret;
	char *key, *input;

	/* verify "input" */
	ret = json_object_object_get_ex(obj, "input", &json_buf);

	if (!ret) {
		struct json_object *json_err = json_error(
			"the given JSON object does not have an 'input' value");
		coninfo->http_status = MHD_HTTP_BAD_REQUEST;
		coninfo->answer = strdup(json_object_to_json_string(json_err));
		json_object_put(json_err);
		json_object_put(obj);
		return MHD_NO;
	}

	input = strdup(json_object_to_json_string(json_buf));

	/* verify "key" */
	ret = json_object_object_get_ex(obj, "key", &json_buf);

	if (!ret) {
		key = get_default_key();
		printf("info: using the default key\n");
		/* TODO: limit usage */
	} else {
		key = strdup(json_object_to_json_string(json_buf));
	}

	json_object_put(obj);

	printf("debug: input=%s\n", input);
	printf("debug: key=%s\n", key);

	struct json_object *raw_responses = prompt_execute_all(key, input);

	printf("==LLM raw reply==\n");
	printf("%s\n", json_object_to_json_string_ext(raw_responses,
						      JSON_C_TO_STRING_PRETTY));
	printf("==END==\n");

	struct json_object *translated_responses =
		translate_llm_responses(coninfo, raw_responses);

	if (!translated_responses) {
		json_object_put(raw_responses);
		free(input);
		free(key);
		return MHD_NO;
	}

	coninfo->http_status = MHD_HTTP_OK;
	coninfo->answer = strdup(json_object_to_json_string(translated_responses));

	json_object_put(raw_responses);
	json_object_put(translated_responses);
	free(input);
	free(key);

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

	/* TODO: handle NULL answer */

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
