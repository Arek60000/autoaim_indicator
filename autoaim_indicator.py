"""
AutoAim indicator
by Krzysztof_Chodak
"""
import BigWorld, ResMgr, GUI, json, os, time, VehicleGunRotator, Math, CommandMapping, math, inspect
from debug_utils import *
from gui.WindowsManager import g_windowsManager
from PlayerEvents import g_playerEvents
from constants import ARENA_PERIOD
from gui import g_guiResetters, g_repeatKeyHandlers, GUI_SETTINGS
from AvatarInputHandler.control_modes import ArcadeControlMode

config = None
old_autoAim = None
old_onAutoAimVehicleLost = None
indicator = None
playerVehicleID = None
myEventsAttached = False
toggleKey = 0
toggleStateOn = True
enemies = {}
player = None
playerVehicle = None
autoAimVehicle = None

print '2014-11-25'

def MYLOGLIVE(message, permanent_log = True, make_red = True):
    from messenger import MessengerEntry
    if message=="":
        return
    if permanent_log:
        LOG_NOTE(message)
    if make_red:
        message = '<font color="#FF0000">' + message + '</font>'
    MessengerEntry.g_instance.gui.addClientMessage(message)

def MYLOG(message, *args):
    LOG_NOTE(message, *args)

def PT2STR(obj):
    return "x=%f, y=%f, z=%f" % (obj.x, obj.y, obj.z)

def MYPPRINT(obj, name = None):
    import inspect, pprint
    if isinstance(obj, dict) or isinstance(obj, list):
        pprint.pprint(obj)
    elif isinstance(obj, Math.Vector3):
        if name is None:
            print PT2STR(obj)
        else:
            print "%s: %s" % (name, PT2STR(obj))
    elif hasattr(obj, '__call__'):
        pprint.pprint(inspect.getargspec(obj))
    else:
        pprint.pprint(inspect.getmembers(obj))

def myPe_onArenaPeriodChange(period = ARENA_PERIOD.BATTLE, *args):
    global config
    global old_autoAim
    global old_onAutoAimVehicleLost
    global indicator
    global playerVehicleID
    global myEventsAttached
    global player
    if period is ARENA_PERIOD.BATTLE:
        if g_windowsManager.battleWindow is None:
            BigWorld.callback(1, myPe_onArenaPeriodChange)
            return
        player = BigWorld.player()
        arena = player.arena
        vehicles = arena.vehicles
        if player.isVehicleAlive:
            playerVehicleID = player.playerVehicleID
            if 'SPG' not in vehicles[playerVehicleID]['vehicleType'].type.tags:
                for vehicleID, desc in vehicles.items():
                    if player.team is not desc['team'] and desc['isAlive'] == True:
                        enemies[vehicleID] = True

                if indicator is None:
                    indicator = TextLabel(config.get('autoaim_indicator_panel', {}))
                    onChangeScreenResolution()
                    new_autoAim(None, True)
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
    global playerVehicle
    global autoAimVehicle
    playerVehicleID = None
    if myEventsAttached:
        player.autoAim = old_autoAim
        old_autoAim = None
        player.onAutoAimVehicleLost = old_onAutoAimVehicleLost
        old_onAutoAimVehicleLost = None
        player.arena.onVehicleKilled -= myOnVehicleKilled
        myEventsAttached = False
    if not indicator is None:
        GUI.delRoot(indicator.window)
        indicator = None
    enemies.clear()
    playerVehicle = None
    if not autoAimVehicle is None:
        removeOutline(autoAimVehicle)
        autoAimVehicle = None
    
