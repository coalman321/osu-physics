import visa


class K2182A:

    #  source can be 1 or 2, 0 is internal temp
    def __init__(self, gpib_id, source=1):
        self.meter = visa.ResourceManager().open_resource(gpib_id)

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