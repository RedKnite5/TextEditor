
import tkinter as tk
from tkinter import Tk, Frame, Button, Menu, Canvas
import tkinter.font as tkFont
from tkinter import filedialog as FD

from collections import deque, namedtuple
from itertools import islice
from string import printable

# TODO:
# highlight current line
# scrollbar
# line numbers
# dark theme
# close tabs

# blink cursor (not working)
# variable character width (too hard)


Point = namedtuple('Point', ['x', 'y'])

class DummyEvent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class Selection:
    def __init__(self, startx=None, starty=None, endx=None, endy=None):
        self.start = Point(startx, starty)
        self.end = Point(endx, endy)

    def __bool__(self):
        return (None not in self.start) and (None not in self.end)
    
    @classmethod
    def from_start(cls, x, y):
        return cls(x, y)
    
    def from_end(self, x2, y2):
        return self.__class__(self.start.x, self.start.y, x2, y2)

class SliceDeque(deque):
    def __getitem__(self, index):
        if isinstance(index, slice):
            start = index.start or 0
            if index.stop is None:
                stop = len(self)
            else:
                stop = index.stop
            step = index.step or 1

            self.rotate(-start)
            cut = list(islice(self, 0, stop-start, step))
            self.rotate(start)
            return cut
        else:
            return super().__getitem__(index)
    
    def __delitem__(self, index):
        if isinstance(index, slice):
            start = index.start or 0
            if index.stop is None:
                stop = len(self)
            else:
                stop = index.stop
            step = index.step or 1
            assert step == 1  # TODO: implement step

            self.rotate(-start)
            for i in range(stop-start):
                self.popleft()
            self.rotate(start)
        else:
            super().__delitem__(index)

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
    
    def duplicate_line(self):
        self.lines.insert(self.y, SliceDeque(self.current_line()))
        self.y += 1
    
    def newline(self):
        remaining_text = ""
        if remaining_text := self.current_line()[self.x:]:
            # TODO: should do differently depending on which side of the line the cursor is closer to
            del self.current_line()[self.x:self.x + len(remaining_text)]
        self.lines.insert(self.y + 1, SliceDeque(remaining_text))
        self.y += 1
        self.x = 0
    
    def backspace(self) -> tuple[int]:
        # return (line number, 0|1|2) if 0, 1, or more than one line needs to be updated
        if self.x > 0:
            del self.current_line()[self.x - 1]
            self.x -= 1
            return (self.y, 1)
        elif self.y > 0:
            length = len(self.lines[self.y - 1])
            self.lines[self.y - 1].extend(self.current_line())
            del self.lines[self.y]
            self.y -= 1
            self.x = length
            return (self.y, 2)
        return (-1, 0)
    
    def delete(self):
        if self.x < len(self.current_line()):
            del self.current_line()[self.x]
            return (self.y, 1)
        elif self.y < len(self.lines) - 1:
            self.current_line().extend(self.lines[self.y + 1])
            del self.lines[self.y + 1]
            return (self.y, 2)
        return (-1, 0)


