@echo off

python %~dp0\gzip_main.py -d %*
exit /B %ERRORLEVEL%

