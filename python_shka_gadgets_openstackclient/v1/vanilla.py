# Copyright (c) 2020 Shintaro Katayama
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re
import subprocess

from osc_lib.command import command

##

class _AddPort(command.Command):

    def add_port_arguments(self, ports):
        arg = ""
        for port in ports:
            if port != 22:
                arg += "--add-port %d " % (port)
        return arg

    def get_parser(self, prog_name):
        parser = super(_AddPort, self).get_parser(prog_name)
        parser.add_argument(
            '--add-port', metavar='<port>', type=int, action='append',
            dest='ports', default=[22],
            help='Destination port (allow multiple times, default: [22])',
        )
        return parser

##

class _Flavor(command.Command):
    def get_parser(self, prog_name):
        parser = super(_Flavor, self).get_parser(prog_name)
        parser.add_argument(
            '--flavor', metavar='<flavor>', required=True,
            help='Create with this flavor (name or ID)',
        )
        return parser

##

class _Login(command.Command):
    def get_parser(self, prog_name):
        parser = super(_Login, self).get_parser(prog_name)
        parser.add_argument(
            '--login', metavar='<login-name>', required=True,
            help='Login name for ssh/sshfs',
        )
        return parser

##

class _Mount(_Login):

    def mount_argument(self, mount):
        mount = ''
        if mount:
            mount = '--mount %s' % (monut)
        return mount
    
    def get_parser(self, prog_name):
        parser = super(_Mount, self).get_parser(prog_name)
        parser.add_argument(
            '--mount', metavar='<mount-point>', default='',
            help='Directory of the vanilla server to mount (default: ~)',
        )
        return parser

##

class _Vanilla(command.Command):

    def _insert_verbosity_option(self, cmd):
        verbosity = ''
        verbose_level = self.app.options.verbose_level
        if verbose_level == 0:
            verbosity = '-q'
        elif verbose_level > 1:
            verbosity = '-%s' % ('v' * (verbose_level-1))
        return re.sub(r'(openstack \S+)', r'\1 %s' % (verbosity), cmd)

    logger = logging.getLogger(__name__)

    def check_call(self, cmd, silent=''):
        cmd = self._insert_verbosity_option(cmd)
        if self.app.options.verbose_level < 2:
            cmd += ' %s' % (silent)
        self.logger.info("-- _Vanilla.check_call ------\n%s\n--------" % cmd)
        subprocess.check_call('sleep 1 && ' + cmd, shell=True)
        return

    def check_calls(self, cmds):
        for cmd in cmds:
            self.check_call(cmd)
        return

    def check_output(self, cmd):
        cmd = self._insert_verbosity_option(cmd)
        self.logger.info("-- _Vanilla.check_output ------\n%s\n--------" % cmd)
        return subprocess.check_output('sleep 1 && ' + cmd, shell=True)

    def get_parser(self, prog_name):
        parser = super(_Vanilla, self).get_parser(prog_name)
        parser.add_argument(
            'server', metavar='<server>', help='Server (name or ID)',
        )
        return parser

##

class AllowMe(_Vanilla, _AddPort):
    """Allow me connection to the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        self.check_call("openstack security group create --format yaml --description 'for %s' %s" % (server, server), '> /dev/null')
        self.check_call('openstack server add security group %s %s' % (server, server))
        for port in parsed_args.ports:
            self.check_call('openstack security group rule create --format yaml --proto tcp --dst-port %d --remote-ip `openstack vanilla show my ip %s` %s' % (port, server, server), '> /dev/null')
        return

##

class Create(_Vanilla, _Mount, _Flavor, _AddPort):
    """Create a vanilla server."""

    def get_parser(self, prog_name):
        parser = super(Create, self).get_parser(prog_name)
        parser.add_argument(
            '--key-name', metavar='<key-name>', required=True,
            help='Keypair to inject into this server (optional extension)',
        )
        parser.add_argument(
            '--image', metavar='<image>', required=True,
            help='Create server boot disk from this image (name or ID)',
        )
        parser.add_argument(
            '--volume', metavar='<volume>',
            help='Volume (size in GB for new or ID to mount)',
        )
        return parser
    
    def _is_float(self, s):
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True

    def take_action(self, parsed_args):
        server = parsed_args.server
        volume = parsed_args.volume
        if volume and self._is_float(volume):
            volume = self.check_output("openstack volume create %s --description 'for %s' --size %s --format value --column id" % (server, server, volume)).decode().strip()
        self.check_call('openstack server create --format yaml --flavor %s --image %s --key-name %s --wait %s' % (parsed_args.flavor, parsed_args.image, parsed_args.key_name, server), '> /dev/null')
        self.check_calls([
            'openstack vanilla allow me %s %s' % (self.add_port_arguments(parsed_args.ports), server),
            'openstack vanilla give ip %s' % (server),
            'openstack vanilla mount --login %s %s %s' % (parsed_args.login, self.mount_argument(parsed_args.mount), server)
        ])
        if volume:
            self.check_call('openstack server add volume %s %s' % (server, volume))
        return

##
    
class Delete(_Vanilla):
    """Delete the vanilla server."""
    
    def get_parser(self, prog_name):
        parser = super(Delete, self).get_parser(prog_name)
        parser.add_argument(
            '--delete-volumes', action='store_true', 
            help='Delete the attached volumes if exist',
        )
        return parser
    
    def take_action(self, parsed_args):
        server = parsed_args.server
        volumes = parsed_args.delete_volumes
        server_id = False
        self.check_call('openstack vanilla unmount %s' % (server))
        if volumes:
            volumes = self.check_output('openstack server show %s --format value --column volumes_attached' % (server)).decode().strip()
        self.check_call('ssh-keygen -R `openstack vanilla show ip %s`' % (server), '> /dev/null 2>&1')
        self.check_calls([
            'openstack vanilla take ip %s' % (server),
            'openstack vanilla deny us %s' % (server),
            'openstack server delete --wait %s' % (server)
        ])
        if volumes:
            for volume in re.findall("'([^']+)'", volumes):
                self.check_call('openstack volume delete %s' % (volume))
        return

##

class DenyUs(_Vanilla):
    """Deny us connection to the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        try:
            self.check_call('openstack security group show --format yaml %s' % (server), '> /dev/null 2>&1')
        except:
            pass
        else:
            self.check_calls([
                'openstack server remove security group %s %s' % (server, server),
                'openstack security group delete %s' % (server)
            ])
        return
