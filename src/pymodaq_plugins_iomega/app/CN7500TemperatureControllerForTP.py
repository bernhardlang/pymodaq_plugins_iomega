from qtpy import QtWidgets

from pymodaq_gui import utils as gutils
from pymodaq_utils.config import Config
from pymodaq_utils.logger import set_logger, get_module_name

# added
from pymodaq_gui.utils.dock import DockArea, Dock
from pymodaq.control_modules.daq_viewer import DAQ_Viewer
from pymodaq_gui.plotting.data_viewers.viewer0D import Viewer0D
from pymodaq.control_modules.daq_move import DAQ_Move
from pymodaq_gui.utils.widgets.lcd import LCD
from pymodaq.utils.data import DataToExport
import numpy as np
from pymodaq_gui.utils.widgets import QLED, SpinBox
from PyQt6.QtWidgets import *

#from PyQt5 import QtWidgets
#from PyQt5.QtWidgets import *
#from PyQt5.QtCore import QTimer, QTime
#from PyQt5.QtGui import *
#from PyQt5.QtCore import Qt

#from PyQt6.QtGui import QFont
#from PyQt6.QtCore import Qt
#from PyQt6.QtGui import *
#from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt


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

        self.raw_data                = None

        self.current_temperature_display    = None
        self.target_temperature             = None
        self.lcd_current_temperature        = None
        self.lcd_target_temperature         = None

        self.setPointSelection  = None
        self.running_led        = None
        self.startBtn           = None
        self.stopBtn            = None

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
        #
        #                 Main DockArea
        #  ----------------------- ----------------
        #  |                      | Setting Dock  |
        #  |                      |---------------|
        #  |                      | Current Temp  |
        #  |  Custom Viewer Dock  |---------------|
        #  |                      | Target  Temp  |
        #  |                      |---------------|
        #  |                      | Out1 - Out 2  |
        #  ----------------------- ----------------
        #
        #  ------------------------
        #  | dockarea             |
        #  | 0DViewer Dock        |
        #  ------------------------
        #
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

        # TEST Dock
        # -------------

        # Set Point Selection
        self.setPointSelection = SpinBox(font_size=64)      # set default text label


        # LED indicator
        self.running_led = QLED('Indicator')
        self.running_led.scale(2)
        self.running_led.set_as_false()


        # buttons relative to Timer
        self.startBtn = QPushButton('Start')
        self.startBtn.setStyleSheet("background-color: green")
        self.stopBtn = QPushButton('Stop')
        self.stopBtn.setStyleSheet("background-color: red")


        self.docks['CN7500_Test'] = gutils.Dock('CN7500 Test')
        self.dockarea.addDock(self.docks['CN7500_Test'], 'right',
                              self.docks['Custom_CN7500_Viewer'])  # add this dock to the dock area (windows)
        # Add the differents widgets in the dock
        self.docks['CN7500_Test'].addWidget(self.setPointSelection, row=0, col=0,
                                                colspan=2)  # rowspan=1,add the widget setting tree in
        self.docks['CN7500_Test'].addWidget(self.running_led, row=1, col=0,
                                            colspan=2)  # rowspan=1,add the widget setting tree in
        self.docks['CN7500_Test'].addWidget(self.stopBtn, row=2, col=1,
                                            colspan=2)  # rowspan=1,add the widget setting tree in
        self.docks['CN7500_Test'].addWidget(self.running_led, row=2, col=2,
                                            colspan=2)  # rowspan=1,add the widget setting tree in

        # Setting Dock
        # -------------

        self.docks['CN7500_Settings'] = gutils.Dock('CN7500 Settings')
        self.dockarea.addDock(self.docks['CN7500_Settings'], 'right', self.docks['Custom_CN7500_Viewer'])  # add this dock to the dock area (windows)
        # Add the settings tree
        self.docks['CN7500_Settings'].addWidget(self.settings_tree, row=0, col=0, colspan=2)  # rowspan=1,add the widget setting tree in





        # Display current temperature Dock
        # -----------------------------
        dock_current_temperature = Dock('Current Temperature', size=(200, 200))
        self.dockarea.addDock(dock_current_temperature, 'bottom', self.docks['CN7500_Settings'])
        self.current_temperature_display = QtWidgets.QLabel()
        dock_current_temperature.addWidget(self.current_temperature_display)

        # set apparence (color...)
        #font = QFont('Helvetica', 80)  # set font and its size
        self.current_temperature_display.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)

        #self.current_temperature_display.setFont(font)
        self.current_temperature_display.setAutoFillBackground(True)  # to enable background color
        palette_0 = QPalette()  # create a palette
        palette_0.setColor(QPalette.Window, Qt.green)  # set background color
        palette_0.setColor(QPalette.WindowText, Qt.white)  # set text color


        self.current_temperature_display.setAlignment(Qt.AlignCenter)

        self.current_temperature_display.setPalette(palette_0)  # add the palette to the label
        #self.current_temperature_display.setFont(font)  # add font to the label
        self.current_temperature_display.setStyleSheet("color:green; background-color: black")
        self.current_temperature_display.setText('--.-')





        # target temperature Dock
        # ----------------------------
        dock_target_temperature = Dock('Target Temperature', size=(200, 200))
        self.dockarea.addDock(dock_target_temperature, 'bottom', self.docks['CN7500_Settings'])
        self.target_temperature = QtWidgets.QDoubleSpinBox(value=10,maximum=100,minimum=0,singleStep=5)
        dock_target_temperature.addWidget(self.target_temperature)

        # set apparence (color...)
        font = QFont('Helvetica', 80)  # set font and its size
        self.target_temperature.setDecimals(1)
        self.target_temperature.setRange(0.0, 50.0)
        self.target_temperature.setSingleStep(5)

        self.target_temperature.setFont(font)
        self.target_temperature.setAutoFillBackground(True)  # to enable background color
        #palette_0 = self.target_temperature.palette()
        #palette_0.setColor(QPalette.Window, Qt.red)  # set background color
        #palette_0.setColor(QPalette.WindowText, Qt.white)  # set text color

        self.target_temperature.setAlignment(Qt.AlignCenter)

        #self.target_temperature.setPalette(palette_0)  # add the palette to the label
        self.target_temperature.setFont(font)  # add font to the label
        #self.target_temperature.setStyleSheet("color:blue;"
        #                                      "background-color: black;"
        #                                      "QDoubleSpinBox:up-button { width: 40px; };"
        #                                      "QDoubleSpinBox:down-button { width: 40px; }"
        #                                      )
        self.target_temperature.setStyleSheet("color:blue;"
                                              "background-color: black;")
        self.target_temperature.setValue(12)

        """
        # LCD current temperature Dock
        # -----------------------------
        dock_lcd_current_temperature = Dock('Current Temperature', size=(200, 200))
        self.dockarea.addDock(dock_lcd_current_temperature, 'bottom', self.docks['CN7500_Settings'])
        lcd_widget_current_temperature = QtWidgets.QWidget()
        dock_lcd_current_temperature.addWidget(lcd_widget_current_temperature)
        self.lcd_current_temperature = LCD(lcd_widget_current_temperature, Nvals=1, digits=4, labels=['Current Temperature'])
        self.lcd_current_temperature.viewer0D.setVisible(False)

        # set apparence (color...)
        font = QFont('Helvetica', 32)  # set font and its size
        self.lcd_current_temperature.parent.setFont(font)
        self.lcd_current_temperature.parent.setAutoFillBackground(True)  # to enable background color
        lcd_palette_1 = self.lcd_current_temperature.parent.palette()
        lcd_palette_1.setColor(QPalette.Window, Qt.green)  # set background color
        lcd_palette_1.setColor(QPalette.WindowText, Qt.white)  # set text color

        self.lcd_current_temperature.parent.setPalette(lcd_palette_1)  # add the palette to the label
        self.lcd_current_temperature.parent.setFont(font)  # add font to the label
        self.lcd_current_temperature.parent.setStyleSheet("color:green; background-color: black")


        # LCD target temperature Dock
        # ----------------------------
        
        dock_lcd_target_temperature = Dock('Target Temperature', size=(200, 200))
        self.dockarea.addDock(dock_lcd_target_temperature, 'bottom', dock_lcd_current_temperature)
        lcd_widget_target_temperature = QtWidgets.QWidget()
        dock_lcd_target_temperature.addWidget(lcd_widget_target_temperature)
        self.lcd_target_temperature = LCD(lcd_widget_target_temperature, Nvals=1, digits=4, labels=['Target Temperature'])
        self.lcd_target_temperature.viewer0D.setVisible(False)
        # set apparence (color...)
        self.lcd_target_temperature.parent.setStyleSheet("color:red; background-color: black")
        self.lcd_target_temperature.digits = 4
        """

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

        # ----------------------------
        # A IOmega DockArea (Move)
        # ----------------------------

        # Dock area for IOmega CN7500  (NB: detected as a actuator (daq_move_plugin) with the dashboard)
        #self.daq_Move_Area = DockArea()
        self.daq_move_widget = QtWidgets.QWidget()
        self.actuator = DAQ_Move(self.daq_move_widget, ui_identifier='Original',
                                 title='A IOmega Ctrl')

        #self.actuator = DAQ_Move(self.daq_Move_Area, ui_identifier='Original',
        #                         title='A IOmega Ctrl')

        # set its type to 'IOmega' actuator
        self.actuator.actuator = 'IOmega_CN7500'  # its identifier, its name (cf. via dashboard)
        self.detector.daq_type = 'DAQ0D'  # spectro is a DAQ 0D
        self.detector.detector = 'IOmega_CN7500'  # its identifier, its name (cf. via dashboard)

        # init the actuator and wait 1000ms for the completion
        # self.actuator.init_hardware()  # init the hardware
        # self.actuator.settings.child('main_settings', 'refresh_time').setValue(500)
        # QtWidgets.QApplication.processEvents()


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
        self.add_action('showCN75000DViewer', 'Viewer Show/hide', 'showCN75000DViewer', "Show or Hide DAQViewer", checkable=True,
                        toolbar=self.toolbar)
        self.add_action('showCN7500daqMove', 'Ctrl Show/hide', 'showCN7500daqMove', "Show or Hide DAQMove", checkable=True,
                        toolbar=self.toolbar)

        #raise NotImplementedError(f'You have to define actions here')

    def connect_things(self):
        """Connect actions and/or other widgets signal to methods"""
        self.connect_action('quit', self.quit_function)
        self.connect_action('showCN75000DViewer', self.show_CN7500_0DViewer)
        self.connect_action('showCN7500daqMove', self.show_CN7500_daqMove)

        self.detector.grab_done_signal.connect(self.show_data)
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

    def show_data(self, data: DataToExport):
        """
        do stuff with data from the detector if its grab_done_signal has been connected
        Parameters
        ----------
        data: DataToExport
        """
        #self.raw_data = data
        #data0D = data.get_data_from_dim('Data0D')
        #data0D.data
        #x, y, dx, dy, phi = lbs.beam_size(dataD[0][0])

        #self.target_viewer.show_data(data2D[0])
        current_temperature = data[0][0]
        target_temperature = data[0][1]
        #np.array([0])=current_temperature
        self.current_temperature_display.setText("{:.1f}".format(current_temperature[0]))   # format float to xx.x
        self.target_temperature.setValue(target_temperature[0])             # format float to xx.x
        #self.lcd_current_temperature.setvalues([current_temperature])
        #self.lcd_target_temperature.setvalues([target_temperature])

    def quit_function(self):
        # close all stuff that need to be
        self.detector.quit_fun()
        QtWidgets.QApplication.processEvents()
        self.mainwindow.close()

    def show_CN7500_0DViewer(self,status):
        self.daq_Viewer_Area.setVisible(status)

    def show_CN7500_daqMove(self, status):
        #self.daq_Move_Area.setVisible(status)
        self.daq_move_widget.setVisible(status)

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
