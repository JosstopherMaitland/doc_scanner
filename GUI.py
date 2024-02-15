import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import os
import cv2
import imutils
import numpy as np
from PIL import Image, ImageTk
from Final import documentScan, location, addSymbol, multAddSym, editSymbol, deleteSymbol

# my foundation class inherits from an in built tkinter class
class foundation(tk.Tk):
	def __init__(self):
		# initialise tkinter
		tk.Tk.__init__(self)
		# create container
		self.container = tk.Frame(self)

		self.wm_title("Document Scanner")

		# everything in container will be packed to the top, fill all alloted space and expand the window if needed.
		self.container.pack(side="top", fill="both", expand = True)

		# configure grid for conatiner (minimum size = 0 and row and col have same priority)
		self.container.grid_rowconfigure(0, weight=1)
		self.container.grid_columnconfigure(0, weight=1)

		# dictionary where pages of app will be stored
		self.pages = {}

		self.docFiles = []
		self.symRefs = []
		self.symImgs = []

		self.choices = {'Predict':0, 'A/B-series':0.71, 'RA/SRA-series':0.7, 'Letter':0.77}
		self.tkvarPaperSizes = tk.StringVar(self)
		self.tkvarPaperSizes.set('A/B-series')
		self.tkvarPaperSize = tk.DoubleVar(self)

                # cycle through pages, instantiate them and add them to the pages dictionary
		for F in (main, symbols):
			page = F(self.container, self)
			self.pages[F] = page
			page.grid(row=0, column=0, sticky="nsew")

		# run the show_page method to show the main page
		self.showPage(main)

	def onClosing(self):
		for file in range(len(self.docFiles)):
			name = 'docCache/' + self.docFiles[file].replace('/','').replace(':','')
			os.remove(name)
		self.destroy()

	# method for showing pages
	def showPage(self, cont):
		# raise the page passed, so it is displayed in the container
		page = self.pages[cont]
		page.tkraise()


	def scroll(self, cont):
		def function(event):
			canvas.configure(scrollregion=canvas.bbox("all"),width=800,height=150)
		
		# scrollable frame
		# create seperate frame so it can be scolled seperately
		frame = tk.Frame(cont, relief = 'groove', width = 50, height = 150, bd = 1)
		frame.grid(row = 0, column = 0, columnspan = 3)

		# create canvas embedded in frame
		canvas = tk.Canvas(frame)
		mFrame = tk.Frame(canvas)

		# create horizontal scrollbar for frame and pack it to the bottom
		scrollbar = tk.Scrollbar(frame, orient = 'horizontal', command = canvas.xview)
		canvas.configure(xscrollcommand = scrollbar.set)
		scrollbar.pack(side = 'bottom', fill = 'x')

		# configure canvas for scrolling
		canvas.pack(side='left')
		canvas.create_window((0,0),window=mFrame,anchor='nw')
		mFrame.bind('<Configure>', function)

		return mFrame

	# validation for names of symbols
	def validateName(self, S):
		if S.isalpha() == True:
			return True
		else:
			self.bell()
			return False

	def popup(self, message, window):
		def close():
			window.grab_set()
			popup.destroy()
		popup = tk.Toplevel(self)
		popup.grab_set()
		popup.wm_title("!")
		label = tk.Label(popup, text=message, font=('Helvetica', 11), justify='left')
		label.pack(side="top", fill="x", pady=10)
		B1 = tk.Button(popup, text="Okay", command = close)
		B1.pack()
		popup.protocol("WM_DELETE_WINDOW", close)

