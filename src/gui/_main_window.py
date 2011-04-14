#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
_main_window
============

Provides:
---------
  1) MainWindow: Main window of the application pyspread

"""

import wx
import wx.aui

import wx.lib.agw.genericmessagedialog as GMD

from config import MAIN_WINDOW_ICON, MAIN_WINDOW_SIZE, DEFAULT_DIM
from config import file_approval_warning

from _menubars import MainMenu
from _toolbars import MainToolbar, FindToolbar, AttributesToolbar
from _widgets import EntryLine, StatusBar, TableChoiceIntCtrl
from lib._interfaces import PysInterface
from _gui_interfaces import GuiInterfaces

from _grid import Grid
from _events import *

from model._data_array import DataArray

from actions._main_window_actions import AllMainWindowActions

class MainWindow(wx.Frame):
    """Main window of pyspread"""
    
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        
        self.interfaces = GuiInterfaces(self)
        
        self._mgr = wx.aui.AuiManager(self)
    
        self.parent = parent
        
        self.handlers = MainWindowEventHandlers(self)
        
        # Program states
        # --------------
        
        self._states()
        
        # Has the current file been changed since the last save?
        self.changed_since_save = False
        self.filepath = None
        
        # GUI elements
        # ------------
        
        # Menu Bar
        menubar = wx.MenuBar()
        self.main_menu = MainMenu(parent=self, menubar=menubar)
        self.SetMenuBar(menubar)
        
        # Disable menu item for leaving save mode
        post_command_event(self, SaveModeExitMsg)
        
        # Status bar
        statusbar = StatusBar(self)
        self.SetStatusBar(statusbar)
        
        welcome_text = "Welcome to pyspread."
        post_command_event(self, StatusBarMsg, text=welcome_text)
        
        # Toolbars
        self.main_toolbar = MainToolbar(self, -1)
        self.find_toolbar = FindToolbar(self, -1)
        self.attributes_toolbar = AttributesToolbar(self, -1)
        
        # Entry line
        self.entry_line = EntryLine(self)
        
        # Main grid
        
        self.grid = Grid(self, -1, dimensions=DEFAULT_DIM)

        # IntCtrl for table choice
        self.table_choice = TableChoiceIntCtrl(self, DEFAULT_DIM[2])

        # Main window actions
        
        self.actions = AllMainWindowActions(self, self.grid)
        
        # Layout and bindings
        
        self._set_properties()
        self._do_layout()
        self._bind()
    
        
    def _states(self):
        """Sets main window states"""
        # Print data
        
        self.print_data = wx.PrintData()
        # wx.PrintData properties setup from 
        # http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3471083
    
    def _set_properties(self):
        """Setup title, icon, size, scale, statusbar, main grid"""
        
        self.set_icon(MAIN_WINDOW_ICON)
        
        # Set initial size to 90% of screen
        
        self.SetInitialSize(MAIN_WINDOW_SIZE)
        
        # Without minimum size, initial size is minimum size in wxGTK
        self.SetMinSize((2, 2))
        
        # Leave save mode
        post_command_event(self, SaveModeExitMsg)
        
    def _do_layout(self):
        """Adds widgets to the wx.aui manager and controls the layout"""
        
        # Add the toolbars to the manager
        self._mgr.AddPane(self.main_toolbar, wx.aui.AuiPaneInfo().
                          Name("main_window_toolbar").Caption("Main Toolbar").
                          ToolbarPane().Top().Row(0).CloseButton(False).
                          LeftDockable(False).RightDockable(False))
                                  
        self._mgr.AddPane(self.find_toolbar, wx.aui.AuiPaneInfo().
                          Name("find_toolbar").Caption("Find").
                          ToolbarPane().Top().Row(1).MaximizeButton(False).
                          LeftDockable(False).RightDockable(False))
        
        self._mgr.AddPane(self.attributes_toolbar, wx.aui.AuiPaneInfo().
                          Name("attributes_toolbar").Caption("Cell Attributes").
                          ToolbarPane().Top().Row(1).MaximizeButton(False).
                          LeftDockable(False).RightDockable(False))
                          
                          
        self._mgr.AddPane(self.table_choice, wx.aui.AuiPaneInfo().
                          Name("table_choice").Caption("Table choice").
                          ToolbarPane().MaxSize((50, 50)).Row(2).
                          Top().CloseButton(False).MaximizeButton(False).
                          LeftDockable(True).RightDockable(True))
        
        self._mgr.AddPane(self.entry_line, wx.aui.AuiPaneInfo().
                          Name("entry_line").Caption("Entry line").
                          ToolbarPane().MinSize((10, 10)).Row(2).
                          Top().CloseButton(False).MaximizeButton(False).
                          LeftDockable(True).RightDockable(True))
        
        # Add the main grid
        self._mgr.AddPane(self.grid, wx.CENTER)
        
        # Tell the manager to 'commit' all the changes just made
        self._mgr.Update()
    
    def _bind(self):
        """Bind events to handlers"""
        
        handlers = self.handlers
        
        # Program state events
        
        self.Bind(EVT_COMMAND_TITLE, handlers.OnTitle)
        self.Bind(EVT_COMMAND_SAFE_MODE_ENTRY, handlers.OnSaveModeEntry)
        self.Bind(EVT_COMMAND_SAFE_MODE_EXIT, handlers.OnSaveModeExit)
        self.Bind(wx.EVT_CLOSE, handlers.OnClose)
        self.Bind(EVT_COMMAND_CLOSE, handlers.OnClose)
        
        # File events
        
        self.Bind(EVT_COMMAND_NEW, handlers.OnNew)
        self.Bind(EVT_COMMAND_OPEN, handlers.OnOpen)
        self.Bind(EVT_COMMAND_SAVE, handlers.OnSave)
        self.Bind(EVT_COMMAND_SAVEAS, handlers.OnSaveAs)
        self.Bind(EVT_COMMAND_IMPORT, handlers.OnImport)
        self.Bind(EVT_COMMAND_EXPORT, handlers.OnExport)
        self.Bind(EVT_COMMAND_APPROVE, handlers.OnApprove)
        
        # Print events
        
        self.Bind(EVT_COMMAND_PAGE_SETUP, handlers.OnPageSetup)
        self.Bind(EVT_COMMAND_PRINT_PREVIEW, handlers.OnPrintPreview)
        self.Bind(EVT_COMMAND_PRINT, handlers.OnPrint)
        
        # Clipboard events
        
        self.Bind(EVT_COMMAND_CUT, handlers.OnCut)
        self.Bind(EVT_COMMAND_COPY, handlers.OnCopy)
        self.Bind(EVT_COMMAND_COPY_RESULT, handlers.OnCopyResult)
        self.Bind(EVT_COMMAND_PASTE, handlers.OnPaste)
        
        # Help events
        
        self.Bind(EVT_COMMAND_MANUAL, handlers.OnManual)
        self.Bind(EVT_COMMAND_TUTORIAL, handlers.OnTutorial)
        self.Bind(EVT_COMMAND_FAQ, handlers.OnFaq)
        self.Bind(EVT_COMMAND_ABOUT, handlers.OnAbout)
        
        self.Bind(EVT_COMMAND_MACROLIST, handlers.OnMacroList)
        self.Bind(EVT_COMMAND_MACROLOAD, handlers.OnMacroListLoad)
        self.Bind(EVT_COMMAND_MACROSAVE, handlers.OnMacroListSave)
    
    def set_icon(self, bmp):
        """Sets main window icon to given wx.Bitmap"""
        
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(bmp)
        self.SetIcon(_icon)

    def get_safe_mode(self):
        """Returns safe_mode state from data_array"""
        
        return self.grid.data_array.safe_mode

    safe_mode = property(get_safe_mode)

# End of class MainWindow

class MainWindowEventHandlers(object):
    """Contains main window event handlers"""
    
    def __init__(self, parent):
        self.main_window = parent
        self.interfaces = parent.interfaces
    
    # Main window events
    
    def OnTitle(self, event):
        """Title change event handler"""
        
        self.main_window.SetTitle(event.text)
    
    def OnSaveModeEntry(self, event):
        """Save mode entry event handler"""
        
        # Enable menu item for leaving save mode
        
        self.main_window.main_menu.enable_file_approve(True)
        
        self.main_window.grid.ForceRefresh()
    
    def OnSaveModeExit(self, event):
        """Save mode exit event handler"""
        
        # Run macros
        
        ##self.MainGrid.model.pysgrid.sgrid.execute_macros(safe_mode=False)
        
        # Disable menu item for leaving save mode
        
        self.main_window.main_menu.enable_file_approve(False)
        
        self.main_window.grid.ForceRefresh()
    
    def OnClose(self, event):
        """Program exit event handler"""
        
        # Ask if the user really wants to close pyspread
        
        msg = "Do you want to close pyspread?"
        short_msg = "Close pyspread"
        style = wx.OK | wx.CANCEL | wx.NO_DEFAULT | wx.ICON_QUESTION
        
        if self.main_window.interfaces\
                .get_warning_choice(msg, short_msg, style) == wx.ID_CANCEL:
            return 
        
        # If changes have taken place save of old grid
        
        if self.main_window.changed_since_save:
            if self.interfaces.get_save_request_from_user():
                post_command_event(self.main_window, SaveMsg)
        
        # Uninit the AUI stuff
        
        self.main_window._mgr.UnInit()
        
        # Close main_window
        
        self.main_window.Destroy()
    
   
    # File events
    
    def OnNew(self, event):
        """New grid event handler"""
        
        # If changes have taken place save of old grid
        
        if self.main_window.changed_since_save:
            if self.interfaces.get_save_request_from_user():
                post_command_event(self.main_window, SaveMsg)
        
        # Get grid dimensions
        
        dim = self.interfaces.get_dimensions_from_user(no_dim=3)
        
        if dim is None:
            return
        
        data_array = DataArray(dim)
        
        # Set new filepath and post it to the title bar
        
        self.main_window.filepath = None
        post_command_event(self.main_window, TitleMsg, text="pyspread")
        
        # Create new grid
        post_command_event(self.main_window, GridActionNewMsg, 
                           data_array=data_array)
        
        # Update TableChoiceIntCtrl
        post_command_event(self.main_window, ResizeGridMsg, 
                           dim=dim)
        
        # Display grid creation in status bar
        
        statustext = "New grid with dimensions " + str(dim) + " created."
        post_command_event(self.main_window, StatusBarMsg, text=statustext)

    def OnOpen(self, event):
        """File open event handler"""
        
        # If changes have taken place save of old grid
        
        if self.main_window.changed_since_save:
            if self.interfaces.get_save_request_from_user():
                post_command_event(self.main_window, SaveMsg)
        
        # Get filepath from user
        
        wildcard = "Pyspread file (*.pys)|*.pys|" \
                   "All files (*.*)|*.*"
        message = "Choose pyspread file to open."
        style = wx.OPEN | wx.CHANGE_DIR
        filepath, filterindex = self.interfaces.get_filepath_findex_from_user( \
                                    wildcard, message, style)
        
        if filepath is None:
            return
        
        # Change the main window filepath state
        
        self.main_window.filepath = filepath
            
        # Load file into grid
        
        post_command_event(self.main_window, GridActionOpenMsg, 
            attr={"filepath": filepath, "interface": PysInterface})
        
        # Set Window title to new filepath
        
        title_text = "pyspread - " + filepath.split("/")[-1]
        post_command_event(self.main_window, TitleMsg, text=title_text)
        
        # Display file load in status bar
        
        statustext = "File " + filepath + " loaded."
        post_command_event(self.main_window, StatusBarMsg, text=statustext)
    
    def OnSave(self, event):
        """File save event handler"""
        
        # If there is no filepath then jump to save as
        
        if self.main_window.filepath is None:
            post_command_event(self.main_window, SaveAsMsg)
            return
        
        # Save the grid
        
        post_command_event(self.main_window, GridActionSaveMsg, attr={ \
            "filepath": self.main_window.filepath, "interface": PysInterface})
        
        # Display file save in status bar
        
        statustext = self.main_window.filepath.split("/")[-1] + " saved."
        post_command_event(self.main_window, StatusBarMsg, text=statustext)
    
    def OnSaveAs(self, event):
        """File save as event handler"""
        
        # Get filepath from user
        
        wildcard = "Pyspread file (*.pys)|*.pys|" \
                   "All files (*.*)|*.*"
        message = "Choose filename for saving."
        style = wx.SAVE | wx.CHANGE_DIR
        filepath, filterindex = self.interfaces.get_filepath_findex_from_user( \
                                    wildcard, message, style)
        
        if filepath is not None:
            
            # Put pys suffix if wildcard choice is 0
            
            if filterindex == 0 and filepath[-4:] != ".pys":
                filepath += ".pys"
            
            # Set the filepath state
            
            self.main_window.filepath = filepath
            
            # Set Window title to new filepath
        
            title_text = "pyspread - " + filepath.split("/")[-1]
            post_command_event(self.main_window, TitleMsg, text=title_text)
            
            # Now jump to save
            
            post_command_event(self.main_window, SaveMsg)
                
    def OnImport(self, event):
        """File import event handler"""
        
        # Get filepath from user
        
        wildcard = wildcard=" CSV file|*.*|Tab-delimited text file|*.*"
        message = "Choose file to import."
        style = wx.OPEN | wx.CHANGE_DIR
        path, filterindex = self.interfaces.get_filepath_findex_from_user( \
                                    wildcard, message, style)
        
        if path is None:
            return
        
        # Get generator of import data
        import_data = self.main_window.actions.import_file(path, filterindex)
        
        if import_data is None:
            return
        
        # Paste import data to grid
        grid = self.main_window.grid
        tl_cell = grid.GetGridCursorRow(), grid.GetGridCursorCol()
        
        grid.actions.paste(tl_cell, import_data)
        
    def OnExport(self, event):
        """File export event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    def OnApprove(self, event):
        """File approve event handler"""
        
        if not self.main_window.safe_mode:
            return
        
        msg = file_approval_warning
        short_msg = "Security warning"
        
        if self.main_window.interfaces.get_warning_choice(msg, short_msg) == \
                wx.ID_YES:
            # Leave safe mode
            self.main_window.grid.actions.leave_save_mode()
            
            # Display safe mode end in status bar
        
            statustext = "Safe mode deactivated."
            post_command_event(self.main_window, StatusBarMsg, text=statustext)
    
    # Print events
    
    def OnPageSetup(self, event):
        """Page setup handler for printing framework"""
        
        print_data = self.main_window.print_data
        new_print_data = self.main_window.interfaces.get_print_setup(print_data)
        self.main_window.print_data = new_print_data

    
    def _get_print_area(self):
        """Returns selection bounding box or visible area"""
        
        # Get print area from current selection
        selection = self.main_window.grid.selection
        print_area = selection.get_bbox()
        
        # If there is no selection use the visible area on the screen
        if print_area is None:
            print_area = self.main_window.grid.actions.get_visible_area()
        
        return print_area
    
    def OnPrintPreview(self, event):
        """Print preview handler"""
        
        print_area = self._get_print_area()
        print_data = self.main_window.print_data
        
        self.main_window.actions.print_preview(print_area, print_data)
    
    def OnPrint(self, event):
        """Print event handler"""
        
        print_area = self._get_print_area()
        print_data = self.main_window.print_data
        
        self.main_window.actions.printout(print_area, print_data)
    
    # Clipboard events

    def OnCut(self, event): 
        """Clipboard cut event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    def OnCopy(self, event):
        """Clipboard copy event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    def OnCopyResult(self, event):
        """Clipboard copy results event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    def OnPaste(self, event):
        """Clipboard paste event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    # Help events
    
    def OnManual(self, event):
        """Manual launch event handler"""
        
        self.main_window.actions.launch_help("Pyspread manual", "manual.html")
    
    def OnTutorial(self, event):
        """Tutorial launch event handler"""
        
        self.main_window.actions.launch_help("Pyspread tutorial", 
                                             "tutorial.html")
        
    def OnFaq(self, event):
        """FAQ launch event handler"""
        
        self.main_window.actions.launch_help("Pyspread tutorial", "faq.html")
    
    def OnAbout(self, event):
        """About dialog event handler"""
        
        self.main_window.interfaces.display_about(self.main_window)
    
    # Macro events
    
    def OnMacroList(self, event):
        """Macro list dialog event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    def OnMacroListLoad(self, event): 
        """Macro list load event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
    def OnMacroListSave(self, event):
        """Macro list save event handler"""
        
        raise NotImplementedError
        
        event.Skip()
    
# End of class MainWindowEventHandlerMixin
