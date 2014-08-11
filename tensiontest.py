"""
tensiontest.py

Written by Anthony McNicoll <am859@cornell.edu>

This class executes a simple tension test using the BasicTest class.

It illustrates that a short, procedural test can be written painlessly
simply by overriding the run_test() method, and illustrates how to do so.

Note the import statement:

from basictest import BasicTest, Freeloader, FreeloaderError

You need Freeloader to create a machine and connect to it.
You need FreeloaderError to catch any errors while connecting.
And you need BasicTest, which is the class you are extending.
"""

from basictest import BasicTest, Freeloader, FreeloaderError
import traceback

class TensionTest(BasicTest):
    """
    Write a new class with any name you want (here, TensionTest).
    It must inherit from BasicTest, which is done by putting BasicTest in parenthesis.
    """

    def run_test(self):
        """
        To override run_test(), simply write it as if it had never been
        defined before. Use commands from BasicTest. This does the following:

            - Ask user for speed and break detection force
            - Initialize data collection
            - Move up and collect until force is greater than break
            - Keep moving up and collect until force is less than break
            - Stop motor
            - Wait for user to remove test piece (keyboard input)
            - Move back down until position is less than original.
            - Write data to file with header.

        As you can see, there is no problem with using outside Python functions
        such as raw_input and print to communicate with the user at different
        points in the test.

        The most important thing to remember is that data is only collected during
        the collect_until and collect_until_keyboard methods, so one of these
        two should always be running if you want to be recording.
        """

        # PRE-TEST: USER INTERACTION, IF ANY
        linspd = int(raw_input("Enter linear speed in mm/min from 0 to 70: "))
        broken = float(raw_input("Enter break detect load: "))

        # TEST PROCESS - MOTOR MOVING, DATA COLLECTED
        print "Beginning test."
        self.initialize_data()
        self.fl.start_motor(linspd, down = False)
        self.collect_until("load", "greaterthan", broken)
        self.collect_until("load", "lessthan", broken)
        self.fl.stop_motor()

        # POST-TEST: USER INTERACTION, IF ANY, AND CLEANUP
        print "Please remove the test piece. Hit any key when ready."
        self.wait_for_keyboard()
        print "Returning to original position."
        self.fl.start_motor(linspd, down = True)
        self.wait_until("position", "lessthan", self.get_first_value("position"))
        self.fl.stop_motor()

        # DEFINE HEADER AND WRITE FILE
        h = "Speed setting (mm/min): " + str(linspd) + "\n"
        h += "User-specified break force (lbs): " + str(broken) + "\n"
        h += "Time,Displacement,Load\n"
        h += "sec,mm,lbs\n"
        self.write_file(h)


if __name__ == '__main__':
    """
    This is the main code, which runs when you double-click the file.
    To run the test, you need to do the following:
        - Instantiate a machine (Freeloader)
        - Connect the machine
        - Instantiate your test with the machine as argument
        - Call your test's run_test() method.
    If you want to be neat, you can include try...except statements as I did.
    """
    try:
        machine = Freeloader()
        machine.autoconnect()
        test = TensionTest(machine)
        test.run_test()
        test.fl.disconnect()
    except FreeloaderError as fe:
        print "Something went wrong during the test:"
        print fe.msg
        out = raw_input("Hit enter to exit program.")
    except:
        print "Unexpected code error!"
        out = raw_input("Hit enter to show exception.")
        traceback.print_exc()
        out = raw_input("Hit enter to exit program.")