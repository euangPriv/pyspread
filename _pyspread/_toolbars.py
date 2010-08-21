#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6 on Sun May 25 23:31:23 2008

# Copyright 2008 Martin Manns
# Distributed under the terms of the GNU General Public License
# generated by wxGlade 0.6 on Mon Mar 17 23:22:49 2008

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
_toolbars
===========

Provides toolbars

Provides:
---------
  1. MainToolbar: Main toolbar of pyspread
  2. FindToolbar: Toolbar for Find operation
  3. AttributesToolbar: Toolbar for editing cell attributes

"""
import wx
import wx.lib.colourselect as csel

from _pyspread.config import odftags, border_toggles, default_cell_attributes
from _pyspread.config import FONT_SIZES, DEFAULT_FONT, faces, icons, small_icon_size

from _pyspread._interfaces import get_font_list
import _widgets

class MainToolbar(wx.ToolBar):
    """Main application toolbar, built from attribute toolbardata

    toolbardata has the following structure:
    [[toolobject, "Methodname", "Label",
                  "Iconname", "Tooltip", "Help string"] , \
    ...
    ["Separator"] ,\
    ...
    ]

    """

    tool = wx.ITEM_NORMAL

    toolbardata = [
    [tool, "OnFileNew", "New", "FileNew", "New spreadsheet", 
        "Create a new, empty spreadsheet"], \
    [tool, "OnFileOpen", "Open", "FileOpen", "Open spreadsheet", 
        "Open spreadsheet from file"], \
    [tool, "OnFileSave", "Save", "FileSave", "Save spreadsheet", 
        "Save spreadsheet to file"], \
    ["Separator"] , \
    [tool, "OnUndo", "Undo", "Undo", "Undo", "Undo last operation"], \
    [tool, "OnRedo", "Redo", "Redo", "Redo", "Redo next operation"], \
    ["Separator"] , \
    [tool, "OnShowFind", "Find", "Find", "Find", "Find cell by content"], \
    [tool, "OnShowFindReplace", "Replace", "FindReplace", "Replace", 
        "Replace strings in cells"], \
    ["Separator"] , \
    [tool, "OnCut", "Cut", "EditCut", "Cut", "Cut cells to clipboard"], \
    [tool, "OnCopy", "Copy", "EditCopy", "Copy", 
        "Copy the input strings of the cells to clipboard"], \
    [tool, "OnCopyResult", "Copy Results", "EditCopyRes", "Copy Results", 
        "Copy the result strings of the cells to the clipboard"], \
    [tool, "OnPaste", "Paste", "EditPaste", "Paste", 
        "Paste cell from clipboard"], \
    ["Separator"] , \
    [tool, "OnFilePrint", "Print", "FilePrint", "Print current spreadsheet", 
        "Print current spreadsheet"], \
    ]

    def _add_tools(self):
        """Adds tools from self.toolbardata to self"""
        
        for tool in self.toolbardata:
            obj = tool[0]
            if obj == "Separator":
                self.AddSeparator()
            elif obj == self.tool:
                methodname = tool[1]
                method = self.parent.__getattribute__(methodname)
                label = tool[2]
                icon = wx.Bitmap(icons[tool[3]], wx.BITMAP_TYPE_ANY)
                icon2 = wx.NullBitmap
                tooltip = tool[4]
                helpstring = tool[5]
                toolid = wx.NewId()
                self.AddLabelTool(toolid, label, icon, icon2, obj, 
                                  tooltip, helpstring)
                self.parent.Bind(wx.EVT_TOOL, method, id=toolid)
            else:
                raise TypeError, "Toolbar item unknown"

    def __init__(self, *args, **kwargs):
        wx.ToolBar.__init__(self, *args, **kwargs)
        self.parent = args[0]
        self._add_tools()


# end of class MainToolbar


class FindToolbar(wx.ToolBar):
    """Toolbar for find operations (replaces wxFindReplaceDialog)"""
    
    # Search flag buttons
    search_options_buttons = { \
      "matchcase_tb": { \
        "ID": wx.NewId(), 
        "iconname": "SearchCaseSensitive", 
        "shorthelp": "Case sensitive",
        "longhelp": "Case sensitive search",
        "flag": "MATCH_CASE",
      },
      "regexp_tb": { 
        "ID": wx.NewId(), 
        "iconname": "SearchRegexp", 
        "shorthelp": "Regular expression",
        "longhelp": "Treat search string as regular expression",
        "flag": "REG_EXP",
      },
      "wholeword_tb": { \
        "ID": wx.NewId(), 
        "iconname": "SearchWholeword", 
        "shorthelp": "Whole word",
        "longhelp": "Search string is surronted by whitespace characters",
        "flag": "WHOLE_WORD",
      },
    }
    
    def __init__(self, *args, **kwargs):
        kwargs["style"] = wx.TB_FLAT | wx.TB_NODIVIDER
        wx.ToolBar.__init__(self, *args, **kwargs)
        
        self.parent = args[0]
        
        # Search entry control
        self.search_history = []
        self.search = wx.SearchCtrl(self, size=(150, -1), \
                        style=wx.TE_PROCESS_ENTER | wx.NO_BORDER)
        self.search.SetToolTip(wx.ToolTip("Enter search string for " + \
                                "searching in the grid cell source code"))
        self.menu = self.make_menu()
        self.search.SetMenu(self.menu)
        self.SetToolBitmapSize(small_icon_size)
        self.AddControl(self.search)
        
        # Search direction toggle button
        self.search_options = ["DOWN"]
        self.setup_searchdirection_togglebutton()
        
        # Search flags buttons
        sfbs = self.search_options_buttons
        for name in sfbs:
            iconname = sfbs[name]["iconname"]
            __id = sfbs[name]["ID"]
            shorthelp = sfbs[name]["shorthelp"]
            longhelp = sfbs[name]["longhelp"]
            
            bmp = wx.Bitmap(icons[iconname], wx.BITMAP_TYPE_PNG)
            self.SetToolBitmapSize(small_icon_size)
            self.AddCheckLabelTool(__id, name, bmp, 
                shortHelp=shorthelp, longHelp=longhelp)
            
        # Event bindings
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self.search)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self.search)
        self.Bind(wx.EVT_MENU_RANGE, self.OnSearchFlag)
        self.Bind(wx.EVT_BUTTON, self.OnSearchDirectionButton, 
                                 self.search_direction_tb)
        self.Bind(wx.EVT_MENU, self.OnMenu)
        self.Realize()
    
    def setup_searchdirection_togglebutton(self):
        """Setup of search direction toggle button for searching up and down"""
        
        iconnames = ["SearchDirectionUp", "SearchDirectionDown"]
        bmplist = [wx.Bitmap(icons[iconname]) for iconname in iconnames]
        self.search_direction_tb = _widgets.BitmapToggleButton(self, bmplist)
        
        self.search_direction_tb.SetInitialSize()
        self.search_direction_tb.SetToolTip( \
            wx.ToolTip("Search direction"))
        self.SetToolBitmapSize(small_icon_size)
        self.AddControl(self.search_direction_tb)
        
    
    def make_menu(self):
        """Creates the search menu"""
        
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        
        for __id, txt in enumerate(self.search_history):
            menu.Append(__id, txt)
        return menu
    
    def OnMenu(self, event):
        """Search history has been selected"""
        
        __id = event.GetId()
        try:
            menuitem = event.GetEventObject().FindItemById(__id)
            selected_text = menuitem.GetItemLabel()
            self.search.SetValue(selected_text)
        except AttributeError:
            # Not called by menu
            event.Skip()
    
    def OnSearch(self, event):
        """Event handler for starting the search"""
        
        search_string = self.search.GetValue()
        
        if search_string not in self.search_history:
            self.search_history.append(search_string)
        if len(self.search_history) > 10:
            self.search_history.pop(0)
            
        self.menu = self.make_menu()
        self.search.SetMenu(self.menu)
        
        search_flags = self.search_options + ["FIND_NEXT"]
        findpos = self.parent.find_position(search_string, search_flags)
        self.parent.find_gui_feedback(event, search_string, findpos)
        self.search.SetFocus()
    
    def OnSearchDirectionButton(self, event):
        """Event handler for search direction toggle button"""
        
        if "DOWN" in self.search_options:
            flag_index = self.search_options.index("DOWN")
            self.search_options[flag_index] = "UP"
        elif "UP" in self.search_options:
            flag_index = self.search_options.index("UP")
            self.search_options[flag_index] = "DOWN"
        else:
            raise AttributeError, "Neither UP nor DOWN in search_flags"
        event.Skip()
    
    def OnSearchFlag(self, event):
        """Event handler for search flag toggle buttons"""
        
        sfbs = self.search_options_buttons
        for name in sfbs:
            if sfbs[name]["ID"] == event.GetId():
                if event.IsChecked():
                    self.search_options.append(sfbs[name]["flag"])
                else:
                    flag_index = self.search_options.index(sfbs[name]["flag"])
                    self.search_options.pop(flag_index)
        event.Skip()

# end of class FindToolbar


class AttributesToolbar(wx.ToolBar):
    """Toolbar for editing cell attributes"""
        
    def __init__(self, *args, **kwargs):
        kwargs["style"] = wx.TB_FLAT | wx.TB_NODIVIDER
        self.parent = args[0]
        self.grid = self.parent.MainGrid
        self.pysgrid = self.grid.pysgrid
        
        wx.ToolBar.__init__(self, *args, **kwargs)
        
        self._create_font_choice_combo()
        self._create_font_size_combo()
        self._create_font_face_buttons()
        self._create_justification_button()
        self._create_alignment_button()
        self._create_borderchoice_combo()
        self._create_penwidth_combo()
        self._create_color_buttons()
        self._create_textrotation_spinctrl()
        
        self.Realize()
    
    # Create toolbar widgets
    # ----------------------
    
    def _create_font_choice_combo(self):
        """Creates font choice combo box"""
        
        self.fonts = get_font_list()
        self.font_choice_combo = _widgets.FontChoiceCombobox(self, \
                                    choices=self.fonts, style=wx.CB_READONLY,
                                    size=(125, -1))
        self.SetToolBitmapSize(self.font_choice_combo.GetSize())
        self.AddControl(self.font_choice_combo)
        self.Bind(wx.EVT_COMBOBOX, self.OnTextFont, self.font_choice_combo)
    
    def _create_font_size_combo(self):
        """Creates font size combo box"""
        
        self.std_font_sizes = FONT_SIZES
        font_size = str(DEFAULT_FONT.GetPointSize())
        self.font_size_combo = wx.ComboBox(self, -1, value=font_size,
            size=(60, -1), choices=map(unicode, self.std_font_sizes),
            style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.SetToolBitmapSize(small_icon_size)
        self.AddControl(self.font_size_combo)
        self.Bind(wx.EVT_COMBOBOX, self.OnTextSize, self.font_size_combo)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextSize, self.font_size_combo)
    
    def _create_font_face_buttons(self):
        """Creates font face buttons"""
        
        font_face_buttons = [
            ("bold_button", wx.FONTWEIGHT_BOLD, "FormatTextBold", "Bold"),
            ("italic_button", wx.FONTSTYLE_ITALIC, "FormatTextItalic", 
                "Italic"),
            ("underline_button", wx.FONTFLAG_UNDERLINED, "FormatTextUnderline", 
                "Underline"),
            ("strikethrough_button", wx.FONTFLAG_STRIKETHROUGH, 
                "FormatTextStrikethrough", "Strikethrough"),
            ("freeze_button", wx.FONTFLAG_MASK, "Freeze", "Freeze"),
            ]
            
        for name, __id, iconname, buttonname in font_face_buttons:
            bmp = wx.Bitmap(icons[iconname])
            self.SetToolBitmapSize(small_icon_size)
            self.AddCheckLabelTool(__id, name, bmp, shortHelp=buttonname)
            self.Bind(wx.EVT_TOOL, self.OnToolClick, id=__id)
    
    def _create_justification_button(self):
        """Creates horizontal justification button"""
        
        iconnames = ["JustifyLeft", "JustifyCenter", "JustifyRight"]
        bmplist = [wx.Bitmap(icons[iconname]) for iconname in iconnames]
        self.justify_tb = _widgets.BitmapToggleButton(self, bmplist)
        self.Bind(wx.EVT_BUTTON, self.OnToolClick, self.justify_tb)
        self.AddControl(self.justify_tb)
    
    def _create_alignment_button(self):
        """Creates vertical alignment button"""
        
        iconnames = ["AlignTop", "AlignCenter", "AlignBottom"]
        bmplist = [wx.Bitmap(icons[iconname]) for iconname in iconnames]
        
        self.alignment_tb = _widgets.BitmapToggleButton(self, bmplist)
        self.Bind(wx.EVT_BUTTON, self.OnToolClick, self.alignment_tb)
        self.AddControl(self.alignment_tb)
    
    def _create_borderchoice_combo(self):
        """Create border choice combo box"""
        
        self.pen_width_combo = _widgets.BorderEditChoice(self, 
                                choices=[c[0] for c in border_toggles], \
                                style=wx.CB_READONLY, size=(50, -1))
        
        self.borderstate = border_toggles[0][0]
        
        self.AddControl(self.pen_width_combo)
        
        self.Bind(wx.EVT_COMBOBOX, self.OnBorderChoice, self.pen_width_combo)
        
        self.pen_width_combo.SetValue("AllBorders")
    
    def _create_penwidth_combo(self):
        """Create pen width combo box"""
        
        self.pen_width_combo = _widgets.PenWidthComboBox(self, 
                                choices=map(unicode, xrange(12)), \
                                style=wx.CB_READONLY, size=(50, -1))
        self.AddControl(self.pen_width_combo)
        self.Bind(wx.EVT_COMBOBOX, self.OnLineWidth, self.pen_width_combo)

    
    def _create_color_buttons(self):
        """Create color choice buttons"""
        
        button_size = (30, 30)
        button_style = wx.NO_BORDER
        
        self.linecolor_choice = \
            csel.ColourSelect(self, -1, unichr(0x2500), (0, 0, 0), 
                              size=button_size, style=button_style)
        self.bgcolor_choice = \
            csel.ColourSelect(self, -1, "", (255, 255, 255), 
                              size=button_size, style=button_style)
        self.textcolor_choice = \
            csel.ColourSelect(self, -1, "A", (0, 0, 0), 
                              size=button_size, style=button_style)
        
        self.AddControl(self.linecolor_choice)
        self.AddControl(self.bgcolor_choice)
        self.AddControl(self.textcolor_choice)
        
        self.linecolor_choice.Bind(csel.EVT_COLOURSELECT, self.OnLineColor)
        self.bgcolor_choice.Bind(csel.EVT_COLOURSELECT, self.OnBGColor)
        self.textcolor_choice.Bind(csel.EVT_COLOURSELECT, self.OnTextColor)
    
    def _create_textrotation_spinctrl(self):
        """Create text rotation spin control"""
        
        self.rotation_spinctrl = wx.SpinCtrl(self, -1, "", size=(50, -1))
        self.rotation_spinctrl.SetRange(-179, 180)
        self.rotation_spinctrl.SetValue(0)
        
        # For compatibility with toggle buttons
        self.rotation_spinctrl.GetToolState = lambda x: None
        
        self.AddControl(self.rotation_spinctrl)
        
        self.Bind(wx.EVT_SPINCTRL, self.OnToolClick, self.rotation_spinctrl)
    
    # Update widget state methods
    # ---------------------------
    
    def _update_textfont(self, textfont):
        """Updates text font widgets"""
        
        if textfont is None:
            textfont = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        
        font_face = textfont.FaceName
        font_size = textfont.PointSize
        font_weight = textfont.GetWeight()
        font_style = textfont.GetStyle()
        font_is_underlined = textfont.GetUnderlined()
        
        try:
            fontface_id = self.fonts.index(font_face)
        except ValueError:
            fontface_id = 0
        
        self.font_choice_combo.Select(fontface_id)
        
        self.font_size_combo.SetValue(str(font_size))
        
        if font_weight == wx.FONTWEIGHT_NORMAL:
            # Toggle up
            self.ToggleTool(wx.FONTWEIGHT_BOLD, 0)
        elif font_weight == wx.FONTWEIGHT_BOLD:
            # Toggle down
            self.ToggleTool(wx.FONTWEIGHT_BOLD, 1)
        else:
            print "Unknown fontweight"
        
        if font_style == wx.FONTSTYLE_NORMAL:
            # Toggle up
            self.ToggleTool(wx.FONTSTYLE_ITALIC, 0)
        elif font_style == wx.FONTSTYLE_ITALIC:
            # Toggle down
            self.ToggleTool(wx.FONTSTYLE_ITALIC, 1)
        else:
            print "Unknown fontstyle"
    
    def _update_bgbrush(self, bgbrush_data):
        """Updates background color"""
        
        try:
            brush_color = wx.Colour(255, 255, 255, 0)
            brush_color.SetRGB(bgbrush_data[0])
        except KeyError:
            brush_color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW)
        
        self.bgcolor_choice.SetColour(brush_color)
    
    def _update_borderpen(self, borderpen_data):
        """Updates background color"""
        
        try:
            borderpen_color = wx.Colour(255, 255, 255, 0)
            borderpen_color.SetRGB(borderpen_data[0])
            borderpen_width = borderpen_data[1]
        except KeyError:
            borderpen_color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW)
            borderpen_width = 0
        
        self.linecolor_choice.SetColour(borderpen_color)
        self.pen_width_combo.SetSelection(borderpen_width)
    
    def _update_frozencell(self):
        """Updates frozen cell button"""
        
        # Frozen cell information is not in the sgrid because the
        # stored results may not be pickleable.
        
        # Get selected cell's key
        
        key = self.grid.key
        
        # Compatibility: Create frozen_cells if missing
        
        if not hasattr(self.pysgrid.sgrid, "frozen_cells"):
            self.pysgrid.sgrid.frozen_cells = {}
        
        # Check if cell is frozen and adjust frozen cell button
            
        if key in self.pysgrid.sgrid.frozen_cells:
            # Toggle down
            self.ToggleTool(wx.FONTFLAG_MASK, 1)
        else:
            # Toggle up
            self.ToggleTool(wx.FONTFLAG_MASK, 0)
    
    def _update_underline(self, textattributes):
        """Updates underline cell button"""
        
        try:
            underline_tag = odftags["underline"]
            underline_mode = textattributes[underline_tag]
        except KeyError:
            underline_mode = "none"
        
        if underline_mode == "continuous":
            # Toggle down
            self.ToggleTool(wx.FONTFLAG_UNDERLINED, 1)
        else:
            # Toggle up
            self.ToggleTool(wx.FONTFLAG_UNDERLINED, 0)
    
    def _update_justification(self, textattributes):
        """Updates horizontal text justification button"""
        
        justification_tag = odftags["justification"]
        try:
            justification = textattributes[justification_tag]
        except:
            justification = "left"
        
        if justification == "left":
            self.justify_tb.state = 2
        elif justification == "center":
            self.justify_tb.state = 0
        elif justification == "right":
            self.justify_tb.state = 1
        else:
            self.justify_tb.state = 2
        
        self.justify_tb.toggle(None)
        self.justify_tb.Refresh()
    
    def _update_alignment(self, textattributes):
        """Updates vertical text alignment button"""
        
        vert_align_tag = odftags["verticalalign"]
        try:
            vertical_align = textattributes[vert_align_tag]
        except:
            vertical_align = "top"
        
        if vertical_align == "top":
            self.alignment_tb.state = 2
        elif vertical_align == "middle":
            self.alignment_tb.state = 0
        elif vertical_align == "bottom":
            self.alignment_tb.state = 1
        else:
            self.alignment_tb.state = 2
            ##print "Vertical align tag " + vertical_align + " unknown"
        self.alignment_tb.toggle(None)
        self.alignment_tb.Refresh()
    
    def _update_fontcolor(self, textattributes):
        """Updates text font color button"""
        
        try:
            fontcolortag = odftags["fontcolor"]
            textcolor = textattributes[fontcolortag]
        except KeyError:
            textcolor = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        self.textcolor_choice.SetColour(textcolor)
    
    def _update_strikethrough(self, textattributes):
        """Updates text strikethrough button"""
        
        try:
            strikethrough_tag = odftags["strikethrough"]
            strikethrough = textattributes[strikethrough_tag]
        except KeyError:
            strikethrough = "transparent"
        
        if strikethrough == "solid":
            self.ToggleTool(wx.FONTFLAG_STRIKETHROUGH, 1)
        else:
            self.ToggleTool(wx.FONTFLAG_STRIKETHROUGH, 0)
    
    def _update_textrotation(self, textattributes):
        """Updates text rotation spin control"""
        
        try:
            rot_angle_tag = odftags["rotationangle"]
            angle = float(textattributes[rot_angle_tag])
        except KeyError:
            angle = 0.0
        
        self.rotation_spinctrl.SetValue(angle)
    
    def update(self, borderpen_data=None, bgbrush_data=None, 
                     textattributes=None, textfont=None):
        """Updates all widgets
        
        Parameters
        ----------
        
        borderpen: wx.Pen (defaults to None)
        \tPen for cell borders
        bgbrush: wx.Brush (defaults to None), 
        \tBrush for cell background
        textattributes: Dict (defaults to None)
        \tAdditional text attributes
        textfont: wx.Font (defaults to None)
        \tText font
        
        """
        
        if textattributes is None:
            textattributes = {}
        
        self._update_textfont(textfont)
        self._update_bgbrush(bgbrush_data)
        self._update_borderpen(borderpen_data)
        
        self._update_frozencell()
        
        # Text attributes
        
        self._update_underline(textattributes)
        self._update_justification(textattributes)
        self._update_alignment(textattributes)
        self._update_fontcolor(textattributes)
        self._update_strikethrough(textattributes)
        self._update_textrotation(textattributes)

    # Attributes toolbar event handlers
    # ---------------------------------
    
    def _getkey(self):
        """Returns the key of the currentky selected cell"""
        
        row, col = self.grid.get_currentcell()
        tab = self.grid.current_table 
        
        return row, col, tab
    
    def _get_key_list(self):
        """Returns a key list of selected cells
        
        Returns the current cell if no selection.
        
        """
        
        selected_cells = self.grid.get_selection()
        if selected_cells:
            tab = self.grid.current_table
            return [(row, col, tab) for row, col in selected_cells]
        else:
            return [self._getkey()]
    
    def OnBorderChoice(self, event):
        """Change the borders that are affected by color and width changes"""
        
        choicelist = event.GetEventObject().GetItems()
        self.borderstate = choicelist[event.GetInt()]
    
    def get_chosen_borders(self, keys):
        """Returns 2-tuple of bottom and right borderlines to be changed
        
        {"borderpen_bottom": [keys], "borderpen_right":[keys]}
        
        where [keys] are lists of cell keys with border line adjustments
        
        """
        
        bottom_keys = []
        right_keys = []
        
        # top, bottom, left, right, inner, outer
        for borderstate, toggles in border_toggles:
            if self.borderstate == borderstate:
                btoggles = toggles
                break
        
        min_x = min(x for x, y, z in keys)
        max_x = max(x for x, y, z in keys)
        min_y = min(y for x, y, z in keys)
        max_y = max(y for x, y, z in keys)
        
        # Returns True if a right key is outer key
        is_inner_r = lambda key: min_x <= key[0] <= max_x and \
                                 min_y <= key[1] < max_y
        is_inner_b = lambda key: min_x <= key[0] < max_x and \
                                 min_y <= key[1] <= max_y
        
        for key in keys:
            if btoggles[0] and key[0] > 0:
                # Top border
                bottom_keys.append((key[0] - 1, key[1], key[2]))
            elif btoggles[0] and key[0] == 0:
                bottom_keys.append(("top", key[1], key[2]))
            if btoggles[1]:
                # Bottom border
                bottom_keys.append(key)
            if btoggles[2] and key[1] > 0:
                # Left border
                right_keys.append((key[0], key[1] - 1, key[2]))
            elif btoggles[2] and key[1] == 0:
                right_keys.append((key[0], "left", key[2]))
            if btoggles[3]:
                # Right border
                right_keys.append(key)
            if not btoggles[4]:
                # Inner borders
                right_keys = [key for key in right_keys if not is_inner_r(key)]
                bottom_keys= [key for key in bottom_keys if not is_inner_b(key)]
            if not btoggles[5]:
                # Outer borders
                right_keys = [key for key in right_keys if is_inner_r(key)]
                bottom_keys = [key for key in bottom_keys if is_inner_b(key)]
        
        return (bottom_keys, right_keys)
    
    def OnLineColor(self, event):
        """Change the line color of current cell/selection border"""
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        self.grid.backgrounds = {}
        
        keys = self._get_key_list()
        
        color = event.GetValue()
        
        bottom_keys, right_keys = self.get_chosen_borders(keys)
        
        for key in bottom_keys:
            pysgrid.create_sgrid_attribute(key, "borderpen_bottom")
            if key not in sgrid:
                sgrid[key] = None
            try:
                sgrid[key].borderpen_bottom[0] = color.GetRGB()
            except KeyError:
                sgrid[key].borderpen_bottom = \
                    default_cell_attributes["borderpen_bottom"]
                sgrid[key].borderpen_bottom[0] = color.GetRGB()
        
        for key in right_keys:
            pysgrid.create_sgrid_attribute(key, "borderpen_right")
            if key not in sgrid:
                sgrid[key] = None
            try:
                sgrid[key].borderpen_right[0] = color.GetRGB()
            except KeyError:
                sgrid[key].borderpen_right = \
                    default_cell_attributes["borderpen_right"]
                sgrid[key].borderpen_right[0] = color.GetRGB()
        
        self.grid.ForceRefresh()
        
        event.Skip()
    
    def OnLineWidth(self, event):
        """Change the line width of current cell/selection border"""
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        self.grid.backgrounds = {}
        
        keys = self._get_key_list()
        bottom_keys, right_keys = self.get_chosen_borders(keys)
        
        linewidth_combobox = event.GetEventObject()
        idx = event.GetInt()
        line_width  = int(linewidth_combobox.GetString(idx))
        if line_width == 0:
            penstyle = wx.TRANSPARENT
        else:
            penstyle = wx.SOLID
        
        for key in right_keys:
            pysgrid.create_sgrid_attribute(key, "borderpen_right")
            if key not in sgrid:
                sgrid[key] = None
            try:
                sgrid[key].borderpen_right[1] = line_width
                sgrid[key].borderpen_right[2] = int(penstyle)
            except KeyError:
                sgrid[key].borderpen_right = \
                    default_cell_attributes["borderpen_right"]
                sgrid[key].borderpen_right[1] = line_width
                sgrid[key].borderpen_right[2] = int(penstyle)

        
        for key in bottom_keys:
            pysgrid.create_sgrid_attribute(key, "borderpen_bottom")
            if key not in sgrid:
                sgrid[key] = None
            try:
                sgrid[key].borderpen_bottom[1] = line_width
                sgrid[key].borderpen_bottom[2] = int(penstyle)
            except KeyError:
                sgrid[key].borderpen_bottom = \
                    default_cell_attributes["borderpen_bottom"]
                sgrid[key].borderpen_bottom[1] = line_width
                sgrid[key].borderpen_bottom[2] = int(penstyle)
        
        self.grid.ForceRefresh()
        
    def OnBGColor(self, event):
        """Change the color of current cell/selection background"""
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        self.grid.backgrounds = {}
        
        keys = self._get_key_list()
        
        bgcolor = event.GetValue()
        
        for key in keys:
            pysgrid.create_sgrid_attribute(key, "bgbrush")
            try:
                sgrid[key].bgbrush[0] = int(bgcolor.GetRGB())
            except KeyError:
                try:
                    sgrid[key].bgbrush = default_cell_attributes["bgbrush"]
                except KeyError:
                    sgrid[key] = None
                    sgrid[key].bgbrush = default_cell_attributes["bgbrush"]
                    
                sgrid[key].bgbrush[0] = int(bgcolor.GetRGB())
        
        self.grid.ForceRefresh()
        
        event.Skip()
        
    def OnTextColor(self, event):
        """Change the color of current cell/selection text"""
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        keys = self._get_key_list()
        new_textcolor = event.GetValue()
        
        for key in keys:
            pysgrid.create_sgrid_attribute(key, "textattributes")
            
            if key not in sgrid:
                sgrid[key] = None
                
            sgrid[key].textattributes[odftags["fontcolor"]] = new_textcolor
        
        self.grid.ForceRefresh()
        
        event.Skip()
    
    def OnTextFont(self, event):
        """Change the font of current cell/selection text"""
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        keys = self._get_key_list()
        
        fontchoice_combobox = event.GetEventObject()
        idx = event.GetInt()
        
        try:
            font_string  = fontchoice_combobox.GetString(idx)
        except AttributeError:
            font_string  = event.GetString()
        
        for key in keys:
            pysgrid.create_sgrid_attribute(key, "textfont")
            try:
                old_font_string = sgrid[key].textfont
            except KeyError:
                old_font_string = default_cell_attributes["textfont"]
            
            nativefontinfo = wx.NativeFontInfo()
            nativefontinfo.FromString(old_font_string)
            
            textfont = wx.Font(10, wx.NORMAL, wx.NORMAL, 
                               wx.NORMAL, False, 'Arial')
            textfont.SetNativeFontInfo(nativefontinfo)
            textfont.SetFaceName(font_string)
            
            if key not in sgrid:
                sgrid[key] = None
            
            sgrid[key].textfont = str(textfont.GetNativeFontInfo())
          
        self.grid.ForceRefresh()
        
        event.Skip()
    
    def OnTextSize(self, event):
        """Text size combo text event handler"""
        
        try:
            size = int(event.GetString())
        except Exception:
            size = faces['size']
        
        self.change_text_size(size)
        
        event.Skip()
        
    def change_text_size(self, size):
        """Change the size of current cell/selection text"""
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        keys = self._get_key_list()
        
        for key in keys:
            pysgrid.create_sgrid_attribute(key, "textfont")
            try:
                old_font_string = sgrid[key].textfont
            except KeyError:
                old_font_string = default_cell_attributes["textfont"]
            
            textfont = wx.Font(10, wx.NORMAL, wx.NORMAL, 
                               wx.NORMAL, False, 'Arial')
            nativefontinfo = wx.NativeFontInfo()
            nativefontinfo.FromString(sgrid[key].textfont)

            textfont.SetNativeFontInfo(nativefontinfo)
            textfont.SetPointSize(size)
            
            if key not in sgrid:
                sgrid[key] = None
                
            sgrid[key].textfont = str(textfont.GetNativeFontInfo())
        
        self.grid.ForceRefresh()
    
    def OnToolClick(self, event):
        """Toggle the tool attribute of the current cell/selection text
        
        This event handler method covers both fornt related buttons and
        text attribute buttons.
        
        """
        
        pysgrid = self.pysgrid
        sgrid = pysgrid.sgrid
        
        keys = self._get_key_list()
        
        # Font buttons
        
        for key in keys:
        
            if key not in sgrid:
                sgrid[key] = None
                
            pysgrid.create_sgrid_attribute(key, "textfont")
            
            try:
                old_font_string = sgrid[key].textfont
            except KeyError:
                old_font_string = default_cell_attributes["textfont"]

            nativefontinfo = wx.NativeFontInfo()
            nativefontinfo.FromString(old_font_string)

            font = wx.Font(10, wx.NORMAL, wx.NORMAL, 
                           wx.NORMAL, False, 'Arial')
            
            font.SetNativeFontInfo(nativefontinfo)
            font.SetPointSize(faces['size'])

            istoggled = event.GetEventObject().GetToolState(event.GetId())

            if event.GetId() == wx.FONTWEIGHT_BOLD and istoggled:
                font.SetWeight(wx.FONTWEIGHT_BOLD)
            elif event.GetId() == wx.FONTWEIGHT_BOLD and not istoggled:
                font.SetWeight(wx.FONTWEIGHT_NORMAL)

            if event.GetId() == wx.FONTSTYLE_ITALIC and istoggled:
                font.SetStyle(wx.FONTSTYLE_ITALIC)
            elif event.GetId() == wx.FONTSTYLE_ITALIC and not istoggled:
                font.SetStyle(wx.FONTSTYLE_NORMAL)
                
            sgrid[key].textfont = str(font.GetNativeFontInfo())

            # Text attribute buttons

            pysgrid.create_sgrid_attribute(key, "textattributes")

            textattr = sgrid[key].textattributes

            if event.GetId() == wx.FONTFLAG_STRIKETHROUGH and istoggled:
                textattr[odftags["strikethrough"]] = "solid"
            elif event.GetId() == wx.FONTFLAG_STRIKETHROUGH and not istoggled:
                textattr[odftags["strikethrough"]] = "transparent"

            if event.GetId() == wx.FONTFLAG_UNDERLINED and istoggled:
                textattr[odftags["underline"]] = "continuous"
            elif event.GetId() == wx.FONTFLAG_UNDERLINED and not istoggled:
                textattr[odftags["underline"]] = "none"
            
            tb_state_map = {0: "left",
                            1: "center",
                            2: "right",
                            }
            if event.GetEventObject() == self.justify_tb:
                justification = tb_state_map[self.justify_tb.state]
                textattr[odftags["justification"]] = justification
            
            tb_state_map = {0: "top",
                            1: "middle",
                            2: "bottom",
                            }
            if event.GetEventObject() == self.alignment_tb:
                vert_align = tb_state_map[self.alignment_tb.state]
                textattr[odftags["verticalalign"]] = vert_align

            # Freeze goes directly into pysgrid
            # eval is done at this time!
            
            if event.GetId() == wx.wx.FONTFLAG_MASK and istoggled:
                res = self.pysgrid[key]
                self.pysgrid.sgrid.frozen_cells[key] = res
            elif event.GetId() == wx.wx.FONTFLAG_MASK and not istoggled:
                try:
                    self.pysgrid.sgrid.frozen_cells.pop(key)
                except KeyError:
                    pass

            if event.GetEventObject() == self.rotation_spinctrl:
                angle = self.rotation_spinctrl.GetValue()
                textattr[odftags["rotationangle"]] = int(angle)

        self.grid.ForceRefresh()
        
        event.Skip()

# end of class AttributesToolbar
