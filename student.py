import sklearn.neighbors

from kisim import Activity, Collector
from random import uniform, triangular
from math import exp
from simpy import Environment
import matplotlib.pyplot as plt

rozvrh = [(8, 2, "Matematická analýza"), (11, 4, "Programování"), (18, 6, "Simulace")]

class Student(Activity):
    def __init__(self, env, abs_k: float):
        super().__init__(env)
        self.abs_k = abs_k
        self.zatizeni = 0
        self.na_vyuce = False

    def lifetime(self):
        for hodina, trvani, predmet in rozvrh:
            yield self.env.timeout(hodina*60 - self.now)
            if self.abs_k *  uniform(0, 1) * exp(-self.zatizeni / 120.0) * (8.0 / trvani) > 0.3:
                zpozdeni = triangular(0, 15, 5)
                doba_vyuka = trvani * 60 * (1.0 - uniform(0, 1)**8)
                yield self.env.timeout(zpozdeni)
                self.trace(predmet)
                self.na_vyuce = True
                yield self.env.timeout(doba_vyuka)
                self.na_vyuce = False
                self.zatizeni += doba_vyuka


class Hlidac(Collector):
    def __init__(self, env, studenti):
        super().__init__(env, 1)
        self.data = []
        self.studenti = studenti

    def collect(self):
        self.data.append(sum(int(s.na_vyuce) for s in self.studenti))

env = Environment()
studenti = []
for _ in range(100):
    studenti.append(Student(env, uniform(0.5, 1.0)))
h = Hlidac(env, studenti)
env.run(until=24*60)
print(h.data)

plt.plot(h.data)
plt.show()


