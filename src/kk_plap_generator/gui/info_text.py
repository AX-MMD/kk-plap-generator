README = """
### INTRO #####################################################################
___
Author: AX-MMD
Docs: https://github.com/AX-MMD/kk-plap-generator/tree/main?tab=readme-ov-file#intro

PLAP generator uses a Timeline interpolable as reference to generate a sequence to use with sound components. It is meant to sync with a simple movement like forward-backward, up-down, etc.

The process is as follows:
- Export the Timeline Single File of your reference
- Configure PLAP generator
- Generate your PLAP files
- Setup your scene (import `/resources/Plap1234.png` or make your own sound components)
- Import the generated PLAP files to Timeline

### EXPORT TIMELINE SINGLE FILE ###############################################
___
> In CharaStudio
* Choose an interpolable like "GO Pos Waist", Hips, Dick, etc. Rotation is fine too.
* Rename it with an alias, can also just Rename -> ctrl+X -> ctrl+V.
* Make sure the owner of that interpolable is selected (green) in your Workspace.
* Timeline -> Single Files -> Save.

> In PLAP generator
* Drop the exported file into the file drop zone or use the `Select File` button.

### CONFIGURATION #############################################################
___
There are only two required info for a default generation of a sequence: The name of the interpolable (or Path if part of a group) and the Time of a reference keyframe.

> In CharaStudio
* Choose a keyframe where the interpolable is fully extended:
  -- Dick pushed in the female.
  -- Female pushed on dick (if she's the one moving).
  -- It can be whatever is the apex/movement of your interpolable.
* Copy the exact Time of that interpolable.
* Copy the exact Name of that interpolable.

> In PLAP generator
* The generator needs the Path and Time of the interpolable to use as reference.

    Exemple:

    Your interpolable "Pos Waist" is part of a group(s), and the reference keyframe is at 00:02.454
     __________
    |  Main    |
    ------------
    |   male   |      "00:02.454"
    ------------      ⇓
     |Pos Waist|    ◆◆◆ ◆◆◆ ◆◆◆       ◆◆ ◆◆ ◆◆◆◆◆◆
      ---------

    Path = Pos Waist
    Time = 00:02.454

If the generator has trouble finding the reference keyframe try giving the full path, Main.male.Pos Waist for this exemple. You can check the TROUBLESHOOTING section for more help.

[-- Advanced use case ------------------------------------------------------]

You can click the ` ℹ ` icons for a full explanation of the parameters available to customize or apply corrections to your sound sequence:

* Use multiple reference interpolable.
* A time range other then 00:00.0 -> End Of Scene.
* A different sound pattern.
* A different number of sound components and custom names.
* Add a `cutoff` to `Sound Components` if you want to use a "loop" sound item.
* Offset the timing of the sound compared to the reference.
* Adjust the margin of error accepted to register a sound.

[---------------------------------------------------------------------------]

### GENERATE THE PLAP FILES ###################################################
___
Once your have exported your Single File and configured the generator, press the `▶` Play button. The program will generate a file for each name in `Sound Components`. They will be created to whatever location your exported Single File was in.

The output should be something like this:

    Generating plap for (Plap2 Plap1 Plap3 Plap4)
    Using pattern 'V'
    Plap1:: Generated 39 keyframes from time 5.95 to 27.05
    Plap2:: Generated 39 keyframes from time 5.95 to 27.05
    Plap3:: Generated 39 keyframes from time 5.95 to 27.05
    Plap4:: Generated 39 keyframes from time 5.95 to 27.05
    ================================================================

See TROUBLESHOOTING below if you have an issue.

### SETUP YOUR SCENE ##########################################################
___
> In CharaStudio

With the Plap.xml files generated, it's time to add SFX components to your scene. You can just import `/resources/Plap1234.png` that is included with this install and skip to the next phase: IMPORT TO TIMELINE.

* Add a sound item or create a folder containing sound items for each name you defined for `Sound Components`, doesn't need to be the same names.

* Each sound component is activated in sequence, following the sound pattern.

### IMPORT TO TIMELINE ########################################################
___
> In CharaStudio

(If you already have interpolables in Timeline for your sound components, delete them)

For each of your sound components in your workspace:
* Click the folder to highlight it.
* In Timeline -> Single Files, load the corresponding name.

And voilà, a simple sequence of sound keyframes is added to your scene.

### LIMITATIONS ###############################################################
___
The reference can be lost if the subject of that interpolable:
 * (A) Increase/decrease his movement by a lot.
 * (B) Moves away from his point of origin.

 Case (A) can usually be corrected in CONFIGURATION.
 Case (B) is not yet supported with the app, only with TERMINAL.

### TROUBLESHOOTING ###########################################################
___

Could not find the reference keyframe at ...
* Make sure you gave the correct time for the reference keyframe.

There are keyframes for only a part of the scene, then it stop :
* Most likely the subject moved from his position to much, you can try decreasing Min Pull Out and/or Min Push In.

There is a spam of sound keyframes at one point of the scene :
* This can happen when the subject makes micro in-out moves near the contact point, you can try increasing Min Pull Out and/or Min Push In.

Missing node: `<interpolableGroup name='xxx'>`
* The path you gave for the reference interpolable contains a parent group that is not recognized, make sure the path is correct.
* Modded CharaStudio auto-translates, look at your Timeline and press Alt+T to see the real names of the groups and interpolables.

Missing node: `<interpolable alias='xxx'>`
* An interpolable with the given name was not found. Make sure it is correct and that you renamed it in your scene before you exported it to Single File.
* Modded CharaStudio auto-translates, look at your Timeline and press Alt+T to see the real names of the groups and interpolables.

Could not find the ... file
* PLAP generator cannot access `/configs` and `/resources`, or `config.toml` and `template.xml` that is supposed to be in these folders. Re-install the program.

"""

