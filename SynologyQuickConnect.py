import requests


class Host:
    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port


def get_server_info(quick_connect_id, _id, url='http://global.quickconnect.to/Serv.php'):
    payload = {
        'version': 1,
        'command': 'get_server_info',
        'stop_when_error': 'false',
        'stop_when_success': 'true',
        'id': _id,
        'serverID': quick_connect_id
    }
    result = requests.post(url, json=payload).json()
    try:
        return result['server']
    except KeyError:
        return get_server_info(quick_connect_id, _id, 'http://%s/Serv.php' % result.sites[0])


def ping(host: Host, is_https: bool):
    scheme = "https" if is_https else "http"
    url = "%s://%s:%d/webman/pingpong.cgi?action=cors" % (scheme, host.address, host.port)
    try:
        result = requests.get(url, verify=False)
        if result.status_code == 200 and result.json()['success']:
            return host
    except: pass
    return None


def resolve_by_ping_dsm(server_info, is_https: bool):
    server = server_info['server']
    service = server_info['service']
    port = service.port
    externalPort = service.ext_port
    return None


def resolve_by_ping_tunnel(service, is_https: bool):
    return None


def request_tunnel(server_info, quick_connect_id, _id, is_https: bool):
    return None


def resolve(quick_connect_id, is_https: bool=True):
    if ':' in quick_connect_id or '.' in quick_connect_id or quick_connect_id == '':
        raise Exception('%s is not a QuickConnect ID' % quick_connect_id)

    _id = 'dsm_portal_https' if is_https else 'dsm_portal'
    server_info = get_server_info(quick_connect_id, _id)
    result = resolve_by_ping_dsm(server_info, is_https)
    if result is not None:
        return result
    result = resolve_by_ping_tunnel(server_info['service'], is_https)
    if result is not None:
        return result
    result = request_tunnel(server_info, quick_connect_id, _id, is_https)
    if result is not None:
        return result
    return None


if __name__ == '__main__':
    # print(resolve('landicefu', True))
    print(ping(Host("61.220.55.78", 31763), True))
