class BusinessError(Exception):
    def __init__(self, error_msg):
        super().__init__()
        self.error_msg = error_msg