"""
AutoAim indicator
by Krzysztof_Chodak
"""
from debug_utils import *
from PlayerEvents import g_playerEvents
from constants import ARENA_PERIOD
from gui.WindowsManager import g_windowsManager
import BigWorld
import ResMgr
import json
import os
import GUI
from gui import g_guiResetters

config = None
old_autoAim = None
old_onAutoAimVehicleLost = None
indicator = None
playerVehicleID = None
myEventsAttached = False

def MYLOGLIVE(message):
    from messenger import MessengerEntry
    MessengerEntry.g_instance.gui.addClientMessage('<font color="#FF0000">' + message + '</font>')
    LOG_NOTE(message)

def MYLOG(message, *args):
    LOG_NOTE(message, *args)

def myPe_onArenaPeriodChange(period = ARENA_PERIOD.BATTLE, *args):
    global config
    global old_autoAim
    global old_onAutoAimVehicleLost
    global indicator
    global playerVehicleID
    global myEventsAttached
    if period is ARENA_PERIOD.BATTLE:
        #MYLOG('in a battle')
        if g_windowsManager.battleWindow is None:
            #MYLOG('no battleWindow yet, retrying in a sec')
            BigWorld.callback(1, myPe_onArenaPeriodChange)
            return
        player = BigWorld.player()
        arena = player.arena
        vehicles = arena.vehicles
        if player.isVehicleAlive:
            playerVehicleID = player.playerVehicleID
            if not 'SPG' in vehicles[playerVehicleID]['vehicleType'].type.tags:
                if indicator is None:
                    indicator = TextLabel(config.get('autoaim_indicator_panel', {}))
                    onChangeScreenResolution()
                    new_autoAim(None, True)
                    #MYLOG('indicator prepared')
                if not myEventsAttached:
                    old_autoAim = player.autoAim
                    player.autoAim = new_autoAim
                    old_onAutoAimVehicleLost = player.onAutoAimVehicleLost
                    player.onAutoAimVehicleLost = new_onAutoAimVehicleLost
                    arena.onVehicleKilled += myOnVehicleKilled
                    myEventsAttached = True
            else:
                cleanUp()
        else:
            cleanUp()
    elif period is ARENA_PERIOD.AFTERBATTLE:
        cleanUp()

def cleanUp():
    global old_autoAim
    global old_onAutoAimVehicleLost
    global indicator
    global playerVehicleID
    global myEventsAttached
    playerVehicleID = None
    if myEventsAttached:
        player = BigWorld.player()
        player.autoAim = old_autoAim
        old_autoAim = None
        player.onAutoAimVehicleLost = old_onAutoAimVehicleLost
        old_onAutoAimVehicleLost = None
        player.arena.onVehicleKilled -= myOnVehicleKilled
        myEventsAttached = False
    if not indicator is None:
        GUI.delRoot(indicator.window)
        indicator = None                
    
def new_autoAim(target, init = False):
    prevAutoAimVehicle = None
    if not init:
        prevAutoAimVehicle = BigWorld.player().autoAimVehicle
        old_autoAim(target)
    autoAimVehicle = BigWorld.player().autoAimVehicle
    enabled = not autoAimVehicle is None
    #MYLOGLIVE("autoAimVehicle = %s" % (not autoAimVehicle is None))
    if enabled and config.get("use_target_as_text", False):
        indicator.setText(autoAimVehicle.typeDescriptor.type.userString)
    indicator.setVisible(enabled)
    if not init and prevAutoAimVehicle is None and not enabled and config.get("snap_to_nearest", False):
        player = BigWorld.player()
        source = player.inputHandler.getDesiredShotPoint()
        new_target = None
        distance_to_target = 10000
        vehicles = player.arena.vehicles
        for vehicleID, desc in vehicles.items():
            if player.team is not vehicles[vehicleID]['team'] and desc['isAlive'] == True:
                entity = BigWorld.entity(vehicleID)
                if not entity is None:
                    vehicle = BigWorld.entities[vehicleID]
                    distance = source.flatDistTo(vehicle.position)
                    if distance < distance_to_target:
                        new_target = vehicle
                        distance_to_target = distance
        if not new_target is None:
            new_autoAim(new_target)

