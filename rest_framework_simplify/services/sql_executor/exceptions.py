class EngineNotSupported(Exception):
    def __init__(self, message):
        super(EngineNotSupported, self).__init__(message)