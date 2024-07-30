#include <json_object.h>
#include <json_tokener.h>
#include <linkhash.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/queue.h>
#include <sys/select.h>
#include <sys/socket.h>

#include "flow.h"
#include "request.h"
#include "prompt.h"
#include "llm.h"
#include "trace.h"

/* 1KB */
#define BUFSIZE (1 << 10)

#define EYE_SIZE 3

char *default_key;

/* Information regarding a request being currently processed.  For each
   request, a pointer to a coninfo structure is used by the handle_request
   and handle_chunk functions to process the request. */
struct coninfo {
	struct sockaddr *clientaddr;
	int using_default_key;
	/* JSON parser */
	struct json_tokener *tok;
	/* answer to the request, non-NULL if processing is done */
	char *answer;
	/* HTTP status of reply */
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

/* Give CONINFO 'bad request' status and MSG content, enclosed in JSON. */
static void coninfo_set_error(struct coninfo *coninfo, const char *msg)
{
	struct json_object *json_err = json_error(msg);
	coninfo->http_status = MHD_HTTP_BAD_REQUEST;
	coninfo->answer = strdup(json_object_to_json_string_ext(
		json_err, JSON_C_TO_STRING_PLAIN));
	json_object_put(json_err);
}

/* Set the headers that are mandatory for network traffic to properly go. */
static void set_mandatory_headers(struct MHD_Response *response)
{
	MHD_add_response_header(response, "Access-Control-Allow-Headers", "*");
	MHD_add_response_header(response, "Access-Control-Allow-Origin", "*");
	MHD_add_response_header(response, "Access-Control-Allow-Methods",
				"POST, OPTIONS");
	MHD_add_response_header(response, "Content-Type", "application/json");
	MHD_add_response_header(response, "Server", "PPP");
}

/* Reply to the pending request of CON, using the answer and the
   HTTP status of CONINFO. */
static enum MHD_Result reply_request(struct MHD_Connection *con,
				     struct coninfo *coninfo)
{
	TRACE;
	printf("%s: reply text '%s'\n", __func__, coninfo->answer);
	printf("%s: reply HTTP code '%d'\n", __func__, coninfo->http_status);

	int ret;
	struct MHD_Response *response;

	response = MHD_create_response_from_buffer(strlen(coninfo->answer),
						   (void *)coninfo->answer,
						   MHD_RESPMEM_PERSISTENT);
	set_mandatory_headers(response);
	ret = MHD_queue_response(con, coninfo->http_status, response);
	MHD_destroy_response(response);

	return ret;
}

/* Build a heap-allocated string from the given format FMT. */
static char *strf(const char *fmt, ...)
{
	char buf[2048];
	va_list ap;

	TRACE;

	va_start(ap, fmt);
	vsnprintf(buf, sizeof(buf) - 1, fmt, ap);
	va_end(ap);

	return strdup(buf);
}

/* Wrapper for reply_request to send formatted error messages. */
static enum MHD_Result reply_request_error(struct MHD_Connection *con,
					   struct coninfo *coninfo,
					   const char *msg)
{
	TRACE;
	coninfo_set_error(coninfo, msg);
	return reply_request(con, coninfo);
}

/* Read the file containing the default key and return
   it. The result is cached. */
static char *get_default_key(void)
{
	if (default_key)
		return default_key;

	size_t key_size = 0;
	ssize_t bytes_read;
	FILE *stream;

	stream = fopen(DEFAULT_KEY_FILE, "r");

	if (!stream) {
		perror(DEFAULT_KEY_FILE);
		exit(EXIT_FAILURE);
	}

	bytes_read = getline(&default_key, &key_size, stream);

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

	default_key[bytes_read - 1] = '\0';
	fclose(stream);

	return default_key;
}

/* Send an error thrown by the LLM API to the client. */
static void forward_llm_error(struct coninfo *coninfo,
			      struct json_object *json_err)
{
	TRACE;
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
	coninfo->answer = strdup(json_object_to_json_string_ext(
		json_reply, JSON_C_TO_STRING_PLAIN));
	json_object_get(json_buf);
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
	printf("%s\n",
	       json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PRETTY));
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
	/* check for error */
	/* I use weird braces because the json_object_object_foreach macro
	   declares KEY in the current scope */
	json_object_object_foreach(raw, __key, val0)
	{
		(void)__key;
		struct json_object *json_err;

		if (json_object_object_get_ex(val0, "error", &json_err)) {
			forward_llm_error(coninfo, json_err);
			return NULL;
		}
	}

	/* no error, retrieve information */
	struct json_object *res = json_object_new_object();

