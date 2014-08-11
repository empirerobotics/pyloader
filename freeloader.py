"""
freeloader.py

Originally by Anthony McNicoll <am859@cornell.edu>
Based on work by John Amend and Nadia Cheng

Simple Python interface for working with a Freeloader machine.
It assumes you have a simple Freeloader consisting of the following:
    - An MX-64 Dynamixel, programmed with ID = 1
    - A Loadstar USB load cell interface

The rest can be specified by the user. Usage is described below.

This code is made available under a Creative Commons
Attribution-Noncommercial-Share-Alike 3.0 license. See
<http://creativecommons.org/licenses/by-nc-sa/3.0> for details.
"""

import time
import serial
import dynamixel
from serial.tools import list_ports

class FreeloaderError(Exception):
    """ 
    This is an exception for errors explicitly related to a Freeloader.
    There is nothing special about it. It is instantiated with a single
    argument, a message string, which can be accessed by FreeloaderError.msg.
    """
    def __init__(self, msg):
        self.msg = msg

class Freeloader():
    """
    This class represents a classic Freeloader machine with motor and load
    cell, and provides useful methods for interfacing with it.
    """

    def __init__(self, pitch = 10, gear_ratio = 2):
        """
        The user can optionally specify "pitch" or "gear_ratio" as options
        during instantiation if they have built a non-typical Freeloader.
        """
        self.dyna_online = 0
        self.cell_online = 0
        self.linpos = 0
        self.last_encoder = 9999
        self.mmpm2speed = float( pitch * (1/25.4) * gear_ratio * 7.95 )
        self.mm2enc = float( pitch * (1/25.4) * gear_ratio * 4096 )

    def connect_dynamixel(self, port, baudr):
        """ 
        Method to connect to the Dynamixel motor.
        port is a string of form "COM5" for Windows. 
        baudr is the baudrate provided as an int.
        If a Dynamixel is found, connect_dynamixel will return normally
        and the dyna_online attribute will be set to True.
        If not, a descriptive FreeloaderError will be raised.
        """
        # Make sure there is need to connect in first place
        if self.dyna_online:
            return
        # Connect
        try:
            self.dyna = dynamixel.ServoController(portstring = port, baud = baudr, to=1)
        except:
            raise FreeloaderError("Error opening Dynamixel serial port!")
        # Check to confirm there's a Dynamixel.
        try:
            res = self.dyna.GetPosition(1)
        except:
            raise FreeloaderError("Error communicating with Dynamixel!")
        # Send introductory commands to Dynamixel.
        self.dyna.SetMovingSpeed(1,0)
        self.dyna_online = True

    def connect_load(self, port, baudr, sps = 120):
        """ 
        Method to connect to the load cell interface.
        port is a string of form "COM5" for Windows. 
        baudr is the baudrate provided as an int.
        User can optionally set "sps" for lower, more accurate rate.
        If a load cell is found, connect_load will return normally
        and the cell_online attribute will be set to True.
        If not, a descriptive FreeloaderError will be raised.
        """
        # Make sure there is need to connect in first place
        if self.cell_online == 1:
            return
        # Establish connection to the load cell.
        # Set SPS to preferred value to confirm communication.
        try:
            self.cell = serial.Serial(port, baudr, timeout = .5)
        except:
            raise FreeloaderError("Error opening load cell port.")
        out = self.cell.write("SPS " + str(sps) + "\r")
        self.cell_online = 1
        # Lastly, make sure we received an appropriate response to SPS setting.
        try:
            self.wait_for_cell(12, .5)
            self.cell.flushInput()
        except FreeloaderError as fe:
            self.cell.close()
            self.cell_online = 0
            out = "Load connect failed: " + fe.msg
            raise FreeloaderError(out)

    def autoconnect(self, verbose = False, loadbaud = 9600, loadsps = 120, dynabaud = 1000000):
        """
        A convenient method which automatically finds the Dynamixel and load cell 
        on whatever port they may be connected to, if they are indeed available.
        To print status updates, call with verbose = True. 
        loadbaud, loadsps, and dynabaud are all options as well.
        Simply calling autoconnect() will scan with most common settings as above.
        Failure to connect in any case will raise a descriptive FreeloaderError.
        """
        if verbose:
            print "Scanning for load cell..."
        for port in list_ports.comports():
            try:
                self.connect_load(port[0], loadbaud, loadsps)
                if verbose:
                    print "Connected to load cell on " + port[0]
                break
            except FreeloaderError as fe:
                if verbose:
                    print "No load cell found on " + port[0] # + " (" + fe.msg + ")"
        if not self.cell_online:
            if verbose:
                print "Autoconnect failed to find a load cell."
            raise FreeloaderError("Could not find a load cell.")
        if verbose:
            print "Scanning for Dynamixel..."
        for port in list_ports.comports():
            try:
                self.connect_dynamixel(port[0], dynabaud)
                if verbose:
                    print"Connected to Dynamixel on " + port[0]
                break
            except FreeloaderError:
                if verbose:
                    print "No Dynamixel found on " + port[0]
        if not self.dyna_online:
            if verbose:
                print "Autoconnect failed to find a Dynamixel."
            self.disconnect()
            raise FreeloaderError("Could not find a Dynamixel.")
        
    def start_motor(self, speed, down = False):
        """
        Moves the motor up or down with a speed in mm/min.
        Ex: start_motor(60, down = True) moves down at 60 mm/min.
        """
        if speed > 70:
            speed = 70
        speed = int(round(speed*self.mmpm2speed))
        if self.dyna_online == 1:
            if not down:
                speed += 1024
            self.dyna.SetMovingSpeed(1,speed)
        else:
            raise FreeloaderError("Motor not connected, cannot move")

    def stop_motor(self):
        """Stops the motor."""
        if self.dyna_online == 1:
            self.dyna.SetMovingSpeed(1,0)
        else:
            raise FreeloaderError("Motor not connected, cannot stop")

    def get_raw_encoder(self):
        """Returns a raw encoder value from 0 to 4096. """
        if self.dyna_online == 1:
            return self.dyna.GetPosition(1)
        else:
            raise FreeloaderError("Motor not connected, cannot get position.")

    def get_linear_position(self):
        """
        A convenient but fragile function which returns the linear position
        of the crosshead itself, calculated from screw pitch, gear, etc.
        In order to be accurate, it must be continually called any time the 
        motor is in motion, at a rate greater than twice per revolution.
        Calling it too infrequently will cause incorrect overflow compensation.
        """
        if self.last_encoder == 9999:
            self.last_encoder = self.get_raw_encoder()
            return 0
        current_encoder = self.get_raw_encoder()
        if abs(self.last_encoder - current_encoder) > 2048:      # ie, overflow
            if current_encoder < self.last_encoder:
                difference = self.last_encoder - current_encoder - 4096
            else:
                difference = self.last_encoder - current_encoder + 4096
        else:
            difference = self.last_encoder - current_encoder
        self.last_encoder = current_encoder
        self.linpos += difference/self.mm2enc
        return self.linpos

    def reset_linear_position(self):
        """ Resets the linear position tracker to zero."""
        self.linpos = 0
        self.last_encoder = 9999

    def wait_for_cell(self, len, timeout):
        """
        Method which waits until load cell returns message of len bytes.
        If it waits for longer than timeout, a FreeloaderError is raised.
        """
        if self.cell_online == 1:
            elapsed = 0
            start = time.time()
            while (self.cell.inWaiting() < len) and (elapsed <= timeout):
                elapsed = time.time() - start
            if elapsed > timeout:
                msg = "Load cell response timed out with " + str(self.cell.inWaiting())
                msg += " bytes after " + str(round(elapsed,3)) + " seconds."
                raise FreeloaderError(msg)
        else:
            raise FreeloaderError("Load cell not connected, cannot wait on.")

    def read_raw_cell(self):
        """Reads a load cell response in raw form (string with return and newline)"""
        if self.cell_online == 1:
            out = ""
            while self.cell.inWaiting() > 0:
                out += self.cell.read()
            return out
        else:
            raise FreeloaderError("Load cell not connected, cannot read.")

    def read_cell(self):
        """Read a load cell response and returns as a float in lbs."""
        if self.cell_online == 1:
            self.cell.write("W\r")
            self.wait_for_cell(14, .5)
            out = self.read_raw_cell()
            return float(out.split()[0])
        else:
            raise FreeloaderError("Load cell not connected, cannot read.")

    def tare_cell(self):
        """Send the TARE command to the load cell."""
        if self.cell_online == 1:
            self.cell.write("TARE\r")
            self.wait_for_cell(7, .5)
            self.cell.flushInput()
        else:
            raise FreeloaderError("Load cell not connected, cannot tare.")

    def disconnect(self):
        """Safely disconnects everything which is connected."""
        if self.cell_online == 1:
            self.cell.close()
            self.cell_online = 0
        if self.dyna_online == 1:
            self.stop_motor()
            self.dyna.Close()
            self.dyna_online = 0


if __name__ == '__main__':
    print "This is a module to be imported into a program."
    print "Since you tried to run it directly, it will try to find a machine."

    try:
        fl = Freeloader()
        print "Connecting..."
        fl.autoconnect(verbose = True)
        print "Connected to machine successfully."
        print "Disconnecting..."
        fl.disconnect()
    except FreeloaderError as fe:
        pass # Because verbose is on, we already have info.