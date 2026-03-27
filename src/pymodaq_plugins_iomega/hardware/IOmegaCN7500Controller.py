#-----------------------------------------------------------------------
# IOmega CN7500 Temperature Controller Wrapper
#
# Informations:
# Use RS485 serial hardware: an internal USB-RS485 converter is installed into the instrument so a simple
# USB cable can be used for a connexion between the instrument and the PC.
# CN7500 Serial parameters: 9600 bauds, 8 data bits, 1 stop bit, no parity
# The ASCII modbus protocol is used to communicate with the IOmega controller.
#
# This wrapper used the minimalmodbus module and part of the omegaCN7500.py module so see:
# --> https://minimalmodbus.readthedocs.io/en/stable/index.html  for a documentation on module Modbus and how to install
# --> https://github.com/pyhys/minimalmodbus  to download the minimal modbus code
# --> https://github.com/SarathM1/modbus  for a example of IOmega CN7500
# Thank's to all for the job already done
#
# Documentation on IOmega CN7500 registers (and user manual) can be found on
# --> https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://assets.omega.com/manuals/M4704.pdf&ved=2ahUKEwiN0PSqxL2TAxU9hv0HHSuiGmsQFnoECBcQAQ&usg=AOvVaw0i6gxZrREGIsB6PgQ84Oua
# NB: date of download  26.03.2026
#
# The wrapper inherits of a OmegaCN7500 object that inherits itself of a minimalmodbus one.
# Added commands are:
#           ... to do
#
# version:  1.0
# Date:     26.3.2026
# AUthor:   Eric Studemann
#
#-----------------------------------------------------------------------

import serial
import time
from omegacn7500 import OmegaCN7500


def select_Com_Port():
    # Detection of available serial ports
    import serial.tools.list_ports as port_list
    ports = list(port_list.comports())
    for p in ports:
        print(str(ports.index(p)) + ' --> ' + p.device)

    # selection of the port
    comNo = int(input('Select the com number: '))
    selectedComPort = ports[comNo].device
    print('Selected COM Port : ' + selectedComPort)
    return(selectedComPort)

