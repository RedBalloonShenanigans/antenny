class AntennyException(Exception):
    pass
class AntennyConfigException(AntennyException):
    pass

class AntennyIMUException(AntennyException):
    pass

class AntennyMotorException(AntennyException):
    pass

class AntennyScreenException(AntennyException):
    pass

class AntennyGPSException(AntennyException):
    pass

class AntennyTelemetryException(AntennyException):
    pass

class AntennyControllerException(AntennyException):
    pass

class AntennyAPIException(AntennyException):
    pass