	json_object_object_foreach(raw, key, val1)
	{
		struct json_object *json_buf;
		json_bool found;

		found = json_object_object_get_ex(val1, "choices", &json_buf);

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
		/* We must take ownership in order to
		   keep data after RAW is freed */
		json_object_get(json_buf);
	}

	print_big_json("LLM isolated reply", res);
	return res;

isolate_parse_err:
	reply_parsing_failed(coninfo);
	json_object_put(res);
	return NULL;
}

/* Removes all the '\n' and '\' in STR. */
static void strip_json_array_string(char *str)
{
	int i, offset = 0;
	const int len = strlen(str);
	char *clone = strdup(str);

	for (i = 0; i < len; i++) {
		if ((i < len - 1) && (clone[i] == '\\') &&
		    (clone[i + 1] == 'n')) {
			offset += 2;
			i++;
		} else if (clone[i] == '\\') {
			offset++;
		} else {
			str[i - offset] = clone[i];
		}
	}

	str[i - offset] = '\0';
	free(clone);
}

/* Convert the JSON string OBJ representing an array to a JSON array.
   Return NULL is the given JSON string does not represent an array. */
static json_object *json_string_to_json_array(struct json_object *obj)
{
	struct json_tokener *tok = json_tokener_new();
	char *str = strdup(
		json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN));
	struct json_object *arr;

	str[strlen(str) - 1] = '\0';
	strip_json_array_string(str + 1);
	arr = json_tokener_parse(str + 1);
	json_tokener_free(tok);
	free(str);

	if (!arr)
		return NULL;

	if (json_object_get_type(arr) != json_type_array) {
		json_object_put(arr);
		return NULL;
	}

	return arr;
}

/* Returns non-zero if every row of ARR has the width specified in DIM and
   every element of ARR has the type specified in DIM. */
static int rows_valid(const struct array_dim *dim,
		      const struct json_object *arr)
{
	for (size_t i = 0; i < json_object_array_length(arr); i++) {
		struct json_object *row;
		int row_len;

		row = json_object_array_get_idx(arr, i);

		if (json_object_get_type(row) != json_type_array)
			return 0;

		row_len = json_object_array_length(row);

		if (row_len != dim->width)
			return 0;

		for (int j = 0; j < row_len; j++) {
			struct json_object *elem =
				json_object_array_get_idx(row, j);

			if (json_object_get_type(elem) != dim->type)
				return 0;
		}
	}

	return 1;
}

/* Get the dimension of the JSON array OBJ, which is either a JSON string we
   have to parse like "[[1], [2]]", or directly a JSON array. Return NULL if an
   error occured, usually because OBJ does not have a valid shape or is not an
   array at all. */
static struct array_dim *json_array_get_dim(struct json_object *obj)
{
	struct json_object *elem;
	struct json_object *arr;
	struct array_dim *dim = NULL;
	enum json_type type = json_object_get_type(obj);

	if (type == json_type_string)
		arr = json_string_to_json_array(obj);
	else if (type == json_type_array)
		arr = obj;
	else
		return NULL;

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

	if (dim->width == 0)
		goto array_get_dim_err;

	dim->type = json_object_get_type(json_object_array_get_idx(elem, 0));

	if (!rows_valid(dim, arr))
		goto array_get_dim_err;

	if (type == json_type_string)
		json_object_put(arr);

	return dim;

array_get_dim_err:
	/* LLM returned bullshit */
	if (arr && (type == json_type_string))
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
static void json_array_add_padding(struct json_object **arr, int final_len)
{
	int current_len;
	struct json_object *last;

	current_len = json_object_array_length(*arr);
	last = json_object_array_get_idx(*arr, current_len - 1);

	while (current_len < final_len) {
		struct json_object *buf = NULL;
		json_object_deep_copy(last, &buf, NULL);
		json_object_array_add(*arr, buf);
		current_len++;
	}
}

/* Write an array containing one line of zeros of width WANTED_WIDTH to
   ARR_DEST, and write its dimension to DIM_DEST. */
static void fill_zeros(struct json_object **arr_dest,
		       struct array_dim **dim_dest, int wanted_width)
{
	print_big_json("LLM bullshit", *arr_dest);
	struct json_object *line = json_object_new_array_ext(wanted_width);

	for (int i = 0; i < wanted_width; i++) {
		struct json_object *new = json_object_new_int(0);
		/* json_object_get(new); */
		json_object_array_put_idx(line, i, new);
	}

