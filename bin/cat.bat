@echo off

python %~dp0\cat_main.py %*
exit /B %ERRORLEVEL%
