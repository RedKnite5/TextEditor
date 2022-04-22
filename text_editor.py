

from cgitb import text
from tkinter import (
	Tk, Frame, Button, Menu, Canvas, Scrollbar, Toplevel, Label, Entry,
)
import tkinter.font as tkFont
from tkinter import filedialog as FD

from string import printable

import pyperclip

from DataStructures import *

# TODO:
# highlight current line
# dark theme
# undo/redo
# find/replace
# align text in menu labels
# variable character width and make tab key work
# dont have cursor toggled off while typing


# INDEFINATE DELAY:
# bind horizontal scrolling to horizontal scrollbar (no binding for horizontal scrolling on Windows)

# BUGS:
# holding down keys can cause the screen not to update
# ctrl+d doesn't update linenumbers



class DummyEvent:
	"""Class to mimic events for fuctions that are bound to an event and
	are called independently"""

	def __init__(self, **kwargs):
		"""Set all keyword arguments to instance variables"""

		self.__dict__.update(kwargs)


class FindReplaceWindow:
	"""Class to create a window for finding and replacing text"""

	def __init__(
		self,
		parent,
		text_array,
		highlight,
		replace,
		update_cursor,
		scroll,
	):
		self.root = parent
		self.text_array = text_array
		self.highlight = highlight
		self.replace = replace
		self.update_cursor = update_cursor
		self.scroll = scroll

		self.win = Toplevel(self.root)
		self.win.title("Find")

		self.label = Label(self.win, text="Find:")
		self.entry = Entry(self.win)
		self.find_prev = Button(
			self.win,
			text="▲",
			command=self.find_next_or_prev(-1)
		)
		self.find_next = Button(
			self.win,
			text="▼ Find Next",
			command=self.find_next_or_prev(1)
		)
		self.error_label = Label(self.win, text="")


		self.label.grid(row=0, column=0)
		self.entry.grid(row=0, column=1)
		self.find_prev.grid(row=0, column=2)
		self.find_next.grid(row=0, column=3)
		self.error_label.grid(row=2, column=0, columnspan=4)

		self.replace_label = Label(self.win, text="Replace with:")
		self.replace_entry = Entry(self.win)
		self.replace_but = Button(
			self.win,
			text="Replace",
			command=self.replace_text
		)
		self.replace_all_but = Button(
			self.win,
			text="Replace All",
			command=self.replace_all
		)

		self.replace_config()

		self.entry.focus_set()

		self.entry.bind("<Return>", self.find)

		self.find_text = None
		self.occurances = None
		self.showing = 0
	
	def replace_config(self, event=None):
		self.replace_label.grid(row=1, column=0)
		self.replace_entry.grid(row=1, column=1)
		self.replace_but.grid(row=1, column=2)
		self.replace_all_but.grid(row=1, column=3)

	def find_next_or_prev(self, inc):
		def find_suc(event=None):

			if self.find_text != (tmp := self.entry.get()):
				self.showing = -1
				self.find_text = tmp
			if self.find_text == "":
				return

			text = self.text_array.get_text()
			self.occurances = text.split(self.find_text)

			self.showing += inc
			if self.showing < 0:
				self.showing %= len(self.occurances) - 1
			selection = self.nth_occurance(self.showing)
			if selection is None:
				if self.find_text is None:
					self.error_label.config(text="No text to find")
				else:
					self.error_label.config(text=f"Can not find '{self.find_text}'")
				return
			self.error_label.config(text="")
			self.highlight(selection)

			self.text_array.x = selection.end.x
			self.text_array.y = selection.end.y
			self.scroll()
			self.update_cursor()

		return find_suc

	def find(self, event=None):
		"""Find the text in the entry box and highlight it on the canvas and set
		self.occurances to the text separated by the occurances"""

		self.find_text = self.entry.get()
		if self.find_text == "":
			return
		
		text = self.text_array.get_text()

		self.occurances = text.split(self.find_text)
		self.showing = -1
		self.find_next_or_prev(1)()

	def nth_occurance(self, n):
		"""Return a selection of the nth occurance of the text in the entry box"""

		if n > len(self.occurances or ()) - 2:
			return None

		occurances_before = self.occurances[:n + 1]
		text_before = self.find_text.join(occurances_before)

		newlines_in_find = self.find_text.count("\n")

		y1 = text_before.count("\n")

		x1 = len(text_before.split("\n")[-1])

		y2 = newlines_in_find + y1
		if newlines_in_find:
			x2 = len(self.find_text.split("\n")[-1])
		else:
			x2 = x1 + len(self.find_text)
		
		return Selection(x1, y1, x2, y2)

	def replace_text(self):
		pass

	def replace_all(self):
		pass



