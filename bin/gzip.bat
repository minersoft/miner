@echo off

python %~dp0\gzip_main.py %*
exit /B %ERRORLEVEL%

