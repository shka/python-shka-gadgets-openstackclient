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

from setuptools import setup, find_packages

try:
    with open('README.rst') as f:
        readme = f.read()
except IOError:
    readme = ''

setup(
    name='python-shka-gadgets-openstackclient',
    version='0.0.2',
    url='https://github.com/shka/python-shka-gadgets-openstackclient',
    author='Shintaro Katayama',
    author_email='shintaro.katayama@gmail.com',
    maintainer='Shintaro Katayama',
    maintainer_email='shintaro.katayama@gmail.com',
    classifiers=[
        'Environment :: OpenStack',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
    ],

    summary='OpenStackClient plugin for manipulation of a simple virtual machine',
    long_description=readme,
    
    packages=find_packages(),
    install_requires=['python-openstackclient',],
    
    entry_points={
        'openstack.cli.extension': [
            'shka=python_shka_gadgets_openstackclient.client',
        ],
        'openstack.python_shka_gadgets_openstackclient.v1': [
            'vanilla_allow_me=python_shka_gadgets_openstackclient.v1.vanilla:AllowMe',
            'vanilla_create=python_shka_gadgets_openstackclient.v1.vanilla:Create',
            'vanilla_delete=python_shka_gadgets_openstackclient.v1.vanilla:Delete',
            'vanilla_deny_us=python_shka_gadgets_openstackclient.v1.vanilla:DenyUs',
            'vanilla_give_ip=python_shka_gadgets_openstackclient.v1.vanilla:GiveIP',
            'vanilla_resize=python_shka_gadgets_openstackclient.v1.vanilla:Resize',
            'vanilla_shelve=python_shka_gadgets_openstackclient.v1.vanilla:Shelve',
            'vanilla_show_id=python_shka_gadgets_openstackclient.v1.vanilla:ShowID',
            'vanilla_show_ip=python_shka_gadgets_openstackclient.v1.vanilla:ShowIP',
            'vanilla_show_my_ip=python_shka_gadgets_openstackclient.v1.vanilla:ShowMyIP',
            'vanilla_show_status=python_shka_gadgets_openstackclient.v1.vanilla:ShowStatus',
            'vanilla_take_ip=python_shka_gadgets_openstackclient.v1.vanilla:TakeIP',
            # 'vanilla_test=python_shka_gadgets_openstackclient.v1.vanilla:Test',
            'vanilla_unshelve=python_shka_gadgets_openstackclient.v1.vanilla:Unshelve',
        ],
    },
)
