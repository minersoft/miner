@echo off
SET args = ""
FOR %%A IN (%*) DO (
  SET args = %args% "%%A"
)

python miner_main.py %*
exit /B %ERRORLEVEL%

