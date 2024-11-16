from genvironment import GEnvironment, InfoBar, Box
from kisim import Activity, ExpFactory
from random import uniform


class Anima(Activity):
    purgatorium = []
    eden = []

    def __init__(self, env, peccatus):
        super().__init__(env)
        self.peccatus = peccatus

    @property
    def gcolor(self):
        return "red" if self.peccatus else "green"

    def lifetime(self):
        Anima.purgatorium.append(self)
        yield self.env.timeout(10 if self.peccatus else 2)
        Anima.purgatorium.remove(self)
        Anima.eden.append(self)
        yield self.env.timeout(0)


class AnimaFactory(ExpFactory):
    def __init__(self, env, mean):
        super().__init__(env, mean)

    def produce(self):
        return Anima(self.env, uniform(0, 1) < 0.88)


env = GEnvironment(0.1, 8, width=80, height=21)
env.addBar(InfoBar(lambda env: env.now, 0, -1, 10, "black", "white"))
env.addBar(Box(Anima.purgatorium, 0, 0, 40, 20, "#333333", span=2, label="Očistec"))
env.addBar(Box(Anima.eden, 40, 0, 40, 20, "#555555", span=2, label="Ráj"))
AnimaFactory(env, lambda _: 2)
env.run(10000)
