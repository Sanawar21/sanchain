import time
import random


def generate_uid():
    return int(str(int(time.time_ns() / 1_000_000)) +
               str(random.randint(0, 1_000)))
