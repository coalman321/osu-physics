import wx
import visa
import time
from vsm_temp_controller import VsmTempController
from k2400_isource import K2400
from k2182A_nvmeter import K2182A
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import wx.lib.agw.aui as aui

# DO NOT MODIFY ON THIS COMPUTER
library = 'C:\\Windows\\System32\\visa64.dll'
k_epsilon = 1.0E0  # value used for an approximately equals statement

def sweep(start, end, step):
    arr = []
    current = start
    for x in range(int((end-start)/step)):
        arr.append(current)
        current += step
    arr.append(end)
    return arr

# Sample name
sname = "XD326"
# File to output data to
fname = "C:/temp/work/{}RANDOM_RESISTOR.csv".format(sname)
# Currents in uA
currents = [3, -3] # 30, -30
# time between voltage readings in s
reading_delay = 1.0
# Temperatures in K
temps = sweep(80, 300, 20)
# wait for stability in s
temp_stable_wait = 2 * 60
# End Temperature in K
# end_temp = 300

class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1300, 600))

        self.res_manager = visa.ResourceManager(library)
        self.instrument_list = self.res_manager.list_resources()

        self.allow_measurement = False

        self.menu_bar = wx.MenuBar()
        self.page_menu = wx.Menu()
        self.page_menu.Append(wx.NewId(), "Main Menu", "Main configuration menu", wx.ITEM_RADIO)
        self.page_menu.Append(wx.NewId(), "Live Graph", "Live updated graph", wx.ITEM_RADIO)
        self.menu_bar.Append(self.page_menu, "&Menu")
        self.SetMenuBar(self.menu_bar)

        # setup measurement panel & log
        self.mainpanel = wx.Panel(self)
        self.mainpanel.Show(True)

        self.header = wx.StaticText(self.mainpanel, label="R vs. T Measurement Interface", pos=(0, 0))
        font = self.header.GetFont()
        font.PointSize += 10
        self.header.SetFont(font)

        wx.StaticText(self.mainpanel, label="Temperature Controller GPIB Address", pos=(0, 40))
        self.temp_ID_selector = wx.ComboBox(self.mainpanel, choices=self.instrument_list,
                                       size=(200, 30), pos=(0, 60), style=wx.CB_READONLY)
        wx.StaticText(self.mainpanel, label="Nanovoltmeter GPIB Address", pos=(0, 90))
        self.volt_ID_selector = wx.ComboBox(self.mainpanel, choices=self.instrument_list,
                                       size=(200, 30), pos=(0, 110), style=wx.CB_READONLY)
        wx.StaticText(self.mainpanel, label="Current Source GPIB Address", pos=(0, 140))
        self.curr_ID_selector = wx.ComboBox(self.mainpanel, choices=self.instrument_list,
                                       size=(200, 30), pos=(0, 160), style=wx.CB_READONLY)

        self.step_readout = wx.TextCtrl(self.mainpanel, size=(200, 30), pos=(0, 280), style=wx.TE_READONLY, value="Step {} of {}".format(0, 0))
        self.temp_readout = wx.TextCtrl(self.mainpanel, size=(200, 30), pos=(0, 320), style=wx.TE_READONLY, value="current temp {}K   Desired {}K".format(293, 293))
        self.heater_readout = wx.TextCtrl(self.mainpanel, size=(200, 30), pos=(0, 360), style=wx.TE_READONLY, value="Heater Power: {:3.2f}%".format(0))

        self.connect_button = wx.Button(self.mainpanel, -1, "Test Connections", pos=(50, 190), size=(100, 30))
        self.connect_button.Bind(wx.EVT_BUTTON, self.test_intruments)
        self.start_button = wx.Button(self.mainpanel, -1, "Start Measurement", pos=(40, 230), size=(120, 30))
        self.start_button.Bind(wx.EVT_BUTTON, self.run_measurement)

        self.console = wx.TextCtrl(self.mainpanel, size=(500, 400), pos=(250, 50), style=wx.TE_READONLY|wx.TE_MULTILINE)

        # self.graphpanel = wx.Panel(self)
        # self.graphpanel.Hide()


    def test_intruments(self, aaa):
        if not self.temp_ID_selector.GetCurrentSelection() == -1:
            temp = self.res_manager.open_resource(self.instrument_list[self.temp_ID_selector.GetCurrentSelection()])
            self.append_log("Temperature controller ID: " + temp.query("*IDN?"))
            temp.close()
        else:
            self.append_log("Temperature controller not selected")
        if not self.volt_ID_selector.GetCurrentSelection() == -1:
            volt = self.res_manager.open_resource(self.instrument_list[self.volt_ID_selector.GetCurrentSelection()])
            self.append_log("Nanovoltmeter ID: " + volt.query("*IDN?"))
            volt.close()
        else:
            self.append_log("Nano-voltmeter not selected")
        if not self.volt_ID_selector.GetCurrentSelection() == -1:
            curr = self.res_manager.open_resource(self.instrument_list[self.curr_ID_selector.GetCurrentSelection()])
            self.append_log("Current Source ID: " + curr.query("*IDN?"))
            curr.close()
        else:
            self.append_log("Current source not selected")

    def run_measurement(self, aaa):
        instr_select = True
        if self.temp_ID_selector.GetCurrentSelection() == -1:
            self.append_log("Temperature controller not selected")
            instr_select = False
        if self.volt_ID_selector.GetCurrentSelection() == -1:
            self.append_log("Nano-voltmeter not selected")
            instr_select = False
        if self.volt_ID_selector.GetCurrentSelection() == -1:
            self.append_log("Current source not selected")
            instr_select = False
        if not instr_select:
            return
        self.clear_log()
        self.allow_measurement = True
        self.start_button.SetLabel("Stop Measurement")
        self.start_button.Bind(wx.EVT_BUTTON, self.stop_measurement)

    def append_log(self, to_log: str):
        self.console.AppendText(to_log + "\n")

    def clear_log(self):
        self.console.SetValue("")

    def stop_measurement(self, aaa):
        self.allow_measurement = False
        self.start_button.SetLabel("Start Measurement")
        self.start_button.Bind(wx.EVT_BUTTON, self.run_measurement)

    def OnCloseWindow(self, event):
        self.Destroy()

    def OnIdle(self, event):
        self.idleCtrl.SetValue(str(self.count))
        self.count = self.count + 1

    def OnSize(self, event):
        size = event.GetSize()
        self.sizeCtrl.SetValue("%s, %s" % (size.width, size.height))
        event.Skip()

    def OnMove(self, event):
        pos = event.GetPosition()
        self.posCtrl.SetValue("%s, %s" % (pos.x, pos.y))