def new_autoAim(target, init = False):
    global playerVehicle
    global counter
    global autoAimVehicle
    prevAutoAimVehicleID = 0
    if init:
        playerVehicle = BigWorld.entity(playerVehicleID)
    else:
        prevAutoAimVehicleID = player._PlayerAvatar__autoAimVehID
        old_autoAim(target)
    if prevAutoAimVehicleID != 0:
        removeOutline(autoAimVehicle)
    autoAimVehicleID = player._PlayerAvatar__autoAimVehID
    enabled = autoAimVehicleID != 0
    if enabled:
        autoAimVehicle = BigWorld.entity(autoAimVehicleID)
        if config.get("use_target_as_text", True):
            indicator.setText(autoAimVehicle.typeDescriptor.type.shortUserString[0:config.get("max_characters", 15)-1])
    else:
        autoAimVehicle = None
    indicator.setVisible(enabled)
    if not init and prevAutoAimVehicleID == 0 and not enabled and config.get("snap_to_nearest", False):
        try:
            callers_frame = inspect.getouterframes(inspect.currentframe())[1]
            if callers_frame[3] == "handleKeyEvent":
                callers_locals = inspect.getargvalues(callers_frame[0]).locals
                if callers_locals["cmdMap"].isFired(CommandMapping.CMD_CM_LOCK_TARGET_OFF, callers_locals["key"]) and callers_locals["isDown"]:
                    #MYLOG("disable autoaim used")
                    return
        except:        
            pass
        if isinstance(player.inputHandler.ctrl, ArcadeControlMode):
            desiredShotPoint = player.inputHandler.ctrl.camera.aimingSystem.getThirdPersonShotPoint()
        else:
            desiredShotPoint = player.inputHandler.getDesiredShotPoint()
            if desiredShotPoint is None:
                MYLOG("No desiredShotPoint available - trying alternative")
                desiredShotPoint = player.gunRotator.markerInfo[0]
        if desiredShotPoint is None:
            MYLOG('No desiredShotPoint available')
        else:
            new_target = None
            distance_to_target = math.radians(config.get("snapping_angle_degrees", 7.5))
            vehicles = player.arena.vehicles
            v1norm = normalize(desiredShotPoint - playerVehicle.position)
            for vehicleID in enemies:
                vehicle = BigWorld.entity(vehicleID)
                if vehicle is not None and vehicle.isAlive():
                    v2norm = normalize(vehicle.position - playerVehicle.position)
                    distance = math.acos(v1norm.x * v2norm.x + v1norm.y * v2norm.y + v1norm.z * v2norm.z)
                    if distance < 0:
                        distance = -distance
                    if distance > math.pi:
                        distance = 2 * math.pi - distance
                    if distance < distance_to_target:
                        new_target = vehicle
                        distance_to_target = distance

            if new_target is not None:
                new_autoAim(new_target)
    if enabled:
        addOutline(autoAimVehicle)
        counter = 0

def normalize(v):
    return v / math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)

def new_onAutoAimVehicleLost():
    global autoAimVehicle
    removeOutline(autoAimVehicle)
    autoAimVehicle = None
    old_onAutoAimVehicleLost()
    indicator.setVisible(False)

def addOutline(vehicle):
    #if config.get("outline_target", True):
        #BigWorld.wgAddEdgeDetectEntity(autoAimVehicle, 1)
    pass

def removeOutline(vehicle):
    if not config.get("outline_target", True):
        return
    #target = BigWorld.target()
    #if not(target is not None and isinstance(target, Vehicle.Vehicle) and target.id == vehicle.id):
    #BigWorld.wgDelEdgeDetectEntity(vehicle)
    
def myOnVehicleKilled(vehicleID, *args):
    global autoAimVehicle
    if vehicleID == playerVehicleID:
        cleanUp()
    else:
        if autoAimVehicle and vehicleID == autoAimVehicle.id:
            autoAimVehicle = None
    