class Tab:
    def __init__(self, root, filename=None):
        self.root = root
        self.text = TextArray()

        self.filename = filename

        w, h = root.winfo_width(), root.winfo_height()
        self.canvas = Canvas(self.root, width=w, height=h)
        self.canvas.grid(row=1, column=0, sticky="w")
        
        self.highlight_color = "light blue"
        self.text_color = "black"
        self.font_size = 12
        self.font = tkFont.Font(family="Courier", size=self.font_size)
        self.char_width = self.font.measure("A")
        self.char_height = self.font.metrics("linespace") + 1
        self.x_offset = 10
        self.x_cursor_offset = self.x_offset - 2
        self.y_offset = 5

        self.selection = None
        self.canvas.focus_set()
        self.bindings()
        self.init_cursor()

    def init_cursor(self):
        self.canvas.create_line(
            self.x_cursor_offset,                     # x1
            self.y_offset,                            # y1
            self.x_cursor_offset,                     # x2
            self.char_height + self.y_offset - 2,     # y2
            tag="cursor"
        )
        #self.cursor_shown = True
        #self.canvas.after(500, self.toggle_cursor)
    
    """
    def toggle_cursor(self):
        print("toggle", not self.cursor_shown)
        if self.cursor_shown:
            self.canvas.itemconfig("cursor", state="hidden")
        else:
            self.canvas.itemconfig("cursor", state="normal")
        
        # cursor will move while hidden is strange ways if I dont do this
        self.update_cursor()
        self.cursor_shown = not self.cursor_shown
        self.canvas.after(500, self.toggle_cursor)
    """

    def update_cursor(self):
        self.canvas.moveto(
            "cursor",
            self.text.x * self.char_width + self.x_cursor_offset,
            self.text.y * self.char_height + self.y_offset
        )
    
    def update_line(self, line_number):
        self.canvas.delete(f"line_{line_number}")
        text = "".join(self.text[line_number]) if line_number < len(self.text) else ""
        self.canvas.create_text(
            self.x_offset,                                      # x
            self.char_height * line_number + self.y_offset,     # y
            text=text,
            anchor='nw',
            font=self.font,
            fill=self.text_color,
            tag=f"line_{line_number}"
        )

    def arrow(self, direction):
        def arrow_press(event):
            self.selection = None
            self.canvas.delete("selection")
            
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
                if self.text.x > len(self.text.current_line()):
                    self.text.x = len(self.text.current_line())
            elif direction == "down" and self.text.y < len(self.text.lines) - 1:
                self.text.y += 1
                if self.text.x > len(self.text.current_line()):
                    self.text.x = len(self.text.current_line())
            
            self.update_cursor()
        return arrow_press

    def key_press(self, event):
        if not event.char or event.char not in printable:
            return
        if self.selection:
            self.delete_selection()

        self.text.insert(event.char)
        self.update_line(self.text.y)
        self.update_cursor()
    
    def enter_key(self, event=None):
        if self.selection:
            self.delete_selection()
        self.text.newline()
        for i in range(self.text.y - 1, len(self.text)):
            self.update_line(i)
        self.update_cursor()

    def backspace(self, event):
        if self.selection:
            self.delete_selection()
            return
        to_update = self.text.backspace()
        self.update_cursor()
        if to_update[1] == 0:
            return
        elif to_update[1] == 1:
            self.update_line(to_update[0])
        else:
            for line_number in range(to_update[0], len(self.text)+1):
                self.update_line(line_number)
        
    def delete(self, event=None):
        if self.selection:
            self.delete_selection()
            return
        to_update = self.text.delete()
        if to_update[1] == 0:
            return
        elif to_update[1] == 1:
            self.update_line(to_update[0])
        else:
            for line_number in range(to_update[0], len(self.text)+1):
                self.update_line(line_number)
    
    def delete_selection(self):
        if not self.selection:
            return
        
        x1, y1 = self.selection.start
        x2, y2 = self.selection.end

        if y1 > y2:
            x2, x1 = x1, x2
            y2, y1 = y1, y2
        elif y1 == y2 and x1 > x2:
            x2, x1 = x1, x2

        self.text.cursor = [x1, y1]
        self.update_cursor()
        self.selection = None
        self.canvas.delete("selection")

        if y1 == y2:
            del self.text[y1][x1:x2] # possibly x1 + 1:x2
            self.update_line(y1)
            return
        length = len(self.text)
        new_y2 = y2
        line_pops = y2 - y1 - 1
        if line_pops:
            del self.text.lines[y1 + 1:y2]
            new_y2 -= line_pops
        
        del self.text[y1][x1:]
        del self.text[new_y2][:x2]
        self.delete()

        for line_num in range(y1, length):
            self.update_line(line_num)

    def ctrl_c(self, event=None):
        if self.selection:
            s = ""
            for line_number in range(self.selection.start.y, self.selection.end.y + 1):
                if line_number == self.selection.start.y:
                    start = self.selection.start.x
                else:
                    start = 0
                if line_number == self.selection.end.y:
                    end = self.selection.end.x
                else:
                    end = len(self.text[line_number])
                s += "".join(self.text[line_number][start:end]) + "\n"
            self.root.clipboard_clear()
            self.root.clipboard_append(s[:-1])
            self.root.update()
    
    def ctrl_v(self, event):
        t = self.root.clipboard_get()
        if not t:
            if self.selection:
                self.delete_selection()
            return
        
        for char in t:
            if char == "\n":
                self.enter_key()
            else:
                self.key_press(DummyEvent(char=char))

    def ctrl_d(self, event):
        self.text.duplicate_line()
        for i in range(self.text.y - 1, len(self.text)):
            self.update_line(i)
        self.update_cursor()

    def ctrl_x(self, event):
        self.ctrl_c()
        self.delete_selection()

    def ctrl_a(self, event):
        self.selection = Selection(0, 0, len(self.text[-1]), len(self.text) - 1)
        self.highlight_selection(self.selection)

    def mouse_press(self, event):
        x, y = self.move_cursor(event.x, event.y)
        #self.toggle_cursor() # this is a for testing
        self.canvas.delete("selection")
        self.selection = Selection.from_start(x, y)


    def mouse_move(self, event):
        x, y = self.move_cursor(event.x, event.y)
        self.selection = self.selection.from_end(x, y)
        self.highlight_selection(self.selection)

    def move_cursor(self, xp, yp):
        x = round((xp - self.x_offset) / self.char_width)
        y = round((yp - self.y_offset - self.char_height / 2) / self.char_height)
        
        if y < 0:
            y = 0
        if x < 0:
            x = 0
        if y >= len(self.text):
            y = len(self.text) - 1
        if x > len(self.text[y]):
            x = len(self.text[y])
        self.text.x = x
        self.text.y = y
        self.update_cursor()
        return x, y
    
    def highlight_selection(self, selection):
        if selection.start.y > selection.end.y:
            selection = Selection(*selection.end, *selection.start)
        
        self.canvas.delete("selection")

        for line_number in range(selection.start.y, selection.end.y + 1):
            y1 = line_number * self.char_height + self.y_offset
            y2 = (line_number + 1) * self.char_height + self.y_offset
            if line_number == selection.start.y:
                x1 = selection.start.x * self.char_width + self.x_cursor_offset
            else:
                x1 = self.x_cursor_offset
            if line_number == selection.end.y:
                x2 = selection.end.x * self.char_width + self.x_cursor_offset
            else:
                x2 = len(self.text[line_number]) * self.char_width + self.x_cursor_offset

            self.canvas.create_rectangle(
                x1, y1,
                x2, y2,
                fill=self.highlight_color,
                tag="selection"
            )
            self.canvas.lower("selection")

    
    def bindings(self):
        bind = self.canvas.bind

        bind("<Key>", self.key_press)
        bind("<Return>", self.enter_key)
        bind("<BackSpace>", self.backspace)
        bind("<Delete>", self.delete)
        bind("<Left>", self.arrow("left"))
        bind("<Right>", self.arrow("right"))
        bind("<Up>", self.arrow("up"))
        bind("<Down>", self.arrow("down"))

        bind("<Control-c>", self.ctrl_c)
        bind("<Control-v>", self.ctrl_v)
        bind("<Control-d>", self.ctrl_d)
        bind("<Control-x>", self.ctrl_x)
        bind("<Control-a>", self.ctrl_a)

        bind("<Button-1>", self.mouse_press)
        bind("<B1-Motion>", self.mouse_move)

