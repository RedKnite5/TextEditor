


from collections import deque, namedtuple
from itertools import islice


__all__ = [
	"Selection",
	"TextArray",
]


Point = namedtuple('Point', ['x', 'y'])

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