def new_onAutoAimVehicleLost():
    old_onAutoAimVehicleLost()
    indicator.setVisible(False)

def myOnVehicleKilled(vehicleID, *args):
    global playerVehicleID
    global indicator
    #MYLOGLIVE('myOnVehicleKilled (%s, own %s)' % (vehicleID, playerVehicleID))
    if vehicleID == playerVehicleID:
        playerVehicleID = None
        #MYLOGLIVE("Oh no! We've got killed :(")
        GUI.delRoot(indicator.window)
        indicator = None
    
# borrowed from https://github.com/macrosoft/wothp/blob/master/src/totalhp.py
class TextLabel(object):
    label = None
    shadow = None
    window = None
    color = '\cFFFFFFFF;'
    visible = True
    x = 0
    y = 0
    hcentered = False
    vcentered = False
    mainCaliberValue = 0

    def __init__(self, config):
        if config.get('color', False):
            self.color = '\c' + config.get('color')[1:] + 'FF;'
        self.visible = config.get('visible', True)
        self.x  = config.get('x', 0)
        self.y  = config.get('y', 0)
        self.hcentered  = config.get('hcentered', False)
        self.vcentered  = config.get('vcentered', False)
        background = os.path.join('scripts', 'client', 'mods', config.get('background')) \
            if config.get('background', '') else ''
        self.window = GUI.Window(background)
        self.window.materialFX = "BLEND"
        self.window.verticalAnchor = "TOP"
        self.window.horizontalAnchor = "LEFT"
        self.window.horizontalPositionMode = 'PIXEL'
        self.window.verticalPositionMode = 'PIXEL'
        self.window.heightMode = 'PIXEL'
        self.window.widthMode = 'PIXEL'
        self.window.width = config.get('width', 186)
        self.window.height = config.get('height', 32)
        GUI.addRoot(self.window)
        self.shadow = GUI.Text('')
        font = config.get('font', 'default_medium.font')
        self.installItem(self.shadow, font)
        self.label = GUI.Text('')
        self.installItem(self.label, font)
        self.setText(config.get('text', ''))
        self.setVisible(self.visible)

    def installItem(self, item, font):
        item.font = font
        self.window.addChild(item)
        item.verticalAnchor = "TOP"
        item.horizontalAnchor = "CENTER"
        item.horizontalPositionMode = 'PIXEL'
        item.verticalPositionMode = 'PIXEL'
        item.position = (self.window.width/2, 0, 1)
        item.colourFormatting = True

    def setVisible(self, flag):
        flag = flag and self.visible
        self.window.visible = flag
        self.shadow.visible = flag
        self.label.visible = flag

    def setText(self, text, color = None):
        shadowText = text.replace('\c60FF00FF;','')
        self.shadow.text = '\c000000FF;' + shadowText
        color = '\c' + color + 'FF;' if color else self.color
        self.label.text = color + text

def onChangeScreenResolution():
    sr = GUI.screenResolution()
    for panel in [indicator]:
        if panel is None:
            continue
        x = sr[0]/2 - panel.window.width /2 + panel.x if panel.hcentered else panel.x
        y = sr[1]/2 - panel.window.height/2 + panel.y if panel.vcentered else panel.y
        panel.window.position = (x, y, 1)

res = ResMgr.openSection('../paths.xml')
sb = res['Paths']
vals = sb.values()[0:2]
for vl in vals:
    path = vl.asString + '/scripts/client/mods/'
    if os.path.isdir(path):
        conf_file = path + 'autoaim_indicator.json'
        if os.path.isfile(conf_file):
            with open(conf_file) as data_file:
                try:
                    config = json.load(data_file)
                except:
                    print "Error while loading autoaim_indicator.json: %s" % sys.exc_info()[0]
                finally:
                    break

if config:
    g_playerEvents.onArenaPeriodChange += myPe_onArenaPeriodChange
    g_guiResetters.add(onChangeScreenResolution)
