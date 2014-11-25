Autoaim Indicator
======

Autoaim Indicator Mod for [World of Tanks](http://worldoftanks.eu/) shows a yellow "AUTO" near the center of the screen while in autoaim mode.
The Configuration is done via provided json file.

![Screenshot](http://cdn-frm-eu.wargaming.net/wot/eu/uploads/monthly_10_2014/post-506947255-0-02175200-1414274138.jpg)

Support for this mod is available at the official [World of Tanks Forum](http://forum.worldoftanks.eu/index.php?/topic/441413-)

Download & Install
------
Download latest compiled version [here](https://drive.google.com/folderview?id=0B8Pbr6Jr1eaCRE5vNkZwRXl1bkk&usp=sharing#list) and drop its files (assuming you got other mods already) into
```
\res_mods\x.x.x\scripts\client\mods
```

Configuration
------
Edit the file autoaim_indicator.json to suit your needs

* Instead of "AUTO" the name of the vehicle can be displayed
* Ability to snap to nearest vehicle while autoaiming (When you autoaim without any target highlighted - the nearest vehicle to aiming circle is being found)
* Ability to define a toggle key code to (permanently) turn the mod on/off with it (You need to press and hold the key during the battle, off by default as it could bring some performance penalty. A list of key codes can be found [here](http://dev.modxvm.com/xvm/raw/f8ce452d02dadabdd6b5a0a47fb5f110842f9582/release/configs/default/hotkeys.xc)

Available Fonts:
```
default_medium.font (HGSoeiKakugothicUB 20)
default_small.font (HGSoeiKakugothicUB 15)
default_smaller.font (HGSoeiKakugothicUB 12)
hpmp_panel.font (Arial 12)
system_large.font (Courier_New 15)
system_medium.font (Courier_New 13)
system_small.font (Courier_New 11)
system_tiny.font (Courier_New 10)
verdana_medium.font (Verdana 20)
verdana_small.font (Verdana 15)
```

Credits
------
* GUI code based on [macrosoft/wothp](https://github.com/macrosoft/wothp/blob/master/src/totalhp.py)
