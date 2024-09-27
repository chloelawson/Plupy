"""
This document contains the python functions used in the plume experiment

The document is devided into classes which group the Different Functions used for each device.

Authors: Enzo Picinnoi and Chloe Lawson
"""

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
### Importing libraries
import serial
import time
from contextlib import contextmanager
import numpy as np
import pyvisa
import os
import sys
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
### General Functions
@contextmanager
def initialize_device(port, brate, bsize, par, stopb):
    """
    DESCRIPTION:
        Stablishes communication with a device and closes the conection before finishing
            
    PARAMETERS:
        port(string): Port in which the device is connected in the format of "COM##"
        
        brate(int): Baud rate of the connected device defaults to 115200
        
        bsize: bytesize, defaults to default to EIGHTBITS, need to use the serial library variables
                                accepts: serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS. serial.FIVEBITS
        
        par: Parity,need to use the serial library variables
                                accepts: serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
        
        stopb: Stopbits, need to use the serial library variables
                                accepts: serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
    
    RETURNS:
        None
    """
    
    device = serial.Serial(port = port, baudrate=brate, bytesize=bsize, parity=par, stopbits=stopb, timeout = 1.5)
    try:
        yield device
    finally:
        device.close()
    
def command(port, command, brate, bsize, par, stopb, repeat = False, good_response = b"ok\r\n"):
    """
    DESCRIPTION:
        Sends the input serial command to the device connected to the specified port
        
    PAARAMETERS:
        port(string): Port in which the device is connected in the format of "COM##"
        
        command(str): The command which you wuld like to send to the device 
        
        brate(optional int): Baud rate of the connected device defaults to 115200
        
        bsize: bytesize, need to use the serial library variables
                                accepts: serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS. serial.FIVEBITS
        
        par: Parity,need to use the serial library variables
                                accepts: serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
        
        stopb: Stopbits, need to use the serial library variables
                                accepts: serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
                                
        repeat (optional): Repeat the command to ensure it returns the good response, default is False
        
        good_response (optional): Expected response if successfull, default is b"ok\r\n"
        
    RETURNS:
        res: the response from the device
    """
    with initialize_device(port, brate, bsize, par, stopb) as device: 
        while True:
            device.write(str.encode(command)) # Sending the command
            res = device.readline() # Reading response
            if res == good_response: # Checking if the response is what we want
                repeat = False
                
            if not repeat: # Breaking the loop
                break
        pass
    return res

