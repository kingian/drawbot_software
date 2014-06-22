from serial import Serial
from time import sleep
import logging
from Queue import Queue, Empty
from threading import Thread, Event
from warnings import warn
import re

log = logging.getLogger('grbl')
SERIAL_READ_TIMEOUT = 0.1 # seconds
SERIAL_LINE_ENDING = "\r"
GRBL_RX_BUFFER_SIZE = 128 # characters
BAUD = 9600
STATUS_POLLING_PERIOD = 5

class Grbl:
    def __init__(self, serial_device_path):
        log.debug('init with path "{}"'.format(serial_device_path))
        self.serial_device_path = serial_device_path
        self.serial_thread = None
        self.status_thread = None
        self.send_queue = None
        self.priority_send_queue = None
        self.disconnecting = Event()
        self.idle = Event()
        self.connected = Event()

    def _process_serial_io(self):
        log = logging.getLogger('grbl.serial')
        log.info('connecting to: {}'.format(self.serial_device_path))
        serial_port = Serial(self.serial_device_path, BAUD, timeout=SERIAL_READ_TIMEOUT)

        grbl_buffered_commands = []
        grbl_buffered_command_sizes = []
        command_to_send = None
        priority_command_to_send = None

        def pop_command(response, log_method=log.debug):
            log_method('{} response: {}'.format(grbl_buffered_commands[0].__repr__(), response))
            del grbl_buffered_commands[0]
            del grbl_buffered_command_sizes[0]

        def fetch_queued_command(queue, queue_name):
            try:
                command_to_send = queue.get_nowait()
                log.debug('fetched from {}: {}'.format(queue_name, command_to_send))
                command_to_send += SERIAL_LINE_ENDING
                if len(command_to_send) > GRBL_RX_BUFFER_SIZE:
                    raise Exception('command exceeds grbl buffer size')
                return command_to_send
            except Empty:
                log.debug('tried to read empty queue')
                return None

        def send_command(command_to_send):
            log.debug('write: {}'.format(command_to_send.__repr__()))
            serial_port.write(command_to_send)
            grbl_buffered_command_sizes.append(len(command_to_send))
            grbl_buffered_commands.append(command_to_send.strip())

        def read_response():
            response = serial_port.readline().strip()
            if response:
                log.debug('read: {}'.format(response.__repr__()))
                if response.find('error') == 0:
                    pop_command(response, log_method=log.warn)
                elif response == 'ok':
                    pop_command(response)
                elif response[0] == '<':
                    self._state, mpos, wpos = re.match(r'^<(\w+),MPos:([\-\d.,]+),WPos:([\-\d.,]+)>$', response).groups()
                    self._machine_position = tuple(float(n) for n in mpos.split(','))
                    self._work_position = tuple(float(n) for n in wpos.split(','))
                    self._status_update()

        def can_send(command_to_send):
            return command_to_send and sum(grbl_buffered_command_sizes) + len(command_to_send) <= GRBL_RX_BUFFER_SIZE

        while True:
            line = serial_port.readline().strip()
            log.debug('read: {}'.format(line.__repr__()))
            if line:
                if line.find('Grbl') == 0:
                    break
                else:
                    raise Exception("didn't find grbl welcome message where expected")
        serial_port.flushInput()
        log.info('done connecting')
        self.connected.set()

        # priorities are:
        # 1. send a priority command
        # 2. fetch a priority command from the priority send queue
        # 3. send a command
        # 4. fetch a command from the send queue
        # 5. process incoming data from grbl
        # 6. short sleep to be a good thread neighbor
        while not self.disconnecting.is_set():
            if priority_command_to_send:
                send_command(priority_command_to_send)
                priority_command_to_send = None
            elif not priority_command_to_send and not self.priority_send_queue.empty():
                priority_command_to_send = fetch_queued_command(self.priority_send_queue, 'priority queue')
            elif not priority_command_to_send and can_send(command_to_send):
                send_command(command_to_send)
                command_to_send = None
            elif not command_to_send and not self.send_queue.empty():
                command_to_send = fetch_queued_command(self.send_queue, 'queue')
            elif serial_port.inWaiting():
                read_response()
            else:
                sleep(0.01)
        log.debug('disconnecting')
        self.connected.clear()
        serial_port.close()
        log.info('disconnected')

    def connect(self):
        if self.serial_thread and self.serial_thread.is_alive():
            warn('serial port already connected. not trying to reopen')
        else:
            log.debug('starting serial io thread')
            self.send_queue = Queue()
            self.priority_send_queue = Queue()
            self.disconnecting.clear()
            self.idle.clear()
            self.serial_thread = Thread(target=self._process_serial_io, name='grbl-serial')
            self.serial_thread.daemon = True
            self.serial_thread.start()
            self._start_polling_status()

    def _poll_status(self):
        while self.serial_thread and self.serial_thread.is_alive():
            self.connected.wait()
            self._get_status()
            sleep(STATUS_POLLING_PERIOD)
        log.debug('status polling thread shutting down')
        self.idle.set() # not technically correct, but keeps wait_for_idle from stalling forever if the serial thread craps out during a move
        self.connected.clear()

    def _start_polling_status(self):
        if self.status_thread and self.status_thread.is_alive():
            warn('already polling status. not starting another thread')
        else:
            log.debug('starting status polling thread')
            sleep(3) # super hacky. wait for grbl to connect
            self.status_thread = Thread(target=self._poll_status, name='poll-status')
            self.status_thread.daemon = True
            self.status_thread.start()

    def disconnect(self):
        log.info('requesting serial disconnect')
        self.disconnecting.set()

    def _status_update(self):
        if self.is_idle():
            self.idle.set()
        else:
            self.idle.clear()

    def _get_status(self):
        self._execute('?')

    def hold(self):
        log.info('holding feed')
        self._execute('!')

    def start(self):
        log.info('cycle start')
        self._execute('~')

    def is_idle(self):
        return self._state == 'Idle'

    def wait_for_idle(self, timeout=None):
        log.debug('waiting for idle')
        sleep(STATUS_POLLING_PERIOD) # in case the user feeds in commands and calls this before we read the 'running' state
        self.idle.wait(timeout)

    def _execute(self, script):
        "Immediately sends a string of commands to grbl, bypassing queued commands"
        lines = script.splitlines()
        for line in lines:
            self.priority_send_queue.put(line)

    def queue(self, script):
        "Queues a string of commands for streaming to grbl"
        lines = script.splitlines()
        for line in lines:
            self.send_queue.put(line)
