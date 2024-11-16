import math

from simpy import Environment
from tkinter import Canvas, Tk
from tkinter.font import Font
from typing import Iterable, Callable, Any


class Bar:
    def __init__(self, x, y, width, height, color):
        self.genv = None
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.genv.canvas.create_rectangle(self.xpos(), self.ypos(),
                                          self.xpos(self.width), self.ypos(self.height), fill=self.color)

    def xpos(self, relx=0, shiftx=0):
        return (self.x + relx) * self.genv.grid_size + shiftx

    def ypos(self, rely=0, shifty=0):
        return (self.y + rely) * self.genv.grid_size + shifty

    def moveDx(self, dx, dy):
        self.x += dx
        self.y += dy

    def moveAt(self, x, y):
        self.x = x
        self.y = y


class InfoBar(Bar):
    def __init__(self, string_getter: Callable[['GEnvironment'], Any], x: int, y:int,
                 width: int, fillColor: str="black", textColor: str="white"):
        """
        Create bar which displays text from simulation environment
        :param string_getter: function which get displayed object (with __str__ method)
        :param x: grid column of left corner
        :param y: grid line
        :param width: width in grid
        :param fillColor: background color
        :param textColor: text color
        """
        super().__init__(x, y, width, 1, fillColor)
        self.getter = string_getter
        self.textColor = textColor

    def draw(self):
        super().draw()
        self.genv.canvas.create_text(self.xpos(1), self.ypos(0, self.genv.grid_size / 2),
                                     text=str(self.getter(self.genv)), fill=self.textColor,
                                     font=self.genv.font, anchor="w")


class Box(Bar):
    def __init__(self, objects: Iterable,
                 x: int, y: int, width: int, height: int,
                 bg_color:str, *, span: int = 1,
                 color_getter: Callable[[Any], Any] = lambda a: a.gcolor,
                 id_getter: Callable[[Any], Any]= lambda a: a.id,
                 label: str = None):
        """
        Create rectangular box with visual representation of simulation entities
        :param objects: iterable of simulation entities
        :param x: grid column of left corner
        :param y:  grid line of top corner
        :param width: width in grid
        :param height: height in grid
        :param bg_color: background color
        :param span: width of visual representation of every simulation entity (divisable with width)
        :param color_getter: function which maps simulation entity to (background) color (Tk color name)
        :param id_getter: function which maps simulation entity to short identifier (
        :param label: label of box
        """
        super().__init__(x, y, width, height, bg_color)
        assert width % span == 0, "Span must be diviser of width"
        self.objects = objects
        self.color_getter = color_getter
        self.span = span
        self.id_getter = id_getter
        self.label = label

    def draw(self):
        super().draw()
        size = self.genv.grid_size
        if self.label:
            self.genv.canvas.create_text(self.xpos(1), self.ypos(self.height - 1), text=self.label,
                                    fill="white", font=self.genv.font, anchor="w")
        for i, obj in enumerate(self.objects):
            y = (self.span * i) // self.width
            x = (self.span * i) % self.width
            if y >= self.height: # už se tam nevejdou
                break
            color = self.color_getter(obj)
            text = str(self.id_getter(obj))
            self.genv.canvas.create_rectangle(self.xpos(x, 1), self.ypos(y, 1),
                                              self.xpos(x + self.span - 1, size-1), self.ypos(y, size-1), fill=color)
            self.genv.canvas.create_text(self.xpos(x, self.span*size/2), self.ypos(y, size/2), text=text,
                                         fill="black", font=self.genv.font)


class GEnvironment(Environment):
    def __init__(self, unit_time=0, grid_size = 16, width=100, height=50):
        """
        Create similation environment with simple GUI 
        :param unit_time: duration of simulation time unit in seconds (it must be > 0)
        :param grid_size: grid span in pixel
        :param width: number of columns of grid
        :param height: number of lines of grid
        """
        super().__init__()
        self.unit_time = unit_time
        self.grid_size = grid_size
        self.width = width
        self.height = height
        self.bars = []
        self.canvas = None
        self.root = None
        self.untilTime = None
        self.pixelWidth = self.width * self.grid_size
        self.pixelHeight = self.height * self.grid_size
        self.font = None

    def gstep(self):
        if self.now > self.untilTime:
            return
        self.step()
        self.canvas.delete('all')
        for bar in self.bars:
            bar.draw()
        delta_t = self.peek() - self.now
        if delta_t != math.inf:
            self.root.after(int(delta_t * self.unit_time * 1000), self.gstep)

    def run(self, until):
        self.untilTime = until
        self.root = Tk()
        self.canvas = Canvas(self.root, bg="black", width=self.pixelWidth, height=self.pixelHeight)
        self.canvas.pack()
        self.root.after(0, self.gstep)
        self.font = Font(family="Helvetica", size=-(self.grid_size - 2))
        self.root.mainloop()

    def addBar(self, bar:Bar):
        bar.genv = self
        bar.x = bar.x if bar.x >=0 else self.width + bar.x
        bar.y = bar.y if bar.y >= 0 else self.height + bar.y
        self.bars.append(bar)