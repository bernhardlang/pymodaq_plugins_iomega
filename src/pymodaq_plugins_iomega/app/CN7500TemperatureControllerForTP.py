from qtpy import QtWidgets

from pymodaq_gui import utils as gutils
from pymodaq_utils.config import Config
from pymodaq_utils.logger import set_logger, get_module_name

# added
from pymodaq_gui.utils.dock import DockArea, Dock
from pymodaq.control_modules.daq_viewer import DAQ_Viewer
from pymodaq_gui.plotting.data_viewers.viewer0D import Viewer0D
from pymodaq.control_modules.daq_move import DAQ_Move


# todo: replace here *pymodaq_plugins_template* by your plugin package name
from pymodaq_plugins_iomega.utils import Config as PluginConfig

logger = set_logger(get_module_name(__file__))

main_config = Config()
plugin_config = PluginConfig()


# todo: modify the name of this class to reflect its application and change the name in the main
# method at the end of the script
class CustomAppCN7500TemperatureControllerForTP(gutils.CustomApp):

    # todo: if you wish to create custom Parameter and corresponding widgets. These will be
    # automatically added as children of self.settings. Morevover, the self.settings_tree will
    # render the widgets in a Qtree. If you wish to see it in your app, add is into a Dock
    params = [
                {'title': 'Regulation:', 'name': 'regulation', 'type': 'group', 'children': [
                    {'title': 'Setpoint:', 'name': 'CN7500_set_setpoint', 'type': 'float', 'value': 25, 'default': 25,
                    'min': 20, 'max': 50, 'tip': 'set the temperature setpoint'},
                    {'title': 'Run:', 'name': 'CN7500_run', 'type': 'led_push', 'value': False, 'default': False,
                    'tip': 'Turn the CN7500 regulation ON or OFF'}
                ]}
              ]

    def __init__(self, parent: gutils.DockArea):
        super().__init__(parent)

        self.detector = None
        self.actuator = None

        self.custom_CN7500_0DViewer = None

        self.CN7500_0DViewer    = None
        self.CN7500_Move        = None

        self.daq_Viewer_Area    = None
        self.daq_Move_Area      = None

        self.setup_ui()

    def setup_docks(self):
        """Mandatory method to be subclassed to setup the docks layout

        Examples
        --------
        #>>>self.docks['ADock'] = gutils.Dock('ADock name')
        #>>>self.dockarea.addDock(self.docks['ADock'])
        #>>>self.docks['AnotherDock'] = gutils.Dock('AnotherDock name')
        #>>>self.dockarea.addDock(self.docks['AnotherDock'''], 'bottom', self.docks['ADock'])

        See Also
        --------
        pyqtgraph.dockarea.Dock
        """
        # todo: create docks and add them here to hold your widgets
        # reminder, the attribute self.settings_tree will  render the widgets in a Qtree.
        # If you wish to see it in your app, add is into a Dock
        #  ----------------------- ----------------
        #  |  Custom Viewer Dock  | Setting Dock  |
        #  ----------------------- ----------------
        #  ------------------------
        #  | dockarea             |
        #  | 0DViewer Dock        |
        #  ------------------------
        #  ----------------
        #  |  dockarea     |
        #  |  Move Dock    |
        #  ----------------
        #

        # Custom Viewer Dock
        #--------------------
        self.docks['Custom_CN7500_Viewer'] = gutils.Dock('Custom_CN7500 Viewer')
        self.dockarea.addDock(self.docks['Custom_CN7500_Viewer'])              # add this dock to the dock area (windows)
        custom_CN7500_0DViewer_widget = QtWidgets.QWidget()                      # create a widget
        self.custom_CN7500_0DViewer = Viewer0D(custom_CN7500_0DViewer_widget)           # create a viewer1D with its widget as parent
        self.docks['Custom_CN7500_Viewer'].addWidget(custom_CN7500_0DViewer_widget)     # add this widget in the dock

        # Setting Dock
        # -------------
        self.docks['CN7500_Settings'] = gutils.Dock('CN7500 Settings')
        self.dockarea.addDock(self.docks['CN7500_Settings'], 'right', self.docks['Custom_CN7500_Viewer'])  # add this dock to the dock area (windows)
        # Add the settings tree
        self.docks['CN7500_Settings'].addWidget(self.settings_tree, row=0, col=0, colspan=2)  # rowspan=1,add the widget setting tree in

        # ----------------------------
        # A IOmega DockArea (Move)
        # ----------------------------
        # Dock area for IOmega CN7500  (NB: detected as a actuator ( daq_move_plugin) with the dashboard)
        self.daq_Move_Area = DockArea()
        self.actuator = DAQ_Move(self.daq_Move_Area,
                                 title='A IOmega Ctrl')

        # set its type to 'IOmega' actuator
        self.actuator.actuator = 'IOmega_CN7500'  # its identifier, its name (cf. via dashboard)
        # self.detector.daq_type = 'DAQ0D'  # spectro is a DAQ 0D
        # self.detector.detector = 'IOmega_CN7500'  # its identifier, its name (cf. via dashboard)

        # init the actuator and wait 1000ms for the completion
        self.actuator.init_hardware()  # init the hardware
        self.actuator.settings.child('main_settings', 'refresh_time').setValue(500)
        QtWidgets.QApplication.processEvents()


        # ----------------------------
        # A IOmega DockArea (0DViewer)
        # ----------------------------
        # Dock area for IOmega CN7500  (NB: detected as a detector (a daq_viewer_plugin) with the dashboard)
        self.daq_Viewer_Area = DockArea()
        self.detector = DAQ_Viewer(self.daq_Viewer_Area,
                                   title='CN7500 Viewer')

        # set its type to 'avantes' spectrometer
        self.detector.daq_type = 'DAQ0D'            # spectro is a DAQ 0D
        self.detector.detector = 'IOmega_CN7500'    # its identifier, its name (cf. via dashboard)

        # init the detector and wait 1000ms for the completion
        self.detector.init_hardware()           # init the hardware
        self.detector.settings.child('main_settings', 'refresh_time').setValue(500)
        QtWidgets.QApplication.processEvents()
        # QThread.msleep(1000)




        #self.docks['CN7500_daqMove'] = gutils.Dock('CN7500 daq move')
        #self.dockarea.addDock(self.docks['CN7500_daqMove'], 'right', self.docks['CN7500_daq0DViewer'])  # add this dock to the dock area (windows)
        #CN7500_Move_Widget = QtWidgets.QWidget()                                            # create a widget
        #self.CN7500_Move = DAQ_Move(CN7500_Move_Widget, title='DAQ CN7500 Ctrl - Move')     # create the daq_move with its name
        #self.CN7500_Move.actuator = 'IOmega_CN7500'                               # select the actuator of the daq_move
        #self.CN7500_Move.init_hardware()                                                   # init the actuator of the daq_move
        #self.docks['CN7500 daqMove'].addWidget(CN7500_Move_Widget)                             # add this widget in the dock

        #raise NotImplementedError

    def setup_actions(self):
        """Method where to create actions to be subclassed. Mandatory

        Examples
        --------
        #>>> self.add_action('quit', 'Quit', 'close2', "Quit program")
        #>>> self.add_action('grab', 'Grab', 'camera', "Grab from camera", checkable=True)
        #>>> self.add_action('load', 'Load', 'Open', "Load target file (.h5, .png, .jpg) or data from camera"
        #    , checkable=False)
        #>>> self.add_action('save', 'Save', 'SaveAs', "Save current data", checkable=False)

        See Also
        --------
        ActionManager.add_action
        """
        self.add_action('quit', 'Quit', 'close2', "Quit program")
        self.add_action('showCN75000DViewer', 'Show/hide', 'showCN75000DViewer', "Show or Hide DAQViewer", checkable=True,
                        toolbar=self.toolbar)
        self.add_action('showCN7500daqMove', 'Show/hide', 'showCN7500daqMove', "Show or Hide DAQMove", checkable=True,
                        toolbar=self.toolbar)

        #raise NotImplementedError(f'You have to define actions here')

    def connect_things(self):
        """Connect actions and/or other widgets signal to methods"""
        self.connect_action('quit', self.quit_function)
        self.connect_action('showCN75000DViewer', self.show_CN7500_0DViewer)
        self.connect_action('showCN7500daqMove', self.show_CN7500_daqMove)

        return
        #raise NotImplementedError

    def setup_menu(self, menubar: QtWidgets.QMenuBar = None):
        """Non mandatory method to be subclassed in order to create a menubar

        create menu for actions contained into the self._actions, for instance:

        Examples
        --------
        #>>>file_menu = menubar.addMenu('File')
        #>>>self.affect_to('load', file_menu)
        #>>>self.affect_to('save', file_menu)

        #>>>file_menu.addSeparator()
        #>>>self.affect_to('quit', file_menu)

        See Also
        --------
        pymodaq.utils.managers.action_manager.ActionManager
        """
        # todo create and populate menu using actions defined above in self.setup_actions
        file_menu = menubar.addMenu('File')
        self.affect_to('quit', file_menu)

        pass

    def value_changed(self, param):
        """ Actions to perform when one of the param's value in self.settings is changed from the
        user interface

        For instance:
        if param.name() == 'do_something':
            if param.value():
                print('Do something')
                self.settings.child('main_settings', 'something_done').setValue(False)

        Parameters
        ----------
        param: (Parameter) the parameter whose value just changed
        """
        pass


    def quit_function(self):
        # close all stuff that need to be
        self.detector.quit_fun()
        QtWidgets.QApplication.processEvents()
        self.mainwindow.close()

    def show_CN7500_0DViewer(self,status):
        self.daq_Viewer_Area.setVisible(status)

    def show_CN7500_daqMove(self, status):
        self.daq_Move_Area.setVisible(status)

def main():
    from pymodaq_gui.utils.utils import mkQApp
    app = mkQApp('CustomAppCN7500TemperatureControllerForTP')

    mainwindow = QtWidgets.QMainWindow()
    dockarea = gutils.DockArea()
    mainwindow.setCentralWidget(dockarea)

    # todo: change the name here to be the same as your app class
    prog = CustomAppCN7500TemperatureControllerForTP(dockarea)

    mainwindow.show()

    app.exec()


if __name__ == '__main__':
    main()
