# External Libraries
import argparse
import numpy as np
import tkinter as tk
import time
import PIL.ImageTk, PIL.Image
import pynput
# Our Modules
import llm
import utils
import penguin
import pixelboardsimulator as pbs
import pixelboard
import pixelsnake

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

def canvas_send_img(canvas, img):
    tk_img = PIL.ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    canvas.image = tk_img

def draw_all(canvas, penguin, simulator, board, angles):
    pixels = penguin.do_draw(*angles)
    board.draw_pixels(pixels)
    simulator_img = simulator.do_draw(pixels)
    canvas_send_img(canvas, simulator_img)

def draw_next_frame(canvas, penguin, simulator, board, llm_data, index):
    global animating
    angles = llm_data["ANGLES"]
    frame_count = len(angles)

    if index == frame_count:
        # Animation done
        utils.debug()
        animating = False
        user_input.set(prompt_str)
        return


    if index == 0:
        # First frame
        ## Angles
        utils.debug(f"LLM generated {frame_count} frames, "
                    + f"animation will last {frame_count*dt} s")


    # Other frames
    ## Angles
    utils.debug(f"\rFrame {index+1}/{frame_count}", end="")
    draw_all(canvas, mypenguin, simulator, board, angles[index])
    canvas.after(int(dt*1000),
                 lambda:
                 draw_next_frame(canvas, penguin, simulator, llm_data, index+1))

def snake_loop(canvas, snake, simulator, board, listener):
    pixels = snake.loop()

    if not pixels:
        listener.Stop()
        return
    
    canvas.after(int(dt*1000), lambda: snake_loop(canvas, snake, simulator, board, listener))

def launch_snake(size, canvas, simulator, board):
    snake = pixelsnake.PixelSnake(size)
    pixels = snake.gen_pixels()
    board.draw_pixels(pixels)
    simulator_img = simulator.do_draw(pixels)
    canvas_send_img(canvas, simulator_img)
    listener = pynput.Listener(on_press=snake.handle_key)
    snake_loop(canvas, snake, simulator, board, listener)

def process_input(*args):
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

    if text == "snake":
        launch_snake(mypenguin.size, canvas, simulator, board)
        return

    llm_data = llm_get_information(myllm, text)

    draw_next_frame(canvas, mypenguin, simulator, board, llm_data, 0)



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

args = arg_parser.parse_args()
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

draw_all(canvas, mypenguin, simulator, board, [0, 0, 0, 0, 0])

app.mainloop()
