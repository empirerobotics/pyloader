"""
basictest.py

Originally by Anthony McNicoll <am859@cornell.edu>
Based on work by John Amend and Nadia Cheng

This is a class providing all the framework for conveniently writing
a test class for a Freeloader. It provides users a set of simple functions,
while still providing access to low-level Freeloader communication and the full
bag of Python tricks. It allows the test writer to be as straightforward or 
complex as they want.

To use this class, write another class of your choosing and specify this
class as a parent class. Then, override the run_test() method to define your
test. Read below for descriptions of the methods available to you.

This basic test assumes a simple Freeloader collecting time, load, and displacement.
To specify or collect more data, you will need to override get_datapoint() 
and call set_columns() before running the test.

For an example test class which uses this, see tensiontest.py.
"""

import sys, msvcrt, time, Tkinter, tkFileDialog
from freeloader import Freeloader, FreeloaderError

class BasicTest():
    """Represents a basic test and provides useful methods. Meant to be extended."""

    def __init__(self, machine):
        """
        BasicTest must be instantiated with a machine which is already connected.
        machine must be an instance of Freeloader or a class inheriting from Freeloader.
        """
        self.fl = machine

        # Attribute "fun" stores functions which can be accessed by string.
        # These are useful for the collect_until method.
        self.funs = {'lessthan': (lambda x, y: x<y), 'greaterthan': (lambda x, y: x>y)}

        # Attribute "col" stores the index at which various types of data
        # can be found in a datapoint, so the user doesn't have to remember.
        self.col = {'time': 0, 'position': 1, 'load': 2}

        # Collect zero data for the load
        self.load_zer = self.fl.read_cell()
    
    def set_columns(self, label_list):
        """
        If you would like to collect more than time, position, and load, you must
        specify the column labels for passing into get_last_value and get_first_value by
        calling this function with a list of strings in label_list., in order of columns.
        """
        self.col = {}
        for i in range(0,len(label_list)):
            self.col[label_list[i]] = i

    def exit_error(self, error):
        """Prompts before exiting, so user has time to read error."""
        print error
        self.fl.disconnect()
        out = raw_input("Hit enter to exit program.")
        sys.exit(0)

    def collect_data(self):
        """
        Collects time, position, and load from the Freeloader.
        If you would like to collect additional data, you must override
        this method and add to the returned list.
        """
        time_point = time.time() - self.start_time
        position_point = self.fl.get_linear_position()
        load_point = self.fl.read_cell() - self.load_zer
        return [time_point, position_point, load_point]

    def get_last_value(self, value):
        """
        Returns the most recently collected value of name "value".
        For example, get_last_value("load") returns the last collected load.
        """
        if not len(self.data):
            self.exit_error("Tried to access last point with no data collected.")
        return self.data[-1][self.col[value]]

    def get_first_value(self, value):
        """
        Returns the first collected value of name "value".
        For example, get_last_value("load") returns the initial load.
        """
        if not len(self.data):
            self.exit_error("Tried to access last point with no data collected.")
        return self.data[0][self.col[value]]

    def get_last_point(self):
        """Returns the most recently collected datapoint as a list."""
        if not len(self.data):
            self.exit_error("Tried to access last point with no data collected.")
        return self.data[-1]

    def get_first_point(self):
        """Returns the first collected datapoint."""
        if not len(self.data):
            self.exit_error("Tried to access first point with no data collected.")
        return self.data[0]

    def get_all_values(self, value):
        """Returns one column with label 'value'"""
        out = []
        for datum in self.data:
            out.append(datum[self.col[value]])
        return out

    def initialize_data(self):
        """Clears any stored data and sets reference time to 0."""
        self.start_time = time.time()
        self.data = [self.collect_data()]

    def run_test(self):
        """Main test routine. Must be overriden by user."""
        print "This is the basic template test. It does nothing. You must write a test class"
        print "which inherits from BasicTest in order to define an actual test."

    def collect_until(self, value, fun, threshold, rate = 1000000, verbose = True):
        """
        Important, magical function.
        Automatically constructs loop to collect data until either:
        value is "lessthan" or "greaterthan" threshold
        Keyboard is hit (ends test completely)
        For example, collect_until("load","greaterthan",10) will (predictably)
        continously collect data using the collect_data() method until load
        exceeds 10 lbs. 
        The rate option specifies sampling rate in Hz. With a 9600 baud Loadstar, this
        cannot exceed 30 Hz. The default, 1Mhz, simply means "as fast as possible."
        The verbose option prints the watched value and the threshold, so that the
        user can monitor progress themselves. This is left on by default as a safety
        feature, but can be muted by setting verbose = False.
        """
        try:
            loop_time = 1/rate
            while not self.funs[fun](self.get_last_value(value), threshold):
                loop_start = time.time()
                self.data.append(self.collect_data())
                if verbose:
                    print value + ": " + str(round(self.get_last_value(value),2)) + \
                        "\ttarget: " + fun + " " + str(threshold)
                while (time.time()-loop_start) < loop_time:
                    pass
                if msvcrt.kbhit():
                    msvcrt.getch()
                    self.fl.disconnect()
                    self.exit_error("Test terminated early by user.")
        except KeyError as ke:
            self.exit_error("An invalid column was asked for: " + str(ke))

    def collect_for(self, sec, rate = 1000000):
        """ 
        More convenient way of calling collect_until with time.
        The caveat is that the this function is only as accurate as
        the speed of the equipment. If it takes 30 ms collect a datapoint,
        and sec is 120 ms, collection may occur for up to 150 ms. Keep this
        in mind.
        """
        current_time = time.time() - self.start_time
        self.collect_until("time", "greaterthan", sec + current_time, rate = rate)

    def wait_until(self, value, fun, threshold, verbose = True):
        """
        See collect_until. Same operation, but no data is collected.
        It does still ask for data in order to check the end condition, but
        does not store it. This means position will remain accurate during wait.
        """
        localdat = self.collect_data()
        while not self.funs[fun](localdat[self.col[value]], threshold):
            localdat = self.collect_data()
            if verbose:
                print value + ": " + str(round(localdat[self.col[value]],2)) + \
                    "\ttarget: " + fun + " " + str(threshold)
            time.sleep(.01)
            if msvcrt.kbhit():
                msvcrt.getch()
                self.fl.disconnect()
                self.exit_error("Test terminated early by user.")

    def wait_for(self, sec):
        """
        Convenient version of wait_until for time only.
        It keeps track of time more accurately.
        Will keep position updated if motor is moving.
        """
        start = time.time()
        while time.time() - start < sec:   
            p = self.fl.get_linear_position()  # Keeps position accurate

    def collect_until_keyboard(self, rate = 1000000):
        """
        Collects data until user hits any key on the keyboard.
        The rate option specifies sampling rate in Hz. With a 9600 baud Loadstar, 
        this cannot exceed 30 Hz. The default, 1Mhz, simply means "as fast as possible."
        """
        loop_time = 1/rate
        while True:
            loop_start = time.time()
            self.data.append(self.collect_data())
            while (time.time()-loop_start) < loop_time:
                pass
            if msvcrt.kbhit():
                msvcrt.getch()
                return

    def wait_for_keyboard(self):
        """
        Machine continues to do whatever it was doing until user hits keyboard.
        Data is collected but discarded to keep position accurate.
        """
        while True:   
            p = self.fl.get_linear_position()  # Keeps position accurate
            if msvcrt.kbhit():
                msvcrt.getch()
                return

    def write_file(self, h):
        """
        Writes the collected data to a file.
        The user can specify a text header, h, which will be written to the top.
        A graphical "Save As" dialogue appears to ask the user where to save the file.
        """
        if not len(self.data):
            self.exit_error("Can't write file - no data available.")
        root = Tkinter.Tk()         # These "root" calls are annoying Tk hacks to make
        root.withdraw()             # the file dialogue appear by itself with focus.
        root.overrideredirect(True)
        root.geometry('0x0+0+0')
        root.deiconify()
        root.lift()
        root.focus_force()
        options = {'defaultextension': '.csv', \
            'filetypes':[('CSV','.csv')], 'title': "Save Data As"}
        fname = tkFileDialog.asksaveasfilename(**options)
        if fname == '':
            print "Save aborted."
            return
        f = open(fname,'w')
        f.write(h)
        for datum in self.data:
            for value in range(0,len(datum)):
                f.write(str(datum[value]))
                if not (value == len(datum) - 1):
                    f.write(",")
            f.write("\n")
        f.close()

if __name__ == '__main__':
    machine = Freeloader()
    machine.autoconnect()
    test = BasicTest(machine)
    test.run_test()