CORRECTIONS = """
[---------------------------- Adjustments ---------------------------]

These settings are used for corrections. You can change them if the plaps are not synced with the reference, there is to much plaps, or not enough plaps.

::: Offset :::
A global offset in seconds for all Sound Components of the current page, in case you don't want the sfx to be timed exactly with the reference keyframes. Can be positive or negative.

::: Minimum Pull Out % :::
The generator estimates the distance traveled by the subject for each plap, here you can set what (%) of that distance the subject needs to pull away from the contact point before re-enabling plaps.

This is to prevents spam if the subject is making micro in-out moves when fully inserted.

::: Minimum Push In % :::
The generator estimates the distance traveled by the subject for each plap, here you can set what (%) of that distance the subject needs to push toward the contact point for a plap to register.

This is in case the contact point gets closer and the subject does not need to thrust as far.
"""

SOUND_FOLDERS = """
[--------------------------- Customization --------------------------]

::: Sound Components :::
Here you define your sound components preferably 1 per sound item or folder you setup in Charastudio.

Double-Click on the name to edit the parameters of the sound component.

:Name: The name of the sound component, this will the name of its corresponding plap file and interpolable in Timeline.
:Offset: A custom offset in seconds for this sound component, can be positive or negative.
:Cutoff: You can use this to define when the sound should stop playing, usefull if you want to use "loop" sound items.
"""

SOUND_PATTERN = """
[-------------------------- Customization ---------------------------]

::: Sound Pattern :::
PLAP generator will create a sequence of keyframes for each of your sound components.
The sound pattern is what determines the order of activation of your folder.
For example if you have 4 components named Plap1-4 and your pattern is "W", the generated keyframes for Timeline will look like this:
_______
|Plap1|  ◆               ◆                 ◆
|Plap2|    ◆     ◆     ◆  ◆      ◆     ◆  ◆  and so on...
|Plap3|      ◆  ◆ ◆ ◆      ◆  ◆  ◆  ◆
|Plap4|        ◆    ◆         ◆      ◆
=======

You can combine multiple letters to create a more complex pattern.

"""

TIME_RANGES = """
[---------------------------- Adjustments ---------------------------]

::: Time Ranges :::
By default the generator will try to make keyframes starting from 00:00.00.
You can have a different start point, end point or multiple ranges.

Double-Click on the time range to edit the parameters.

For exemple, if you give the ranges 00:01.5, 00:05.0 and 00:10.5, 00:15.0 the generator will try to make keyframes only at those points.

! important !
If you give a custom range, you must put both a Start and Stop point.
"""