# main page class
class main(tk.Frame):
	def __init__(self, parent, controller):
		# initialise tkiner frame
		tk.Frame.__init__(self,parent)

		docDisplay = controller.scroll(self)

		self.choices = {'Predict':0, 'A/B-series':0.71, 'RA/SRA-series':0.7, 'Letter':0.77}
		self.tkvarPaperSizes = tk.StringVar(self)
		self.tkvarPaperSizes.set('A/B-series')
		self.tkvarPaperSize = tk.DoubleVar(self)

		# buttons (lambda is used so parameters can be passed into functions within command)
		browseButton = tk.Button(self, text="Browse", height=3, width=15, command=lambda: self.browseDoc(controller))
		browseButton.grid(row = 1, column = 1)

		scanButton = tk.Button(self, text="Scan", height=3, width=15, command=lambda: self.scan(controller))
		scanButton.grid(row = 2, column = 1)

		symbolsButton = tk.Button(self, text="Symbols", height=3, width=15, command=lambda: controller.showPage(symbols))
		symbolsButton.grid(row = 1, column = 0)

		helpButton = tk.Button(self, text="Help", height=3, width=15, command=lambda: self.help(controller))
		helpButton.grid(row = 1, column = 2)

		if len(controller.docFiles) == 0:
			# temporary message for when the frame is empty
			emptyMess = tk.Label(docDisplay, text = 'No Documents', font = ('Helvetica', 20))
			emptyMess.pack(side = 'left')
		else:
                        # fill scrollable frame with the documents added
			for file in range(len(controller.docFiles)):
				name = 'docCache/' + controller.docFiles[file].replace('/','').replace(':','')
				doc = cv2.imread(name)
				thumbnail = Image.fromarray(doc)
				thumbnail = ImageTk.PhotoImage(thumbnail)
				image = tk.Button(docDisplay, image=thumbnail, command=lambda file=file: self.delDoc(file, controller))
				image.image = thumbnail
				image.pack(side='left')

	def browseDoc(self, controller):
		# open tkinter file manager and store the path to the file they chose to filename
		fileNames = filedialog.askopenfilenames(filetypes =(("Image File", "*.jpg"),
							  ("Image File", "*.jpeg"),
							  ("Image File", "*.jpe"),
							  ("Image File", "*.jp2"),
							  ("Image File", "*.png"),
							  ("Image File", "*.webp"),
							  ("Image File", "*.pbm"),
							  ("Image File", "*.pgm"),
							  ("Image File", "*.ppm"),
							  ("Image File", "*.sr"),
							  ("Image File", "*.ras"),
							  ("Image File", "*.tiff"),
							  ("Image File", "*.tif"),
							  ("Image File", "*.bmp"),
							  ("Image File", "*.dib")),
			   title = "Choose an Image.")
		

		addedFiles = []
		for file in fileNames:
			if file in controller.docFiles:
				addedFiles.append(file)
			else:
				controller.docFiles.append(file)
				doc = cv2.imread(file)
				doc = imutils.resize(doc, height=150)
				doc = cv2.cvtColor(doc, cv2.COLOR_BGR2RGB)
				name = file.replace('/','').replace(':','')
				cv2.imwrite('docCache/' + name, doc)
		
		page = main(controller.container, controller)
		controller.pages[main] = page
		page.grid(row=0, column=0, sticky="nsew")
		
		if len(addedFiles) != 0:
			controller.popup('File(s)\n' + ', \n'.join(addedFiles) + '\nalready added.', controller)
			
	def delDoc(self, doc, controller):
		os.remove('docCache/' + controller.docFiles[doc].replace('/','').replace(':',''))

		del controller.docFiles[doc]

		page = main(controller.container, controller)
		controller.pages[main] = page
		page.grid(row=0, column=0, sticky="nsew")

	def paperSizePopup(self):
		popupPaper = self.popupPaper = tk.Toplevel(self)
		popupPaper.grab_set()
		popupPaper.wm_title("Paper Size")
		label = tk.Label(popupPaper, text='Enter Paper Size for the documents:', font=('Helvetica', 11))
		label.pack(side="top", fill="x", pady=10)
		menu = tk.OptionMenu(popupPaper, self.tkvarPaperSizes, *self.choices.keys())
		menu.pack()
		B1 = tk.Button(popupPaper, text="Okay", command = popupPaper.destroy)
		B1.pack()

	def scan(self, controller):
                # check there are symbols and documents ready
		if len(controller.docFiles) == 0:
			controller.popup('No documents prepared.', controller)
			return
		if len(controller.symImgs) == 0:
			controller.popup('No symbols stored.', controller)
			return

		# create empty string variable for report
		report = '\n'

		self.paperSizePopup()
		self.wait_window(self.popupPaper)
		paperSize = self.choices[self.tkvarPaperSizes.get()]
		
		for doc in range(len(controller.docFiles)):

			document = documentScan(controller.docFiles[doc], paperSize)

			report += 'Document ' + str(doc+1) + ': '

			if type(document) == int:
				report += 'No document found\n'
				continue

                        ## TESTING
			cv2.imwrite('Testing/document' + str(doc+1) + '.jpg', document[2])
                        ## TESTING

			outlines = document[0]

			numberOut = len(outlines)

			grayDocument = document[1]
			origDocument = document[2]

			if numberOut == 0:
				path = location(grayDocument)

				if path == '1':
					report += "No Circle or Symbol Found\n"
					continue

				name = controller.symRefs[path][1] + '/image' + str(doc + 1) + '.jpg'
				cv2.imwrite(name, origDocument)

				report += controller.symRefs[path][0] + '\n'
				continue

			report += '\n'

			for oul in range(numberOut):
				# crop outlines
				outline = grayDocument[outlines[oul][0]:outlines[oul][1], outlines[oul][2]:outlines[oul][3]]

				## TESTING
				bounds = outlines[oul]
				cv2.imwrite('Testing/outline'+str(doc+1)+'.'+str(oul+1)+'.jpg', origDocument[bounds[0]:bounds[1], bounds[2]:bounds[3]])
				## TESTING
				
				path = location(outline)

				report += '\tOutline ' + str(oul+1) + ': '

				if path == '1':
					report += "No Circle or Symbol Found\n"
					continue

				bounds = outlines[oul]
				name = controller.symRefs[path][1] + '/image' + str(doc + 1) + '.' + str(oul + 1) + '.jpg'
				cv2.imwrite(name, origDocument[bounds[0]:bounds[1], bounds[2]:bounds[3]])

				report += controller.symRefs[path][0] + '\n'

		controller.popup("Done. The report, that should have opened,\nis stored where this program is stored.", controller)
		
		with open('report.txt', 'w') as reportFile:
			reportFile.write('Report:' + report)
			
		os.startfile('report.txt')
                        
	def help(self, controller):
		def close():
			controller.grab_set()
			window.destroy()
			
		window = tk.Toplevel(self)

		window.grab_set()

		window.wm_title("Help")
		
		about = "This software scans pictures of documents, flattens them as if they were scanned and then stores the document or parts of the document to locations on your computer. To tell the software where to save the document, you draw a symbol on it. These symbols are uploaded to the software and given a location before you start the scan and they are created by you. You don't have to save the whole document though. By drawing rectangular outlines on the document, the software will extract only those parts and save them instead (you can have as many outlines on one document as you like). To then specify where they should be saved, draw a symbol in them. All symbols should be drawn within a circle. For example:"
		imageInfo = 'This symbol refers to the location C:\\Users\\Joss\\Documents on the computer and so the outline crop is stored there.'
		how = "To add images ready to be scanned, click the browse button and select them in the file manager. Once added, they should appear on the main menu. Once enough have been added you should be able to scroll through them.\nTo remove any images from the scan queue, click on them.\nWhen you’re ready to scan them, click scan. A new window should open that will allow you to select the paper size of the document(s) you’ve added. Use the drop down to select the paper size. If you’re scanning an image with a document that isn’t a standard size, use the ‘predict’ option. The option you choose will be applied to all the documents currently in queue.\nClick the symbols button to navigate to the symbols page, where you can add and edit symbols and the location they refer to."
		documents = "                        For the software to accurately scan documents and flatten them, make sure the document is on a dark background (contrasting to the document colour). Make sure none of the edges of the document are covered, folded or curved."
		outlines = "                  Try to draw the outlines as rectangular as you can and ensure it is made up of a continuous connected line (no gaps). The line must be the same shade all the way along, as even a slightly lighter part of the line can be regarded as a gap."
		circles = "                Again, try to keep these as circular as you can and without gaps."
		symbols = "                   Make sure the symbol is one continuous drawn shape (not split into multiple parts) and is not connected to the circle."

		canvas = tk.Canvas(window, width=660, height=875)
		canvas.create_text(5, 0, anchor='nw', text='About:', font=('Helvetica', 14, 'bold'))
		canvas.create_text(5, 25, anchor='nw', text=about, font=('Helvetica', 11), justify = 'left', width = 660)

		self.aboutPicture = ImageTk.PhotoImage(Image.open('helpImages/about.jpg'))
		canvas.create_image(5,170, anchor='nw', image=self.aboutPicture)

		canvas.create_text(470, 310, anchor='nw', text=imageInfo, font=('Helvetica', 11), justify = 'left', width = 175)

		canvas.create_text(5, 480, anchor='nw', text='How:', font=('Helvetica', 14, 'bold'))
		canvas.create_text(5, 505, anchor='nw', text=how, font=('Helvetica', 11), justify = 'left', width = 660)

		canvas.create_text(5, 685, anchor='nw', text='Important:', font=('Helvetica', 14, 'bold'))

		canvas.create_text(5, 710, anchor='nw', text='Documents:', font=('Helvetica', 12, 'bold'))
		canvas.create_text(5, 710, anchor='nw', text=documents, font=('Helvetica', 11), justify = 'left', width = 660)

		canvas.create_text(5, 765, anchor='nw', text='Outlines:', font=('Helvetica', 12, 'bold'))
		canvas.create_text(5, 765, anchor='nw', text=outlines, font=('Helvetica', 11), justify = 'left', width = 660)
		
		canvas.create_text(5, 820, anchor='nw', text='Circles:', font=('Helvetica', 12, 'bold'))
		canvas.create_text(5, 820, anchor='nw', text=circles, font=('Helvetica', 11), justify = 'left', width = 660)
		
		canvas.create_text(5, 840, anchor='nw', text='Symbols:', font=('Helvetica', 12, 'bold'))
		canvas.create_text(5, 840, anchor='nw', text=symbols, font=('Helvetica', 11), justify = 'left', width = 660)

		canvas.pack()

		B1 = tk.Button(window, text="Okay", command = close)
		B1.pack()

		window.protocol("WM_DELETE_WINDOW", close)

