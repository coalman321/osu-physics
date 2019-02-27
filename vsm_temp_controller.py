import time
import visa

k_epsilon = 1.0E-3  # value used for an approximately equals statement

def config_340_controller(temp_controller):
    instr_ok = temp_controller.query("*TST?")
    if instr_ok == 0:
        print("ERROR, Temperature controller self test failed")
        exit(-1)
    loop = 1  # control loop to address
    controller_mode = 1  # 1 = manual PID, 2 = Zone, 3 = Open Loop, 4 = AutoTune PID, 5 = AutoTune PI, 6 = AutoTune P
    temp_controller.write("CMODE {}, {}".format(loop, controller_mode))
    sensor_input = "A"  # configure for temperature probe A
    controller_units = 1  # 1 is kelvin, 2 is celsius, 3 is sensor units
    controller_state = 0  # 0 is off, 1 is on DEFAULT OFF
    penable = 0  # 0 is off after power up, 1 is on after power up DEFAULT OFF
    temp_controller.write("CSET {}, {}, {}, {}, {}".format(loop, sensor_input,
                                                           controller_units,
                                                           controller_state,
                                                           penable))
    ramp_enable = 1  # enable or disable temperature ramping: 0 = off, 1 = on
    ramp_rate = 10  # Ramp rate in degrees kelvin per minute
    temp_controller.write("RAMP {}, {}, {}".format(loop, ramp_enable, ramp_rate))


def in_range(lower, upper, value):
    if lower <= value <= upper:
        return True
    else:
        return False


# setpoint in kelvin, Loop can be either 0 or 1
def temp_sel_set(temp_controller, setpoint, loop=1):
    if in_range(100, 150, setpoint):
        temp_controller.write("PID {}, {}, {}, {}".format(loop, 0, 0, 0))
        temp_controller.write("SETP {}, {}".format(loop, setpoint))
    elif in_range(150, 200, setpoint):
        temp_controller.write("PID {}, {}, {}, {}".format(loop, 0, 0, 0))
        temp_controller.write("SETP {}, {}".format(loop, setpoint))
    elif in_range(200, 250, setpoint):
        temp_controller.write("PID {}, {}, {}, {}".format(loop, 0, 0, 0))
        temp_controller.write("SETP {}, {}".format(loop, setpoint))
    else:
        print("out of safe range for this program, setting PID to 0")
        temp_controller.write("PID {}, {}, {}, {}".format(loop, 0, 0, 0))
        temp_controller.write("SETP {}, {}".format(loop, 273))


#  Read in kelvin, Sensor can be either A or B
def read_temp(temp_controller, sensor="A"):
    return temp_controller.query_ascii_values("KRDG? {}".format(sensor))


# wait ot arrive at a specific temperature in kelvin plus or minus k_epsilon
def wait_for_temp(temp_controller, target):
    temp = read_temp(temp_controller)
    while temp < target - k_epsilon or temp > target + k_epsilon:
        time.sleep(0.01)
        temp = read_temp(temp_controller)


# set temperature and wait for arrival
def set_wait_for_temp(temp_controller, setpoint):
    temp_sel_set(temp_controller, setpoint)
    wait_for_temp(temp_controller, setpoint)