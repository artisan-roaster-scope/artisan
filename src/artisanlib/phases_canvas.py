#
# ABOUT
# Artisan Phases Canvas

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


import warnings
import numpy
import logging

from typing import Final, Dict, Tuple, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from matplotlib.axes import Axes # pylint: disable=unused-import

from artisanlib.suppress_errors import suppress_stdout_stderr
from artisanlib.util import toGrey, toDim, stringfromseconds


try:
    from PyQt6.QtGui import QColor # @Reimport @UnresolvedImport @UnusedImport
    from PyQt6.QtCore import QSettings # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtGui import QColor # type: ignore # @Reimport @UnresolvedImport @UnusedImport
    from PyQt5.QtCore import QSettings # type: ignore # @Reimport @UnresolvedImport @UnusedImport


with suppress_stdout_stderr():
    import matplotlib as mpl

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # @Reimport
from matplotlib.font_manager import FontProperties

_log: Final[logging.Logger] = logging.getLogger(__name__)

class tphasescanvas(FigureCanvas):

    __slots__ = [ 'aw', 'dpi_offset', 'barheight', 'm', 'g', 'data', 'fig', 'ax' , 'tight_layout_params' ]

    def __init__(self, dpi:int, aw:'ApplicationWindow') -> None:
        self.aw = aw
        self.dpi_offset = -30 # set the dpi to 30% less than the user selected dpi
        # values that define the bars and spacing
        self.barheight =  0.88  # height of each bar within the norm row height of 1
        self.m = 10             # width of batch number field and drop time field
        self.g = 2              # width of the gap between batch number field and drop time field and the actual phase percentage bars
        # set data
        self.data:Optional[List[Tuple]] = None  # the phases data per profile
        # the canvas
        self.fig = Figure(figsize=(1, 1), frameon=False, dpi=dpi+self.dpi_offset)
        # as alternative to the experimental constrained_layout we could use tight_layout as for them main canvas:
        self.tight_layout_params: Final[Dict[str, float]] = {'pad':.3,'h_pad':0.0,'w_pad':0.0} # slightly less space for axis labels
#        self.fig.set_tight_layout(self.tight_layout_params)
        self.fig.set_layout_engine('tight', **self.tight_layout_params)
        #
        super().__init__(self.fig)
        self.ax:Optional['Axes'] = None
        self.clear_phases()

    def clear_phases(self):
        if self.ax is None:
            self.ax = self.fig.add_subplot(111, frameon=False)
        if self.ax is not None:
            self.ax.clear() # type: ignore # mypy: Statement is unreachable  [unreachable]
            self.ax.axis('off')
            self.ax.grid(False)
            self.ax.set_xlim(0,100 + 2*self.m + 2*self.g)

    # a similar function is define in aw:ApplicationWindow
    def setdpi(self,dpi,moveWindow=True):
        if self.aw is not None and self.fig and dpi >= 40:
            try:
                dpi = (dpi + self.dpi_offset) * self.aw.devicePixelRatio()
                self.fig.set_dpi(dpi)
                if moveWindow:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        self.fig.canvas.draw()
