from kisim import Activity, Collector
from simpy import Environment, Resource
from random import triangular, expovariate, uniform
import matplotlib.pyplot as plt


class Customer(Activity):
    count = 0
    total_waiting = []
    def __init__(self, env, cash: bool):
        super().__init__(env)
        self.cash = cash

    def lifetime(self):
        self.trace("vstup do obchodu")
        Customer.count += 1
        shop_time = triangular(2, 90, 20)
        yield self.env.timeout(shop_time)
        self.trace("příchod k pokladně")
        with self.env.cashdesk.request() as req:
            start = self.now
            yield req
            self.trace("začíná obsluha u pokladny")
            finish = self.now
            Customer.total_waiting.append(finish - start)
            cd_time = (triangular(1, 10, 3)
                       + triangular(1, 5, 1.5) if self.cash
                       else triangular(1, 3, 1.2))
            yield self.env.timeout(cd_time)
        Customer.count -= 1
        self.trace("opuštění obchodu")


class ShopCollector(Collector):
    def __init__(self, env):
        super().__init__(env, 1)
        self.customers = []

    def collect(self):
        self.customers.append(Customer.count)


class CustomerFactory(Activity):
    def __init__(self, env, mean_arrival_interval: float):
        super().__init__(env)
        self.mai = mean_arrival_interval

    def lifetime(self):
        while True:
            dt = expovariate(1/self.mai)
            yield self.env.timeout(dt)
            Customer(self.env, uniform(0, 100) < 9)  # s pravděpod. 10% bude zákazník platící hotově


class ShopEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self.cashdesk = Resource(self, 1)


if __name__ == "__main__":
    env = ShopEnvironment()
    CustomerFactory(env, 2.3)
    c = ShopCollector(env)
    env.run(until=60*2400)

    #plt.plot(c.customers)
    plt.hist(Customer.total_waiting, bins=20, edgecolor='black')
    plt.show()

