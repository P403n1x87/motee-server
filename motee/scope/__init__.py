class ScopeHandler:
    @classmethod
    def handle(cls, action, data):
        return getattr(cls, action)(**(data if data else {}))
