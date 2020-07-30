# Priting
import sys
import serial


class TerminalPrinter(object):

    def print_error(self, string):
        print("\n" + string + "\n")

    def parse_error(self, e):
        error_list = str(e).strip('()').split(", b'")
        error_list[0] = error_list[0][1:]
        ret = []
        for err in error_list:
            ret.append(bytes(err[0:-1], 'utf-8').decode('unicode-escape'))
        return ret

    def print_error_and_exception(self, error, exception):
        self.print_error(error)
        error_list = self.parse_error(exception)
        try:
            print(error_list[2])
        except:
            pass

    def calibration_wait_message(self, gyro_calibrated, accel_calibrated, magnet_calibrated, use_ellipsis=True):
        """
        generate a human-readable message that indicates which components remain
        to be calibrated, e.g. if all the arguments are true, then it should
        return the string "waiting for gyroscope, accelerometer and magnetometer
        to be calibrated...".
        """
        components = ((['gyroscope'] if not gyro_calibrated else []) +
                      (['accelerometer'] if not accel_calibrated else []) +
                      (['magnetometer'] if not magnet_calibrated else []))
        components_list_string = ', '.join(components[:-2] + [" and ".join(components[-2:])])
        if components:
            return ("waiting for " + components_list_string +
                    " to be calibrated" + ("..." if use_ellipsis else ""))
        else:
            return "all components calibrated!"


    pass
