from llmbase.main.utils.net_util import NetUtil

if __name__ == '__main__':
    # 获取本机IP地址
    local_ips = NetUtil.get_all_ip_addresses(subnet="192.168.31.0/24")
    print(f"本机IP地址: {local_ips}")
