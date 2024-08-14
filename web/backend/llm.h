#ifndef LLM_H
#define LLM_H

#include <json_object.h>

struct llm_ctx;

/* Initialize the LLM with the API key KEY. MODEL can be one of :
 - gpt-3.5-turbo
 - gpt-4-turbo
*/
struct llm_ctx *llm_init(const char *key, const char *model);

void llm_destroy(struct llm_ctx *ctx);

/* Push a LLM prompt, giving it the identifier KEY.  Prompts can be executed
   later, all in parallel, by calling llm_execute_prompts. */
void llm_push_prompt(struct llm_ctx *ctx, const char *key, const char *sys,
		     const char *usr);

/* Execute the prompts previously pushed. Return a JSON object whose keys are
   the ones given to the llm_push_prompt calls, and whose values are the
   corresponding LLM responses. */
struct json_object *llm_execute_prompts(struct llm_ctx *ctx);

#endif
