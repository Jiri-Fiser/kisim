import simpy
from math import exp
from random import uniform, expovariate

class Activity:
    instance_count = 0
    DEBUG = True
    trace_queue = []

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


    def tracex(self, event, timeFormatter=None):
        if Activity.DEBUG:
            if timeFormatter is None:
                Activity.trace_queue.append(f"{self.now:8.2f}: {event} [{self.ident}]")
            else:
                Activity.trace_queue.append(f"{timeFormatter(self.now)}: {event} [{self.ident}]")

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

    def lifetime2(self):
        while True:
            lamda = 1.0 / self.mean(self.now)
            p = 1 - exp(-lamda)
            while True: # lze nahradit generovat jako poisson
                r = uniform(0, 1)
                if r < p:
                    self.produceFunction()
                else:
                    break
            yield self.env.timeout(1)  # rovnoměrně rozdělit

    def lifetime(self):
        while True:
            lamda = self.mean(self.now)
            p = expovariate(lamda)
            cp = int(p)
            pp = p - cp
            for i in range(cp):
                self.produceFunction()
            r = uniform(0, 1)
            if r < pp:
                self.produceFunction()
            yield self.env.timeout(1)

    def produce(self):
        raise NotImplemented("Abstract method")

