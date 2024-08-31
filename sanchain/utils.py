import time
import random

from models.config import SanchainConfig

CONFIG = SanchainConfig.load_local()


class UIDGenerator:
    last_uid = 0

    def get(self):
        while True:
            uid = int(
                str(int(time.time())) +
                str(random.randint(100, 1000))
            )
            if uid != self.last_uid:
                self.last_uid = uid
                return uid


__uidg = UIDGenerator()

generate_uid = __uidg.get
