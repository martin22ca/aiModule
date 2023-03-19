from socket import inet_ntoa
from zeroconf import Zeroconf

class FlaskServerListener:
    def __init__(self,serverName):
        self.serverIp = None
        self.serverName = serverName

    def add_service(self, zeroconf, service_type, name):
        if name.startswith(self.serverName):
            info = zeroconf.get_service_info(service_type, name)
            if info is not None:
                self.serverIp = inet_ntoa((info.addresses[0]))
                

    def update_service(self, zc: "Zeroconf", type_: str, name: str) -> None:
        """Callback for state updates, which we ignore for now."""