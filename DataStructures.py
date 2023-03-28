


from collections import deque, namedtuple
from itertools import islice


__all__ = [
	"Selection",
	"TextArray",
]


Point = namedtuple('Point', ['x', 'y'])

class Selection:
	"""A class representing a selection of text or the start of a selection"""

	def __init__(self, startx=None, starty=None, endx=None, endy=None):
		"""Create a selection from the given start and end coordinates."""

		self.start = Point(startx, starty)
		self.end = Point(endx, endy)

	def __bool__(self):
		"""Return True if all four coordinates are set and False otherwise"""

		return (None not in self.start) and (None not in self.end)

	def __str__(self):
		return f"{self.start} to {self.end}"

	@classmethod
	def from_start(cls, x, y):
		"""Create a selection from only the start coordinates. Does not result
		in a valid selection."""

		return cls(x, y)

	def from_end(self, x2, y2):
		"""Create a selection from the current start coordinates and the given
		end coordinates. Does result in a valid selection."""

		return self.__class__(self.start.x, self.start.y, x2, y2)

class SliceDeque(deque):
	"""A deque that can be sliced"""

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
	"""Descriptor to expose the cursor as x and y attributes"""

	def __init__(self, index):
		self.index = index

	def __get__(self, instance, owner):
		return instance.cursor[self.index]

	def __set__(self, instance, value):
		instance.cursor[self.index] = value

class TextArray:
	"""A class representing a holding the text as a deque of deques. Also keeps
	track of the current cursor position."""

	x = Coordinate(0)
	y = Coordinate(1)

	def __init__(self):
		self.lines = SliceDeque([SliceDeque()])
		self.cursor = [0, 0]  # x, y

	def __getitem__(self, index):
		return self.lines[index]

	def __len__(self):
		return len(self.lines)

	def get_text(self) -> str:
		"""Return the text as a string"""

		return "\n".join("".join(line) for line in self.lines)

	def set_text(self, text):
		"""Set the text from a string and set the cursor to the beginning of
		the text"""

		t = text.split("\n")
		self.lines = SliceDeque([SliceDeque(line) for line in t])
		self.cursor = [0, 0]

	def current_line(self):
		"""Return the line the cursor is on as a deque"""

		return self.lines[self.y]

	def insert(self, char):
		"""Insert the given character at the cursor position"""

		self.current_line().insert(self.x, char)
		self.x += 1

	def duplicate_line(self):
		"""Duplicate the line the cursor is on"""

		self.lines.insert(self.y, SliceDeque(self.current_line()))
		self.y += 1

	def newline(self):
		"""Insert a newline at the cursor position and move any text after the
		cursor to the new line"""

		remaining_text = ""
		if remaining_text := self.current_line()[self.x:]:
			# TODO: should do differently depending on which side of the line the cursor is closer to
			del self.current_line()[self.x:self.x + len(remaining_text)]
		self.lines.insert(self.y + 1, SliceDeque(remaining_text))
		self.y += 1
		self.x = 0

	def backspace(self) -> tuple[int]:
		"""Delete the character behind the cursor.

		Return (line number, 0|1|2) if 0, 1, or more than one line needs to be
		updated."""

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
		"""Delete the character infront of the cursor and return a tuple
		containing the the line the cursor is on and whether no lines need to
		be updated, only the current line, or all lines after the current
		line. (line number, 0|1|2)"""

		if self.x < len(self.current_line()):
			del self.current_line()[self.x]
			return (self.y, 1)
		elif self.y < len(self.lines) - 1:
			self.current_line().extend(self.lines[self.y + 1])
			del self.lines[self.y + 1]
			return (self.y, 2)
		return (-1, 0)