#                        self.fig.canvas.update()
                    FigureCanvas.updateGeometry(self)  #@UndefinedVariable
                self.aw.scroller.setMaximumHeight(self.sizeHint().height())
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)

    # data is expected to be a None or a list of tuples of the form
    #   (label, total_time, (phase1_time, phase2_time, phase3_time), active, color)
    # each time value in the triple is in seconds and can be 0 if corresponding phase is missing
    # active is of type bool indicating the state of the corresponding profile
    # aligned is of type bool indicating that the profile is aligned to the current selected alignment target
    # color is a regular color string like '#00b950'
    def set_phases(self, data:Optional[List[Tuple]]) -> None:
        self.data = data

    # updates the phases graphs data and redraws its canvas
    # side condition: only profile data of visible profiles are contained in data
    def update_phases(self, data:Optional[List[Tuple]]) -> None:
        self.set_phases(data)
        self.redraw_phases()

    def redraw_phases(self):
        if self.ax is None:
            return
        # clear canvas
        self.clear_phases()
        if self.data is not None and len(self.data):
            self.aw.scroller.setVisible(True)
            # set canvas background color
            background_color = self.aw.qmc.palette['background']
            self.setStyleSheet(f'background-color: {background_color}')
            # maximum total roast time of all given profiles
            max_total_time = max(p[1] for p in self.data)
            # set font
            if self.aw:
                prop = self.aw.mpl_fontproperties
            else:
                prop = FontProperties().copy()
            prop.set_family(mpl.rcParams['font.family'])
            prop.set_size('medium')

            digits = (1 if self.aw.qmc.LCDdecimalplaces else 0)
            # dimmed phases bar colors
            rect1dim = toDim(self.aw.qmc.palette['rect1'])
            rect2dim = toDim(self.aw.qmc.palette['rect2'])
            rect3dim = toDim(self.aw.qmc.palette['rect3'])
            # i counts the number of rows drawn to get the geometry right
            i = 0
            # add bars
            for p in self.data:
                label, total_time, phases_times, active, aligned, color = p
                if not (active and aligned):
                    color = toGrey(color)
                rects = None
                patch_colors = []
                labels = []
                if all(phases_times):
                    # all phases defined
                    if int(round(total_time)) == int(round(sum(phases_times))):
                        phases_percentages = [(phase_time/total_time) * 100. for phase_time in phases_times]
                        extended_phases_percentages = [self.m,self.g] + phases_percentages + [self.g,self.m*total_time/max_total_time]
                        widths = numpy.array(extended_phases_percentages)
                        starts = widths.cumsum() - widths
                        if active:
                            labels = [f"{str(round(percent,digits)).rstrip('0').rstrip('.')}%  {stringfromseconds(tx,leadingzero=False)}" if percent>20 else (f"{str(round(percent,digits)).rstrip('0').rstrip('.')}%" if percent>10 else '')
                                    for (percent,tx) in zip(phases_percentages, phases_times)] # type: ignore # pyright: error: "object*" is not iterable
                        else:
                            labels = ['']*3
                        labels = [label, ''] + labels + ['', stringfromseconds(total_time,leadingzero=False)]
                        # draw the bars
                        if active:
                            patch_colors = [color, background_color, self.aw.qmc.palette['rect1'], self.aw.qmc.palette['rect2'], self.aw.qmc.palette['rect3'], background_color, color]
                        else:
                            patch_colors = [color, background_color, rect1dim, rect2dim, rect3dim, background_color, color]
                        rects = self.ax.barh(i, widths, left=starts, height=self.barheight, color=patch_colors)
                    else:
                        _log.error('redraw_phases(): inconsistent phases data in %s (total: %s, sum(phases): %s)', label, total_time, sum(phases_times))
                    # else something is inconsistent in this data and we skip this entry
                elif phases_times[0] and not phases_times[1] and not phases_times[2]:
                    # only Drying Phase is defined
                    phase1_percentage = (phases_times[0]/total_time) * 100.
                    phases_percentages = [phase1_percentage, 100-phase1_percentage]
                    extended_phases_percentages = [self.m,self.g] + phases_percentages + [self.g,self.m*total_time/max_total_time]
                    widths = numpy.array(extended_phases_percentages)
                    starts = widths.cumsum() - widths
                    if active:
                        label1 = f"{str(round(phase1_percentage,digits)).rstrip('0').rstrip('.')}%  {stringfromseconds(phases_times[0],leadingzero=False)}" if phase1_percentage>20 else (f"{str(round(phase1_percentage,digits)).rstrip('0').rstrip('.')}%" if phase1_percentage>10 else '')
                    else:
                        label1 = ''
                    labels = [label, '', label1, '', #QApplication.translate('Message', 'Profile missing FCs event'),
                        '', stringfromseconds(total_time,leadingzero=False)]
                    # draw the bars
                    if active:
                        patch_colors = [color, background_color, self.aw.qmc.palette['rect1'], background_color, background_color, color]
                    else:
                        patch_colors = [color, background_color, rect1dim, background_color, background_color, color]
                    rects = self.ax.barh(i, widths, left=starts, height=self.barheight, color=patch_colors)
                elif not phases_times[0] and not phases_times[1] and phases_times[2]:
                    # only Finishing Phase is defined
                    phase3_percentage = (phases_times[2]/total_time) * 100.
                    phases_percentages = [100-phase3_percentage, phase3_percentage]
                    extended_phases_percentages = [self.m,self.g] + phases_percentages + [self.g,self.m*total_time/max_total_time]
                    widths = numpy.array(extended_phases_percentages)
                    starts = widths.cumsum() - widths
                    if active:
                        label3 = f"{str(round(phase3_percentage,digits)).rstrip('0').rstrip('.')}%  {stringfromseconds(phases_times[2],leadingzero=False)}" if phase3_percentage>20 else (f"{str(round(phase3_percentage,digits)).rstrip('0').rstrip('.')}%" if phase3_percentage>10 else '')
                    else:
                        label3 = ''
                    labels = [label, '', '', # QApplication.translate('Message', 'Profile missing DRY event'),
                        label3, '', stringfromseconds(total_time,leadingzero=False)]
                    # draw the bars
                    if active:
                        patch_colors = [color, background_color, background_color, self.aw.qmc.palette['rect3'], background_color, color]
                    else:
                        patch_colors = [color, background_color, background_color, rect3dim, background_color, color]
                    rects = self.ax.barh(i, widths, left=starts, height=self.barheight, color=patch_colors)
                # draw the row
                if rects is not None:
                    # draw the labels
                    tboxes = self.ax.bar_label(rects, label_type='center', labels=labels, fontproperties=prop)
                    # set the colors to ensure good contrast
                    if active:
                        text_colors = ['white' if self.aw.QColorBrightness(QColor(c)) < 128 else 'black' for c in patch_colors]
                    else:
                        text_colors = ['gainsboro' if self.aw.QColorBrightness(QColor(c)) < 128 else 'dimgrey' for c in patch_colors]
                    for j,tb in enumerate(tboxes):
                        tb.set_color(text_colors[j])
                    # we set the sketch params for elements of the graph
                    if self.aw.qmc.graphstyle:
                        for c in rects.get_children():
                            c.set_sketch_params(scale=1, length=700, randomness=12)
                    # we increase the row counter
                    i += 1

            # set the graph axis limits
            x,_ = self.fig.get_size_inches()
            self.fig.set_size_inches(x, (i-1)*0.35 + 0.445, forward=True)
            self.ax.set_ylim((-0.5, i-0.5)) # 0 to number of entries but shifted by one half to get rid of borders

