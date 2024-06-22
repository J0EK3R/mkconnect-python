__author__ = "J0EK3R"
__version__ = "0.1"

import sys
import logging
import asyncio

logger = logging.getLogger(__name__)

sys.path.append("Advertiser") 
from Advertiser.Advertiser import Advertiser

import subprocess
import time

class AdvertiserHCITool(Advertiser) :
    """
    baseclass
    """

    HCITool_path = '/usr/bin/hcitool'

    def __init__(self):
        """
        initializes the object and defines the fields
        """
        super().__init__()

        logger.debug("AdvertiserHCITool.__init__")

        self._isInitialized = False
        self._ad_task_Run = False
        self._ad_task = None
        self._ad_task_Lock = asyncio.Lock()
        self._advertisementTable = dict()

        return

    async def AdvertisementStop(self) -> None:
        """
        stop bluetooth advertising
        """
        logger.debug("AdvertiserHCITool.AdvertisementStop")

        self._ad_task_Run = False
        if(self._ad_task is not None):
            await self._ad_task
            self._ad_task = None
            self._isInitialized = False

        hcitool_args_0x08_0x000a = self.HCITool_path + ' -i hci0 cmd 0x08 0x000a 00'

        subprocess.run(hcitool_args_0x08_0x000a + ' &> /dev/null', shell=True, executable="/bin/bash")

        logger.debug(f"AdvertiserHCITool.AdvertisementStop: '{hcitool_args_0x08_0x000a}'")

        return

    async def AdvertisementDataSet(self, identifier: str, manufacturerId: bytes, rawdata: bytes) -> None:
        """
        Set Advertisement data
        """
        logger.debug("AdvertiserHCITool.AdvertisementDataSet")

        advertisementCommand = self.HCITool_path + ' -i hci0 cmd 0x08 0x0008 ' + self._CreateTelegramForHCITool(manufacturerId, rawdata)
        async with self._ad_task_Lock:
            self._advertisementTable[identifier] = advertisementCommand
    
        if(not self._ad_task_Run):
            self._ad_task = asyncio.create_task(self._publish())
            self._ad_task_Run = True

        logger.debug('AdvertiserHCITool.AdvertisementSet')

        return

    async def _publish(self) -> None:
        logger.debug('AdvertiserHCITool._publish')

        while(self._ad_task_Run):
            try:
                async with self._ad_task_Lock:
                    copy_of_advertisementTable = self._advertisementTable.copy()
                
                # We want to repeat each command 
                repetitionsPerSecond = 4
                # timeSlot = 1 second / repetitionsPerSecond / len(copy_of_advertisementTable)
                timeSlot = 1 / repetitionsPerSecond / max(1, len(copy_of_advertisementTable))

                for key, advertisementCommand in copy_of_advertisementTable.items():
                    # stopp publishing?
                    if(not self._ad_task_Run):
                        return

                    timeStart = time.time()    
                    subprocess.run(advertisementCommand + ' &> /dev/null', shell=True, executable="/bin/bash")

                    if(not self._isInitialized):
                        hcitool_args_0x08_0x0006 = self.HCITool_path + ' -i hci0 cmd 0x08 0x0006 A0 00 A0 00 03 00 00 00 00 00 00 00 00 07 00'
                        hcitool_args_0x08_0x000a = self.HCITool_path + ' -i hci0 cmd 0x08 0x000a 01'

                        subprocess.run(hcitool_args_0x08_0x0006 + ' &> /dev/null', shell=True, executable="/bin/bash")
                        subprocess.run(hcitool_args_0x08_0x000a + ' &> /dev/null', shell=True, executable="/bin/bash")

                        logger.debug(str(hcitool_args_0x08_0x0006))
                        logger.debug(str(hcitool_args_0x08_0x000a))
                        
                        self._isInitialized = True

                    timeEnd = time.time()    
                    timeDelta = timeEnd - timeStart
                    timeSlotRemain = max(0.001, timeSlot - timeDelta)

                    #     logger.debug(str(timeSlotRemain) + " " + str(key) + ": " + str(advertisement))
                    #     logger.debug(str(timeSlotRemain))

                    await asyncio.sleep(timeSlotRemain)
            except:
                pass

    def _CreateTelegramForHCITool(self, manufacturerId: bytes, rawDataArray: bytes) -> str:
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
