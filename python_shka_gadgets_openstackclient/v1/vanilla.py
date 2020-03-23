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

import re
import subprocess

from osc_lib.command import command

##

def _add_port_arguments(ports):
    arg = ""
    for port in ports:
        if port != 22:
            arg += "--add-port %d " % (port)
    return arg

class _AddPort(command.Command):
    def get_parser(self, prog_name):
        parser = super(_AddPort, self).get_parser(prog_name)
        parser.add_argument(
            '--add-port', metavar='<port>', type=int, action='append',
            dest='ports', default=[22],
            help='Destination port (allow multiple times, default: [22]).',
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

class _Vanilla(command.Command):
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
        subprocess.check_call("sleep 1 && openstack security group create --description 'for %s' %s > /dev/null && openstack server add security group %s %s" % (server, server, server, server), shell=True)
        for port in parsed_args.ports:
            subprocess.check_call("sleep 1 && openstack security group rule create --proto tcp --dst-port %d --remote-ip `openstack vanilla show my ip` %s > /dev/null" % (port, server), shell=True)
        return

##

class Create(_Vanilla, _Flavor, _AddPort):
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
    
    def _is_float(s):
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True

    def take_action(self, parsed_args):
        server = parsed_args.server
        volume = parsed_args.volume
        if volume and _is_float(volume):
            volume = subprocess.check_output("sleep 1 && openstack volume create --description 'for %s' --size %s --format value --column id %s" % (server, volume, server), shell=True).decode()
        subprocess.check_call("sleep 1 && openstack server create --flavor %s --image %s --key-name %s --wait %s > /dev/null && openstack vanilla allow me %s %s && openstack vanilla give ip %s" % (parsed_args.flavor, parsed_args.image, parsed_args.key_name, server, _add_port_arguments(parsed_args.ports), server, server), shell=True)
        if volume:
            subprocess.check_call("sleep 1 && openstack server add volume %s %s" % (server, volume), shell=True)
        return

##
    
class Delete(_Vanilla):
    """Delete the vanilla server."""
    
    def get_parser(self, prog_name):
        parser = super(Delete, self).get_parser(prog_name)
        parser.add_argument(
            '--delete-volumes', action='store_true', 
            help="Delete the attached volumes if exist",
        )
        return parser
    
    def take_action(self, parsed_args):
        server = parsed_args.server
        volumes = parsed_args.delete_volumes
        server_id = False
        if volumes:
            volumes = subprocess.check_output("sleep 1 && openstack server show %s --format value --column volumes_attached" % (server), shell=True).decode()
        subprocess.check_call("ssh-keygen -R `openstack vanilla show ip %s` && openstack vanilla take ip %s && openstack vanilla deny us %s && openstack server delete --wait %s" % (server, server, server, server), shell=True)
        if volumes:
            for volume in re.findall("'([^']+)'", volumes):
                subprocess.check_call("sleep 1 && openstack volume delete %s" % (volume), shell=True)
        return

##

class DenyUs(_Vanilla):
    """Deny us connection to the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        try:
            subprocess.check_call("sleep 1 && openstack security group show %s > /dev/null 2>&1" %(server), shell=True)
        except:
            pass
        else:
            subprocess.check_call("sleep 1 && openstack server remove security group %s %s && openstack security group delete %s" % (server, server, server), shell=True)
        return
##

class GiveIP(_Vanilla):
    """Give a floating IP to the vanilla server, if not assigned."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        ip = subprocess.check_output("openstack vanilla show ip %s" % (server), shell=True).decode().strip()
        if re.search('=', ip):
            subprocess.check_call("sleep 1 && openstack server add floating ip %s `openstack floating ip create public --format value --column 'floating_ip_address'`" % (server), shell=True)
        return

##

class Resize(_Vanilla, _Flavor):
    """Resize the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        subprocess.check_call("sleep 1 && openstack server resize --flavor %s --wait %s > /dev/null && openstack server resize confirm %s" % (parsed_args.flavor, server, server), shell=True)
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
        images =  subprocess.check_output("sleep 1 && openstack image list --format value --column ID --property instance_uuid=`openstack vanilla show id %s`" % (server), shell=True).decode().strip().split()
        subprocess.check_call("ssh-keygen -R `openstack vanilla show ip %s` && openstack vanilla take ip %s && openstack vanilla deny us %s && openstack server shelve %s > /dev/null" % (server, server, server, server), shell=True)
        if not parsed_args.keep_images:
            while 'SHELVED_OFFLOADED' != subprocess.check_output("openstack vanilla show status %s" % (server), shell=True).decode().strip():
                subprocess.check_call("sleep 1", shell=True)
            for image in images:
                subprocess.check_call("sleep 1 && openstack image delete %s > /dev/null 2>&1" % (image), shell=True)
        return

##

class ShowID(_Vanilla):
    """Show the ID of the vanilla server."""

    def take_action(self, parsed_args):
        subprocess.check_call("sleep 1 && openstack server show --format value --column id %s" % (parsed_args.server), shell=True)
        return

##

class ShowIP(_Vanilla):
    """Show the floating IP address of the vanilla server."""

    def take_action(self, parsed_args):
        subprocess.check_call("sleep 1 && openstack server show --format value --column addresses %s | cut -d' ' -f 2" % (parsed_args.server), shell=True)
        return

##

class ShowMyIP(command.Command):
    """Show my IP address."""

    def take_action(self, parsed_args):
        subprocess.check_call("sleep 1 && curl --silent https://ipinfo.io/ip", shell=True)
        return

##

class ShowStatus(_Vanilla):
    """Show the status of the vanilla server."""

    def take_action(self, parsed_args):
        subprocess.check_call("sleep 1 && openstack server show --format value --column status %s" % (parsed_args.server), shell=True)
        return

##

class TakeIP(_Vanilla):
    """Take the floating IP from the vanilla server, if assigned."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        ip = subprocess.check_output("openstack vanilla show ip %s" % (server), shell=True).decode().strip()
        if not re.search('=', ip):
            subprocess.check_call("sleep 1 && openstack floating ip delete %s" % (ip), shell=True)
        return
        
##

class Test(_Vanilla, _AddPort):
    """Test for the plugin."""

    def take_action(self, parsed_args):
        print(_add_port_arguments(parsed_args.ports))
        return

##

class Unshelve(_Vanilla, _AddPort):
    """Unshelve the vanilla server."""

    def take_action(self, parsed_args):
        server = parsed_args.server
        subprocess.check_call("sleep 1 && openstack server unshelve %s > /dev/null && openstack vanilla allow me %s %s && openstack vanilla give ip %s" % (server, _add_port_arguments(parsed_args.ports), server, server), shell=True)
        return
