# External Libraries
import argparse
import numpy as np
import tkinter as tk
import time
import PIL.ImageTk, PIL.Image
import threading as th
# Our Modules
import llm
import utils
import penguin
import pixelboardsimulator as pbs
import pixelboard
from speech import SpeechToText, Lang

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
    utils.debug("Preparing prompts...")
    ## Angles
    limb_prompt_types = [llm.PromptType.ARM, llm.PromptType.LEG, llm.PromptType.HEAD]
    user_prompt = f"The requested motion is: {user_input}"

    for kind in limb_prompt_types:
        myllm.push_prompt(llm.build_prompt(kind), user_prompt, f"ANGLE{kind}")

    ## Facial Expression
    myllm.push_prompt(llm.build_prompt(llm.PromptType.FACE), user_prompt, "FE")

    ## Particle
    myllm.push_prompt(llm.particle_prompt, user_prompt, "PARTICLE")

    # Executing Prompts ...
    utils.debug("Executing prompts...")
    responses = myllm.execute_prompts()


    # Processing Responses ...
    utils.debug("Processing reponses...")
    ## Facial Expression
    res["FE"] = responses["FE"].lower()
    
    ## Angles
    angles = {}
    for kind in limb_prompt_types:
        __res_or_die__ = llm.interprete_as_nparray(responses[f"ANGLE{kind}"])
        if __res_or_die__ is None:
            angles[kind] = [[0] * (1 if kind == llm.PromptType.HEAD else 2)]
        else:
            angles[kind] = __res_or_die__

    myarr = [np.shape(angles[kind])[0] for kind in limb_prompt_types]
    maxlen = max(*myarr)

    angles[llm.PromptType.ARM] = array_setlength(angles[llm.PromptType.ARM], maxlen)
    angles[llm.PromptType.LEG] = array_setlength(angles[llm.PromptType.LEG], maxlen)
    angles[llm.PromptType.HEAD] = array_setlength(angles[llm.PromptType.HEAD], maxlen)

    angles = np.concatenate((angles[llm.PromptType.ARM],
                             angles[llm.PromptType.LEG],
                             angles[llm.PromptType.HEAD]),
                            axis=1)

    res["ANGLES"] = angles

    ## Particle
    res["PARTICLE"] = responses["PARTICLE"].lower()

    # RES is a dictionary containing all the results
    return res

def draw_pixel_board(board, pixels):
    pixels_width = len(pixels[0])
    i_min = (pixels_width - board.width) // 2
    i_max = (pixels_width + board.width) // 2
    pixels_cropped = [row[i_min:i_max] for row in pixels]
    board.draw_pixels(pixels_cropped)

def draw_canvas(canvas, img):
    tk_img = PIL.ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    canvas.image = tk_img

def draw_all(canvas, penguin, simulator, board, angles):
    pixels = penguin.do_draw(*angles)
    simulator_img = simulator.do_draw(pixels)
    draw_canvas(canvas, simulator_img)
    draw_pixel_board(board, pixels)

def draw_next_frame(canvas, penguin, simulator, board, llm_data, index):
    global animating, adjust_th, stt
    angles = llm_data["ANGLES"]
    frame_count = len(angles)

    if index == frame_count:
        # Animation done
        utils.debug()
        animating = False
        user_input.set(prompt_str)
        adjust_th.join()
        return


    if index == 0:
        # First frame
        ## Facial Expression
        fe = llm_data["FE"]
        penguin.set_fe(fe)
        ## Particle
        particle = llm_data["PARTICLE"]
        penguin.set_particle(particle)
        ## Angles
        if np.sum(angles) == 0:
            utils.debug("no movement, adding question mark")
            penguin.set_particle("question")

        utils.debug(f"LLM generated {frame_count} frames, "
                    + f"animation will last {frame_count*dt:.2f} s")
        ## Mic Adjustment
        adjust_th = th.Thread(target=stt.adjust)
        adjust_th.start()

    # Other frames
    ## Angles
    utils.debug(f"\rFrame {index+1}/{frame_count}", end="")
    draw_all(canvas, mypenguin, simulator, board, angles[index])
    canvas.after(int(dt*1000),
                 lambda:
                 draw_next_frame(canvas, penguin, simulator, board, llm_data, index+1))