	*arr_dest = json_object_new_array_ext(1);
	json_object_array_put_idx(*arr_dest, 0, line);
	*dim_dest = json_array_get_dim(*arr_dest);
}

/* Retrieve the value of KEY in OBJ. If it is an array of width WANTED_WIDTH,
   it is returned. Else, if it is either not a array or an array of bad width,
   an array containing a single line of zeros of width WANTED_WIDTH is
   returned. */
static void sanitize_array(const struct json_object *obj, const char *key,
			   struct json_object **arr_dest,
			   struct array_dim **dim_dest, int wanted_width)
{
	json_object_object_get_ex(obj, key, arr_dest);
	*dim_dest = json_array_get_dim(*arr_dest);

	if (!(*dim_dest)) {
		/* OBJ[KEY] is not a valid array or not an array at all */
		fill_zeros(arr_dest, dim_dest, wanted_width);
		return;
	}

	if ((*dim_dest)->width != wanted_width) {
		free(*dim_dest);
		fill_zeros(arr_dest, dim_dest, wanted_width);
		return;
	}

	*arr_dest = json_string_to_json_array(*arr_dest);
}

/* Split the JSON array at *DEST, and write the result to *DEST as well.
   Before split :
   [[0, 2],
    [1, 3]]
   After split :
   {
     "left":  [0, 1],
     "right": [2, 3]
   }
*/
static void json_array_split(struct json_object **dest)
{
	int length = json_object_array_length(*dest);
	struct json_object *right = json_object_new_array_ext(length);
	struct json_object *left = json_object_new_array_ext(length);

	for (int i = 0; i < length; i++) {
		struct json_object *row = json_object_array_get_idx(*dest, i);

		json_object_array_put_idx(left, i,
					  json_object_get(json_object_array_get_idx(row, 0)));
		json_object_array_put_idx(right, i,
					  json_object_get(json_object_array_get_idx(row, 1)));
	}

	json_object_put(*dest);
	*dest = json_object_new_object();
	json_object_object_add(*dest, "left", left);
	json_object_object_add(*dest, "right", right);
}

/* Return non-zeros if the NULL-terminated array ARR contains STR. */
static int string_array_contains(const char *const *arr, const char *str)
{
	for (int i = 0; arr[i] != NULL; i++) {
		if (strcmp(str, arr[i]) == 0)
			return 1;
	}

	return 0;
}

/* Verify that OBJ[KEY] is in ARR. If it is, it is written to *DEST, else
   DEF is written. */
static void sanitize_string(const struct json_object *obj,
			    struct json_object **dest, const char *key,
			    const char *const *arr, const char *def)
{
	json_object_object_get_ex(obj, key, dest);

	if (json_object_get_type(*dest) != json_type_string)
		goto sanitize_string_default;

	if (!string_array_contains(arr, json_object_to_json_string(*dest)))
		goto sanitize_string_default;

	json_object_get(*dest);
	return;

sanitize_string_default:
	*dest = json_object_new_string(def);
}

/* Verify that OBJ["FACE"] is a valid facial expression. If it is, it is
   written to *DEST, else "neutral" is written. */
static void sanitize_face(const struct json_object *obj,
			  struct json_object **dest)
{
	const char *const faces[] = { "neutral", "happy",     "sad",
				      "angry",	 "surprised", NULL };

	sanitize_string(obj, dest, "FACE", faces, faces[0]);
}

/* Verify that OBJ["PARTICLE"] is a valid particle. If it is, it is
   written to *DEST, else "none" is written. */
static void sanitize_particle(const struct json_object *obj,
			      struct json_object **dest)
{
	const char *const particles[] = { "none",  "angry", "heart", "sleepy",
					  "spark", "sweat", "cloud", NULL };

	sanitize_string(obj, dest, "PARTICLE", particles, particles[0]);
}

/* Convert a C triplet (usually for an RGB pixel) into a
   JSON array of three integers. */
static struct json_object *triplet_to_json(const int *triplet)
{
	struct json_object *arr = json_object_new_array_ext(3);

	for (int i = 0; i < 3; i++) {
		struct json_object *json_int = json_object_new_int(triplet[i]);
		json_object_array_put_idx(arr, i, json_int);
	}

	return arr;
}

/* Return the JSON array of integers of length 3 corresponding to the
   color OBJ as a JSON string. */
static struct json_object *convert_eye_element(struct json_object *obj)
{
	char *json_str = strdup(json_object_to_json_string(obj));
	const char *const colors_str[] = { "blue",  "bright", "green", "red",
					   "white", "yellow", NULL };
	const int colors_int[][3] = { { 50, 50, 255 }, { 200, 200, 200 },
				      { 0, 255, 130 }, { 255, 0, 0 },
				      { 10, 10, 10 },  { 255, 222, 40 } };

