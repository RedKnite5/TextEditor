

import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog as FD

from functools import partial
from typing import Text
from collections import deque
from itertools import islice
from string import printable


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
    
    def __len__(self):
        return len(self.lines)
    
    def get_text(self):
        return "\n".join("".join(line) for line in self.lines)
    
    def set_text(self, text):
        t = text.split("\n")
        self.lines = SliceDeque([SliceDeque(line) for line in t])
        self.cursor = [0, 0]
    
    def current_line(self):
        return self.lines[self.y]

    def insert(self, char):
        self.current_line().insert(self.x, char)
        self.x += 1
    
    def newline(self):
        remaining_text = ""
        if remaining_text := self.current_line()[self.x:]:
            self.current_line().rotate(-self.x)
            for i in range(len(remaining_text)):     # should do differently depending on which side of the line the cursor is closer to
                self.current_line().popleft()
            self.current_line().rotate(self.x)
        self.lines.insert(self.y + 1, SliceDeque(remaining_text))
        self.y += 1
        self.x = 0
    
    def backspace(self) -> tuple[int]:
        # return (line number, 0|1|2) if 0, 1, or more than one line needs to be updated
        if self.x > 0:
            self.current_line().rotate(1 - self.x)
            self.current_line().popleft()
            self.current_line().rotate(self.x - 1)
            self.x -= 1
            return (self.y, 1)
        elif self.y > 0:
            length = len(self.lines[self.y - 1])
            self.lines[self.y - 1].extend(self.current_line())
            self.lines.rotate(-self.y)
            self.lines.popleft()
            self.lines.rotate(self.y)
            self.y -= 1
            self.x = length
            return (self.y, 2)
        return (-1, 0)
    
    def delete(self):
        if self.x < len(self.current_line()):
            self.current_line().rotate(-self.x)
            self.current_line().popleft()
            self.current_line().rotate(self.x)
            return (self.y, 1)
        elif self.y < len(self.lines) - 1:
            self.current_line().extend(self.lines[self.y + 1])
            self.lines.rotate(-1 - self.y)
            self.lines.popleft()
            self.lines.rotate(self.y + 1)
            return (self.y, 2)
        return (-1, 0)


class Tab:
    def __init__(self, root, filename=None):
        self.root = root
        self.text = TextArray()

        self.filename = filename

        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.grid(row=1, column=0)
        
        self.font_size = 12
        self.font = tkFont.Font(family="Courier", size=self.font_size)
        self.char_width = self.font.measure("A")
        self.char_height = self.font.metrics("linespace") + 1

        self.canvas.focus_set()
        self.bindings()
        self.init_cursor()

    def init_cursor(self):
        self.canvas.create_line(
            self.text.x + self.char_width - 2,        # x1
            self.text.y + self.char_height,           # y1
            self.text.x + self.char_width - 2,        # x2
            self.text.y + 2 * self.char_height - 3,   # y2
            tag="cursor"
        )

    def update_cursor(self):
        self.canvas.moveto(
            "cursor",
            (self.text.x + 1) * self.char_width - 2,
            (self.text.y + 1) * self.char_height
        )
    
    def update_line(self, line_number):
        self.canvas.delete(f"line_{line_number}")
        text = "".join(self.text[line_number]) if line_number < len(self.text) else ""
        self.canvas.create_text(
            self.char_width,                         # x
            self.char_height * (line_number + 1),    # y
            text=text,
            anchor='nw',
            font=self.font,
            fill='black',
            tag=f"line_{line_number}"
        )

    def arrow(self, direction):
        def arrow_press(event):

            if direction == "left":
                if self.text.x > 0:
                    self.text.x -= 1
                elif self.text.y > 0:
                    self.text.y -= 1
                    self.text.x = len(self.text.current_line())
            elif direction == "right":
                if self.text.x < len(self.text.current_line()):
                    self.text.x += 1
                elif self.text.y < len(self.text) - 1:
                    self.text.x = 0
                    self.text.y += 1
            elif direction == "up" and self.text.y > 0:           # still need to handle differnt length line switching
                self.text.y -= 1
            elif direction == "down" and self.text.y < len(self.text.lines) - 1:
                self.text.y += 1
            
            self.update_cursor()
        return arrow_press

    def key_press(self, event):
        if not event.char or event.char not in printable:
            return
        self.text.insert(event.char)
        self.update_line(self.text.y)
        self.update_cursor()
    
    def enter_key(self, event):
        self.text.newline()
        self.update_line(self.text.y - 1)
        self.update_line(self.text.y)
        self.update_cursor()

    def backspace(self, event):
        to_update = self.text.backspace()
        self.update_cursor()
        if to_update[1] == 0:
            return
        elif to_update[1] == 1:
            self.update_line(to_update[0])
        else:
            for line_number in range(to_update[0], len(self.text)+1):
                self.update_line(line_number)
        
    def delete(self, event):
        to_update = self.text.delete()
        self.update_cursor()
        if to_update[1] == 0:
            return
        elif to_update[1] == 1:
            self.update_line(to_update[0])
        else:
            for line_number in range(to_update[0], len(self.text)+1):
                self.update_line(line_number)

    def mouse_press(self, event):
        print("click")
    
    def bindings(self):
        bind = self.canvas.bind

        bind("<Key>", self.key_press)
        bind("<Button-1>", self.mouse_press)
        bind("<Return>", self.enter_key)
        bind("<BackSpace>", self.backspace)
        bind("<Delete>", self.delete)
        bind("<Left>", self.arrow("left"))
        bind("<Right>", self.arrow("right"))
        bind("<Up>", self.arrow("up"))
        bind("<Down>", self.arrow("down"))



class TextEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Editor")
        self.window_shape = (400, 400)
        self.root.geometry("x".join(map(str, self.window_shape)))

        self.tab_buttons_fame = tk.Frame(self.root)
        self.tab_buttons_fame.grid(row=0, column=0, sticky="w")

        self.tabs = []
        self.tab_buttons = []
        self.current_tab = self.create_tab()
        self.current_tab_button = self.tab_buttons[0]

        self.bindings()
        self.init_menu()


    def create_tab(self, filename=None):
        tab = Tab(self.root, filename=filename)

        text = tab.filename if tab.filename else "untitled"
        button = tk.Button(self.tab_buttons_fame, text=text, command=self.select_tab(tab, len(self.tabs)))
        button.grid(row=0, column=len(self.tabs))
        self.tab_buttons.append(button)
        self.tabs.append(tab)

        return tab

    
    def select_tab(self, tab, button_index):
        def select():
            self.current_tab = tab
            self.current_tab.canvas.focus_set()
            self.current_tab_button = self.tab_buttons[button_index]
        return select


    def init_menu(self):
        self.menu = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menu, tearoff=0)
        #self.filemenu.add_command(label="New", command=donothing)
        self.filemenu.add_command(label="Open", command=self.openfile)
        self.filemenu.add_command(label="Save", command=self.save)
        self.filemenu.add_command(label="Save as", command=self.saveas)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=self.menu)
    
    def save(self, event=None):
        if not self.current_tab.filename:
            self.saveas(event)
        else:
            with open(self.current_tab.filename, "w") as file:
                file.write(self.current_tab.text.get_text())
    
    def saveas(self, event=None):
        fname = FD.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not fname: # asksaveasfile return "" if dialog closed with "cancel".
            return
        self.current_tab.filename = fname
        self.current_tab_button.config(text=fname)
        with open(fname, "w") as file:
            file.write(self.current_tab.text.get_text())
    

    def openfile(self, event=None):
        fname = FD.askopenfilename()
        if not (self.current_tab.filename is None and not self.current_tab.text.get_text()):
            self.current_tab = self.create_tab(filename=fname)
            self.current_tab_button = self.tab_buttons[0]
        else:
            self.current_tab_button.config(text=fname)

        with open(fname, "r") as file:
            text = file.read()
            self.current_tab.text.set_text(text)
        for line_number in range(len(self.current_tab.text)):
            self.current_tab.update_line(line_number)
        
        self.current_tab.init_cursor()


    def resize(self, event):
        if event.widget is self.root:
            if self.window_shape != (event.width, event.height):
                self.window_shape = (event.width, event.height)
                for tab in self.tabs:
                    tab.canvas.config(width = event.width, height = event.height)


    def bindings(self):
        bind = self.root.bind

        bind("<Control-s>", self.save)
        bind("<Control-S>", self.saveas)  # capital s
        bind("<Control-o>", self.openfile)

        bind("<Configure>", self.resize)


    def mainloop(self):
        self.root.mainloop()



def main():
    t = TextEditor()
    t.mainloop()

if __name__ == "__main__":
    main()