class CurrentTab:
    def __set_name__(self, instance, name):
        self.name = name

    def __set__(self, instance, value):
        try:
            instance.current_tab.button.config(bg="SystemButtonFace")   # default button color
        except AttributeError:
            pass
        instance.__dict__[self.name] = value
        instance.current_tab_button = value.button
        value.canvas.focus_set()
        value.button.config(bg="grey")

class TextEditor:
    current_tab = CurrentTab()

    def __init__(self):
        self.root = Tk()
        self.root.title("Text Editor")
        self.window_shape = (500, 500)
        self.root.geometry("x".join(map(str, self.window_shape)))

        self.tab_buttons_fame = Frame(self.root)
        self.tab_buttons_fame.grid(row=0, column=0, sticky="w")

        self.tabs = []
        self.tab_buttons = []
        self.newfile()

        self.bindings()
        self.init_menu()

    def create_tab(self, filename=None):
        tab = Tab(self.root, filename=filename)

        text = tab.filename if tab.filename else "untitled"
        button = Button(self.tab_buttons_fame, text=text, command=self.select_tab(tab, len(self.tabs)))
        button.grid(row=0, column=len(self.tabs))
        tab.button = button
        self.tab_buttons.append(button)
        self.tabs.append(tab)

        return tab
    
    def select_tab(self, tab, button_index):
        def select():
            #tab.canvas.lift() # doesn't work for this purpose
            # this is the only way I could find to raise a canvas as canvas
            # overloaded it to raise drawn items instead of the canvas itself
            tk.Widget.lift(tab.canvas)
            
            self.current_tab = tab
        return select

    def init_menu(self):
        self.menu = Menu(self.root)
        self.filemenu = Menu(self.menu, tearoff=0)
        self.filemenu.add_command(label="New", command=self.newfile)
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
        if not fname:
            return
        if not (self.current_tab.filename is None and not self.current_tab.text.get_text()):
            self.current_tab = self.create_tab(filename=fname)
        else:
            self.current_tab_button.config(text=fname)
            self.current_tab.filename = fname

        with open(fname, "r") as file:
            text = file.read()
        self.current_tab.text.set_text(text)
        for line_number in range(len(self.current_tab.text)):
            self.current_tab.update_line(line_number)
        
        self.current_tab.init_cursor()

    def newfile(self, event=None):
        self.current_tab = self.create_tab()

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
        bind("<Control-n>", self.newfile)

        bind("<Configure>", self.resize)

    def mainloop(self):
        self.root.mainloop()



def main():
    t = TextEditor()
    t.mainloop()

if __name__ == "__main__":
    main()