class Tab:
	def __init__(self, root, filename=None):
		self.root = root
		self.text = TextArray()

		self.filename = filename

		self.linenumbers = True
		yview = self.yview_canvases if self.linenumbers else self.canvas.yview

		self.frame = Frame(self.root)
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
			self.linenumber_canvas = Canvas(
				self.frame,
				width=self.linenumber_canvas_width,
				highlightthickness=0
			)
			self.linenumber_canvas.grid(row=0, column=0, sticky="news")
			self.create_line_number(1)

			self.linenumber_canvas.config(
				scrollregion=self.linenumber_canvas.bbox("all")
			)
		
		self.bindings()
		self.update_cursor()

	def set_font_info(self):
		"""Set infomation about the font and cursor location"""

		self.text_color = "black"
		self.font_size = 20
		self.font = tkFont.Font(family="Cascadia Code ExtraLight", size=self.font_size)
		self.char_width = self.font.measure("A")
		self.char_height = self.font.metrics("linespace") + 1
		self.x_offset = 10
		self.y_offset = 5
		self.x_cursor_offset = self.x_offset - 2

	def init_cursor(self):
		"""Create the cursor so that it can be moved later and start toggling
		it"""

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
		"""Toggle whether the cursor is shown or not.
		
		After that schedual this function to be called again."""

		if self.cursor_shown:
			self.canvas.itemconfig("cursor", state="hidden")
		else:
			self.canvas.itemconfig("cursor", state="normal")
		
		# cursor will move while hidden is strange ways if I dont do this
		self.update_cursor()
		self.cursor_shown = not self.cursor_shown
		self.canvas.after(500, self.toggle_cursor)

	def yview_canvases(self, *args):
		"""A wrapper for the canvas.yview and linenumber_canvas methods
		so that they can be bound to the same scrollbar"""

		self.canvas.yview(*args)
		self.linenumber_canvas.yview(*args)

	def create_line_number(self, line_number):
		"""Create a line number on the line number canvas"""

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
		"""Delete a line number from the line number canvas.
		
		Defaults to the line number corosponding to the end of the TextArray
		if multiple lines have been deleted simultaniously this may not be the
		last line number."""

		if line_number is None:
			line_number = len(self.text) + 1
		self.linenumber_canvas.delete("line_num_" + str(line_number))

	def update_cursor(self):
		"""Move the cursor to the position specified by the TextArray.
		
		Also set the scrollregion of the canvases to the size of the text."""
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
		"""Draw the text on the canvas for a specific line"""

		self.canvas.delete(f"line_{line_number}")
		text = "".join(self.text[line_number]) if line_number < len(self.text) else ""
		# Can't just use itemconfig because it needs to be drawn a first time
		# Maybe if you add a check to see if it needs to be drawn
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
		"""Factory for arrow event fuctions"""

		if direction == "up":
			def up(event):
				"""Move the cursor up"""

				self.selection = None
				self.canvas.delete("selection")
				if self.text.y <= 0:
					return
				self.text.y -= 1
				if self.text.x > len(self.text.current_line()):
					self.text.x = len(self.text.current_line())

				self.update_cursor()
				self.scroll_to_see_cursor()
			return up
		elif direction == "down":
			def down(event):
				"""Move the cursor down"""

				self.selection = None
				self.canvas.delete("selection")
				if self.text.y >= len(self.text.lines) - 1:
					return
				self.text.y += 1
				if self.text.x > len(self.text.current_line()):
					self.text.x = len(self.text.current_line())

				self.update_cursor()
				self.scroll_to_see_cursor()
			return down
		elif direction == "left":
			def left(event):
				"""Move the cursor left"""

				self.selection = None
				self.canvas.delete("selection")
				if self.text.x > 0:
					self.text.x -= 1
				elif self.text.y > 0:
					self.text.y -= 1
					self.text.x = len(self.text.current_line())

				self.update_cursor()
				self.scroll_to_see_cursor()
			return left
		elif direction == "right":
			def right(event):
				"""Move the cursor right"""

				self.selection = None
				self.canvas.delete("selection")
				if self.text.x < len(self.text.current_line()):
					self.text.x += 1
				elif self.text.y < len(self.text) - 1:
					self.text.x = 0
					self.text.y += 1

				self.update_cursor()
				self.scroll_to_see_cursor()
			return right
		else:
			raise ValueError(f"{direction} is not a valid direction")

	def key_press(self, event):
		"""Insert a character into the text
		
		Also moves the cursor and updates the line and replaces any selected
		text."""

		if not event.char or event.char not in printable:
			return
		if self.selection:
			self.delete_selection()

		self.text.insert(event.char)
		self.update_line(self.text.y)
		self.update_cursor()
		self.scroll_to_see_cursor()

	def enter_key(self, event=None):
		"""Insert a newline into the TextArray

		Also moves the cursor and updates the line and replaces any selected
		text and draws a new line number."""

		if self.selection:
			self.delete_selection()
		self.text.newline()
		for i in range(self.text.y - 1, len(self.text)):
			self.update_line(i)
		self.update_cursor()

		if self.linenumbers:
			self.create_line_number(len(self.text))

		self.scroll_to_see_cursor()

	def backspace(self, event=None):
		"""Delete the character to the left of the cursor

		Possibly delete a line if the cursor is at the beginning of a line or a
		selection is something is selected. Also moves the cursor and redraws
		the line."""

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
		"""Delete the character to the right of the cursor

		Possibly delete a line if the cursor is at the end of a line or
		something is selected. Also moves the cursor and redraws the line."""

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
		"""Delete the selected text"""

		if not self.selection:
			return

		x1, y1 = self.selection.start
		x2, y2 = self.selection.end

		# Swap beginning and end if necessary
		if y1 > y2:
			x2, x1 = x1, x2
			y2, y1 = y1, y2
		elif y1 == y2 and x1 > x2:
			x2, x1 = x1, x2

		self.text.cursor = [x1, y1]
		self.update_cursor()
		self.selection = None
		self.canvas.delete("selection")

		if y1 == y2:  # if only deleting part of one line
			del self.text[y1][x1:x2]
			self.update_line(y1)
			return
		length = len(self.text)

		new_y2 = y2
		line_pops = y2 - y1 - 1
		if line_pops:   # delete lines that are being completly deleted
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
		"""Copy the selected text to the clipboard"""

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
			pyperclip.copy(s[:-1])

	def ctrl_v(self, event=None):
		"""Paste the text from the clipboard into the TextArray"""

		t = pyperclip.paste()
		self.replace(t)

	def replace(self, new_text, selection=None):
		if selection is None:
			selection = self.selection
			tmp_sel = None
		else:
			tmp_sel = self.selection

		if selection:
			self.delete_selection()

		for char in new_text:  # simulating keypresses
			if char == "\n":
				self.enter_key()
			else:
				self.key_press(DummyEvent(char=char))
		self.selection = tmp_sel

	def ctrl_d(self, event=None):
		"""Duplicate the current line"""

		self.text.duplicate_line()
		for i in range(self.text.y - 1, len(self.text)):
			self.update_line(i)
		self.update_cursor()

	def ctrl_x(self, event=None):
		"""Cut the selected text to the clipboard"""

		self.ctrl_c()
		self.delete_selection()

	def ctrl_a(self, event=None):
		"""Select all text"""

		self.selection = Selection(0, 0, len(self.text[-1]), len(self.text) - 1)
		self.highlight_selection(self.selection)

	def ctrl_f(self, event=None):
		"""Open find window"""

		self.find_window = FindReplaceWindow(
			parent=self.root,
			text_array=self.text,
			highlight=self.highlight_selection,
			replace=self.replace,
			update_cursor=self.update_cursor,
			scroll=self.scroll_to_see_cursor
		)

	def mouse_press(self, event):
		"""Move the cursor and unselect any selected text"""

		cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		x, y = self.move_cursor(cx, cy)
		self.canvas.delete("selection")
		self.selection = Selection.from_start(x, y)

	def mouse_move(self, event):
		"""Move the cursor and select new text"""

		cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		x, y = self.move_cursor(cx, cy)
		self.selection = self.selection.from_end(x, y)
		self.highlight_selection(self.selection)

	def scrollwheel(self, event):
		"""Scroll the text up or down as well as linenumbers"""

		if self.vbar.get() == (0, 1):
			return
		self.canvas.yview_scroll(-1*int(event.delta/120), "units")
		if self.linenumbers:
			self.linenumber_canvas.yview_scroll(-1*int(event.delta/120), "units")

	def scroll_to_see_cursor(self):
		"""Scroll the text so that the cursor is visible"""

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

		# max prevents scrolling everytime the canvas bounding box expands
		if cursor_vpos + 2 * self.char_height > max(bottom_of_screen, can_height):
			new_y = (cursor_vpos + self.char_height - can_height) / scrollable_height
			self.canvas.yview_moveto(new_y)
			if self.linenumbers:
				self.linenumber_canvas.yview_moveto(new_y)
		elif cursor_vpos < top_of_screen:
			new_y = cursor_vpos / scrollable_height
			self.canvas.yview_moveto(new_y)
			if self.linenumbers:
				self.linenumber_canvas.yview_moveto(new_y)
		
		if cursor_hpos + self.char_width > max(right_of_screen, can_width):
			new_x = (cursor_hpos + self.char_width - can_width) / scrollable_width
			self.canvas.xview_moveto(new_x)
		elif cursor_hpos < left_of_screen:
			new_x = (cursor_hpos - self.char_width) / scrollable_width
			self.canvas.xview_moveto(new_x)

	def move_cursor(self, xp, yp):
		"""Convert canvas coordinates to TextArray coordinates and move the
		TextArray cursor to the new position"""

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
		"""Highlight the selected text"""

		self.selection = selection

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
		"""Bind the keys/events to the appropriate functions"""

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
		bind("<Control-f>", self.ctrl_f)

		bind("<Button-1>", self.mouse_press)  # left click
		bind("<B1-Motion>", self.mouse_move)  # drag mouse while left click
		bind("<MouseWheel>", self.scrollwheel)
		if self.linenumbers:
			self.linenumber_canvas.bind("<MouseWheel>", self.scrollwheel)

	def destroy_widgets(self):
		"""Destroy all widgets belonging to the tab"""

		self.frame.destroy()
		# must destroy widgets before tag object can be garbage collected
		self.canvas.destroy()
		self.vbar.destroy()
		self.hbar.destroy()
		if self.linenumbers:
			self.linenumber_canvas.destroy()


