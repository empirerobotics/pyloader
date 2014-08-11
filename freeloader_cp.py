"""
Simple GUI for controlling a Freeloader.
Buttons and controls generally change state variables stored in the handles
object, h. Every few hundred milliseconds, update_GUI runs and communicates
with the machine based on what the state variables are asking for. 

This is a Tkinter GUI. Fully documenting it here would be a little cumbersome,
but the below should be self-explanatory enough.
"""

from Tkinter import *
from freeloader import Freeloader, FreeloaderError
import ttk, sys

def update_GUI(gui, h, fl):
    if (not h.stopped) and (not h.override):
        try:
            fl.start_motor(h.SliderSpeed.get(), down = h.down)
        except:
            print "There was an error setting speed!"
    h.position = fl.get_linear_position()
    h.load = fl.read_cell()
    h.PositionOut.configure(text=str(round(h.position,2))+" mm")
    h.LoadOut.configure(text=str(round(h.load,2))+" lbs")
    if not (h.target == None):
        if h.target > h.position:
            h.down = False
            h.stopped = False
        if h.target < h.position:
            h.down = True
            h.stopped = False
        if (abs(h.target - h.position) < 1) and (h.SliderSpeed.get() > 30):
            h.override = True
            fl.start_motor(30, down = h.down)
        if abs(h.target - h.position) < .5:
            h.override = True
            fl.start_motor(abs(h.target - h.position)*60, down = h.down)
        if abs(h.target - h.position) < .01:
            h.override = False
            stop(h,fl)
    h.alarm = gui.after(h.poll_rate,update_GUI,gui,h,fl)

def go_up(h, fl):
    h.stopped = False
    h.down = False

def go_down(h, fl):
    h.stopped = False
    h.down = True

def move(h, fl):
    h.target = h.position + float(h.TextMove.get(1.0,END))
    print "Moving to position " + str(round(h.target,2))

def stop(h, fl):
    h.target = None
    h.stopped = True
    try:
        fl.stop_motor()
    except:
        print "There was an error sending the stop command!"

def init_GUI(gui, h, fl):
    """This initializes callbacks and bindings (functions that get called when
    buttons get hit, etc). It also initializes all the state variables.)
    """
    h.ButtonUp.config(command=lambda: go_up(h,fl))
    h.ButtonStop.config(command=lambda: stop(h,fl))
    h.ButtonDown.config(command=lambda: go_down(h,fl))
    h.SliderSpeed.set(10)
    h.ButtonGo.config(command=lambda: move(h,fl))
    h.ButtonZero.config(command=lambda: fl.reset_linear_position())
    # fl.tare_cell()

    # Define GUI state variables
    h.poll_rate = 300
    h.target = None
    h.position = 0
    h.load = 0
    h.stopped = True
    h.down = False
    h.override = False
    return h

class Handle():
    pass

