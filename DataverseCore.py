#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Dataverse Utility.
# Tool for automating data repositories on Dataverse.
# To develop and adapt to the specific needs of experimental platforms.
# (C) Université de Lorraine
# Developed by Pr. Sidi HAMADY <sidi.hamady@univ-lorraine.fr>
# Released under the MIT licence (https://opensource.org/licenses/MIT)

import distutils.version as dver
import sys, os, os.path, time, platform 
import threading
import subprocess
import shlex
import datetime
import requests

DataMutex = threading.Condition()
StyleBackground     = '#f7f9fa'
StyleButtoncolor    = '#dae8eb'
StyleActivecolor    = '#f1f59d'
StyleInactivecolor  = '#f5fafa'

try:

    if sys.version_info[0] < 3:
        # Python 2.7.x
        import Tkinter as Tk
        import ttk
        import tkFileDialog
    else:
        # Python 3.x
        import tkinter as Tk
        import tkinter.ttk as ttk
        import tkinter.filedialog as tkFileDialog
    # end if
    
except ImportError as ierr:
    print("\n! cannot load Tkinter:\n  " + ("{0}".format(ierr)) + "\n")
    sys.exit(1)
except Exception as excT:
    print("\n! cannot load Tkinter:\n  %s\n" % str(excT))
    sys.exit(1)
# end try

class ScrolledFrame(Tk.Frame):

    def __init__(self, parent, *args, **kwargs):
    
        self.os = platform.system()

        self.parent = parent

        global StyleBackground
        global StyleButtoncolor
        global StyleActivecolor
        global StyleInactivecolor

        Tk.Frame.__init__(self, self.parent.root, *args, **kwargs)
        scrollbarstyle = ttk.Style(self)
        scrollbarstyle.layout('Dataverse.ScrollbarV', 
            [
                (   'Vertical.Scrollbar.trough',
                    {
                        'children': 
                        [
                            (
                                'Vertical.Scrollbar.thumb', 
                                {
                                    'expand': '1',
                                    'sticky': 'nswe'
                                }
                            )
                        ],
                        'sticky': 'ns'
                    }
                )
            ])
        scrollbarstyle.configure('Dataverse.ScrollbarV', background = StyleButtoncolor)
        scrollbarstyle.configure('Dataverse.ScrollbarV', troughcolor = StyleBackground)

        self.scrollbarv = ttk.Scrollbar(self, orient = 'vertical', style = 'Dataverse.ScrollbarV')
        self.scrollbarv.pack(fill = Tk.Y, side = Tk.RIGHT, expand = Tk.FALSE)
        self.canvas = Tk.Canvas(self, bd = 0, highlightthickness = 0, yscrollcommand = self.scrollbarv.set)
        self.canvas.pack(side = Tk.LEFT, fill = Tk.BOTH, expand = Tk.TRUE)
        if self.os == "Linux":
            self.canvas.bind_all('<4>', self.onMouseWheel, add='+')
            self.canvas.bind_all('<5>', self.onMouseWheel, add='+')
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel, add='+')
        #
        self.scrollbarv.config(command = self.canvas.yview)
        self.canvas.yview_moveto(0)
        self.frame = Tk.Frame(self.canvas, background = StyleBackground)
        self.window = self.canvas.create_window(0, 0, window = self.frame, anchor = Tk.NW)
        self.frame.bind('<Configure>', self.onConfigureFrame)
        self.canvas.bind('<Configure>', self.onConfigureCanvas)
    #

    def onMouseWheel(self, event):
        widget = self.canvas.focus_get()
        scrollableWidgets = [self.parent.DescriptionEdit, self.parent.NotesEdit, self.parent.JSONstdoutEdit, self.parent.DataStdoutEdit]
        if (widget in scrollableWidgets):
            x,y = self.parent.root.winfo_pointerxy()
            widgetm = self.parent.root.winfo_containing(x,y)
            if (widgetm is widget):
                yview = widget.yview()
                if yview[0] > 0.0 or yview[1] < 1.0:
                    return "break"
                #
            #
        #
        if self.os == "Linux":
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
            #
        else:     
            self.canvas.yview_scroll(-1 * (event.delta / 120), "units")
        #
        return "break"
    #

    def onConfigureFrame(self, event):
        self.canvas.config(scrollregion = "0 0 %s %s" % (self.frame.winfo_reqwidth(), self.frame.winfo_reqheight()))
        if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.config(width = self.frame.winfo_reqwidth())
        #
    #

    def onConfigureCanvas(self, event):
        if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.window, width = self.canvas.winfo_width())
        #
    #

# end ScrolledFrame

class MessageBox(Tk.Toplevel):

    def __init__(self, parent, title, message,
        callbackA = None, callbackB = None,
        labelA = "OK", labelB = "Cancel",
        TwoButton = True):

        self.window = None
        if (parent is None) or (parent.dialogshown):
            return
        #

        global StyleBackground
        global StyleButtoncolor
        global StyleActivecolor
        global StyleInactivecolor
 
        self.parent = parent
        self.window = Tk.Toplevel(self.parent.root)
        self.window.title(title)

        spx  = 18
        spy  = 6

        self.topFrame = Tk.Frame(self.window, background = StyleBackground)
        self.topFrame.pack(fill = Tk.X, side = Tk.TOP, padx = spx, pady = spy)
        self.message = Tk.Label(self.topFrame, text = message)
        self.message.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)

        self.btnstyle = ttk.Style()
        self.btnstyle.configure("MessageBox.TButton", foreground="black", background = StyleButtoncolor, focuscolor='none')
        self.btnstyle.map('MessageBox.TButton', background = [('active', StyleActivecolor), ])

        self.bottomFrame = Tk.Frame(self.window, background = StyleBackground)
        self.bottomFrame.pack(fill = Tk.X, side = Tk.TOP, padx = spx, pady = spy)        
        self.buttonA = ttk.Button(self.bottomFrame, text = labelA if labelA else "OK")
        if TwoButton:
            self.buttonA = ttk.Button(self.bottomFrame, text = labelA if labelA else "OK")   
            self.buttonA.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
        else:
            self.LLabel = Tk.Label(self.bottomFrame, text = " ", background = StyleBackground)
            self.LLabel.pack(fill = Tk.X, side = Tk.LEFT, expand = True, padx = spx, pady = spy)
            self.buttonA = ttk.Button(self.bottomFrame, width = 16, text = labelA if labelA else "OK")   
            self.buttonA.pack(side = Tk.LEFT, padx = spx, pady = spy)
            self.RLabel = Tk.Label(self.bottomFrame, text = " ", background = StyleBackground)
            self.RLabel.pack(fill = Tk.X, side = Tk.LEFT, expand = True, padx = spx, pady = spy)
        #
        self.buttonA.configure(style="MessageBox.TButton")
        self.buttonA.bind("<ButtonRelease-1>", self.onButtonA)
        if TwoButton:
            self.buttonB = ttk.Button(self.bottomFrame, text = labelB if labelB else "Cancel")
            self.buttonB.pack(side = Tk.LEFT, fill = Tk.BOTH, expand = 1)
            self.buttonB.configure(style="MessageBox.TButton")
            self.buttonB.bind("<ButtonRelease-1>", self.onButtonB)
        else:
            self.buttonB = None
        #

        self.labelA = labelA
        self.labelB = labelB
        self.callbackA = callbackA
        self.callbackB = callbackB
        self.retvalue = None

        self.window.deiconify()
        self.window.wm_attributes("-topmost", True)
        self.window.protocol('WM_DELETE_WINDOW', self.onClose)

        # center the window
        x = self.parent.root.winfo_x()
        y = self.parent.root.winfo_y()
        rw = self.parent.root.winfo_width()
        rh = self.parent.root.winfo_height()
        ix = x + (rw - self.parent.MessageBoxWidth) / 2
        iy = y + (rh - self.parent.MessageBoxHeight) / 2
        self.window.geometry("+%d+%d" % (ix, iy))

        self.window.minsize(160, 90)

        if (os.name == "nt"):
            self.window.iconbitmap(r'iconmain.ico')
        else:
            iconmain = Tk.PhotoImage(file='iconmain.gif')
            self.window.tk.call('wm', 'iconphoto', self.window._w, iconmain)
        # end if

        self.window.mainloop()
        self.destroy()
    # end __init__

    def destroy(self):
        if self.window is not None:
            self.parent.MessageBoxWidth = self.window.winfo_width()
            self.parent.MessageBoxHeight = self.window.winfo_height()
            self.window.quit()
            self.window.destroy()
            self.parent.root.deiconify()
            self.window = None
        #
    #

    def onButtonA(self, event = None):
        if self.window is not None:
            self.retvalue = self.labelA
            self.destroy()
            if self.callbackA is not None:
                self.callbackA()
            #
        #
    #

    def onButtonB(self, event = None):
        if self.window is not None:
            self.retvalue = self.labelB
            self.destroy()
            if self.callbackB is not None:
                self.callbackB()
            #
        #
    #

    def onClose(self):
        if self.window is not None:
            self.destroy()
        #
    #
