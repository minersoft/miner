@echo off

python %~dp0\tar_main.py %*
exit /B %ERRORLEVEL%
