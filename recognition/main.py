import argparse
import llm

ppp_desc = "Pixel Penguin Project a.k.a. PPP"
prompt_str = "What should I do ? "

arg_parser = argparse.ArgumentParser(prog="ppp", description=ppp_desc)
arg_parser.add_argument("-d", "--debug", action='store_const',
                        const=True, default=False, help="run in debug mode")
arg_parser.add_argument("-k", "--keyfile", action='store', default="./key.txt",
                        help="file that contain LLM API key, defaults to ./key.txt")
arg_parser.add_argument("-s", "--penguin-size", action='store', default=25,
                        type=int, help="size of penguin, defaults to 25")
arg_parser.add_argument("-p", "--port", action='store', default="/dev/ttyACM0",
                        help="pixel board port, defaults to /dev/ttyACM0")
arg_parser.add_argument("-v", "--llm-version", action='store', default="gpt-4-turbo",
                        choices=["3.5-turbo", "4-turbo"], help="ChatGPT version use")

args = arg_parser.parse_args()
llm.init(args.keyfile, args.llm_version)

print("Order 'quit' to exit")
while True:
    order = input()

    if order == "quit":
        exit(0)

    # TODO: draw penguin on simulation
    # TODO: draw penguin on pixel board
