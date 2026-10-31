@echo off
rem FreeCAD Weekly (Windows portable): launcher de doble clic.
rem No cambia la ExecutionPolicy del sistema (solo este proceso).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0FreeCAD-weekly.ps1" %*
