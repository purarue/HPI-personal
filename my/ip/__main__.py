from my.ip.all import deny, ips

if __name__ == "__main__":
    # to mark IPs as incorrect, run 'python3 -m my.ip.all'
    deny.deny_cli(ips())
