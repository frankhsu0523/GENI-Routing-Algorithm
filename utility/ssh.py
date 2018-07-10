"""ssh.

Usage:
    ssh.py push <host> <user> [--port=<port>] <file> [--remote_file=<file>]
    ssh.py exec_cmd <host> <user> [--port=<port>] <cmd>
    ssh.py kill <host> <user> [--port=<port>]
    ssh.py ryu <host> <user> [--port=<port>]

Options:
    -h --help Show this screen

"""
from docopt import docopt
import paramiko

import os, sys, threading

class ssh:

    def __init__(self, host, user, port=None):
        self.host = host
        self.user = user
        self.port = port
        self.ssh = None

    def __str__(self):
        s = 'host: {0}, user: {1}, port: {2}'.format(self.host, self.user, self.port)
        return s

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.port:
            self.ssh.connect( hostname=self.host, username=self.user, port=self.port)
        else:
            self.ssh.connect( hostname=self.host, username=self.user)

    def exec_command(self, cmd):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd)
        return ssh_stdout

    def put(self, local_file, remote_file = None, cmd=None):
        if not remote_file:
            remote_file = '/tmp/{0}'.format(os.path.basename(local_file))

        sftp = self.ssh.open_sftp()
        sftp.put(local_file, remote_file)
        if cmd:
            self.exec_command(cmd)
        self.close()

    def get(self, data, dirname ):
        for f in data:
            print(f)
            remotepath='/tmp/{0}.txt'.format(f)
            localpath= dirname + '/{0}.txt'.format(f)
            sftp = self.ssh.open_sftp()
            sftp.get(remotepath, localpath)
        self.close()
    """
    def threading_get(self, data, dirname):
        self.connect()
        threads = []
        sftp = self.ssh.open_sftp()
        for f in data:
            print(f)
            remotepath='/tmp/{0}.txt'.format(f)
            localpath= dirname + '/{0}.txt'.format(f)
            t = threading.Thread(target=sftp.get, args=(remotepath, localpath))
            t.start()
            threads.append(t)
            #sftp.get(remotepath, localpath) 
        for t in threads:
            t.join()
        """
    def close(self):
        self.ssh.close()

def send_host_server(G, dirname):
    threads = []
    for n, data in G.nodes(data=True):
        node = data['object']
        if node.type == 'host':
            hostname = node.login['hostname']
            username = node.login['username']
            port = int(node.login['port'])
            localpath = dirname + '/{0}_server.sh'.format(n)
            remotepath = '/tmp/{0}_server.sh'.format(n)
            if os.path.exists(localpath):
                print('send to /tmp/{0}_server.sh'.format(n))
                obj = ssh(hostname, username, port)
                obj.connect()
                t = threading.Thread(target=obj.put, args=(localpath, remotepath))
                t.start()
                threads.append(t)
    for t in threads:
        t.join()

def run_host_server(G, dirname):
    threads = []
    for n, data in G.nodes(data=True):
        node = data['object']
        if node.type == 'host':
            hostname = node.login['hostname']
            username = node.login['username']
            port = int(node.login['port'])
            localpath = dirname + '/{0}_server.sh'.format(n)
            remotepath = '/tmp/{0}_server.sh'.format(n)
            print('sudo bash /tmp/{0}_server.sh'.format(remotepath))
            if os.path.exists(localpath):
                obj = ssh(hostname, username, port)
                obj.connect()
                t = threading.Thread(target=obj.exec_command, args=('sudo bash /tmp/{0}_server.sh'.format(remotepath)))
                t.start()
                threads.append(t)
    for t in threads:
        t.join()

def send_host_client(G, dirname):
    threads = []
    for n, data in G.nodes(data=True):
        node = data['object']
        if node.type == 'host':
            hostname = node.login['hostname']
            username = node.login['username']
            port = int(node.login['port'])
            localpath = dirname + '/{0}_client.sh'.format(n)
            remotepath = '/tmp/client.sh'
            if os.path.exists(localpath):
                obj = ssh(hostname, username, port)
                obj.connect()
                t = threading.Thread(target=obj.put, args=(localpath, remotepath))
                t.start()
                threads.append(t)
    for t in threads:
        t.join()