	json_str[strlen(json_str) - 1] = '\0';

	for (int i = 0; colors_str[i] != NULL; i++) {
		if (strcmp(json_str + 1, colors_str[i]) == 0) {
			free(json_str);
			return triplet_to_json(colors_int[i]);
		}
	}

	free(json_str);
	return NULL;
}

static void convert_eye_colors(struct json_object **dest)
{
	struct json_object *arr = json_string_to_json_array(*dest);

	for (int i = 0; i < EYE_SIZE; i++) {
		struct json_object *row = json_object_array_get_idx(arr, i);

		for (int j = 0; j < EYE_SIZE; j++) {
			struct json_object *old_elem =
				json_object_array_get_idx(row, j);
			struct json_object *new_elem =
				convert_eye_element(old_elem);
			json_object_array_put_idx(row, j, new_elem);
		}
	}

	*dest = arr;
}

/* Verify that the eye OBJ["EYE"] has the right 3x3 shape, and that
   colors are valid. A null JSON object is written to *DEST if eye is
   not valid. */
static void sanitize_eye(const struct json_object *obj,
			 struct json_object **dest)
{
	struct array_dim *dim;

	json_object_object_get_ex(obj, "EYE", dest);
	dim = json_array_get_dim(*dest);

	if (!dim) {
		*dest = json_object_new_null();
		return;
	}

	if ((dim->width != EYE_SIZE) || (dim->height != EYE_SIZE) ||
	    (dim->type != json_type_string)) {
		free(dim);
		*dest = json_object_new_null();
		return;
	}

	free(dim);
	convert_eye_colors(dest);
}

/* Convert the ChatGPT raw response RAW to the format the front-end expects. */
static struct json_object *
translate_llm_responses(struct coninfo *coninfo, const struct json_object *raw)
{
	struct json_object *isl = isolate_llm_responses(coninfo, raw);

	struct array_dim *arm_dim, *leg_dim, *head_dim, *height_dim;
	struct json_object *arm, *leg, *head, *height;
	int frame_count;

	if (!isl)
		return NULL;

	sanitize_array(isl, "ARM", &arm, &arm_dim, 2);
	sanitize_array(isl, "LEG", &leg, &leg_dim, 2);
	sanitize_array(isl, "HEAD", &head, &head_dim, 1);
	sanitize_array(isl, "HEIGHT", &height, &height_dim, 1);

	frame_count = vmax(4, arm_dim->height, leg_dim->height,
			   head_dim->height, height_dim->height);

	free(arm_dim);
	free(leg_dim);
	free(head_dim);
	free(height_dim);

	json_array_add_padding(&arm, frame_count);
	json_array_add_padding(&leg, frame_count);
	json_array_add_padding(&head, frame_count);
	json_array_add_padding(&height, frame_count);

	json_array_split(&arm);
	json_array_split(&leg);

	struct json_object *face;
	sanitize_face(isl, &face);

	struct json_object *particle;
	sanitize_particle(isl, &particle);

	struct json_object *eye;
	sanitize_eye(isl, &eye);

	struct json_object *res = json_object_new_object();
	json_object_object_add(res, "ARM", arm);
	json_object_object_add(res, "LEG", leg);
	json_object_object_add(res, "HEAD", head);
	json_object_object_add(res, "HEIGHT", height);
	json_object_object_add(res, "FACE", face);
	json_object_object_add(res, "PARTICLE", particle);
	json_object_object_add(res, "EYE", eye);

	json_object_put(isl);

	return res;
}

/* Verify the content of the json object OBJ. */
static enum MHD_Result process_request(struct coninfo *coninfo,
				       struct json_object *obj)
{
	printf("%s: processing valid JSON\n", __func__);

	struct json_object *json_buf;
	json_bool ret;
	char *key = NULL, *input = NULL;

	/* verify "input" */
	ret = json_object_object_get_ex(obj, "input", &json_buf);

	if (!ret) {
		coninfo_set_error(
			coninfo,
			"the given JSON object does not have an 'input' value");
		goto process_err;
	}

	input = strdup(json_object_to_json_string(json_buf));

	/* verify "key" */
	ret = json_object_object_get_ex(obj, "key", &json_buf);

	if (!ret) {
		coninfo_set_error(
			coninfo,
			"the given JSON object does not have a 'key' value");
		goto process_err;
	}

	key = strdup(json_object_to_json_string(json_buf));
	json_object_put(obj);
	obj = NULL;

	if (strcmp(key, "\"\"") == 0) {
		free(key);
		key = get_default_key();
		coninfo->using_default_key = 1;
	} else {
		coninfo->using_default_key = 0;
	}

