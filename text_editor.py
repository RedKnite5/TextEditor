

import tkinter as tk
from tkinter import Tk, Frame, Button, Menu, Canvas, Scrollbar
import tkinter.font as tkFont
from tkinter import filedialog as FD

from string import printable

from DataStructures import *

# TODO:
# highlight current line
# dark theme
# undo/redo
# find/replace
# align text in menu labels
# scroll tab list


# INDEFINATE DELAY:
# variable character width (too hard)
# bind horizontal scrolling to horizontal scrollbar (no binding for horizontal scrolling on Windows)

# BUGS:
# holding down keys can cause the screen not to update



class DummyEvent:
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


class Tab:
	def __init__(self, root, filename=None):
		self.root = root
		self.text = TextArray()

		self.filename = filename

		self.linenumbers = True
		yview = self.yview_canvases if self.linenumbers else self.canvas.yview

		self.frame = tk.Frame(self.root)
		self.canvas = Canvas(self.frame, highlightthickness=0)
		self.vbar = Scrollbar(self.frame, orient="vertical", command=yview)
		self.hbar = Scrollbar(
			self.frame,
			orient="horizontal",
			command=self.canvas.xview
		)

		self.frame.grid(row=1, column=0, sticky="w")
		self.canvas.grid(row=0, column=1, sticky="news")
		self.vbar.grid(row=0, column=2, sticky="nse")
		self.hbar.grid(row=1, column=0, columnspan=2, sticky="ews")
		
		self.canvas.config(
			xscrollcommand=self.hbar.set,
			yscrollcommand=self.vbar.set
		)
		self.canvas.config(scrollregion=self.canvas.bbox("all"))

		self.highlight_color = "light blue"
		self.set_font_info()

		self.selection = None
		self.canvas.focus_set()
		self.init_cursor()

		self.linenumber_canvas_width = 0

		if self.linenumbers:
			self.linenumber_canvas_width = self.char_width * 5 + 4
			self.linenumber_canvas = tk.Canvas(
				self.frame,
				width=self.linenumber_canvas_width,
				highlightthickness=0
			)
			self.linenumber_canvas.grid(row=0, column=0, sticky="news")
			self.create_line_number(1)

			#self.linenumber_canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
			self.linenumber_canvas.config(
				scrollregion=self.linenumber_canvas.bbox("all")
			)
		
		self.bindings()
		self.update_cursor()

	def set_font_info(self):
		self.text_color = "black"
		self.font_size = 12
		self.font = tkFont.Font(family="Courier", size=self.font_size)
		self.char_width = self.font.measure("A")
		self.char_height = self.font.metrics("linespace") + 1
		self.x_offset = 10
		self.y_offset = 5
		self.x_cursor_offset = self.x_offset - 2

	def init_cursor(self):
		self.cursor_shown = True
		self.canvas.after(500, self.toggle_cursor)
		self.canvas.create_line(
			self.x_cursor_offset,                     # x1
			self.y_offset,                            # y1
			self.x_cursor_offset,                     # x2
			self.char_height + self.y_offset - 2,     # y2
			tag="cursor"
		)

	def toggle_cursor(self):
		if self.cursor_shown:
			self.canvas.itemconfig("cursor", state="hidden")
		else:
			self.canvas.itemconfig("cursor", state="normal")
		
		# cursor will move while hidden is strange ways if I dont do this
		self.update_cursor()
		self.cursor_shown = not self.cursor_shown
		self.canvas.after(500, self.toggle_cursor)

	def yview_canvases(self, *args):
		self.canvas.yview(*args)
		self.linenumber_canvas.yview(*args)

	def create_line_number(self, line_number):
		self.linenumber_canvas.create_text(
			2,
			(line_number - 1) * self.char_height + self.y_offset,
			text=f"{line_number:>5}",
			tag="line_num_" + str(line_number),
			anchor="nw",
			font=self.font,
			fill="light gray"
		)

	def delete_line_number(self, line_number=None):
		if line_number is None:
			line_number = len(self.text) + 1
		self.linenumber_canvas.delete("line_num_" + str(line_number))

	def update_cursor(self):
		self.canvas.moveto(
			"cursor",
			self.text.x * self.char_width + self.x_cursor_offset,
			self.text.y * self.char_height + self.y_offset
		)
		self.canvas.config(scrollregion=self.canvas.bbox("all"))   # not entirely sure when this needs to happen
		if self.linenumbers:
			self.linenumber_canvas.config(
				scrollregion=self.linenumber_canvas.bbox("all")
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
			elif direction == "up" and self.text.y > 0:
				self.text.y -= 1
				if self.text.x > len(self.text.current_line()):
					self.text.x = len(self.text.current_line())
			elif direction == "down" and self.text.y < len(self.text.lines) - 1:
				self.text.y += 1
				if self.text.x > len(self.text.current_line()):
					self.text.x = len(self.text.current_line())
			
			self.update_cursor()

			self.scroll_to_see_cursor()

			
		return arrow_press

	def key_press(self, event):
		if not event.char or event.char not in printable:
			return
		if self.selection:
			self.delete_selection()

		self.text.insert(event.char)
		self.update_line(self.text.y)
		self.update_cursor()
		self.scroll_to_see_cursor()

	def enter_key(self, event=None):
		if self.selection:
			self.delete_selection()
		self.text.newline()
		for i in range(self.text.y - 1, len(self.text)):
			self.update_line(i)
		self.update_cursor()

		if self.linenumbers:
			self.create_line_number(len(self.text))

		self.scroll_to_see_cursor()

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
				if self.linenumbers:
					self.delete_line_number()
			self.scroll_to_see_cursor()

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
				if self.linenumbers:
					self.delete_line_number()

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

		if self.linenumbers:
			for line_num in range(length - line_pops, length):
				self.delete_line_number(line_num+1)

	def ctrl_c(self, event=None):
		if self.selection:
			x1, y1 = self.selection.start
			x2, y2 = self.selection.end

			if y1 > y2:
				x2, x1 = x1, x2
				y2, y1 = y1, y2
			elif y1 == y2 and x1 > x2:
				x2, x1 = x1, x2

			s = ""
			for line_number in range(y1, y2 + 1):
				if line_number == y1:
					start = x1
				else:
					start = 0
				if line_number == y2:
					end = x2
				else:
					end = len(self.text[line_number])
				s += "".join(self.text[line_number][start:end]) + "\n"
			self.root.clipboard_clear()
			self.root.clipboard_append(s[:-1])
			self.root.update()

	def ctrl_v(self, event=None):
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

	def ctrl_d(self, event=None):
		self.text.duplicate_line()
		for i in range(self.text.y - 1, len(self.text)):
			self.update_line(i)
		self.update_cursor()

	def ctrl_x(self, event=None):
		self.ctrl_c()
		self.delete_selection()

	def ctrl_a(self, event=None):
		self.selection = Selection(0, 0, len(self.text[-1]), len(self.text) - 1)
		self.highlight_selection(self.selection)

	def mouse_press(self, event):
		cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		x, y = self.move_cursor(cx, cy)
		self.canvas.delete("selection")
		self.selection = Selection.from_start(x, y)

	def mouse_move(self, event):
		cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		x, y = self.move_cursor(cx, cy)
		self.selection = self.selection.from_end(x, y)
		self.highlight_selection(self.selection)

	def scrollwheel(self, event):
		if self.vbar.get() == (0, 1):
			return
		self.canvas.yview_scroll(-1*int(event.delta/120), "units")
		if self.linenumbers:
			self.linenumber_canvas.yview_scroll(-1*int(event.delta/120), "units")

	def scroll_to_see_cursor(self):
		t, b = self.vbar.get()
		l, r = self.hbar.get()
		can_height = int(self.canvas["height"])
		can_width = int(self.canvas["width"])
		boundingbox = self.canvas.bbox("all")
		scrollable_height = boundingbox[3]
		scrollable_width = boundingbox[2]
		top_of_screen = t * scrollable_height
		bottom_of_screen = b * scrollable_height
		left_of_screen = l * scrollable_width
		right_of_screen = r * scrollable_width

		cursor_vpos = self.text.y * self.char_height + self.y_offset
		cursor_hpos = self.text.x * self.char_width + self.x_offset

		if cursor_vpos + 2 * self.char_height > max(bottom_of_screen, can_height):
			print("scroll down")
			new_y = (cursor_vpos + self.char_height - can_height) / scrollable_height
			self.canvas.yview_moveto(new_y)
		elif cursor_vpos < top_of_screen:
			print("scroll up")
			new_y = cursor_vpos / scrollable_height
			self.canvas.yview_moveto(new_y)
		
		if cursor_hpos + self.char_width > max(right_of_screen, can_width):
			print("scroll right")
			new_x = (cursor_hpos + self.char_width - can_width) / scrollable_width
			self.canvas.xview_moveto(new_x)
		elif cursor_hpos < left_of_screen:
			print("scroll left")
			new_x = cursor_hpos / scrollable_width
			self.canvas.xview_moveto(new_x)

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
		bind("<MouseWheel>", self.scrollwheel)
		if self.linenumbers:
			self.linenumber_canvas.bind("<MouseWheel>", self.scrollwheel)

	def destroy_widgets(self):
		self.frame.destroy()
		# must destroy widgets before tag object can be garbage collected
		self.canvas.destroy()
		self.linenumber_canvas.destroy()
		self.vbar.destroy()
		self.hbar.destroy()


class CurrentTab:
	def __set_name__(self, instance, name):
		self.name = name

	def __set__(self, instance, value):
		try:
			if instance.current_tab.button.winfo_exists():
				instance.current_tab.button.config(bg="SystemButtonFace")   # default button color
				instance.current_tab.close_button.config(bg="SystemButtonFace")
		except AttributeError:
			pass
		instance.__dict__[self.name] = value
		instance.current_tab_button = value.button
		value.button.config(bg="grey")
		value.close_button.config(bg="grey")
		value.canvas.focus_set()

class TextEditor:
	current_tab = CurrentTab()

	def __init__(self):
		self.root = Tk()
		self.root.title("Text Editor")
		self.window_shape = (500, 400)
		self.root.geometry("x".join(map(str, self.window_shape)))

		# very difficult to get these values dynamically
		self.vbar_width = 17 #self.current_tab.vbar.winfo_width()
		self.hbar_height = 17 #self.current_tab.hbar.winfo_height()
		self.tab_buttons_height = 26 #self.tab_buttons_fame.winfo_height()

		self.tab_buttons_fame = Frame(self.root)
		self.tab_buttons_fame.grid(row=0, column=0, sticky="we")

		self.scroll_tabs = Scrollbar(self.tab_buttons_fame, orient="horizontal")
		self.tab_button_canvas = Canvas(
			self.tab_buttons_fame,
			height=self.tab_buttons_height,
			bd=0,
			highlightthickness=0,
			xscrollcommand=self.scroll_tabs.set
		)

		self.scroll_tabs.config(command=self.tab_button_canvas.xview)

		self.scroll_tabs.pack(side="right", fill="x")
		self.tab_button_canvas.pack(fill="x")

		self.inner_frame = Frame(self.tab_button_canvas, height=self.tab_buttons_height)

		self.tab_button_canvas.create_window(
			(4, 4),
			height=self.tab_buttons_height,
			tags="window",
			window=self.inner_frame
		)

		self.inner_frame.bind("<Configure>", self.on_button_mod)




		self.tabs = {}
		self.tab_buttons = {}
		self.newfile()

		self.bindings()
		self.init_menu()

	def on_button_mod(self, event):
		self.tab_button_canvas.configure(scrollregion=self.tab_button_canvas.bbox("all"))

	def create_tab(self, filename=None):
		tab = Tab(self.root, filename=filename)

		text = tab.filename if tab.filename else "untitled"
		button = Button(
			self.inner_frame,
			text=text,
			command=self.select_tab(tab)
		)
		close_button = Button(
			self.inner_frame,
			width=2,
			text="X",
			fg="red",
			command=self.close_tab(tab, id(button))
		)

		#button.grid(row=0, column=2 * len(self.tabs))
		#close_button.grid(row=0, column=1 + 2 * len(self.tabs))
		button.pack(side="left")
		close_button.pack(side="left")

		tab.button = button
		tab.close_button = close_button
		self.tab_buttons[id(button)] = (
			button,
			close_button
			)
		self.tabs[id(button)] = tab

		self.resize_tab(tab)

		return tab

	def select_tab(self, tab):
		def select():
			# old code preserved for posterity
			# tab.canvas.lift() # doesn't work for this purpose
			# this is the only way I could find to raise a canvas as canvas
			# overloaded it to raise drawn items instead of the canvas itself
			#tk.Widget.lift(tab.canvas)

			self.current_tab.frame.grid_remove()
			tab.frame.grid()

			self.current_tab = tab
		return select

	def close_tab(self, tab, button_id):
		def close():
			self.tab_buttons[button_id][0].grid_forget()
			self.tab_buttons[button_id][1].grid_forget()
			self.tab_buttons[button_id][0].destroy()
			self.tab_buttons[button_id][1].destroy()
			del self.tab_buttons[button_id]
			tab.destroy_widgets()
			del self.tabs[button_id]

			if self.current_tab == tab:
				if len(self.tabs) > 0:
					next_tab = tuple(self.tabs.values())[0]
					next_tab.frame.grid()
					self.current_tab = next_tab
					#del self.tabs[button_id]
				else:
					#del self.tabs[button_id]
					self.newfile()

		return close

	def init_menu(self):
		self.menu = Menu(self.root)
		self.filemenu = Menu(self.menu, tearoff=0)
		self.filemenu.add_command(label="New                 Ctrl+n", command=self.newfile)
		self.filemenu.add_command(label="Open                Ctrl+o", command=self.openfile)
		self.filemenu.add_command(label="Save                Ctrl+s", command=self.save)
		self.filemenu.add_command(label="Save as       Ctrl+Shift+s", command=self.saveas)
		self.menu.add_cascade(label="File", menu=self.filemenu)

		self.editmenu = Menu(self.menu, tearoff=0)
		self.editmenu.add_command(label="Cut                 Ctrl-x", command=self.delegate_to_tab("ctrl_x"))
		self.editmenu.add_command(label="Copy                Ctrl-c", command=self.delegate_to_tab("ctrl_c"))
		self.editmenu.add_command(label="Paste               Ctrl-v", command=self.delegate_to_tab("ctrl_v"))
		self.menu.add_cascade(label="Edit", menu=self.editmenu)
		self.root.config(menu=self.menu)

	def delegate_to_tab(self, method):
		return lambda: getattr(self.current_tab, method)()

	def save(self, event=None):
		if not self.current_tab.filename:
			self.saveas(event)
		else:
			with open(self.current_tab.filename, "w") as file:
				file.write(self.current_tab.text.get_text())

	def saveas(self, event=None):
		fname = FD.asksaveasfilename(
			defaultextension=".txt",
			filetypes=[("Text Files", "*.txt")]
		)
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
		if self.current_tab.filename is None and not self.current_tab.text.get_text():
			self.current_tab_button.config(text=fname)
			self.current_tab.filename = fname
		else:
			self.current_tab = self.create_tab(filename=fname)

		with open(fname, "r") as file:
			text = file.read()
		self.current_tab.text.set_text(text)
		for line_number in range(len(self.current_tab.text)):
			self.current_tab.update_line(line_number)
			if self.current_tab.linenumbers:
				self.current_tab.create_line_number(line_number+1)
		self.current_tab.update_cursor()

	def newfile(self, event=None):
		self.current_tab = self.create_tab()

	def on_resize(self, event):
		if event.widget is self.root:
			if self.window_shape != (event.width, event.height):
				self.window_shape = (event.width, event.height)
				for tab in self.tabs.values():
					self.resize_tab(tab, event.width, event.height)

	def resize_tab(self, tab, width=None, height=None):
		if not width or not height:
			width, height = self.window_shape
		new_width = width - self.vbar_width - tab.linenumber_canvas_width
		new_height = height - self.tab_buttons_height - self.hbar_height
		tab.canvas.config(width = new_width, height = new_height)
		if tab.linenumbers:
			tab.linenumber_canvas.config(height = new_height)

	def bindings(self):
		bind = self.root.bind

		bind("<Control-s>", self.save)
		bind("<Control-S>", self.saveas)  # capital s
		bind("<Control-o>", self.openfile)
		bind("<Control-n>", self.newfile)

		bind("<Configure>", self.on_resize)

	def mainloop(self):
		self.root.mainloop()



def main():
	t = TextEditor()
	t.mainloop()

if __name__ == "__main__":
	main()
