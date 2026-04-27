import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from pymodaq_plugins_iomega.hardware.IOmegaCN7500Controller import IOmegaCN7500Controller


class DAQ_0DViewer_IOmega_CN7500(DAQ_Viewer_base):
    """ Instrument plugin class for a OD viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument,
    a IOmega CN7500 Temperature Controller

    Attributes:
    -----------
    controller: object IOmega CN7500 Temperature Controller
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
    """

    # Check the available serial COM port
    import serial.tools.list_ports as port_list
    ports = list(port_list.comports())
    com_list = []
    for p in ports:
        print('DAQ VIEW TMS92 ' + str(ports.index(p)) + ' --> ' + p.device)
        if p.device != '/dev/ttyS0':
            com_list.append(p.device)

    params = comon_parameters+[
        # elements to be added here as dicts in order to control your custom stage
        {'title': 'Communication:', 'name': 'serial', 'type': 'group', 'children': [
            {'title': 'Serial Port:', 'name': 'serial_port', 'type': 'list', 'limits': com_list}
        ]},
        {'title': 'Regulation:', 'name': 'regulation', 'type': 'group', 'children': [
            {'title': 'Setpoint:', 'name': 'CN7500_set_setpoint', 'type': 'float', 'value': 25, 'default': 25,
             'min': -100,
             'max': 200, 'tip': 'set the temperature setpoint'},
            {'title': 'Run:', 'name': 'CN7500_run', 'type': 'led_push', 'value': False, 'default': False,
             'tip': 'Turn the CN7500 regulation ON or OFF'},
        ]}

        ]

    def ini_attributes(self):
        #  the type of the wrapper (and assign it to self.controller) you're going to use for easy autocompletion
        self.controller: IOmegaCN7500Controller = None

        # To declare here attributes you want/need to init with a default value
        pass

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """

        if param.name() == 'serial_port':
            selected_COM_port = self.settings.child('serial', 'serial_port').value()

        elif param.name() == "CN7500_set_setpoint":
            setpointvalue = self.settings.child('regulation', 'CN7500_set_setpoint').value()
            self.controller.set_TemperatureSetpoint(setpointvalue)

        elif param.name() == "CN7500_run":
            if param.value():
                self.controller.start()
                self.settings.child('regulation', 'CN7500_run').setValue(True)
            else:
                self.controller.stop()
                self.settings.child('regulation', 'CN7500_run').setValue(False)

        else:
            pass

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        # in case of Slave
        # self.ini_detector_init(slave_controller=controller)

        selected_COM_port = self.settings.child('serial', 'serial_port').value()

        # self.ini_detector_init(slave_controller=controller)

        if self.is_master:
            self.controller = IOmegaCN7500Controller()  # instantiate you driver with whatever arguments are needed
            # set com port parameters
            self.controller.port = selected_COM_port
            self.controller.set_communication_parameters()
            self.controller.open_communication()

            initialized = self.controller.IsInitialized()

        else:
            self.controller = controller
            initialized = True

        # initialize viewers panel with the future type of data
        self.dte_signal_temp.emit(DataToExport(name='CN7500',
                                               data=[DataFromPlugins(name='CN7500',
                                                                    data=[np.array([0]), np.array([0]), np.array([0]), np.array([0])],
                                                                    dim='Data0D',
                                                                    labels=['Current Temperature', 'Setpoint Temperature', 'Out1', 'Out2'])]))

        if initialized:
            self.settings.child('serial', 'serial_port').setOpts(readonly=True)
            self.settings.child('regulation').show()
            # set the initial setpoint value
            setpointvalue = self.settings.child('regulation', 'CN7500_set_setpoint').value()
            self.controller.set_TemperatureSetpoint(setpointvalue)

        info = "IOmega CN7500 - Viewer initialization"
        # initialized = self.controller.a_method_or_atttribute_to_check_if_init()
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close_communication()
        self.settings.child('serial', 'serial_port').setOpts(readonly=False)
        self.settings.child('regulation', ).hide()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """

        # synchrone version (blocking function)
        # ata_tot = self.controller.your_method_to_start_a_grab_snap()
        currentSetPoint = self.controller.get_setpoint()
        currentProcessTemperatureValue = self.controller.get_Current_Temperature()
        PWM_Out1 = self.controller.get_Output_PWM_1()
        PWM_Out2 = self.controller.get_Output_PWM_2()
        data_tot = [np.array([currentProcessTemperatureValue]), np.array([currentSetPoint]), np.array([PWM_Out1]), np.array([PWM_Out2])]

        self.dte_signal.emit(DataToExport(name='CN7500',
                                          data=[DataFromPlugins(name='CN7500', data=data_tot,
                                                                dim='Data0D', labels=['Process Temperature', 'Setpoint Temperature', 'Out1', 'Out2'])]))
        #########################################################
        # asynchrone version (non-blocking function with callback)
        # self.controller.your_method_to_start_a_grab_snap(self.callback)  # when writing your own plugin replace this line
        #########################################################

    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        data_tot = self.controller.your_method_to_get_data_from_buffer()
        self.dte_signal.emit(DataToExport(name='myplugin',
                                          data=[DataFromPlugins(name='Mock1', data=data_tot,
                                                                dim='Data0D', labels=['dat0', 'data1'])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        self.controller.stop()
        self.emit_status(ThreadCommand('Update_Status', ['Stop grabbing data from CN7500']))
        return ''


if __name__ == '__main__':
    main(__file__)