def set_submiting():
    global submitting
    submitting = True

def process_input(*_):
    """
    Process the user input. If an animation is currently running, do nothing.
    """
    global user_input, canvas, animating, myllm, mypenguin, simulator, board, dt
    text = user_input.get()
    user_input.set("Animating ...")

    if animating:
        return

    animating = True
    utils.debug(text)

    llm_data = llm_get_information(myllm, text)

    draw_next_frame(canvas, mypenguin, simulator, board, llm_data, 0)

def process_speech(*_):
    """
    Process the user input as a speech.
    """
    global myllm, canvas, mypenguin, simulator, stt, animating, board, lang_var, user_input
    if animating:
        return

    stt.set_lang(lang_var.get())

    text = stt.listen()

    if not text:
        print("Error during recognition, retrying", flush=True)
        stt.adjust()
        return
    
    user_input.set(text)
    
    animating = True
    utils.debug(text)

    llm_data = llm_get_information(myllm, text)

    draw_next_frame(canvas, mypenguin, simulator, board, llm_data, 0)

def speech_loop():
    global running, submitting
    while running:
        if submitting:
            process_input()
            submitting = False
        else:
            process_speech()


ppp_desc = "Pixel Penguin Project a.k.a. PPP"
prompt_str = "Hello, how are you ?"

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
arg_parser.add_argument("-f", "--framerate", action='store', default=1,
                        type=int, help="frames per second, defaults to 1")
arg_parser.add_argument("-q", "--quick", action='store', default=None,
                        metavar="PROMPT", help="quickly send a prompt")
arg_parser.add_argument("-t", "--test", action='store_true', default=False,
                        help="test LLM connection")

args = arg_parser.parse_args()
utils.init(args.debug)
myllm = llm.Llm(args.keyfile, args.llm_version)

if args.test:
    myllm.test()
    exit(0)

mypenguin = penguin.Penguin(args.penguin_size)
animating = False
dt = 1/args.framerate # number of seconds to sleep between frames
simulator = pbs.PixelBoardSimulator(args.scale)
board = pixelboard.PixelBoard(args.port,
                              [[0, 9, 10, 19, 20],
                               [1, 8, 11, 18, 21],
                               [2, 7, 12, 17, 22],
                               [3, 6, 13, 16, 23],
                               [4, 5, 14, 15, 24]],
                              [[15, 10, 5, 0],
                               [16, 11, 6, 1],
                               [17, 12, 7, 2],
                               [18, 13, 8, 3],
                               [19, 14, 9, 4]])
stt = SpeechToText()
stt.adjust()

adjust_th = None

app = tk.Tk()
app.title("Pixel Penguin Project")
raw_icon = PIL.Image.open("./assets/oscar_32x32.png")
icon = PIL.ImageTk.PhotoImage(raw_icon)
app.wm_iconphoto(False, icon)
row_count = 9

canvas_size = args.scale*args.penguin_size
canvas = tk.Canvas(app, width=canvas_size, height=canvas_size, bg="#000000")
canvas.grid(column=0, row=0, rowspan=row_count)

user_input = tk.StringVar(app, value=prompt_str)
user_entry = tk.Entry(app, textvariable=user_input)
user_entry.grid(column=1, row=0, sticky='S')

submit_button = tk.Button(app, text="Submit", command=set_submiting)
submit_button.grid(column=1, row=1, sticky='N')
# submit_button = tk.Button(app, text="Talk", command=process_speech)
# submit_button.grid(column=1, row=2)

quit_button = tk.Button(app, text="Quit", command=app.destroy)
quit_button.grid(column=1, row=row_count-1, sticky='SE')

lang_var = tk.StringVar(app, "en-US")
for i in range(len(Lang.langs)):
    name, code = Lang.langs[i]
    rb = tk.Radiobutton(app, text=name, value=code, variable=lang_var)
    rb.grid(column=1, row=i+3)

draw_all(canvas, mypenguin, simulator, board, [20, -20, 0, 0, 0])

if args.quick:
    user_input.set(args.quick)
    process_input()

running = True
submitting = False
    
speech_thread = th.Thread(target=speech_loop)
speech_thread.start()
app.mainloop()
running = False
speech_thread.join()