# end MessageBox

# uploading done in a secondary thread, not on GUI
class UploadThread(threading.Thread):
    def __init__(self, id, func):
        threading.Thread.__init__(self)
        self.id     = id
        self.func   = func
    # end __init__
    def run(self):
        self.func()
    # end run
# end UploadThread

# the core class
class DataverseCore(object):
    """ the Dataverse core class """

    def __init__(self):
        """ the Dataverse class constructor """

        self.name                   = "Dataverse Utility"
        self.__version__            = "Version 1.0 Build 2105"
        self.os                     = platform.system()

        # @shared
        self.DATAVERSE_KEY          = "zbc9f319-194c-403c-f818-f24cf6e6aacd"
        # @shared
        self.DATAVERSE_SERVER       = "https://bac-dataverse.univ-lorraine.fr/api/dataverses/carel_lmops/datasets"
        # @shared
        self.DATASET_SERVER         = "https://bac-dataverse.univ-lorraine.fr/api/datasets"
        # @shared
        self.CURL_COMMAND_JSON      = "-H X-Dataverse-key:%s -X POST \"%s\" --upload-file %s"
        # @shared
        self.CURL_COMMAND_DATA      = "-H X-Dataverse-key:%s -X POST -F file=@%s -F 'jsonData={\"description\":\"%s\",\"directoryLabel\":\"%s\",\"categories\":[\"Data\"], \"restrict\":\"false\"}' \"%s/:persistentId/add?persistentId=%s\""

        # @shared
        self.JSONfilename           = "zinc_oxide.json"

        # @shared
        self.ReportFilename         = "zinc_oxide.pdf"
        # @shared
        self.ReportDescription      = "Report detailing the experimental procedure"
        # @shared
        self.DataFilename           = ["zinc_oxide.txt", "", "", "", ""]
        # @shared
        self.DataDescription        = ["zinc oxide vdP/Hall data", "", "", "", ""]

        self.title                  = "van der Pauw and Hall effect characterization of semiconductor oxides"
        self.description            = "This dataset contains the van der Pauw and Hall effect data for semiconductor oxide thin films with respect to the growth temperature"
        self.displayName            = "Electrical characterization of semiconductor oxides"
        self.subject                = "Physics"
        self.keyword                = ["Semiconductors", "Thin Films", "Electrical Characterization", "Optoelectronics", "Solar Cells"]
        self.author                 = ["Hamady, Sidi", "", "", "", ""]
        self.affiliation            = ["Université de Lorraine, CentraleSupélec, LMOPS", "", "", "", ""]
        self.identifier             = ["0000-0002-0480-6381", "", "", "", ""]
        self.contactname            = "Hamady, Sidi"
        self.contactaffiliation     = "Université de Lorraine, CentraleSupélec, LMOPS"
        self.contactemail           = "sidi.hamady@univ-lorraine.fr"
        self.publicationCitation    = ""
        self.notesText              = ""
        self.DataDirectory          = "vdPauw/References/Measurements/data"
        self.categories             = "Data"
        self.persistentId           = "doi:10.80427/FK2/NBWPDH"

        self.JSON_TEMPLATE_HEADER   =  ("{\n"
                                        "    \"datasetVersion\":\n"
                                        "    {\n"
                                        "        \"termsOfUse\": \"CC0 Waiver\",\n"
                                        "        \"license\": \"CC0\",\n"
                                        "        \"protocol\":\"doi\",\n"
                                        "        \"authority\":\"10.502\",\n"
                                        "        \"identifier\":\"CC1/21D1\",\n"
                                        "        \"metadataBlocks\":\n"
                                        "        {\n"
                                        "            \"citation\":\n"
                                        "            {\n"
                                        "                \"fields\":\n"
                                        "                [\n")
                                        

        self.JSON_TEMPLATE_FOOTER   =  ("                ],\n"
                                        "                \"displayName\": \"%s\"\n"
                                        "            }\n"
                                        "        }\n"
                                        "    }\n"
                                        "}\n")

        self.JSON_TEMPLATE_TITLE    =  ("                    {\n"
                                        "                        \"typeName\": \"title\",\n"
                                        "                        \"multiple\": false,\n"
                                        "                        \"value\": \"%s\",\n"
                                        "                        \"typeClass\": \"primitive\"\n"
                                        "                    },\n"
                                        "                    {\n"
                                        "                        \"typeName\": \"language\",\n"
                                        "                        \"multiple\": true,\n"
                                        "                        \"value\":\n"
                                        "                        [\n"
                                        "                           \"English\"\n"
                                        "                        ],\n"
                                        "                        \"typeClass\": \"controlledVocabulary\"\n"
                                        "                    },\n"
                                        "                    {\n"
                                        "                        \"typeName\": \"producer\",\n"
                                        "                        \"multiple\": true,\n"
                                        "                        \"value\":\n"
                                        "                        [\n"
                                        "                           {\n"
                                        "                                \"producerName\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"producerName\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"Université de Lorraine\",\n"
                                        "                                    \"typeClass\": \"primitive\"\n"
                                        "                                }\n"
                                        "                            }\n"
                                        "                        ],\n"
                                        "                        \"typeClass\": \"compound\"\n"
                                        "                    }")

        self.JSON_TEMPLATE_DESCR    =  ("                    {\n"
                                        "                        \"typeName\": \"dsDescription\",\n"
                                        "                        \"multiple\": true,\n"
                                        "                        \"value\":\n"
                                        "                        [\n"
                                        "                            {\n"
                                        "                                \"dsDescriptionValue\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"dsDescriptionValue\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"%s\",\n"
                                        "                                    \"typeClass\": \"primitive\"\n"
                                        "                                },\n"
                                        "                                \"dsDescriptionDate\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"dsDescriptionDate\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"%s\",\n"
                                        "                                    \"typeClass\": \"primitive\"\n"
                                        "                                }\n"
                                        "                            }\n"
                                        "                        ],\n"
                                        "                        \"typeClass\": \"compound\"\n"
                                        "                    }")

        self.JSON_TEMPLATE_AUTH_H   =  ("                    {\n"
                                        "                        \"typeName\": \"author\",\n"
                                        "                        \"multiple\": true,\n"
                                        "                        \"value\":\n"
                                        "                        [\n")

        self.JSON_TEMPLATE_AUTH_F   =  ("                        ],\n"
                                        "                        \"typeClass\": \"compound\"\n"
                                        "                    }")

        self.JSON_TEMPLATE_AUTH     =  ("                            {\n"
                                        "                                \"authorAffiliation\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"authorAffiliation\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"%s\",\n"
                                        "                                    \"typeClass\": \"primitive\"\n"
                                        "                                },\n"
                                        "                                \"authorName\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"authorName\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"%s\",\n"
                                        "                                    \"typeClass\": \"primitive\"\n"
                                        "                                },\n"
                                        "                                \"authorIdentifierScheme\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"authorIdentifierScheme\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"ORCID\",\n"
                                        "                                    \"typeClass\": \"controlledVocabulary\"\n"
                                        "                                },\n"
                                        "                                \"authorIdentifier\":\n"
                                        "                                {\n"
                                        "                                    \"typeName\": \"authorIdentifier\",\n"
                                        "                                    \"multiple\": false,\n"
                                        "                                    \"value\": \"%s\",\n"
                                        "                                    \"typeClass\": \"primitive\"\n"
                                        "                                }\n"
                                        "                            }")

        self.JSON_TEMPLATE_DEP      =  ("                    {\n"
                                        "                        \"typeName\": \"depositor\",\n"
                                        "                        \"multiple\": false,\n"
                                        "                        \"value\": \"%s\",\n"
                                        "                        \"typeClass\": \"primitive\"\n"
                                        "                    },\n"
                                        "                    {\n"
                                        "                        \"typeName\": \"dateOfDeposit\",\n"
                                        "                        \"multiple\": false,\n"
                                        "                        \"value\": \"%s\",\n"
                                        "                        \"typeClass\": \"primitive\"\n"
                                        "                    }")

        self.JSON_TEMPLATE_CONTACT  =  ("                    {\n"
                                        "                       \"typeName\": \"datasetContact\",\n"
                                        "                       \"multiple\":true,\n"
                                        "                       \"typeClass\":\"compound\",\n"
                                        "                       \"value\":\n"
                                        "                       [\n"
                                        "                           {\n"
                                        "                               \"datasetContactName\":\n"
                                        "                               {\n"
                                        "                                   \"typeName\":\"datasetContactName\",\n"
                                        "                                   \"multiple\":false,\n"
                                        "                                   \"typeClass\":\"primitive\",\n"
                                        "                                   \"value\":\"%s\"\n"
                                        "                               },\n"
                                        "                               \"datasetContactAffiliation\":\n"
                                        "                               {\n"
                                        "                                   \"typeName\":\"datasetContactAffiliation\",\n"
                                        "                                   \"multiple\":false,\n"
                                        "                                   \"typeClass\":\"primitive\",\n"
                                        "                                   \"value\":\"%s\"\n"
                                        "                               },\n"
                                        "                               \"datasetContactEmail\":\n"
                                        "                               {\n"
                                        "                                   \"typeName\":\"datasetContactEmail\",\n"
                                        "                                   \"multiple\":false,\n"
                                        "                                   \"typeClass\":\"primitive\",\n"
                                        "                                   \"value\":\"%s\"\n"
                                        "                               }\n"
                                        "                           }\n"
                                        "                       ]\n"
                                        "                   }")                                       

        self.JSON_TEMPLATE_SUBJECT  =  ("                    {\n"
                                        "                       \"typeName\":\"subject\",\n"
                                        "                       \"multiple\":true,\n"
                                        "                       \"typeClass\":\"controlledVocabulary\",\n"
                                        "                       \"value\":\n"
                                        "                       [\n"
                                        "                           \"%s\"\n"
                                        "                       ]\n"
                                        "                    }")

        self.JSON_TEMPLATE_PUBLI    =  ("                    {\n"
                                        "                       \"typeName\":\"publication\",\n"
                                        "                       \"multiple\":true,\n"
                                        "                       \"typeClass\":\"compound\",\n"
                                        "                       \"value\":\n"
                                        "                       [\n"
                                        "                           {\n"
                                        "                               \"publicationCitation\":\n"
                                        "                               {\n"
                                        "                                   \"typeName\":\"publicationCitation\",\n"
                                        "                                   \"multiple\":false,\n"
                                        "                                   \"typeClass\":\"primitive\",\n"
                                        "                                   \"value\":\"%s\"\n"
                                        "                               }\n"
                                        "                           }\n"
                                        "                       ]\n"
                                        "                    }")

        self.JSON_TEMPLATE_NOTES    =  ("                    {\n"
                                        "                       \"typeName\":\"notesText\",\n"
                                        "                       \"multiple\":false,\n"
                                        "                       \"typeClass\":\"primitive\",\n"
                                        "                       \"value\":\"%s\"\n"
                                        "                    }")

        self.JSON_TEMPLATE_KEYW_H   =  ("                    {\n"
                                        "                       \"typeName\":\"keyword\",\n"
                                        "                       \"multiple\":true,\n"
                                        "                       \"typeClass\":\"compound\",\n"
                                        "                       \"value\":\n"
                                        "                       [\n")

        self.JSON_TEMPLATE_KEYW_F   =  ("                       ]\n"
                                        "                   }")

        self.JSON_TEMPLATE_KEYW     =  ("                           {\n"
                                        "                               \"keywordValue\":\n"
                                        "                               {\n"
                                        "                                   \"typeName\":\"keywordValue\",\n"
                                        "                                   \"multiple\":false,\n"
                                        "                                   \"typeClass\":\"primitive\",\n"
                                        "                                   \"value\":\"%s\"\n"
                                        "                               }\n"
                                        "                           }")
        
        # @shared
        self.JSONcontent            = ""

        self.thread                 = None
        self.threadfinish           = None
        self.running                = False
        self.action                 = None
        self.actionbutton           = None
        self.actionbuttonText       = None
        self.dialogshown            = False

        # @shared
        self.actionText             = None

        self.timerduration          = 100       # in milliseconds

        # @shared
        self.Stdout                 = ""

        # @shared
        self.tic                    = None

        self.GUIstarted             = False

        return

    # end __init__

    def isRunning(self):
        if (self.thread is None):
            return self.running
        # end if
        if (not self.thread.isAlive()):
            self.thread  = None
            self.running = False
        # end if
        return self.running
    # end isRunning

    def setRunning(self, running = True):
        self.running = running
        try:
            if self.actionbutton is not None:
                self.actionbutton["text"] = self.actionbuttonText
                if self.running:
                    self.actionbutton.configure(style='Red.TButton')
                else:
                    self.actionbutton.configure(style='Black.TButton')
                    self.actionbutton = None
                    if self.actionText == 'JSON':
                        self.JSONstdoutEdit.insert("end", self.Stdout)
                        self.JSONstdoutEdit.insert("end", "\n\nelapsed time = %.6f sec." % self.tic)
                        strItem = "\"status\":\"OK\""
                        iFound = self.Stdout.find(strItem)
                        if (iFound > 0):
                            strItem = "\"persistentId\":\""
                            iFound = self.Stdout.find(strItem)
                            if (iFound > 0):
                                iStart = iFound + len(strItem)
                                strId = self.Stdout[iStart:iStart+len("doi:10.80427/FK2/MW99OH")]
                                self.persistentIdEdit.delete(0, Tk.END)
                                self.persistentIdEdit.insert(0, strId)
                            #
                        #
                    else:
                        self.DataStdoutEdit.insert("end", self.Stdout)
                        self.DataStdoutEdit.insert("end", "\n\nelapsed time = %.6f sec." % self.tic)
                    #
                # end if
            # end if
        except:
            pass
        #
    # end setRunning

    # init the Tkinter GUI
    def show(self):

        if self.GUIstarted:
            return
        # end if

        try:

            global StyleBackground
            global StyleButtoncolor
            global StyleActivecolor
            global StyleInactivecolor

            self.root = Tk.Tk()
            self.root['background'] = StyleBackground

            self.root.bind_class("Entry","<Control-a>", self.onEntrySelectAll)
            self.root.bind_class("Entry","<Control-z>", self.onEntryUndo)
            self.root.bind_class("Entry","<Control-y>", self.onEntryRedo)
            self.root.withdraw()
            self.root.wm_title(self.name)

            self.rootrame = ScrolledFrame(self)
            self.mainFrame = self.rootrame.frame
            self.rootrame.pack(side = Tk.LEFT, fill = Tk.BOTH, expand = 1)

            self.root.bind_class("Entry", "<<Paste>>", self.onTextPaste)
            self.root.bind_class("Text", "<<Paste>>", self.onTextPaste)

            dlgStyle = ttk.Style(self.root)
            dlgStyle.configure('.', background = StyleBackground)
            dlgStyle.configure('.', foreground = 'black')
            dlgStyle.configure('TEntry', background = 'white')
            dlgStyle.configure('TButton', foreground='red', background = StyleButtoncolor)
            dlgStyle.configure("TButton", foreground="black", background = StyleButtoncolor, focuscolor='none')
            dlgStyle.map('TButton', background = [('active', StyleActivecolor), ])
            dlgStyle.map('TButton', background = [('active', StyleActivecolor), ])
            dlgStyle.configure('TScrollbar', background = StyleButtoncolor)
            dlgStyle.configure('TScrollbar', troughcolor = StyleBackground)    

            self.MessageBoxWidth = 0
            self.MessageBoxHeight = 0

            spx  = 18
            spy  = 6
            spxm = 1
            parFrame = []

            FramesCount = 21
            for ii in range(0, FramesCount):
                frameT = Tk.Frame(self.mainFrame, background = StyleBackground)
                frameT.pack(fill = Tk.X, side = Tk.TOP, padx=spx, pady=spy)
                parFrame.append(frameT)
            #

            FrameX = 0

            self.TitleTop = Tk.Label(parFrame[FrameX], text = "Dataverse Utility", font='Helvetica 12 bold', background = StyleBackground)
            self.TitleTop.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            FrameX += 1

            self.TitleLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Title: ", anchor = Tk.E, background = StyleBackground)
            self.TitleLabel.pack(side = Tk.LEFT)
            TitleValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.TitleEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = TitleValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.TitleEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.TitleEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.TitleEdit.insert(0, self.title)
            self.TitleEdit.prev = None
            self.TitleEdit.next = None
            FrameX += 1

            self.DescriptionLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Description: ", anchor = Tk.E, background = StyleBackground)
            self.DescriptionLabel.pack(side = Tk.LEFT)
            self.DescriptionEdit = Tk.Text(parFrame[FrameX], wrap="word", background = "white", highlightthickness = 2, selectbackground = "pale turquoise", selectforeground = "black", height = 5)
            self.DescriptionEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.DescriptionEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.DescriptionEdit.insert("end", self.description)
            FrameX += 1

            self.AuthorsLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Authors: ", anchor = Tk.E, background = StyleBackground)
            self.AuthorsLabel.pack(side = Tk.LEFT)
            AuthorValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.AuthorEdit = []
            self.AuthorsCount = 5
            for ii in range(0, self.AuthorsCount):
                AuthorE = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = AuthorValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
                AuthorE.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
                AuthorE.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
                AuthorE.insert(0, self.author[ii])
                AuthorE.prev = None
                AuthorE.next = None
                self.AuthorEdit.append(AuthorE)
            #
            FrameX += 1

            self.AffiliationLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Affiliations: ", anchor = Tk.E, background = StyleBackground)
            self.AffiliationLabel.pack(side = Tk.LEFT)
            AffiliationValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.AffiliationEdit = []
            for ii in range(0, self.AuthorsCount):
                AffiliationE = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = AffiliationValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
                AffiliationE.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
                AffiliationE.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
                AffiliationE.insert(0, self.affiliation[ii])
                AffiliationE.prev = None
                AffiliationE.next = None
                self.AffiliationEdit.append(AffiliationE)
            #
            FrameX += 1

            self.IdentifierLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Identifiers (ORCID): ", anchor = Tk.E, background = StyleBackground)
            self.IdentifierLabel.pack(side = Tk.LEFT)
            IdentifierValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.IdentifierEdit = []
            for ii in range(0, self.AuthorsCount):
                IdentifierE = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = IdentifierValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
                IdentifierE.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
                IdentifierE.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
                IdentifierE.insert(0, self.identifier[ii])
                IdentifierE.prev = None
                IdentifierE.next = None
                self.IdentifierEdit.append(IdentifierE)
            #
            FrameX += 1

            self.ContactLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Contact: ", anchor = Tk.E, background = StyleBackground)
            self.ContactLabel.pack(side = Tk.LEFT)
            ContactValidateName = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.ContactNameEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = ContactValidateName, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.ContactNameEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.ContactNameEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.ContactNameEdit.insert(0, self.contactname)
            self.ContactNameEdit.prev = None
            self.ContactNameEdit.next = None
            ContactValidateAffiliation = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.ContactAffiliationEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = ContactValidateAffiliation, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.ContactAffiliationEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.ContactAffiliationEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.ContactAffiliationEdit.insert(0, self.contactaffiliation)
            self.ContactAffiliationEdit.prev = None
            self.ContactAffiliationEdit.next = None
            ContactValidateEmail = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.ContactEmailEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = ContactValidateEmail, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.ContactEmailEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.ContactEmailEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.ContactEmailEdit.insert(0, self.contactemail)
            self.ContactEmailEdit.prev = None
            self.ContactEmailEdit.next = None
            FrameX += 1

            self.DisplayNameLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Display Name: ", anchor = Tk.E, background = StyleBackground)
            self.DisplayNameLabel.pack(side = Tk.LEFT)
            DisplayNameValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.DisplayNameEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = DisplayNameValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.DisplayNameEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.DisplayNameEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.DisplayNameEdit.insert(0, self.displayName)
            self.DisplayNameEdit.prev = None
            self.DisplayNameEdit.next = None
            self.SubjectLabel = Tk.Label(parFrame[FrameX], width = 12, text = "Subject: ", anchor = Tk.E, background = StyleBackground)
            self.SubjectLabel.pack(side = Tk.LEFT)
            SubjectValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.SubjectEdit = Tk.Entry(parFrame[FrameX], width = 24, validate = "key", vcmd = SubjectValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.SubjectEdit.pack(side = Tk.LEFT)
            self.SubjectEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.SubjectEdit.insert(0, self.subject)
            self.SubjectEdit.prev = None
            self.SubjectEdit.next = None
            FrameX += 1

            self.PublicationCitationLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Publication Citation: ", anchor = Tk.E, background = StyleBackground)
            self.PublicationCitationLabel.pack(side = Tk.LEFT)
            PublicationCitationValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.PublicationCitationEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = PublicationCitationValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.PublicationCitationEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.PublicationCitationEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.PublicationCitationEdit.insert(0, self.publicationCitation)
            self.PublicationCitationEdit.prev = None
            self.PublicationCitationEdit.next = None
            FrameX += 1
            
            self.NotesLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Notes: ", anchor = Tk.E, background = StyleBackground)
            self.NotesLabel.pack(side = Tk.LEFT)
            self.NotesEdit = Tk.Text(parFrame[FrameX], wrap="word", background = "white", highlightthickness = 2, selectbackground = "pale turquoise", selectforeground = "black", height = 3)
            self.NotesEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.NotesEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.NotesEdit.insert("end", self.notesText)
            FrameX += 1

            self.KeywordsLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Keywords: ", anchor = Tk.E, background = StyleBackground)
            self.KeywordsLabel.pack(side = Tk.LEFT)
            KeywordValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.KeywordEdit = []
            self.KeywordsCount = 5
            for ii in range(0, self.KeywordsCount):
                KeywordE = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = KeywordValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
                KeywordE.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
                KeywordE.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
                KeywordE.insert(0, self.keyword[ii])
                KeywordE.prev = None
                KeywordE.next = None
                self.KeywordEdit.append(KeywordE)
            #
            FrameX += 1

            self.btnstyle_red = ttk.Style()
            self.btnstyle_red.configure("Red.TButton", foreground="#DE0015", background = StyleButtoncolor, focuscolor='none')
            self.btnstyle_black = ttk.Style()
            self.btnstyle_black.configure("Black.TButton", foreground="black", background = StyleButtoncolor, focuscolor='none')
            self.btnstyle_black.map('Red.TButton', background = [('active', StyleActivecolor), ])
            self.btnstyle_black.map('Black.TButton', background = [('active', StyleActivecolor), ])

            self.Buttons = {}

            self.JSONfilenameLabel = Tk.Label(parFrame[FrameX], width = 18, text = "JSON Filename: ", anchor = Tk.E, background = StyleBackground)
            self.JSONfilenameLabel.pack(side = Tk.LEFT)
            JSONfilenameValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.JSONfilenameEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = JSONfilenameValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.JSONfilenameEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.JSONfilenameEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            if (self.JSONfilename is not None) and (self.JSONfilename.endswith(".json")):
                self.JSONfilename = os.path.join(os.path.dirname(__file__), self.JSONfilename)
            #
            self.JSONfilenameEdit.insert(0, self.JSONfilename if (self.JSONfilename is not None) else "")
            self.JSONfilenameEdit.prev = None
            self.JSONfilenameEdit.next = None
            self.JSONfilenameBrowse = ttk.Button(parFrame[FrameX], width=4, text = "...")
            self.JSONfilenameBrowse.pack(side = Tk.LEFT, padx=(2, 2))
            self.JSONfilenameBrowse.configure(style="Black.TButton")
            self.JSONfilenameBrowse.bind("<ButtonRelease-1>", self.onBrowse)
            self.Buttons[self.JSONfilenameBrowse] = (self.JSONfilenameEdit, 'JSON')
            FrameX += 1

            self.KeyLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Key: ", anchor = Tk.E, background = StyleBackground)
            self.KeyLabel.pack(side = Tk.LEFT)
            KeyValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.KeyEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = KeyValidate, highlightthickness = 2, background = StyleInactivecolor, selectbackground = "pale turquoise", selectforeground = "black")
            self.KeyEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.KeyEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.KeyEdit.insert(0, self.DATAVERSE_KEY)
            self.KeyEdit.prev = None
            self.KeyEdit.next = None
            self.DataverseServerLabel = Tk.Label(parFrame[FrameX], width = 12, text = "Server DV: ", anchor = Tk.E, background = StyleBackground)
            self.DataverseServerLabel.pack(side = Tk.LEFT)
            DataverseServerValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.DataverseServerEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = DataverseServerValidate, highlightthickness = 2, background = StyleInactivecolor, selectbackground = "pale turquoise", selectforeground = "black")
            self.DataverseServerEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.DataverseServerEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.DataverseServerEdit.insert(0, self.DATAVERSE_SERVER)
            self.DataverseServerEdit.prev = None
            self.DataverseServerEdit.next = None
            self.DatasetServerLabel = Tk.Label(parFrame[FrameX], width = 12, text = "Server DS: ", anchor = Tk.E, background = StyleBackground)
            self.DatasetServerLabel.pack(side = Tk.LEFT)
            DatasetServerValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.DatasetServerEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = DatasetServerValidate, highlightthickness = 2, background = StyleInactivecolor, selectbackground = "pale turquoise", selectforeground = "black")
            self.DatasetServerEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.DatasetServerEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.DatasetServerEdit.insert(0, self.DATASET_SERVER)
            self.DatasetServerEdit.prev = None
            self.DatasetServerEdit.next = None
            FrameX += 1

            self.LLabel = Tk.Label(parFrame[FrameX], text = " ", background = StyleBackground)
            self.LLabel.pack(fill = Tk.X, side = Tk.LEFT, expand = True, padx=(spxm, spxm), pady=0)
            self.btnUploadJSON = ttk.Button(parFrame[FrameX], width = 32, text = "Upload JSON", compound=Tk.LEFT, command=self.onUploadJSON)
            self.btnUploadJSON.pack(side = Tk.LEFT, padx=spx, pady=0)
            self.btnUploadJSON.configure(style="Black.TButton")
            self.RLabel = Tk.Label(parFrame[FrameX], text = " ", background = StyleBackground)
            self.RLabel.pack(fill = Tk.X, side = Tk.LEFT, expand = True, padx=(spxm, spxm), pady=0)
            FrameX += 1

            self.JSONstdoutEdit = Tk.Text(parFrame[FrameX], wrap="word", background=StyleInactivecolor, highlightthickness = 2, selectbackground = "pale turquoise", selectforeground = "black", height = 5)
            self.JSONstdoutEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.JSONstdoutEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            FrameX += 1

            self.persistentIdLabel = Tk.Label(parFrame[FrameX], width = 18, text = "persistentId: ", anchor = Tk.E, background = StyleBackground)
            self.persistentIdLabel.pack(side = Tk.LEFT)
            persistentIdValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.persistentIdEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = persistentIdValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.persistentIdEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.persistentIdEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.persistentIdEdit.insert(0, self.persistentId)
            self.persistentIdEdit.prev = None
            self.persistentIdEdit.next = None
            FrameX += 1

            self.DataDirectoryLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Directory: ", anchor = Tk.E, background = StyleBackground)
            self.DataDirectoryLabel.pack(side = Tk.LEFT)
            DataDirectoryValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.DataDirectoryEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = DataDirectoryValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.DataDirectoryEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.DataDirectoryEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.DataDirectoryEdit.insert(0, self.DataDirectory if (self.DataDirectory is not None) else "")
            self.DataDirectoryEdit.prev = None
            self.DataDirectoryEdit.next = None
            FrameX += 1

            self.ReportFilenameLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Report Filename: ", anchor = Tk.E, background = StyleBackground)
            self.ReportFilenameLabel.pack(side = Tk.LEFT)
            ReportFilenameValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.ReportFilenameEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = ReportFilenameValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.ReportFilenameEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.ReportFilenameEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            if (self.ReportFilename is not None) and (self.ReportFilename.endswith(".pdf")):
                self.ReportFilename = os.path.join(os.path.dirname(__file__), self.ReportFilename)
            #
            self.ReportFilenameEdit.insert(0, self.ReportFilename if (self.ReportFilename is not None) else "")
            self.ReportFilenameEdit.prev = None
            self.ReportFilenameEdit.next = None
            self.ReportFilenameBrowse = ttk.Button(parFrame[FrameX], width=4, text = "...")
            self.ReportFilenameBrowse.pack(side = Tk.LEFT, padx=(2, 2))
            self.ReportFilenameBrowse.configure(style="Black.TButton")
            self.ReportFilenameBrowse.bind("<ButtonRelease-1>", self.onBrowse)
            self.Buttons[self.ReportFilenameBrowse] = (self.ReportFilenameEdit, 'PDF')
            FrameX += 1

            ReportDescriptionLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Report Description: ", anchor = Tk.E, background = StyleBackground)
            ReportDescriptionLabel.pack(side = Tk.LEFT)
            ReportDescriptionValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
            self.ReportDescriptionEdit = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = ReportDescriptionValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
            self.ReportDescriptionEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.ReportDescriptionEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            self.ReportDescriptionEdit.insert(0, self.ReportDescription if (self.ReportDescription is not None) else "")
            self.ReportDescriptionEdit.prev = None
            self.ReportDescriptionEdit.next = None
            FrameX += 1

            self.DataFilenamesCount = 5
            self.DataFilenameEdit = [None] * self.DataFilenamesCount
            self.DataFilenameBrowse = [None] * self.DataFilenamesCount
            self.DataDescriptionEdit = [None] * self.DataFilenamesCount
            for ii in range(0, self.DataFilenamesCount):
                frameT = Tk.Frame(self.mainFrame, background = StyleBackground)
                frameT.pack(fill = Tk.X, side = Tk.TOP, padx=spx, pady=spy)
                parFrame.append(frameT)
                self.DataFilenameLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Data Filename #%d: " % (ii + 1), anchor = Tk.E, background = StyleBackground)
                self.DataFilenameLabel.pack(side = Tk.LEFT)
                DataFilenameValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
                self.DataFilenameEdit[ii] = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = DataFilenameValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
                self.DataFilenameEdit[ii].pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
                self.DataFilenameEdit[ii].config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
                if (self.DataFilename[ii] is not None) and (self.DataFilename[ii].endswith(".txt")):
                    self.DataFilename[ii] = os.path.join(os.path.dirname(__file__), self.DataFilename[ii])
                #
                self.DataFilenameEdit[ii].insert(0, self.DataFilename[ii] if (self.DataFilename[ii] is not None) else "")
                self.DataFilenameEdit[ii].prev = None
                self.DataFilenameEdit[ii].next = None
                self.DataFilenameBrowse[ii] = ttk.Button(parFrame[FrameX], width=4, text = "...")
                self.DataFilenameBrowse[ii].pack(side = Tk.LEFT, padx=(2, 2))
                self.DataFilenameBrowse[ii].configure(style="Black.TButton")
                self.DataFilenameBrowse[ii].bind("<ButtonRelease-1>", self.onBrowse)
                self.Buttons[self.DataFilenameBrowse[ii]] = (self.DataFilenameEdit[ii], 'Data')
                FrameX += 1

                frameD = Tk.Frame(self.mainFrame, background = StyleBackground)
                frameD.pack(fill = Tk.X, side = Tk.TOP, padx=spx, pady=spy)
                parFrame.append(frameD)
                DataDescriptionLabel = Tk.Label(parFrame[FrameX], width = 18, text = "Data Description #%d: " % (ii + 1), anchor = Tk.E, background = StyleBackground)
                DataDescriptionLabel.pack(side = Tk.LEFT)
                DataDescriptionValidate = (parFrame[FrameX].register(self.onInputValidate), '%P')
                self.DataDescriptionEdit[ii] = Tk.Entry(parFrame[FrameX], validate = "key", vcmd = DataDescriptionValidate, highlightthickness = 2, background = "white", selectbackground = "pale turquoise", selectforeground = "black")
                self.DataDescriptionEdit[ii].pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
                self.DataDescriptionEdit[ii].config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
                self.DataDescriptionEdit[ii].insert(0, self.DataDescription[ii] if (self.DataDescription[ii] is not None) else "")
                self.DataDescriptionEdit[ii].prev = None
                self.DataDescriptionEdit[ii].next = None
                FrameX += 1
            #

            if FrameX >= FramesCount:
                frameT = Tk.Frame(self.mainFrame, background = StyleBackground)
                frameT.pack(fill = Tk.X, side = Tk.TOP, padx=spx, pady=spx)
                parFrame.append(frameT)
            #
    
            self.LLabelX = Tk.Label(parFrame[FrameX], text = " ", background = StyleBackground)
            self.LLabelX.pack(fill = Tk.X, side = Tk.LEFT, expand = True, padx=(spxm, spxm), pady=0)
            self.btnUploadData = ttk.Button(parFrame[FrameX], width = 32, text = "Upload Data", compound=Tk.LEFT, command=self.onUploadData)
            self.btnUploadData.pack(side = Tk.LEFT, padx=spx, pady=0)
            self.btnUploadData.configure(style="Black.TButton")
            self.RLabelX = Tk.Label(parFrame[FrameX], text = " ", background = StyleBackground)
            self.RLabelX.pack(fill = Tk.X, side = Tk.LEFT, expand = True, padx=(spxm, spxm), pady=0)
            FrameX += 1
            
            self.DataStdoutEdit = Tk.Text(parFrame[FrameX],  wrap="word", highlightthickness = 2, background=StyleInactivecolor, selectbackground = "pale turquoise", selectforeground = "black", height = 5)
            self.DataStdoutEdit.pack(side = Tk.LEFT, fill = Tk.X, expand = 1)
            self.DataStdoutEdit.config(highlightbackground = StyleBackground, highlightcolor = StyleActivecolor)
            FrameX += 1

            self.root.protocol('WM_DELETE_WINDOW', self.onClose)
 
            # center the window
            iw = self.root.winfo_screenwidth()
            ih = self.root.winfo_screenheight()
            isize = (1020, 680)
            ix = (iw - isize[0]) / 2
            iy = (ih - isize[1]) / 2
            self.root.geometry("%dx%d+%d+%d" % (isize + (ix, iy)))

            self.root.minsize(800, 600)

            self.fontsize = 10

            if (os.name == "nt"):
                self.root.iconbitmap(r'iconmain.ico')
            else:
                iconmain = Tk.PhotoImage(file='iconmain.gif')
                self.root.tk.call('wm', 'iconphoto', self.root._w, iconmain)
            # end if

            self.root.deiconify()
            self.setFocus()

            self.GUIstarted = True

            self.root.mainloop()

        except Exception as excT:
            excType, excObj, excTb = sys.exc_info()
            excFile = os.path.split(excTb.tb_frame.f_code.co_filename)[1]
            strErr  = "\n! cannot initialize GUI:\n  %s\n  in %s (line %d)\n" % (str(excT), excFile, excTb.tb_lineno)
            print(strErr)
            os._exit(1)
            # never reached
            pass
        # end try

    # end show

    def monitorAction(self):
        running = self.isRunning()
        try:
            if not running:
                self.setRunning(running = False)
                if self.threadfinish is not None:
                    self.threadfinish()
                    self.threadfinish = None
                # end if
                return
            # end if
            if self.root:
                self.root.after(self.timerduration if ((self.timerduration >= 100) and (self.timerduration <= 1000)) else 200, self.monitorAction)
            # end if
        except Exception as excT:
            pass
        # end try
    # end monitorAction

    def encodeString(self, strT):
        if sys.version_info[0] < 3:
            return strT.encode('utf-8')
        #
        return str
        # end if
    #

    def start(self, tType):

        if self.isRunning():
            return False
        # end if

        self.JSONstdoutEdit.delete('1.0', 'end')
        self.DataStdoutEdit.delete('1.0', 'end')
     
        self.title = self.TitleEdit.get()
        self.description = self.DescriptionEdit.get("1.0", Tk.END).replace("\n", " ").replace("\r", " ")
        self.displayName = self.DisplayNameEdit.get()
        self.subject = self.SubjectEdit.get()
        self.contactname = self.ContactNameEdit.get()
        self.contactaffiliation = self.ContactAffiliationEdit.get()
        self.contactemail = self.ContactEmailEdit.get()
        for ii in range(0, self.AuthorsCount):
            self.author[ii] = self.AuthorEdit[ii].get()
            self.affiliation[ii] = self.AffiliationEdit[ii].get()
            self.identifier[ii] = self.IdentifierEdit[ii].get()
        #
        self.publicationCitation = self.PublicationCitationEdit.get()
        self.notesText = self.NotesEdit.get("1.0", Tk.END).replace("\n", " ").replace("\r", " ")
        for ii in range(0, self.KeywordsCount):
            self.keyword[ii] = self.KeywordEdit[ii].get()
        #
        self.DATAVERSE_KEY = self.KeyEdit.get()
        self.DATAVERSE_SERVER = self.DataverseServerEdit.get()
        self.DATASET_SERVER = self.DatasetServerEdit.get()
        self.JSONfilename = self.JSONfilenameEdit.get()
        self.persistentId = self.persistentIdEdit.get()
        self.DataDirectory = self.DataDirectoryEdit.get()
        self.ReportFilename = self.ReportFilenameEdit.get()
        for ii in range(0, self.DataFilenamesCount):
            self.DataFilename[ii] = self.DataFilenameEdit[ii].get()
        #

        tNow = datetime.datetime.now()
        tDate = tNow.strftime("%Y-%m-%d")

        self.JSONcontent    = self.JSON_TEMPLATE_HEADER
        self.JSONcontent   += self.JSON_TEMPLATE_TITLE % self.title
        self.JSONcontent   += ",\n"
        self.JSONcontent   += self.JSON_TEMPLATE_DESCR % (self.encodeString(self.description), tDate)
        self.JSONcontent   += ",\n"

        self.JSONcontent   +=  self.JSON_TEMPLATE_AUTH_H
        for ii in range(0, self.AuthorsCount):
            if (self.author[ii] != "") and (self.affiliation[ii] != ""):
                self.JSONcontent += self.JSON_TEMPLATE_AUTH % (self.encodeString(self.affiliation[ii]), self.author[ii], self.identifier[ii])
                self.JSONcontent += ",\n"
            #
        #
        if self.JSONcontent.endswith(",\n"):
            self.JSONcontent = self.JSONcontent[:-2]
            self.JSONcontent += "\n"
        #
        self.JSONcontent += self.JSON_TEMPLATE_AUTH_F
        self.JSONcontent += ",\n"

        self.JSONcontent += self.JSON_TEMPLATE_SUBJECT % self.subject
        self.JSONcontent += ",\n"
        self.JSONcontent += self.JSON_TEMPLATE_PUBLI % self.publicationCitation
        self.JSONcontent += ",\n"
        self.JSONcontent += self.JSON_TEMPLATE_NOTES % self.encodeString(self.notesText)
        self.JSONcontent += ",\n"
        
        self.JSONcontent   +=  self.JSON_TEMPLATE_KEYW_H
        for ii in range(0, self.AuthorsCount):
            if (self.keyword[ii] != ""):
                self.JSONcontent += self.JSON_TEMPLATE_KEYW % (self.keyword[ii])
                self.JSONcontent += ",\n"
            #
        #
        if self.JSONcontent.endswith(",\n"):
            self.JSONcontent = self.JSONcontent[:-2]
            self.JSONcontent += "\n"
        #
        self.JSONcontent += self.JSON_TEMPLATE_KEYW_F
        self.JSONcontent += ",\n"

        self.JSONcontent += self.JSON_TEMPLATE_DEP % (self.contactname, tDate)
        self.JSONcontent += ",\n"
        self.JSONcontent += self.JSON_TEMPLATE_CONTACT % (self.contactname, self.encodeString(self.contactaffiliation), self.contactemail)
        self.JSONcontent += "\n"
        self.JSONcontent += self.JSON_TEMPLATE_FOOTER % self.displayName

        self.actionbutton = self.btnUploadJSON if tType == 'JSON' else self.btnUploadData
        self.actionbuttonText = "Upload " + tType
        self.actionText = tType
        self.setRunning(running = True)
        self.thread = UploadThread(id=1, func=self.run)
        self.threadfinish = self.onThreadFinish
        self.thread.start()
        self.monitorAction()

     # end start

    def run(self):

        try:

            global DataMutex
            DataMutex.acquire()
            self.tic = time.time()
            actionText = self.actionText[:]
            JSONfilename = self.JSONfilename[:]
            JSONcontent = self.JSONcontent[:]
            persistentId = self.persistentId[:]
            DataFilenamesCount = self.DataFilenamesCount
            ReportFilename = self.ReportFilename[:]
            ReportDescription = self.ReportDescription[:]
            DataFilename = self.DataFilename[:]
            DataDescription = self.DataDescription[:]
            DATAVERSE_KEY = self.DATAVERSE_KEY[:]
            DATAVERSE_SERVER = self.DATAVERSE_SERVER[:]
            DATASET_SERVER = self.DATASET_SERVER[:]
            CURL_COMMAND_JSON = self.CURL_COMMAND_JSON[:]
            CURL_COMMAND_DATA = self.CURL_COMMAND_DATA[:]
            DataDirectory = self.DataDirectory[:]
            DataMutex.release()

            Stdout = ""
            if actionText == 'JSON':
                JSONfile = open(JSONfilename, "w")
                JSONfile.write(JSONcontent)
                JSONfile.close()
                if os.path.isfile(JSONfilename):
                    if self.os == "Linux":
                        strCmd = "curl " + CURL_COMMAND_JSON % (DATAVERSE_KEY, DATAVERSE_SERVER, JSONfilename)
                        Stdout = subprocess.check_output(shlex.split(strCmd), stderr=subprocess.STDOUT)
                    else:
                        JSONhead = {'X-Dataverse-key': DATAVERSE_KEY}
                        Stdout = requests.post(DATAVERSE_SERVER, headers = JSONhead, data = open(JSONfilename, 'rb').read())
                        Stdout = Stdout.text
                    #
                #
            else:
                if os.path.isfile(ReportFilename):
                    if self.os == "Linux":
                        strCmd = "curl " + CURL_COMMAND_DATA % (DATAVERSE_KEY, ReportFilename, ReportDescription, DataDirectory, DATASET_SERVER, persistentId)
                        Stdout = subprocess.check_output(shlex.split(strCmd), stderr=subprocess.STDOUT)
                    else:
                        JSONhead = {'X-Dataverse-key': DATAVERSE_KEY}
                        Stdout = requests.post(
                            "%s/:persistentId/add?persistentId=%s" % (DATASET_SERVER, persistentId),
                            headers = JSONhead,
                            files = dict(file = open("%s" % ReportFilename, 'rb')),
                            data = dict(jsonData = '{\"description\":\"%s\",\"directoryLabel\":\"%s\",\"categories\":[\"Data\"], \"restrict\":\"false\"}' % (ReportDescription, DataDirectory))
                            )
                        Stdout = Stdout.text
                #
                for ii in range(0, DataFilenamesCount):
                    if os.path.isfile(DataFilename[ii]):
                        if self.os == "Linux":
                            strCmd = "curl " + CURL_COMMAND_DATA % (DATAVERSE_KEY, DataFilename[ii], DataDescription[ii], DataDirectory, DATASET_SERVER, persistentId)
                            Stdout = subprocess.check_output(shlex.split(strCmd), stderr=subprocess.STDOUT)
                        else:
                            JSONhead = {'X-Dataverse-key': DATAVERSE_KEY}
                            Stdout = requests.post(
                                "%s/:persistentId/add?persistentId=%s" % (DATASET_SERVER, persistentId),
                                headers = JSONhead,
                                files = dict(file = open("%s" % DataFilename[ii], 'rb')),
                                data = dict(jsonData = '{\"description\":\"%s\",\"directoryLabel\":\"%s\",\"categories\":[\"Data\"], \"restrict\":\"false\"}' % (DataDescription[ii], DataDirectory))
                                )
                            Stdout = Stdout.text
                    #
                #
            #

            DataMutex.acquire()
            self.Stdout = Stdout
            self.tic = float(time.time() - self.tic)
            DataMutex.release()

            self.setRunning(running = False)

            return True

        except Exception as excT:

            excType, excObj, excTb = sys.exc_info()
            excFile = os.path.split(excTb.tb_frame.f_code.co_filename)[1]
            strErr  = "\n! cannot upload the to dataverse:\n  %s\n  in %s (line %d)\n" % (str(excT), excFile, excTb.tb_lineno)
            print(strErr)
            return False
            # never reached
            pass

        # end try

    # end run

    def setFocus(self):
        if (not self.root):
            return
        # end if
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)
        self.root.after(10, lambda: self.root.focus_force())
    # end setFocus

    def onThreadFinish(self):
        try:
            self.monitorAction()
        except Exception as excT:
            pass
        # end try
    # end onThreadFinish

    def onInputValidate(self, sp):
        try:
            if (not sp) or (len(sp) <= 255):
                self.dataFilenameEdit.prev = sp
                return True
            # end if
            return False
        except:
            return True
        # end try
    # end onInputValidate

    def onBrowse(self, event):
        if self.isRunning() or not self.GUIstarted:
            return
        # end if

        tEdit = self.Buttons[event.widget][0]
        tType = self.Buttons[event.widget][1]

        fileopt = {}
        fileopt['defaultextension'] = 'txt'
        fileopt['filetypes'] = [('JSON File', '*.json')] if tType == 'JSON' else ([('Data File', '*.txt')] if tType == 'Data' else [('Report File', '*.pdf')])
        fileopt['initialfile'] = tEdit.get()
        fileopt['parent'] = self.root
        fileopt['title'] = 'Open JSON File' if tType == 'JSON' else 'Open Data File'
        inputFilename = tkFileDialog.askopenfilename(**fileopt)
        if inputFilename:
            try:
                for ii in range(0, self.DataFilenamesCount):
                    if self.DataFilenameEdit[ii].get() == inputFilename:
                        MessageBox(self,
                            title = self.name,
                            message = "File already added",
                            TwoButton = False)
                        return
                    #
                #
                tEdit.delete(0, Tk.END)
                tEdit.insert(0, inputFilename)
            except:
                pass
            # end try
        # end if
    # end onBrowse

    def onUploadOK(self):
        return self.start(self.action)
    #

    def onUploadJSON(self):
        self.action = 'JSON'
        MessageBox(self,
            title = self.name,
            message = "Are all the metadata correctly filled? Upload JSON?",
            labelA = "Yes",
            labelB = "No",
            callbackA = self.onUploadOK)
    # end onUploadJSON

    def onUploadData(self):
        self.action = 'Data'
        MessageBox(self,
            title = self.name,
            message = "Are all the fields correctly filled? Upload data?",
            labelA = "Yes",
            labelB = "No",
            callbackA = self.onUploadOK)
    # end onUploadData

    def onEntryUndo(self, event):
        if not self.GUIstarted:
            return
        # end if
        try:
            if event.widget.prev is not None:
                event.widget.next = event.widget.get()
                strT = event.widget.prev
                idx = event.widget.index(Tk.INSERT)
                event.widget.delete(0, Tk.END)
                event.widget.insert(0, strT)
                event.widget.prev = strT
                event.widget.icursor(idx + 1)
            #
        except:
            pass
        # end try
    # end onEntryUndo

    def onEntryRedo(self, event):
        if not self.GUIstarted:
            return
        # end if
        try:
            if event.widget.next is not None:
                idx = event.widget.index(Tk.INSERT)
                strT = event.widget.prev
                event.widget.delete(0, Tk.END)
                event.widget.insert(0, event.widget.next)
                event.widget.prev = strT
                event.widget.icursor(idx + 1)
            #
        except:
            pass
        # end try
    # end onEntryRedo

    def onEntrySelectAll(self, event):
        if not self.GUIstarted:
            return
        # end if
        try:
            event.widget.select_range(0, Tk.END)
        except:
            pass
        # end try
    # end onEntrySelectAll

    def onTextPaste(self, event):
        try:
            event.widget.delete("sel.first", "sel.last")
        except:
            pass
        #
        event.widget.insert("insert", event.widget.clipboard_get().strip())
        return "break"
    # end onTextPaste
    
    def onAbout(self):
        if not self.GUIstarted:
            return
        # end if
        MessageBox(self,
            title = self.name,
            message =  (self.name                                       +
            "\n"                                                        +
            self.__version__                                            +
            "\n(C) Université de Lorraine"),
            TwoButton = False)
    # end onAbout

    def onClose(self):
        if (not self.GUIstarted) or (self.root is None):
            return
        # end if
        try:
            if self.isRunning():
                if self.actionbutton == self.btnUploadJSON:
                    self.JSONstdoutEdit.insert("end", "\nPlease wait until uploading done.\n")
                else:
                    self.DataStdoutEdit.insert("end", "\nPlease wait until uploading done.\n")
                return
            # end if
            self.root.quit()
            self.root.destroy()
            self.root = None
        except:
            pass
        # end try
    # end onClose

# end DataverseCore class
