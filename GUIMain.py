import os

import wx
import visa
import time
from vsm_temp_controller import VsmTempController
from k2400_isource import K2400
from k2182A_nvmeter import K2182A
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sweep(start, end, step):
    arr = []
    current = start
    for x in range(int((end-start)/step)):
        arr.append(current)
        current += step
    arr.append(end)
    return arr


# DO NOT MODIFY ON THIS COMPUTER
library = 'C:/Windows/System32/visa32.dll'
k_epsilon = 1.0E-1  # value used for an approximately equals statement


class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(900, 700))

        self.CenterOnScreen()

        self.res_manager = visa.ResourceManager(library)
        self.instrument_list = self.res_manager.list_resources()

        self.allow_measurement = False

        self.menu_bar = wx.MenuBar()
        self.page_menu = wx.Menu()
        self.main_menu_select = self.page_menu.Append(wx.NewId(), "Main Menu", "Main menu")
        self.page_menu.Bind(wx.EVT_MENU, self.show_main_menu, self.main_menu_select)
        self.config_menu_select = self.page_menu.Append(wx.NewId(), "Configuration Menu", "Configuration menu")
        self.page_menu.Bind(wx.EVT_MENU, self.show_config_menu, self.config_menu_select)
        self.graph_menu_select = self.page_menu.Append(wx.NewId(), "Live Graph", "Live updated graph")
        self.page_menu.Bind(wx.EVT_MENU, self.show_graph_menu, self.graph_menu_select)
        self.menu_bar.Append(self.page_menu, "&Menu")
        self.SetMenuBar(self.menu_bar)

        # setup measurement panel & log
        self.main_panel = wx.Panel(self)
        self.main_panel.SetSize(size=(900, 700))
        self.main_panel.Show(True)

        self.main_header = wx.StaticText(self.main_panel, label="R vs. T Measurement Interface", pos=(250, 0))
        font = self.main_header.GetFont()
        font.PointSize += 10
        self.main_header.SetFont(font)

        wx.StaticText(self.main_panel, label="Temperature Controller GPIB Address", pos=(10, 40))
        self.temp_ID_selector = wx.ComboBox(self.main_panel, choices=self.instrument_list,
                                            size=(200, 30), pos=(10, 60), style=wx.CB_READONLY)
        wx.StaticText(self.main_panel, label="Nanovoltmeter GPIB Address", pos=(10, 90))
        self.volt_ID_selector = wx.ComboBox(self.main_panel, choices=self.instrument_list,
                                            size=(200, 30), pos=(10, 110), style=wx.CB_READONLY)
        wx.StaticText(self.main_panel, label="Current Source GPIB Address", pos=(10, 140))
        self.curr_ID_selector = wx.ComboBox(self.main_panel, choices=self.instrument_list,
                                            size=(200, 30), pos=(10, 160), style=wx.CB_READONLY)

        self.step_readout = wx.TextCtrl(self.main_panel, size=(200, 30), pos=(10, 280), style=wx.TE_READONLY, value="")
        self.temp_readout = wx.TextCtrl(self.main_panel, size=(200, 30), pos=(10, 320), style=wx.TE_READONLY, value="")
        self.heater_readout = wx.TextCtrl(self.main_panel, size=(200, 30), pos=(10, 360), style=wx.TE_READONLY, value="")
        self.sample_ID = wx.TextCtrl(self.main_panel, size=(200, 30), pos = (10, 400), style=wx.TE_READONLY, value="Sample ID: #####")

        self.connect_button = wx.Button(self.main_panel, -1, "Test Connections", pos=(50, 190), size=(100, 30))
        self.connect_button.Bind(wx.EVT_BUTTON, self.test_intruments)
        self.start_button = wx.Button(self.main_panel, -1, "Start Measurement", pos=(40, 230), size=(120, 30))
        self.start_button.Bind(wx.EVT_BUTTON, self.run_measurement)

        self.console = wx.TextCtrl(self.main_panel, size=(500, 400), pos=(250, 50), style=wx.TE_READONLY | wx.TE_MULTILINE)

        # setup configuration panel
        self.config_panel = wx.Panel(self)
        self.config_panel.SetSize(size=(900, 700))
        self.config_panel.Show(False)

        self.config_header = wx.StaticText(self.config_panel, label="Measurement Configuration", pos=(300, 0))
        font = self.config_header.GetFont()
        font.PointSize += 8
        self.config_header.SetFont(font)

        # temp and current configs
        wx.StaticText(self.config_panel, label="Currents to run (uA)\n separated by a ,", pos=(10, 25))
        self.user_currents = wx.TextCtrl(self.config_panel, size=(100, 30), pos=(10, 60), value="-10,10")
        wx.StaticText(self.config_panel, label="Starting temperature (K)", pos=(10, 100))
        self.user_start_temp = wx.TextCtrl(self.config_panel, size=(100, 30), pos=(10, 120), value="80")
        wx.StaticText(self.config_panel, label="Ending temperature (K)", pos=(10, 160))
        self.user_stop_temp = wx.TextCtrl(self.config_panel, size=(100, 30), pos=(10, 180), value="280")
        wx.StaticText(self.config_panel, label="Temperature step", pos=(10, 220))
        self.user_temp_step = wx.TextCtrl(self.config_panel, size=(100, 30), pos=(10, 240), value="10")

        # data file save selection
        wx.StaticText(self.config_panel, label="Sample ID", pos=(200, 40))
        self.user_sample = wx.TextCtrl(self.config_panel, size=(100, 25), pos=(200, 60), value="")
        wx.StaticText(self.config_panel, label="Save directory", pos=(200, 100))
        self.user_folder = wx.TextCtrl(self.config_panel, size=(400, 25), pos=(200, 120), value="", style=wx.TE_READONLY)
        self.user_browse = wx.Button(self.config_panel, -1, "Browse files", pos=(200, 160), size=(100, 30))
        self.user_browse.Bind(wx.EVT_BUTTON, self.on_browse)

        # wait times for measurement stability
        wx.StaticText(self.config_panel, label="Initial stability\nwait time (s)", pos=(650, 40))
        self.user_init_delay = wx.TextCtrl(self.config_panel, size=(100, 25), pos=(650, 75), value="1200")
        wx.StaticText(self.config_panel, label="Operational stability\nwait time (s)", pos=(650, 105))
        self.user_other_delay = wx.TextCtrl(self.config_panel, size=(100, 25), pos=(650, 140), value="480")
        wx.StaticText(self.config_panel, label="Measurement\nwait time (s)", pos=(650, 170))
        self.user_measure_delay = wx.TextCtrl(self.config_panel, size=(100, 25), pos=(650, 205), value="1.00")

        # setup image panel for a live graph
        self.graph_panel = wx.Panel(self)
        self.graph_panel.SetSize(size=(900, 700))
        self.graph_panel.Show(False)

        self.graph_header = wx.StaticText(self.graph_panel, label="Live updated graph", pos=(325, 0))
        font = self.graph_header.GetFont()
        font.PointSize += 8
        self.graph_header.SetFont(font)

        # setup image viewer for "live" graph
        plt.title("R vs T")
        plt.xlabel("Temperature (K)")
        plt.ylabel("Resistance (ohms)")
        self.r_vs_t = plt.plot([0],[0])
        plt.savefig("lastgraph.png")
        self.graph = wx.StaticBitmap(self.graph_panel, -1,
                                     wx.Bitmap("{}\\lastgraph.png".format(os.getcwd()), wx.BITMAP_TYPE_ANY),
                                     size=(700, 700), pos=(110, 35))
        self.graph.SetBitmap(wx.Bitmap("{}\\lastgraph.png".format(os.getcwd()), wx.BITMAP_TYPE_ANY))

        # pre-measurement setup
        self.temps = []
        self.currents = []
        self.sample_name = ""
        self.data_file_path = ""
        self.temp_stable_wait_initial = 1200
        self.temp_stable_wait_other = 480
        self.measurement_delay_time = 1.00
        self.update_readouts(-1, 280, 0.0, "off")




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
        if not self.curr_ID_selector.GetCurrentSelection() == -1:
            curr = self.res_manager.open_resource(self.instrument_list[self.curr_ID_selector.GetCurrentSelection()])
            self.append_log("Current Source ID: " + curr.query("*IDN?"))
            curr.close()
        else:
            self.append_log("Current source not selected")

    def run_measurement(self, aaa):
        self.clear_log()

        if not self.check_valid_config():
            self.append_log("Measurement is not properly configured\n" +
                            "Set all values before proceeding with measurement")
            return

        # set the measurement values
        self.sample_name = self.user_sample.GetValue()
        self.data_file_path = "{}{}.csv".format(self.user_folder.GetValue(), self.sample_name)
        self.temps = sweep(float(self.user_start_temp.GetValue()), float(self.user_stop_temp.GetValue()), float(self.user_temp_step.GetValue()))
        self.currents = [float(x) for x in self.user_currents.GetValue().split(",")]
        self.append_log("Executing measurement for sample {}".format(self.sample_name))
        self.append_log("Recording to file: {}".format(self.data_file_path))
        self.append_log("Executing Temperatures (K): {}".format(self.temps))
        self.append_log("Executing Currents (uA): {}".format(self.currents))
        self.update_sample_name(self.sample_name)
        self.update_readouts(-1, 280, 0.0, "off")

        self.temp_stable_wait_initial = float(self.user_init_delay.GetValue())
        self.temp_stable_wait_other = float(self.user_other_delay.GetValue())
        self.measurement_delay_time = float(self.user_measure_delay.GetValue())

        # Adjust currents from uA to A
        self.currents[:] = [x / 1000000 for x in self.currents]

        self.append_log("\nearliest possible finish time will be {}".format(time.strftime(
            "%m/%d/%y at %I:%M:%S %p\n", time.localtime(time.time() + self.temp_stable_wait_initial +
                                                   len(self.temps) * self.temp_stable_wait_other))))

        if not self.check_valid_instr():
            self.append_log("One or more instruments were not selected\n"
                            + "select all instruments before running measurement")
            return

        self.lock_config(True)
        self.allow_measurement = True
        self.start_button.SetLabel("Stop Measurement")
        self.start_button.Unbind(wx.EVT_BUTTON, self.run_measurement)
        self.start_button.Bind(wx.EVT_BUTTON, self.stop_measurement)

    def append_log(self, to_log: str):
        self.console.AppendText(to_log + "\n")

    def clear_log(self):
        self.console.SetValue("")

    def stop_measurement(self, aaa):
        self.lock_config(False)
        self.allow_measurement = False
        self.start_button.SetLabel("Start Measurement")
        self.start_button.Unbind(wx.EVT_BUTTON, self.stop_measurement)
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

    def update_temp(self, current, target):
        self.temp_readout.SetValue("Current {:3.3f}K   Desired {}K".format(current, target))

    def update_htr(self, power):
        self.heater_readout.SetValue("Heater Power: {:3.2f}%".format(power))

    def update_step(self, current_step):
        self.step_readout.SetValue("Step {} of {}".format(current_step, len(self.temps)))

    def update_readouts(self, current_temp, target_temp, htr_power, current_step):
        self.update_temp(current_temp, target_temp)
        self.update_htr(htr_power)
        self.update_step(current_step)

    def update_sample_name(self, sample_name):
        self.sample_ID.SetValue("Sample ID: {}".format(sample_name))
        plt.title("R vs T for {}".format(sample_name))
        self.update_plot_data([0], [0])

    def show_main_menu(self, aaaaa):
        if not self.main_panel.IsShown():
            self.main_panel.Show()
            self.config_panel.Hide()
            self.graph_panel.Hide()

    def show_config_menu(self, aaaaa):
        if not self.config_panel.IsShown():
            self.config_panel.Show()
            self.main_panel.Hide()
            self.graph_panel.Hide()

    def show_graph_menu(self, aaaaa):
        if not self.graph_panel.IsShown():
            self.graph_panel.Show()
            self.config_panel.Hide()
            self.main_panel.Hide()

    def on_browse(self, aaaaa):
        file_dialog = wx.DirDialog(self,  "Select data file directory", "", wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # the user changed their mind
        # Proceed loading the file chosen by the user
        self.user_folder.SetValue(file_dialog.GetPath() + "\\")

    def lock_config(self, lock):
        self.user_currents.SetEditable(not lock)
        self.user_start_temp.SetEditable(not lock)
        self.user_stop_temp.SetEditable(not lock)
        self.user_temp_step.SetEditable(not lock)
        self.user_sample.SetEditable(not lock)
        self.user_measure_delay.SetEditable(not lock)
        self.user_init_delay.SetEditable(not lock)
        self.user_other_delay.SetEditable(not lock)
        self.user_browse.Enable(not lock)

    def update_plot_data(self, temps, resistances):
        self.r_vs_t = plt.plot(temps, resistances)
        plt.savefig("lastgraph.png")
        self.graph.SetBitmap(wx.Bitmap("{}\\lastgraph.png".format(os.getcwd()), wx.BITMAP_TYPE_ANY))

    # def save_config(self):

    # def load_config(self):

    def check_valid_config(self):
        to_return = True
        if self.user_currents.GetValue() is "":
            self.append_log("User currents have not been set")
            to_return = False
        if self.user_start_temp.GetValue() is "":
            self.append_log("Starting temperature has not been set")
            to_return = False
        if self.user_stop_temp.GetValue() is "":
            self.append_log("Ending temperature has not been set")
            to_return = False
        if self.user_temp_step.GetValue() is "":
            self.append_log("Temperature step has not been set")
            to_return = False
        if not os.path.isdir(self.user_folder.GetValue()):
            self.append_log("No save directory selected")
            to_return = False
        if self.user_sample.GetValue() is "":
            self.append_log("Sample ID has not been set")
            to_return = False
        if self.user_measure_delay.GetValue() is "":
            self.append_log("Measurement delay has not been set")
            to_return = False
        if self.user_init_delay.GetValue() is "":
            self.append_log("Initial cool-down delay has not been set")
            to_return = False
        if self.user_other_delay.GetValue() is "":
            self.append_log("Operational delay has not been set")
            to_return = False
        return to_return

    def check_valid_instr(self):
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
        return instr_select

class MainEventLoop(wx.GUIEventLoop):
    def __init__(self, frame):
        wx.GUIEventLoop.__init__(self)
        self.frame = frame
        self.exitCode = 0
        self.shouldExit = False
        self.blocked = False
        self.historic = False
        self.init_ready = False
        self.idle = False
        self.state = -1
        self.t_done = float("inf")
        self.temp_index = 0
        self.temp_data = []
        self.resistance_data = []

    def update_experiment(self):
        if self.frame.allow_measurement:
            if self.state is 0:
                self.frame.append_log("Setting temperature to {}K".format(self.target_temp))
                self.temperature_controller.set_controller_enable(True)
                self.temperature_controller.temp_sel_set(self.target_temp)
                self.state = 1
            elif self.state is 1:
                # ramping to a temperature
                # update readouts
                temp = self.temperature_controller.read_temp()
                htr_power = self.temperature_controller.query_heater_power()
                self.frame.update_readouts(temp, self.target_temp, htr_power, self.temp_index + 1)

                # check if ready to advance or engage timer
                if not (temp < self.target_temp - k_epsilon or temp > self.target_temp + k_epsilon) and not self.blocked:
                    self.frame.append_log("Temperature reached, waiting for stability")
                    if self.temp_index < 1:
                        # on initial cooldown wait a bit longer for adjustments
                        self.t_done = time.time() + self.frame.temp_stable_wait_initial
                    else:
                        self.t_done = time.time() + self.frame.temp_stable_wait_other
                    self.frame.append_log("measurement will start at {}".format(time.strftime("%H:%M:%S", time.localtime(self.t_done))))
                    self.blocked = True
                if self.blocked and self.t_done < time.time():
                    # ready to advance state into measurement
                    self.state = 2

            elif self.state is 2:
                # update statuses
                self.frame.append_log("Executing measurement {}".format(self.temp_index+1))
                temp = self.temperature_controller.read_temp()
                htr_power = self.temperature_controller.query_heater_power()
                self.frame.update_readouts(temp, self.target_temp, htr_power, self.temp_index + 1)

                # execute measurement
                # TODO find way to not block thread on reads
                temperature = 0
                resistance = 0
                voltage = []
                for current in self.frame.currents:
                    self.i_source.enable_at_current(True, current)
                    time.sleep(self.frame.measurement_delay_time)
                    temperature += self.temperature_controller.read_temp()
                    voltage.append(self.nanovoltmeter.get_last_measurement())
                    resistance += voltage[-1] / current
                self.i_source.enable(False)

                # Calculate resistance and voltage average
                temp_avg = temperature / len(self.frame.currents)
                res_avg = resistance / len(self.frame.currents)

                # update live graph
                self.temp_data.append(temp_avg)
                self.resistance_data.append(res_avg)
                self.frame.update_plot_data(self.temp_data, self.resistance_data)

                # Update data file
                self.file.write("{}, {},".format(res_avg, temp_avg))
                for index in range(len(self.frame.currents)):
                    self.file.write(" {},".format(voltage[index]))
                self.file.write("\n")
                self.file.flush()

                self.frame.append_log("Measurement {} complete at {}".format(self.temp_index+1,
                                         time.strftime("%H:%M:%S", time.localtime(time.time()))))

                self.state = 3

            elif self.state is 3:
                # reset machine for next run
                self.blocked = False
                self.temp_index += 1
                if self.temp_index >= len(self.frame.temps):
                    # out of temperatures to run
                    self.state = 4
                else:
                    self.state = 0
                    self.target_temp = self.frame.temps[self.temp_index]

            elif self.state is 4:
                # measurement done shut everything off
                self.temperature_controller.temp_sel_set(600)
                self.temperature_controller.set_controller_enable(False)
                self.i_source.enable(False)
                self.state = 5

            elif self.state is 5:
                # idle state post measurement
                self.frame.append_log("Measurement complete at {}\nSee data file for results".format(time.strftime("%H:%M:%S", time.localtime(time.time()))))
                temp = self.temperature_controller.read_temp()
                htr_power = self.temperature_controller.query_heater_power()
                self.frame.update_readouts(temp, self.target_temp, htr_power, self.temp_index + 1)

            else:
                self.frame.update_readouts(-1, 280, 0.0, "starting")
                # uninitialized state
                # open file
                self.file = open(self.frame.fname, 'a+')

                # Populate data file header
                header = "R, T, "
                for i in range(len(self.frame.currents)):
                    header += "v{}, ".format(i)
                header += "\n"

                self.file.write(header)
                self.file.flush()

                self.temperature_controller = VsmTempController(self.frame.instrument_list[self.frame.temp_ID_selector.GetCurrentSelection()], library=library)
                self.i_source = K2400(self.frame.instrument_list[self.frame.curr_ID_selector.GetCurrentSelection()], library=library, current=0)  # keithley 2400 current source
                self.nanovoltmeter = K2182A(self.frame.instrument_list[self.frame.volt_ID_selector.GetCurrentSelection()], library=library, range=10.0)  # keithley 2182A
                self.temp_index = 0
                self.target_temp = self.frame.temps[self.temp_index]
                self.state = 0
                self.historic = True
                self.idle = False
                self.frame.append_log("drivers loaded succesfully")

        elif self.historic:
            # measurement paused shut current off
            temp = self.temperature_controller.read_temp()
            htr_power = self.temperature_controller.query_heater_power()
            self.frame.update_readouts(temp, self.target_temp, htr_power, "paused")

            self.i_source.enable(False)

            self.historic = False
            self.idle = True

        elif self.idle:
            temp = self.temperature_controller.read_temp()
            htr_power = self.temperature_controller.query_heater_power()
            self.frame.update_readouts(temp, self.target_temp, htr_power, "paused")

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

    def append_log(self, to_log: str):
        self.frame.append_log(to_log)


app = MyApp(False)
app.MainLoop()

