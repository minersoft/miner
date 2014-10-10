@echo off

python %~dp0\md5sum_main.py %*
exit /B %ERRORLEVEL%
