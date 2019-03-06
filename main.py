from vsm_temp_controller import *
from k2400_isource import K2400
from k2182A_nvmeter import K2182A
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
library = 'C:\\Windows\\System32\\visa64.dll'

# Sample name
sname = "XD###"
# File to output data to
fname = "C:/temp/work/{}.csv".format(sname)
# Currents in mA
currents = [-2500, 2500]
# time between voltage readings in s
reading_delay = .25
# Temperatures in K
temps = sweep(80, 300, 20)
# End Temperature in K
end_temp = 300

print("Recording to file:")
print(fname)
print("Executing Temperatures (K):")
print(temps)
print("Executing Currents (mA):")
print(currents)

# User Data confirmation
user_input = input("Proceed with measurement? Y/N\n")
if "N" in user_input or "n" in user_input:
    print("correct values then re-run to continue")
    exit(-2)

# Adjust currents to A
currents[:] = [x / 1000 for x in currents]

# open file
file = open(fname, 'a+')

# Populate data file header
file.write("R, T\n")
file.flush()

# Enable Matplotlib interactivity
plt.ion()

progress = 1

# begin loading device drivers
print("loading device drivers")
temp_control = VsmTempController(gpib_id='GPIB0::12::INSTR', library=library,)  # VSM Heater controller
i_source = K2400(gpib_id='GPIB0::24::INSTR', library=library, current=0)  # keithley 2400 current source
nvm = K2182A(gpib_id='GPIB0::08::INSTR', library=library, source=1)  # keithley 2182A
print("Driver loading succeeded, beginning data capture")

print("none shall Pass")
exit(-100)

for temp in temps:

    # Execute measurement
    print("Measurement {} of {} \nRamping to Temp: {}°K".format(progress, len(temps), temp))
    temp_control.wait_for_temp(temp)
    temperature = 0
    resistance = 0
    for current in currents:
        i_source.enable_at_current(True, current)
        time.sleep(reading_delay)
        temperature += temp_control.read_temp()
        resistance += nvm.get_last_measurement()/current
    i_source.enable(False)

    # Calculate resistance and voltage average
    temp_avg = temperature / len(currents)
    res_avg = resistance / len(currents)

    # Update data file
    file.write("{}, {}\n".format(res_avg, temp_avg))
    file.flush()

    # Update live data plot
    plt.plot(res_avg, temp_avg)
    plt.title("R vs T for {}".format(sname))
    plt.draw()
    plt.pause(0.01)

    # Update progress
    progress += 1

# Close instrument resources
temp_control.close()
i_source.close()
nvm.close()
file.close()

# Hold data plot open
plt.show(block=True)













