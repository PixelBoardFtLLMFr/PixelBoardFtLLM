# Dependencies

- [libcurl](https://curl.se/libcurl/c/)
- [GNU libmicrohttpd](https://www.gnu.org/software/libmicrohttpd/)
- [json-c](https://json-c.github.io/json-c/json-c-0.17/doc/html/index.html)

The correponding packages are listed in the `*_deps.txt` files, such as
`apt_deps.txt` for the `apt` package manager. You can install them using the
following command.

``` shell
xargs -d "\n" sudo apt install < ./apt_deps.txt
```

# Building

To build the server, run `make`. There are several customizable variables, see
the Makefile content. To build the test program `llm_tester`, run
`make llm_tester`.

# ChatGPT API Reference

See [this page](https://platform.openai.com/docs/api-reference/chat/create).

# Source Formatting

A `.clang-format` file is present. It is the Linux Kernel one. You can format
all the sources by running `make fmt`.
