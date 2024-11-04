import argparse
import numpy as np
import tkinter as tk
import time
import PIL.ImageTk, PIL.Image
import llm
import utils
import penguin
import pixelboardsimulator as pbs
import pixelboard
import random
import dc_bot
import threading as th
import os
from dotenv import load_dotenv
from dc_bot import DCBot

prompt_type=[llm.PromptType.ARM,
             llm.PromptType.LEG,
             llm.PromptType.HEAD,
             llm.PromptType.HEIGHT,
             llm.PromptType.FE,
             llm.PromptType.PARTICLE,
             llm.PromptType.EYE,
             llm.PromptType.DIALOGUE]
limb_type=[llm.PromptType.ARM,
           llm.PromptType.LEG,
           llm.PromptType.HEAD]
pe=[llm.PEType.FEW_SHOT, llm.PEType.ZERO_SHOT_COT]

instructions = open("instruction.txt", 'r').readlines()
print(len(instructions))
def random_instructions():    
    inst=random.choice(instructions)
    return inst

def array_setlength(array, newlen):
    """
    Set Numpy array ARRAY to length NEWLEN, either by truncating it if it is too
    long, or by repeating the last element if it is too short.
    """
    currlen = np.shape(array)[0]

    if currlen == 0:
        return [0]*newlen
    elif currlen >= newlen:
        return np.resize(array, (newlen, np.shape(array)[1]))
    else:
        res = np.copy(array)
        for i in range(newlen - currlen):
            res = np.append(res, np.array([array[currlen-1]]), axis=0)
        return res

def llm_get_information(myllm, instruction):
    """
    Get different pieces of information from MYLLM. Edit this function if more
    information is needed from the LLM. Return a dictionary containing all the
    information produced.
    """
    print(f'processing-->{instruction}')
    res = {}
    utils.debug("Preparing prompts...")
    for pt in prompt_type:
        myllm.push_prompt(llm.build_prompt(kind=pt, pes=pe), instruction, pt)

    utils.debug("Executing prompts...")
    responses = myllm.execute_prompts()

    utils.debug("Processing reponses...")    
    
    angles = {}
    utils.debug("Processing angles")
    for kind in limb_type:
        __res_or_die__ = llm.interprete_as_nparray(responses[kind])
        if __res_or_die__ is None:
            angles[kind] = [[0] * (1 if kind == llm.PromptType.HEAD or kind == llm.PromptType.HEIGHT else 2)]
            utils.debug("llm_get_information: filling with zeros")
        else:
            angles[kind] = __res_or_die__

    myarr = [np.shape(angles[kind])[0] for kind in limb_type]
    maxlen = max(*myarr)

    angles[llm.PromptType.ARM] = array_setlength(angles[llm.PromptType.ARM], maxlen)
    angles[llm.PromptType.LEG] = array_setlength(angles[llm.PromptType.LEG], maxlen)
    angles[llm.PromptType.HEAD] = array_setlength(angles[llm.PromptType.HEAD], maxlen)

    angles = np.concatenate((angles[llm.PromptType.ARM],
                             angles[llm.PromptType.LEG],
                             angles[llm.PromptType.HEAD]),
                            axis=1)

    res["ANGLES"] = angles
    res["FE"] = responses[llm.PromptType.FE].lower()    
    res["PARTICLE"] = responses[llm.PromptType.PARTICLE].lower()

    height = llm.interprete_as_nparray(responses[llm.PromptType.HEIGHT])
    res["HEIGHT"] = height if height is not None else [[0]]
    res["EYE"] = llm.interprete_eye(responses[llm.PromptType.EYE])
    res["DIALOGUE"] = responses[llm.PromptType.DIALOGUE]
    show_output(res["DIALOGUE"])
    
    return res

def draw_pixel_board(board, pixels):
    pixels_width = len(pixels[0])
    i_min = (pixels_width - board.width) // 2
    i_max = (pixels_width + board.width) // 2
    pixels_cropped = [row[i_min:i_max] for row in pixels]
    return board.draw_pixels(pixels_cropped)

def draw_canvas(canvas, img):
    tk_img = PIL.ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    canvas.image = tk_img

def draw_all(canvas, penguin, simulator, board, angles):
    pixels = penguin.do_draw(*angles)
    simulator_img = simulator.do_draw(pixels)
    draw_canvas(canvas, simulator_img)
    return draw_pixel_board(board, pixels)