class IOmageCN7500Controller(OmegaCN7500):
    """
     Serial class controller for the IOmega CN7500 Controller
            This class relies on OmegaCN7500 (and implicitly on minimlamodbus and serial modules)
             to communicate with the instrument via RS485 serial transmission

     Current actions:
            - init - close the IOmega CN7500 instrument
            - set IOmega CN7500 target temperature for heating-cooling
            - start-stop mecanisms
    """

    def __init__(self):  # object constructor
        """ method called at object creation (implementation)
            Port and baudrate will be configured later
            Init object attributes

        Parameter
        ----------
            None

        """

        # init parent class by calling the parent constructor
        OmegaCN7500.__init__(self)

        # init object attributes
        #-----------------------
        # Firmware identifier and requested minimal version (fake ones !)
        self._requestedFirmwareIdentifier = "CN7500"
        self._requestedFirmwareVersion = "1.0"
        self._identification_string  = "CN7500"
        # hardware initialisation flag
        self._initialized = False


    # ================================================================
    # Serial configuration
    # ================================================================
    def set_communication_parameters(self):
        """
        Allow to set or change some serial internal parameters
        For CN7500 set baudrate to 9600 by default
        :return: none
        """
        print('\nDefault settings')
        print('Port       :',self.port)
        print('Bauderate  :',self.baudrate)
        print('Bytesize   :',self.bytesize)
        print('Parity     :',self.parity)
        print('Stopbits   :',self.stopbits)
        print('RTS-CTS    :',self.rtscts)
        print('TimeOut (read):',self.timeout)
        print('Inter byte TimeOut :', self.inter_byte_timeout)

        self.baudrate = 9600
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.rtscts = True
        self.timeout = 1.0              # 1.0 instead of 0.5 because communication can be slow
        self.inter_byte_timeout = 1.0   # 1.0 instead of 0.5 because communication can be slow

        print('\nSerial settings')
        print('Port       :',self.port)
        print('Bauderate  :',self.baudrate)
        print('Bytesize   :',self.bytesize)
        print('Parity     :',self.parity)
        print('Stopbits   :',self.stopbits)
        print('RTS-CTS    :', self.rtscts)
        print('TimeOut (read):', self.timeout)
        print('Inter byte TimeOut :', self.inter_byte_timeout)

    def set_baudrate(self, new_baudrate):
        """
        Set the baudrate for serial communication
        :param new_baudrate:
        :return: none
        """
        self.baudrate = new_baudrate

    #================================================================
    # Communication functions part
    #================================================================


    def close_communication(self):
        """
        Close serial port
        :return: none
        """
        to do ... self.close()

    # ======================================================================
    # Redefine the IsInitialized method regarding the TMS92 instrument used
    # ======================================================================
    def IsInitialized(self):
         """
         Do not Check if the controller is initialized by
         comparing the identification string and what it should be
         but force the retrun value to True (no identification string in TMS92)
         return: False or True
         """
         to do ...
         name = self.get_identification_string()
         # name = "TMS92"
         if self._requestedFirmwareIdentifier in name:
             self._initialized = True
         else:
             self._initialized = False
         return self._initialized

    # ================================================================
    # Redefine get_identification_string (not available in TMS_92)
    # ================================================================
    def get_identification_string(self):
        """
        Get the firmware name or identification string
        return: identification string
        """
        to do ...
        return self._identification_string

    def get_firmware_version(self) -> str:
        """
        Get the firmware version of the TMS_92
        :return: firmware version
        """
        # To simulate a answer (for compatibility with other Chiphy controllers)
        to do ...
        return self._requestedFirmwareVersion

    def get_temperature(self):
        """
        Get the temperature of the Linkam TMS92
        'T' command
        -----------
        In answer to the ‘T’ command the current status and temperature information is returned in the form of
        the 11 byte string detailed below :
        Byte 0  Status byte SB1     Information about what the programmer is currently doing
        Byte 1  Error byte EB1      Indicates sources of errors in the programmer
        Byte 2  Pump byte PB1       Current speed of the LNP Cooling Unit
        Byte 3  Gen status GS1      Used by the CSS 450 or the MDS 600 unit for status information
        Byte 4  Not used
        Byte 5  Not used
        Byte 6  MSB         ----|   Temperature *10
        Byte 7                  |   sent as
        Byte 8                  |   a signed integer ASCII
        Byte 9  LSB         ----|   hex value
        Byte 10 Carriage Return

        Temperature Information
        -----------------------
        To save sending the decimal point the temperature is multiplied by 10. This value is converted to a signed
        integer value covering the range -1960 to 15000 as F858H to 3A98H. These are then transmitted as :
        MSB ‘F’ 46H     ‘3’     33H
            ‘8’ 38H     ‘A’     41H
            ‘5’ 35H     ‘9’     39H
        LSB ‘8’ 38H     ‘8’     38H

        Status Byte (SB1)
        ------------------
        Value   Function
        01H     Stopped

        20H     Cooling
        30H     Holding at the limit or limit reached end of a ramp
        40H     Holding the limit time
        50H     Holding the current temperature (used in heating/cooling for quick hold)

        Error Byte
        ----------
        Bit 0   Cooling rate too fast       Cooling rate cannot be maintained
        Bit 1   Open circuit                Stage not connected or sensor is open circuit
        Bit 2   Power surge                 Current protection has been set due to an overload
        Bit 3   No Exit 300                 TS 1500 tried to exit profile at a temperature >300° (Not allowed)
        Bit 4   Both stages                 TMS 92 has a TS 1500 and a THM stage connected (Not allowed)
        Bit 5   Link error                  Problems with the RS 232 data transmission
        Bit 6   NC
        Bit 7   1                           Default value

        Pump byte (PB1)
        ---------------
        Current pump speed in hex from 0 to 30 with the most significant bit set. The LNP only shows these speeds
        on the front panel LED’s by five bands, each one comprised of 6 speeds.
        Value       Function
        80H         Stopped
        81H         Minimum speed (Band 1 LED on the front panel of the LNP)
        9EH         Maximum speed (Band 5 LED on the front panel of the LNP)

        General status (GS1)
        --------------------
        Currently not used with our instrument

        :return: temperature in [°C] with information bytes
        """
        to do ...
        answer = self.treat_serial_cmd('T' + '\r', True)
        #print(self. receive_answer())
        return answer



    def set_limit(self, limit_value):
        """
        Set the target (limit) temperature in °C -value must be an integer !

        EXample: L1125\r --> sets the current limit to 125°C
        :return: none
        """
        #_limit = 50
        #cmd = "L1 "+str(limit_value)+"\r"
        to do ...
        self.treat_serial_cmd("L1 "+str(int(limit_value))+"\r", False)



    def start(self):
        """
        Start heating or cooling at the rate specified in R1 and to a limit set by L1
        :return: none
        """
        to do ...
        self.treat_serial_cmd("S\r", False)


    def heat(self):
        """
        Heat the stage
        Works only when regulation process on hold !
        :return: none
        """
        to do ...
        self.treat_serial_cmd("H\r", False)

    def cool(self):
        """
        Cool the stage
        Works only when regulation process on hold !
        :return: none
        """
        to do ...
        self.treat_serial_cmd("C\r", False)

    def stop(self):
        """
        Stop heating or cooling
        :return: none
        """
        to do ...
        self.treat_serial_cmd("E\r", False)

#==========================================================
# Main application part
#==========================================================

if __name__ == "__main__":

    # Press the green button in the gutter to run the script.
    print('Python Test Program IOmage CN7500 Controller')
    print('------------------------------------------\n')

    to
    do...

    # selection of a available com port
    selected_Com_Port = select_Com_Port()

    # init Linkam_TMS92 com object and open the port !
    TMS92 = TMS92Controller()
    TMS92.port = selected_Com_Port
    TMS92.baudrate = 19200

    # set com port parameters
    TMS92.set_communication_parameters()

    TMS92.open()

    # clear input and ouput buffers to start on clean buffers
    TMS92.reset_input_buffer()
    TMS92.reset_output_buffer()

    #===============================
    # TEST PART
    #===============================


    print('------------- LINKAM TMS 92 - TEST COMMUNICATION ---------------')

    input('Press Enter to get temperature')
    current_Temperature = TMS92.get_temperature()
    print(current_Temperature)

    print('Longueur')
    print(len(current_Temperature))
    for x in current_Temperature:
        print(x)


    rate_value = input('Input rate in °C/min')
    TMS92.set_rate(rate_value)
    limit_value = input('Input limit value in °C')
    TMS92.set_limit(limit_value)

    input('Press Enter to start controller')
    TMS92.start()

    input('Press Enter to get temperature')
    current_Temperature = TMS92.get_temperature()

    print(current_Temperature)

    for x in current_Temperature:
        print(x)

    input('Press Enter to set pump in manual mode')
    TMS92.set_pump('Manual')

    input('Press Enter to set pump speed to 1')
    TMS92.set_pump_speed(1)

    input('Press Enter to set pump speed to 0')
    TMS92.set_pump_speed(0)

    input('Press Enter to stop controller')
    TMS92.stop()


    TMS92.close()
