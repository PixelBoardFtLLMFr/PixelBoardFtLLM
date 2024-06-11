# External Libraries
import argparse
import numpy as np
import tkinter as tk
import time
import PIL.ImageTk
# Our Modules
import llm_ebin
import utils
import penguin
import pixelboardsimulator as pbs
import traceback

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

    for kind in llm_ebin.PromptType.allTypes:
        myllm.push_prompt(llm_ebin.build_system_prompt(kind=kind), llm_ebin.build_user_prompt(kind=kind, user_input=user_input), f"ANGLE{kind}")

    responses = myllm.execute_prompts()


    # Processing Responses ...
    ## Angles
    angles = []

    try:
        for kind in llm_ebin.PromptType.allTypes:
            angles.append(llm_ebin.interprete_as_nparray(responses[f"ANGLE{kind}"]))

        maxlen = max(*[np.shape(angles[kind])[0] for kind in llm_ebin.PromptType.allTypes])

        angles[llm_ebin.PromptType.ARM] = array_setlength(angles[llm_ebin.PromptType.ARM], maxlen)
        angles[llm_ebin.PromptType.LEG] = array_setlength(angles[llm_ebin.PromptType.LEG], maxlen)
        angles[llm_ebin.PromptType.HEAD] = array_setlength(angles[llm_ebin.PromptType.HEAD], maxlen)

        angles = np.concatenate((angles[llm_ebin.PromptType.ARM],
                                angles[llm_ebin.PromptType.LEG],
                                angles[llm_ebin.PromptType.HEAD]),
                                axis=1)
    except Exception as e:
        print(traceback.print_exc())
        

    res["ANGLES"] = angles

    # RES is a dictionary containing all the results
    return res

def draw_all(canvas, penguin, simulator, angles):
    pixels = penguin.do_draw(*angles)
    simulator_img = simulator.do_draw(pixels)
    simulator_tk_img = PIL.ImageTk.PhotoImage(simulator_img)
    canvas.create_image(0, 0, anchor=tk.NW, image=simulator_tk_img)
    canvas.image = simulator_tk_img

def draw_next_frame(canvas, penguin, simulator, llm_data, index):
    global animating, submit_button
    angles = llm_data["ANGLES"]
    frame_count = len(angles)

    try:
        if index == frame_count:
            # Animation done
            utils.debug()
            animating = False
            submit_button.config(state='normal')
            return


        if index == 0:
            # First frame
            ## Angles
            utils.debug(f"LLM generated {frame_count} frames, "
                        + f"animation will last {frame_count*dt} s")


        # Other frames
        ## Angles
        utils.debug(f"\rFrame {index+1}/{frame_count}", end="")
        draw_all(canvas, mypenguin, simulator, angles[index])
        canvas.after(int(dt*1000),
                    lambda:
                    draw_next_frame(canvas, penguin, simulator, llm_data, index+1))
    except Exception as e:
        utils.debug()
        animating = False
        submit_button.config(state='normal')
        print(traceback.print_exc())


def process_input(*args):
    """
    Process the user input. If an animation is currently running, do nothing.
    """
    global user_input, submit_button, canvas, animating, myllm, mypenguin, simulator, dt
    text = user_input.get()
    submit_button.config(state='disabled')

    if animating:
        return

    animating = True
    utils.debug(text)

    llm_data = llm_get_information(myllm, text)

    draw_next_frame(canvas, mypenguin, simulator, llm_data, 0)



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
arg_parser.add_argument("-v", "--llm-version", action='store', default="3.5-turbo",
                        choices=["3.5-turbo", "4-turbo"], help="ChatGPT version to use")
arg_parser.add_argument("-x", "--scale", action='store', default=32,
                        type=int, help="scale of pixel board, "
                        + "has to be a mutiple of 5, defaults to 30")
arg_parser.add_argument("-f", "--framerate", action='store', default=10,
                        type=int, help="frames per second, defaults to 1")

args = arg_parser.parse_args()
utils.init(args.debug)
myllm = llm_ebin.LlmEbin(args.keyfile, args.llm_version)
mypenguin = penguin.Penguin(args.penguin_size)
animating = False
dt = 1/args.framerate # number of seconds to sleep between frames
simulator = pbs.PixelBoardSimulator(args.scale)

app = tk.Tk(baseName="PPP")

canvas_size = args.scale*args.penguin_size
canvas = tk.Canvas(app, width=canvas_size, height=canvas_size, bg="#000000")
canvas.grid(column=0, row=0, rowspan=3)

user_input = tk.StringVar(app, value=prompt_str)
user_entry = tk.Entry(app, textvariable=user_input)
user_entry.grid(column=1, row=0, sticky='S')

submit_button = tk.Button(app, text="Submit", command=process_input)
submit_button.grid(column=1, row=1, sticky='N')

quit_button = tk.Button(app, text="Quit", command=app.destroy)
quit_button.grid(column=1, row=2, sticky='SE')

draw_all(canvas, mypenguin, simulator, [0, 0, 0, 0, 0])

app.mainloop()
