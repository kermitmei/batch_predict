import ipaddress
import socket
import psutil


class NetUtil:

    @staticmethod
    def get_all_ip_addresses(subnet: str = None):
        ip_addresses = []
        for _interface, _addresses in psutil.net_if_addrs().items():
            for addr in _addresses:
                if addr.family == socket.AF_INET or addr.family == socket.AF_INET6:  # For IPv4 or IPv6 addresses
                    if subnet is None or (ipaddress.ip_address(addr.address) in ipaddress.ip_network(subnet)):
                        ip_addresses.append(addr.address)
        return ip_addresses
