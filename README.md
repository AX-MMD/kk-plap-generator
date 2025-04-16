### INSTALLATION ##############################################################
___
Unzip the archive wherever you like, but make sure `/configs`, `/resources`, and their content stays together.


### INTRO #####################################################################
___
Author: AX-MMD

Docs: https://github.com/AX-MMD/kk-plap-generator/tree/main?tab=readme-ov-file#intro

Demonstration: Check the Koikatsu discord

Koikatsu PLAP generator uses a Timeline interpolable as reference to generate keyframes for activable items and the Pregnancy+ plugin. It is meant to sync with a repetitive movement like forward-backward, up-down, etc.

The process is as follows:
- Export the Timeline Single File of your reference
- Configure PLAP generator
- Generate your PLAP files
- Add activable items to your scene (import `/resources/Plap1234.png` for an example with sound items)
- Import each generated PLAP files to each of your items in Timeline 

### EXPORT TIMELINE SINGLE FILE ###############################################
___
> In CharaStudio
* Choose an interpolable like "GO Pos Waist", Hips, Dick, sphere/folder, etc. Rotation is fine too.
* Rename it with an alias, can also just Rename -> ctrl+X -> ctrl+V.
* Timeline -> Single Files -> Save.

> In PLAP generator
* (Optional) Click `Load` and select "example.toml" to use a default config.
* Drop the exported file into the file drop zone or use the `Select File` button.

### CONFIGURATION #############################################################
___
The required info for generation is the Name/alias of the chosen reference interpolable and the Time of a reference keyframe for that interpolable.

> In CharaStudio
* Choose a keyframe where the interpolable is fully extended:
  -- Dick pushed in the female.
  -- Female pushed on dick (if she's the one moving).
  -- It can be whatever is the apex of your movement/interpolable.
* Copy the exact Name of that interpolable.
* Copy the exact Time of that keyframe.

NOTE: If the apex is in between 2 keyframes, always take the keyframe on the right.

> In PLAP generator
* The generator needs the Name and Start Time of the interpolable to use as reference.

    Example:
    
    Your interpolable "Pos Waist" is part of a group(s), and the reference keyframe is at 00:02.454
    ```
     __________
    |  Main    |
    ------------
    |   male   |      "00:02.454"
    ------------      ⇓
     |Pos Waist|    ◆◆◆ ◆◆◆ ◆◆◆       ◆◆ ◆◆ ◆◆◆◆◆◆
      ---------
    ```
    In "Reference Interpolable" tab: 
    * Path => Pos Waist
    
    In the "Time Ranges" tab:
    * Double click "00:00.0 - END" and change it to "<reference_time_here> - END" 


Once that is done, if you didn't load the example config we need to configure Components. The 2 main components are MultiActivableComponent (MAC, usually for Studio sound items) and PregPlusComponent (Preg+).

Let's say you have 4 sound items in your scene:
* In Components, click "+" to add a MAC component then add MAC-Items until you have 4 (the amount of sound items).
* Adjust the offsets as needed to account for sound delays of the items.
* Make sure you don't have multiple components with the same name on one page.
* Click Ok.

Let's say you want a stomach bulge:
* click "+" to add a PregPlus component.
* Default values are fine, but you can tweak the min/max bulge size.
* The "Curve" options are the same curves as in Timeline, "SameAsReference" will copy whatever curves your chosen reference uses on each keyframe.

[-- Advanced use case ------------------------------------------------------]

You can click the ` ℹ ` icons for a full explanation of the parameters available to customize or apply corrections:

* Use multiple reference interpolables using pages in the `Reference Interpolable` (For multiple actors/pairs).
* Use multiple time ranges if actors change location during the scene, a new time range will refresh the reference.
* A different keyframe generation pattern for activable Studio items.
* Add a `cutoff` to `Activable` or `MultiActivable` Components to stop a sound early.
* Offset the time of the keyframe (ex. audio items have some delay, so can compensate with offset).
* Adjust the margin of error accepted to register a keyframe.

[---------------------------------------------------------------------------]

### GENERATE THE PLAP FILES ###################################################
___
Once you have exported your Single File and configured the generator, press the `▶` Play button. The program will generate a file for each component (`Preg+`) or each component item (`MAC`). They will be created at whatever location your exported Single File is coming from.

The output should be something like this:

    ::: Success :::

    Generating xml for (MAC, Preg+)

    MAC-Item1:: Generated xx keyframes from 00:00.xx to 00:yy.xx
    MAC-Item2:: Generated xx keyframes from 00:00.xx to 00:yy.xx
    MAC-Item3:: Generated xx keyframes from 00:00.xx to 00:yy.xx
    MAC-Item4:: Generated xx keyframes from 00:00.xx to 00:yy.xx

    Preg+:: Generated xx keyframes from 00:00.00 to 00:37.01
    ==================================================================

See TROUBLESHOOTING below if you have an issue.

### SETUP YOUR SCENE ##########################################################
___
> In CharaStudio

With the Plap.xml files generated, it's time to setup your scene. You can just import `/resources/Plap1234.png` that is included with this install and skip to the next phase: IMPORT TO TIMELINE.

* Add activable items or folders containing activable items (like sound items) for up to the number of Items in your MAC component.

* Each item will be activated in sequence, following the sound pattern of your MAC (default V shape).

### IMPORT TO TIMELINE ########################################################
___
> In CharaStudio

(Delete any interpolables with keyframes in Timeline for the activable components you want to import)

For each of your activable Studio items in your scene:
* Click the folder to highlight it.
* In Timeline -> Single Files, load 1 of the MAC-Item.
* Repeat to link each Mac-Item to one of your activable Studio items, 1 Studio item per MAC-Item.

And voilà, a simple sequence of sound keyframes is added to your scene. By default, it should make a series of repetitive "V" shapes

### LIMITATIONS ###############################################################
___
The reference can be lost if the subject of that interpolable:
 * (A) Increase/decrease his movement by a lot.
 * (B) Moves away from his point of origin.

 Case (A) can usually be fixed by tweaking the Min Pull Out % and Min Push In %.
 Case (B) you can set your `Time Range` to end right where the actor moves location and add a second or more `Time Ranges` with a start time corresponding to the next keyframe of reference for your chosen interpolable.

### TROUBLESHOOTING ###########################################################
___

Could not find the reference keyframe at ...
* Make sure you gave the correct time for the reference keyframe.

There are keyframes for only a part of the scene, and then it stops:
* Most likely the subject moved from his position too much, you can try tweaking Min Pull Out and/or Min Push In. You can also define a second (or more) `Time Ranges` starting at a new reference keyframe (where your actor settled in his new location).

There is a spam of sound keyframes at one point in the scene :
* This can happen when the subject makes micro-in-out moves near the contact point, you can try increasing Min Pull Out and/or Min Push In.

Missing node: `<interpolableGroup name='xxx'>`
* The path you gave for the reference interpolable contains a parent group that is not recognized, make sure the path is correct.
* Modded CharaStudio auto-translates, look at your Timeline and press Alt+T to see the real names of the groups and interpolables.

Missing node: `<interpolable alias='xxx'>`
* An interpolable with the given name was not found. Make sure it is correct and that you renamed it in your scene before you exported it to Single File.
* Modded CharaStudio has auto-translates, look at your Timeline and press Alt+T to see the real names of the groups and interpolables.

Could not find the ... file
* Koikatsu PLAP generator cannot access `/configs` and `/resources`, or `config.toml` and `template.xml` that are supposed to be in these folders. Re-install the program.
