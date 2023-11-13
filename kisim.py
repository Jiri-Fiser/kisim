import simpy
from math import exp
from random import uniform

class Activity:
    instance_count = 0
    DEBUG = True

    def __init__(self, env:simpy.Environment):
        self.env = env
        self.env.process(self.lifetime())
        self.id = Activity.instance_count
        Activity.instance_count += 1

    def lifetime(self):
        raise NotImplemented("abstract method")

    @property
    def ident(self):
        return f"{self.__class__.__name__} {self.id}"

    @property
    def now(self):
        return self.env.now

    def trace(self, event, timeFormatter=None):
        if Activity.DEBUG:
            if timeFormatter is None:
                print(f"{self.now:8.2f}: {event} [{self.ident}]")
            else:
                print(f"{timeFormatter(self.now)}: {event} [{self.ident}]")

class Collector(Activity):
    def __init__(self, env, tick, collect=None):
        super().__init__(env)
        self.tick = tick
        self.cf = collect if collect is not None else self.collect

    def lifetime(self):
        while True:
            self.collect()
            yield self.env.timeout(self.tick)

    def collect(self):
        raise NotImplemented("Abstract method")


class ExpFactory(Activity):
    def __init__(self, env: simpy.Environment, mean, produceFunction=None):
        super().__init__(env)
        self.mean = mean
        self.produceFunction = produceFunction if produceFunction is not None else self.produce

    def lifetime(self):
        while True:
            lamda = 1.0 / self.mean(self.now)
            p = lamda * exp(-lamda)
            while p > 1e-6:
                r = uniform(0, 1)
                if r < p:
                    self.produceFunction()
                p *= p
            yield self.env.timeout(1)

    def produce(self):
        raise NotImplemented("Abstract method")

