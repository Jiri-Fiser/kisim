# dopravní síť s třemi zastávkami a jednou linkou
# zastávky A - B - C
# časová vzdálenost: A->B 10, B->C 5 minut
# matice přepravních nároků:
#       A     B       C
# A   0        1200   800
# B   1000    O      20
# C   650     50     0
#
# minimální doba obratu je 10 minut
#
# kapacita prostředku: 50

from kisim import Activity, ExpFactory
import numpy as np
from simpy import Environment, Event
from collections import namedtuple
from datetime import timedelta


def tform(sec):
    return str(timedelta(seconds=int(sec)))


class Stanice:
    def __init__(self, nazev, index):
        self.nazev = nazev
        self.index = index
        self.queues = namedtuple("Queue", ("down", "up"))([], [])

    def vstup(self, p):
        wait_event = Event(env)
        if self.index > p.end:
            self.queues.down.append((wait_event, p.end))
        else:
            self.queues.up.append((wait_event, p.end))
        return wait_event

class TovarnaNaPasazery(ExpFactory):
    def __init__(self, env, start, end, frekvence):
        super().__init__(env, lambda _: 60*60 / frekvence)
        self.start = start
        self.end = end

    def produce(self):
        return Pasazer(self.env, self.start, self.end)

class Pasazer(Activity):
    def __init__(self, env, start, end):
        super().__init__(env)
        self.start = start
        self.end = end

    def lifetime(self):
        #self.trace(f"pasažer {self.start}-{self.end}")
        nastup_event = stanice[self.start].vstup(self)
        vystup_event = yield nastup_event
        #self.trace("nastup")
        yield vystup_event
        #self.trace("vystup")


class Prostredek(Activity):
    def __init__(self, env, kapacita, trasa, casObratu):
        super().__init__(env)
        self.kapacita =kapacita
        self.trasa = trasa
        self.casObratu = casObratu

    def obrat(self):
        yield self.env.timeout(self.casObratu)

    def lifetime(self):
        indexStanice = self.trasa[0]
        direction = -1 # trasa musí být vzestupná posloupnost indexů
        free = self.kapacita
        targets = [[], [], []]

        while True:
            self.trace(f"prijezd do {indexStanice}", tform)
            # planování obratu
            if indexStanice == len(self.trasa) - 1 or indexStanice == 0:
               direction = -direction
               obrat_event = self.env.process(self.obrat())
            else:
               obrat_event = None

            # vystup
            while targets[indexStanice]:
                event = targets[indexStanice].pop()
                event.succeed()
                yield self.env.timeout(8)
                free += 1

            # nastup
            if direction > 0:
                queue = stanice[indexStanice].queues.up
            else:
                queue = stanice[indexStanice].queues.down
            nastup = min(free, len(queue))
            for i in range(nastup):
                if not queue:
                    break
                nastup_event, end = queue.pop(0)
                vystup_event = Event(self.env)
                nastup_event.succeed(vystup_event)
                targets[end].append(vystup_event)
                yield self.env.timeout(8)
                free -= 1

            if obrat_event is not None: # FIXME: // co pasažéři, kteří přijdou než se dokončí obrat
                yield obrat_event # čekání na případný obrat

            self.trace(f"odjezd z {indexStanice}, pasazeri: {self.kapacita - free}", tform)
            fromIndex = indexStanice
            indexStanice += direction

            yield self.env.timeout(60 * pc[fromIndex, indexStanice])




pm = np.array([[0, 1200, 800],
               [1000, 0, 20],
               [650, 50, 0]])

pc = np.array([[0, 10, 15],
               [10, 0, 5],
               [15, 5, 0]])


stanice = [Stanice("A", 0), Stanice("B", 1), Stanice("C", 2)]
env = Environment()
for i in range(pm.shape[0]):
     for j in range(pm.shape[1]):
         if i != j:
             TovarnaNaPasazery(env, i, j, pm[i,j])

Prostredek(env, 1000, [0,1,2], 60*8)
env.run(until=4*60*60)
