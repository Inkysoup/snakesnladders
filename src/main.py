import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import messagebox, simpledialog

from gameboard import *

import random as rd
import os



row_count = 10
col_count = row_count

root = tk.Tk()
root.title("snakes and ladders")

icon_path = "assets/werm.ico"
if os.path.exists(icon_path):
    root.iconbitmap(default=icon_path)

root.geometry("700x500")
root.minsize(525, 375)
root.grid_rowconfigure(0, weight=1, uniform="row_group")
root.grid_rowconfigure(1, weight=18, uniform="row_group")
root.grid_rowconfigure(2, weight=1, uniform="row_group")
root.grid_columnconfigure(0, weight=1, uniform="col_group")
root.grid_columnconfigure(1, weight=18, uniform="col_group")
root.grid_columnconfigure(2, weight=9, uniform="col_group")

font1 = font.Font(family="segoe ui", size=16)


board_frame = tk.Frame(root)
board_frame.grid(row=1, column=1, sticky="nsew")

root.withdraw()
gameboard = Gameboard(board_frame, row_count, col_count, font1)
root.deiconify()

roll_label = tk.Label(
    root,
    text="",
    font=font1
)
roll_label.grid(row=1, column=2, sticky="s")

def resize_square(event):
    size = min(event.width, event.height)
    gameboard.get_tk_window().place(relx=0.5, rely=0.5, anchor="center", width=size, height=size)
board_frame.bind("<Configure>", resize_square)

def reset_board():
    gameboard.regen_portals(4, 4, 3, 3)
    gameboard.reset_players()
    roll_label.config(text="")
    # redraw
    canvas: tk.Canvas = gameboard.get_tk_window()
    canvas.event_generate("<Configure>", width=canvas.winfo_width(), height=canvas.winfo_height())
reset_button = ttk.Button(
    root,
    text="reset",
    command=reset_board
)
reset_button.grid(row=1, column=2, sticky="n")

def roll():
    roll: int = rd.randint(1,6)
    roll_label.config(text=f"{roll}")
    gameboard.move_next_player(roll)
roll_button = ttk.Button(
    root,
    text="roll",
    command=roll
)
roll_button.grid(row=1, column=2)


root.focus_force()
root.mainloop()