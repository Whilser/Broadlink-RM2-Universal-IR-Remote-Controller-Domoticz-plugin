#
#           Broadlink Universal IR Remote Controller (Broadlink RM) python Plugin for Domoticz
#           Version 0.1.3

#           Powered by lib python broadlink https://github.com/mjg59/python-broadlink
#

"""
<plugin key="BroadlinkRM" name="Broadlink Universal IR Remote Controller (RM2)" author="Whilser" version="0.1.3" wikilink="https://www.domoticz.com/wiki/BroadlinkIR" externallink="https://github.com/Whilser/Broadlink-RM2-Universal-IR-Remote-Controller-Domoticz-plugin">
    <description>
        <h2>Broadlink Universal IR Remote Controller</h2><br/>
        <h3>Configuration</h3>
        Enter the Mac Address of your Broadlink RM2 IR device (lowercase without colon). If you do not know the Mac Address, just leave Mac Address field defaulted 0, <br/>
        this will launch discover mode for your broadlink devices. Go to the log, it will display the found broadlink devices and the Mac Address you need.
        <h3> </h3>

    </description>
    <params>
        <param field="Mode1" label="Mac Address" width="200px" required="true" default="0"/>
        <param field="Mode2" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="True" />
            </options>
        </param>
    </params>
</plugin>
"""

import os
import sys
import time
import os.path
import json
import base64
import codecs

import Domoticz

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)

import broadlink

