from editor_scripts.cursor import Cursor

class EditorInterface:

    _instance = None

    @staticmethod 
    def get_instance()->"EditorInterface":
        if EditorInterface._instance is None: 
            EditorInterface._instance = EditorInterface()
        
        return EditorInterface._instance
    
    def __init__(self)->None: 
        self.cursor = Cursor()