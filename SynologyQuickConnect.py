import requests


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


def resolve_by_ping_dsm(server_info):
    server = server_info['server']
    service = server_info['service']
    port = service.port
    externalPort = service.ext_port
    return None


def resolve_by_ping_tunnel(service):
    return None


def request_tunnel(server_info, quick_connect_id, _id):
    return None


def resolve(quick_connect_id, is_https=True):
    if ':' in quick_connect_id or '.' in quick_connect_id or quick_connect_id == '':
        raise Exception('%s is not a QuickConnect ID' % quick_connect_id)

    _id = 'dsm_portal_https' if is_https else 'dsm_portal'
    server_info = get_server_info(quick_connect_id, _id)
    result = resolve_by_ping_dsm(server_info)
    if result is not None:
        return result
    result = resolve_by_ping_tunnel(server_info['service'])
    if result is not None:
        return result
    result = request_tunnel(server_info, quick_connect_id, _id)
    if result is not None:
        return result
    return None


if __name__ == '__main__':
    # print(resolve('landicefu', True))
    rx.of("1")