class MainEventLoop(wx.GUIEventLoop):
    def __init__(self, frame):
        wx.GUIEventLoop.__init__(self)
        self.frame = frame
        self.exitCode = 0
        self.shouldExit = False
        self.blocked = False
        self.historic = False
        self.init_ready = False
        self.state = -1
        self.t_arrived = float("inf")
        self.temp_index = 0

        # Adjust currents from uA to A
        currents[:] = [x / 1000000 for x in currents]

    def update_experiment(self):
        if self.frame.allow_measurement:
            if self.state is 0:
                self.frame.append_log("setting temperature to {}K".format(self.target_temp))
                # self.temperature_controller.set_controller_enable(True)
                # self.temperature_controller.temp_sel_set(self.target_temp)
                # TODO SET BACK TO STATE 1 AFTER TEMP SET
                self.state = 2
            elif self.state is 1:
                # ramping to a temperature
                temp = self.temperature_controller.read_temp()
                self.frame.temp_readout.SetValue("current temp {:3.3f}K   Desired {}K".format(temp, self.target_temp))
                htr_power = self.temperature_controller.query_heater_power()
                self.frame.heater_readout.SetValue("Heater Power: {:3.2f}%".format(htr_power))
                self.frame.step_readout.SetValue("Step {} of {}".format(self.temp_index+1, len(temps)))
                if not (temp < self.target_temp - k_epsilon or temp > self.target_temp + k_epsilon) and not self.blocked:
                    self.t_arrived = time.time()
                    self.blocked = True
                if self.blocked and self.t_arrived + temp_stable_wait < time.time():
                    # ready to advance state into measurement
                    self.state = 2

            elif self.state is 2:
                # update statuses
                self.frame.append_log("executing measurement {}".format(self.temp_index+1))
                temp = self.temperature_controller.read_temp()
                self.frame.temp_readout.SetValue("current temp {:3.3f}K   Desired {}K".format(temp, self.target_temp))
                htr_power = self.temperature_controller.query_heater_power()
                self.frame.heater_readout.SetValue("Heater Power: {:3.2f}%".format(htr_power))
                self.frame.step_readout.SetValue("Step {} of {}".format(self.temp_index+1, len(temps)))

                # execute measurement
                # TODO find way to not block thread on reads
                temperature = 0
                resistance = 0
                voltage = []
                for current in currents:
                    self.i_source.enable_at_current(True, current)
                    time.sleep(reading_delay)
                    temperature += self.temperature_controller.read_temp()
                    voltage.append(self.nanovoltmeter.get_last_measurement())
                    resistance += voltage[-1] / current
                self.i_source.enable(False)

                # Calculate resistance and voltage average
                temp_avg = temperature / len(currents)
                res_avg = resistance / len(currents)

                # Update data file
                self.file.write("{}, {},".format(res_avg, temp_avg))
                for index in range(len(currents)):
                    self.file.write(" {},".format(voltage[index]))
                self.file.write("\n")
                self.file.flush()

                self.state = 3

            elif self.state is 3:
                # reset machine for next run
                self.blocked = False
                self.temp_index += 1
                if self.temp_index >= len(temps):
                    # out of temperatures to run
                    self.state = 4
                else:
                    self.state = 0
                    self.target_temp = temps[self.temp_index]

            elif self.state is 4:
                # measurement done shut everything off
                self.temperature_controller.temp_sel_set(600)
                self.temperature_controller.set_controller_enable(False)
                self.i_source.enable(False)
                self.state = 5

            elif self.state is 5:
                # idle state post measurement
                temp = self.temperature_controller.read_temp()
                self.frame.temp_readout.SetValue("current temp {:3.3f}K   Desired {}K".format(temp, -1))
                htr_power = self.temperature_controller.query_heater_power()
                self.frame.heater_readout.SetValue("Heater Power: {:3.2f}%".format(htr_power))
                self.frame.step_readout.SetValue("Step {} of {}".format(self.temp_index, len(temps)))

            else:
                # uninitialized state
                # open file
                self.file = open(fname, 'a+')

                # Populate data file header
                header = "R, T, "
                for i in range(len(currents)):
                    header += "v{}, ".format(i)
                header += "\n"

                self.file.write(header)
                self.file.flush()

                self.temperature_controller = VsmTempController(self.frame.instrument_list[self.frame.temp_ID_selector.GetCurrentSelection()], library=library)
                self.i_source = K2400(self.frame.instrument_list[self.frame.curr_ID_selector.GetCurrentSelection()], library=library, current=0)  # keithley 2400 current source
                self.nanovoltmeter = K2182A(self.frame.instrument_list[self.frame.volt_ID_selector.GetCurrentSelection()], library=library, range=10.0)  # keithley 2182A
                self.temp_index = 0
                self.target_temp = temps[self.temp_index]
                self.state = 0
                self.historic = True
                self.frame.append_log("drivers loaded succesfully")

        elif self.historic:
            # measurement done shut everything off
            self.temperature_controller.temp_sel_set(600)
            self.temperature_controller.set_controller_enable(False)
            self.i_source.enable(False)
            self.frame.step_readout.SetValue("Step {} of {}".format(0, 0))
            self.state = 5
            self.historic = False


    def Run(self):
        # Set this loop as the active one. It will automatically reset to the
        # original evtloop when the context manager exits.
        with wx.EventLoopActivator(self):
            while True:

                self.update_experiment()

                # Generate and process idles events for as long as there
                # isn't anything else to do
                while not self.shouldExit and not self.Pending() and self.ProcessIdle():
                    pass

                if self.shouldExit:
                    break

                # Dispatch all the pending events
                self.ProcessEvents()

                # Currently on wxOSX Pending always returns true, so the
                # ProcessIdle above is not ever called. Call it here instead.
                if 'wxOSX' in wx.PlatformInfo:
                    self.ProcessIdle()

            # Proces remaining queued messages, if any
            while True:
                checkAgain = False
                if wx.GetApp() and wx.GetApp().HasPendingEvents():
                    wx.GetApp().ProcessPendingEvents()
                    checkAgain = True
                if 'wxOSX' not in wx.PlatformInfo and self.Pending():
                    self.Dispatch()
                    checkAgain = True
                if not checkAgain:
                    break

        return self.exitCode

    def Exit(self, rc=0):
        self.close_drivers()
        self.exitCode = rc
        self.shouldExit = True
        self.OnExit()
        self.WakeUp()

    def close_drivers(self):
        if not self.state == -1:
            # safety disable instruments
            self.temperature_controller.temp_sel_set(600)
            self.temperature_controller.set_controller_enable(False)
            self.i_source.enable(False)

            # Close instrument resources
            self.temperature_controller.close()
            self.i_source.close()
            self.nanovoltmeter.close()
            self.file.close()

    def ProcessEvents(self):
        if wx.GetApp():
            wx.GetApp().ProcessPendingEvents()

        if self.shouldExit:
            return False

        return self.Dispatch()


class Plot(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.CENTER)
        sizer.Add(self.toolbar, 0, wx.CENTER)
        self.SetSizer(sizer)


class PlotNotebook(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def add(self, name="plot"):
        page = Plot(self.nb)
        self.nb.AddPage(page, name)
        return page.figure



class MyApp(wx.App):

    def MainLoop(self):
        self.SetExitOnFrameDelete(True)
        self.mainLoop = MainEventLoop(self.frame)
        self.mainLoop.Run()

    def ExitMainLoop(self):
        self.mainLoop.Exit()

    def OnInit(self):
        self.frame = MyFrame(None, -1, "R vs. T")
        self.frame.Show(True)
        self.SetTopWindow(self.frame)

        # self.keepGoing = True
        return True

    def append_log(self, to_log: str):
        self.frame.append_log(to_log)


app = MyApp(False)

# Print configuration data
app.append_log("Executing measurement for sample {}".format(sname))
app.append_log("Recording to file: {}".format(fname))
app.append_log("Executing Temperatures (K): {}".format(temps))
app.append_log("Executing Currents (uA): {}".format(currents))

app.MainLoop()

