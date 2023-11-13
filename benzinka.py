from kisim import ExpFactory, Activity, Collector
from simpy import Environment, Resource, Container
from scipy.interpolate import splrep, BSpline
import matplotlib.pyplot as plt
from random import triangular
from statistics import mean

class GasStation(Environment):
    def __init__(self, capacity, tank_capacity):
        super().__init__()
        self.dispensers = Resource(self, capacity)
        self.tank = Container(self, init=tank_capacity, capacity=tank_capacity)
class Car(Activity):
    wtimes = []

    def __init__(self, env:GasStation, free_capacity:float):
        super().__init__(env)
        self.c = free_capacity

    def lifetime(self):
        self.trace("prijezd")
        #Car.atimes.append(self.now)
        with self.env.dispensers.request() as req:
            start_t = self.env.now
            yield req
            finished_t = self.env.now
            Car.wtimes.append(finished_t-start_t)
            self.trace("zacinam tankovat")
            yield self.env.tank.get(self.c) | self.env.timeout(5)
            yield self.env.timeout(3)
            self.trace("dotankováno")

def mean_for_time(t):
    day_t = t % (24 * 60)
    day_t /= 60
    x = [0, 8, 11, 17, 24]
    y = [60, 15, 20, 2, 60]
    ticks = splrep(x, y, s=len(x))
    f = BSpline(*ticks)
    return f(day_t)

class GSCollector(Collector):
    def __init__(self, env, tick):
        super().__init__(env, tick)
        self.quecount = []
        self.rescount = []
        self.fuel = []
        self.times = []

    def collect(self):
        self.quecount.append(len(self.env.dispensers.queue))
        self.rescount.append(self.env.dispensers.count)
        self.times.append(self.now)
        self.fuel.append(self.env.tank.level)

env = GasStation(2, 10_000)
ExpFactory(env, mean_for_time, lambda: Car(env, triangular(10, 50, 40)))
stat = GSCollector(env, 1)
env.run(until=24*60)


#print(stat.quecount)
plt.plot(stat.times, stat.rescount, label="čerpající", c="blue", alpha=0.5)
plt.plot(stat.times, stat.quecount, label="čekající", c="red")
plt.legend()
#plt.hist(Car.atimes, 24)
plt.show()
print(mean(Car.wtimes))
plt.plot(stat.times, stat.fuel)
plt.show()