class BasePlugin:
    commandOptions =   {
        "LevelActions"  :"|||||" ,
        "LevelNames"    :"Off|Reset Level|Learn|Test|Save Level|Create" ,
        "LevelOffHidden":"true",
        "SelectorStyle" :"0"
    }

    iconName = 'BroadlinkRM'
    iconNameMini = 'BroadlinkRMmini'

    commandUnit = 1
    temperatureUnit = 0

    devicesCount = 1
    levelsCount = 0
    IRCodeCount = 0
    nextTimeSync = 0
    lastLearnedIRCode = ''
    connected = False

    data = {}
    IR_dict = {}

    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        Domoticz.Debug("onStart called")

        if Parameters['Mode2'] == 'Debug': Domoticz.Debugging(1)

        if Parameters['Mode1'] == '0':
            self.discover()
            return

        self.nextTimeSync = 0
        self.loadConfig()
        self.CreateDevices()

        if not self.connect(): return

        temperature = ir.check_temperature()
        if  temperature > 0:
            Domoticz.Debug('Temperature is {} degrees.'.format(temperature))
            self.temperatureUnit = 1

            if (self.iconName not in Images): Domoticz.Image(Filename='Broadlink-icons.zip').Create()
            iconID = Images[self.iconName].ID
        else:
            if (self.iconNameMini not in Images): Domoticz.Image(Filename='Broadlink-mini-icons.zip').Create()
            iconID = Images[self.iconNameMini].ID

        if self.commandUnit not in Devices:
            Domoticz.Device(Name="Command",  Unit=self.commandUnit, TypeName="Selector Switch", Switchtype=18, Image=iconID, Options=self.commandOptions, Used=1).Create()

        if (self.temperatureUnit == 1) and (self.commandUnit+self.temperatureUnit not in Devices):
            Domoticz.Device(Name="Temperature",  Unit=2, TypeName="Temperature", Used=1).Create()

        if (temperature > 0) and (self.temperatureUnit == 1): Devices[2].Update(nValue=0, sValue=str(temperature), TimedOut = False)

        DumpConfigToLog()
        Domoticz.Heartbeat(20)

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        if not self.connect(): return

        if Unit == self.commandUnit:
            Domoticz.Debug('Handle Command Unit Commands')
            self.HandleCommandUnitCommands(Level)
            return

        Domoticz.Debug('Handle IR Commands')
        levelsList = self.data.get('Unit {0}'.format(Unit))

        if levelsList is None:
            Domoticz.Error('No config file was found for Unit {0} Remove Unit {0} from selectors.'.format(Unit))
            return

        Domoticz.Debug('Count levels: {0}'.format(len(levelsList)))

        for levels in levelsList:
            Domoticz.Debug('Record numbers {0}'.format(len(levels)))

            if Command == 'On' and levels.get('Level') == 10:
                IR_dict = dict(levels.get('LearnedCodes'))
                self.sendIRCommands(IR_dict)
                Devices[Unit].Update(nValue=1, sValue='On', TimedOut = False)

            elif Command == 'Off' and levels.get('Level') == 20:
                IR_dict = dict(levels.get('LearnedCodes'))
                self.sendIRCommands(IR_dict)
                Devices[Unit].Update(nValue=0, sValue='Off', TimedOut = False)

            elif Level == levels.get('Level'):
                IR_dict = dict(levels.get('LearnedCodes'))
                self.sendIRCommands(IR_dict)
                Devices[Unit].Update(nValue=1, sValue=str(Level), TimedOut = False)

        self.lastLearnedIRCode = ''
        self.IRCodeCount = 0
        self.IR_dict.clear()

    def HandleCommandUnitCommands(self, Level):
        if self.commandUnit not in Devices:
            Domoticz.Error('Command device is required! Restart plugin to create one.')
            return

        # Reset Level
        if Level == 10:
            self.lastLearnedIRCode = ''
            self.IRCodeCount = 0
            self.IR_dict.clear()
            Domoticz.Log('levels reset')
            Devices[self.commandUnit].Update(nValue=1, sValue=str(Level), TimedOut = False)

        # Learn Code
        if Level == 20:
            self.lastLearnedIRCode = self.learnIRCode()
            Domoticz.Debug('Learned Code: '+ str(self.lastLearnedIRCode))
            self.IRCodeCount += 1
            self.IR_dict['IRCode'+str(self.IRCodeCount)] = self.lastLearnedIRCode
            Domoticz.Log('Code Learned')
            Devices[self.commandUnit].Update(nValue=1, sValue=str(Level), TimedOut = False)

        # Test IR Commands
        if Level == 30:
            if len(self.lastLearnedIRCode) == 0:
                Domoticz.Error('No IR command received, nothing to test!')
                return

            self.sendIRCommands(self.IR_dict)
            Domoticz.Log('IR Commands sent')
            Devices[self.commandUnit].Update(nValue=1, sValue=str(Level), TimedOut = False)

        # Save command
        if Level == 40:
            if len(self.lastLearnedIRCode) == 0:
                Domoticz.Error('No IR command received, nothing to save!')
                return

            devicesCount = self.devicesCount + self.commandUnit + self.temperatureUnit
            self.levelsCount += 10
            if self.levelsCount == 10: self.data['Unit '+str(devicesCount)] = []
            self.data['Unit '+str(devicesCount)].append({
                'Level': self.levelsCount,
                'LearnedCodes': self.IR_dict.copy()
                })

            self.IR_dict.clear()
            self.lastLearnedIRCode = ''
            self.IRCodeCount = 0
            Domoticz.Log('levels saved')
            Devices[self.commandUnit].Update(nValue=1, sValue=str(Level), TimedOut = False)

        # Create device
        if Level == 50:
            if self.levelsCount == 0:
                Domoticz.Error('No IR Levels saved, nothing to create!')
                return

            self.devicesCount += 1

            self.dumpConfig()
            self.CreateDevices()
            self.levelsCount = 0

            Domoticz.Log('Device Created')
            Devices[self.commandUnit].Update(nValue=1, sValue=str(Level), TimedOut = False)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")

        if Parameters['Mode1'] == '0': return
        self.nextTimeSync -= 1

        if self.nextTimeSync <= 0:
            self.nextTimeSync = 15
            if not self.connect(): return

            try:
                temperature = ir.check_temperature()
                if ((temperature > 0) and (temperature < 100) and (self.commandUnit+self.temperatureUnit in Devices)): Devices[2].Update(nValue=0, sValue=str(temperature), TimedOut = False)
                Domoticz.Debug('The temperature now is {} degrees.'.format(temperature))

            except Exception as e:
                Domoticz.Error('Error getting temperature for {0}, check power/network connection. Error: {1}'.format(Parameters['Name'], e.__class__))
                self.connected = False
                self.nextTimeSync = 0

                for x in Devices:
                    if Devices[x].TimedOut == False: Devices[x].Update(nValue=Devices[x].nValue, sValue=Devices[x].sValue, TimedOut = True)

                return

    def dumpConfig(self):
        json_Path = os.path.join(str(Parameters['HomeFolder']), 'Broadlink_ir'+str(Parameters["HardwareID"])+'.json')
        Domoticz.Debug('Save data to: '+json_Path)
        with open(json_Path, 'w') as outfile:
            if json.dump(self.data, outfile, indent=4, sort_keys=True): return True

    def loadConfig(self):
        json_Path = os.path.join(str(Parameters['HomeFolder']), 'Broadlink_ir'+str(Parameters["HardwareID"])+'.json')

        if os.path.isfile(json_Path):
            Domoticz.Debug('Loading data from '+json_Path)

            with open(json_Path) as json_file:
                self.data = json.load(json_file)

    def CreateDevices(self):
        self.devicesCount = len(self.data)+self.commandUnit
        Domoticz.Debug('Total broadlink devices: {0}'.format(self.devicesCount))

        for key in sorted(self.data):
            Domoticz.Debug('{0} was found'.format(key))

            levelsDict = self.data.get(key)
            Domoticz.Debug('Count levels: {0}'.format(len(levelsDict)))

            if int(key.strip('Unit ')) not in Devices:
                if len(levelsDict) == 1:
                    Domoticz.Device(Name=key, Unit=int(key.strip('Unit ')), Type=244, Switchtype=9, Subtype=73, Used=1).Create()
                    Domoticz.Debug('Device {0} was created.'.format(key))

                elif len(levelsDict) == 2:
                    Domoticz.Device(Name=key, Unit=int(key.strip('Unit ')), Type=244, Switchtype=0, Subtype=73, Used=1).Create()
                    Domoticz.Debug('Device {0} was created.'.format(key))

                else:
                    SelectorOptions =   {
                        "LevelActions"  :"|"*len(levelsDict),
                        "LevelNames"    :"Level|"*len(levelsDict)+"Level" ,
                        "LevelOffHidden":"true",
                        "SelectorStyle" :"0"
                    }

                    Domoticz.Device(Name=key,  Unit=int(key.strip('Unit ')), TypeName="Selector Switch", Switchtype=18, Image=12, Options=SelectorOptions, Used=1).Create()
                    Domoticz.Debug('Device {0} was created.'.format(key))

        DumpConfigToLog()

    def learnIRCode(self):
        Domoticz.Debug('Learn command called')
        if not self.connect(): return

        learnedCode = ''
        timeout = 30

        try:
            ir.enter_learning()
            while (len(learnedCode)==0) and (timeout > 0):
                time.sleep(1)
                timeout -= 1
                ir_packet = ir.check_data()

                if ir_packet is not None: learnedCode = (codecs.encode(ir_packet, 'hex_codec')).decode('utf-8')

        except Exception as e:
            Domoticz.Error('{0} is not responding, check power/network connection. Error: {1}'.format(Parameters['Name'], e.__class__))
            self.connected = False

            for x in Devices:
                if Devices[x].TimedOut == False: Devices[x].Update(nValue=Devices[x].nValue, sValue=Devices[x].sValue, TimedOut = True)

        if (len(learnedCode)==0): Domoticz.Error('No IR command received!')
        return learnedCode

    def sendIRCommands(self, IRCommands):
        if not self.connect(): return

        try:
            for key in sorted(IRCommands):
                Domoticz.Debug('IR Code: '+key)
                Domoticz.Debug(IRCommands.get(key))

                ir_packet = IRCommands.get(key)
                ir.send_data(bytes.fromhex(ir_packet))
                #time.sleep(0.100)
        except Exception as e:
            Domoticz.Error('{0} is not responding, check power/network connection. Error: {1}'.format(Parameters['Name'], e.__class__))
            self.connected = False

            for x in Devices:
                if Devices[x].TimedOut == False: Devices[x].Update(nValue=Devices[x].nValue, sValue=Devices[x].sValue, TimedOut = True)

    def discover(self):
        devices = broadlink.discover(timeout=10)
        Domoticz.Log('Found {0} Broadlink RM Universal IR Remote '.format(len(devices)))

        if str(len(devices)) == 0:
            Domoticz.Error('No broadlink devices was found. Check power/network and try again.')
            return False

        for device in devices:
            if device.auth():
                mac = ''.join(format(x, '02x') for x in device.mac)
                Domoticz.Log('Device type {0} have IP address = {1} Mac address = {2}'.format(device.type, device.host[0], mac))

            else:
                Domoticz.Error('Error authenticating with device : {}'.format(device.host[0]))
                return False

        return True

    def connect(self):
        if self.connected: return True
        global ir

        ir = None
        devices = broadlink.discover(timeout=8)

        if str(len(devices)) == 0:
            Domoticz.Error('No broadlink devices was found! Check power/network and try again.')
            return False

        for device in devices:
            if device.auth():
                mac = ''.join(format(x, '02x') for x in device.mac)
                if mac == Parameters['Mode1']:
                    ir = device
                    self.connected = True
            else:
                Domoticz.Log('Error authenticating with device : {}'.format(device.host[0]))
                self.connected = False

        if ir is None:
            Domoticz.Error('No Broadlink devices was found with MAC address = {0}. Check Network/MAC Address.'.format(Parameters['Mode1']))
            self.connected = False

            for x in Devices:
                if Devices[x].TimedOut == False: Devices[x].Update(nValue=Devices[x].nValue, sValue=Devices[x].sValue, TimedOut = True)

        else:
            mac = ''.join(format(x, '02x') for x in ir.mac)
            Domoticz.Log('Connected to Broadlink device type {0} with IP address = {1} and Mac address = {2}'.format(ir.type, ir.host[0], mac))

            for x in Devices:
                if Devices[x].TimedOut == True: Devices[x].Update(nValue=Devices[x].nValue, sValue=Devices[x].sValue, TimedOut = False)

        return self.connected

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
        Domoticz.Debug("Device TimedOut: " + str(Devices[x].TimedOut))
    return
