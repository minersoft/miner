@echo off

python %~dp0\gzip_main.py -c %*
exit /B %ERRORLEVEL%

