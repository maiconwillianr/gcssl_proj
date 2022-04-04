class InfoConfigDTO:

    def __init__(self, status, detalhes):
        self.status = status
        self.detalhes = detalhes

    def get_status(self):
        return self.status
