pymodaq_plugins_iomega
########################

.. the following must be adapted to your developed package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_template.svg
   :target: https://pypi.org/project/pymodaq_plugins_template/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_template/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_iomega
   :alt: Publication Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_iomega/actions/workflows/Test.yml/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_iomega/actions/workflows/Test.yml


Authors
=======

* Eric Studemann  (eric.studemann@unige.ch)

.. if needed use this field

    Contributors
    ============

    * First Contributor
    * Other Contributors

.. if needed use this field

  Depending on the plugin type, delete/complete the fields below


Instruments
===========

This plugins can control a IOmega Temperature Controller CN7500

Actuators
+++++++++

* daq_move_IOmega.py: control of CN7500 IOmega temperature controller actuator

Viewer0D
++++++++

* daq_0Dviewer_IOmega.py: control of CN7500 IOmega temperature 0D detector


PID Models
==========


Extensions
==========


Installation instructions
=========================

* PyMoDAQ’s version: 5.x
* Operating system’s version: linux Debian 12, Windows 11
* What manufacturer’s drivers should be installed to make this plugin run?
* Install MinimalModbus to be able to use Modbus protocol
