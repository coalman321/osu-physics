import wx
import visa
import time
from vsm_temp_controller import VsmTempController
from k2400_isource import K2400
from k2182A_nvmeter import K2182A

# DO NOT MODIFY ON THIS COMPUTER
library = 'C:\\Windows\\System32\\visa64.dll'
k_epsilon = 1.0E-1  # value used for an approximately equals statement

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
fname = "C:/temp/work/{}DRYRUN.csv".format(sname)
# Currents in uA
currents = [30, -30]
# time between voltage readings in s
reading_delay = 1.0
# Temperatures in K
temps = sweep(80, 300, 20)
# wait for stability in s
temp_stable_wait = 2 * 60
# End Temperature in K
# end_temp = 300

# Print configuration data
print("Executing measurement for sample {}".format(sname))
print("Recording to file: {}".format(fname))
print("Executing Temperatures (K): {}".format(temps))
print("Executing Currents (uA): {}".format(currents))

# Adjust currents from uA to A
currents[:] = [x / 1000000 for x in currents]

class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1000, 800))

        self.res_manager = visa.ResourceManager(library)
        self.instrument_list = self.res_manager.list_resources()

        self.allow_measurement = False

        # custom
        panel = wx.Panel(self)

        self.header = wx.StaticText(panel, label="R vs. T Measurement Interface", pos=(0, 0))
        font = self.header.GetFont()
        font.PointSize += 10
        self.header.SetFont(font)

        wx.StaticText(panel, label="Temperature Controller GPIB Address", pos=(0, 40))
        self.temp_ID_selector = wx.ComboBox(panel, choices=self.instrument_list,
                                       size=(200, 30), pos=(0, 60), style=wx.CB_READONLY)
        wx.StaticText(panel, label="Nanovoltmeter GPIB Address", pos=(0, 90))
        self.volt_ID_selector = wx.ComboBox(panel, choices=self.instrument_list,
                                       size=(200, 30), pos=(0, 110), style=wx.CB_READONLY)
        wx.StaticText(panel, label="Current Source GPIB Address", pos=(0, 140))
        self.curr_ID_selector = wx.ComboBox(panel, choices=self.instrument_list,
                                       size=(200, 30), pos=(0, 160), style=wx.CB_READONLY)

        self.temp_readout = wx.TextCtrl(panel, size=(200, 30), pos=(300, 60), style=wx.TE_READONLY)
        self.heater_readout = wx.TextCtrl(panel, size=(200, 30), pos=(300, 100), style=wx.TE_READONLY)
        self.step_readout = wx.TextCtrl(panel, size=(200, 30), pos=(300, 140), style=wx.TE_READONLY)

        self.connect_button = wx.Button(panel, -1, "Test Connections", pos=(50, 190), size=(100, 30))
        self.connect_button.Bind(wx.EVT_BUTTON, self.test_intruments)
        self.start_button = wx.Button(panel, -1, "Start Measurement", pos=(40, 230), size=(120, 30))
        self.start_button.Bind(wx.EVT_BUTTON, self.run_measurement)

    def append_log(self, to_log: str):
        print(to_log)

    def test_intruments(self, aaa):
        temp = self.res_manager.open_resource(self.instrument_list[self.temp_ID_selector.GetCurrentSelection()])
        self.append_log("Temperature controller ID: " + temp.query("*IDN?"))
        temp.close()
        volt = self.res_manager.open_resource(self.instrument_list[self.volt_ID_selector.GetCurrentSelection()])
        self.append_log("Nanovoltmeter ID: " + volt.query("*IDN?"))
        volt.close()
        curr = self.res_manager.open_resource(self.instrument_list[self.curr_ID_selector.GetCurrentSelection()])
        self.append_log("Current Source ID: " + curr.query("*IDN?"))
        curr.close()

    def run_measurement(self, aaa):
        self.allow_measurement = True
        self.start_button.SetLabel("Stop Measurement")
        self.start_button.Bind(wx.EVT_BUTTON, self.stop_measurement)

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
        self.state = -1
        self.t_arrived = float("inf")
        self.temp_index = 0

    def update_experiment(self):
        if self.frame.allow_measurement:
            if self.state is 0:
                print("setting temperature to {}K".format(self.target_temp))
                self.temperature_controller.set_controller_enable(True)
                # self.temperature_controller.temp_sel_set(self.target_temp)
                self.state = 1
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
                print("executing measurement")
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
                self.frame.step_readout.SetValue("Step {} of {}".format(self.temp_index+1, len(temps)))

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
                self.nanovoltmeter = K2182A(self.frame.instrument_list[self.frame.volt_ID_selector.GetCurrentSelection()], library=library)  # keithley 2182A
                self.temp_index = 0
                self.target_temp = temps[self.temp_index]
                self.state = 0
                self.historic = True
                print("drivers loaded succesfully")
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


app = MyApp(False)
app.MainLoop()

