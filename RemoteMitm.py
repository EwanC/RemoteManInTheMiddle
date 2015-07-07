#! /usr/bin/python

import optparse
import socket
import threading

gSubs = {}
gNetwork = None


class Network:

  def __init__(self, host, serverPort, clientPort):
      self.serverHost = host
      self.serverPort = serverPort
      self.serverSock = None
 
      self.clientPort = clientPort
      self.clientSock = None

  def CreateServerSocket(self):
    try:
        hostip = socket.gethostbyname(self.serverHost)
        print "connecting to " + str(hostip)
    except Exception,e:
        print 'unable to resolve host ' + str(e)
        return False

    self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.serverSock.connect((self.serverHost, self.serverPort))

  def CreateClientSocket(self):
    self.clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.clientSock.bind(('', self.clientPort))
    self.clientSock.listen(1)

  def WaitForClient(self):
    print 'Listening for connection from client on port ' + str(self.clientPort)
    conn, addr = self.clientSock.accept()
    self.clientSock = conn
    print 'Connection from ' + str(addr)  
 
  def CloseSockets(self):
   self.clientSock.close()
   self.serverSock.close() 

            
class Forward(threading.Thread):
  def __init__(self, msg, send, reciever):
   threading.Thread.__init__(self)
   self.msg = msg
   self.sender = send
   self.reciever = reciever

  def run(self):
     global gSubs
     while 1:
         data = self.reciever.recv(1024)
         if not data: break
          
         for key,value in gSubs.iteritems():
             data = data.replace(key,value)

         print self.msg + str(data)
         self.sender.send(data) 



def connect():
  global gNetwork

  socket.setdefaulttimeout(60)

  # open a socket to this port
  try:
      gNetwork.CreateServerSocket(); 
  except Exception,e:
      print 'unable to create server socket ' + str(e)
      return False

  # open a socket to this port
  try:
      gNetwork.CreateClientSocket(); 
  except Exception, e:
      print 'unable to create client socket' + str(e)
      return False


  # Wait for client to connect
  try:
      gNetwork.WaitForClient(); 
  except Exception, e:
      print 'Client couldn\'t connect ' + str(e)
      return False


  return True


def loadFile(path):
 global gSubs

 handle = open(path)
 if handle is None:
   print 'unable to load command file'
   return False

 for line in handle:
   split = line.split(':')
   if len(split) != 2:
        continue
   gSubs[split[0]] = split[1]


 print str(len(gSubs)) + ' substitutions loaded'

 return True

def parseoptions():
  global gNetwork

  parser = optparse.OptionParser('usage %prog -H<target> -S <server port> -C <client port> -F<file>')
  parser.add_option('-H',dest='host',type='string')
  parser.add_option('-S',dest='sport',type='int')
  parser.add_option('-C',dest='cport',type='int')
  parser.add_option('-F',dest='file',type='string')

  (options, args) = parser.parse_args()
  host = options.host
  sport = options.sport
  cport = options.cport

  if cport is None:
     cport = 1234 

 
  gNetwork = Network(host,sport,cport)

  fpath = options.file

  if (host is None) or (sport is None):
    print parser.usage
    exit(0)

  if fpath:
   if not loadFile(fpath):
      print "No substitutions used"
      exit(0)

  return

def go():

 global gNetwork

 thread1 = Forward("Host> ",gNetwork.clientSock,gNetwork.serverSock)
 thread2 = Forward("Stub> ",gNetwork.serverSock,gNetwork.clientSock)

 try:
    thread1.start()
    thread2.start()
 except Exception, e:
   print "Error: unable to start thread " + str(e)
 
 try:
   thread1.join()
   thread2.join()
 except Exception, e:
   print "Error: unable to join thread " + str(e)

 gNetwork.CloseSockets() 


def main():

 parseoptions()

 if not connect():
    exit(0)

 go()

 return

if __name__ == '__main__':
  main()
  exit(0);
