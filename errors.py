class ExternalError:

    def __init__(self, initiator, asin, error):
        self.initiator = initiator
        self.asin = asin
        self.error = error

    def show_error(self):
        print(
            f"Error while executing {self.initiator}, for ASIN: {self.asin}, msg: {self.error}")
