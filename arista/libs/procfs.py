
import datetime

from .fs import readFileContent

def uptime(path='/proc/uptime'):
   '''Read uptime from /proc/uptime'''
   return tuple(float(v) for v in readFileContent(path).rstrip().split())

def bootDatetime():
   '''Read uptime and return a datetime object representing boot time'''
   return datetime.datetime.now() - datetime.timedelta(seconds=uptime()[0])
