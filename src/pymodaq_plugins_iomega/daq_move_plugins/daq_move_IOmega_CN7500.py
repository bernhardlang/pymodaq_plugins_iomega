import time
from typing import Union, List, Dict
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          main, DataActuatorType, DataActuator)

from pymodaq_utils.utils import ThreadCommand  # object used to send info back to the main thread
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_iomega.hardware.IOmegaCN7500Controller import IOmegaCN7500Controller, IOmegaStatus


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

    PID_Profil_list = [0, 1, 2, 3]
    Ctrl_Method_List = ['PID', 'ON/OFF', 'Manual', 'Program']
    Heating_Cooling_Ctrl_List = ['Heating', 'Cooling', 'Heating-Cooling', 'Cooling-Heating']

    is_multiaxes = False  # for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names: Union[List[str], Dict[str, int]] = ['Axis1', 'Axis2']  # for your plugin: complete the list
    _controller_units: Union[str, List[str]] = ['°C','°C']  # for your plugin: put the correct unit here, it could be
    # a single str (the same one is applied to all axes) or a list of str (as much as the number of axes)
    _epsilon: Union[float, List[float]] = 0.1  # replace this by a value that is correct depending on your controller
    # it could be a single float of a list of float (as much as the number of axes)
    data_actuator_type = DataActuatorType.DataActuator  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType.float  (or entirely remove the line)

    params = [{'title': 'Communication:', 'name': 'serial', 'type': 'group', 'children': [
                {'title': 'Serial Port:', 'name': 'serial_port', 'type': 'list', 'limits': com_list}
              ]},

              # Regulation
              {'title': 'Regulation:', 'name': 'regulation', 'type': 'group', 'children': [
                {'title': 'Setpoint:', 'name': 'CN7500_set_setpoint', 'type': 'float', 'value': 25, 'default': 25, 'min': -200,
                'max': 1000, 'tip': 'set the temperature setpoint'},
                {'title': 'Run:', 'name': 'CN7500_run', 'type': 'led_push', 'value': False, 'default': False,
                'tip': 'Turn the CN7500 regulation ON or OFF'}
              ]},

              # Status
              {'title': 'Status:', 'name': 'status', 'type': 'group', 'children': [
                  {'title': 'deg °C:', 'name': 'CN7500_status_unit', 'type': 'led', 'value': True, 'readonly': True, 'tip': '°C or F temperature unit'},
                  {'title': 'Out 1:', 'name': 'CN7500_status_Out1', 'type': 'led', 'value': False, 'readonly': True,  'tip': 'Output 1 is running'},
                  {'title': 'Out 2:', 'name': 'CN7500_status_Out2', 'type': 'led', 'value': False, 'readonly': True,  'tip': 'Output 2 is running'},
                  {'title': 'Auto Tune:', 'name': 'CN7500_status_AT', 'type': 'led', 'value': False, 'readonly': True,  'tip': 'Auto Tune is running'}
              ]},

              # CN7500 parameters
              {'title': 'CN7500 Parameters:', 'name': 'CN7500_Internal_Param', 'type': 'group', 'expanded': False, 'children': [

                # Modes parameters
                {'title': 'Modes Parameters:', 'name': 'CN7500_Modes_Param', 'type': 'group', 'expanded': False, 'children': [
                    {'title': 'Control_Modes', 'name': 'CN7500_Modes', 'type': 'list', 'limits': Ctrl_Method_List},
                    {'title': 'Auto Tune', 'name': 'Auto_Tune', 'type':'led_push', 'value': False, 'default': False,
                    'tip': 'Run Auto-tune process'},
                ]},

                # Temperature Range
                {'title': 'Temperature Range:', 'name': 'CN7500_Temperature_Range', 'type': 'group', 'expanded': False, 'children': [
                    {'title': 'Read:', 'name': 'Temperature_Range_read', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Read the temperature ranges parameters'},
                    {'title': 'Write:', 'name': 'Temperature_Range_write', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Write the temperature ranges parameters'},

                    {'title': 'Upper Temp Limit', 'name': 'Ctrl_param_Upper_Temp_Limit', 'type': 'float', 'value': 0,
                    'tip': 'Upper-limit of temperature range'},
                    {'title': 'Lower Temp Limit', 'name': 'Ctrl_param_Lower_Temp_Limit', 'type': 'float', 'value': 0,
                    'tip': 'Lower-limit of temperature range'}
                ]},

                # Control Cycle [s]
                {'title': 'Control Cycle[s]:', 'name': 'CN7500_Control_Cycle', 'type': 'group', 'expanded': False, 'children': [
                    {'title': 'Read:', 'name': 'Control_Cycles_read', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Read the control cycle parameters'},
                    {'title': 'Write:', 'name': 'Control_Cycles_write', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Write the control cycle parameters'},

                    {'title': '1st Group cycle', 'name': 'Ctrl_param_1st_Group_Cycle', 'type': 'float', 'value': 0,
                    'tip': '1st group of Heating/Cooling control cycle'},
                    {'title': '2nd Group cycle', 'name': 'Ctrl_param_2nd_Group_Cycle', 'type': 'float', 'value': 0,
                    'tip': '2nd group of Heating/Cooling control cycle'}
                ]},

                # PID parameters
                {'title': 'PID Parameters:', 'name': 'CN7500_PID_Param', 'type': 'group', 'expanded': False, 'children': [
                    {'title': 'Read:', 'name': 'PID_read', 'type': 'led_push', 'value': False, 'default': False,
                    'tip': 'Read the PID parameters'},
                    {'title': 'Write:', 'name': 'PID_write', 'type': 'led_push', 'value': False, 'default': False,
                    'tip': 'Write the PID parameters'},
                              
                    {'title': 'PID No:', 'name': 'PID_Profil_No', 'type': 'list', 'limits': PID_Profil_list,
                    'tip': 'PID Profil No'},
                    {'title': 'PID Svn:', 'name': 'PID_Svn', 'type': 'float', 'value': 0,
                    'tip': 'PID temperature setpoint'},
                    {'title': 'PID Pn:', 'name': 'PID_Pn', 'type': 'float', 'value': 0,
                    'tip': 'PID Proportional Band'},
                    {'title': 'PID In:', 'name': 'PID_In', 'type': 'int', 'value': 0,
                    'tip': 'PID Integral Time'},
                    {'title': 'PID Dn:', 'name': 'PID_Dn', 'type': 'int', 'value': 0,
                    'tip': 'PID Derivative Time'},
                    {'title': 'PID iofn:', 'name': 'PID_Iofn', 'type': 'float', 'value': 0,
                    'tip': 'PID Integral Deviation Setting'}
                ]},

                # Additionnal Control parameters
                {'title': 'Additionnal Ctrl Parameters:', 'name': 'CN7500_Additionnal_Ctrl_param', 'type': 'group',  'expanded': False, 'children': [
                    {'title': 'Read:', 'name': 'Additionnal_Ctrl_read', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Read the additionnal Control parameters'},
                    {'title': 'Write:', 'name': 'Additionnal_Ctrl_write', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Write the additionnal Control parameters'},

                    {'title': 'Pdof', 'name': 'Ctrl_param_Pdof', 'type': 'float', 'value': 0,
                    'tip': 'Pd Offset correction settings (only if PID mode and in=0'},
                    {'title': 'HtS', 'name': 'Ctrl_param_HtS', 'type': 'float', 'value': 0,
                    'tip': 'Heating hysteresis (differential) setting'},
                    {'title': 'CtS', 'name': 'Ctrl_param_CtS', 'type': 'float', 'value': 0,
                    'tip': 'Cooling hysteresis (differential) setting'},
                    {'title': 'Coeff', 'name': 'Ctrl_param_Coeff', 'type': 'float', 'value': 0,
                    'tip': 'Proportional band coefficient for output 2'},
                    {'title': 'DeAd', 'name': 'Ctrl_param_DeAd', 'type': 'float', 'value': 0,
                    'tip': 'Dead band'}
                ]},

                # System Configuration parameters
                {'title': 'System Configuration Parameters:', 'name': 'CN7500_System_Config_param', 'type': 'group', 'expanded': False, 'children': [
                    {'title': 'Read:', 'name': 'System_Config_read', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Read the additionnal Control parameters'},
                    {'title': 'Write:', 'name': 'System_Config_write', 'type': 'led_push', 'value': False, 'default': False,
                     'tip': 'Write the additionnal Control parameters'},

                    {'title': 'Communication Write Enable', 'name': 'Comm_Write_Enable', 'type': 'led_push', 'value': True, 'default': True,
                     'tip': 'Communication write-in selection: Enable or Disable'},
                    {'title': 'Setting Lock:', 'name': 'Setting_Lock_State', 'type': 'int', 'value': 0,
                     'tip': '0 : Normal, 1 : All setting lock, 11 : Lock others than SV value'},
                    {'title': 'Temperature Unit', 'name': 'Temperature_Unit_Deg_C', 'type': 'led_push', 'value': True, 'default': True,
                     'tip': 'Temperature Unit Selection: °C=On F=Off'},
                    {'title': 'Heating/Cooling control selection', 'name': 'H_C_Ctrl_Selection', 'type': 'list', 'limits': Heating_Cooling_Ctrl_List,
                     'tip': '0: Heating, 1: Cooling, 2: Heating/Cooling, 3: Cooling/Heating'},
                ]}

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
        """ Get the current value from the hardware with scaling conversion.
        In this case it is the current temperature
        Also gather status information and update setting status LEDs
        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = DataActuator(data=self.controller.get_Current_Temperature())
        pos = self.get_position_with_scaling(pos)

        # read status
        current_status = self.controller.get_status()
        CN75000IOmegaStatus = IOmegaStatus(current_status)

        if (CN75000IOmegaStatus.DEG_C in CN75000IOmegaStatus):
            self.settings.child('status', 'CN7500_status_unit').setValue(True)
        else:
            self.settings.child('status', 'CN7500_status_unit').setValue(False)

        if (CN75000IOmegaStatus.OUT1 in CN75000IOmegaStatus):
            self.settings.child('status', 'CN7500_status_Out1').setValue(True)
        else:
            self.settings.child('status', 'CN7500_status_Out1').setValue(False)

        if (CN75000IOmegaStatus.OUT2 in CN75000IOmegaStatus):
            self.settings.child('status', 'CN7500_status_Out2').setValue(True)
        else:
            self.settings.child('status', 'CN7500_status_Out2').setValue(False)

        if (CN75000IOmegaStatus.AT in CN75000IOmegaStatus):
            self.settings.child('status', 'CN7500_status_AT').setValue(True)
        else:
            self.settings.child('status', 'CN7500_status_AT').setValue(False)


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
            self.controller.set_TemperatureSetpoint(setpointvalue)

        elif param.name() == "CN7500_run":
            if param.value():
                self.controller.start()
                self.settings.child('regulation', 'CN7500_run').setValue(True)
            else:
                self.controller.stop()
                self.settings.child('regulation', 'CN7500_run').setValue(False)

        elif param.name() == "CN7500_Modes":
            # set the process mode -> to do
            mode = self.settings.child('CN7500_Internal_Param', 'CN7500_Modes_Param','CN7500_Modes').value()
            self.controller.set_control_mode(mode)

        elif param.name() == "Auto_Tune":
            if param.value():
                # set the auto tune mode only if Control Mode in PID mode
                if self.settings.child('CN7500_Internal_Param', 'CN7500_Modes_Param','CN7500_Modes').value() == 'PID':
                    self.settings.child('CN7500_Internal_Param', 'CN7500_Modes_Param','Auto_Tune').setValue(True)
                    self.controller.AutoTune(True)
            else:
                self.controller.AutoTune(False)
                self.settings.child('CN7500_Internal_Param', 'CN7500_Modes_Param','Auto_Tune').setValue(False)

        elif param.name() == "Temperature_Range_read":
            # check state button
            if param.value():
                # Get  temperature limits from controller
                Upper_Temp_Limit = self.controller.getUpperTemperatureLimit()
                Lower_Temp_Limit = self.controller.getLowerTemperatureLimit()
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_Temperature_Range', 'Ctrl_param_Upper_Temp_Limit').setValue(Upper_Temp_Limit)
                self.settings.child('CN7500_Internal_Param', 'CN7500_Temperature_Range', 'Ctrl_param_Lower_Temp_Limit').setValue(Lower_Temp_Limit)
                time.sleep(0.25)
                self.settings.child('CN7500_Internal_Param', 'CN7500_Temperature_Range', 'Temperature_Range_read').setValue(False)

                print('Temperature Range read')

        elif param.name() == "Temperature_Range_write":
            # check state button
            if param.value():
                Upper_temp = self.settings.child('CN7500_Internal_Param', 'CN7500_Temperature_Range', 'Ctrl_param_Upper_Temp_Limit').value()
                Lower_temp = self.settings.child('CN7500_Internal_Param', 'CN7500_Temperature_Range', 'Ctrl_param_Lower_Temp_Limit').value()
                self.controller.setUpperTemperatureLimit(Upper_temp)
                self.controller.setLowerTemperatureLimit(Lower_temp)
                time.sleep(0.25)
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_Temperature_Range', 'Temperature_Range_write').setValue(False)

                print('Temperature Range write')

        elif param.name() == "Control_Cycles_read":
            # check state button
            if param.value():
                # Get  control cycles from controller
                first_Group_Heating_Cooling_Cycle = self.controller.getFirst_Grp_Heating_Cooling_Cycle()
                second_Group_Heating_Cooling_Cycle = self.controller.getSecond_Grp_Heating_Cooling_Cycle()
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_Control_Cycle', 'Ctrl_param_1st_Group_Cycle').setValue(first_Group_Heating_Cooling_Cycle)
                self.settings.child('CN7500_Internal_Param', 'CN7500_Control_Cycle', 'Ctrl_param_2nd_Group_Cycle').setValue(second_Group_Heating_Cooling_Cycle)
                time.sleep(0.25)
                self.settings.child('CN7500_Internal_Param', 'CN7500_Control_Cycle', 'Control_Cycles_read').setValue(False)

                print('Control Cycles param read')

        elif param.name() == "Control_Cycles_write":
            # check state button
            if param.value():
                First_cycle = self.settings.child('CN7500_Internal_Param', 'CN7500_Control_Cycle',
                                                 'Ctrl_param_1st_Group_Cycle').value()
                Second_cycle = self.settings.child('CN7500_Internal_Param', 'CN7500_Control_Cycle',
                                                 'Ctrl_param_2nd_Group_Cycle').value()
                self.controller.setFirst_Grp_Heating_Cooling_Cycle(First_cycle)
                self.controller.setSecond_Grp_Heating_Cooling_Cycle(Second_cycle)
                time.sleep(0.25)
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_Control_Cycle',
                                    'Control_Cycles_write').setValue(False)
                print('Control Cycles param write')

        elif param.name() == "PID_read":
            # check state button
            if param.value():
                # Which PID Profil No ?
                PID_no = self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Profil_No').value()
                # Get PID parameters from controller
                PID_param = self.controller.get_PID_values(PID_no)
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Svn').setValue(PID_param["Svn"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Pn').setValue(PID_param["Pn"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_In').setValue(PID_param["in"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Dn').setValue(PID_param["dn"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Iofn').setValue(PID_param["iofn"])

                time.sleep(0.25)
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_read').setValue(False)

        elif param.name() == "PID_write":
            # check state button
            if param.value():
                # Which PID Profil No ?
                PID_no = self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Profil_No').value()
                # Get PID parameters from controller
                # PID_param = self.controller.get_PID_values(PID_no)
                # write PID parameters
                PID_values = {"PID_no": self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Profil_No').value(),
                              "Svn":    self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Svn').value(),
                              "Pn":     self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Pn').value(),
                              "in":     self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_In').value(),
                              "dn":     self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Dn').value(),
                              "iofn":   self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_Iofn').value()}

                self.controller.set_PID_values(PID_values)
                time.sleep(0.25)
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_PID_Param', 'PID_write').setValue(False)

                print ('PID param write')

        elif param.name() == "Additionnal_Ctrl_read":
            # todo
            # check state button
            if param.value():
                # Get Additionnal Control parameters from controller
                Additionnal_Ctrl_param = self.controller.get_Additionnal_Control_Parameters()
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_Pdof').setValue(Additionnal_Ctrl_param["Pdof"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_HtS').setValue(Additionnal_Ctrl_param["HtS"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_CtS').setValue(Additionnal_Ctrl_param["CtS"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_Coeff').setValue(Additionnal_Ctrl_param["Coeff"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_DeAd').setValue(Additionnal_Ctrl_param["dEAd"])

                time.sleep(0.25)
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Additionnal_Ctrl_read').setValue(False)
                print('Additionnal Ctr param read')

        elif param.name() == "Additionnal_Ctrl_write":
            # check state button
            if param.value():
                # write Additionnal Control parameters
                Additionnal_Ctrl_param = {
                    "Pdof":     self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_Pdof').value(),
                    "HtS":      self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_HtS').value(),
                    "CtS":      self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_CtS').value(),
                    "Coeff":    self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_Coeff').value(),
                    "dEAd":     self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Ctrl_param_DeAd').value()}

                self.controller.set_Additionnal_Control_Parameters(Additionnal_Ctrl_param)
                time.sleep(0.25)
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_Additionnal_Ctrl_param', 'Additionnal_Ctrl_write').setValue(False)

            print('Additionnal Ctr param write')

        elif param.name() == "System_Config_read":
            # check state button
            if param.value():
               # Get System Configuration parameters from controller
                System_Config_param = self.controller.get_System_Configuration_Parameters()
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'Comm_Write_Enable').setValue(System_Config_param["Comm_Enable"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'Setting_Lock_State').setValue(System_Config_param["Set_Lock_State"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'Temperature_Unit_Deg_C').setValue(System_Config_param["Temp_Unit"])
                self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'H_C_Ctrl_Selection').setValue(System_Config_param["Heat_Cool_Setting"])

                time.sleep(0.25)
                self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'System_Config_read').setValue(False)
                print('Additionnal Ctr param read')

        elif param.name() == "System_Config_write":
            # check state button
            if param.value():
                # write System Configuration parameters
                System_Config_param = {
                    "Comm_Enable":      self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'Comm_Write_Enable').value(),
                    "Set_Lock_State":   self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'Setting_Lock_State').value(),
                    "Temp_Unit":        self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'Temperature_Unit_Deg_C').value(),
                    "Heat_Cool_Setting":self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'H_C_Ctrl_Selection').value()}

                self.controller.set_System_Configuration_Parameters(System_Config_param)
                time.sleep(0.25)
                # Update GUI
                self.settings.child('CN7500_Internal_Param', 'CN7500_System_Config_param', 'System_Config_write').setValue(False)

            print('Additionnal Ctr param write')

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
            self.controller.set_TemperatureSetpoint(setpointvalue)

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
        self.controller.set_TemperatureSetpoint(float_setpoint_value)  # when writing your own plugin replace this line
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
        self.controller.set_TemperatureSetpoint(float_setpoint_value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['set a new setpoint temperature relative one']))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.set_TemperatureSetpoint(25)  # when writing your own plugin replace this line home = 25°C
        self.settings.child('regulation', 'CN7500_set_setpoint').setValue(25)
        self.emit_status(ThreadCommand('Update_Status', ['set a setpoint to room temperature']))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.controller.stop()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Stop temperature regulation']))


if __name__ == '__main__':
    main(__file__)
