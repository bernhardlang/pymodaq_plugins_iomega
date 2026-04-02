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
#            select_Com_Port
#            get_firmware_version
#            set_PID
#            get_PID
#            AutoTune
#            getUpperTemperatureLimit
#            setUpperTemperatureLimit
#            getLowerTemperatureLimit
#            setLowerTemperatureLimit
#            getFirst_Grp_Heating_Cooling_Cycle
#            setFirst_Grp_Heating_Cooling_Cycle
#            getSecond_Grp_Heating_Cooling_Cycle
#            setSecond_Grp_Heating_Cooling_Cycle
#
# version:  1.0
# Date:     26.3.2026
# AUthor:   Eric Studemann
#
#-----------------------------------------------------------------------

import serial
import time
from pymodaq_plugins_iomega.hardware.omegacn7500 import OmegaCN7500
import minimalmodbus



def select_Com_Port() -> serial.Serial.port :
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

class IOmegaCN7500Controller(OmegaCN7500):
    """
     Serial class controller for the IOmega CN7500 Controller
            This class relies on OmegaCN7500 (and implicitly on minimalmodbus and serial modules)
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
        OmegaCN7500.__init__(self,'/dev/ttyUSB0', 1)

        # Init a minimalmodabus instrument object
        #instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1, minimalmodbus.MODE_ASCII, debug=True)

        self.serial.port = '/dev/ttyUSB0'  # this is the serial port name
        self.serial.baudrate = 9600  # Baud
        self.serial.bytesize = 8
        self.serial.parity = serial.PARITY_NONE
        self.serial.stopbits = 1
        self.serial.timeout = 0.5  # seconds

        self.address = 1  # this is the slave address number
        self.mode = minimalmodbus.MODE_ASCII  # rtu or ascii mode
        self.clear_buffers_before_each_transaction = True

        """
        instrument.serial.port = '/dev/ttyUSB0'  # this is the serial port name
        instrument.serial.baudrate = 9600  # Baud
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 0.5  # seconds

        instrument.address = 1  # this is the slave address number
        instrument.mode = minimalmodbus.MODE_ASCII  # rtu or ascii mode
        instrument.clear_buffers_before_each_transaction = True
        """

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
        print('Port       :',self.serial.port)
        print('Bauderate  :',self.serial.baudrate)
        print('Bytesize   :',self.serial.bytesize)
        print('Parity     :',self.serial.parity)
        print('Stopbits   :',self.serial.stopbits)
        print('TimeOut (read):',self.serial.timeout)

        self.serial.baudrate = 9600
        self.serial.bytesize = 8
        self.serial.parity = 'N'
        self.serial.stopbits = 1
        self.serial.timeout = 0.5             # could be increase to 1.0 for slow communication

        print('\nSerial settings')
        print('Port       :',self.serial.port)
        print('Bauderate  :',self.serial.baudrate)
        print('Bytesize   :',self.serial.bytesize)
        print('Parity     :',self.serial.parity)
        print('Stopbits   :',self.serial.stopbits)
        print('TimeOut (read):', self.serial.timeout)

    def set_baudrate(self, new_baudrate):
        """
        Set the baudrate for serial communication
        :param new_baudrate:
        :return: none
        """
        self.serial.baudrate = new_baudrate

    #================================================================
    # Communication functions part
    #================================================================

    def open_communication(self):
        """
        Open serial port
        :return: none
        """
        if not self.serial.is_open:
            self.serial.open()
        else:
            self.serial.close()
            self.serial.open()

    def close_communication(self):
        """
        Close serial port
        :return: none
        """
        self.serial.close()


    # ======================================================================
    # Redefine the IsInitialized method regarding the CN7500 instrument used
    # ======================================================================
    def IsInitialized(self):
         """
         Do not Check if the controller is initialized by
         comparing the identification string and what it should be
         but force the retrun value to True (no identification string in CN7500)
         return: False or True
         """
         name = self.get_identification_string()
         # name = "CN7500"
         if self._requestedFirmwareIdentifier in name:
             self._initialized = True
         else:
             self._initialized = False
         return self._initialized

    # ================================================================
    # Redefine get_identification_string (not available in CN7500)
    # ================================================================
    def get_identification_string(self):
        """
        Get the firmware name or identification string
        return: identification string
        """
        return self._identification_string

    def get_firmware_version(self) -> str:
        """
        Get the firmware version of the CN7500
        :return: firmware version
        """
        # To simulate a answer (for compatibility with other Chiphy controllers)
        # return self._requestedFirmwareVersion
        firmwareVersionHex = hex(self.read_register(0x102F))                    # integer value  ie. 512 -> 0x200
        versionStr = (firmwareVersionHex[2]) + '.' + (firmwareVersionHex[3])   # extraction version ie.2.0
        return versionStr    # return a string ie '2.0'

    def get_temperature(self):
        """
        Get the temperature of the CN7500
        :return: current temperature in [°C] or [F] regarding used unit
        """
        answer = self.get_pv()
        #print(self. receive_answer())
        return answer


    def get_setpointtemperature(self):
        """
        Get the set point (target) temperature in °C or [F]
        :return: set point temperature in [°C] or [F] regarding used unit
        """
        answer = self.get_setpoint()
        return answer


    def start(self):
        """
        Start heating or cooling
        :return: none
        """
        self.run()


    def heat(self, percent_value):
        """
        Heat the stage with a percent value that control the time
        during the heat is set ON.
        Works only when Control method is on Manual_Tuning
        Warning: Activate Output value read and write of Output 1 so
                 heat if configuration is done with output1 <-> heat
        input: percent_value (0 ..100)
        :return: none
        """
        # must multiple value by 10 beacause unit is set to 0.1% --> to do
        self.write_register(0x1010, percent_value)

    def cool(self, percent_value):
        """
        Cool the stage with a percent value that control the time
        during the cool is set ON.
        Works only when Control method is on Manual_Tuning
        Warning: Activate Output value read and write of Output 2 so
                 cool if configuration is done with output2 <-> cool
        input: percent_value (0 ..100)
        :return: none
        """
        # must multiple value by 10 beacause unit is set to 0.1% --> to do
        self.write_register(0x1011, percent_value)

    def get_PID_values(self, PID_Profil_No: int):
        """
        Get the PID parameters for PID Profil (0..3):
            Svn:    Target Set Value associated with each PID Profile
            Pn:     Proportional Band Setting associated with each PID
            in:     Integral time (reset time) associated with each PID
            dn:     Derivative time (rate time) associated with each PID
            iofn:   Integral Deviation Offset Correction associated with each PID
        :return: dict containing parameters
        """
        # Select the PID profil
        self.write_register(0x101C, value=PID_Profil_No)
        # Read Svn=set point value (only valid in available range; scale 0.1)
        Svn_value = self.read_register(0x101D, number_of_decimals=1, signed=True)
        # Read Pn = proportionnal band (0.1 ... 999.9)
        Pn_value = self.read_register(0x1009, number_of_decimals=1, signed=True)
        # Read in = integral time (0 ..  9999)
        in_value = self.read_register(0x100A, signed=True)
        # Read dn =  derivative time (0 .. 9999)
        dn_value = self.read_register(0x100B, signed=True)
        # Read iof = integral deviation settings (0 .. 100% unit 0.1%)
        iofn_value = self.read_register(0x100C, number_of_decimals=1, signed=True)
        PID_values = {"PID_no": PID_Profil_No,
                      "Svn":    Svn_value,
                      "Pn":     Pn_value,
                      "in":     in_value,
                      "dn":     dn_value,
                      "iofn":   iofn_value}
        print(PID_values)
        return PID_values

    def set_PID_values(self, PID_param: dict):
        """
        Set the PID parameters for PID Profil (0..3):
            Svn:    Target Set Value associated with each PID Profile
            Pn:     Proportional Band Setting associated with each PID
            in:     Integral time (reset time) associated with each PID
            dn:     Derivative time (rate time) associated with each PID
            iofn:   Integral Deviation Offset Correction associated with each PID
        :return:
        """
        # Select the PID profil
        self.write_register(0x101C, value=PID_param["PID_no"])
        # Write Svn=set point value (only valid in available range; scale 0.1)
        self.write_register(0x101D, value=PID_param["Svn"], number_of_decimals=1, signed=True)
        # Write Pn = propotionnal band (0.1 ... 999.9)
        self.write_register(0x1009, value=PID_param["Pn"], number_of_decimals=1, signed=True)
        # Write in = integral time (0 ..  9999)
        self.write_register(0x100A, value=PID_param["in"], signed=True)
        # Write dn =  dirivative time (0 .. 9999)
        self.write_register(0x100B, value=PID_param["dn"], signed=True)
        # Write iof = integral deviation settings (0 .. 100% unit 0.1%)
        self.write_register(0x100C, value=PID_param["iofn"], number_of_decimals=1, signed=True)


    def get_Additionnal_Control_Parameters(self):
        """
        Get the additionnal control parameters:
            Pdof:   PD Offset Correction Setting
            HtS:    Heating Hysteresis (Differential) Setting
            CtS:    Cooling Hysteresis (Differential) Setting.
            Coeff:  Proportional Band Coefficient.The setting of COEF when Dual Loop output control are used
            DeAd:   Dead Band
        :return: dict containing parameters
        """

        # Read Pdof=PD Offset Correction Setting. only available when control
        # mode is set to PID and integral time = 0. See Programming
        # and Operation of PID function for moving information. (0~100%, unit is 0.1%)
        Pdof_value = self.read_register(0x100D, number_of_decimals=1, signed=True)

        # Read HtS = Heating Hysteresis (Differential) Setting. Sets the value for the
        # amount of difference between the turn off point (set point) and
        # the turn on point. Figure A shows the output behavior for a
        # heating (reverse acting) application. Only available when
        # control mode set to on/off control. (0 ~ 9999)
        HtS_value = self.read_register(0x1010,  signed=True)

        # Read CtS = Cooling Hysteresis (Differential) Setting. Sets the value for the
        # amount of difference between the turn off point (set point) and
        # the turn on point. Figure A shows the output behavior for a
        # cooling (direct acting) application. Only available when control
        # mode set to on/off control. (0 ~ 9999)
        CtS_value = 10*self.read_register(0x1011, signed=True)

        # Read Coeff = Proportional Band Coefficient. Sets the value of the
        # proportional band for output 2. The proportional band of
        # output 2 is equal to the proportional band of output 1
        # multiplied by the proportional band coefficient. This parameter
        # is only available when the control mode is set to PID and Dual
        # Loop Output Control. (0.01 ~ 99.99)
        Coeff_value = self.read_register(0x100E, number_of_decimals=2, signed=True)

        # Read DeAd = Dead Band. The zone centered on the set point in which the
        # control is thought to be at the desired set level. The outputs
        # will be turned off at this point unless there is an integral
        # deviation offset or the dead band is negative. This parameter
        # is only shown when the control is set to Dual Loop Output
        # Control. (-999 ~ 9999)
        dEAd_value = self.read_register(0x100F, signed=True)

        Additionnal_Ctrl_Param_values = {"Pdof":   Pdof_value,
                                         "HtS":    HtS_value,
                                         "CtS":    CtS_value,
                                         "Coeff":  Coeff_value,
                                         "dEAd":   dEAd_value}

        print(Additionnal_Ctrl_Param_values)
        return Additionnal_Ctrl_Param_values

    def set_Additionnal_Control_Parameters(self, Additionnal_Ctrl_Param_values: dict):
        """
        Set the additionnal Control parameters:
            Pdof:   PD Offset Correction Setting
            HtS:    Heating Hysteresis (Differential) Setting
            CtS:    Cooling Hysteresis (Differential) Setting.
            Coeff:  Proportional Band Coefficient.The setting of COEF when Dual Loop output control are used
            DeAd:   Dead Band
        """
        # Write Pdof=PD Offset Correction Setting (0~100%, unit is 0.1%)
        self.write_register(0x100D, Additionnal_Ctrl_Param_values["Pdof"], number_of_decimals=1, signed=True)
        # Write HtS = Heating Hysteresis (Differential) Setting (0 ~ 9999)
        self.write_register(0x1010, Additionnal_Ctrl_Param_values["HtS"], signed=True)
        # Write CtS = Cooling Hysteresis (Differential) Setting (0 ~ 9999)
        self.write_register(0x1011, Additionnal_Ctrl_Param_values["CtS"], signed=True)
        # Write Coeff =  Proportional Band Coefficient (0.01 ~ 99.99)
        self.write_register(0x100E, Additionnal_Ctrl_Param_values["Coeff"], number_of_decimals=2, signed=True)
        # Write DeAd = Dead Band (-999 ~ 9999)
        self.write_register(0x100F, Additionnal_Ctrl_Param_values["dEAd"], signed=True)

    def AutoTune(self, State: bool):
        """
        Trun ON or OFF the AutoTune function
        :param State: True or False regarding the desired Autotune function state
        :return:
        """
        if State:
            self.write_bit(0x0813,1)
        else:
            self.write_bit(0x0813, 0)

    def getUpperTemperatureLimit(self):
        """
        Get the Upper temperature limit
        :return: the upper temperature limit
        """
        return self.read_register(0x1002, number_of_decimals=1, signed=True)

    def setUpperTemperatureLimit(self, Upper_Temp: float):
        """
        Set the Upper temperature limit (int)
        :return:
        """
        self.write_register(0x1002, Upper_Temp, number_of_decimals=1, signed=True)

    def getLowerTemperatureLimit(self):
        """
        Get the Upper temperature limit
        :return: the lower temperature limit
        """
        return self.read_register(0x1003, number_of_decimals=1, signed=True)

    def setLowerTemperatureLimit(self, Lower_Temp: float):
        """
        Set the Lower temperature limit (int)
        :return:
        """
        self.write_register(0x1003, Lower_Temp, number_of_decimals=1, signed=True)

    def getFirst_Grp_Heating_Cooling_Cycle(self):
        """
        Get the 1st group heating-cooling cycle in [s] (float)
        :return: 1st group heating-cooling cycle in [s]
        """
        return self.read_register(0x1007, 1, signed=True)

    def setFirst_Grp_Heating_Cooling_Cycle(self, first_cycle: float):
        """
        Set the 1st group heating-cooling cycle in [s] (float: min 0.5)
        """
        self.write_register(0x1007, first_cycle, number_of_decimals=1, signed=True)

    def getSecond_Grp_Heating_Cooling_Cycle(self):
        """
        Get the 2nd group heating-cooling cycle in [s] (float)
        :return: 2nd group heating-cooling cycle in [s]
        """
        return self.read_register(0x1008, 1, signed=True)

    def setSecond_Grp_Heating_Cooling_Cycle(self, second_cycle: float):
        """
        Set the 2nd group heating-cooling cycle in [s] (float: min 0.5)
        """
        self.write_register(0x1008, second_cycle, number_of_decimals=1, signed=True)

#==========================================================
# Main application part
#==========================================================

if __name__ == "__main__":

    # Press the green button in the gutter to run the script.
    print('Python Test Program IOmega CN7500 Controller')
    print('------------------------------------------\n')


    # selection of a available com port
    selected_Com_Port = select_Com_Port()

    # init CN7500 com object and open the port !
    CN7500 = IOmegaCN7500Controller()
    CN7500.port = selected_Com_Port
    CN7500.baudrate = 9600

    # set com port parameters
    CN7500.set_communication_parameters()

    #CN7500.serial.open()

    #===============================
    # TEST PART
    #===============================


    print('------------- IOMEGA CN75000 - TEST COMMUNICATION ---------------')

    input('Press Enter to get firmware version')
    version = CN7500.get_firmware_version()
    print(version)

    input('Press Enter to get temperature')
    current_Temperature = CN7500.get_temperature()
    print(current_Temperature)

    input('Press Enter to get set point value')
    set_point = CN7500.get_setpoint()
    print(set_point)

    new_set_point = input('Input set point value in °C')
    CN7500.set_setpoint(float(new_set_point))

    input('Press Enter to start controller')
    CN7500.start()

    input('Press Enter to get temperature')
    current_Temperature = CN7500.get_temperature()
    print(current_Temperature)

    input('Press Enter to stop controller')
    CN7500.stop()

    CN7500.serial.close()
