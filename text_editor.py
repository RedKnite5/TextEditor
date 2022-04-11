

import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog as FD

from functools import partial
from typing import Text
from collections import deque
from itertools import islice


class SliceDeque(deque):
    def __getitem__(self, index):
        if isinstance(index, slice):
            start = index.start or 0
            stop = index.stop or len(self)
            step = index.step or 1

            self.rotate(-start)
            cut = list(islice(self, 0, stop-start, step))
            self.rotate(start)
            return cut
        else:
            return super().__getitem__(index)

class Coordinate:
    def __init__(self, index):
        self.index = index

    def __get__(self, instance, owner):
        return instance.cursor[self.index]
    
    def __set__(self, instance, value):
        instance.cursor[self.index] = value


class TextArray:
    x = Coordinate(0)
    y = Coordinate(1)

    def __init__(self):
        self.lines = SliceDeque([SliceDeque()])
        self.cursor = [0, 0]  # x, y
    
    def __getitem__(self, index):
        return self.lines[index]
    
    def current_line(self):
        return self.lines[self.y]

    def insert(self, char):
        self.current_line().insert(self.x, char)
        self.x += 1
    
    def newline(self):
        remaining_text = ""
        if remaining_text := self.current_line()[self.x:]:
            self.current_line().rotate(-self.x)
            for i in range(len(remaining_text)):
                self.current_line().popleft()
            self.current_line().rotate(self.x)
        self.lines.insert(self.y + 1, SliceDeque(remaining_text))
        self.y += 1
        self.x = 0



class TextEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Editor")
        self.root.geometry("400x400")

        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.pack()

        self.text = TextArray()
        self.font_size = 12
        self.font = tkFont.Font(family="Courier", size=self.font_size)
        self.char_width = self.font.measure("A")

        self.canvas.create_line(
            self.text.x + self.char_width,      # x1
            self.text.y + self.char_width,      # y1
            self.text.x + self.char_width,      # x2
            self.text.y + 2 * self.char_width,   # y2
            tag="cursor"
        )
        self.canvas.focus_set()

        self.init_menu()

        self.bindings()

    def init_menu(self):
        self.menu = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menu, tearoff=0)
        #self.filemenu.add_command(label="New", command=donothing)
        #self.filemenu.add_command(label="Open", command=donothing)
        self.filemenu.add_command(label="Save", command=self.save)
        #self.filemenu.add_separator()
        #self.filemenu.add_command(label="Exit", command=root.quit)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=self.menu)
    
    def save(self):
        f = FD.asksaveasfile(mode='w', defaultextension=".txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = "".join(self.text.current_line())
        f.write(text2save)
        f.close()

    
    def bindings(self):
        self.canvas.bind("<Key>", self.key_press)
        self.canvas.bind("<Button-1>", self.mouse_press)
        self.canvas.bind("<Return>", self.enter_key)
        self.canvas.bind("<BackSpace>", self.backspace)
        self.canvas.bind("<Left>", self.arrow("left"))
        self.canvas.bind("<Right>", self.arrow("right"))
        self.canvas.bind("<Up>", self.arrow("up"))
        self.canvas.bind("<Down>", self.arrow("down"))

    def update_cursor(self):
        self.canvas.moveto(
            "cursor",
            (self.text.x + 1) * self.char_width,
            (self.text.y + 1) * self.char_width
        )
    
    def update_line(self, line_number):

        self.canvas.delete(f"line_{line_number}")
        self.canvas.create_text(
            self.char_width,                        # x
            self.char_width * (line_number + 1),    # y
            text="".join(self.text[line_number]),
            anchor='nw',
            font=self.font,
            fill='black',
            tag=f"line_{line_number}"
        )
    
    def arrow(self, direction):
        def arrow_press(event):
            print(direction)

            if direction == "left" and self.text.x > 0:
                self.text.x -= 1
            elif direction == "right" and self.text.x < len(self.text.current_line()):
                self.text.x += 1
            elif direction == "up" and self.text.y > 0:           # still need to handle differnt length line switching
                self.text.y -= 1
            elif direction == "down" and self.text.y < len(self.text.lines) - 1:
                self.text.y += 1
            
            self.update_cursor()
        return arrow_press

    def key_press(self, event):
        self.text.insert(event.char)
        self.update_line(self.text.y)
        self.update_cursor()
    
    def enter_key(self, event):
        print("enter")
        self.text.newline()
        self.update_line(self.text.y - 1)
        self.update_line(self.text.y)
        self.update_cursor()


    def backspace(self, event):
        print("backspace")





    def mouse_press(self, event):
        print("click")


    def mainloop(self):
        self.root.mainloop()



def main():
    t = TextEditor()

    t.mainloop()

if __name__ == "__main__":
    main()


