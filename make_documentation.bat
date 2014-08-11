@python c:\Python27\Lib\pydoc.py -w dynamixel
@python c:\Python27\Lib\pydoc.py -w freeloader
@python c:\Python27\Lib\pydoc.py -w phidgetloader
@python c:\Python27\Lib\pydoc.py -w basictest
@python c:\Python27\Lib\pydoc.py -w tensiontest
@python c:\Python27\Lib\pydoc.py -w griptest
xcopy *.html docs /i /y /q
del *.html