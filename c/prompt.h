#ifndef PROMPT_H
#define PROMPT_H

#include <json_object.h>

/* Should be called before any other function for initializing
   the prompt builder. */
void prompt_init(void);

void prompt_destroy(void);

/* Build all the needed prompts, execute them all, and return the results. */
struct json_object *prompt_execute_all(const char *key, const char *input);

#endif
