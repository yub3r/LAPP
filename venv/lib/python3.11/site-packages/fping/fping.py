from __future__ import print_function

import csv
import subprocess
from distutils import spawn
from multiprocessing.dummy import Pool as ThreadPool

from netaddr import IPAddress, IPNetwork, AddrFormatError

__author__ = 'NetworkEng - https://github.com/NetworkEng/fping.py'

# TODO - Add function to ping a range of IP's
# TODO - Add ability to ping hosts within /31 and /32 masks


class FastPing(object):
    """
    FastPing - Utility to ping lists of individual hosts or networks

    NOTE: This requires a custom modified version of the fping utility that
          adds the -V option to output the results in CSV format, located at
          https://github.com/NetworkEng/fping

    Examples:
        >>> from fping import FastPing
        >>> fp = FastPing()
        >>> fp.ping(filename='testing')
        # cmd =  ['/usr/local/sbin/fping', '-nV', '8.8.8.8',
                  'www.google.com', '206.190.36.45', 'localhost',
                  'host.cannotresolve.com']
        {'host.cannotresolve.com': 'unresolvable',
        'pa-in-f99.1e100.net': 'alive',
        'google-public-dns-a.google.com': 'alive',
        'localhost': 'unreachable',
        'ir1.fp.vip.gq1.yahoo.com': 'alive'}
        >>> fp.hosts(filename='testing', status='alive')
        'pa-in-f99.1e100.net': 'alive',
        'google-public-dns-a.google.com': 'alive',
        'ir1.fp.vip.gq1.yahoo.com': 'alive'}
        >>> fp.alive
        ['pa-in-f99.1e100.net',
        'google-public-dns-a.google.com',
        'ir1.fp.vip.gq1.yahoo.com']
        >>> fp.dead
        ['localhost']
        >>> fp.noip
        ['host.cannotresolve.com']
        >>>

    """

    def __init__(self):
        if not spawn.find_executable('fping'):
            raise SystemError('Executable fping file not found.')
        else:
            self.fping = spawn.find_executable('fping')
            if subprocess.check_output([self.fping, '-v']).find('csv') < 0:
                raise SystemError('Acceptable version of fping executable not '
                                  'found.')
        self.results = dict()
        self.num_pools = 128

    def ping(self, targets=list(), filename=str(), status=str()):
        """
        Attempt to ping a list of hosts or networks (can be a single host)
        :param targets: List - Name(s) or IP(s) of the host(s).
        :param filename: String - name of the file containing hosts to ping
        :param status: String - if one of ['alive', 'dead', 'noip'] then only
        return results that have that status. If this is not specified,
        then all results will be returned.
        :return: Type and results depends on whether status is specified:
                 if status == '': return dict: {targets: results}
                 if status != '': return list: targets if targets == status
        """

        if targets and filename:
            raise SyntaxError("You must specify only one of either targets=[] "
                              "or filename=''.")
        elif not targets and not filename:
            raise SyntaxError("You must specify either a list of targets or "
                              "filename='', but not both.")
        elif filename:
            targets = self.read_file(filename)

        my_targets = {'hosts': [], 'nets': []}
        addresses = []

        # Check for valid networks and add hosts and nets to my_targets
        for target in targets:
            # Targets may include networks in the format "network mask", or,
            # a file could contain multiple hosts or IP's on a single line.
            if len(target.split()) > 1:
                target_items = target.split()
                for item in target_items:
                    try:
                        ip = IPAddress(item)
                        # If it is an IPv4 address or mask put in in addresses
                        if ip.version == 4:
                            addresses.append(str(ip))
                    except AddrFormatError:
                        # IP Address not detected, so assume it's a host name
                        my_targets['hosts'].append(item)
                    except ValueError:
                        # CIDR network detected
                        net = IPNetwork(item)
                        # Make sure it is a CIDR address acceptable to fping
                        if net.ip.is_unicast() and net.version == 4 and \
                                net.netmask.netmask_bits() in range(8, 31):
                            my_targets['nets'].append(target_items[0])
                        else:
                            msg = str(str(net) + ':Only IPv4 unicast addresses'
                                      ' with bit masks\n               '
                                      ' from 8 to 30 are supported.')
                            raise AttributeError(msg)
                # Iterate over the IP strings in addresses
                while len(addresses) > 1:
                    ip = IPAddress(addresses[0])
                    mask = IPAddress(addresses[1])
                    # Test to see if IP is unicast, and mask is an actual mask
                    if ip.is_unicast() and mask.is_netmask():
                        net = IPNetwork(str(ip) + '/' + str(
                            mask.netmask_bits()))
                        # Convert ip and mask to CIDR and remove from addresses
                        my_targets['nets'].append(str(net.cidr))
                        addresses.pop(0)
                        addresses.pop(0)
                    elif ip.is_unicast() and not ip.is_netmask():
                        # mask was not a mask so only remove IP and start over
                        my_targets['hosts'].append(str(ip))
                        addresses.pop(0)
                # There could be one more item in addresses, so check it
                if addresses:
                    ip = IPAddress(addresses[0])
                    if ip.is_unicast() and not ip.is_netmask():
                        my_targets['hosts'].append(addresses[0])
                        addresses.pop()
            # target has only one item, so check it
            else:
                try:
                    ip = IPAddress(target)
                    if ip.version == 4 and ip.is_unicast() and \
                            not ip.is_netmask():
                        my_targets['hosts'].append(target)
                    else:
                        msg = str(target + 'Only IPv4 unicast addresses are '
                                  'supported.')
                        raise AttributeError(msg)
                except AddrFormatError:
                    # IP Address not detected, so assume it's a host name
                    my_targets['hosts'].append(target)
                except ValueError:
                    # CIDR network detected
                    net = IPNetwork(target)
                    if net.ip.is_unicast() and net.version == 4 and \
                            net.netmask.netmask_bits() in range(8, 31):
                        my_targets['nets'].append(target)
                    else:
                        msg = str(str(net) + ':Only IPv4 unicast addresses'
                                  ' with bit masks\n               '
                                  ' from 8 to 30 are supported.')
                        raise AttributeError(msg)

        """
        Build the list of commands to run.
        """
        commands = []
        if len(my_targets['hosts']) != 0:
            for target in range(len(my_targets['hosts'])):
                commands.append([self.fping, '-nV', my_targets['hosts'][
                    target]])
        if len(my_targets['nets']) != 0:
            for target in range(len(my_targets['nets'])):
                commands.append([self.fping, '-ngV', my_targets['nets'][
                    target]])

        """
        Start pinging each item in my_targets and return the requested results
        when done.
        """
        pool = ThreadPool(self.num_pools)
        raw_results = pool.map(self.get_results, commands)
        pool.close()
        pool.join()
        self.results = {host: result for host, result in csv.reader(
            ''.join(raw_results).splitlines())}
        if not status:
            return self.results
        elif status == 'alive':
            return self.alive
        elif status == 'dead':
            return self.dead
        elif status == 'noip':
            return self.noip
        else:
            raise SyntaxError("Valid status options are 'alive', 'dead' or "
                              "'noip'")

    @staticmethod
    def get_results(cmd):
        """
        def get_results(cmd: list) -> str:
            return lines
        Get the ping results using fping.
        :param cmd: List - the fping command and its options
        :return: String - raw string output containing csv fping results
        including the newline characters
        """
        try:
            return subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            return e.output

    @staticmethod
    def read_file(filename):
        """
        Reads the lines of a file into a list, and returns the list
        :param filename: String - path and name of the file
        :return: List - lines within the file
        """
        lines = []
        with open(filename) as f:
            for line in f:
                if len(line.strip()) != 0:
                    lines.append(line.strip())
        return lines

    @property
    def alive(self):
        """
        Parse results and return list of hosts that are responding to ping
        :return: List - hosts that replied
        """
        return [host for host in self.results if self.results[host] == 'alive']

    @property
    def dead(self):
        """
        Parse results and return list of hosts that are not responding to ping
        :return: List - hosts that did not respond
        """
        return [host for host in self.results if self.results[host] ==
                'unreachable']

    @property
    def noip(self):
        """
        Parse results and return a list of hosts whose IP address was not found
        :return: List - host names that failed IP lookup
        """
        return [host for host in self.results if self.results[host] ==
                'unresolvable']
