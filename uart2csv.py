# Author : moonlight83340
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
DESCRIPTION: Python script for reading a line via UART and
             appending it to a CSV file along with a timestamp
"""

# -----------------------------------------------------------------------------
# include libraries and set defaults
# -----------------------------------------------------------------------------

from __future__ import print_function
import os
import operator
import serial
import serial.tools.list_ports
from datetime import datetime

folder_output = "csv"
#file_cfg      = "settings.cfg"

# -----------------------------------------------------------------------------
# settings (change this as required)
# -----------------------------------------------------------------------------

serial_baud_rate     = 115200
serial_timeout_read  = 0.05        # number of seconds after which we consider the serial read operation to have failed

# -----------------------------------------------------------------------------
# global variables
# -----------------------------------------------------------------------------

global selected_port       # serial port that will be used
global uart                # serial port object
global file_csv            # file object for the CSV file
global serial_read_ok      # 'True' if we read what we expected

# -----------------------------------------------------------------------------
# helper functions
# -----------------------------------------------------------------------------

def mkdir(folder_name):
    """create a new folder"""
    if not os.path.isdir(folder_name):
        try:
            os.makedirs(folder_name)
        except OSError:
            if not os.path.isdir(folder_name):
                raise

def get_available_serial_ports():
    available_ports_all = list(serial.tools.list_ports.comports())               # get all available serial ports
    available_ports = [port for port in available_ports_all if port[2] != 'n/a'] # remove all unfit serial ports
    available_ports.sort(key=operator.itemgetter(1))                             # sort the list based on the port
    return available_ports

def select_a_serial_port(available_ports):                                       # TODO: check file_cfg for preselected serial port
    global selected_port
    if len(available_ports) == 0:       # list is empty -> exit
        print("[!] No suitable serial port found.")
        exit(-1)
    elif len(available_ports) == 1:     # only one port available
        (selected_port,_,_) = available_ports[0]
        print("[+] Using only available serial port: %s" % selected_port)
    else:                               # let user choose a port
        successful_selection = False
        while not successful_selection:
            print("[+] Select one of the available serial ports:")
            # port selection
            item=1
            for port,desc,_ in available_ports:
                print ("    (%d) %s \"%s\"" % (item,port,desc))
                item=item+1
            while True:
                try:
                    # Try to convert input to integer
                    selected_item = int(input(">>> "))  
                    # If input is valid go to next line
                    break # End loop
                except:
                    # Handle Value Error
                    print("Invalid input!")
            # check if a valid item was selected
            if (selected_item > 0) and (selected_item <= len(available_ports)):
                (selected_port,_,_) = available_ports[selected_item-1]
                successful_selection = True
            else:
                print("[!] Invalid serial port.\n")

def open_selected_serial_port():
    global uart
    try:
        uart = serial.Serial(
            selected_port,
            serial_baud_rate,
            timeout  = serial_timeout_read,
            bytesize = serial.EIGHTBITS,
            parity   = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
        )
        print("[+] Successfully connected.")
    except serial.SerialException:
        print("[!] Unable to open %s." % selected_port)
        exit(-1)

def create_csv_file():
    global file_csv              # file object for CSV file
    mkdir(folder_output)         # create the output folder for the CSV files if it does not already exist
    file_csv = open('%s/%s.csv' % (folder_output,datetime.now().strftime("%Y-%m-%d %H-%M-%S")), 'w+', -1)  # FIXME: make sure the file is continuously flushed

def print_usage_guide():
    print("\nPress ENTER to read a line from the serial port.")
    print("Crtl + c to exit.")

def safe_exit():
    """exit program after releasing all resources"""
    global uart
    global file_csv
    successful_exit = False
    # close serial port
    try:
        uart.close()
        print("[+] Closed %s." % selected_port)
        successful_exit = True
    except serial.SerialException:
        print("[!] Unable to close %s." % selected_port)
    # close file
    try:
        file_csv.close()
        print("[+] Closed CSV file.")
        successful_exit = True
    except:
        print("[!] Unable to close CSV file.")
    # exit
    if successful_exit:
        print("\nprogram exiting gracefully")
        exit(0)
    else:
        print("\ntermination program error")
        exit(-1)

def get_uart_message():
    global uart
    global serial_read_ok
    # request the device's ID and read the response
    try:
        data_raw = uart.readline()
        data_raw = data_raw.strip()
        if data_raw:
            serial_read_ok = True
            output_data(data_raw.decode('utf-8'))
        else:
            serial_read_ok = False
    except KeyboardInterrupt:
        serial_read_ok = False
        uart.close()

def output_data(data_raw):
    global file_csv
    # create a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # append the result to the CSV
    if serial_read_ok:
        file_csv.write("%s,%s\n" % (timestamp, data_raw))
        
import sys, signal
def signal_handler(signal, frame):
    safe_exit()

# -----------------------------------------------------------------------------
# main program
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    select_a_serial_port(get_available_serial_ports())
    open_selected_serial_port()

    create_csv_file()

    print_usage_guide()

    # wait for enter
    user_input = input("")
    
    while True:
        serial_read_ok = False;
        get_uart_message()