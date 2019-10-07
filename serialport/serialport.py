#!/usr/bin/python

# This is free and unencumbered software released into the public domain.
# 
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
# 
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <https://unlicense.org>


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
author: Theron Bair
module: serialport
short_description: Use a local serial port as the connection method.
description:
  - This is a plugin to use the local serial port for connections.
version_added: "2.7"
options:
  serial_device:
    type: string
    description:
      - A path to a serial device.  Usually /dev/ttyXXX.
    default: '/dev/ttyUSB0'
    ini:
      - section: serialport
        key: serial_device
    env:
      - name: ANSIBLE_SERIAL_DEVICE
    vars:
      - name: ansible_serial_device
  serial_rate:
    type: int
    description:
      - A baud rate for the given serial device.
    default: 115200
    ini:
      - section: serialport
        key: serial_rate
    env:
      - name: ANSIBLE_SERIAL_RATE
    vars:
      - name: ansible_serial_rate
  command:
    description:
      - The command that will be run.
    required: true
  responses:
    type: dict
    description:
      - Mapping of expected strings/regexes and the string to respond with.  If the response is a list,
        successive matches return successive responses.
    required: true
  echo:
    description:
      - Whether or not to echo out your response strings.
    default: false
    type: bool
  timeout:
    type: int
    description:
      - Amount of time in seconds to wait for the expected strings.  Use C(null) to disable timeout.
    default: 30
requirements:
  - python >= 2.6
  - pexpect >= 3.3
  - pexpect_serial >= 0.1
  - pyserial >= 2.6
'''

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
import serial
import pexpect
from pexpect_serial import SerialSpawn

display = Display()

class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        if self._task.environment and any(self._task.environment):
            display.warning('The serialport task does not support the environment keyword')

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if self._play_context.check_mode:
            # in --check mode, always skip this module execution
            result['skipped'] = True
            result['msg'] = 'The serialport task does not support check mode'
        else:
            result['changed'] = True
            result['failed'] = False

        serial_device = self._task.args.get('serial_device', u'/dev/ttyUSB0')
        serial_rate = self._task.args.get('serial_rate', 115200)
        command = self._task.args.get('command')
        echo = self._task.args.get('echo', False)
        timeout = self._task.args.get('timeout', 30)
        responses = self._task.args.get('responses')

        with serial.Serial(serial_device, serial_rate, timeout=0) as ser:
            ss = SerialSpawn(ser)
            ss.sendline(command)
            for key, value in responses.items():
                display.v('key: {} value: {}'.format(key, value))
                ss.expect(key)
                ss.sendline(value)

        return dict()
