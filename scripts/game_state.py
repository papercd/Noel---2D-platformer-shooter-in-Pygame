from enum import Enum

class GameState(Enum): 
    StartSequence = 0
    MainMenu = 1
    MainMenuSettings =2
    GameLoop = 3
    PauseMenu = 4 
    PauseMenuSettings =5

