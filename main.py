from vsm_temp_controller import *
from k2400_isource import K2400
from k2182A_nvmeter import K2182A

fname = "C:/temp/work/filename.csv"

print("loading device drivers")
#  temp_control = VsmTempController(gpib_id='GPIB0::##::INSTR')  # VSM Heater controller
#  i_source = K2400(gpib_id='GPIB0::##::INSTR', current=0)  # keithley 2400 current source
nvm = K2182A(gpib_id='GPIB0::##::INSTR', source=1)  # keithley 2182A
for x in range(100):
    time.sleep(.25)
    print(nvm.get_last_measurement())













