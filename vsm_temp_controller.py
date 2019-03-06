import time
import visa

k_epsilon = 1.0E-1  # value used for an approximately equals statement


class VsmTempController:

    #  loop: control loop, can be 0 or 1
    def __init__(self, gpib_id:str, library:str,  loop=1):
        self.temp_controller = visa.ResourceManager(library).open_resource(gpib_id)
        print(self.temp_controller.query("*IDN?"))
        self.loop = loop
        self.config_340_controller()

    #  controller_units: 1 is kelvin, 2 is celsius, 3 is sensor units
    #  sensor_input can be A or B
    def config_340_controller(self, controller_units=1, sensor_input="A"):
        instr_ok = self.temp_controller.query("*TST?")
        if instr_ok == 0:
            print("ERROR, Temperature controller self test failed")
            exit(-1)
        print("Temperature Controller OK")
        controller_mode = 1  # 1 = manual PID, 2 = Zone, 3 = Open Loop, 4 = AutoTune PID, 5 = AutoTune PI, 6 = AutoTune P
        self.temp_controller.write("CMODE {}, {}".format(self.loop, controller_mode))
        controller_state = 0  # 0 is off, 1 is on -- DEFAULT OFF
        penable = 0  # 0 is off after power up, 1 is on after power up -- DEFAULT OFF
        self.temp_controller.write("CSET {}, {}, {}, {}, {}".format(self.loop, sensor_input,
                                                                    controller_units, controller_state, penable))
        ramp_enable = 0  # enable or disable temperature ramping: 0 = off, 1 = on
        ramp_rate = 10  # Ramp rate in degrees kelvin per minute
        self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, ramp_enable, ramp_rate))
        self.temp_sel_set(600)  # zeroes PID Values and disables heater

    # setpoint in kelvin, Loop can be either 0 or 1
    # Configures the PID values to achieve the setpoint
    def temp_sel_set(self, setpoint: float):
        #  ALL PID Values came from the VSM Manual
        if self.__in_range(75, 90, setpoint):
            self.temp_controller.write("PID {}, {}, {}, {}".format(self.loop, 20, 30, 0))
            self.temp_controller.write("SETP {}, {}".format(self.loop, setpoint))
            self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, 1, 10))
            self.temp_controller.write("SETTLE {}, {}".format(0.5, 5))
        elif self.__in_range(90, 135, setpoint):
            self.temp_controller.write("PID {}, {}, {}, {}".format(self.loop, 20, 20, 0))
            self.temp_controller.write("SETP {}, {}".format(self.loop, setpoint))
            self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, 1, 10))
            self.temp_controller.write("SETTLE {}, {}".format(0.5, 5))
        elif self.__in_range(135, 175, setpoint):
            self.temp_controller.write("PID {}, {}, {}, {}".format(self.loop, 20, 20, 0))
            self.temp_controller.write("SETP {}, {}".format(self.loop, setpoint))
            self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, 1, 10))
            self.temp_controller.write("SETTLE {}, {}".format(1, 5))
        elif self.__in_range(175, 250, setpoint):
            self.temp_controller.write("PID {}, {}, {}, {}".format(self.loop, 20, 15, 0))
            self.temp_controller.write("SETP {}, {}".format(self.loop, setpoint))
            self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, 1, 15))
            self.temp_controller.write("SETTLE {}, {}".format(1, 5))
        elif self.__in_range(250, 350, setpoint):
            self.temp_controller.write("PID {}, {}, {}, {}".format(self.loop, 20, 15, 0))
            self.temp_controller.write("SETP {}, {}".format(self.loop, setpoint))
            self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, 1, 20))
            self.temp_controller.write("SETTLE {}, {}".format(1, 5))
        else:
            self.temp_controller.write("PID {}, {}, {}, {}".format(self.loop, 0, 0, 0))
            self.temp_controller.write("SETP {}, {}".format(self.loop, 273))
            self.temp_controller.write("RAMP {}, {}, {}".format(self.loop, 0, 10))
            self.temp_controller.write("SETTLE {}, {}".format(1, 5))

    #  Read in kelvin, Sensor can be either A or B
    def read_temp(self, sensor="A"):
        """
        Reads the temperature of the chamber in K

        :param sensor: Sensor to get the reading from
        :return: the temperature value returned by the instrument in K
        """
        return self.temp_controller.query_ascii_values("KRDG? {}".format(sensor))

    # wait ot arrive at a specific temperature in kelvin plus or minus k_epsilon
    def wait_for_temp(self, target):
        """
        While loop that waits for a specified temperature to be reached. It will exit when within + or - .1 K

        :param target: setpoint in K to wait for
        """
        temp = self.read_temp()
        while temp < target - k_epsilon or temp > target + k_epsilon:
            time.sleep(0.01)
            temp = self.read_temp()

    # set temperature and wait for arrival
    def set_wait_for_temp(self, setpoint):
        self.temp_sel_set(setpoint)
        self.wait_for_temp(setpoint)

    def __in_range(self, lower, upper, value):
        if lower <= value <= upper:
            return True
        else:
            return False

    def close(self):
        self.temp_controller.close()