#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread. If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""
charts
======

Provides matplotlib figure that are chart templates

Provides
--------

* ChartFigure: Main chart class

"""

import i18n

from matplotlib.figure import Figure

#use ugettext instead of getttext to avoid unicode errors
_ = i18n.language.ugettext


class ChartFigure(Figure):
    """Chart figure class with drawing method"""

    plot_type_fixed_attrs = {
        "plot": ["ydata"],
        "bar": ["left", "height"],
    }

    plot_type_xy_mapping = {
        "plot": ["xdata", "ydata"],
        "bar": ["left", "height"],
    }

    def __init__(self, *attributes):

        Figure.__init__(self, (5.0, 4.0), facecolor="white")

        self.attributes = attributes

        self.__axes = self.add_subplot(111)

        # Insert empty attributes with a dict for figure attributes
        if not self.attributes:
            self.attributes = [{}]

        self.draw_chart()

    def _setup_axes(self, axes_data):
        """Sets up axes for drawing chart"""

        self.__axes.clear()

        if "xlabel" in axes_data:
            if axes_data["xlabel"]:
                self.__axes.set_xlabel(axes_data["xlabel"])

        if "ylabel" in axes_data:
            if axes_data["ylabel"]:
                self.__axes.set_ylabel(axes_data["ylabel"])

    def draw_chart(self):
        """Plots chart from self.attributes.clear"""

        if not hasattr(self, "attributes"):
            return

        # The first element is always aaxes data
        self._setup_axes(self.attributes[0])

        for series in self.attributes[1:]:
            # Extract chart type
            chart_type_string = series.pop("type")

            x_str, y_str = self.plot_type_xy_mapping[chart_type_string]
            # Check xdata length
            if x_str in series and \
               len(series[x_str]) != len(series[y_str]):
                # Wrong length --> ignore xdata
                series.pop(x_str)
            else:
                series[x_str] = tuple(series[x_str])

            fixed_attrs = []
            for attr in self.plot_type_fixed_attrs[chart_type_string]:
                # Remove attr if it is a fixed (non-kwd) attr
                # If a fixed attr is missing, insert a dummy
                try:
                    fixed_attrs.append(tuple(series.pop(attr)))
                except KeyError:
                    fixed_attrs.append(())

            if all(fixed_attrs):

                # Draw series to axes
                chart_method = getattr(self.__axes, chart_type_string)
                chart_method(*fixed_attrs, **series)