import numpy as np
from stochastic.processes.continuous import FractionalBrownianMotion
import matplotlib.pyplot as plt
import random as rand
import numpy as np
import pandas as pd
import string


def create_bar(price: float, symbol: str):

    return {
        "symbol": symbol,
        "open": price * rand.gammavariate(1, 0.2),
        "close": price * rand.gammavariate(1, 0.2),
        "high": price * rand.gammavariate(1, 0.2),
        "low": price * rand.gammavariate(1, 0.2),
        "volume": price * rand.gammavariate(1, 0.2) * rand.uniform(800, 900)
    }


def pick_symbol():
    return ''.join([
        rand.choice(string.ascii_letters).upper()
        for _ in range(rand.randint(2, 4))
    ])


def create_single_asset(length: int):
    fbm = FractionalBrownianMotion(0.2, 25)
    dist = length
    s = fbm.sample(dist)
    lowest = min(s)
    s = np.array(s)
    if lowest < 0:
        s = s + abs(lowest)
    base = rand.uniform(20, 20000)
    s = s * base
    goods = pick_symbol()

    bars = list(map(lambda x: create_bar(x, goods), s))
    return bars


def main():
    fbm = FractionalBrownianMotion(0.2, 25)
    length = 1000
    # Lolz, just select an outlandish amount of data of a give type by a filter then work backwards.
    assets = [create_single_asset(length) for _ in range(60)]
    asset_time = fbm.times(length)
    frame_group = []
    for asset in assets:
        frame = pd.DataFrame.from_records(asset)
        frame['time'] = asset_time
        frame.set_index('time', inplace=True)
        frame_group.append(frame)
    print()
    total_frame = pd.concat(frame_group)
    print(total_frame[total_frame.index > 22.0].sort_index().groupby(
        'symbol').head())
    # plt.plot(times, s)
    # plt.show()


if __name__ == "__main__":
    main()