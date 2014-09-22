@echo off

python %~dp0\curl_main.py %*
exit /B %ERRORLEVEL%

