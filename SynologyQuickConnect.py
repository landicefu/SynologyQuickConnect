# coding=UTF-8

import requests
from threading import Thread


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs, verbose)
        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)

    def join(self):
        Thread.join(self)
        return self._return


class Host:
    def __init__(self, address, port):  # type: (str, int) -> Host
        self.address = address
        self.port = port


def start_tasks(threads):
    result = []
    for thread in threads:
        thread.start()
    for thread in threads:
        result.append(thread.join())
    return result


def get_server_info(quick_connect_id, _id, url='http://global.quickconnect.to/Serv.php'):
    payload = {
        'version': 1,
        'command': 'get_server_info',
        'stop_when_error': 'false',
        'stop_when_success': 'true',
        'id': _id,
        'serverID': quick_connect_id
    }
    result = requests.post(url, json=payload, timeout=30).json()
    try:
        return result
    except KeyError:
        try:
            return get_server_info(quick_connect_id, _id, 'http://%s/Serv.php' % result['sites'][0])
        except KeyError:
            return None


def ping(host, is_https, timeout):  # type: (Host, bool, int) -> None
    scheme = "https" if is_https else "http"
    url = "%s://%s:%d/webman/pingpong.cgi?action=cors" % (scheme, host.address, host.port)
    try:
        result = requests.get(url, verify=False, timeout=timeout)
        if result.status_code == 200 and result.json()['success']:
            return host
    except:
        pass
    return None


def create_ping_thread(host, is_https, timeout=10):  # type: (Host, bool, int) -> ThreadWithReturnValue
    return ThreadWithReturnValue(target=ping, args=(host, is_https, timeout))


def resolve_by_ping(server_info, is_https):  # type: (dict, bool) -> Host
    server = server_info['server']
    service = server_info['service']
    port = service['port']
    external_port = service['ext_port']
    interfaces = server['interface']
    tasks = []  # type: list [ThreadWithReturnValue]

    # internal addresses like `192.168.x.x` or `10.x.x.x`
    if interfaces is not None and len(interfaces) > 0:
        for interface in interfaces:
            tasks.append(create_ping_thread(Host(interface['ip'], port), is_https, 10))
            try:
                ipv6_addresses = interface['ipv6']
                for ipv6 in ipv6_addresses:
                    tasks.append(create_ping_thread(Host("[%s]" % ipv6['address'], port), is_https, 10))
            except KeyError:
                pass

    # host addresses (DDNS or FQDN)
    try:
        ddns = server['ddns']
        if ddns != 'NULL':
            tasks.append(create_ping_thread(Host(ddns, port), is_https, 10))
    except KeyError:
        pass
    try:
        fqdn = server['fqdn']
        if fqdn != 'NULL':
            tasks.append(create_ping_thread(Host(fqdn, port), is_https, 10))
    except KeyError:
        pass

    # external address (pubic ip address)
    ext_port = external_port if external_port != 0 else port
    try:
        tasks.append(create_ping_thread(Host(server['external']['ip'], ext_port), is_https, 10))
    except KeyError:
        pass
    try:
        ipv6 = server['external']['ipv6']
        if ipv6 is not None and ipv6 != '' and ipv6 != '::':
            tasks.append(create_ping_thread(Host("[%s]" % ipv6, ext_port), is_https, 10))
    except KeyError:
        pass

    # relay
    try:
        relay_ip = service['relay_ip']
        relay_port = service['relay_port']
        if relay_ip is not None and relay_ip != '' and relay_port != 0:
            tasks.append(create_ping_thread(Host(relay_ip, relay_port), is_https, 10))
    except KeyError:
        pass

    # find valid host from results
    resolved_hosts = start_tasks(tasks)
    for host in resolved_hosts:
        if host is not None:
            return host
    return None


def request_tunnel(server_info, quick_connect_id, _id):
    try:
        control_host = server_info['env']['control_host']
        payload = {
            'version': 1,
            'command': 'request_tunnel',
            'id': _id,
            'serverID': quick_connect_id
        }
        result = requests.post("http://%s/Serv.php" % control_host, json=payload, timeout=30).json()
        host = Host(result['service']['relay_ip'], result['service']['relay_port'])
        return host
    except KeyError:
        pass
    return None


def resolve(quick_connect_id, is_https=True):  # type: (str, bool) -> Host
    if ':' in quick_connect_id or '.' in quick_connect_id or quick_connect_id == '':
        raise Exception('%s is not a QuickConnect ID' % quick_connect_id)

    _id = 'dsm_portal_https' if is_https else 'dsm_portal'
    server_info = get_server_info(quick_connect_id, _id)
    if server_info is None:
        raise Exception("We cannot find QuickConnect ID %s" % quick_connect_id)

    result = resolve_by_ping(server_info, is_https)
    if result is not None:
        return result

    result = request_tunnel(server_info, quick_connect_id, _id)
    if result is not None:
        return result
    return None


if __name__ == '__main__':
    _host = resolve('landicefu', True)
    if _host is not None:
        print("https://%s:%d" % (_host.address, _host.port))