def draw_next_frame(canvas, penguin, simulator, board, llm_data, index):
    global animating
    angles = llm_data["ANGLES"]
    frame_count = len(angles)

    if index >= frame_count:
        # Animation done
        utils.debug()
        animating = False
        bot.set_animating(animating)
        user_input.set("")
        return

    if index == 0:
        # First frame
        ## Facial Expression
        fe = llm_data["FE"]
        penguin.set_fe(fe)
        ## Particle
        particle = llm_data["PARTICLE"]
        penguin.set_particle(particle)

        utils.debug(f"LLM generated {frame_count} frames, "
                    + f"animation will last {frame_count*dt:.2f} s")
        ## Eye
        if llm_data["EYE"] is not None:
            utils.debug("LLM-generated eyes :")
            utils.debug(llm_data["EYE"])
        penguin.set_eye(llm_data["EYE"])

    utils.debug(f"\rFrame {index+1}/{frame_count}", end="")
    mypenguin.set_size(mypenguin.size, llm_data["HEIGHT"][index][0] if index < len(llm_data["HEIGHT"]) else 0)
    draw_all(canvas, mypenguin, simulator, board, angles[index])

    next_frame = index+1
    canvas.after(int(dt*1000),
                 lambda:
                 draw_next_frame(canvas, penguin, simulator, board, llm_data, next_frame))

def ui_submit():
    global ui_submitting
    ui_submitting = True
    show_output('')
    print("hoho")

def dc_submit():
    global dc_submitting
    dc_submitting = True
    show_output('')

def set_board_first_state(token:str):
    global board
    if token == board_enable_token:
        draw_all(canvas, mypenguin, simulator, board, [20, 20, 0, 0, 0])
        print("aneb")
    elif token == board_disable_token:
        board._clear_serial()
        print("disab")
    
def process_ui_input():
    global user_input, canvas, animating, myllm, mypenguin, simulator, board, dt, bot
    if animating:
        return
    text = user_input.get()
    user_input.set("Animating ...")

    animating = True
    bot.set_animating(animating)
    utils.debug(text)
    
    llm_data = llm_get_information(myllm, text)

    draw_next_frame(canvas, mypenguin, simulator, board, llm_data, 0)

def process_discord_message():
    global user_input, canvas, animating, myllm, mypenguin, simulator, board, dt, bot
    if animating:
        return

    msg_pair = bot.get_unprocessed_message()
    text = bot.get_cleaned_message(msg_pair[0])
    user_input.set("Animating ...")

    animating = True
    bot.set_animating(animating)

    utils.debug(text)
    
    llm_data = llm_get_information(myllm, text)

    reply_msg=llm_data["DIALOGUE"].splitlines()
    reply_msg=reply_msg[0]
    msg_pair[1] = reply_msg
    time.sleep(3)
    while bot.is_sending:
        time.sleep(1)
    draw_next_frame(canvas, mypenguin, simulator, board, llm_data, 0)

def main_loop():
    global running, ui_submitting, dc_submitting, bot
    
    running = True
    bot.run()
    while running:
        dc_submitting = bot is not None and bot.is_running and bot.get_unprocessed_message() is not None
        dc_resetting = bot is not None and bot.is_running and bot.communication_token is not None
        if ui_submitting:
            process_ui_input()
            ui_submitting = False
        elif dc_submitting:
            process_discord_message()
        elif dc_resetting:
            set_board_first_state(bot.communication_token)
            bot.communication_token = None

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
arg_parser.add_argument("-v", "--llm-version", action='store', default="gpt-3.5-turbo",
                        choices=["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o-mini"], help="ChatGPT version to use")
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
load_dotenv(dotenv_path='./.env')

utils.init(args.debug)
myllm = llm.Llm(args.keyfile, args.llm_version)

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

app = tk.Tk()
app.title("Pixel Penguin Project")
raw_icon = PIL.Image.open("./assets/oscar_32x32.png")
icon = PIL.ImageTk.PhotoImage(raw_icon)
app.wm_iconphoto(False, icon)
row_count = 9

canvas_size = args.scale*args.penguin_size
canvas = tk.Canvas(app, width=canvas_size, height=canvas_size, bg="#000000")
canvas.grid(column=0, row=0, rowspan=row_count)

user_input = tk.StringVar(app, value=random_instructions())
user_entry = tk.Entry(app, textvariable=user_input)
user_entry.grid(column=1, row=0, sticky='S')

submit_button = tk.Button(app, text="Submit", command=ui_submit)
submit_button.grid(column=1, row=1, sticky='N')

quit_button = tk.Button(app, text="Quit", command=app.destroy)
quit_button.grid(column=1, row=row_count-1, sticky='SE')

def show_output(msg:str):
    output_text.delete(1.0, tk.END)  # Clear the text box first
    output_text.insert(tk.END, msg)

output_text = tk.Text(app, height=2, width=25)
output_text.grid(column=1, row = 4, sticky='N')

draw_all(canvas, mypenguin, simulator, board, [20, 20, 0, 0, 0])

if args.quick:
    user_input.set(args.quick)
    process_ui_input()

ui_submitting = False
dc_submitting = False

bot = DCBot(token=os.getenv("DISCORD_TOKEN"), channel_id=int(os.getenv("DISCORD_CHANNEL_ID")))
board_disable_token = os.getenv("BOARD_DISABLE_TOKEN")
board_enable_token = os.getenv("BOARD_ENABLE_TOKEN")
main_thread = th.Thread(target=main_loop, daemon=True)
main_thread.start()
app.mainloop()