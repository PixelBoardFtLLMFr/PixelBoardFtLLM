#ifndef PROMPT_H
#define PROMPT_H

enum prompt_type {
	PT_ARM,
	PT_LEG,
	PT_HEAD,
	PT_FACE,
	PT_PARTICLE,
	PT_EYE,
	PT_HEIGHT,
};

/* Should be called before any other function for initializing
   the prompt builder. */
void prompt_init(void);

void prompt_destroy(void);

/* Get the "system" part of the prompt for the given TYPE. The returned
 string is heap-allocated. */
char *prompt_sys(enum prompt_type type);

/* Get the "user" part of the prompt for the given TYPE and the
   INPUT given by the end-user. The returned string is heap-allocated. */
char *prompt_user(enum prompt_type type, const char *input);

#endif
