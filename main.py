from vsm_temp_controller import *
from k2400_isource import K2400
from k2182A_nvmeter import K2182A

fname = "C:/temp/work/filename.csv"
library = 'C:\\Windows\\System32\\visa64.dll'

print("loading device drivers")
#  temp_control = VsmTempController(gpib_id='GPIB0::##::INSTR', library=library,)  # VSM Heater controller
i_source = K2400(gpib_id='GPIB0::24::INSTR', library=library, current=0)  # keithley 2400 current source
nvm = K2182A(gpib_id='GPIB0::08::INSTR', library=library, source=1)  # keithley 2182A
i_source.enable_at_current(True, 0.001)
for x in range(10):
    time.sleep(.25)
    print(nvm.get_last_measurement())
i_source.enable(False)













