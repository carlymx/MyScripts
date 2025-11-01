[Español](README_ES.md)

# Windows UTC Time Registry Fix

This registry file fixes the time inconsistency issue when dual-booting Windows and Linux on the same machine.

## Problem Description

When you have both Windows and Linux installed on the same computer, you may notice that the time is incorrect in one of the operating systems after switching between them.

### Why does this happen?

Windows and Linux handle system time differently:

- **Windows** traditionally uses local time (RTC in local time)
- **Linux** uses UTC (Coordinated Universal Time) for the hardware clock

When Linux sets the hardware clock to UTC and then you boot into Windows, Windows reads the UTC time but interprets it as local time, causing a time difference equal to your time zone offset.

## Solution

This registry file configures Windows to use UTC time for the hardware clock, making it compatible with Linux's approach.

## Installation

1. **Download** the `.reg` file
2. **Right-click** on the file and select **"Merge"**
3. **Confirm** the registry changes when prompted
4. **Restart** your computer for changes to take effect

## Registry Contents

The file configures:

- Time zone to Romance Standard Time (Central European Time)
- UTC time handling (`RealTimeIsUniversal=1`)
- Proper bias values for time zone offset
- Daylight saving time rules

## Verification

After applying the fix:

1. Boot into Windows and check if the time is correct
2. Boot into Linux and verify the time is also correct
3. The time should now be consistent between both operating systems

## Reverting Changes

To revert to Windows default behavior:

1. Open Registry Editor
2. Navigate to `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\TimeZoneInformation`
3. Delete the `RealTimeIsUniversal` value or set it to `0`
4. Restart your computer
