import visa


class K2400:

    #  current is measured in A not mA or uA
    def __init__(self, gpib_id: str, library: str, current: int, source=1):
        self.isource = visa.ResourceManager(library).open_resource(gpib_id)
        print(self.isource.query("*IDN?"))
        self.source = source
        self.current = current
        self.__config_k2400()

    def __config_k2400(self):
        instr_ok = self.isource.query("*TST?")
        if instr_ok == 0:
            print("ERROR, Current source self test failed")
            exit(-1)
        print("Current Source OK")
        #  Forcibly disable Source channel being confiured
        self.isource.write("OUTP{}:STAT {}".format(self.source, 0))
        #  Forcibly set IO: can be FRON or REAR
        self.isource.write("ROUT:TERM {}".format("FRON"))
        #  Function mode: can be DC or PULSE
        #  NOT SUPPORTED ON OUR INSTRUMENT
        #  self.isource.write("SOUR{}:FUNC:SHAP {}".format(self.source, "DC"))
        #  Function Mode: can be VOLT, CURR, or MEMO
        self.isource.write(":SOUR{}:FUNC:MODE {}".format(self.source, "CURR"))
        #  Sourcing Mode: can be FIXed, LIST, or SWEep
        self.isource.write(":SOUR{}:CURR:MODE {}".format(self.source, "FIX"))
        #  Source Amplitude: between -1.05 A and 1.05 A
        self.isource.write(":SOUR{}:CURR:LEV:IMM:AMPL {}".format(self.source, self.current))
        #  Source Configuration auto: can be 1 or 0
        self.isource.write(":SOUR{}:CURR:RANG:AUTO {}".format(self.source, 1))
        #  set source delay enable
        self.isource.write(":SOUR{}:DEL {}".format(self.source, "MIN"))

    def enable(self, state: bool):
        """
        enables or disables the selected current source output

        :param state: state of the current source, on or off
        """
        self.isource.write("OUTP{}:STAT {}".format(self.source, 1 if state else 0))

    def enable_at_current(self, state: bool, current: float):
        """
        sets a selected current then enables or disables the current source

        :param state: state of the output channel, on or off
        :param current: how much current to source in A
        """
        self.isource.write(":SOUR{}:CURR:LEV:IMM:AMPL {}".format(self.source, current))
        self.enable(state)
