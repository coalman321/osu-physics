import wx
import visa


# DO NOT MODIFY ON THIS COMPUTER
library = 'C:\\Windows\\System32\\visa64.dll'
res_manager = visa.ResourceManager(library)
instrument_list = res_manager.list_resources()

app = wx.App()
frame = wx.Frame(None, title="R vs. T Measurement Interface")

frame.SetSize(size=(1000, 500))
panel = wx.Panel(frame)

header = wx.StaticText(panel, label="R vs. T Measurement Interface", pos=(0, 0))
font = header.GetFont()
font.PointSize += 10
header.SetFont(font)

wx.StaticText(panel, label="Temperature Controller GPIB Address", pos=(0, 40))
temp_ID_selector = wx.ComboBox(panel, choices=instrument_list,
                               size=(200, 30), pos=(0, 60), style=wx.CB_READONLY)
wx.StaticText(panel, label="Nanovoltmeter GPIB Address", pos=(0, 90))
volt_ID_selector = wx.ComboBox(panel, choices=instrument_list,
                               size=(200, 30), pos=(0, 110), style=wx.CB_READONLY)
wx.StaticText(panel, label="Current Source GPIB Address", pos=(0, 140))
curr_ID_selector = wx.ComboBox(panel, choices=instrument_list,
                               size=(200, 30), pos=(0, 160), style=wx.CB_READONLY)


def append_log(to_log: str):
    x=1


def test_intruments():
    temp = res_manager.open_resource(temp_ID_selector.GetCurrentSelection())
    append_log("Temperature controller ID: " + temp.query("*IDN?"))
    temp.close()
    volt = res_manager.open_resource(volt_ID_selector.GetCurrentSelection())
    append_log("Nanovoltmeter ID: " + volt.query("*IDN?"))
    volt.close()
    curr = res_manager.open_resource(curr_ID_selector.GetCurrentSelection())
    append_log("Nanovoltmeter ID: " + curr.query("*IDN?"))
    curr.close()


connect_button = wx.Button(panel, -1, "Test Connections", pos=(50, 190), size=(100, 30))
connect_button.Bind(wx.EVT_BUTTON, test_intruments)
start_button = wx.Button(panel, -1, "Start Measurement", pos=(40, 230), size=(120, 30))

frame.Show()
app.MainLoop()
