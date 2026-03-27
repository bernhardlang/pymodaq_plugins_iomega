#!/usr/bin/env python3
import minimalmodbus
import serial


#instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1)  # port name, slave address (in decimal)
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1, minimalmodbus.MODE_ASCII, debug=True)
instrument.serial.port     = '/dev/ttyUSB0'             # this is the serial port name
instrument.serial.baudrate = 9600                       # Baud
instrument.serial.bytesize = 8
instrument.serial.parity   = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = 0.5                       # seconds

instrument.address         = 1                          # this is the slave address number
instrument.mode = minimalmodbus.MODE_ASCII              # rtu or ascii mode
instrument.clear_buffers_before_each_transaction = True

print(instrument)


## Read temperature (PV = ProcessValue) ##
temperature = instrument.read_register(0x1000, 1)  # Registernumber, number of decimals
print(temperature)

## Change temperature setpoint (SP) ##
NEW_TEMPERATURE = 35
instrument.write_register(0x1001, NEW_TEMPERATURE, 1)  # Registernumber, value, number of decimals for storage
