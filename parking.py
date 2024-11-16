import simpy.resources.resource

from genvironment import GEnvironment, InfoBar, Box
from datetime import timedelta
from kisim import Activity
from simpy import Resource
from random import lognormvariate, expovariate
from math import log, sqrt
from collections.abc import Iterable
import colorsys
import multiprocessing

def hsv_to_hex(h, s, v):
    # colorsys.hsv_to_rgb vrací hodnoty v rozsahu [0, 1], musíme je převést na [0, 255]
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, v / 100.0)
    # Převod na 8bitové hodnoty
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    # Vytvoření hex stringu
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def lognorm(m, s):
    return lognormvariate(log(m*m/sqrt(s*s+m*m)), log(1+s**2/m**2))

class EnvironMixin:
    def __init__(self, park_capacity, re_capacity):
        self.parking = Resource(self, park_capacity)
        self.recharge = Resource(self, re_capacity)
        self.parking_list = []
        self.resign_count = 0


class Environ(GEnvironment, EnvironMixin):
    def __init__(self, park_capacity=100, re_capacity=10):
        GEnvironment.__init__(self, 0.1, 16, 100, 51)
        EnvironMixin.__init__(self, park_capacity, re_capacity)
        self.debug = True

class MPEnviron(simpy.Environment, EnvironMixin):
    def __init__(self, park_capacity=100, re_capacity=10):
        simpy.Environment.__init__(self)
        EnvironMixin.__init__(self, park_capacity, re_capacity)
        self.debug = False

def tform(sec):
    return str(timedelta(minutes=int(sec)))


class Car(Activity):
    def __init__(self, env):
        super().__init__(env)

    def reqToColor(self, req: simpy.resources.resource.Request, maxDeltaT: float) -> str:
        alpha = min((self.now - req.wait_start) / maxDeltaT, 1.0)
        hue = 120 - int(alpha * 120)
        return hsv_to_hex(hue, 100, 100)


class NonR_Car(Car):
    def __init__(self, env):
        super().__init__(env)

    def lifetime(self):
        self.trace("start")
        with self.env.parking.request() as req:
            req.owner = self
            req.wait_start = self.now
            result = yield req | self.env.timeout(10)
            if req not in result:
                self.trace("resignation")
                self.env.resign_count += 1
                return
            self.env.parking_list.append(self)
            yield self.env.timeout(lognorm(20, 5))
            self.env.parking_list.remove(self)
        self.trace("end")

    @property
    def gcolor(self):
        return "green"


class CarFactory(Activity):
    def __init__(self, env, deltaT):
        super().__init__(env)
        self.deltaT = deltaT

    def lifetime(self):
        while True:
            c = NonR_Car(self.env)
            c.DEBUG = self.env.debug
            yield self.env.timeout(expovariate(1/self.deltaT))


class MapIterable(Iterable):
    def __init__(self, collection, map_func):
        self.collection = collection
        self.map_function = map_func

    def __iter__(self):
        return (self.map_function(item) for item in self.collection)



def gsimulation():
    env = Environ(park_capacity=10)
    env.addBar(InfoBar(lambda env: tform(env.now), 0, -1, 80))

    env.addBar(Box(env.parking.queue,
                   0, 0, 100, 20, "#330011",
                   color_getter=lambda req: req.owner.reqToColor(req, 10.0),
                   id_getter=lambda req: req.owner.id,
                   label="waiting queue", span=4))
    env.addBar(Box(env.parking_list, 0, 20, 60, 30, "#000033", label="normal parking", span=4))
    env.addBar(Box([], 60, 20, 40, 30, "#002200", label="recharge parking", span=4))

    CarFactory(env, 1)

    env.run(until=24*60)

def simulation(capacity):
    env = MPEnviron(park_capacity=capacity)
    CarFactory(env, 1)
    env.run(until=24 * 60)
    return env.resign_count

if __name__ == "__main__":
    with multiprocessing.Pool(4) as p:
        results = p.map(simulation, range(5, 50))
    print(results)