##

class GiveIP(_Vanilla):
    """Give a floating IP to the vanilla server, if not assigned."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        if re.search('=', self.check_output('openstack vanilla show ip %s' % (server)).decode().strip()):
            self.check_call('openstack server add floating ip %s `openstack floating ip create public --format value --column floating_ip_address`' % (server))
        return

##

class Mount(_Vanilla, _Mount):
    """Mount the root directory of the vanilla server to ./vanilla by sshfs."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        login = parsed_args.login
        while self.check_output('openstack vanilla wait sshd --login %s %s' % (login, server)).decode().strip() == 'NG':
            self.check_call('mkdir -p ./vanilla')
        self.check_call('sshfs %s@`openstack vanilla show ip %s`:%s ./vanilla' % (login, server, parsed_args.mount))
        return

##

class Resize(_Vanilla, _Mount, _Flavor):
    """Resize the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        self.check_call('openstack server resize --flavor %s --wait %s' % (parsed_args.flavor, server), '> /dev/null')
        self.check_calls([
            'openstack server resize confirm %s' % (server),
            'openstack vanilla mount --login %s %s %s' % (parsed_args.login, self.mount_argument(parsed_args.mount), server)
        ])
        return

##

class Shelve(_Vanilla):
    """Shelve the vanilla server."""

    def get_parser(self, prog_name):
        parser = super(Shelve, self).get_parser(prog_name)
        parser.add_argument(
            '--keep-images', action='store_true',
            help="Keep the image after unshelve",
        )
        return parser

    def take_action(self, parsed_args):
        server = parsed_args.server
        images =  self.check_output('openstack image list --format value --column ID --property instance_uuid=`openstack vanilla show id %s`' % (server)).decode().strip().split()
        self.check_call('openstack vanilla unmount %s' % (server))
        self.check_call('ssh-keygen -R `openstack vanilla show ip %s`' % (server), '> /dev/null 2>&1')
        self.check_calls([
            'openstack vanilla take ip %s' % (server),
            'openstack vanilla deny us %s' % (server),
            'openstack server shelve %s' % (server)
        ])
        if not parsed_args.keep_images:
            while 'SHELVED_OFFLOADED' != self.check_output('openstack vanilla show status %s' % (server)).decode().strip():
                self.check_call('sleep 1')
            for image in images:
                self.check_call('openstack image delete %s' % (image))
        return

##

class ShowID(_Vanilla):
    """Show the ID of the vanilla server."""

    def take_action(self, parsed_args):
        self.check_call('openstack server show --format value --column id %s' % (parsed_args.server))
        return

##

class ShowIP(_Vanilla):
    """Show the floating IP address of the vanilla server."""

    def take_action(self, parsed_args):
        self.check_call("openstack server show --format value --column addresses %s | cut -d' ' -f 2" % (parsed_args.server))
        return

##

class ShowMyIP(_Vanilla):
    """Show my IP address."""

    def take_action(self, parsed_args):
        self.check_call('curl --silent https://ipinfo.io/ip')
        return

##

class ShowStatus(_Vanilla):
    """Show the status of the vanilla server."""

    def take_action(self, parsed_args):
        self.check_call('openstack server show --format value --column status %s' % (parsed_args.server))
        return

##

class TakeIP(_Vanilla):
    """Take the floating IP from the vanilla server, if assigned."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        ip = self.check_output('openstack vanilla show ip %s' % (server)).decode().strip()
        if not re.search('=', ip):
            self.check_call('openstack floating ip delete %s' % (ip))
        return
        
##

class Test(_Vanilla):
    """Test for the plugin."""

    logger = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        print(self.app.options.verbose_level)
        self.check_call('openstack vanilla show ip %s' % (parsed_args.server))
        return

##

class Unmount(_Vanilla):
    """Unmount the vanilla server."""

    def take_action(self, parsed_args):
        if re.search(self.check_output('openstack vanilla show ip %s' % (parsed_args.server)).decode().strip(),
                     self.check_output('mount').decode()):
            self.check_call('umount ./vanilla')
        return

##

class Unshelve(_Vanilla, _Mount, _AddPort):
    """Unshelve the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        self.check_call('openstack server unshelve %s' % (server), '> /dev/null')
        self.check_calls([
            'openstack vanilla allow me %s %s' % (self.add_port_arguments(parsed_args.ports), server),
            'openstack vanilla give ip %s' % (server),
            'openstack vanilla mount --login %s %s %s' % (parsed_args.login, self.mount_argument(parsed_args.mount), server)
        ])
        return

##

class WaitSShD(_Vanilla, _Login):
    """Wait sshd in the vanilla server."""

    def take_action(self, parsed_args):
        try:
            self.check_call("ssh -oStrictHostKeyChecking=accept-new %s@`openstack vanilla show ip %s` 'echo OK' 2>/dev/null" % (parsed_args.login, parsed_args.server))
        except:
            print('NG')
        return
