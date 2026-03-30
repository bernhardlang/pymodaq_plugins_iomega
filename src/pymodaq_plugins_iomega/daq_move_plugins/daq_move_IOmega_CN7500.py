
from typing import Union, List, Dict
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          main, DataActuatorType, DataActuator)

from pymodaq_utils.utils import ThreadCommand  # object used to send info back to the main thread
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_iomega.hardware.IOmegaCN7500Controller import IOmegaCN7500Controller


class DAQ_Move_IOmega_CN7500(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.
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

    is_multiaxes = False  # for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names: Union[List[str], Dict[str, int]] = ['Axis1', 'Axis2']  # for your plugin: complete the list
    _controller_units: Union[str, List[str]] = '°C'  # for your plugin: put the correct unit here, it could be
    # a single str (the same one is applied to all axes) or a list of str (as much as the number of axes)
    _epsilon: Union[float, List[float]] = 0.1  # replace this by a value that is correct depending on your controller
    # it could be a single float of a list of float (as much as the number of axes)
    data_actuator_type = DataActuatorType.DataActuator  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType.float  (or entirely remove the line)

    params = [{'title': 'Communication:', 'name': 'serial', 'type': 'group', 'children': [
                {'title': 'Serial Port:', 'name': 'serial_port', 'type': 'list', 'limits': com_list}
              ]},

              {'title': 'Regulation:', 'name': 'regulation', 'type': 'group', 'children': [
                  {'title': 'Setpoint:', 'name': 'CN7500_set_setpoint', 'type': 'float', 'value': 25, 'default': 25, 'min': 20,
                   'max': 50, 'tip': 'set the temperature setpoint'},
                  {'title': 'Run:', 'name': 'CN7500_run', 'type': 'led_push', 'value': False, 'default': False,
                   'tip': 'Turn the CN7500 regulation ON or OFF'},
              ]}
              ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)
    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def ini_attributes(self):
        #  the type of the wrapper (and assign it to self.controller) you're going to use for easy autocompletion
        self.controller: IOmegaCN7500Controller = None

        # To declare here attributes you want/need to init with a default value
        pass

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = DataActuator(data=self.controller.get_temperature())
        pos = self.get_position_with_scaling(pos)
        return pos

    def user_condition_to_reach_target(self) -> bool:
        """ Implement a condition for exiting the polling mechanism and specifying that the
        target value has been reached

       Returns
        -------
        bool: if True, PyMoDAQ considers the target value has been reached
        """
        #  either delete this method if the usual polling is fine with you, but if need you can
        #  add here some other condition to be fullfilled either a completely new one or
        #  using or/and operations between the epsilon_bool and some other custom booleans
        #  for a usage example see DAQ_Move_brushlessMotor from the Thorlabs plugin
        return True

    def close(self):
        """Terminate the communication protocol"""
        self.controller.stop()
        self.controller.serial.close()
        self.settings.child('serial', 'serial_port').setOpts(readonly=False)
        self.settings.child('regulation', ).hide()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        # for your custom plugin
        # if param.name() == 'axis':
            # self.axis_unit = self.controller.your_method_to_get_correct_axis_unit()
            # do this only if you can and if the units are not known beforehand, for instance
            # if the motors connected to the controller are of different type (mm, µm, nm, , etc...)
            # see BrushlessDCMotor from the thorlabs plugin for an exemple

        if param.name() == 'serial_port':
            selected_COM_port = self.settings.child('serial', 'serial_port').value()

        elif param.name() == "CN7500_set_setpoint":
            setpointvalue = self.settings.child('regulation', 'CN7500_set_setpoint').value()
            self.controller.set_setpoint(setpointvalue)

        elif param.name() == "CN7500_run":
            if param.value():
                self.controller.start()
                self.settings.child('regulation', 'CN7500_run').setValue(True)
            else:
                self.controller.stop()
                self.settings.child('regulation', 'CN7500_run').setValue(False)

        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        # self.ini_stage_init(slave_controller=controller)  # will be useful when controller is slave

        selected_COM_port = self.settings.child('serial', 'serial_port').value()

        if self.is_master:  # is needed when controller is master
            self.controller = IOmegaCN7500Controller()      # arguments for instantiation!)

            self.controller.port = selected_COM_port
            self.controller.set_communication_parameters()
            self.controller.open_communication()

            initialized = self.controller.IsInitialized()
            info = "IOmega daq_move CN7500 initialized"
        else:
            self.ini_stage_init(slave_controller=controller)  # will be useful when controller is slave
            initialized = True

        if initialized:
            self.settings.child('serial', 'serial_port').setOpts(readonly=True)
            self.settings.child('regulation').show()
            # set the initial limit value
            setpointvalue = self.settings.child('regulation', 'CN7500_set_setpoint').value()
            self.controller.set_setpoint(setpointvalue)

        # initialized = self.controller.a_method_or_atttribute_to_check_if_init()  # todo
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  # if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        float_setpoint_value = float(value.value('°C'))
        self.settings.child('regulation', 'CN7500_set_setpoint').setValue(float_setpoint_value)
        self.controller.set_setpoint(float_setpoint_value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['set new setpoint temperature']))

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        # value = self.set_position_relative_with_scaling(value) not used ?

        float_setpoint_value = int(self.target_value.value('°C'))
        self.settings.child('regulation', 'CN7500_set_setpoint').setValue(float_setpoint_value)
        self.controller.set_setpoint(float_setpoint_value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['set a new setpoint temperature relative one']))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.set_setpoint(25)  # when writing your own plugin replace this line home = 25°C
        self.settings.child('regulation', 'CN7500_set_setpoint').setValue(25)
        self.emit_status(ThreadCommand('Update_Status', ['set a setpoint to room temperature']))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.controller.stop()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Stop temperature regulation']))


if __name__ == '__main__':
    main(__file__)
