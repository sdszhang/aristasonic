class SramContent(object):
   def __init__(self, size=255, dataSize=4):
      self.dataSize_ = dataSize
      self.content_ = [[0] * self.dataSize_ for _ in range(size)]

   def write(self, addr, value):
      externalIndex = addr / self.dataSize_
      internalIndex = addr % self.dataSize_
      self.content_[externalIndex][internalIndex] = value

   def __iter__(self):
      return iter(self.content_)
