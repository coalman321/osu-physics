import visa


def config_k2400(isource):
    instr_ok = isource.query("*TST?")
    if instr_ok == 0:
        print("ERROR, Temperature controller self test failed")
        exit(-1)