class symbols(tk.Frame):
	def __init__(self, parent, controller):
		# initialise tkiner frame
		tk.Frame.__init__(self,parent)

		symDisplay = controller.scroll(self)

		self.path = False
		self.file = ''

		# buttons
		mainButton = tk.Button(self, text="Main Menu", height=3, width=15, command=lambda: controller.showPage(main))
		mainButton.grid(row = 1, column = 0)

		addButton = tk.Button(self, text="Add Symbols", height=3, width=15, command=lambda: self.sAddSelect(controller))
		addButton.grid(row = 1, column = 1)

		helpButton = tk.Button(self, text="Help", height=3, width=15, command=lambda: self.helpSym(controller))
		helpButton.grid(row = 1, column = 2)

		controller.symRefs = np.genfromtxt('symbols/reference.data', dtype='str', delimiter=',')
		controller.symImgs = np.loadtxt('symbols/symbols.data', np.float32)

		try:
			controller.symRefs = controller.symRefs.reshape((1,2))
		except ValueError:
			pass

		try:
			controller.symImgs = controller.symImgs.reshape((1,900))
		except ValueError:
			pass

		length = len(controller.symRefs)
		
		if length == 0:
			# temporary message for when the frame is empty
			emptyMess = tk.Label(symDisplay, text = 'No Symbols', font = ('Helvetica', 20))
			emptyMess.pack(side = 'left')
		else:
			# fill scrollable frame with symbols stored
			for img in range(length):
				name = controller.symRefs[img][0]
				text = tk.Label(symDisplay, text=name)
				symbol = controller.symImgs[img]
				symbol = symbol.reshape((30,30))
				symbol = imutils.resize(symbol, height=125)
				symbol = Image.fromarray(symbol)
				symbol = ImageTk.PhotoImage(symbol)
				image = tk.Button(symDisplay, image=symbol, command=lambda img=img: self.sEdit(img,controller))
				image.image = symbol				
				image.grid(column=img, row=0)
				text.grid(column=img, row=1)

	### ADD SYMBOLS
	def sAddSelect(self, controller):
		def findSymbols():
			if self.file != '':
				symbolCrops = multAddSym(self.file)
				symbolsImage = cv2.imread(self.file)
				self.sAdd(controller, symbolsImage, symbolCrops, 0)
				window.destroy()
			else:
				controller.popup('Please select an image.', window)
		
		# create new child window
		window = tk.Toplevel(self)

		# ensure user cannot click anywhere other than on this window
		window.grab_set()

		window.wm_title("Add Symbols")

		# image
		self.symbolLabel = tk.Label(window, text = 'No Symbols', font = ('Helvetica', 20), height=10, width=20, background='gray75')
		self.symbolLabel.grid(row=0, column=0, columnspan=2)

		# buttons
		browseButton = tk.Button(window, text="Browse", height=3, width=15, command=lambda: self.browseSym(controller))
		browseButton.grid(row = 1, column = 1)

		proceedButton = tk.Button(window, text="Proceed", height=3, width=15, command=findSymbols)
		proceedButton.grid(row = 1, column = 0)

		helpButton = tk.Button(window, text="Help", height=3, width=15, command=lambda: self.helpAddSelect(window))
		helpButton.grid(row = 1, column = 2)

	def sAdd(self, controller, symbolsImage, symbolCrops, sym):
		def save(x, sym, name, path):
			if x == 1:
				if path != False and name != '':
					error = addSymbol(symbol, name, path)
					if error == 0:
						controller.popup('Symbol name taken or \n symbol already stored.', window)
						
					elif sym != len(symbolCrops) - 1:
						sym += 1
						window.destroy()
						self.sAdd(controller, symbolsImage, symbolCrops, sym)

					else:
						page = symbols(controller.container, controller)
						controller.pages[symbols] = page
						page.grid(row=0, column=0, sticky="nsew")
						window.destroy()
						
				else:
					controller.popup('Please give the symbol a name \n and assign it a path.', window)
					
			elif sym != len(symbolCrops) - 1:
				sym += 1
				window.destroy()
				self.sAdd(controller, symbolsImage, symbolCrops, sym)

			else:
				page = symbols(controller.container, controller)
				controller.pages[symbols] = page
				page.grid(row=0, column=0, sticky="nsew")
				window.destroy()

		# create new child window
		window = tk.Toplevel(self)

		# ensure user cannot click anywhere other than on this window
		window.grab_set()

		window.wm_title("Add Symbols")

		self.path = False

		# location label
		self.location = tk.Label(window, text = 'No Location', font = ('Helvetica', 16), wraplength = 327)
		self.location.grid(row=2, column=0, columnspan=2)

		# entry for name
		vcmd = (self.register(controller.validateName), '%S')
		enterName = tk.Entry(window, font=('Helvetica', 16), validate='key', validatecommand=vcmd)
		enterName.insert(0, 'Name')
		enterName.grid(row=0, column=0, columnspan=2)

		symbol = symbolsImage[symbolCrops[sym][0]:symbolCrops[sym][1], symbolCrops[sym][2]:symbolCrops[sym][3]]

		symbolD = cv2.resize(symbol, (327, 327))
		symbolD = cv2.cvtColor(symbolD, cv2.COLOR_BGR2RGB)
		symbolD = Image.fromarray(symbolD)
		symbolD = ImageTk.PhotoImage(symbolD)
		symbolLabel = tk.Label(window, image = symbolD, height = 327, width = 327)
		symbolLabel.image = symbolD
		symbolLabel.grid(row = 1, column = 0, columnspan = 2)

		# buttons
		discardButton = tk.Button(window, text="Discard", height=3, width=15, command=lambda: save(0, sym, 0, 0))
		discardButton.grid(row = 3, column = 1)

		assignButton = tk.Button(window, text="Assign", height=3, width=15, command=lambda: self.browsePath(controller))
		assignButton.grid(row = 0, column = 2)

		saveButton = tk.Button(window, text="Save", height=3, width=15, command=lambda: save(1, sym, enterName.get(), self.path))
		saveButton.grid(row = 3, column = 0)

		helpButton = tk.Button(window, text="Help", height=3, width=15, command=lambda: self.helpAdd(window))
		helpButton.grid(row = 3, column = 2)
	
	def browsePath(self, controller):
		# select folder using Tkinter file manager and verify entry
		folder = filedialog.askdirectory(title = "Choose a Folder.")

		if folder != '':
			self.path = folder
			self.location.config(text=folder)

	def browseSym(self, controller):
		# select image file using Tkinter file manager and verify entry
		file = filedialog.askopenfilename(filetypes =(("Image File", "*.jpg"),
							  ("Image File", "*.jpeg"),
							  ("Image File", "*.jpe"),
							  ("Image File", "*.jp2"),
							  ("Image File", "*.png"),
							  ("Image File", "*.webp"),
							  ("Image File", "*.pbm"),
							  ("Image File", "*.pgm"),
							  ("Image File", "*.ppm"),
							  ("Image File", "*.sr"),
							  ("Image File", "*.ras"),
							  ("Image File", "*.tiff"),
							  ("Image File", "*.tif"),
							  ("Image File", "*.bmp"),
							  ("Image File", "*.dib")),
			   title = "Choose an Image.")

		if file != '':
			# add image to symbol label
			symbol = cv2.imread(file)
			self.file = file
			symbol = cv2.resize(symbol, (327, 327))
			symbol = cv2.cvtColor(symbol, cv2.COLOR_BGR2RGB)
			symbol = Image.fromarray(symbol)
			symbol = ImageTk.PhotoImage(symbol)
			self.symbolLabel.config(image = symbol, height = 327, width = 327)
			self.symbolLabel.image = symbol

	def save(self, window, name, path, file, controller):
		if path != False and file != '' and name != '':
			image = cv2.imread(file)
			error = addSymbol(image, name, path)
			if error == 0:
				controller.popup('Symbol name taken or \n symbol already stored.', window)
				
			else:
				page = symbols(controller.container, controller)
				controller.pages[symbols] = page
				page.grid(row=0, column=0, sticky="nsew")
				window.destroy()
		else:
			controller.popup('Please select a symbol, \n give it a name \n and assign it a path.', window)
	### ADD SYMBOLS

	### EDIT SYMBOLS
	def sEdit(self, img, controller):
		# create new child window
		window = tk.Toplevel(self)
		
		window.grab_set()

		window.wm_title("Edit Symbol")

		self.path = controller.symRefs[img][1]
		name = controller.symRefs[img][0]
		symbol = controller.symImgs[img]
		
		# location label
		self.location = tk.Label(window, text = self.path, font = ('Helvetica', 16), wraplength = 327)
		self.location.grid(row=2, column=0, columnspan=2)

		# preview
		symbol = symbol.reshape((30,30))
		symbol = cv2.resize(symbol, (327,327))
		symbol = Image.fromarray(symbol)
		symbol = ImageTk.PhotoImage(symbol)
		image = tk.Label(window, image=symbol)
		image.image = symbol
		image.grid(row=1, column=0, columnspan=2)

		# entry for name
		vcmd = (self.register(controller.validateName), '%S')
		enterName = tk.Entry(window, font=('Helvetica', 16), validate='key', validatecommand=vcmd)
		enterName.insert(0, name)
		enterName.grid(row=0, column=0, columnspan=2)

		# buttons
		delButton = tk.Button(window, text="Delete", height=3, width=15, command=lambda: self.delSym(window, img, controller))
		delButton.grid(row = 3, column = 1)

		assignButton = tk.Button(window, text="Assign", height=3, width=15, command=lambda: self.browsePath(controller))
		assignButton.grid(row = 0, column = 2)

		saveButton = tk.Button(window, text="Save", height=3, width=15, command=lambda: self.edit(window, enterName.get(), self.path, img, controller))
		saveButton.grid(row = 3, column = 0)

		helpButton = tk.Button(window, text="Help", height=3, width=15, command=lambda: self.helpEdit(window))
		helpButton.grid(row = 3, column = 2)

	def edit(self, window, name, path, img, controller):
		if name != '':
			error = editSymbol(img, name, path)
			if error != 0:
				page = symbols(controller.container, controller)
				controller.pages[symbols] = page
				page.grid(row=0, column=0, sticky="nsew")
				window.destroy()
			else:
				controller.popup('Symbol name taken.', window)
		else:
			controller.popup('Please give the symbol a name.', window)

	def delSym(self, window, img, controller):
		deleteSymbol(img)
		page = symbols(controller.container, controller)
		controller.pages[symbols] = page
		page.grid(row=0, column=0, sticky="nsew")
		window.destroy()
	### EDIT SYMBOLS

	def helpSym(self, controller):
		def close():
			controller.grab_set()
			window.destroy()
			
		window = tk.Toplevel(self)

		window.grab_set()

		window.wm_title("Help")
		
		how = "To add symbols, click Add Symbols. Once you’ve added your symbols, you should see them displayed on the symbols page. Once you’ve added lots of symbols, you’ll be able to scroll through them using the horizontal scroll bar.\nTo edit the symbols, click on the symbols on display. There you can change their name and/or the location they refer to."
		gaps = "Make sure any symbols you add are one continuous drawn shape (not split into multiple parts):"
		fill = "Don’t use symbols with any filled in parts:"
		contain = "Avoid symbols that contain other symbols you’ve already added:"
		
		canvas = tk.Canvas(window, width=560, height=690)
		canvas.create_text(5, 0, anchor='nw', text='How:', font=('Helvetica', 14, 'bold'))
		canvas.create_text(5, 25, anchor='nw', text=how, font=('Helvetica', 11), justify = 'left', width = 560)

		canvas.create_text(5, 115, anchor='nw', text='Important:', font=('Helvetica', 14, 'bold'))

		canvas.create_text(5, 140, anchor='nw', text=gaps, font=('Helvetica', 11), justify = 'left', width = 560)
		self.gapPicture = ImageTk.PhotoImage(Image.open('helpImages/gap.jpg'))
		canvas.create_image(5,177, anchor='nw', image=self.gapPicture)

		canvas.create_text(5, 337, anchor='nw', text=fill, font=('Helvetica', 11), justify = 'left', width = 560)
		self.fillPicture = ImageTk.PhotoImage(Image.open('helpImages/fill.jpg'))
		canvas.create_image(5,357, anchor='nw', image=self.fillPicture)
		
		canvas.create_text(5, 517, anchor='nw', text=contain, font=('Helvetica', 11), justify = 'left', width = 560)
		self.containsPicture = ImageTk.PhotoImage(Image.open('helpImages/contains.jpg'))
		canvas.create_image(5,537, anchor='nw', image=self.containsPicture)

		canvas.pack()

		B1 = tk.Button(window, text="Okay", command = close)
		B1.pack()

		window.protocol("WM_DELETE_WINDOW", close)

	def helpAddSelect(self, parent):
		def close():
			parent.grab_set()
			window.destroy()
			
		window = tk.Toplevel(self)

		window.grab_set()

		window.wm_title("Help")
		
		how = "Here you can add either a single symbol or multiple from one image. For example:"
		imageInfo = "As you can see, the image doesn’t have to only contain the symbol."
		howMore = "To add this image click browse and a file manager you should be familiar with will open. Find the image you’d like to add, select it and then click open. You should see preview a of it in the window. It may look a bit distorted but that’s nothing to worry about, it’s just a preview. Once it’s added, click proceed and the program will locate the symbol or symbols within the image. A new window should open."
		small = "Make sure the symbols aren’t too small in the image. Make them as large as you can."
		
		canvas = tk.Canvas(window, width=735, height=325)
		canvas.create_text(5, 0, anchor='nw', text='How:', font=('Helvetica', 14, 'bold'))
		canvas.create_text(5, 25, anchor='nw', text=how, font=('Helvetica', 11), justify = 'left', width = 735)

		self.symbolsPicture = ImageTk.PhotoImage(Image.open('helpImages/symbols.jpg'))
		canvas.create_image(5,45, anchor='nw', image=self.symbolsPicture)

		canvas.create_text(160, 52, anchor='nw', text=imageInfo, font=('Helvetica', 11), justify = 'left', width = 735)

		canvas.create_text(5, 200, anchor='nw', text=howMore, font=('Helvetica', 11), justify = 'left', width = 735)

		canvas.create_text(5, 280, anchor='nw', text='Important:', font=('Helvetica', 14, 'bold'))

		canvas.create_text(5, 305, anchor='nw', text=small, font=('Helvetica', 11), justify = 'left', width = 735)

		canvas.pack()

		B1 = tk.Button(window, text="Okay", command = close)
		B1.pack()

		window.protocol("WM_DELETE_WINDOW", close)

	def helpAdd(self, parent):
		def close():
			parent.grab_set()
			window.destroy()
			
		window = tk.Toplevel(self)

		window.grab_set()

		window.wm_title("Help")
		
		how = "An image should now be displayed in the window. If this is an image of a symbol you’d like to add you can now give it a name and assign it a location to refer to. To choose a name, write it in the entry box at the top (you can’t use symbols or numbers, only letters). To choose the location the symbol refers to, click the assign button. A familiar file manager should open, and you can find and select the folder you’d like to use. You should see the location displayed below the image preview. Once you’ve given the symbol a name and a location, click save.\nThe program is now cycling through all the images it has found in the image you’ve given it. This means, it may find what it thinks is a symbol, but it isn’t. If the image in the display is not of a symbol you’d like to add, click discard. For example:"
		howMore = "If your symbol never appears, your symbol(s) may be too small in the image or has gaps in it.\nOnce the program has cycled through all the symbols it thinks it has found in the image, you will be navigated back to the symbols page, where you should see all your added symbols."
		
		canvas = tk.Canvas(window, width=420, height=500)
		canvas.create_text(5, 0, anchor='nw', text='How:', font=('Helvetica', 14, 'bold'))
		canvas.create_text(5, 25, anchor='nw', text=how, font=('Helvetica', 11), justify = 'left', width = 420)

		self.discardPicture = ImageTk.PhotoImage(Image.open('helpImages/discard.jpg'))
		canvas.create_image(5,258, anchor='nw', image=self.discardPicture)

		canvas.create_text(5, 415, anchor='nw', text=howMore, font=('Helvetica', 11), justify = 'left', width = 420)

		canvas.pack()

		B1 = tk.Button(window, text="Okay", command = close)
		B1.pack()

		window.protocol("WM_DELETE_WINDOW", close)

	def helpEdit(self, parent):
		def close():
			parent.grab_set()
			window.destroy()
			
		window = tk.Toplevel(self)

		window.grab_set()

		window.wm_title("Help")
		
		how = "This window should look very similar to the window used to add a symbol. It works very similarly. You can change the name of the symbol using the entry box and change the location it refers to using the assign button. When you’re done, you can click Save. If you’d like to delete the symbol, click the Delete button. If you’d like to cancel any changes you’ve made simply close the window."

		canvas = tk.Canvas(window, width=420, height=145)
		canvas.create_text(5, 0, anchor='nw', text='How:', font=('Helvetica', 14, 'bold'))
		canvas.create_text(5, 25, anchor='nw', text=how, font=('Helvetica', 11), justify = 'left', width = 420)
		
		canvas.pack()

		B1 = tk.Button(window, text="Okay", command = close)
		B1.pack()

		window.protocol("WM_DELETE_WINDOW", close)

app = foundation()
app.protocol("WM_DELETE_WINDOW", app.onClosing)
app.mainloop()
