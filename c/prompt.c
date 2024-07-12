#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "prompt.h"
#include "llm.h"

/* 4KB */
#define MAX_FILE_SIZE (1 << 12)

enum prompt_type {
	PT_ARM,
	PT_LEG,
	PT_HEAD,
	PT_FACE,
	PT_PARTICLE,
	PT_EYE,
	PT_HEIGHT,
	PT_COUNT,
	PT_FIRST = PT_ARM,
};

static char *keys[] = {
	[PT_ARM] = "ARM",
	[PT_LEG] = "LEG",
	[PT_HEAD] = "HEAD",
	[PT_FACE] = "FACE",
	[PT_PARTICLE] = "PARTICLE",
	[PT_EYE] = "EYE",
	[PT_HEIGHT] = "HEIGHT",
};

static char *angle_base;

static char *arm_spec;
static char *arm_example;

static char *leg_spec;
static char *leg_example;

static char *head_spec;
static char *head_example;

static char *face;

static char *particle;

static char *eye;

static char *height;

/* Read the whole content of file given by PATH. The file size
   has not to exceed MAX_FILE_SIZE. */
static char *read_whole_file(const char *path)
{
	char buf[MAX_FILE_SIZE] = { 0 };
	size_t buf_len = 0;
	FILE *stream = fopen(path, "r");

	if (!stream) {
		perror(path);
		exit(EXIT_FAILURE);
	}

	while (!ferror(stream) && !feof(stream) && (buf_len < MAX_FILE_SIZE)) {
		buf_len += fread(buf + buf_len, 1, MAX_FILE_SIZE - buf_len - 1,
				 stream);

		if (buf_len == MAX_FILE_SIZE - 1) {
			fprintf(stderr, "erorr: file %s too big\n", path);
			exit(EXIT_FAILURE);
		}
	}

	if (ferror(stream)) {
		perror("fread");
		fclose(stream);
		exit(EXIT_FAILURE);
	}

	fclose(stream);
	return strdup(buf);
}

void prompt_init(void)
{
	angle_base = read_whole_file("angle_base.txt");

	arm_spec = read_whole_file("arm_spec.txt");
	arm_example = read_whole_file("arm_example.txt");

	leg_spec = read_whole_file("leg_spec.txt");
	leg_example = read_whole_file("leg_example.txt");

	head_spec = read_whole_file("head_spec.txt");
	head_example = read_whole_file("head_example.txt");

	face = read_whole_file("face.txt");

	particle = read_whole_file("particle.txt");

	eye = read_whole_file("eye.txt");

	height = read_whole_file("height.txt");
}

void prompt_destroy(void)
{
	free(angle_base);

	free(arm_spec);
	free(arm_example);

	free(leg_spec);
	free(leg_example);

	free(head_spec);
	free(head_example);

	free(face);

	free(particle);

	free(eye);

	free(height);
}

static char *concat(const char *s0, const char *s1, const char *s2)
{
	char buf[3 * MAX_FILE_SIZE];
	strcpy(buf, s0);
	strcat(buf, s1);
	strcat(buf, s2);
	return strdup(buf);
}

/* Get the "system" part of the prompt for the given TYPE. The returned
 string is heap-allocated. */
static char *prompt_sys(enum prompt_type type)
{
	switch (type) {
	case PT_ARM:
		return concat(angle_base, arm_example, arm_spec);
	case PT_LEG:
		return concat(angle_base, leg_example, leg_spec);
	case PT_HEAD:
		return concat(angle_base, head_example, head_spec);
	case PT_FACE:
		return strdup(face);
	case PT_PARTICLE:
		return strdup(particle);
	case PT_EYE:
		return strdup(eye);
	case PT_HEIGHT:
		return strdup(height);
	default:
		fprintf(stderr, "%s: invalid prompt type %d\n", __func__, type);
		break;
	}

	return NULL;
}

/* Get the "user" part of the prompt for the given TYPE and the
   INPUT given by the end-user. The returned string is heap-allocated. */
static char *prompt_usr(enum prompt_type type, const char *input)
{
	char buf[MAX_FILE_SIZE];
	strcpy(buf, "The user input is : ");
	strncat(buf, input, MAX_FILE_SIZE - strlen(input) - 1);
	return strdup(buf);
}

struct json_object *prompt_execute_all(const char *key, const char *input)
{
	struct llm_ctx *ctx = llm_init(key, "gpt-3.5-turbo");
	struct json_object *raw_responses;

	for (int i=0; i < PT_COUNT; i++) {
		char *sys = prompt_sys(i);
		char *usr = prompt_usr(i, input);
		llm_push_prompt(ctx, keys[i], sys, usr);
		free(sys);
		free(usr);
	}

	raw_responses = llm_execute_prompts(ctx);
	llm_destroy(ctx);
	return raw_responses;
}
