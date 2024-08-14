#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "llm.h"

int main(int argc, char *argv[])
{
	if (argc < 2) {
		fprintf(stderr, "Usage: %s KEY\n", argv[0]);
		exit(EXIT_FAILURE);
	}

	struct llm_ctx *ctx = llm_init(argv[1], "gpt-3.5-turbo");
	char *input = NULL;
	size_t input_size = 0;
	struct json_object *results = NULL;

	printf("Type 'quit' to exit.\n");

	while (1) {
		printf("(llm) ");
		fflush(stdout);
		ssize_t bytes_read = getline(&input, &input_size, stdin);

		if (bytes_read == -1) {
			perror("getline");
			exit(EXIT_FAILURE);
		}

		if (bytes_read < 1)
			continue;

		input[bytes_read - 1] = '\0';

		if (strcmp(input, "quit") == 0) {
			break;
		}

		llm_push_prompt(ctx, "KEY", "", input);
		results = llm_execute_prompts(ctx);
		struct json_object *answer =
			json_object_object_get(results, "KEY");
		answer = json_object_object_get(answer, "choices");
		answer = json_object_array_get_idx(answer, 0);
		answer = json_object_object_get(answer, "message");
		answer = json_object_object_get(answer, "content");
		printf("%s\n", json_object_to_json_string_ext(
				       answer, JSON_C_TO_STRING_PRETTY));
		json_object_put(results);
	}

	if (input)
		free(input);

	llm_destroy(ctx);

	return EXIT_SUCCESS;
}