#            # add legend
#            phases_names = [QApplication.translate('Button','Drying Phase'), QApplication.translate('Button','Maillard Phase'),
#                      QApplication.translate('Button','Finishing Phase')]
#            phases_colors = self.aw.qmc.palette['rect1'], self.aw.qmc.palette['rect2'], self.aw.qmc.palette['rect3']
#            import matplotlib.patches as mpatches
#            handles = [mpatches.Patch(color=color, label=name) for (name, color) in zip(phases_names,phases_colors)]
#            legend_labelcolor = 'white' if self.aw.QColorBrightness(QColor(background_color)) < 120 else 'black'
#            self.ax.legend(ncol=len(phases_names),handles=handles, bbox_to_anchor=(0,-0.01,1,0),
#                  loc='upper center', fontsize='small', shadow=False, frameon=False, fancybox=False, labelcolor=legend_labelcolor)

            self.fig.canvas.draw_idle()
            self.aw.scroller.setMaximumHeight(self.sizeHint().height())
        else:
            # if no profiles are given we set the canvas height to 0
            QSettings().setValue('MainSplitter',self.aw.splitter.saveState())
            if self.ax is not None:
                self.ax.set_ylim((0, 0))
            #self.fig.set_size_inches(0,0, forward=True) # this one crashes numpy on Windows and seems not needed
            self.aw.scroller.setMaximumHeight(0)
            self.aw.scroller.setVisible(False)
