__author__ = "J0EK3R"
__version__ = "0.1"

# import hack for micro-python-simulator with flat filesystem
try:
    from Advertiser.AdvertiserBase import AdvertiserBase
except ImportError:
    from Advertiser import AdvertiserBase

import subprocess
import platform

class AdvertiserHCITool(AdvertiserBase) :
    """
    baseclass
    """

    def __init__(self):
        """
        initializes the object and defines the fields
        """

        super().__init__()
        self._hcitool_path = '/usr/bin/hcitool'


    def AdvertismentStop(self):
        """
        stop bluetooth advertising
        """
        hcitool_args1 = self._hcitool_path + ' -i hci0 cmd 0x08 0x000a 00' + ' &> /dev/null'

        if platform.system() == 'Linux':
            subprocess.run(hcitool_args1, shell=True, executable="/bin/bash")
        elif platform.system() == 'Windows':
            print('Connect command :')
            print(hcitool_args1)
        else:
            print('Unsupported OS')

        return

    def AdvertismentStart(self, manufacturerId: bytes, rawdata: bytes, debug: bool=False):
        """
        send the bluetooth connect telegram to switch the MouldKing hubs in bluetooth mode
        press the button on the hub(s) and the flashing of status led should switch from blue-green to blue
        """
        hcitool_args1 = self._hcitool_path + ' -i hci0 cmd 0x08 0x0008 ' + self._CreateTelegramForHCITool(manufacturerId, rawdata)
        hcitool_args2 = self._hcitool_path + ' -i hci0 cmd 0x08 0x0006 A0 00 A0 00 03 00 00 00 00 00 00 00 00 07 00'
        hcitool_args3 = self._hcitool_path + ' -i hci0 cmd 0x08 0x000a 01'

        if platform.system() == 'Linux':
            subprocess.run(hcitool_args1 + ' &> /dev/null', shell=True, executable="/bin/bash")
            subprocess.run(hcitool_args2 + ' &> /dev/null', shell=True, executable="/bin/bash")
            subprocess.run(hcitool_args3 + ' &> /dev/null', shell=True, executable="/bin/bash")
        else:
            print('Unsupported OS or debug mode, this is the command(s) that should be run :')

        if (debug or platform.system() != 'Linux'):
            print(str(hcitool_args1))
            print(str(hcitool_args2))
            print(str(hcitool_args3))

        return

    def AdvertismentSet(self, manufacturerId: bytes, rawdata: bytes, debug: bool=False):
        hcitool_args = self._hcitool_path + ' -i hci0 cmd 0x08 0x0008 ' + self._CreateTelegramForHCITool(manufacturerId, rawdata)

        if platform.system() == 'Linux':
            subprocess.run(hcitool_args + ' &> /dev/null', shell=True, executable="/bin/bash")
        else:
            print('Unsupported OS or debug mode, this is the command that should be run :')

        if (debug or platform.system() != 'Linux'):
            print(str(hcitool_args) + '\n')

        return

    def _CreateTelegramForHCITool(self, manufacturerId: bytes, rawDataArray: bytes):
        """
        Create input data for hcitool 
        """
        rawDataArrayLen = len(rawDataArray)
        
        resultArray = bytearray(8 + rawDataArrayLen)
        resultArray[0] = rawDataArrayLen + 7 # len
        resultArray[1] = 0x02                 # flags
        resultArray[2] = 0x01
        resultArray[3] = 0x02
        resultArray[4] = rawDataArrayLen + 3 # len
        resultArray[5] = 0xFF                # type manufacturer specific
        resultArray[6] = manufacturerId[1]   # companyId
        resultArray[7] = manufacturerId[0]   # companyId
        for index in range(rawDataArrayLen):
            resultArray[index + 8] = rawDataArray[index]

        return ' '.join(f'{x:02x}' for x in resultArray)
