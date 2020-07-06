# Mario is Missing PRNG Project

## Introduction

Mario is Missing for the SNES is an "education" game (aka "edutainment") where you play as Luigi, who has lost his brother to the evil Bowser. 

You spend your time navigating multiple cities by finding random items that miraculously fit on your person and return them to an omnipresent Princess Peach who scowls at you when you answer the question wrong but then when answered right tells you that she hopes you find Mario. 

All the while you must figure out the city you're in and then have your horse, Yoshi, who is always back in Antarctica every time you end up in a new city and have him leave from there, where Bowser has a castle with Mario within mind you, and meet you in the city you're presently in.

This is necessary as you need to do so to get rid of a Pokey blocking you from leaving the level. It's also to your benefit to do so early since Yoshi will help you get through the city quicker.

You collect three items from three random Koopas that are roaming the streets. These Koopas explode if they don't have an item, but if they do have what you need, they'll just disintegrate instead, leaving behind an object that on the main game screen otherwise looks like crumpled paper.

Annoyingly, you have to wait for NPCs to cross the street in front of you before you can go up or down them. This is regardless of the fact that they often end up being Koopas and you'd otherwise just stomp on them in any other situation.

Anyway, the goal is to collect these items, tell Yoshi where the heck you are, and then defeat three bosses until you finally rescue your brother.

## PRNG

The game is separated into three dungeons each with gates that lead into five different cities. Upon completion of all five cities, you face off against a dungeon boss. This repeats until you've defeated the three bosses and you end with a cut scene where Bowser falls into a hole.

Dungeon order is set but city is not and you can choose from any of five. However, item placement is dictated by door order so if you choose to go to San Francisco second instead of first, the Koopas with the required items will not be in the same place if you chose San Francisco first.

The PRNG is still being worked out fully, but the number of NPC sprites per level (likely all Koopas and possibly the four human NPCs) dictates the PRNG value and thus which Koopas will have the items. This means that it doesn't matter if San Francisco is third and you play other cities before, the sprites will not stay consistent if you change the city order preceding.

The good news here is that if you play Moscow and Nairobi first, this means that the items in Nairobi will always be the same as will San Franscisco, Rome, and Beijing, but of course depending on what order you choose. A consistent order is a going to have a set sprite and item placement no matter what.

### Technical details

The PRNG stores two 16-bit values in two different locations in memory. It does this by executing the following (in 6502/65816 assembly) at power on:

```
80:834C   LDA     #$119A
80:834F   STA     0x04E4
80:8352   STA     0x04E0
80:8355   LDA     #$E84
80:8358   STA     0x04E6
80:835B   STA     0x04E2
80:835E   LDA     #$4321
80:8361   STA     0x04EA
80:8364   LDA     #$8765
80:8367   STA     0x04EC
```

This means that at `0x04E0` and `0x04E4` we get a "high" value (set to `0x119A`) and at `0x04E2` and `0x04E6` a "low" value (set to `0x0E84`). Both `0x04E4` and `0x04E6` are values that are changed throughout the game but the other two are not and remain the same.

Keep in mind, when viewing this in memory, the 65816 is big-endian, meaning that when we see `0x119A` in code, it will show up in memory and in the CPU's registers as `0x9A11`.

Manipulation of the PRNG can be found at `0x80836C` but work is still being sorted out how it works.

### Using the code

Replication of the code can be found in `mimloader.py` and you can also import it by using the following:

```
from mimloader import machineEmulator
me = machineEmulator()
me.prngPowerOn()
me.prngItemAssignment()
```

It will otherwise run if you execute `python3 mimloader.py`. You will need to make sure that your ROM is in SMC format with the filename `mim.smc` to execute. I imagine it will work if it ends in SFC however. To my knowledge there is only one retail release for this game at least for NTSC regions so it should just work with any copy you have.

More on how to use this will be documented as we progress.

## So what does this mean for speedrunning?

With three dungeons and five cities per dungeon, you're looking at 154 different possible permutations per dungeon with a total of 462 total routes. 

You can check this for yourself and then tell me I am wrong if you figure out otherwise (`c2` and `c3` were left unused since it wasn't necessary to reference them):

```
from itertools import permutations
c1 = 'sf moscow nairobi rome beijing'.split()
c2 = 'paris mexico sydney argentina athens'.split()
c3 = 'cairo tokyo rio london nyc'.split()
len(list(permutations(c1)) + list(permutations(c1[1:])) + list(permutations(c1[2:]))+ list(permutations(c1[3:])) + list(permutations(c1[4:])) + list(permutations(c1[5:]))) * 3
```

This doesn't take into account that it is possible that some cities may have a shared NPC value but since this project is still in its infancy, this will be the logic we have moving forward and there is one other factor that has yet to come up that we need to take into consideration.

One could play all of the possible city orders and figure out where the items are but there is the problem of figuring out what path is most efficient. The sprites are moved depending on the PRNG and having the Koopas as close as possible to the booths where you speak to Princess Peach is optimal. This means that playing the 462 routes isn't effective unless you have a lot of time on your hands.

## Project goals and status

This project intends to perform the following:

- Replicate the PRNG
- Replicate the item and sprite placement
- Determine the fastest order

How this will be achieved is that we'll reverse engineer the 65816 code into Python to then allow us to have 1:1 functionality.

- *2020/07/05* - Code published to Github, baseline details on PRNG memory location has been established, and code disassembled

## Help out?

I am terrible at 6502/65816 assembly (and with assembly in general) and am open to people helping out. If you want to help out, you'll need to have an assembly output of the Mario is Missing SNES ROM. This can be done using a variety of tools but I've worked primarily out of IDA. For licensing and copyright reasons, I won't be providing any of that documentation.

However, much of the current code has been commented with the existing instructions from the game and if you do submit any patches I ask that you include details using the same methodology.

To help out, I am using code borrowed from [PySNES](https://github.com/JonnyWalker/PySNES), which is a Python-based emulator. It doesn't have full implementation of the 65816 processor, but its memory mapping functionality has been super useful. Use of the CPU's stack management proved to be not working so I've implemented my own "stack".

This should be considered an incomplete project and will not help any current speedrunner looking for an edge in this game. At the time of this writing, there are only a handful of people running it anyway with yours truly being in 4th place out of a possible five people for a 100% run.

## Contact

If you have any questions, feel free to reach out to be on Twitter at [@KateLibC](https://twitter.com/katelibc).