#include <curl/curl.h>
#include <json_tokener.h>
#include <linkhash.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "llm.h"

struct llm_ctx {
	/* used only for freeing */
	char *auth_bearer_header;
	struct curl_slist *headers;
	/* actual data */
	CURL *curl_handle;
	struct json_object *stem;
	struct json_object *prompts; /* currently pushed prompts */
};

struct callback_data {
	char *key;
	char *buf;
	size_t buf_size;
	struct json_object *results;
};

static size_t http_post_callback(char *ptr, size_t size,
				 size_t nmemb, void *__data)
{
	struct callback_data *data = __data;
	size_t realsize = size * nmemb;

	data->buf = realloc(data->buf, data->buf_size + realsize + 1);
	memcpy(data->buf + data->buf_size, ptr, realsize);
	data->buf_size += realsize;
	data->buf[data->buf_size] = 0;

	struct json_object *obj = json_tokener_parse(data->buf);

	if (obj) {
		json_object_object_add(data->results, data->key, obj);
		free(data->buf);
		free(data);
	}
	
	return realsize;
}

struct llm_ctx *llm_init(const char *keyfile, const char *model)
{
	char *line = NULL;
	size_t line_size = 0;
	struct llm_ctx *ctx = malloc(sizeof(*ctx));
	FILE *keystream = fopen(keyfile, "r");

	if (!ctx) {
		perror("malloc");
		exit(EXIT_FAILURE);
	}

	if (!keystream) {
		perror("fopen");
		exit(EXIT_FAILURE);
	}

	/* Auth Bearer */
	ssize_t bytes_read = getline(&line, &line_size, keystream);

	if (bytes_read == -1) {
		perror("getline");
		exit(EXIT_FAILURE);
	}

	if (bytes_read < 2) {
		fprintf(stderr, "getline: suspicious length of key (%zu)\n",
			bytes_read);
		exit(EXIT_FAILURE);
	}
		
	fclose(keystream);
	line[bytes_read - 1] = '\0';
	char auth_bearer[256] = "Authorization: Bearer ";
	strcat(auth_bearer, line);
	ctx->auth_bearer_header = strdup(auth_bearer);
	free(line);

	/* CURL Handle */
	ctx->curl_handle = curl_easy_init();
#ifndef NDEBUG
	curl_easy_setopt(ctx->curl_handle, CURLOPT_VERBOSE, 1L);
#endif
	curl_easy_setopt(ctx->curl_handle, CURLOPT_URL, CHATGPT_URL);
	/* Force the use of SSL.  Fail if not possible. */
	curl_easy_setopt(ctx->curl_handle, CURLOPT_USE_SSL, CURLUSESSL_ALL);
	curl_easy_setopt(ctx->curl_handle, CURLOPT_WRITEFUNCTION, http_post_callback);

	ctx->headers = NULL;
	ctx->headers = curl_slist_append(ctx->headers, "Content-Type: application/json");
	ctx->headers = curl_slist_append(ctx->headers, ctx->auth_bearer_header);
	curl_easy_setopt(ctx->curl_handle, CURLOPT_HTTPHEADER, ctx->headers);

	/* Prompt List */
	ctx->prompts = json_object_new_object();

	/* JSON Stem */
	ctx->stem = json_object_new_object();
	json_object_object_add(ctx->stem, "model",
			       json_object_new_string(model));

	return ctx;
}

void llm_destroy(struct llm_ctx *ctx)
{
	curl_slist_free_all(ctx->headers);
	curl_easy_cleanup(ctx->curl_handle);
	json_object_put(ctx->stem);
	json_object_put(ctx->prompts);
	free(ctx->auth_bearer_header);
	free(ctx);
}

/* Create a section of a ChatGPT prompt as a JSON object.  The built object has
   the following structure :
   {
     "role": ROLE,
     "content": CONTENT
   }
*/
struct json_object *json_object_prompt_part(const char *role,
					    const char *content)
{
	struct json_object *obj = json_object_new_object();

	json_object_object_add(obj, "role",
			       json_object_new_string(role));
	json_object_object_add(obj, "content",
			       json_object_new_string(content));

	return obj;
}

void llm_push_prompt(struct llm_ctx *ctx, const char *key,
		    const char *sys, const char *usr)
{
	/* Build the JSON data */
	struct json_object *json_prompt = NULL;

	json_object_deep_copy(ctx->stem, &json_prompt, NULL);

	struct json_object *json_sys = json_object_prompt_part("system", sys);
	struct json_object *json_usr = json_object_prompt_part("user", usr);

	struct json_object *messages = json_object_new_array_ext(2);
	json_object_array_add(messages, json_sys);
	json_object_array_add(messages, json_usr);

	json_object_object_add(json_prompt, "messages", messages);

	/* Add the prompt to the prompt list */
	json_object_object_add(ctx->prompts, key, json_prompt);
}

struct json_object *llm_execute_prompts(struct llm_ctx *ctx)
{
	/* TODO: execute prompts in parallel */
	struct json_object *results = json_object_new_object();
	
	json_object_object_foreach(ctx->prompts, key, val) {
		const char *post_data = json_object_to_json_string(val);
		struct callback_data *callback_data = calloc(1, sizeof(*callback_data));

		callback_data->key = key;
		callback_data->results = results;

		curl_easy_setopt(ctx->curl_handle, CURLOPT_POSTFIELDS, post_data);
		curl_easy_setopt(ctx->curl_handle, CURLOPT_WRITEDATA, (void *)callback_data);

		curl_easy_perform(ctx->curl_handle);
	}
	
	return results;
}