def send_switch_script(G, dirname):
    threads = []
    for n, data in G.nodes(data=True):
        node = data['object']
        if node.type == 'switch' and node.flow_table:
            print('send to /tmp/{0}.sh'.format(n))
            hostname = node.login['hostname']
            username = node.login['username']
            port = int(node.login['port'])
            localpath = dirname + '/{0}.sh'.format(n)
            remotepath = '/tmp/{0}.sh'.format(n)
            obj = ssh(hostname, username, port)
            obj.connect()
            t = threading.Thread(target=obj.put, args=(localpath, remotepath,'sudo bash /tmp/{0}.sh'.format(n)))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()

def get_node_ofport( info ):
    obj = ssh(info['hostname'], info['username'], info['port'])
    obj.connect()
    ssh_stdout = obj.exec_command('ifconfig')
    mac_to_ofport = dict()
    for line in ssh_stdout.readlines():
      if 'eth' in line:
          res = line.strip().split(' ')
          eth = res[0]
          for i, d in enumerate(res):
              if d == 'HWaddr':
                  mac = res[i+1]
          #print('sudo ovs-vsctl get Interface {0} ofport'.format(eth))
          ssh_stdout = obj.exec_command('sudo ovs-vsctl get Interface {0} ofport'.format(eth))
          ofport = str(ssh_stdout.read().decode('utf-8')[:-1])
          print(ofport)
      mac_to_ofport[mac]=ofport
    obj.close()
    return mac_to_ofport

def get_node_datapath_id( info ):
    obj = ssh(info['hostname'], info['username'], info['port'])
    obj.connect()
    ssh_stdout = obj.exec_command('sudo ovs-vsctl get bridge br0 datapath_id')
    datapath_id = int(str(ssh_stdout.read().decode('utf-8')).split('"')[1],16)
    print('datapath_id: {}'.format(datapath_id))
    obj.close()
    return datapath_id

def run_node_cmd( info, cmd ):
    obj = ssh(info['hostname'], info['username'], info['port'])
    obj.connect()
    ssh_stdout = obj.exec_command(cmd)
    for line in ssh_stdout.readlines():
        print(line)
    obj.close()

def get_host_data( G, dirname):
    threads = []
    for n, data in G.nodes(data=True):
        node = data['object']
        #print(node.name)
        if node.type == 'host':

            hostname = node.login['hostname']
            username = node.login['username']
            port = int(node.login['port'])
            obj = ssh(hostname, username, port)
            obj.connect()
            t = threading.Thread(target=obj.get, args=(node.server_data,dirname))
            t.start()
            threads.append(t)
            #localpath = '/home/frank/mcf_code/geni/v2/data/{0}.txt'.format(f)
            #remotepath = '/tmp/{0}.txt'.format(f)
            #if os.path.exists(localpath):
            ##sftp_get( hostname, username, port, node.server_data, False)
    for t in threads:
        t.join()

def main():
    args = docopt(__doc__)
    print(args)
    if args['push']:
        obj = ssh( host=args['<host>'], user=args['<user>'], port=args['--port'])
        obj.connect()
        obj.put( local_file=args['<file>'], remote_file=args['--remote_file'])
        obj.close()
    elif args['exec_cmd']:
        obj = ssh( host=args['<host>'], user=args['<user>'], port=args['--port'])
        obj.connect()
        stdout = obj.exec_command(args['cmd'])
        obj.close()
    elif args['kill']:
        obj = ssh( host=args['<host>'], user=args['<user>'], port=args['--port'])
        obj.connect()
        cmd = 'pkill -f "ryu-manager"'
        stdout = obj.exec_command(cmd)
        obj.close()
    elif args['ryu']:
        obj = ssh( host=args['<host>'], user=args['<user>'], port=args['--port'])
        obj.connect()
        cmd = 'nohup ryu-manager /tmp/controller & >0.txt'
        stdout = obj.exec_command(cmd)
        #print(stdout.read())
        #obj.close()

if __name__ == '__main__':
    main()