class CurrentTab:
	"""Class to do things that need to be done every time the current tab is
	changed"""

	def __set_name__(self, instance, name):
		"""Set the variable name the current tab is given
		(expected to be "current_tab")"""

		self.name = name

	def __set__(self, instance, value):
		"""Set the current tab

		Set the color of previous tab button to the default color, set the
		current tab button to the selected color and the current_tab_button
		attribute to the tab button that was just pressed.

		Args:
			instance (TextEditor): The TextEditor instance
			value (Tab): The tab that is being selected
		"""

		try:
			if instance.current_tab.button.winfo_exists():
				instance.current_tab.button.config(bg="SystemButtonFace")   # default button color
				instance.current_tab.close_button.config(bg="SystemButtonFace")
		except AttributeError:  # if the current tab is None
			pass
		instance.__dict__[self.name] = value
		instance.current_tab_button = value.button
		value.button.config(bg="grey")
		value.close_button.config(bg="grey")
		value.canvas.focus_set()

class TextEditor:
	"""Main class that creates the GUI and contains the TextArray"""

	current_tab = CurrentTab()

	def __init__(self):
		self.root = Tk()
		self.root.title("Text Editor")
		self.window_shape = (500, 400)
		self.root.geometry("x".join(map(str, self.window_shape)))

		# very difficult to get these values dynamically. They are 1 if looked
		# up with the relevant methods too early. So I just hardcode them.
		self.vbar_width = 17 #self.current_tab.vbar.winfo_width()
		self.hbar_height = 17 #self.current_tab.hbar.winfo_height()
		self.tab_buttons_height = 26 #self.tab_buttons_fame.winfo_height()

		self.tab_row_creation()

		self.tabs = {}          # id(selection button): Tab
		self.tab_buttons = {}   # id(selection button): (selection button, close_button)
		self.newfile()

		self.bindings()
		self.init_menu()

	def init_menu(self):
		"""Create the menu bar and add the menu items"""

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

	def tab_row_creation(self):
		"""Create widgets related to displaying and controlling the different
		tabs and tab buttons that are open"""

		self.tab_buttons_fame = Frame(self.root)
		self.tab_buttons_fame.grid(row=0, column=0, sticky="we")

		self.scroll_tabs = Scrollbar(self.tab_buttons_fame, orient="horizontal")
		self.tab_button_canvas = Canvas(
			self.tab_buttons_fame,
			height=self.tab_buttons_height,
			xscrollcommand=self.scroll_tabs.set
		)

		self.scroll_tabs.config(command=self.tab_button_canvas.xview)

		self.scroll_tabs.pack(side="right", fill="y")
		self.tab_button_canvas.pack(fill="x")

		self.inner_frame = Frame(
			self.tab_button_canvas
		)

		self.windowID = self.tab_button_canvas.create_window(
			(0, 0),
			anchor="nw",
			height=self.tab_buttons_height,
			tags="window",
			window=self.inner_frame
		)

		self.inner_frame.bind("<Configure>", self.on_button_mod)

	def on_button_mod(self, event=None):
		"""Reisize the scrollable region of the canvas holding tab buttons
		when the inner_frame is resized aka when a button is added or removed
		so that it becomes scrollable when too many tabs to fit in the window
		are open."""

		self.tab_button_canvas.configure(scrollregion=self.tab_button_canvas.bbox("all"))

	def create_tab(self, filename=None):
		"""Create a new tab and is widgets and add it to the list of tabs"""

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
		"""Return a function that will select the tab"""

		def select():
			"""Set the new current tab and display the new tab's text"""

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
		"""Return a function that will close the tab"""

		def close():
			"""Remove the tab from the list of tabs and destroy the buttons to
			switch to the tab and set the new current tab"""

			buttons = self.tab_buttons[button_id]
			buttons[0].pack_forget()
			buttons[1].pack_forget()
			buttons[0].destroy()
			buttons[1].destroy()
			del self.tab_buttons[button_id]
			tab.destroy_widgets()
			del self.tabs[button_id]

			if self.current_tab == tab:
				if len(self.tabs) > 0:
					next_tab = tuple(self.tabs.values())[0]
					next_tab.frame.grid()
					self.current_tab = next_tab
				else:
					self.newfile()

		return close

	def delegate_to_tab(self, method):
		"""Return a function that will call the current_tab's method"""

		return lambda: getattr(self.current_tab, method)()

	def save(self, event=None):
		"""Save the current tab's text to the tab's filename. Call saveas if
		the tab has no filename."""

		if not self.current_tab.filename:
			self.saveas(event)
		else:
			with open(self.current_tab.filename, "w") as file:
				file.write(self.current_tab.text.get_text())

	def saveas(self, event=None):
		"""Get the user to select a filename and save the current tab's text"""

		fname = FD.asksaveasfilename(
			defaultextension=".txt",
			filetypes=[("Text Files", "*.txt")]
		)
		if not fname: # asksaveasfile return "" if dialog closed with "cancel".
			return
		self.current_tab.filename = fname
		self.current_tab_button.config(text=fname.split("/")[-1])
		with open(fname, "w") as file:
			file.write(self.current_tab.text.get_text())

	def openfile(self, event=None):
		"""Get the user to select a filename and open it in a new tab or the
		current tab if it is empty and has no filename."""

		fname = FD.askopenfilename()
		if not fname:
			return
		if self.current_tab.filename is None and not self.current_tab.text.get_text():
			self.current_tab_button.config(text=fname.split("/")[-1])
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
		"""Create a new tab and make it the current tab."""

		self.current_tab = self.create_tab()

	def on_resize(self, event):
		"""Call resize on all tabs if the window is resized."""

		if event.widget is self.root:
			if self.window_shape != (event.width, event.height):
				self.window_shape = (event.width, event.height)
				for tab in self.tabs.values():
					self.resize_tab(tab, event.width, event.height)

	def resize_tab(self, tab, width=None, height=None):
		"""Resize the tab's canvas to the window width and height minus the
		width and height of other widgets. Also resize the linenumber canvas"""

		if not width or not height:
			width, height = self.window_shape
		new_width = width - self.vbar_width - tab.linenumber_canvas_width
		new_height = height - self.tab_buttons_height - self.hbar_height
		tab.canvas.config(width = new_width, height = new_height)
		if tab.linenumbers:
			tab.linenumber_canvas.config(height = new_height)

	def bindings(self):
		"""Bind editor wide events."""

		bind = self.root.bind

		bind("<Control-s>", self.save)
		bind("<Control-S>", self.saveas)  # capital s
		bind("<Control-o>", self.openfile)
		bind("<Control-n>", self.newfile)

		bind("<Configure>", self.on_resize)

	def mainloop(self):
		"""Start the mainloop."""

		self.root.mainloop()



def main():
	t = TextEditor()
	t.mainloop()

if __name__ == "__main__":
	main()
