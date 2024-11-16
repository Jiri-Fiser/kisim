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
from genvironment import GEnvironment, Box, InfoBar
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
            self.queues.down.append((wait_event, p.end, p))
        else:
            self.queues.up.append((wait_event, p.end, p))
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

    @property
    def gcolor(self):
        return ["red", "green", "blue"][self.end]


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
        event_to_passenger = {}


        self.env.addBar(b:=Box(event_to_passenger.values(), 0, 30, 24, 10, "#222222", label="Vlak", span=2))
        self.env.addBar(InfoBar(lambda _: f"{len(event_to_passenger)}/{self.kapacita}", 72, 0, 8))
        self.env.addBar(InfoBar(lambda  _: "; ".join(Activity.trace_queue), 0, -2, 72))


        while True:
            self.tracex(f"prijezd do {indexStanice}", tform)
            # planování obratu
            if indexStanice == len(self.trasa) - 1 or indexStanice == 0:
               direction = -direction
               obrat_event = self.env.process(self.obrat())
               b.label = "Vlak (obrat)"
            else:
               obrat_event = None

            if obrat_event is not None: # FIXME: // co pasažéři, kteří přijdou než se dokončí obrat
                yield obrat_event # čekání na případný obrat

            b.moveAt(indexStanice*24, 30)
            b.label = "Vlak (vystup)"
            b.color = "#444444"
            # vystup
            while targets[indexStanice]:
                event = targets[indexStanice].pop()
                del event_to_passenger[event]
                event.succeed()
                yield self.env.timeout(8)
                free += 1

            # nastup
            b.label = "Vlak (nastup)"
            if direction > 0:
                queue = stanice[indexStanice].queues.up
            else:
                queue = stanice[indexStanice].queues.down
            nastup = min(free, len(queue))
            self.trace(f"na nastup ceka {nastup} lidi")
            for i in range(nastup):
                if not queue:
                    break
                nastup_event, end, p = queue.pop(0)
                vystup_event = Event(self.env)
                nastup_event.succeed(vystup_event)
                targets[end].append(vystup_event)
                event_to_passenger[vystup_event] = p
                yield self.env.timeout(8)
                free -= 1

            self.trace(f"odjezd z {indexStanice}, pasazeri: {self.kapacita - free}", tform)
            fromIndex = indexStanice
            indexStanice += direction

            b.moveDx(direction * 12, 0)
            b.label = "Vlak (jizda)"
            b.color = "#222222"
            yield self.env.timeout(60 * pc[fromIndex, indexStanice])


def rgbcolor(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def valuecolor(v):
    return f"#{v:06x}"


pm = np.array([[0, 120, 80],
               [50, 0, 60],
               [65, 50, 0]])

pc = np.array([[0, 1, 2],
               [1, 0, 1],
               [2, 1, 0]])


stanice = [Stanice("A", 0), Stanice("B", 1), Stanice("C", 2)]
env = GEnvironment(0.01, 20, width=80, height=41)
for i in range(pm.shape[0]):
     for j in range(pm.shape[1]):
         if i != j:
             TovarnaNaPasazery(env, i, j, pm[i,j])

Prostredek(env, 1000, [0,1,2], 60*1)

env.addBar(InfoBar(lambda env: tform(env.now), 0, -1, 80))

for i in range(3):
    env.addBar(Box(stanice[i].queues.down, i*24, 0, 12, 30, valuecolor(10 << ((2-i) * 8)) , span=2,
                   color_getter=lambda r: r[2].gcolor,
                   id_getter=lambda r: r[2].id,
                   label=stanice[i].nazev + "<-"))
    env.addBar(Box(stanice[i].queues.up, i * 24 + 12, 0, 12, 30, valuecolor(20 << ((2-i) * 8)), span=2,
                   color_getter=lambda r: r[2].gcolor,
                   id_getter=lambda r: r[2].id,
                   label=stanice[i].nazev + "->"))


env.run(until=24*60*60)