def populate_gui(gui):
    """
    This is a large blob of code that puts all the GUI widgets in place.
    It was generated automatically using a program called PAGE.
    """
    _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
    _fgcolor = '#000000'  # X11 color: 'black'
    _compcolor = '#d9d9d9' # X11 color: 'gray85'
    _ana1color = '#d9d9d9' # X11 color: 'gray85' 
    _ana2color = '#d9d9d9' # X11 color: 'gray85' 
    font10 = "-family {Segoe UI} -size 18 -weight bold -slant  " + \
        "roman -underline 0 -overstrike 0"
    font11 = "-family {Segoe UI} -size 14 -weight normal -slant  " + \
        "roman -underline 0 -overstrike 0"
    font12 = "-family {Segoe UI} -size 12 -weight normal -slant  " + \
        "roman -underline 0 -overstrike 0"
    font13 = "-family {Segoe UI} -size 12 -weight normal -slant  " + \
        "roman -underline 1 -overstrike 0"
    font14 = "-family {Segoe UI} -size 16 -weight bold -slant  " + \
        "roman -underline 0 -overstrike 0"
    gui.configure(background=_bgcolor)
    gui.title('Freeloader_Control_Panel')
    gui.geometry('660x450+542+144')

    h = Handle
    h.LabelTitle = Message (gui)
    h.LabelTitle.place(relx=0.24,rely=0.01,relheight=0.09,relwidth=0.52)
    h.LabelTitle.configure(background=_bgcolor)
    h.LabelTitle.configure(font=font10)
    h.LabelTitle.configure(foreground="#000000")
    h.LabelTitle.configure(highlightbackground="#d9d9d9")
    h.LabelTitle.configure(highlightcolor="black")
    h.LabelTitle.configure(text='''Freeloader Control Panel''')
    h.LabelTitle.configure(width=340)

    h.ButtonDown = Button (gui)
    h.ButtonDown.place(relx=0.2,rely=0.66,height=111,width=87)
    h.ButtonDown.configure(activebackground="#d9d9d9")
    h.ButtonDown.configure(activeforeground="#000000")
    h.ButtonDown.configure(background=_bgcolor)
    h.ButtonDown.configure(disabledforeground="#a3a3a3")
    h.ButtonDown.configure(foreground="#000000")
    h.ButtonDown.configure(highlightbackground="#d9d9d9")
    h.ButtonDown.configure(highlightcolor="black")
    h._img1 = PhotoImage(file="img/down.gif")
    h.ButtonDown.configure(image=h._img1)
    h.ButtonDown.configure(pady="0")
    h.ButtonDown.configure(text='''Button''')
    h.ButtonDown.configure(width=87)

    h.ButtonStop = Button (gui)
    h.ButtonStop.place(relx=0.2,rely=0.42,height=84,width=87)
    h.ButtonStop.configure(activebackground="#d9d9d9")
    h.ButtonStop.configure(activeforeground="#000000")
    h.ButtonStop.configure(background=_bgcolor)
    h.ButtonStop.configure(disabledforeground="#a3a3a3")
    h.ButtonStop.configure(foreground="#000000")
    h.ButtonStop.configure(highlightbackground="#d9d9d9")
    h.ButtonStop.configure(highlightcolor="black")
    h._img2 = PhotoImage(file="img/stop.gif")
    h.ButtonStop.configure(image=h._img2)
    h.ButtonStop.configure(pady="0")
    h.ButtonStop.configure(text='''Button''')
    h.ButtonStop.configure(width=87)

    h.ButtonUp = Button (gui)
    h.ButtonUp.place(relx=0.2,rely=0.13,height=111,width=86)
    h.ButtonUp.configure(activebackground="#d9d9d9")
    h.ButtonUp.configure(activeforeground="#000000")
    h.ButtonUp.configure(background=_bgcolor)
    h.ButtonUp.configure(disabledforeground="#a3a3a3")
    h.ButtonUp.configure(foreground="#000000")
    h.ButtonUp.configure(highlightbackground="#d9d9d9")
    h.ButtonUp.configure(highlightcolor="black")
    h._img3 = PhotoImage(file="img/up.gif")
    h.ButtonUp.configure(image=h._img3)
    h.ButtonUp.configure(pady="0")
    h.ButtonUp.configure(text='''Button''')

    h.LabelSpeed = Message (gui)
    h.LabelSpeed.place(relx=0.02,rely=0.11,relheight=0.12,relwidth=0.14)
    h.LabelSpeed.configure(background=_bgcolor)
    h.LabelSpeed.configure(font=font11)
    h.LabelSpeed.configure(foreground="#000000")
    h.LabelSpeed.configure(highlightbackground="#d9d9d9")
    h.LabelSpeed.configure(highlightcolor="black")
    h.LabelSpeed.configure(justify=CENTER)
    h.LabelSpeed.configure(text='''Speed (mm/min)''')
    h.LabelSpeed.configure(width=91)

    h.SliderSpeed = Scale (gui)
    h.SliderSpeed.place(relx=0.03,rely=0.29,relwidth=0.0,relheight=0.61
            ,width=70)
    h.SliderSpeed.configure(activebackground="#d9d9d9")
    h.SliderSpeed.configure(background=_bgcolor)
    h.SliderSpeed.configure(font=font12)
    h.SliderSpeed.configure(foreground="#000000")
    h.SliderSpeed.configure(from_="70.0")
    h.SliderSpeed.configure(highlightbackground="#d9d9d9")
    h.SliderSpeed.configure(highlightcolor="black")
    h.SliderSpeed.configure(length="268")
    h.SliderSpeed.configure(to="0.0")
    h.SliderSpeed.configure(troughcolor="#d9d9d9")
    h.SliderSpeed.configure(width=40)

    h.LabelMove = Message (gui)
    h.LabelMove.place(relx=0.39,rely=0.15,relheight=0.07,relwidth=0.27)
    h.LabelMove.configure(background=_bgcolor)
    h.LabelMove.configure(font=font13)
    h.LabelMove.configure(foreground="#000000")
    h.LabelMove.configure(highlightbackground="#d9d9d9")
    h.LabelMove.configure(highlightcolor="black")
    h.LabelMove.configure(justify=CENTER)
    h.LabelMove.configure(text='''Move Relative Distance''')
    h.LabelMove.configure(width=180)

    h.TextMove = Text (gui)
    h.TextMove.place(relx=0.41,rely=0.25,relheight=0.07,relwidth=0.19)
    h.TextMove.configure(background="white")
    h.TextMove.configure(font=font12)
    h.TextMove.configure(foreground="black")
    h.TextMove.configure(highlightbackground="#d9d9d9")
    h.TextMove.configure(highlightcolor="black")
    h.TextMove.configure(insertbackground="black")
    h.TextMove.configure(selectbackground="#c4c4c4")
    h.TextMove.configure(selectforeground="black")
    h.TextMove.configure(width=124)

    h.Labelmm = Message (gui)
    h.Labelmm.place(relx=0.58,rely=0.25,relheight=0.07,relwidth=0.07)
    h.Labelmm.configure(background=_bgcolor)
    h.Labelmm.configure(font=font12)
    h.Labelmm.configure(foreground="#000000")
    h.Labelmm.configure(highlightbackground="#d9d9d9")
    h.Labelmm.configure(highlightcolor="black")
    h.Labelmm.configure(text='''mm''')
    h.Labelmm.configure(width=185)

    h.ButtonGo = Button (gui)
    h.ButtonGo.place(relx=0.67,rely=0.25,height=32,width=71)
    h.ButtonGo.configure(activebackground="#d9d9d9")
    h.ButtonGo.configure(activeforeground="#000000")
    h.ButtonGo.configure(background=_bgcolor)
    h.ButtonGo.configure(disabledforeground="#a3a3a3")
    h.ButtonGo.configure(font=font11)
    h.ButtonGo.configure(foreground="#000000")
    h.ButtonGo.configure(highlightbackground="#d9d9d9")
    h.ButtonGo.configure(highlightcolor="black")
    h.ButtonGo.configure(pady="0")
    h.ButtonGo.configure(text='''Go''')
    h.ButtonGo.configure(width=71)

    h.ButtonZero = Button (gui)
    h.ButtonZero.place(relx=0.8,rely=0.25,height=32,width=71)
    h.ButtonZero.configure(activebackground="#d9d9d9")
    h.ButtonZero.configure(activeforeground="#000000")
    h.ButtonZero.configure(background=_bgcolor)
    h.ButtonZero.configure(disabledforeground="#a3a3a3")
    h.ButtonZero.configure(font=font11)
    h.ButtonZero.configure(foreground="#000000")
    h.ButtonZero.configure(highlightbackground="#d9d9d9")
    h.ButtonZero.configure(highlightcolor="black")
    h.ButtonZero.configure(pady="0")
    h.ButtonZero.configure(text='''Zero''')
    h.ButtonZero.configure(width=71)

    h.LabelData = Message (gui)
    h.LabelData.place(relx=0.39,rely=0.5,relheight=0.07,relwidth=0.17)
    h.LabelData.configure(background=_bgcolor)
    h.LabelData.configure(font=font13)
    h.LabelData.configure(foreground="#000000")
    h.LabelData.configure(highlightbackground="#d9d9d9")
    h.LabelData.configure(highlightcolor="black")
    h.LabelData.configure(justify=CENTER)
    h.LabelData.configure(text='''Machine Data''')
    h.LabelData.configure(width=185)

    h.LabelLoad = Message (gui)
    h.LabelLoad.place(relx=0.49,rely=0.6,relheight=0.09,relwidth=0.11)
    h.LabelLoad.configure(background=_bgcolor)
    h.LabelLoad.configure(font=font14)
    h.LabelLoad.configure(foreground="#000000")
    h.LabelLoad.configure(highlightbackground="#d9d9d9")
    h.LabelLoad.configure(highlightcolor="black")
    h.LabelLoad.configure(justify=CENTER)
    h.LabelLoad.configure(text='''Load:''')
    h.LabelLoad.configure(width=185)

    h.LabelPosition = Message (gui)
    h.LabelPosition.place(relx=0.44,rely=0.7,relheight=0.09
            ,relwidth=0.17)
    h.LabelPosition.configure(background=_bgcolor)
    h.LabelPosition.configure(font=font14)
    h.LabelPosition.configure(foreground="#000000")
    h.LabelPosition.configure(highlightbackground="#d9d9d9")
    h.LabelPosition.configure(highlightcolor="black")
    h.LabelPosition.configure(justify=CENTER)
    h.LabelPosition.configure(text='''Position:''')
    h.LabelPosition.configure(width=185)

    h.LoadOut = Message (gui)
    h.LoadOut.place(relx=0.62,rely=0.6,relheight=0.09,relwidth=0.27)
    h.LoadOut.configure(background=_bgcolor)
    h.LoadOut.configure(font=font14)
    h.LoadOut.configure(foreground="#000000")
    h.LoadOut.configure(highlightbackground="#d9d9d9")
    h.LoadOut.configure(highlightcolor="black")
    h.LoadOut.configure(text='''None''')
    h.LoadOut.configure(width=180)

    h.PositionOut = Message (gui)
    h.PositionOut.place(relx=0.62,rely=0.7,relheight=0.09,relwidth=0.27)

    h.PositionOut.configure(background=_bgcolor)
    h.PositionOut.configure(font=font14)
    h.PositionOut.configure(foreground="#000000")
    h.PositionOut.configure(highlightbackground="#d9d9d9")
    h.PositionOut.configure(highlightcolor="black")
    h.PositionOut.configure(text='''None''')
    h.PositionOut.configure(width=180)

    return h

"""
This is what actually runs, ending the in gui.mainloop, the GUI loop.
Note that a connection to the machine must be established before the GUI
appears and becomes usable.
"""
fl = Freeloader()
try:
    fl.autoconnect()
except FreeloaderError as fe:
    print "Autoconnect failed"
    print fe.msg
    out = raw_input("Hit enter to exit program.")
    sys.exit(0)
gui = Tk()
h = populate_gui(gui)
init_GUI(gui, h, fl)
update_GUI(gui, h, fl)
gui.mainloop()