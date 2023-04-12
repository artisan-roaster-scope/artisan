#
# ABOUT
# Digital Filters

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023


import numpy as np
from collections import deque
from bisect import bisect_left, insort

from typing import List, Optional, Deque, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy.typing as npt # pylint: disable=unused-import

# https://www.samproell.io/posts/yarppg/digital-filters-python/
class LiveFilter:
    """Base class for live filters.
    """
    def process(self, x):
        # do not process NaNs
        if np.isnan(x):
            return x

        return self._process(x)

    def __call__(self, x):
        return self.process(x)

    def _process(self, x):
        raise NotImplementedError('Derived class must implement _process')


class LiveLFilter(LiveFilter):
    """Live implementation of digital filter using difference equations.

    The following is almost equivalent to calling scipy.lfilter(b, a, xs):
    >>> lfilter = LiveLFilter(b, a)
    >>> [lfilter(x) for x in xs]
    """
    def __init__(self, b_:'npt.NDArray[np.float64]', a_:'npt.NDArray[np.float64]') -> None:
        """Initialize live filter based on difference equation.

        Args:
            b (array-like): numerator coefficients obtained from scipy
                filter design.
            a (array-like): denominator coefficients obtained from scipy
                filter design.
        """
        self.b = b_
        self.a = a_
        self._xs:Deque[float] = deque([0.0] * len(b), maxlen=len(b))
        self._ys:Deque[float] = deque([0.0] * (len(a) - 1), maxlen=len(a)-1)

    def _process(self, x:float) -> float:
        """Filter incoming data with standard difference equations.
        """
        self._xs.appendleft(x)
        y = np.dot(np.array(self.b), np.array(self._xs)) - np.dot(np.array(self.a[1:]), np.array(self._ys))
        y = y / self.a[0]
        self._ys.appendleft(y)

        return y


class LiveSosFilter(LiveFilter):
    """Live implementation of digital filter with second-order sections.

    The following is equivalent to calling scipy.sosfilt(sos, xs):
    >>> sosfilter = LiveSosFilter(sos)
    >>> [sosfilter(x) for x in xs]
    """
    def __init__(self, sos_) -> None:
        """Initialize live second-order sections filter.

        Args:
            sos (array-like): second-order sections obtained from scipy
                filter design (with output="sos").
        """
        self.sos = sos_

        self.n_sections = self.sos.shape[0]
        self.state = np.zeros((self.n_sections, 2))

    def _process(self, x):
        """Filter incoming data with cascaded second-order sections.
        """
        y:float = 0
        for s in range(self.n_sections):  # apply filter sections in sequence
            b0, b1, b2, _a0, a1, a2 = self.sos[s, :]

            # compute difference equations of transposed direct form II
            y = b0*x + self.state[s, 0]
            self.state[s, 0] = b1*x - a1*y + self.state[s, 1]
            self.state[s, 1] = b2*x - a2*y
            x = y  # set biquad output as input of next filter section.

        return y

class LiveMedian(LiveFilter):
    """Live implementation of a median low-pass filter.
    """
    def __init__(self, k:int) -> None:
        """Initialize live median low-pass filter.

        Args:
            k (odd natural number): window size
        """
        assert k % 2 == 1, 'Median filter length must be odd.'
        self.k:int = k
        self.init_list:List[float] = [] # collects first k readings until initialized
        self.initialized:bool = False
        self.q:Optional[Deque[float]] = None
        self.l:Optional[List[float]] = None
        self.mididx:int = 0

    def init_queue(self):
        self.q = deque(self.init_list)
        if self.q is not None:
            self.l = list(self.q)
            self.l.sort()
            self.mididx = (len(self.q) - 1) // 2
            self.initialized = True
            del self.init_list

    def _process(self, x:float) -> float:
        """Filter incoming data with median low-pass filter.
        """
        if not self.initialized:
            if len(self.init_list) < self.k:
                self.init_list.append(x)
                return x
            self.init_queue()
        if self.q is not None and self.l is not None:
            old_elem = self.q.popleft()
            self.q.append(x)
            del self.l[bisect_left(self.l, old_elem)]
            insort(self.l, x)
            return self.l[self.mididx]
        return x


if __name__ == '__main__':

    ### example data
    np.random.seed(42)  # for reproducibility
    # create time steps and corresponding sine wave with Gaussian noise
    fs = 30  # sampling rate, Hz
    ts = np.arange(0, 5, 1.0 / fs)  # time vector - 5 seconds

    ys = np.sin(2*np.pi * 1.0 * ts)  # signal @ 1.0 Hz, without noise
    yerr = 0.5 * np.random.normal(size=len(ts))  # Gaussian noise
    yraw = ys + yerr

    # define the filters
    import scipy.signal # type: ignore
    # define lowpass filter with 2.5 Hz cutoff frequency of order 4
    b, a = scipy.signal.iirfilter(4, Wn=2.5, fs=fs, btype='low', ftype='butter')
    y_scipy_lfilter = scipy.signal.lfilter(b, a, yraw)

    live_lfilter = LiveLFilter(b, a)
    # simulate live filter - passing values one by one
    y_live_lfilter = [live_lfilter(y) for y in yraw]


    # define lowpass filter with 2.5 Hz cutoff frequency if order 2
    sos = scipy.signal.iirfilter(2, Wn=2.5, fs=fs, btype='low',
                                 ftype='butter', output='sos')
    y_scipy_sosfilt = scipy.signal.sosfilt(sos, yraw)

    live_sosfilter = LiveSosFilter(sos)
    # simulate live filter - passing values one by one
    y_live_sosfilt = [live_sosfilter(y) for y in yraw]


    med5filter = LiveMedian(5)
    # simulate median filter - passing values one by one
    y_live_med5filt = [med5filter(y) for y in yraw]

    med9filter = LiveMedian(9)
    # simulate median filter - passing values one by one
    y_live_med9filt = [med9filter(y) for y in yraw]

    y_live_med5sosfilt = [live_sosfilter(med5filter(y)) for y in yraw]


    # plot the data
    import matplotlib.pyplot as plt
    plt.figure(figsize=[6.4, 2.4])
    plt.plot(ts, yraw, label='Noisy signal')
#    plt.plot(ts, y_scipy_lfilter, lw=1, label="SciPy lfilter")
#    plt.plot(ts, y_live_lfilter, lw=1, ls="dashed", label="LiveLFilter")
#    plt.plot(ts, y_scipy_sosfilt, lw=1, label="SciPy SoS filter")
    plt.plot(ts, y_live_sosfilt, lw=1, label='LiveSoSFilter')
    plt.plot(ts, y_live_med5filt, lw=1, label='LiveMed5Filter')
#    plt.plot(ts, y_live_med9filt, lw=1, label="LiveMed9Filter")
    plt.plot(ts, y_live_med5sosfilt, lw=1, label='LiveMed5SosFilter')

    plt.legend(loc='lower center', bbox_to_anchor=[0.5, 1], ncol=3,
               fontsize='smaller')
    plt.xlabel('Time / s')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.show()
