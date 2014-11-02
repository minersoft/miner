@echo off

python %~dp0\grep_main.py %*
exit /B %ERRORLEVEL%
