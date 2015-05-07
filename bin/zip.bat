@echo off

python %~dp0\zip_main.py %*
exit /B %ERRORLEVEL%
