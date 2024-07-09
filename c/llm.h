#ifndef LLM_H
#define LLM_H

#include <json_object.h>

struct llm_ctx;

struct llm_ctx *llm_init(const char *keyfile, const char *model);
void llm_destroy(struct llm_ctx *ctx);

void llm_push_prompt(struct llm_ctx *ctx, const char *key, const char *sys,
		     const char *usr);
struct json_object *llm_execute_prompts(struct llm_ctx *ctx);

#endif
