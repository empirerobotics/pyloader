"""
dynamixel.py

Originally by Mac Mason <mac@cs.duke.edu>
Modified for MX-64 by Anthony McNicoll <am859@cornell.edu>

Minimalistic Pythonic access to MX-64. This has been stripped down from
Mac Mason's original to only include MX-64 functions useful in Freeloader
operation.

There are two classes defined here; Response, which you probably don't care
about, and ServoController, which you almost certainly do. A ServoController
controls as many servos as you have plugged into a single port; each
function takes a servo ID as its first argument, and then the actual meat of
the instruction after that. See the individual function documentation for
details. This doesn't implement every single option provided by Dynamixels,
just the most common. Broadcast packets are not implemented.

This code is made available under a Creative Commons
Attribution-Noncommercial-Share-Alike 3.0 license. See
<http://creativecommons.org/licenses/by-nc-sa/3.0> for details. If you'd
like some other license, send Mac Mason an email.

Anthony McNicoll's modifications circa July 2014:
Packets are only accepted if they rigorously follow the expected format,
including a valid checksum. If not, the original request is re-sent up to
20 times. This modification is made with only speed commands and encoder
readings in mind. It is important for critical commands like stopping.
Several range checks were changed throught to accomodate MX-64 values.
Servo-mode commands for AX-12 (set degrees, etc) were removed.
"""

import serial, time

# The types of packets.
PING       = [0x01]
READ_DATA  = [0x02]
WRITE_DATA = [0x03]
REG_WRITE  = [0x04]
ACTION     = [0x05]
RESET      = [0x06]
SYNC_WRITE = [0x83]

# The various errors that might take place.
ERRORS = {64 : "Instruction",
          32 : "Overload",
          16 : "Checksum",
           8 : "Range",
           4 : "Overheating",
           2 : "AngleLimit",
           1 : "InputVoltage"}
           
def _Checksum(s):
  """Returns the Dynamixel checksum (~(ID + length + ...)) & 0xFF."""
  return (~sum(s)) & 0xFF

def _VerifyID(id):
  """Raises a ValueError if the id is not in valid range."""
  if not (0 <= id <= 0xFD):
    raise ValueError, "ID %d isn't legal!" % id

def _EnWire(v):
  """
  Convert an int to the on-wire (little-endian) format. Returns the
  list [lsbyte, msbyte]. Used to transmit 16-bit values.
  """
  if not 0 <= v <= 65535:
    raise ValueError, "EnWiring illegal value: %d" % v
  return [v & 255, v >> 8]

def _DeWire(v):
  """ Returns the 16-bit number in v, which should be the list [lsbyte, msbyte]"""
  return (v[1] << 8) + v[0]

class Response:
  """
  A response packet. Takes care of parsing the response, and figuring what (if
  any) errors have occurred. These will appear in the errors field, which is a
  list of strings, each of which is an element of ERRORS.values().
  """
  def __init__(self, data):
    """
    Data should be the result of a complete read from the serial port, as a
    list of ints. See ServoController.Interact().
    """
    self.errors = []
    if len(data) == 0 or data[0] != 0xFF or data[1] != 0xFF:
        self.errors.append("Bad header")
    if _Checksum(data[2:-1]) != data[-1]:
        self.errors.append("Bad checksum")
        
    self.data = data
    self.id, self.length = data[2:4]
    if len(self.errors) == []:
        for k in ERRORS.keys():
          if data[4] & k != 0:
            self.errors.append(ERRORS[k])
    self.parameters = self.data[5:-1]

  def __str__(self):
    """String representation only includes data."""
    return " ".join(map(hex, self.data))

  def Verify(self):
    """Raises a ValueError if any errors occurred on motor or in packet."""
    if len(self.errors) != 0:
      raise ValueError, "ERRORS: %s" % " ".join(self.errors)
    return self  # Syntactic sugar; lets us do return foo.Verify().

