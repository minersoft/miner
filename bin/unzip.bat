@echo off

python %~dp0\unzip_main.py %*
exit /B %ERRORLEVEL%
