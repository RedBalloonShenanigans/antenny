from mp.pyboard import PyboardError

# TODO: Fix all this: These should have self.message attributes


class NoAntKontrolError(Exception):
    pass


class AntKontrolInitError(Exception):
    pass


class NotRespondingError(Exception):
    pass


class NotVisibleError(Exception):
    pass


class DeviceNotOpenError(Exception):
    pass


class SafeModeWarning(Warning):
    pass


class BNO055RegistersError(Exception):
    pass


class BNO055UploadError(Exception):
    pass


class I2CScanError(Exception):
    pass


class PinInputError(Exception):
    pass


class I2CNoAddressesError(Exception):
    pass


class ConfigStatusError(Exception):
    pass


class NoSuchConfigError(Exception):
    pass


class ConfigUnknownError(Exception):
    pass





if __name__ == '__main__':
    class W(Warning):
        print("Warning....")
        pass

    try:
        raise W
    except:
        print("asdfasdf")
