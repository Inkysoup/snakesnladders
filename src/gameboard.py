import tkinter as tk
from tkinter import font
from tkinter import simpledialog
from tkinter import messagebox

import random as rd
import colorsys
from dataclasses import dataclass

@dataclass
class Vector2:
    x: float = 0.0
    y: float = 0.0

class Gameboard:
    @dataclass
    class Portal:
        entry: int
        exit: int

    @dataclass
    class Player:
        position: int
        radius: int
        colour: str
        is_finished: bool = False

    __row_count: int
    __col_count: int
    __tile_positions: list[Vector2]
    __players: list[Player] = []
    __player_canvas_items: list[int] = []
    __current_player: int = 0
    __player_path_positions: list[int] = []
    __is_game_over: bool = False
    __board_canvas: tk.Canvas
    __snakes: list[Portal] = []
    __ladders: list[Portal] = []
    __font1: font.Font
    def __init__(self, owner: tk.Frame, row_count: int, col_count: int, board_font: font.Font) -> None:
        self.__tile_positions = [Vector2() for _ in range(row_count * col_count)]
        self.__font1 = board_font
        self.__board_canvas = tk.Canvas(owner, bg="#D8D8D8", width=0, height=0, highlightthickness=0)
        self.__board_canvas.grid(row=1, column=1, sticky="snew")
        self.__row_count = row_count
        self.__col_count = col_count

        self.regen_portals(4, 4, 3, 3)
        
        def board_canvas_on_resize(event):
            tile_size: Vector2 = Vector2(0, 0)
            if event.widget == self.__board_canvas:
                self.__board_canvas.delete("all")
                self.__tile_positions.clear()
                canvas_size: Vector2 = Vector2(self.__board_canvas.winfo_width(), self.__board_canvas.winfo_height())
                tile_padding = int(min(canvas_size.x, canvas_size.y)/(max(row_count, col_count)+1) *0.05)
                tile_size = Vector2(
                    (canvas_size.x - tile_padding * (row_count+1))/col_count,
                    (canvas_size.x - tile_padding * (col_count+1))/row_count
                )
                tile_min_dimension = min(tile_size.x, tile_size.y)
                font_size = int((tile_min_dimension/3)//4*4)
                self.__font1.configure(size=font_size)
                text_y_padding = 3
                text_descent = self.__font1.metrics("descent")
                for row in range(row_count):
                    for col in range(col_count):
                        x = tile_padding*(col+1)+tile_size.x*col
                        y = canvas_size.y - (tile_padding*(row+1)+tile_size.y*(row+1))
                        x = canvas_size.x - x - tile_size.x if row%2 == 1 else x
                        self.__board_canvas.create_rectangle(
                            x,
                            y,
                            x + tile_size.x,
                            y + tile_size.y,
                            fill="#F0F0F0",
                            outline=""
                        )
                        self.__tile_positions.append(Vector2(x+tile_size.x/2, y+tile_size.y/2))
                        
                        text = self.__board_canvas.create_text(
                            x,
                            y,
                            text=str(col+row*row_count + 1),
                            fill="black",
                            font=self.__font1,
                            anchor="nw"
                        )
                        bbox = self.__board_canvas.bbox(text)
                        bbox_width = bbox[2]-bbox[0]
                        bbox_height = bbox[3]-bbox[1]-text_descent
                        self.__board_canvas.coords(
                            text,
                            x + tile_size.x-bbox_width,
                            y + tile_size.y-bbox_height-text_y_padding,
                        )
            self._draw_portals()

            player_count = len(self.__players)
            for i, player in enumerate(self.__players):
                player.radius = int((player_count-i)/player_count * min(tile_size.x, tile_size.y)/2)

            self._draw_players()
        self.__board_canvas.bind("<Configure>", board_canvas_on_resize)

        self.__board_canvas.event_generate(
            "<Configure>", width=self.__board_canvas.winfo_width(),
            height=self.__board_canvas.winfo_height()
        )
        player_count = 0
        while not player_count:
            player_count = simpledialog.askinteger(
                title="Players",
                prompt="Specify the number of players (2-8):",
                minvalue=2,
                maxvalue=8,
            )
        for i in range(player_count):
            hue: float = (i / player_count) % 1.0
            r, g, b = (int(channel * 255) for channel in (colorsys.hsv_to_rgb(hue, 0.7, 0.9)))
            self.__players.append(self.Player(
                0,
                0,
                f"#{r:02X}{g:02X}{b:02X}"
            ))


    def regen_portals(self, ladder_mean: int, snake_mean: int, ladder_uncertainty: int = 0, snake_uncertainty: int = 0) -> None:
        def calc_portals(portal_mean:int, portal_uncertainty: int, is_ladder: bool, banned_entry_list: list[int] = []) -> list[Gameboard.Portal]:
            portal_count = portal_mean
            while True and portal_uncertainty:
                portal_count = round(rd.normalvariate(mu=portal_mean, sigma=portal_uncertainty))
                if abs(portal_count - portal_mean) <= portal_uncertainty:
                    break
            portal_count = int(portal_count * 2)
            assert(portal_count < len(self.__tile_positions))

            allowed_indexes = [i for i in range(1, len(self.__tile_positions)-1) if i not in banned_entry_list]

            portal_entryexit_indexes = rd.sample(allowed_indexes, portal_count)
            portal_positions = []
            for i in range(0, len(portal_entryexit_indexes), 2):
                entry: int = portal_entryexit_indexes[i]
                exit: int = portal_entryexit_indexes[i+1]
                if((entry > exit and is_ladder) or (entry < exit and not is_ladder)):
                    entry = portal_entryexit_indexes[i+1]
                    exit = portal_entryexit_indexes[i]
                portal_positions.append(self.Portal(entry, exit))
            return portal_positions
        
        self.__ladders.clear()
        self.__ladders = calc_portals(ladder_mean, ladder_uncertainty, is_ladder=True)
        
        ladder_entry_list: list[int] = [i.entry for i in self.__ladders]
        self.__snakes.clear()
        self.__snakes = calc_portals(snake_mean, snake_uncertainty, is_ladder=False, banned_entry_list=ladder_entry_list)

    def _draw_portals(self) -> None:
        radius: int = int(min(self.__board_canvas.winfo_width(), self.__board_canvas.winfo_height())/100)
        def draw_arrow(pos1: Vector2, pos2: Vector2, colour: str):
            self.__board_canvas.create_line(
                pos1.x,
                pos1.y,
                pos2.x,
                pos2.y,
                fill=colour,
                width=radius*2-1,
                arrow=tk.LAST,
                arrowshape=(16, 20, 6)
            )
        
        for portal in self.__ladders:
            pos1: Vector2 = self.get_tile_position(portal.entry)
            pos2: Vector2 = self.get_tile_position(portal.exit)
            draw_arrow(pos1, pos2, "green")
        for portal in self.__snakes:
            pos1: Vector2 = self.get_tile_position(portal.entry)
            pos2: Vector2 = self.get_tile_position(portal.exit)
            draw_arrow(pos1, pos2, "red")

    def reset_players(self) -> None:
        self.__player_path_positions.clear()
        for player in self.__players:
            player.position=0
            player.is_finished=False
        self._draw_players()

    def move_next_player(self, count: int) -> None:
        players_left: int = len(self.__players)
        while self.__players[self.__current_player].is_finished:
            self.__current_player = (self.__current_player+1)%len(self.__players)
            players_left -= 1
            if players_left == 0:
                return
        self.__player_path_positions.clear()
        position: int = self.__players[self.__current_player].position
        self.__player_path_positions.append(position)
        position += count
        position = min(position, 99)

        prev_row: int = (position-count)//self.__row_count
        current_row: int = (position)//self.__row_count
        if prev_row != current_row:
            self.__player_path_positions.append(current_row*self.__col_count-1)
            self.__player_path_positions.append(current_row*self.__col_count)

        was_on_portal = True
        while was_on_portal and position != 99:
            was_on_portal = False
            for ladder in self.__ladders:
                if position == ladder.entry:
                    self.__player_path_positions.append(position)
                    position = ladder.exit
                    was_on_portal = True
                    break
            if not was_on_portal:
                for snake in self.__snakes:
                    if position == snake.entry:
                        self.__player_path_positions.append(position)
                        position = snake.exit
                        was_on_portal = True
                        break
        
        
        self.__player_path_positions.append(position)

        self.__players[self.__current_player].position = position
        self.__current_player = (self.__current_player+1)%len(self.__players)
        self._draw_players()
        if position == 99:
            messagebox.showinfo("Game Over", f"Player {self.__current_player-1 + 1} has finished!")
            self.__players[self.__current_player-1].is_finished = True

    def _draw_players(self) -> None:
        for item in self.__player_canvas_items:
            self.__board_canvas.delete(item)
        self.__player_canvas_items.clear()

        def draw_player(centre: Vector2, colour: str, radius: int) -> int:
            pos1: Vector2 = Vector2(centre.x-radius, centre.y-radius)
            pos2: Vector2 = Vector2(centre.x+radius, centre.y+radius)
            return self.__board_canvas.create_oval(
                pos1.x,
                pos1.y,
                pos2.x,
                pos2.y,
                fill=colour,
                outline=""
            )

        if len(self.__player_path_positions) >= 1:
            canvas_item: int = draw_player(
                self.get_tile_position(self.__player_path_positions[0]),
                "#B0B0B0",
                self.__players[(self.__current_player-1)%len(self.__players)].radius
            )
            self.__player_canvas_items.append(canvas_item)

        if len(self.__player_path_positions) >= 2:
            for i in range(len(self.__player_path_positions)-1):
                radius: int = int(min(self.__board_canvas.winfo_width(), self.__board_canvas.winfo_height())/200)
                canvas_item = self.__board_canvas.create_line(
                    self.get_tile_position(self.__player_path_positions[i]).x,
                    self.get_tile_position(self.__player_path_positions[i]).y,
                    self.get_tile_position(self.__player_path_positions[i+1]).x,
                    self.get_tile_position(self.__player_path_positions[i+1]).y,
                    fill="#B0B0B0",
                    width=radius*2+1
                )
                self.__player_canvas_items.append(canvas_item)

                centre: Vector2 = self.get_tile_position(self.__player_path_positions[i+1])
                pos1: Vector2 = Vector2(centre.x-radius, centre.y-radius)
                pos2: Vector2 = Vector2(centre.x+radius, centre.y+radius)
                canvas_item = self.__board_canvas.create_oval(
                    pos1.x,
                    pos1.y,
                    pos2.x,
                    pos2.y,
                    fill="#B0B0B0",
                    outline="",
                )
                self.__player_canvas_items.append(canvas_item)
                
        
        for player in self.__players:
            canvas_item = draw_player(
                self.get_tile_position(player.position),
                player.colour,
                player.radius
            )
            self.__player_canvas_items.append(canvas_item)


    def get_tk_window(self) -> tk.Canvas:
        return self.__board_canvas
    def get_tile_position(self, index: int) -> Vector2:
        return self.__tile_positions[index]
