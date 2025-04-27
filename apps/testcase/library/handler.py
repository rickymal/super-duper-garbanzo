class PostgresFacade:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    def on_client_data_received(self, buffer: bytes):
        # Implement connection logic here
        pass

    def on_server_data_received(self, buffer: bytes):
        # Implement disconnection logic here
        pass
