from typing import TYPE_CHECKING


if TYPE_CHECKING: 
    from moderngl import Context


class ResourceManager:
    _instance = None

    @staticmethod
    def get_instance(ctx:"Context")->"ResourceManager":
        if ResourceManager._instance is None: 
            ResourceManager._instance = ResourceManager(ctx)
        return ResourceManager._instance
    

    def __init__(self,ctx:"Context") -> None:
        self._ctx = ctx