def get_file_name(set_delay, true_delay):
    """
    DESCRIPTION:
        Given the delay information for the flashlamp, generates the file name to be used, following the format "[time]_[set delay]_[true delay].[file type]"
        
    PARAMETERS:
        set_delay: ideal value of the delay between the last pulse and the flash lamp, set by the user
        
        true_delay: actual delay measured from the TDC
        
    RETURNS:
        filename: name of the file to be used
    """
    date = round(time.time())
    
    filename = str(date) + "_" + f"{set_delay:09d}" + "_" + f"{true_delay:09d}"
    
    return filename

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
### Class definition and functions for pulse Generator
class pulse_generator:
    def __init__(self, port, baud_rate, bit_size, parity, stop_bits):
        """        
        Class for the Quantum Composers Pulse Generator Series 9520
        
        CLASS ELEMENTS:
        
        port(string): Port in which the device is connected in the format of "COM##"
        
        baud_rate(int): Baud rate of the connected device defaults to 115200
        
        bit_size: bytesize, defaults to default to EIGHTBITS, need to use the serial library variables
                            accepts:
                                serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS. serial.FIVEBITS
        
        parity: Parity,need to use the serial library variables
                            accepts: 
                                serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
        
        stop_bits: Stopbits, need to use the serial library variables
                            accepts:
                                serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
        """
        self.port = port
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.bit_size = bit_size

    def run(self):
        """
        DESCRIPTION:
            Starts the Pulse Generator (equivalent to pressing the run/stop button)
            
        PARAMETERS:
            None
            
        RETURNS:
            res: Response from the Pulse generator
        """
        res = command(self.port, ":PULSE0:STATE ON\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res

    def stop(self):
        """
        DESCRIPTION:
            Stops the Pulse Generator (equivalent to pressing the run/stop button)
            
        PARAMETERS:
            None
        
        RETURNS:
            res: Response from the Pulse generator
        """        
        res = command(self.port, ":PULSE0:STATE OFF\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res
    
    def reset(self):
        """
        DESCRIPTION:
            Resets the Pulse Generator
            
        PARAMETERS:
            None
        
        RETURNS:
            res: Response from the Pulse generator
        """
        res = command(self.port, "*RST\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res

    def set_channel(self, channel, delay, width, amp = 3, mode = "TTL" ,ref = "T0", cmode = "SINGLE", enable = True):
        """
        DESCRIPTION:
            Sets all of the individual parameters of the specified channel
        
        PARAMETERS:
            channel: Channel to be set one of A, B, C or D
                                accepts:
                                    "A", "B", "C", "D"
            
            delay: delay in seconds for the pulse to be sent from the moment when the pulse generator starts
            
            width: width in seconds of the pulse
            
            amp (optional): amplitude of the pulse in Volts, will only be relevant if mode is adjustable, otherwise TTL is 5V. Defaults to 3V.
                                
            mode (optional): the mode of the output signal either defaults to "TTL"
                                accepts:
                                    "TTL", "ADJUSTABLE"
            
            ref (optional): Reference point of the delay (TO or one of the channels), default to TO
                                accepts:
                                    "T0", "CHA", "CHB", "CHC", "CHD"
            
            cmode (optional): Output mode of the pulse generator, default to Single Shot 
                                accepts:
                                    "NORMAL", "SINGLE", "BURTS", "DCYCLE"
            
            enable (optional): If True the channel will be enabled at the end of the settings, defaults to True
        
        RETURNS:
            True, if all settings are successfull

        """
        # Converting the imputs to String
        channel_str = str(ord(channel) - 64)
        delay_str = str(delay)
        width_str = str(width)
        amp_str = str(amp)
        
        
        if ref != "T0":
            ref = "CH" + ref
        
        command(self.port, ":PULSE" + channel_str + ":SYNC " + ref + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port, ":PULSE" + channel_str + ":CMODE "+ cmode +"\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port, ":PULSE" + channel_str + ":OUTPUT:AMPLITUDE " + amp_str + "V\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port, ":PULSE" + channel_str + ":DELAY " + delay_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port, ":PULSE" + channel_str + ":WIDTH " + width_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port, ":PULSE" + channel_str + ":OUTPUT:MODE " + mode + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        
        if enable:
            command(self.port, ":PULSE" + channel_str + ":STATE ON\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        else:
            command(self.port, ":PULSE" + channel_str +":STATE OFF\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        
        return True

        
    def setup(self, flash_delay, skip_num, width1, width2):
        """
        DESCRIPTION:
            Calculates the time at which all the pulses must start so that to match the width of the pulse, and sets the channels accordingly

        PARAMETERS:
            flash_delay(float): Ideal time between the laser shot and the flashlamp in seconds with the smalles possible time being nanoseconds
            
            skip_num(int): Number of pulses to skip before sending the first pedal 
            
            width(float): Width of the pedal pulses in seconds with the smallest possible decimal being nanoseconds
            
        RETURNS:
            None
        """
        period = 0.00099997090 # Period of the PILR Laser
        pedal_delay = 0.00020844 # Time prior to the actual pulse, which the pedal must be sent
        
        # The values are rounded to the 11th digit, since that is the precision of the Pulse Generator
        pulse1_start = round(skip_num * period - pedal_delay - 0.000005 , 11)
        pulse2_start = round((skip_num * period - pedal_delay - 0.000005) + period, 11) + 2*10**(-6)
    

        flash_start = round((skip_num + 1) * period + flash_delay, 11)
        
        self.reset()
        self.set_trigger(level = 0.5)
        self.set_channel(channel = "C", delay = 0.0, width = 0.0005) # Cam
        self.set_channel(channel = "A", delay = pulse1_start , width= width1) # P1 
        self.set_channel(channel = "B", delay = pulse2_start, width= width2) # P2 
        self.set_channel(channel = "D", delay =  flash_start, width = 0.000008) # Flash
  
    def set_trigger(self, level, edge = "RISING"):
        """
        DESCRIPTION:
            Sets the pulse generator to trigger mode and set the trigger parameters
            
        PARAMETERS:
            level: Required voltage to activate the trigger, 
                                accepts: 
                                    between 0.20V and 15V
            
            edge (optional): Edge logic of the trigger
                                accepts: 
                                    "RISING" or "FALLING", default to "RISING"
            
        RETURNS:
            True if sucessfull
        """
        # Converting the input to String
        level_str = str(level)
        
        command(self.port,":PULSE0:TRIG:MODE TRIG\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port,":PULSE0:TRIGGER:LEVEL " + level_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port,":PULSE0:TRIGGER:EDGE " + edge + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)

        return True
        
    def set_gate(self, level, logic = "HIGH"):
        """
        DESCRIPTION:
            Set the pulse generator to gate mode and set the gate parameters
            
        PARAMETERS:
            level: Required voltage to activate the gate
            
            logic (optional): Gate logic
                                accepts:
                                    "HIGH" or "LOW", default to "HIGH"
            
        RETURNS:
            True if sucessfull
        """
        # Converting the input to String
        level_str = str(level)
        
        command(self.port,":PULSE0:GATE:MODE PULSE\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port,":PULSE0:GATE:LEVEL " + level_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port,":PULSE0:GATE:LOGIC " + logic + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)

        return True 

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Class definition and functions for pulse Generator BNC 505
class BNC_505:
    def __init__(self, port, baud_rate, bit_size, parity, stop_bits):
        """    
        class for the Berkely Nucleonics Corporation model 505 pulse generator
        
        CLASS ELEMENTS:
            
            port(string): Port in which the device is connected in the format of "COM##"
        
            baud_rate(int): Baud rate of the connected device defaults to 115200
        
            bit_size: bytesize, defaults to default to EIGHTBITS, need to use the serial library variables
                                accepts: 
                                    serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS. serial.FIVEBITS
        
            parity: Parity,need to use the serial library variables
                                accepts: 
                                    serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
        
            stop_bits: Stopbits, need to use the serial library variables
                                accepts: 
                                    serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
        """
        self.port = port
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.bit_size = bit_size
        return 
    
    def run(self):
        """
        DESCRIPTION:
            Starts the Pulse Generator (equivalent to pressing the run/stop button)
            
        PARAMETERS:
            None
            
        RETURNS:
            res: response from the pulse generator
        """
        res = command(self.port, ":PULSE0:STATE ON\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res
        
    def stop(self):
        """
        DESCRIPTION:
            Stops the Pulse Generator (equivalent to pressing the run/stop button)
            
        PARAMETERS:
            None
        
        RETURNS:
            res: response from the pulse generator
        """        
        res = command(self.port, ":PULSE0:STATE OFF\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res
    
    def reset(self):
        """
        DESCRIPTION:
            Resets the Pulse Generator
            
        PARAMETERS:
            None
        
        RETURNS:
            res: response from the pulse generator
        """
        res = command(self.port, "*RST\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res

    def save(self, mem = 1):
        """
        DESCRIPTION:
            Saves the current settings to a memory block
            
        PARAMETERS:
            mem: memory block which the settings will be saves at, accepts values between 1 and 10 
            
        RETURNS:
            res: response from the pulse generator
        """
        mem_str = str(mem)
        res = command(self.port, "*SAV " + mem_str + "\r\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res
    
    def recall(self, mem = 1):
        """
        DESCRIPTION:
            recalls the settings saved to the memory b;lock spesified
            
        PARAMETERS:
            mem: memory block which the settings will be pullsed from, accepts values between 1 and 10 
        
        RETURNS:
            res: response from the pulse generator
        """
        mem_str = str(mem)
        res = command(self.port, "*RCL " + mem_str + "\n", brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        return res
    
    def set_trigger(self, level, edge = "RISING"):
        """
        DESCRIPTION:
            Set the pulse generator to trigger mode and set the trigger parameters
            
        PARAMETERS:
            level: Required voltage to activate the trigger, must be between 0.20V and 15V
            
            edge (optional): Edge logic of the trigger
                                accepts:
                                    "RISING" or "FALLING", default to "RISING"
            
        RETURNS:
            True if reaches the end 
        """
        # Converting the input to String
        level_str = str(level)
        
        command(self.port,":PULSE0:EXTernal:MODe TRIGger\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port,":PULSE0:EXTernal:LEVel " + level_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
        command(self.port,":PULSE0:EXTernal:EDGe " + edge + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)

        return True 

    def set_channel(self, channel, delay, width, amp = 3 ,ref = "T0", cmode = "SINGLE", enable = True):
      """
      DESCRIPTION: 
          Sets all of the individual parameters of the specified channel
      
      PARAMETERS:
          channel: Channel to be set one of T1, T2, 
                              accepts: 1 or 2
          
          delay: delay in seconds for the pulse to be sent from the moment when the pulse generator starts
          
          width: width in seconds of the pulse
          
          amp (optional): amplitude of the pulse in Volts, will only be relevant if mode is adjustable, otherwise TTL is 5V. Defaults to 3V
                              
          ref (optional): Reference point of the delay (T0 or one of the channels), default to "T0", 
                              accepts: "T0", "T1", "T2"
          
          cmode (optional): Output mode of the pulse generator, default to Single Shot 
                              accepts(str): "NORMAL", "SINGLE", "BURTS", "DCYCLE"
          
          enable (optional): If True the channel will be enabled, default to True
      
      RETURNS
          None

      """        
      # Converting the imput to String
      channel_str = str(channel)
      delay_str = str(delay)
      width_str = str(width)
      amp_str = str(amp)
      
      command(self.port, ":PULSE" + channel_str + ":SYNC " + ref + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
      command(self.port, ":PULSE" + channel_str + ":CMODE "+ cmode +"\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits) # Set to send a single pulse
      command(self.port, ":PULSE" + channel_str + ":OUTPUT:AMPLITUDE " + amp_str + "V\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
      command(self.port, ":PULSE" + channel_str + ":DELAY " + delay_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)
      command(self.port, ":PULSE" + channel_str + ":WIDTH " + width_str + "\n", repeat = True, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits)

      return True

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Class definition and functions for Arduino Uno
class arduino_UNO:    
    def __init__(self, port, baud_rate, bit_size, parity, stop_bits):
        """   
        class for arduino uno
        functions are designed to work with fifteen instruments TDC connected via USB host sheild to the UNO
        functions are designed to work with Arduino IDE code Z:/Users/coop/Chloe_Enzo_2024/Master codes/code_for_UNO
        
        CLASS ELEMENTS:
            
            port(string): Port in which the device is connected in the format of "COM##"
        
            baud_rate(int): Baud rate of the connected device defaults to 115200
        
            bit_size: bytesize, defaults to default to EIGHTBITS, need to use the serial library variables
                                accepts: 
                                    serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS. serial.FIVEBITS
        
            parity: Parity,need to use the serial library variables
                                accepts: 
                                    serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
        
            stop_bits: Stopbits, need to use the serial library variables
                                accepts: 
                                    serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
        """
        self.port = port
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.bit_size = bit_size
    
    def read_timestamps(self, binary_stream, legacy = True):
        """
        (Modified from S15lib.instruments)
        DESCRIPTION:
            Reads the timestamps accumulated in a binary sequence and returns a
            Tuple[List[float], List[str]]: with the event times in ns and the 
            corresponding event channel. The channel are returned as string where
            a 1 indicates the trigger channel. For example an event in channel 2
            would correspond to "0010". Two coinciding events in channel 3 and 4
            correspond to "1100".
        
        PARAMETERS:
            binary_stream: binary input to be read
            
        RETURNS
            ts_list: list containing the timestamps at which signals were received
            event_channel_list: list containing the respective channels which received the signals
        """
        # Changing the input
        bytes_hex = binary_stream[::-1].hex() # reverts the stream and converts is to hexadecimal
        ts_word_list = [    
            int(bytes_hex[i : i + 8], 16) for i in range(0, len(bytes_hex), 8)
            ][::-1] # Truncates the initial stream into packages of two 8-character "words" and 
                    # converts to integers and reverses back to the order from before

        # Initializing variables
        ts_list = []
        event_channel_list = []
        periode_count = 0 # How many rollovers (count restart) happend so far
        periode_duration = 1 << 27 # This is the length of 1 period (same as 2^27)
        prev_ts = -1 # means that no other timestamp was analysed yet
        
        # Iterating for each "words"
        for ts_word in ts_word_list:
            time_stamp = ts_word >> 5 # Removing the last five charachters since they dont have
                                      # timestamp information (only dummy flag and detector pattern)
                                      
            pattern = ts_word & 0x1F # This gets the last 5 bits of the word, that is, the dummy flag
                                     # and the detector pattern
            
            if prev_ts != -1 and time_stamp < prev_ts: # Checks if the new timestamp is  smaller than the 
                                                       # previous one (), which would happend if there is a
                                                       # rollover (restart the count)
                periode_count += 1 # increase the period count to use it latter
            
            prev_ts = time_stamp # sets the previous timestamp to compare with the next one
            
            if (pattern & 0x10) == 0: # Check if the 5 last bit (dummy flag) of the word is zero which indicates that the timestamp is valid.
                                     
                ts_list.append(time_stamp + periode_duration * periode_count)
                # This calculates the actual timestamp by adding the original value with the number of 
                # periods (number of rollovers) * the duration of the period and appends it to a list
                
                if legacy:
                    # Save the channels as a binary string
                    event_channel_list.append("{0:04b}".format(pattern & 0xF))
                else:
                    # Save the channels as integers
                    event_channel_list.append(pattern & 0xF)
        ts_list = np.array(ts_list, dtype="int64") * 2  # Each step is equivalent to 2ns
        if not legacy:
            event_channel_list = np.array(event_channel_list)
        return ts_list, event_channel_list
    
    def convert_units(self, counts_ns, units = 'ns'):
        """ 
        DESCRIPTION:
            takes an list of counts where count times in nanoseconds 
            and returns an array of seperated values in the spesified units 
        
        PARAMETERS:
            counts_ns: list of counts in nanoseconds [   xxxxxxx xxxxxxx xxxxxxx]
            
            units (optional) - units of time in string format lowercase of the following options, 
            'ns', 'us', 'ms', 's'. Default is 'ns'.
        
        RETURNS
            counts_converted: array of counts in the specified units
        """
        counts_ns = np.array(counts_ns) # Changing to an Array 
        
        # Selecting the Units
        if units == 'ns':
            counts_converted = counts_ns
        
        elif units == 'us':
            counts_converted = counts_ns * 10**(-3)
        
        elif units == 'ms':
            counts_converted = counts_ns * 10**(-6)
        
        elif units == 's':
            counts_converted = counts_ns * 10**(-9)
            
        return counts_converted
    
    def channel_cleaner(self, cha_info):
        """
        DESCRIPTION:
            takes an array of 4 digit code for channels sending the pulse and returns the 
            channels that sent the triggers
        
        PARAMETERS:
            cha_info(array): Array containg the code for the channels [   xxxx xxxx xxxx xxxx ...] 
            
        RETURNS
            cha_clean: List of the channels received in order correspondent to the counts
            
            (counts1, ...): tupple containing the number of counts each channel received
        """
        
        cha_clean = []
        counts_1 = 0
        counts_2 = 0
        counts_3 = 0
        counts_4 = 0
        
        # Converting from the 4 digits to channels
        for cha_list in cha_info: 
            channel = []
            if cha_list[0] == '1':
                channel.append('CH4')
                counts_4 += 1
    
            if cha_list[1] == '1':
                channel.append('CH3')
                counts_3 += 1
                
            if cha_list[2] == '1':
                channel.append('CH2')
                counts_2 += 1
    
            if cha_list[3] == '1':
                channel.append('CH1')
                counts_1 += 1
    
            cha_clean.append(channel)
        
        return cha_clean, (counts_1, counts_2, counts_3, counts_4)
        
    def start(self):
        """
        DESCRIPTION:
            sends the command to the arduino to start and will wait for a time (delay)
            before reading the results from the Uno. In the Arduino IDE, when we send start 
            this will trigger the arduino timing for the arduino to start the TDC, send the prepulse
            open the shutter, then recieve the results from the TDC and send them to the serial connection.
            This function will also use other functions to take the hex stream an clean it to a readable 
            depiction of the TDC results. 
    
        PARAMETERS:
            None
            
        RETURNS:
            results from TDC
        """
        with initialize_device(self.port, brate = self.baud_rate, bsize = self.bit_size, par = self.parity, stopb = self.stop_bits) as UNO:
            
            first_com = b""
            while True:
                while first_com != b"start\n":
                    UNO.write(str.encode("start\n"))
                    time.sleep(0.1)
                    first_com = UNO.readline()

                
                
                #print(first_com)
                hex_stream = UNO.readline()
                [counts, cha_info] = self.read_timestamps(hex_stream)

                if hex_stream != b'' and hex_stream != b"start" and hex_stream != b'\r\n'  and hex_stream != b"a":
                    counts = self.convert_units(counts, 'ns')
                    channels, ch_counts = self.channel_cleaner(cha_info)
                    return counts, channels, ch_counts
                    
                    break
            pass
        
        
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Class definition and functions for Camera        
class thor_camera:
    def __init__(self):
        """
        class for thorlabs compact scientific camera model CS505MU1 
        
        CLASS ELEMENTS:
            None
        """
        pass
    
    def windows_set_up(self):
        """
        (Adapted From Thorlabs Library)
        DESCRIPTION:
            Set up the path to the dlls older on the computer, which hte code need to access in order to function correctly
        
        PARAMETERS:
            None
        
        RETURNS:
            None
        """
        try:
            is_64bits = sys.maxsize > 2**32
            relative_path_to_dlls = '.' + os.sep + 'dlls' + os.sep
        
            if is_64bits:
                relative_path_to_dlls += 'Native_64_lib'
            else:
                relative_path_to_dlls += '32_lib'
                
            absolute_path_to_file_directory = os.path.dirname(os.path.abspath(__file__))
            
            absolute_path_to_dlls = os.path.abspath(absolute_path_to_file_directory + os.sep + relative_path_to_dlls)
        
            os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']
        
            try:
                os.add_dll_directory(absolute_path_to_dlls)
            except AttributeError:
                pass
        except ImportError:
            configure_path = None
        
    def set_params(self, exp, frames, mode):
        """
        DESCRIPTION:
            Sets the exposture and mode of the camera
        
        PARAMETERS:
            exp - exposure time in microseconds
            frames - sets the frams per trigger, 1 for trigger 0 for continuous and multiple for many shots per trigger
            mode - set as 1 for hardware trigger, 2 for bulb mode and 0 for software trigger 
        
        RETURNS
            None
        """
        self.windows_set_up()
            
        with TLCameraSDK() as sdk:
            available_cameras = sdk.discover_available_cameras()
            if len(available_cameras) < 1:
                print("no cameras detected")
            
            with sdk.open_camera(available_cameras[0]) as camera:
                camera.exposure_time_us = exp  # Set exposure
                camera.frames_per_trigger_zero_for_unlimited = frames
                camera.image_poll_timeout_ms = 1000  # 1 second polling timeout
                camera.operation_mode = mode # Set operation Mode

    def arm_camera(self):
        """
        DESCRIPTION: 
            Arm the camera so that it is waiting for a trigger
        
        PARAMETERS:
            None
            
        RETURNS:
            None
        """
        global sdk, available_cameras, camera
        self.windows_set_up()
        
        sdk = TLCameraSDK()
        available_cameras = sdk.discover_available_cameras()
        if len(available_cameras) < 1:
            print("no cameras detected")
        
        camera = sdk.open_camera(available_cameras[0])
        camera.arm(2)
        
    def get_image(self, filename):
        """
        DESCRIPTION: 
            When run with hardware trigger parameters will continue to run until hardware trigger is recieved and photo is taken. The Image
            is saved in the image folder with the name "filename.npy"
        
        PARAMETERS:
            filename: name of the file to be saved
            
        RETURNS:
            None
        """
        global sdk, available_cameras, camera
        
        frame = camera.get_pending_frame_or_null()

        if frame is not None:
            #print("frame #{} received!".format(frame.frame_count))
            frame.image_buffer
            image_buffer_copy = np.copy(frame.image_buffer)
            numpy_shaped_image = image_buffer_copy.reshape(camera.image_height_pixels, camera.image_width_pixels)
            nd_image_array = np.full((camera.image_height_pixels, camera.image_width_pixels, 3), 0, dtype=np.uint8)
            nd_image_array[:,:,0] = numpy_shaped_image
            nd_image_array[:,:,1] = numpy_shaped_image
            nd_image_array[:,:,2] = numpy_shaped_image
        else:
            print("No frame detected")
        camera.disarm()
        # Because we are using the 'with' statement context-manager, disposal has been taken care of.
        save_dir = "Z:/Users/coop/Chloe_Enzo_2024/Images"
        file_path = os.path.join(save_dir, filename)

        np.save(file_path, nd_image_array)
        return 
    
    def close_camera(self):
        """
        DESCRIPTION: 
            Disposes the camera
        
        PARAMETERS:
            None
            
        RETURNS:
            None
        """
        global sdk, available_cameras, camera
        camera.dispose()
        sdk.dispose()

        
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Class definition and functions for Oscilloscope
# IMPORTANT: In order for the oscilloscope to send correct measurements to the computer it needs to have
# the measure menu open on the left hand side of the screen (so you could rean the measurement from the screen)

rm = pyvisa.ResourceManager()
class oscilloscope:
    def __init__(self):
        """
        class for Tektronix TDS 2014C oscilloscope 
        
        CLASS ELEMENTS:
            None
        """
        pass
    
    def ready(self):
        """
        DESCRIPTION:
            tells the oscilloscope to wait for a single shot and when it recieves that shingle shot it will freeze, also puts oscilloscope to the measurement screen 
            
        PARAMETERS:
            None
            
        RETURNS:
            None
        """
        try:
            scope = rm.open_resource('USB::0x0699::0x03A4::C015987::INSTR', send_end=True)
            scope.timeout = None
        except pyvisa.Error as e:
            print(f'Error opening oscilloscope: {str(e)}')
            
        scope.write("ACQuire:STATE RUN")   
        scope.write("ACQuire:STOPAfter SEQuence")
         
          
        
        return 
    
    def setup(self, meas_num, meas_source, meas_type):
        """
        DESCRIPTION:
            Sets up the parameters for the measurement in the oscilloscope
            
        PARAMETERS:
            meas_num - the number between 1 and 5 spesifying the measurement on the oscilloscope which contains the desired value
                                    accepts (int): 1, 2, 3, 4 or 5
            meas_source - Channel used for the measurement
                                    accepts (int): 1, 2, 3 or 4
            
            meas_type - type of measurement, refeer to the manual: https://download.tek.com/manual/TBS1000-B-EDU-TDS2000-B-C-TDS1000-B-C-EDU-TDS200-TPS2000-Programmer.pdf
            
        RERTURN:
            None
        """
        meas_num_str = str(meas_num)
        meas_source_str = str(meas_source)
        
        try:
            scope = rm.open_resource('USB::0x0699::0x03A4::C015987::INSTR', send_end=True)
            scope.timeout = None
        except pyvisa.Error as e:
            print(f'Error opening oscilloscope: {str(e)}')
        
        scope.write("MEASUrement:MEAS"+ meas_num_str + ":SOUrce CH" + meas_source_str)
        scope.write("MEASUrement:MEAS"+ meas_num_str + ":TYPE " + meas_type)
        
    
    def save(self, mem = 1):
        """
        DESCRIPTION:
            saves the current settings to the memory location indicated
            
        PARAMETERS:
            mem - memory location block which desird settings will be located defaulst to 1
            
        RERTURN:
            None
        """
        try:
            scope = rm.open_resource('USB::0x0699::0x03A4::C015987::INSTR', send_end=True)
            scope.timeout = None
        except pyvisa.Error as e:
            print(f'Error opening oscilloscope: {str(e)}')
            
        mem_str = str(mem) 
        scope.write("SAVE:SETUP " + mem_str)  
        
        return 
        
    def recall(self, mem = 1):
        """
        DESCRIPTION:
            recalls the saved settings from the memory location indicated and tessl the oscilloscope to go to the measuremtn screen 
            
        PARAMETERS:
            mem - memory location block which desird settings are located defaults to 1

        RERTURN:
            None
        """
        try:
            scope = rm.open_resource('USB::0x0699::0x03A4::C015987::INSTR', send_end=True)
            scope.timeout = None
        except pyvisa.Error as e:
            print(f'Error opening oscilloscope: {str(e)}')
            
        mem_str = str(mem) 
        scope.write("RECALL:SETUP " + mem_str)            

        
    def get_value(self, meas_num):
        """
        DESCRIPTION:
            requests a measurement from the oscilloscope and prints it 
        
        PARAMETERS:
            meas_num - the number between 1 and 5 spesifying the measurement on the oscilloscope which contains the desired value
            
        RETURNS:
            voltage: The value measured for the voltage in the specified measurement number
        
        """
        meas_num_str = str(meas_num)
        
        try:
            scope = rm.open_resource('USB::0x0699::0x03A4::C015987::INSTR', send_end=True)
            scope.timeout = None
        except pyvisa.Error as e:
            print(f'Error opening oscilloscope: {str(e)}')
            
        voltage = float(scope.query("MEASUrement:MEAS" + meas_num_str + ":VALue?"))
        return voltage
        
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Class definition and functions for SMD2

class stepper_motor:
    def __init__(self, port, baud_rate, bit_size, parity, stop_bits):
        """
        class for SMD2 stepper motor driver 
        
        CLASS ELEMENTS:
            port: COM port to be used
            
            baud_rate: Baud rate of the device
            
            parity: Parity of the device
            
            stop_bits: stop bits of the device
            
            bit_size: bit size of the device
        """
        self.port = port
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.bit_size = bit_size
        self.b1_flag = False
        self.b2_flag = False
        self.end = False
    
    def back(self, steps):
        """
        DESCRIPTION:
            Moves the motor back, looking from the breadboard, a specified number of steps
                
        PARAMETERS:
            steps: number of steps to move
            
        RETURNS:
            res: Response from the device
        """
        
        steps_str = str(steps)
        
        command(self.port, "B1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        res = command(self.port, "-" + steps_str + "\r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        
        return res

    def forward(self, steps):
        """
        DESCRIPTION:
            Moves the motor forward, looking from the breadboard, a specified number of steps
                
        PARAMETERS:
            steps: number of steps to move

        RETURNS:
            res: Response from the device
        """
        
        steps_str = str(steps)
        
        command(self.port, "B1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        res = command(self.port, "+" + steps_str + "\r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        return res
    
    def right(self, steps):
        """
        DESCRIPTION:
            Moves the motor right, looking from the breadboard, a specified number of steps
                
        PARAMETERS:
            steps: number of steps to move
            
        RETURNS:
            res: Response from the device
        """
        steps_str = str(steps)
        
        command(self.port, "B2 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        res = command(self.port, "-" + steps_str + "\r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        return res
        
    def left(self, steps):
        """
        DESCRIPTION:
            Moves the motor left, looking from the breadboard, a specified number of steps
                
        PARAMETERS:
            steps: number of steps to move
            
        RETURNS:
            res: Response from the device
        """        
        steps_str = str(steps)
        
        command(self.port, "B2 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        res = command(self.port, "+" + steps_str + "\r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        return res
    
    def new_position(self, steps, size):
        """
        DESCRIPTION:
            checks location of stage and moves it in the correct way such to make a pattern of ablation shots across the sample, will do this by moving 500 steps each time
            called in either right left forwards or backwards direction depending on current location s that a 2500 step square is made in the following pattern;
            
            -> -> -> -> -> -> -> |
            |  <- <- <- <- <- <- V
            V -> -> -> -> -> -> |
            | <- <- <- <- <- <- V
            V -> -> -> -> -> -> |
            | <- <- <- <- <- <- V
            V -> -> -> -> -> -> |
            | <- <- <- <- <- <- V
              
        PARAMETERS:
            steps: Number of steps to walk between two positions
            
            size: Maximum number of steps to be taken in either direction (determines the limits of the sample)
        
        RETURNS:
            None
        """
        command(self.port, "B2 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        
        
        # Getting the position in integers
        position1 = int(bytes.decode(command(self.port,"V1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits))[2:-1])
        

        
        if position1 >= size and not self.b1_flag: # If @ end of line and not at end of pattern will move forwards to the next line 
            self.forward(steps)
            self.b2_flag = True
            self.b1_flag = True
           
        elif position1 <= 0 and not self.b1_flag: # If @ end of line and not at end of pattern will move forwards to the next line 
            self.forward(steps)
            self.b2_flag = False
            self.b1_flag = True
            
        elif not self.b2_flag: # If not finished moves along the line
            self.left(steps)
            self.b1_flag = False
            
        elif self.b2_flag: # If not finished moves along the line
            self.right(steps)
            self.b1_flag = False
            
        # Getting the position
        command(self.port, "B1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        position2 = int(bytes.decode(command(self.port,"V1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits))[2:-1])
        if position2 >= size:
            self.end = True

    def set_home(self):
        """
        DESCRIPTION:
            sets the current location of ythe stage to 0 in both directions
            
        PARAMETERS:
            None
        """
        command(self.port, "I3 \r"  , self.baud_rate, self.bit_size, self.parity, self.stop_bits)

    def go_home(self):
        """
        DESCRIPTION:
            moves the motor to 0 in both directions
            
        PARAMETERS:
            None
        """
        
        command(self.port, "B1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        command(self.port, "G+0 \r"  , self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        command(self.port, "B2 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        command(self.port, "G+0 \r"  , self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        
        return 

    def is_moving(self):
        """
        DESCRIPTION:
            check if the motor is moving
        
        PARAMETERS:
            None
        
        RETURNS:
            None
        """
        res = command(self.port, "F \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        return res

    def wait(self):
        """
        DESCRIPTION:
            Stops any code from running while the motor is still moving
            
        PARAMETERS:
            None
        
        RETURNS:
            None
        """        
        while self.is_moving() != b'Y\r':
            time.sleep(0.1)
            continue
        
    def position(self, x,y):
        """
        DESCRIPTION:
            will take the motor to the spesified position, with reference to (0,0) 
            
        PARAMETERS:
            x - motor 2 /right/left position of the motor relative to the calibrated 0, 
            y - motor 1 /forward/backwards position of the motor relative to the calibrated 0 

        RETURNS:
            None
        """
        x_com = "G" + str(x) +" \r"
        y_com = "G" + str(y) +" \r"
        
        command(self.port, "B2 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        command(self.port, x_com  , self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        command(self.port, "B1 \r", self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        command(self.port, y_com  , self.baud_rate, self.bit_size, self.parity, self.stop_bits)
        self.wait()
        
        return 

