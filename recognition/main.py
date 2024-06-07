import argparse
import llm
import numpy as np
import utils

def array_setlength(array, newlen):
    """
    Set Numpy array ARRAY to length NEWLEN, either by truncating it if it is too
    long, or by repeating the last element if it is too short.
    """
    currlen = np.shape(array)[0]

    if currlen >= newlen:
        return np.resize(array, (newlen, np.shape(array)[1]))
    else:
        res = np.copy(array)
        for i in range(newlen - currlen):
            res = np.append(res, np.array([array[currlen-1]]), axis=0)
        return res

def llm_get_information(myllm, user_input):
    """
    Get different pieces of information from MYLLM. Edit this function if more
    information is needed from the LLM. Return a dictionary containing all the
    information produced.
    """
    # Preparing Prompts ...
    # put results here, this variable is returned by the function
    res = {}
    ## Angles
    user_prompt = f"The requested motion is: {user_input}"

    for kind in llm.PromptType.allTypes:
        myllm.push_prompt(llm.build_prompt(kind), user_prompt, f"ANGLE{kind}")

    ## Particles


    # Executing Prompts ...
    responses = myllm.execute_prompts()


    # Processing Responses ...
    ## Angles
    angles = []
    for kind in llm.PromptType.allTypes:
        angles.append(llm.interprete_as_nparray(responses[f"ANGLE{kind}"]))

    maxlen = max(*[np.shape(angles[kind])[0] for kind in llm.PromptType.allTypes])

    angles[llm.PromptType.ARM] = array_setlength(angles[llm.PromptType.ARM], maxlen)
    angles[llm.PromptType.LEG] = array_setlength(angles[llm.PromptType.LEG], maxlen)
    angles[llm.PromptType.HEAD] = array_setlength(angles[llm.PromptType.HEAD], maxlen)

    angles = np.concatenate((angles[llm.PromptType.ARM],
                             angles[llm.PromptType.LEG],
                             angles[llm.PromptType.HEAD]),
                            axis=1)

    res["ANGLES"] = angles

    # RES is a dictionary containing all the results
    return res



# Data
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
arg_parser.add_argument("-v", "--llm-version", action='store', default="4-turbo",
                        choices=["3.5-turbo", "4-turbo"], help="ChatGPT version use")

# Initializations
args = arg_parser.parse_args()
utils.init(args.debug)
myllm = llm.Llm(args.keyfile, args.llm_version)

information = llm_get_information(myllm, "Say hi")
utils.debug(information["ANGLES"])
exit(0) # Temporary

# Mainloop
print("Order 'quit' to exit")
while True:
    order = input()

    if order == "quit":
        exit(0)

    llm_data = llm_get_information(myllm, order)
    # TODO: draw penguin on simulation
    # TODO: draw penguin on pixel board