# borrowed from https://github.com/macrosoft/wothp/blob/master/src/totalhp.py
class TextLabel(object):
    label = None
    shadow = None
    window = None
    color = '\\cFFFFFFFF;'
    visible = True
    x = 0
    y = 0
    hcentered = False
    vcentered = False
    mainCaliberValue = 0

    def __init__(self, config):
        if config.get('color', False):
            self.color = '\\c' + config.get('color')[1:] + 'FF;'
        self.visible = config.get('visible', True)
        self.x = config.get('x', 0)
        self.y = config.get('y', 0)
        self.hcentered = config.get('hcentered', False)
        self.vcentered = config.get('vcentered', False)
        background = os.path.join('scripts', 'client', 'mods', config.get('background')) if config.get('background', '') else ''
        self.window = GUI.Window(background)
        self.window.materialFX = 'BLEND'
        self.window.verticalAnchor = 'TOP'
        self.window.horizontalAnchor = 'LEFT'
        self.window.horizontalPositionMode = 'PIXEL'
        self.window.verticalPositionMode = 'PIXEL'
        self.window.heightMode = 'PIXEL'
        self.window.widthMode = 'PIXEL'
        self.window.width = config.get('width', 186)
        self.window.height = config.get('height', 32)
        self.autoSize = True
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
        item.verticalAnchor = 'CENTER'
        item.horizontalAnchor = 'CENTER'
        item.horizontalPositionMode = 'PIXEL'
        item.verticalPositionMode = 'PIXEL'
        item.position = (self.window.width / 2, self.window.height / 2, 1)
        item.colourFormatting = True

    def setVisible(self, flag):
        flag = flag and self.visible
        self.window.visible = flag
        self.shadow.visible = flag
        self.label.visible = flag

    def setText(self, text, color = None):
        shadowText = text.replace('\\c60FF00FF;', '')
        self.shadow.text = '\\c000000FF;' + shadowText
        color = '\\c' + color + 'FF;' if color else self.color
        self.label.text = color + text


def onChangeScreenResolution():
    sr = GUI.screenResolution()
    for panel in [indicator]:
        if panel is None:
            continue
        x = sr[0] / 2 - panel.window.width / 2 + panel.x if panel.hcentered else panel.x
        y = sr[1] / 2 - panel.window.height / 2 + panel.y if panel.vcentered else panel.y
        panel.window.position = (x, y, 1)

    return


def myHandleRepeatKeyEvent(event):
    global toggleStateOn
    if GUI_SETTINGS.minimapSize:
        if event.key == toggleKey and event.repeatCount == 1:
            if toggleStateOn:
                toggleStateOn = False
                g_playerEvents.onArenaPeriodChange -= myPe_onArenaPeriodChange
                cleanUp()
                MYLOGLIVE(config.get('toggledOffMsg', ''), make_red=False)
            else:
                toggleStateOn = True
                g_playerEvents.onArenaPeriodChange += myPe_onArenaPeriodChange
                if g_windowsManager.battleWindow is not None:
                    myPe_onArenaPeriodChange()
                MYLOGLIVE(config.get('toggledOnMsg', ''), make_red=False)
            config['toggleStateOn'] = toggleStateOn
            with open(conf_file, 'w') as data_file:
                try:
                    json.dump(config, data_file, sort_keys=True, indent=4, separators=(',', ': '))
                except:
                    print 'Error while saving %s: %s' % (conf_file, sys.exc_info()[0])

    return


conf_file = None
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
                    import sys
                    print 'Error while loading %s: %s' % (conf_file, sys.exc_info()[0])
                finally:
                    break

if config:
    toggleKey = config['toggleKeyCode']
    if toggleKey > 0:
        g_repeatKeyHandlers.add(myHandleRepeatKeyEvent)
        toggleStateOn = config['toggleStateOn']
    if toggleStateOn:
        g_playerEvents.onArenaPeriodChange += myPe_onArenaPeriodChange
        g_guiResetters.add(onChangeScreenResolution)

def myOnAvatarBecomeNonPlayer(*args):
    cleanUp()
    
g_playerEvents.onAvatarBecomeNonPlayer += myOnAvatarBecomeNonPlayer