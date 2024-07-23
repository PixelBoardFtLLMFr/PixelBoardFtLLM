PPP -- Pixel Penguin Project
===

# Usage

There are two different and independant ways of using the project. Both require
a ChatGPT API key. For best convenience, put it in a `key.txt` file at the root
of the project or in a handy location.

## Local GUI

The *local GUI* is simply a window that pops up on your screen and allow you to
use the project, just like any other application. It is written in Python and
its code is located in the `src` subdirectory, the assets being in `assets`.

1. Install the required libraries `pip install -r requirements.txt`.
2. Use Python to execute the `src/main.py` file. You may give it the `-h` option
for further information about its parameters.

## Web Browser

This version is more complicated to deploy, but allow users to access the
project using their web browser, it is much more convenient for them. Three
components are involved.

- The *frontend*, a piece of Javascript code and HTML the user receives from the
*web server*. This code is executed on the user's machine and sends their input
to the *backend*. Written using Vue by Benjamin.
- The *web server*, the HTTP server whose only mission is to send the graphical
content to the user.
- The *backend*, a HTTP server written in C by Tristan, whose code is located in
the `c` subdirectory. This server receives requests from the user, parse it,
verifiy it, and send it to the LLM, yet again via HTTP. Then, the LLM response
is parsed, verified, and sent back in a custom JSON format to the *frontend*,
which can then render it to the user. Instructions about how to compile and
execute this component are in the dedicated `c/README.md` file.

# Authors

- Augustin Roussely
- Benjamin Dayres
- Febri Abdullah
- Li Xiaoxu
- Ruck Thawonmas
- Rintaro Makino
- Tristan Riehs
