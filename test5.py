import pygame as py

# SCREEN CLASS FOR WINDOW HAVING THE FUNCTION
# OF UPDATING THE ONE SCREEN TO ANOTHER SCREEN


class Screen():

	# INITIALIZATION OF WINDOW HAVING TITLE,
	# WIDTH, HEIGHT AND COLOUR
	# HERE (0,0,255) IS A COLOUR CODE
	def __init__(self, title, width=440, height=445,
				fill=(0, 0, 255)):
		# HEIGHT OF A WINDOW
		self.height = height
		# TITLE OF A WINDOW
		self.title = title
		# WIDTH OF A WINDOW
		self.width = width
		# COLOUR CODE
		self.fill = fill
		# CURRENT STATE OF A SCREEN
		self.CurrentState = False

	# DISPLAY THE CURRENT SCREEN OF
	# A WINDOW AT THE CURRENT STATE
	def makeCurrentScreen(self):
	
		# SET THE TITLE FOR THE CURRENT STATE OF A SCREEN
		py.display.set_caption(self.title)
		# SET THE STATE TO ACTIVE
		self.CurrentState = True
		# ACTIVE SCREEN SIZE
		self.screen = py.display.set_mode((self.width,
										self.height))

	# THIS WILL SET THE STATE OF A CURRENT STATE TO OFF
	def endCurrentScreen(self):
		self.CurrentState = False

	# THIS WILL CONFIRM WHETHER THE NAVIGATION OCCURS
	def checkUpdate(self, fill):
		# HERE FILL IS THE COLOR CODE
		self.fill = fill
		return self.CurrentState

	# THIS WILL UPDATE THE SCREEN WITH
	# THE NEW NAVIGATION TAB
	def screenUpdate(self):
		if self.CurrentState:
			self.screen.fill(self.fill)

	# RETURNS THE TITLE OF THE SCREEN
	def returnTitle(self):
		return self.screen

# NAVIGATION BUTTON CLASS


class Button():

	# INITIALIZATION OF BUTTON
	# COMPONENTS LIKE POSITION OF BUTTON,
	# COLOR OF BUTTON, FONT COLOR OF BUTTON, FONT SIZE,
	# TEXT INSIDE THE BUTTON
	def __init__(self, x, y, sx, sy, bcolour,
				fbcolour, font, fcolour, text):
		# ORIGIN_X COORDINATE OF BUTTON
		self.x = x
		# ORIGIN_Y COORDINATE OF BUTTON
		self.y = y
		# LAST_X COORDINATE OF BUTTON
		self.sx = sx
		# LAST_Y COORDINATE OF BUTTON
		self.sy = sy
		# FONT SIZE FOR THE TEXT IN A BUTTON
		self.fontsize = 25
		# BUTTON COLOUR
		self.bcolour = bcolour
		# RECTANGLE COLOR USED TO DRAW THE BUTTON
		self.fbcolour = fbcolour
		# BUTTON FONT COLOR
		self.fcolour = fcolour
		# TEXT IN A BUTTON
		self.text = text
		# CURRENT IS OFF
		self.CurrentState = False
		# FONT OBJECT FROM THE SYSTEM FONTS
		self.buttonf = py.font.SysFont(font, self.fontsize)

	# DRAW THE BUTTON FOR THE TWO
	# TABS MENU_SCREEN AND CONTROL TABS MENU
	def showButton(self, display):
		if(self.CurrentState):
			py.draw.rect(display, self.fbcolour,
						(self.x, self.y,
						self.sx, self.sy))
		else:
			py.draw.rect(display, self.fbcolour, 
						(self.x, self.y,
						self.sx, self.sy))
		# RENDER THE FONT OBJECT FROM THE SYSTEM FONTS
		textsurface = self.buttonf.render(self.text,
										False, self.fcolour)

		# THIS LINE WILL DRAW THE SURF ONTO THE SCREEN
		display.blit(textsurface, 
					((self.x + (self.sx/2) -
					(self.fontsize/2)*(len(self.text)/2) -
					5, (self.y + (self.sy/2) -
						(self.fontsize/2)-4))))

	# THIS FUNCTION CAPTURE WHETHER 
	# ANY MOUSE EVENT OCCUR ON THE BUTTON
	def focusCheck(self, mousepos, mouseclick):
		if(mousepos[0] >= self.x and mousepos[0] <= self.x +
				self.sx and mousepos[1] >= self.y and mousepos[1]
				<= self.y + self.sy):
			self.CurrentState = True
			# IF MOUSE BUTTON CLICK THEN
			# NAVIGATE TO THE NEXT OR PREVIOUS TABS
			return mouseclick[0]

		else:
			# ELSE LET THE CURRENT STATE TO BE OFF
			self.CurrentState = False
			return False


# INITIALIZATION OF THE PYGAME
py.init()
# INITIALIZATION OF SYSTEM FONTS
py.font.init()

# CREATING THE OBJECT OF THE
# CLASS Screen FOR MENU SCREEN
menuScreen = Screen("Menu Screen")

# CREATING THE OBJECT OF THE
# CLASS Screen FOR CONTROL SCREEN
control_bar = Screen("Control Screen")

# CALLING OF THE FUNCTION TO
# MAKE THE SCREEN FOR THE WINDOW
win = menuScreen.makeCurrentScreen()

# MENU BUTTON
MENU_BUTTON = Button(150, 150, 150, 50, (255, 250, 250),
					(255, 0, 0), "TimesNewRoman",
					(255, 255, 255), "Main Menu")

# CONTROL BUTTON
CONTROL_BUTTON = Button(150, 150, 150, 50,
						(0, 0, 0), (0, 0, 255),
						"TimesNewRoman",
						(255, 255, 255), "Back")

done = False

toggle = False

# MAIN LOOPING
while not done:
	# CALLING OF screenUpdate 
	# function FOR MENU SCREEN
	menuScreen.screenUpdate()
	
	# CALLING THE FUNCTION OF CONTROL BAR
	control_bar.screenUpdate()
	# STORING THE MOUSE EVENT TO
	# CHECK THE POSITION OF THE MOUSE
	mouse_pos = py.mouse.get_pos()
	# CHECKING THE MOUSE CLICK EVENT
	mouse_click = py.mouse.get_pressed()
	# KEY PRESSED OR NOT
	keys = py.key.get_pressed()

# MENU BAR CODE TO ACCESS
	# CHECKING MENU SCREEN FOR ITS UPDATE
	if menuScreen.checkUpdate((25, 0, 255)):
		control_barbutton = MENU_BUTTON.focusCheck(mouse_pos,
												mouse_click)
		MENU_BUTTON.showButton(menuScreen.returnTitle())

		if control_barbutton:
			win = control_bar.makeCurrentScreen()
			menuScreen.endCurrentScreen()

	# CONTROL BAR CODE TO ACCESS
	# CHECKING CONTROL SCREEN FOR ITS UPDATE
	elif control_bar.checkUpdate((255, 0, 255)):
		return_back = CONTROL_BUTTON.focusCheck(mouse_pos,
												mouse_click)
		CONTROL_BUTTON.showButton(control_bar.returnTitle())

		if return_back:
			control_bar.endCurrentScreen()
			win = menuScreen.makeCurrentScreen()
			
	# CHECKING IF THE EXIT BUTTON HAS BEEN CLICKED OR NOT
	for event in py.event.get():
	
		# IF CLICKED THEN CLOSE THE WINDOW
		if(event.type == py.QUIT):
			done = True

	py.display.update()
	
# CLOSE THE PROGRAM
py.quit()