class ServoController:
  """
  Interface to a servo. Most of the real work happens in Interact(), which
  sends a packet and waits for a response. Note that this represents an 
  entire _collection_ of servos, not just a single servo: therefore, each 
  function takes a servo ID as its first argument, to specify the servo that 
  should get the command.
  """

  def __init__(self, portstring="/dev/ttyUSB0", baud=1000000, to=1):
    """
    portstring should be the port of the USB2Dynamixel or other serial adapter,
    in form 'COM17' for Windows or '/dev/ttyUSB0' for Unix. Baud is the baud
    rate at which the target Dynamixels are communicating. to is the timeout
    duration, after which a connection is determined to have failed.
    """
    try:
        self.portstring = portstring
        self.port = serial.Serial(self.portstring, baudrate=baud, timeout=to)
    except:
        raise ValueError("Unable to open COM port.")
    
  def Close(self):
    """Close the serial port."""
    if hasattr(self, 'port'):
      self.port.close()

  def __del__(self):
    """Make sure serial port is closed upon deleting."""
    self.Close()

  def Interact(self, id, packet):
    """
    Given an (assembled) packet, add the various extra bits, and transmit to
    servo at id. Returns the status packet as a Response. id must be in the
    range [0, 0xFD].

    Note that the payload should be a list of integers, suitable for passing
    to chr().

    This is the low-level communication function; you probably want to call 
    one of the other, more specific functions.
    """
    tries = 0
    while tries < 15:
        _VerifyID(id)
        P = [id, len(packet)+1] + packet
        self.port.write("".join(map(chr, [0xFF, 0xFF] + P + [_Checksum(P)])))
        self.port.flushInput()
        self.port.flush()
        
        # Wait for a valid packet to come in, with time-out.
        try:
            res = self.GetPacket(.005)
            out = Response(res).Verify()
            return out
        except ValueError as e:
            # Uncomment the line below to debug communication failures
            # print e
            tries += 1
    raise ValueError("Communication failure")

  def GetPacket(self, timeout):
    """
    This method carefully waits for bytes forming a response packet, and
    raises an informative ValueError if the incoming byte is not what it 
    should be - ie, the response packet has been lost.

    timeout is the maximum time that should be spend waiting on any 
    individual byte. At 9600 baud, this is theoretically 1.04ms.
    """
    # Wait for the start byte
    res = []
    byte = 0x00
    tries = 0
    while byte != 0xFF:
        tries += 1
        if self.ListenWithTimeout(1, timeout*5) or (tries > 20):
            raise ValueError("Timed out while waiting for 1st byte")
        byte = ord(self.port.read())
    res.append(byte)
    # Wait for the second start byte
    if self.ListenWithTimeout(1, timeout):
        raise ValueError("Timed out while waiting for 2nd byte")
    byte = ord(self.port.read())
    if byte != 0xFF:
        raise ValueError("Second byte was incorrect")
    res.append(byte)
    # Wait for the ID and length bytes
    if self.ListenWithTimeout(2, timeout*2):
        raise ValueError("Timed out while waiting for ID and length")
    res.append(ord(self.port.read()))
    len = ord(self.port.read())
    res.append(len)
    # Read as many bytes as indicated by length byte
    for i in range(len):
        if self.ListenWithTimeout(1, timeout*len):
            raise ValueError("Timed out while waiting for data byte")
        res.append(ord(self.port.read()))
    return res
      
  def ListenWithTimeout(self, num, timeout):
    """
    Waits for num bytes to be received, but not longer than timeout.
    Note this returns 1's and 0's in a funny way which makes it useful
    for if statements such as those in GetPacket."""
    start = time.time()
    while self.port.inWaiting() < num:
        if time.time() - start > timeout:
            return 1
    return 0
            
  def Reset(self, id):
    """
    Perform a reset on the servo. Note that this will reset the ID to 1, which
    could be messy if you have many servos plugged in.
    """
    _VerifyID(id)
    self.Interact(id, RESET).Verify()

  def GetPosition(self, id):
    """Return the current position of the servo as a 16-bit value."""
    _VerifyID(id)
    packet = READ_DATA + [0x24] + [2]
    res = self.Interact(id, packet).Verify()
    if len(res.parameters) != 2:
      raise ValueError, "GetPosition didn't get two parameters!"
    return _DeWire(res.parameters)

  def GetPositionDegrees(self, id):
    """Returns position in degrees for an MX-64"""
    return self.GetPosition(id) * (360.0 / 4096.0)

  def SetPosition(self, id, position):
    """Set servo id to be at a position from 0-4096 for MX-64."""
    _VerifyID(id)
    if not (0 <= position <= 4096):
      raise ValueError, "Invalid position!"
    packet = WRITE_DATA + [0x1e] + _EnWire(position)
    self.Interact(id, packet).Verify()

  def SetPositionDegrees(self, id, deg):
    """Set the position in degrees for a servo-mode MX-64."""
    if not 0 <= deg <= 360:
      raise ValueError, "%d is not a valid angle!" % deg
    self.SetPosition(id, int(4096.0/360 * deg))

  def SetID(self, id, nid):
    """
    Change the ID of a servo. Note that this is persistent; you may also be
    interested in Reset().
    """
    _VerifyID(id)
    if not 0 <= nid <= 253:
      raise ValueError, "%id is not a valid servo ID!" % nid
    packet = WRITE_DATA + [0x03] + [nid]
    self.Interact(id, packet).Verify()
  
  def GetMovingSpeed(self, id):
    """Get the moving speed. 0 means stopped for MX-64 in wheel mode."""
    _VerifyID(id)
    packet = READ_DATA + [0x20] + [2]
    Q = self.Interact(id, packet).Verify()
    if len(Q.parameters) != 2:
      raise ValueError, "GetMovingSpeed has the wrong return shape!"
    return _DeWire(Q.parameters)

  def SetMovingSpeed(self, id, speed):
    """Set the moving speed. 0 means stopped for MX-64 in wheel mode."""
    _VerifyID(id)
    if not 0 <= speed <= 2048:
      raise ValueError, "%d is not a valid moving speed!" % speed
    packet = WRITE_DATA + [0x20] + _EnWire(speed)
    self.Interact(id, packet).Verify()

  def Moving(self, id):
    """Return True if the servo is currently moving, False otherwise."""
    _VerifyID(id)
    packet = READ_DATA + [0x2e] + [1]
    Q = self.Interact(id, packet).Verify()
    return Q.parameters[0] == 1

if __name__ == "__main__":
  print "Can't run this directly."
  print "Use 'from dynamixel import ServoController'"