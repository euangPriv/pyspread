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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

Model
=====

The model contains the core data structures of pyspread.
It is divided into layers.

Layer 3: CodeArray
Layer 2: DataArray
Layer 1: DictGrid
Layer 0: KeyValueStore

"""

import ast
import base64
import bz2
from copy import copy
import cStringIO
import datetime
from itertools import imap, ifilter, product
import re
import sys
from types import SliceType, IntType

import numpy

import wx

from src.config import config

from src.lib.typechecks import is_slice_like, is_string_like, is_generator_like
from src.lib.selection import Selection

from src.lib.undo import undoable

import src.lib.charts as charts
from src.gui.grid_panels import vlcpanel_factory

from src.sysvars import get_color, get_font_string


class KeyValueStore(dict):
    """Key-Value store in memory. Currently a dict with default value None.

    This class represents layer 0 of the model.

    The following methods mave been made undoable:
    * __setitem__
    * pop

    """

    def __init__(self, default_value=None):
        dict.__init__(self)

        self.default_value = default_value

    def __missing__(self, value):
        """Returns the default value None"""

        return self.default_value

    @undoable
    def __setitem__(self, key, value):
        old_value = self[key]
        dict.__setitem__(self, key, value)

        yield "__setitem__"
        # Undo actions
        if old_value is None:
            dict.pop(self, key)
        else:
            dict.__setitem__(self, key, old_value)

    @undoable
    def pop(self, key, *args):
        res = dict.pop(self, key, *args)

        yield "pop", res

        # Undo actions
        if res is not None:
            dict.__setitem__(self, key, res)

# End of class KeyValueStore

# -----------------------------------------------------------------------------



class CellAttributes(list):
    """Stores cell formatting attributes in a list of 3 - tuples

    The first element of each tuple is a Selection.
    The second element is the table
    The third element is a dict of attributes that are altered.

    The class provides attribute read access to single cells via __getitem__
    Otherwise it behaves similar to a list.

    The following methods mave been made undoable:
    * __setitem__
    * append

    List methods that may alter the list have been removed

    """

    def __init__(self, *args, **kwargs):
        self.__add__ = None
        self.__delattr__ = None
        self.__delitem__ = None
        self.__delslice__ = None
        self.__iadd__ = None
        self.__imul__ = None
        self.__rmul__ = None
        self.__setattr__ = None
        self.__setslice__ = None
        self.insert = None
        self.pop = None
        self.remove = None
        self.reverse = None
        self.sort = None

    default_cell_attributes = {
        "borderwidth_bottom": 1,
        "borderwidth_right": 1,
        "bordercolor_bottom": get_color(config["grid_color"]).GetRGB(),
        "bordercolor_right": get_color(config["grid_color"]).GetRGB(),
        "bgcolor": get_color(config["background_color"]).GetRGB(),
        "textfont": get_font_string(config["font"]),
        "pointsize": 10,
        "fontweight": wx.NORMAL,
        "fontstyle": wx.NORMAL,
        "textcolor": get_color(config["text_color"]).GetRGB(),
        "underline": False,
        "strikethrough": False,
        "locked": False,
        "angle": 0.0,
        "column-width": 75,
        "row-height": 26,
        "vertical_align": "top",
        "justification": "left",
        "frozen": False,
        "merge_area": None,
        "markup": False,
        "button_cell": False,
        "panel_cell": False,
        "video_volume": None,
    }

    # Cache for __getattr__ maps key to tuple of len and attr_dict

    _attr_cache = {}
    _table_cache = {}

    @undoable
    def append(self, value):
        list.append(self, value)
        self._attr_cache.clear()
        self._table_cache.clear()

        yield "append"

        # Undo actions

        list.pop(self)
        self._attr_cache.clear()
        self._table_cache.clear()

    def __getitem__(self, key):
        """Returns attribute dict for a single key"""

        assert not any(type(key_ele) is SliceType for key_ele in key)

        if key in self._attr_cache:
            cache_len, cache_dict = self._attr_cache[key]

            # Use cache result only if no new attrs have been defined
            if cache_len == len(self):
                return cache_dict

        # Update table cache if it is outdated (e.g. when creating a new grid)
        if len(self) != self._len_table_cache():
            self._update_table_cache()

        row, col, tab = key

        result_dict = copy(self.default_cell_attributes)

        try:
            for selection, attr_dict in self._table_cache[tab]:
                if (row, col) in selection:
                    result_dict.update(attr_dict)
        except KeyError:
            pass

        # Upddate cache with current length and dict
        self._attr_cache[key] = (len(self), result_dict)

        return result_dict

    @undoable
    def __setitem__(self, key, value):
        """Undoable version of list.__setitem__"""

        try:
            old_value = list.__getitem__(self, key)
        except IndexError:
            old_value = None

        list.__setitem__(self, key, value)

        self._attr_cache.clear()
        self._table_cache.clear()

        yield "__setitem__"

        if old_value is None:
            self.pop(key)
        else:
            list.__setitem__(self, key, old_value)

        self._attr_cache.clear()
        self._table_cache.clear()

    def _len_table_cache(self):
        """Returns the length of the table cache"""

        length = 0

        for table in self._table_cache:
            length += len(self._table_cache[table])

        return length

    def _update_table_cache(self):
        """Clears and updates the table cache to be in sync with self"""

        self._table_cache.clear()
        for sel, tab, val in self:
            try:
                self._table_cache[tab].append((sel, val))
            except KeyError:
                self._table_cache[tab] = [(sel, val)]

        assert len(self) == self._len_table_cache()

    def get_merging_cell(self, key):
        """Returns key of cell that merges the cell key

        or None if cell key not merged

        Parameters
        ----------
        key: 3-tuple of Integer
        \tThe key of the cell that is merged

        """

        row, col, tab = key

        # Is cell merged
        merge_area = self[key]["merge_area"]

        if merge_area:
            return merge_area[0], merge_area[1], tab

# End of class CellAttributes


class DictGrid(KeyValueStore):
    """The core data class with all information that is stored in a pys file.

    Besides grid code access via standard dict operations, it provides
    the following attributes:

    * cell_attributes: Stores cell formatting attributes
    * macros:          String of all macros

    This class represents layer 1 of the model.

    Parameters
    ----------
    shape: n-tuple of integer
    \tShape of the grid

    """

    def __init__(self, shape):
        KeyValueStore.__init__(self)

        self.shape = shape

        self.cell_attributes = CellAttributes()

        self.macros = u""

        default_row_height = config["default_row_height"]
        default_col_width = config["default_col_width"]

        # Keys have the format (row, table)
        self.row_heights = KeyValueStore(default_value=default_row_height)

        # Keys have the format (col, table)
        self.col_widths = KeyValueStore(default_value=default_col_width)

    def __getitem__(self, key):

        shape = self.shape

        for axis, key_ele in enumerate(key):
            if shape[axis] <= key_ele or key_ele < -shape[axis]:
                msg = "Grid index {key} outside grid shape {shape}."
                msg = msg.format(key=key, shape=shape)
                raise IndexError(msg)

        return KeyValueStore.__getitem__(self, key)

# End of class DictGrid

# -----------------------------------------------------------------------------


class DataArray(object):
    """DataArray provides enhanced grid read/write access.

    Enhancements comprise:
     * Slicing
     * Multi-dimensional operations such as insertion and deletion along 1 axis
     * Undo/redo operations

    This class represents layer 2 of the model.

    Parameters
    ----------
    shape: n-tuple of integer
    \tShape of the grid

    """

    def __init__(self, shape):
        self.dict_grid = DictGrid(shape)

        # Safe mode
        self.safe_mode = False

    def __eq__(self, other):
        if not hasattr(other, "dict_grid") or \
           not hasattr(other, "cell_attributes"):
            return NotImplemented

        return self.dict_grid == other.dict_grid and \
            self.cell_attributes == other.cell_attributes

    def __ne__(self, other):
        return not self.__eq__(other)

    # Data is the central content interface for loading / saving data.
    # It shall be used for loading and saving from and to pys and other files.
    # It shall be used for loading and saving macros.
    # It is not used for importinf and exporting data because these operations
    # are partial to the grid.

    def _get_data(self):
        """Returns dict of data content.

        Keys
        ----

        shape: 3-tuple of Integer
        \tGrid shape
        grid: Dict of 3-tuples to strings
        \tCell content
        attributes: List of 3-tuples
        \tCell attributes
        row_heights: Dict of 2-tuples to float
        \t(row, tab): row_height
        col_widths: Dict of 2-tuples to float
        \t(col, tab): col_width
        macros: String
        \tMacros from macro list

        """

        data = {}

        data["shape"] = self.shape
        data["grid"] = {}.update(self.dict_grid)
        data["attributes"] = [ca for ca in self.cell_attributes]
        data["row_heights"] = self.row_heights
        data["col_widths"] = self.col_widths
        data["macros"] = self.macros

        return data

    def _set_data(self, **kwargs):
        """Sets data from given parameters

        Old values are deleted.
        If a paremeter is not given, nothing is changed.

        Parameters
        ----------

        shape: 3-tuple of Integer
        \tGrid shape
        grid: Dict of 3-tuples to strings
        \tCell content
        attributes: List of 3-tuples
        \tCell attributes
        row_heights: Dict of 2-tuples to float
        \t(row, tab): row_height
        col_widths: Dict of 2-tuples to float
        \t(col, tab): col_width
        macros: String
        \tMacros from macro list

        """

        if "shape" in kwargs:
            self.shape = kwargs["shape"]

        if "grid" in kwargs:
            self.dict_grid.clear()
            self.dict_grid.update(kwargs["grid"])

        if "attributes" in kwargs:
            self.attributes[:] = kwargs["attributes"]

        if "row_heights" in kwargs:
            self.row_heights = kwargs["row_heights"]

        if "col_widths" in kwargs:
            self.col_widths = kwargs["col_widths"]

        if "macros" in kwargs:
            self.macros = kwargs["macros"]

    data = property(_get_data, _set_data)

    def get_row_height(self, row, tab):
        """Returns row height"""

        try:
            return self.row_heights[(row, tab)]

        except KeyError:
            return config["default_row_height"]

    def get_col_width(self, col, tab):
        """Returns column width"""

        try:
            return self.col_widths[(col, tab)]

        except KeyError:
            return config["default_col_width"]

    # Row and column attributes mask
    # Keys have the format (row, table)

    def _get_row_heights(self):
        """Returns row_heights dict"""

        return self.dict_grid.row_heights

    def _set_row_heights(self, row_heights):
        """Sets  macros string"""

        self.dict_grid.row_heights = row_heights

    row_heights = property(_get_row_heights, _set_row_heights)

    def _get_col_widths(self):
        """Returns col_widths dict"""

        return self.dict_grid.col_widths

    def _set_col_widths(self, col_widths):
        """Sets  macros string"""

        self.dict_grid.col_widths = col_widths

    col_widths = property(_get_col_widths, _set_col_widths)

    # Cell attributes mask
    def _get_cell_attributes(self):
        """Returns cell_attributes list"""

        return self.dict_grid.cell_attributes

    def _set_cell_attributes(self, value):
        """Setter for cell_atributes"""

        # Empty cell_attributes first
        self.cell_attributes[:] = []
        self.cell_attributes.extend(value)

    cell_attributes = attributes = \
        property(_get_cell_attributes, _set_cell_attributes)

    def __iter__(self):
        """Returns iterator over self.dict_grid"""

        return iter(self.dict_grid)

    def _get_macros(self):
        """Returns macros string"""

        return self.dict_grid.macros

    def _set_macros(self, macros):
        """Sets  macros string"""

        self.dict_grid.macros = macros

    macros = property(_get_macros, _set_macros)

    def keys(self):
        """Returns keys in self.dict_grid"""

        return self.dict_grid.keys()

    def pop(self, key):
        """Pops dict_grid

        Parameters
        ----------
        key: 3-tuple of Integer
        \tCell key that shall be popped

        """

        return self.dict_grid.pop(key)

    # Shape mask

    def _get_shape(self):
        """Returns dict_grid shape"""

        return self.dict_grid.shape

    @undoable
    def _set_shape(self, shape):
        """Deletes all cells beyond new shape and sets dict_grid shape

        Parameters
        ----------
        shape: 3-tuple of Integer
        \tTarget shape for grid

        """

        # Delete each cell that is beyond new borders

        old_shape = self.shape
        deleted_cells = {}

        if any(new_axis < old_axis
               for new_axis, old_axis in zip(shape, old_shape)):
            for key in self.dict_grid.keys():
                if any(key_ele >= new_axis
                       for key_ele, new_axis in zip(key, shape)):
                    deleted_cells[key] = self.pop(key)

        # Set dict_grid shape attribute
        self.dict_grid.shape = shape

        self._adjust_rowcol(0, 0, 0)
        self._adjust_cell_attributes(0, 0, 0)

        # Undo actions

        yield "_set_shape"

        self.shape = old_shape

        for key in deleted_cells:
            self[key] = deleted_cells[key]

    shape = property(_get_shape, _set_shape)

    def get_last_filled_cell(self, table=None):
        """Returns key for the bottommost rightmost cell with content

        Parameters
        ----------
        table: Integer, defaults to None
        \tLimit search to this table

        """

        maxrow = 0
        maxcol = 0

        for row, col, tab in self.dict_grid:
            if table is None or tab == table:
                maxrow = max(row, maxrow)
                maxcol = max(col, maxcol)

        return maxrow, maxcol, table

    # Pickle support

    def __getstate__(self):
        """Returns dict_grid for pickling

        Note that all persistent data is contained in the DictGrid class

        """

        return {"dict_grid": self.dict_grid}

    # Slice support

    def __getitem__(self, key):
        """Adds slicing access to cell code retrieval

        The cells are returned as a generator of generators, of ... of unicode.

        Parameters
        ----------
        key: n-tuple of integer or slice
        \tKeys of the cell code that is returned

        Note
        ----
        Classical Excel type addressing (A$1, ...) may be added here

        """

        for key_ele in key:
            if is_slice_like(key_ele):
                # We have something slice-like here

                return self.cell_array_generator(key)

            elif is_string_like(key_ele):
                # We have something string-like here
                msg = "Cell string based access not implemented"
                raise NotImplementedError(msg)

        # key_ele should be a single cell

        return self.dict_grid[key]

    def __setitem__(self, key, value):
        """Accepts index and slice keys

        Parameters
        ----------
        key: 3-tuple of Integer or Slice object
        \tCell key(s) that shall be set
        value: Object (should be Unicode or similar)
        \tCode for cell(s) to be set

        """

        single_keys_per_dim = []

        for axis, key_ele in enumerate(key):
            if is_slice_like(key_ele):
                # We have something slice-like here

                length = key[axis]
                slice_range = xrange(*key_ele.indices(length))
                single_keys_per_dim.append(slice_range)

            elif is_string_like(key_ele):
                # We have something string-like here

                raise NotImplementedError

            else:
                # key_ele is a single cell

                single_keys_per_dim.append((key_ele, ))

        single_keys = product(*single_keys_per_dim)

        for single_key in single_keys:
            if value:
                # Never change merged cells
                merging_cell = \
                    self.cell_attributes.get_merging_cell(single_key)
                if merging_cell is None or merging_cell == single_key:
                    self.dict_grid[single_key] = value
            else:
                # Value is empty --> delete cell
                try:
                    self.pop(key)

                except (KeyError, TypeError):
                    pass

    def cell_array_generator(self, key):
        """Generator traversing cells specified in key

        Parameters
        ----------
        key: Iterable of Integer or slice
        \tThe key specifies the cell keys of the generator

        """

        for i, key_ele in enumerate(key):

            # Get first element of key that is a slice
            if type(key_ele) is SliceType:
                slc_keys = xrange(*key_ele.indices(self.dict_grid.shape[i]))
                key_list = list(key)

                key_list[i] = None

                has_subslice = any(type(ele) is SliceType for ele in key_list)

                for slc_key in slc_keys:
                    key_list[i] = slc_key

                    if has_subslice:
                        # If there is a slice left yield generator
                        yield self.cell_array_generator(key_list)

                    else:
                        # No slices? Yield value
                        yield self[tuple(key_list)]

                break

    def _shift_rowcol(self, insertion_point, no_to_insert):
        """Shifts row and column sizes when a table is inserted or deleted"""

        # Shift row heights

        new_row_heights = {}
        del_row_heights = []

        for row, tab in self.row_heights:
            if tab > insertion_point:
                new_row_heights[(row, tab + no_to_insert)] = \
                    self.row_heights[(row, tab)]
                del_row_heights.append((row, tab))

        for row, tab in new_row_heights:
            self.set_row_height(row, tab, new_row_heights[(row, tab)])

        for row, tab in del_row_heights:
            if (row, tab) not in new_row_heights:
                self.set_row_height(row, tab, None)

        # Shift column widths

        new_col_widths = {}
        del_col_widths = []

        for col, tab in self.col_widths:
            if tab > insertion_point:
                new_col_widths[(col, tab + no_to_insert)] = \
                    self.col_widths[(col, tab)]
                del_col_widths.append((col, tab))

        for col, tab in new_col_widths:
            self.set_col_width(col, tab, new_col_widths[(col, tab)])

        for col, tab in del_col_widths:
            if (col, tab) not in new_col_widths:
                self.set_col_width(col, tab, None)

    def _adjust_rowcol(self, insertion_point, no_to_insert, axis, tab=None):
        """Adjusts row and column sizes on insertion/deletion"""

        if axis == 2:
            self._shift_rowcol(insertion_point, no_to_insert)
            return

        assert axis in (0, 1)

        cell_sizes = self.col_widths if axis else self.row_heights
        set_cell_size = self.set_col_width if axis else self.set_row_height

        new_sizes = {}
        del_sizes = []

        for pos, table in cell_sizes:
            if pos > insertion_point and (tab is None or tab == table):
                if 0 <= pos + no_to_insert < self.shape[axis]:
                    new_sizes[(pos + no_to_insert, table)] = \
                        cell_sizes[(pos, table)]
                del_sizes.append((pos, table))

        for pos, table in new_sizes:
            set_cell_size(pos, table, new_sizes[(pos, table)])

        for pos, table in del_sizes:
            if (pos, table) not in new_sizes:
                set_cell_size(pos, table, None)

    def _get_adjusted_merge_area(self, attrs, insertion_point, no_to_insert,
                                 axis):
        """Returns updated merge area

        Parameters
        ----------
        attrs: Dict
        \tCell attribute dictionary that shall be adjusted
        insertion_point: Integer
        \tPont on axis, before which insertion takes place
        no_to_insert: Integer >= 0
        \tNumber of rows/cols/tabs that shall be inserted
        axis: Integer in range(2)
        \tSpecifies number of dimension, i.e. 0 == row, 1 == col

        """

        assert axis in range(2)

        if "merge_area" not in attrs or attrs["merge_area"] is None:
            return

        top, left, bottom, right = attrs["merge_area"]
        selection = Selection([(top, left)], [(bottom, right)], [], [], [])

        selection.insert(insertion_point, no_to_insert, axis)

        __top, __left = selection.block_tl[0]
        __bottom, __right = selection.block_br[0]

        # Adjust merge area if it is beyond the grid shape
        rows, cols, tabs = self.shape

        if __top < 0 and __bottom < 0 or __top >= rows and __bottom >= rows or\
           __left < 0 and __right < 0 or __left >= cols and __right >= cols:
            return

        if __top < 0:
            __top = 0

        if __top >= rows:
            __top = rows - 1

        if __bottom < 0:
            __bottom = 0

        if __bottom >= rows:
            __bottom = rows - 1

        if __left < 0:
            __left = 0

        if __left >= cols:
            __left = cols - 1

        if __right < 0:
            __right = 0

        if __right >= cols:
            __right = cols - 1

        return __top, __left, __bottom, __right

    def _adjust_cell_attributes(self, insertion_point, no_to_insert, axis,
                                tab=None, cell_attrs=None):
        """Adjusts cell attributes on insertion/deletion

        Parameters
        ----------
        insertion_point: Integer
        \tPont on axis, before which insertion takes place
        no_to_insert: Integer >= 0
        \tNumber of rows/cols/tabs that shall be inserted
        axis: Integer in range(3)
        \tSpecifies number of dimension, i.e. 0 == row, 1 == col, ...
        tab: Integer, defaults to None
        \tIf given then insertion is limited to this tab for axis < 2
        cell_attrs: List, defaults to []
        \tIf not empty then the given cell attributes replace the existing ones

        """

        def replace_cell_attributes_table(index, new_table):
            """Replaces table in cell_attributes item"""

            ca = list(list.__getitem__(self.cell_attributes, index))
            ca[1] = new_table
            self.cell_attributes.__setitem__(index, tuple(ca))

        def get_ca_with_updated_ma(attrs, merge_area):
            """Returns cell attributes with updated merge area"""

            new_attrs = copy(attrs)

            if merge_area is None:
                try:
                    new_attrs.pop("merge_area")
                except KeyError:
                    pass
            else:
                new_attrs["merge_area"] = merge_area

            return new_attrs

        if axis not in range(3):
            raise ValueError("Axis must be in [0, 1, 2]")

        assert tab is None or tab >= 0

        if cell_attrs is None:
            cell_attrs = []

        if cell_attrs:
            self.cell_attributes[:] = cell_attrs

        elif axis < 2:
            # Adjust selections on given table

            ca_updates = {}
            for i, (selection, table, attrs) in enumerate(
                                                    self.cell_attributes):
                selection = copy(selection)
                if tab is None or tab == table:
                    selection.insert(insertion_point, no_to_insert, axis)
                    # Update merge area if present
                    merge_area = self._get_adjusted_merge_area(attrs,
                                                               insertion_point,
                                                               no_to_insert,
                                                               axis)
                    new_attrs = get_ca_with_updated_ma(attrs, merge_area)

                    ca_updates[i] = selection, table, new_attrs

            for idx in ca_updates:
                self.cell_attributes[idx] = ca_updates[idx]

        elif axis == 2:
            # Adjust tabs

            pop_indices = []

            for i, cell_attribute in enumerate(self.cell_attributes):
                selection, table, value = cell_attribute

                if no_to_insert < 0 and insertion_point <= table:
                    if insertion_point > table + no_to_insert:
                        # Delete later
                        pop_indices.append(i)
                    else:
                        replace_cell_attributes_table(i, table + no_to_insert)

                elif insertion_point < table:
                    # Insert
                    replace_cell_attributes_table(i, table + no_to_insert)

            for i in pop_indices[::-1]:
                self.cell_attributes.pop(i)

        self.cell_attributes._attr_cache.clear()
        self.cell_attributes._update_table_cache()

    def insert(self, insertion_point, no_to_insert, axis, tab=None):
        """Inserts no_to_insert rows/cols/tabs/... before insertion_point

        Parameters
        ----------

        insertion_point: Integer
        \tPont on axis, before which insertion takes place
        no_to_insert: Integer >= 0
        \tNumber of rows/cols/tabs that shall be inserted
        axis: Integer
        \tSpecifies number of dimension, i.e. 0 == row, 1 == col, ...
        tab: Integer, defaults to None
        \tIf given then insertion is limited to this tab for axis < 2

        """

        if not 0 <= axis <= len(self.shape):
            raise ValueError("Axis not in grid dimensions")

        if insertion_point > self.shape[axis] or \
           insertion_point < -self.shape[axis]:
            raise IndexError("Insertion point not in grid")

        new_keys = {}
        del_keys = []

        for key in self.dict_grid.keys():
            if key[axis] > insertion_point and (tab is None or tab == key[2]):
                new_key = list(key)
                new_key[axis] += no_to_insert
                if 0 <= new_key[axis] < self.shape[axis]:
                    new_keys[tuple(new_key)] = self(key)
                del_keys.append(key)

        # Now re-insert moved keys

        for key in del_keys:
            if key not in new_keys and self(key) is not None:
                self.pop(key)

        self._adjust_rowcol(insertion_point, no_to_insert, axis, tab=tab)
        self._adjust_cell_attributes(insertion_point, no_to_insert, axis, tab)

        for key in new_keys:
            self.__setitem__(key, new_keys[key])

    def delete(self, deletion_point, no_to_delete, axis, tab=None):
        """Deletes no_to_delete rows/cols/... starting with deletion_point

        Axis specifies number of dimension, i.e. 0 == row, 1 == col, 2 == tab

        """

        if not 0 <= axis < len(self.shape):
            raise ValueError("Axis not in grid dimensions")

        if no_to_delete < 0:
            raise ValueError("Cannot delete negative number of rows/cols/...")

        elif no_to_delete >= self.shape[axis]:
            raise ValueError("Last row/column/table must not be deleted")

        if deletion_point > self.shape[axis] or \
           deletion_point <= -self.shape[axis]:
            raise IndexError("Deletion point not in grid")

        new_keys = {}
        del_keys = []

        # Note that the loop goes over a list that copies all dict keys
        for key in self.dict_grid.keys():
            if tab is None or tab == key[2]:
                if deletion_point <= key[axis] < deletion_point + no_to_delete:
                    del_keys.append(key)

                elif key[axis] >= deletion_point + no_to_delete:
                    new_key = list(key)
                    new_key[axis] -= no_to_delete

                    new_keys[tuple(new_key)] = self(key)
                    del_keys.append(key)

        # Now re-insert moved keys

        for key in new_keys:
            self.__setitem__(key, new_keys[key])

        for key in del_keys:
            if key not in new_keys and self(key) is not None:
                self.pop(key)

        self._adjust_rowcol(deletion_point, -no_to_delete, axis, tab=tab)
        self._adjust_cell_attributes(deletion_point, -no_to_delete, axis)

    def set_row_height(self, row, tab, height):
        """Sets row height"""

        try:
            old_height = self.row_heights.pop((row, tab))

        except KeyError:
            old_height = None

        if height is not None:
            self.row_heights[(row, tab)] = float(height)

    def set_col_width(self, col, tab, width):
        """Sets column width"""

        try:
            old_width = self.col_widths.pop((col, tab))

        except KeyError:
            old_width = None

        if width is not None:
            self.col_widths[(col, tab)] = float(width)

    # Element access via call

    __call__ = __getitem__

# End of class DataArray

# -----------------------------------------------------------------------------


class CodeArray(DataArray):
    """CodeArray provides objects when accessing cells via __getitem__

    Cell code can be accessed via function call

    This class represents layer 3 of the model.

    """

    # Cache for results from __getitem__ calls
    result_cache = {}

    # Cache for frozen objects
    frozen_cache = {}

    # Custom font storage
    custom_fonts = {}

    def __setitem__(self, key, value):
        """Sets cell code and resets result cache"""

        # Prevent unchanged cells from being recalculated on cursor movement

        repr_key = repr(key)

        unchanged = (repr_key in self.result_cache and
                     value == self(key)) or \
                    ((value is None or value == "") and
                     repr_key not in self.result_cache)

        DataArray.__setitem__(self, key, value)

        if not unchanged:
            # Reset result cache
            self.result_cache = {}

    def __getitem__(self, key):
        """Returns _eval_cell"""

        # Frozen cell handling
        if all(type(k) is not SliceType for k in key):
            frozen_res = self.cell_attributes[key]["frozen"]
            if frozen_res:
                if repr(key) in self.frozen_cache:
                    return self.frozen_cache[repr(key)]
                else:
                    # Frozen cache is empty.
                    # Maybe we have a reload without the frozen cache
                    result = self._eval_cell(key, self(key))
                    self.frozen_cache[repr(key)] = result
                    return result

        # Normal cell handling

        if repr(key) in self.result_cache:
            return self.result_cache[repr(key)]

        elif self(key) is not None:
            result = self._eval_cell(key, self(key))
            self.result_cache[repr(key)] = result

            return result

    def _make_nested_list(self, gen):
        """Makes nested list from generator for creating numpy.array"""

        res = []

        for ele in gen:
            if ele is None:
                res.append(None)

            elif not is_string_like(ele) and is_generator_like(ele):
                # Nested generator
                res.append(self._make_nested_list(ele))

            else:
                res.append(ele)

        return res

    def _get_assignment_target_end(self, ast_module):
        """Returns position of 1st char after assignment traget.

        If there is no assignment, -1 is returned

        If there are more than one of any ( expressions or assigments)
        then a ValueError is raised.

        """

        if len(ast_module.body) > 1:
            raise ValueError("More than one expression or assignment.")

        elif len(ast_module.body) > 0 and \
                type(ast_module.body[0]) is ast.Assign:
            if len(ast_module.body[0].targets) != 1:
                raise ValueError("More than one assignment target.")
            else:
                return len(ast_module.body[0].targets[0].id)

        return -1

    def _get_updated_environment(self, env_dict=None):
        """Returns globals environment with 'magic' variable

        Parameters
        ----------
        env_dict: Dict, defaults to {'S': self}
        \tDict that maps global variable name to value

        """

        if env_dict is None:
            env_dict = {'S': self}

        env = globals().copy()
        env.update(env_dict)

        return env

    def _eval_cell(self, key, code):
        """Evaluates one cell and returns its result"""

        # Flatten helper function
        def nn(val):
            """Returns flat numpy arraz without None values"""
            try:
                return numpy.array(filter(None, val.flat))

            except AttributeError:
                # Probably no numpy array
                return numpy.array(filter(None, val))

        # Set up environment for evaluation

        env_dict = {'X': key[0], 'Y': key[1], 'Z': key[2], 'bz2': bz2,
                    'base64': base64, 'charts': charts, 'nn': nn,
                    'R': key[0], 'C': key[1], 'T': key[2], 'S': self,
                    'vlcpanel_factory': vlcpanel_factory}
        env = self._get_updated_environment(env_dict=env_dict)

        #_old_code = self(key)

        # Return cell value if in safe mode

        if self.safe_mode:
            return code

        # If cell is not present return None

        if code is None:
            return

        elif is_generator_like(code):
            # We have a generator object

            return numpy.array(self._make_nested_list(code), dtype="O")

        # If only 1 term in front of the "=" --> global

        try:
            assignment_target_error = None
            module = ast.parse(code)
            assignment_target_end = self._get_assignment_target_end(module)

        except ValueError, err:
            assignment_target_error = ValueError(err)

        except AttributeError, err:
            # Attribute Error includes RunTimeError
            assignment_target_error = AttributeError(err)

        except Exception, err:
            assignment_target_error = Exception(err)

        if assignment_target_error is None and assignment_target_end != -1:
            glob_var = code[:assignment_target_end]
            expression = code.split("=", 1)[1]
            expression = expression.strip()

            # Delete result cache because assignment changes results
            self.result_cache.clear()

        else:
            glob_var = None
            expression = code

        if assignment_target_error is not None:
            result = assignment_target_error

        else:

            try:
                import signal

                signal.signal(signal.SIGALRM, self.handler)
                signal.alarm(config["timeout"])

            except:
                # No POSIX system
                pass

            try:
                result = eval(expression, env, {})

            except AttributeError, err:
                # Attribute Error includes RunTimeError
                result = AttributeError(err)

            except RuntimeError, err:
                result = RuntimeError(err)

            except Exception, err:
                result = Exception(err)

            finally:
                try:
                    signal.alarm(0)
                except:
                    # No POSIX system
                    pass

        # Change back cell value for evaluation from other cells
        #self.dict_grid[key] = _old_code

        if glob_var is not None:
            globals().update({glob_var: result})

        return result

    def pop(self, key):
        """Pops dict_grid with undo and redo support

        Parameters
        ----------
        key: 3-tuple of Integer
        \tCell key that shall be popped

        """

        try:
            self.result_cache.pop(repr(key))

        except KeyError:
            pass

        return DataArray.pop(self, key)

    def reload_modules(self):
        """Reloads modules that are available in cells"""

        import src.lib.charts as charts
        from src.gui.grid_panels import vlcpanel_factory
        modules = [charts, bz2, base64, re, ast, sys, wx, numpy, datetime]

        for module in modules:
            reload(module)

    def clear_globals(self):
        """Clears all newly assigned globals"""

        base_keys = ['cStringIO', 'IntType', 'KeyValueStore', 'undoable',
                     'is_generator_like', 'is_string_like', 'bz2', 'base64',
                     '__package__', 're', 'config', '__doc__', 'SliceType',
                     'CellAttributes', 'product', 'ast', '__builtins__',
                     '__file__', 'charts', 'sys', 'is_slice_like', '__name__',
                     'copy', 'imap', 'wx', 'ifilter', 'Selection', 'DictGrid',
                     'numpy', 'CodeArray', 'DataArray', 'datetime',
                     'vlcpanel_factory']

        for key in globals().keys():
            if key not in base_keys:
                globals().pop(key)

    def get_globals(self):
        """Returns globals dict"""

        return globals()

    def execute_macros(self):
        """Executes all macros and returns result string

        Executes macros only when not in safe_mode

        """

        if self.safe_mode:
            return '', "Safe mode activated. Code not executed."

        # Windows exec does not like Windows newline
        self.macros = self.macros.replace('\r\n', '\n')

        # Set up environment for evaluation
        globals().update(self._get_updated_environment())

        # Create file-like string to capture output
        code_out = cStringIO.StringIO()
        code_err = cStringIO.StringIO()
        err_msg = cStringIO.StringIO()

        # Capture output and errors
        sys.stdout = code_out
        sys.stderr = code_err

        try:
            import signal

            signal.signal(signal.SIGALRM, self.handler)
            signal.alarm(config["timeout"])

        except:
            # No POSIX system
            pass

        try:
            exec(self.macros, globals())
            try:
                signal.alarm(0)
            except:
                # No POSIX system
                pass

        except Exception:
            # Print exception
            # (Because of how the globals are handled during execution
            # we must import modules here)
            from traceback import print_exception
            from src.lib.exception_handling import get_user_codeframe
            exc_info = sys.exc_info()
            user_tb = get_user_codeframe(exc_info[2]) or exc_info[2]
            print_exception(exc_info[0], exc_info[1], user_tb, None, err_msg)
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        results = code_out.getvalue()
        errs = code_err.getvalue() + err_msg.getvalue()

        code_out.close()
        code_err.close()

        # Reset result cache
        self.result_cache.clear()

        # Reset frozen cache
        self.frozen_cache.clear()

        return results, errs

    def _sorted_keys(self, keys, startkey, reverse=False):
        """Generator that yields sorted keys starting with startkey

        Parameters
        ----------

        keys: Iterable of tuple/list
        \tKey sequence that is sorted
        startkey: Tuple/list
        \tFirst key to be yielded
        reverse: Bool
        \tSort direction reversed if True

        """

        tuple_key = lambda t: t[::-1]
        if reverse:
            tuple_cmp = lambda t: t[::-1] > startkey[::-1]
        else:
            tuple_cmp = lambda t: t[::-1] < startkey[::-1]

        searchkeys = sorted(keys, key=tuple_key, reverse=reverse)
        searchpos = sum(1 for _ in ifilter(tuple_cmp, searchkeys))

        searchkeys = searchkeys[searchpos:] + searchkeys[:searchpos]

        for key in searchkeys:
            yield key

    def string_match(self, datastring, findstring, flags=None):
        """
        Returns position of findstring in datastring or None if not found.
        Flags is a list of strings. Supported strings are:
         * "MATCH_CASE": The case has to match for valid find
         * "WHOLE_WORD": The word has to be surrounded by whitespace characters
                         if in the middle of the string
         * "REG_EXP":    A regular expression is evaluated.

        """

        if type(datastring) is IntType:  # Empty cell
            return None

        if flags is None:
            flags = []

        if "REG_EXP" in flags:
            match = re.search(findstring, datastring)
            if match is None:
                pos = -1
            else:
                pos = match.start()
        else:
            if "MATCH_CASE" not in flags:
                datastring = datastring.lower()
                findstring = findstring.lower()

            if "WHOLE_WORD" in flags:
                pos = -1
                matchstring = r'\b' + findstring + r'+\b'
                for match in re.finditer(matchstring, datastring):
                    pos = match.start()
                    break  # find 1st occurrance
            else:
                pos = datastring.find(findstring)

        if pos == -1:
            return None
        else:
            return pos

    def findnextmatch(self, startkey, find_string, flags, search_result=True):
        """ Returns a tuple with the position of the next match of find_string

        Returns None if string not found.

        Parameters:
        -----------
        startkey:   Start position of search
        find_string:String to be searched for
        flags:      List of strings, out of
                    ["UP" xor "DOWN", "WHOLE_WORD", "MATCH_CASE", "REG_EXP"]
        search_result: Bool, defaults to True
        \tIf True then the search includes the result string (slower)

        """

        assert "UP" in flags or "DOWN" in flags
        assert not ("UP" in flags and "DOWN" in flags)

        if search_result:
            def is_matching(key, find_string, flags):
                code = self(key)
                if self.string_match(code, find_string, flags) is not None:
                    return True
                else:
                    res_str = unicode(self[key])
                    return self.string_match(res_str, find_string, flags) \
                        is not None

        else:
            def is_matching(code, find_string, flags):
                code = self(key)
                return self.string_match(code, find_string, flags) is not None

        # List of keys in sgrid in search order

        reverse = "UP" in flags

        for key in self._sorted_keys(self.keys(), startkey, reverse=reverse):
            try:
                if is_matching(key, find_string, flags):
                    return key

            except Exception:
                # re errors are cryptical: sre_constants,...
                pass

    def handler(self, signum, frame):
        raise RuntimeError("Timeout after {} s.".format(config["timeout"]))

# End of class CodeArray
