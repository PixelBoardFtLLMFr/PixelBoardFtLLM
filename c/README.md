# Getting the sources

To upload the sources to the machine that will host the server, either clone the
Git repository, or run `make dist` on any other machine to create a source
archive `ppp_code.tar.gz`, upload it to the server, and extract it. The second
option is the best since it will use much less disk space on the machine. Beware
that the archive is poorly made, everything is at the top-level, make sure to
extract it in an empty build directoy.


# Dependencies

The following libraries are needed to compile the server :

- [libcurl](https://curl.se/libcurl/c/);
- [GNU libmicrohttpd](https://www.gnu.org/software/libmicrohttpd/);
- [json-c](https://json-c.github.io/json-c/json-c-0.17/doc/html/index.html);

and the following programs are needed :

- C compiler (*e.g.* GCC);
- make;
- pkg-config.

The correponding packages are listed in the `*_deps.txt` files, such as
`apt_deps.txt` for the `apt` package manager. You can install them using the
following command.

```shell
xargs -d "\n" sudo apt install < ./apt_deps.txt
```

# Building

To build (*i.e.* compile) the server, run `make`. There are several customizable
variables, see the Makefile content. To build the test program `llm_tester`, run
`make llm_tester`.

# Installing

To install the project on the system, run `make install` (no administrator
privileges required), and optionnaly `make service_install` (administrator
privileges required) to be able to run the server using Systemd, the service
name is "ppp".

# Running

To run the server, run the `ppp_server` executable. You may get help by
providing the `-h` command-line argument.

When runnning with Valgrind (only for development), use the
`--suppressions=dlopen.supp` to suppress Glibc's dlopen memory leaks.

# ChatGPT API Reference

See [this page](https://platform.openai.com/docs/api-reference/chat/create).

# Source Formatting

A `.clang-format` file is present. It is the Linux Kernel one. You can format
all the sources by running `make fmt`.
