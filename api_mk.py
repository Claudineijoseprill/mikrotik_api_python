
import sys, posix, time, binascii, socket, select, ssl
import hashlib

class MK_API:
    "Routeros api"
    def __init__(self, dst, username, password, port=8728, secure=False):

        self.currenttag = 0
        self.dt_snd = {}
        self.command = ''
        self.ig = '='
        self.message = 'message'
        self.error = ''
        self.status = ''
        self.datos = []
        self.sock = None
        self.loged = False
        self.connected = False
        self.secure = secure



        self.open_socket(dst, port, self.secure)
        if self.connected:
            self.login(username, password)
        else:
            print ('could not open socket')

    def open_socket(self, dst, port, secure):
        
        res = socket.getaddrinfo(dst, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        af, socktype, proto, canonname, sockaddr = res[0]
        self.sock = socket.socket(af, socktype, proto)
        if secure:
            self.sock = ssl.wrap_socket(skt, ssl_version=ssl.PROTOCOL_TLSv1_2, ciphers="ADH-AES128-SHA256") #ADH-AES128-SHA256
        self.sock.connect(sockaddr)

        if self.sock is not None: self.connected = True


    def login(self, username, pwd):

        self.loged = False

        self.command = '/login'
        self.dt_snd['name'] = username
        self.dt_snd['password'] = pwd

        self.send()

        if self.status == "!trap":
            return self.loged

        for attrs in self.datos:
          if 'ret' in attrs.keys():
        #for repl, attrs in self.talk(["/login"]):
            chal = binascii.unhexlify((attrs['ret']).encode(sys.stdout.encoding))
            md = hashlib.md5()
            md.update(b'\x00')
            md.update(pwd.encode(sys.stdout.encoding))
            md.update(chal)

            self.command = '/login'
            self.dt_snd['name'] = username
            self.dt_snd['response'] = "00" + binascii.hexlify(md.digest()).decode(sys.stdout.encoding)
            self.dt_snd['password'] = pwd

            self.send()
            if self.status == "!trap":
                return self.loged

        self.loged = True
        return self.loged

    def send(self):
        self.writeSentence()
        self.datos.clear()

        self.error = ''
        vv = ''
        while 1:
            i = self.readSentence()
            
            if len(i) == 0: continue
            self.status = i[0]
            attrs = {}
            oo = 0
            for w in i[1:]:
                
                j = w.find('=', 1)
                if (j == -1):
                    attrs[w] = ''
                    oo = 1
                else:
                    vv = w[1:j]
                    if self.message == vv and self.error == '':
                        self.error = w[j+1:]

                    attrs[vv] = w[j+1:]
                    oo = 1

            if oo == 1: self.datos.append(attrs)
            if self.status == '!done': break

    def writeSentence(self):


        self.writeWord(self.command)
        ret = 0

        for w in self.dt_snd:
            self.writeWord(self.ig+w+self.ig+self.dt_snd[w])
            ret += 1
        self.writeWord('')


        self.dt_snd.clear()
        return ret

    def readSentence(self):
        r = []
        while 1:
            w = self.readWord()
            if w == '': return r
            r.append(w)

    def writeWord(self, w):
        self.writeLen(len(w))
        self.writeStr(w)

    def readWord(self):
        ret = self.readStr(self.readLen())
        return ret

    def writeLen(self, l):
        if l < 0x80:
            self.writeByte((l).to_bytes(1, sys.byteorder))
        elif l < 0x4000:
            l |= 0x8000
            tmp = (l >> 8) & 0xFF
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        elif l < 0x10000000:
            l |= 0xE0000000
            self.writeByte(((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))
        else:
            self.writeByte((0xF0).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 24) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 16) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte(((l >> 8) & 0xFF).to_bytes(1, sys.byteorder))
            self.writeByte((l & 0xFF).to_bytes(1, sys.byteorder))

    def readLen(self):
        c = ord(self.readInt(1))
        # print (">rl> %i" % c)
        if (c & 0x80) == 0x00:
            pass
        elif (c & 0xC0) == 0x80:
            c &= ~0xC0
            c <<= 8
            c += ord(self.readInt(1))
        elif (c & 0xE0) == 0xC0:
            c &= ~0xE0
            c <<= 8
            c += ord(self.readInt(1))
            c <<= 8
            c += ord(self.readInt(1))
        elif (c & 0xF0) == 0xE0:
            c &= ~0xF0
            c <<= 8
            c += ord(self.readInt(1))
            c <<= 8
            c += ord(self.readInt(1))
            c <<= 8
            c += ord(self.readInt(1))
        elif (c & 0xF8) == 0xF0:
            c = ord(self.readInt(1))
            c <<= 8
            c += ord(self.readInt(1))
            c <<= 8
            c += ord(self.readInt(1))
            c <<= 8
            c += ord(self.readInt(1))
        return c

    def writeStr(self, str):
        n = 0;
        while n < len(str):
            r = self.sock.send(bytes(str[n:], 'UTF-8'))
            if r == 0: raise RuntimeError("connection closed by remote end")
            n += r

    def writeByte(self, str):
        n = 0;
        while n < len(str):
            r = self.sock.send(str[n:])
            if r == 0: raise RuntimeError("connection closed by remote end")
            n += r

    def readInt(self, length):
        ret = ''
        # print ("length: %i" % length)
        while len(ret) < length:
            s = self.sock.recv(length - len(ret))
            if s == b'': raise RuntimeError("connection closed by remote end")
            # print (b">>>" + s)
            # atgriezt kaa byte ja nav ascii chars

            if s >= (128).to_bytes(1, "big") :
               return s

            # print((">>> " + s.decode(sys.stdout.encoding, 'ignore')))
            ret += s.decode(sys.stdout.encoding, "replace")
        return ret

    def readStr(self, le):
        ret = ""
        byte = b''
        # print ("length: %i" % length)

        while(le > 0):
            char = self.sock.recv(1)
            if not char: break

            byte += char
            le -= 1
            
        ret += byte.decode(sys.stdout.encoding, "replace")
        return ret


