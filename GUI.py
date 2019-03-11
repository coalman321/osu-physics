import wx


class ControlInterface(wx.Frame):

    def __init__(self, instr: list, *args, **kwargs):
        super(ControlInterface, self).__init__(*args, **kwargs)
        self.instrument_list = instr
        self.panel = wx.Panel(self, size=(1920, 1080))
        header = wx.StaticText(self.panel, label="R vs. T Measurement Interface", pos=(0,0))
        font = header.GetFont()
        font.PointSize += 10
        header.SetFont(font)
        self.make_menu()
        self.make_instrument_panel()

    def make_instrument_panel(self):
        header = wx.StaticText(self.panel, label="GPIB Device ID selection", pos=(0, 40))
        self.temp_ID_selector = wx.ComboBox(self.panel, -1, "Select INSTR ID", choices=self.instrument_list, size=(200, 30), pos=(0, 60), style=wx.CB_READONLY)
        self.volt_ID_selector = wx.ComboBox(self.panel, -1, "Select INSTR ID", choices=self.instrument_list, size=(200, 30), pos=(0, 100), style=wx.CB_READONLY)
        self.curr_ID_selector = wx.ComboBox(self.panel, -1, "Select INSTR ID", choices=self.instrument_list, size=(200, 30), pos=(0, 140), style=wx.CB_READONLY)

    def make_menu(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
                "Help string shown in status bar for this menu item")
        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        # self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a wxPython Hello World sample",
                      "About Hello World 2", wx.OK | wx.ICON_INFORMATION)

