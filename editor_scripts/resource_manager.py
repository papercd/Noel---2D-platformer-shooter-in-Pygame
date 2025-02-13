from moderngl import Context


class ResourceManager:
    _instance = None
    _ctx : Context = None
     
    @staticmethod
    def get_instance(ctx: Context = None) -> "ResourceManager":
        if ResourceManager._instance is None: 
            assert isinstance(ctx,Context), "Error: Resource Manager must be initialized with a GL context."

            ResourceManager._ctx = ctx 
            ResourceManager._instance = ResourceManager()

        return ResourceManager._instance

    def __init__(self)->None: 
        pass