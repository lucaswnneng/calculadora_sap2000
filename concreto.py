import numpy as np


class Concreto:
    def __init__(self, fck, gammac=1.4):
        self.fck = fck  # MPa
        self.gammac = gammac

    @property
    def fctm(self):
        """
        fctm em MPa
        """
        return (
            0.30 * self.fck ** (2 / 3)
            if self.fck <= 50
            else 2.12 * np.log(1 + 0.1 * (self.fck + 8))
        )

    @property
    def fctkinf(self):
        """
        fctkinf em MPa
        """
        return 0.7 * self.fctm

    @property
    def fctd(self):
        """
        fctd em MPa
        """
        return self.fctkinf / self.gammac