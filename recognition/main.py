# External Libraries
import argparse
import numpy as np
import tkinter as tk
# Our Modules
import llm
import utils
import penguin

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

def process_input(user_input):
    pass

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
arg_parser.add_argument("-x", "--scale", action='store', default=32,
                        type=int, help="scale of pixel board, "
                        + "has to be a mutiple of 5, defaults to 30")

# Initializations
args = arg_parser.parse_args()
utils.init(args.debug)
myllm = llm.Llm(args.keyfile, args.llm_version)
mypenguin = penguin.Penguin(args.penguin_size)
pixels = mypenguin.do_draw(0, 0, 0, 0, 0)
# utils.debug(pixels)
# exit(0) # Temporary

# information = llm_get_information(myllm, "Say hi")
# utils.debug(information["ANGLES"])
# exit(0) # Temporary

app = tk.Tk(baseName="PPP")
tk.Button(app, text="Quit", command=app.destroy).pack(side='bottom')
canvas_size = args.scale*args.penguin_size
canvas = tk.Canvas(app,
                   width=canvas_size,
                   height=canvas_size,
                   bg="#000000")
canvas.pack(side='top')
image = tk.PhotoImage(width=canvas_size, height=canvas_size)
canvas.create_image((canvas_size//2, canvas_size//2), image=image, state="normal")

app.mainloop()
