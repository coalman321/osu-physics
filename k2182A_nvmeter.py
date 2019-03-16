import pyvisa
import time


class K2182A:

    #  source can be 1 or 2, 0 is internal temp
    def __init__(self, gpib_id, library:str, source=1, range=1.0):
        self.meter = pyvisa.highlevel.ResourceManager(library).open_resource(gpib_id)
        print(self.meter.query("*IDN?"))
        self.range = range
        self.__config_k2182a()

    def __config_k2182a(self):
        instr_ok = self.meter.query("*TST?")
        if instr_ok == 0:
            print("ERROR, Nanovolt meter self test failed")
            exit(-1)
        print("Nano-Voltmeter OK")
        #  set to DC volts mode -- DOESNT WORK ON OUR METER
        #  self.meter.write("CONF:VOLT:DC")
        #  Disable Analog Out
        self.meter.write(":OUTP OFF")
        #  set voltage range
        self.meter.write(":SENS:VOLT:RANG {:1.2f}".format(self.range))

    def get_last_measurement(self):
        """
        Gets the last measurement taken by the nanovoltmeter on that channel

        :return: returns the voltage in mV
        """
        return float(self.meter.query("FETC?"))

    def close(self):
        self.meter.close()
