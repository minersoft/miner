Miner
=====

Miner is generic engine and interactive framework for processing and analyzing data.
It defines simple yet powerful query language for data processing, see some examples below.
Miner is written in python, allowing easy integration with proprietary data formats and extending its functionality.

Applications
------------
Miner can  be used for wide variety of tasks like analyzing logs of web servers, financial data,
post processing responses from database queries and even processing network captures.
It can be also used to perform simulations  and tests.

Query Examples
--------------
Consider you have log from http server in csv format with something like following:
```
path,time
/index.html,10
/login,1000
/heavy_script?param=1,10000
```
With miner you can easily find user requests that took maximum time:
```
READ log.csv | TOP 5 time | STDOUT
```
The output will be something like:
```
path                   time
----------------------------
/heavy_script?param=5  50000
/heavy_script?param=4  40000
/heavy_script?param=3  30000
/heavy_script?param=2  20000
/heavy_script?param=1  10000
```

You can see the total time consumed by different resources
```
READ log.csv | SELECT path.split('?',1)[0] as resource, time | FOR DISTINCT resource SELECT count(True) as numRequests, sum(time) | STDOUT
resource       numRequests     time
------------------------------------
/heavy_script  10              100000
/index.html    5               50
/login         5               5000
```
And many many others interesting facts that you can learn without writing single line of code.

Miner provides the possibility to work with plain data without need to insert it to database or processing it in another way.

Windows Binaries
----------------
Miner distribution includes python implementation of following linux utilities:
* curl
* gzip, gunzip, zcat
* md5sum
* tar
