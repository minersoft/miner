@echo off

python %~dp0\..\miner_main.py %*
exit /B %ERRORLEVEL%

