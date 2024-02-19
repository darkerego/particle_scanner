from typing import Any


class Ansi:
    CEND = '\33[0m'
    CBOLD = '\33[1m'
    CITALIC = '\33[3m'
    CURL = '\33[4m'
    CBLINK = '\33[5m'
    CBLINK2 = '\33[6m'
    CSELECTED = '\33[7m'
    CBLACK = '\33[30m'
    CRED = '\33[31m'
    CGREEN = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE = '\33[36m'
    CWHITE = '\33[37m'

    CBLACKBG = '\33[40m'
    CREDBG = '\33[41m'
    CGREENBG = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG = '\33[46m'
    CWHITEBG = '\33[47m'

    CGREY = '\33[90m'
    CRED2 = '\33[91m'
    CGREEN2 = '\33[92m'
    CYELLOW2 = '\33[93m'
    CBLUE2 = '\33[94m'
    CVIOLET2 = '\33[95m'
    CBEIGE2 = '\33[96m'
    CWHITE2 = '\33[97m'

    CGREYBG = '\33[100m'
    CREDBG2 = '\33[101m'
    CGREENBG2 = '\33[102m'
    CYELLOWBG2 = '\33[103m'
    CBLUEBG2 = '\33[104m'
    CVIOLETBG2 = '\33[105m'
    CBEIGEBG2 = '\33[106m'
    CWHITEBG2 = '\33[107m'


class ColorPrint:
    def __init__(self, verbosity: int):
        self.verb = verbosity
        self.place_holder = '__TEXT__'
        self.verb_map = {
            0: Ansi.CBLUE2 + '[' + Ansi.CWHITE + '+' + Ansi.CBLUE2 + '] ' + self.place_holder + Ansi.CEND,
            1: Ansi.CVIOLET + '[' + Ansi.CGREEN2 + '*' + Ansi.CVIOLET + '] ' + self.place_holder + Ansi.CEND,
            2: Ansi.CRED2 + '[' + Ansi.CBLACK + '*' + Ansi.CRED2 + '] ' + self.place_holder + Ansi.CEND,
            3: Ansi.CRED + '[' + Ansi.CBLACK + '!' + Ansi.CRED + '] ' + self.place_holder + Ansi.CEND,
            4: Ansi.CVIOLET2 + '[' + Ansi.CYELLOW + 'debug' + Ansi.CVIOLET2 + '] ' + self.place_holder + Ansi.CRED2
        }

    def output(self, text: Any):
        text = "%s%s" % (text, Ansi.CEND)
        print(self.verb_map.get(0).replace(self.place_holder, text))

    def notice(self, text: Any):
        text = "%s%s" % (text, Ansi.CEND)
        print(self.verb_map.get(1).replace(self.place_holder, text))

    def warning(self, text: Any):
        text = "%s%s" % (text, Ansi.CEND)
        print(self.verb_map.get(2).replace(self.place_holder, text))

    def error(self, text: Any):
        text = "%s%s" % (text, Ansi.CEND)
        print(self.verb_map.get(3).replace(self.place_holder, text))

    def debug(self, text: Any):
        # NOTE: prints of -vvv is supplied.
        text = "%s%s" % (text, Ansi.CEND)
        if self.verb >= 3:
            print(self.verb_map.get(4).replace(self.place_holder, text))

    def print(self, text: Any, verbosity: int = 0):
        if self.verb_map.get(verbosity):
            ansi = self.verb_map.get(verbosity)
            output = ansi.replace(self.place_holder,  "%s%s" % (text, Ansi.CEND))
            if verbosity >= self.verb:
                print(output)
