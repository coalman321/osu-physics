import pyvisa


class K2182A:

    #  source can be 1 or 2, 0 is internal temp
    def __init__(self, gpib_id, library:str, source=1):
        self.meter = pyvisa.highlevel.ResourceManager(library).open_resource(gpib_id)
        print(self.meter.query("*IDN?"))

    #  unused
    def config_k2182a(self):
        instr_ok = self.meter.query("*TST?")
        if instr_ok == 0:
            print("ERROR, Nanovolt meter self test failed")
            exit(-1)
        #  set to DC volts mode
        self.meter.write("CONF:VOLT[:DC]")
        #  set autorange on

    def get_last_measurement(self):
        return self.meter.query("FETC?")