from vsm_temp_controller import *

fname = "C:/temp/work/filename.csv"

print("loading visa driver")
rm = visa.ResourceManager()  # TODO add all resource ID's
temp_control = rm.open_resource('GPIB0::##::INSTR')  # VSM Heater controller
i_source = rm.open_resource('GPIB0::##::INSTR')  # keithley 2400 current source
vxx = rm.open_resource('GPIB0::##::INSTR')  # keithley 2182A
vxy = rm.open_resource('GPIB0::##::INSTR')  # keithley 2182A

print("Temperature controller information: {}".format(temp_control.query("*IDN?")))
print("Current Source information: {}".format(i_source.query("*IDN?")))
print("V XX meter information: {}".format(vxx.query("*IDN?")))
print("V XY meter information: {}".format(vxy.query("*IDN?")))
print("configuring 340 temperature controller")
config_340_controller(temp_control)
print("instrument configured! current temperature: {}°K".format(read_temp(temp_control)))