	if (!flow_allow(coninfo->clientaddr)) {
		coninfo_set_error(coninfo,
				  "reached maximum number of requests per hour");
		goto process_err;
	}

	printf("debug: input=%s\n", input);
	printf("debug: key=%s\n", key);

	struct json_object *raw_responses = prompt_execute_all(key, input);

	print_big_json("LLM raw reply", raw_responses);

	struct json_object *translated_responses =
		translate_llm_responses(coninfo, raw_responses);
	json_object_put(raw_responses);
	raw_responses = NULL;

	if (!translated_responses)
		goto process_err;

	coninfo->http_status = MHD_HTTP_OK;
	coninfo->answer =
		strdup(json_object_to_json_string(translated_responses));

	printf("info: freeing translated responses\n");
	json_object_put(translated_responses); /* should not crash */
	free(input);

	return MHD_YES;

process_err:
	if (obj)
		json_object_put(obj);

	if (input)
		free(input);

	if (!coninfo->using_default_key)
		free(key);

	return MHD_NO;
}

/* Handle the chunks of data. Only take care of the JSON
   parsing, not of the JSON content. */
static enum MHD_Result handle_chunk(struct coninfo *coninfo, const char *data,
				    size_t data_size)
{
	TRACE;

	struct json_object *obj =
		json_tokener_parse_ex(coninfo->tok, data, data_size);

	if (obj) {
		if (json_object_get_type(obj) == json_type_object) {
			return process_request(coninfo, obj);
		} else {
			coninfo_set_error(coninfo,
					  "given JSON has the wrong type");
			json_object_put(obj);
			return MHD_NO;
		}
	}

	if (json_tokener_get_error(coninfo->tok) != json_tokener_continue) {
		printf("%s: invalid JSON detected\n", __func__);
		coninfo_set_error(
			coninfo, json_tokener_error_desc(
					 json_tokener_get_error(coninfo->tok)));
		return MHD_NO;
	}

	return MHD_NO;
}

void cleanup_request(void *cls, struct MHD_Connection *con, void **req_cls,
		     enum MHD_RequestTerminationCode toe)
{
	TRACE;

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

static struct coninfo *coninfo_init(struct MHD_Connection *con)
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

	coninfo->clientaddr = *(struct sockaddr **)MHD_get_connection_info(con, MHD_CONNECTION_INFO_CLIENT_ADDRESS);

	return coninfo;
}

static enum MHD_Result reply_request_error_early(struct MHD_Connection *con,
						 struct coninfo *coninfo,
						 char *msg)
{
	TRACE;

	int ret = reply_request_error(con, coninfo, msg);
	free(msg);

	return ret;
}

/* Reply to an OPTIONS request, need for the CORS stuff to work properly. */
static enum MHD_Result reply_options(struct MHD_Connection *con,
				     struct coninfo *coninfo)
{
	enum MHD_Result ret;
	struct MHD_Response *response;

	TRACE;

	coninfo->answer = strdup("");
	coninfo->http_status = MHD_HTTP_OK;

	return reply_request(con, coninfo);
}

/* Called several times per request. The first time, *REQ_CLS is NULL, the
   other times, it is set to what we set it to the first time, namely a
   pointer to a coninfo structure. */
enum MHD_Result handle_request(void *cls, struct MHD_Connection *con,
			       const char *url, const char *method,
			       const char *version, const char *data,
			       size_t *data_size, void **req_cls)
{
	TRACE;

	if (!(*req_cls)) {
		/* first iteration */
		printf("%s: initializing handler\n", __func__);
		*req_cls = coninfo_init(con);

		if (!(*req_cls)) {
			fprintf(stderr, "%s: failed to initalize handler\n",
				__func__);
			return MHD_queue_response(
				con, MHD_HTTP_INTERNAL_SERVER_ERROR, NULL);
		}

		return MHD_YES;
	}

	/* other iterations */
	printf("%s: other iteration\n", __func__);

	if (strcmp(method, "OPTIONS") == 0) {
		return reply_options(con, *req_cls);
	}

	if (strcmp(method, "POST") != 0) {
		return reply_request_error_early(
			con, *req_cls, strf("bad method (%s)", method));
	}

	if (strcmp(url, "/") != 0) {
		return reply_request_error_early(con, *req_cls,
						 strf("bad URL (%s)", url));
	}

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

	if (coninfo->answer != NULL)
		return reply_request(con, coninfo);

	/* incomplete JSON input such as "{" (missing '}') */
	reply_request_error(con, coninfo, "incomplete JSON data");
	return MHD_YES;
}
