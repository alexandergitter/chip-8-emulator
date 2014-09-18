import sys, pygame, random
from pygame import *

pixelwidth = pixelheight = 7
pixelx = 64
pixely = 32
size = width, height = pixelx*pixelwidth, pixely*pixelheight
black = 0, 0, 0
white = 255, 255, 255
autorun = True
printops = False

keymap = [K_KP0, K_KP1, K_KP2, K_KP3,
          K_KP4, K_KP5, K_KP6, K_KP7,
          K_KP8, K_KP9, K_a, K_b,
          K_c, K_d, K_e, K_f]

def reset():
    global regTimer, regSound, regPC, stack, regI, regV, memory, waitforkey

    waitforkey = -1
    regTimer = 0
    regSound = 0
    regPC = 0x200
    stack = []
    regI = 0
    regV = [0 for i in range(16)]

    memory = [0xF0, 0x90, 0x90, 0x90, 0xF0,  #0 @ 0x0
              0x20, 0x60, 0x20, 0x20, 0x70,  #1 @ 0x5
              0xF0, 0x10, 0xF0, 0x80, 0xF0,  #2 @ 0xa
              0xF0, 0x10, 0xF0, 0x10, 0xF0,  #3 @ 0xf
              0x90, 0x90, 0xF0, 0x10, 0x10,  #4 @ 0x15
              0xF0, 0x80, 0xF0, 0x10, 0xF0,  #5 @ 0x1a
              0xF0, 0x80, 0xF0, 0x90, 0xF0,  #6 @ 0x1f
              0xF0, 0x10, 0x20, 0x40, 0x40,  #7 @ 0x25
              0xF0, 0x90, 0xF0, 0x90, 0xF0,  #8 @ 0x2a
              0xF0, 0x90, 0xF0, 0x10, 0xF0,  #9 @ 0x2f
              0xF0, 0x90, 0xF0, 0x90, 0x90,  #A @ 0x35
              0xE0, 0x90, 0xE0, 0x90, 0xE0,  #B @ 0x3a
              0xF0, 0x80, 0x80, 0x80, 0xF0,  #C @ 0x3f
              0xE0, 0x90, 0x90, 0x90, 0xE0,  #D @ 0x45
              0xF0, 0x80, 0xF0, 0x80, 0xF0,  #E @ 0x4a
              0xF0, 0x80, 0xF0, 0x80, 0x80]  #F @ 0x4f

    memory.extend([0 for i in range(len(memory), 512)])

    if len(sys.argv) > 1:
        f = open(sys.argv[1], 'rb')
        memory.extend(map(lambda a: ord(a), list(f.read())))
        f.close()
    else:
        print "no argument given"
        sys.exit(0)

    memory.extend([0 for i in range(len(memory), 4096)])

def getSprite(byte):
    res = []
    for i in range(8):
        if (byte & (0x80 >> i)) != 0:
            res.append(True)
        else:
            res.append(False)

    return res

class KeyPad:
    def __init__(self):
        self.keys = [False for i in range(16)]

    def down(self, key):
        global waitforkey, regV
        for i, v in enumerate(keymap):
            if key == v:
                self.keys[i] = True

                if waitforkey >= 0 and waitforkey <= 0xf:
                    regV[waitforkey] = i
                    waitforkey = -1

                break

    def up(self, key):
        for i, v in enumerate(keymap):
            if key == v:
                self.keys[i] = False
                break

    def isPressed(self, hexkey):
        return self.keys[hexkey]

class Opcode:
    def __init__(self, opcode):
        self.set(opcode)

    def set(self, opcode):
        self.opcode = opcode
        self.b1 = (self.opcode & 0xff00) >> 8
        self.b2 = self.opcode & 0xff
        self.n1 = (self.b1 & 0xf0) >> 4
        self.n2 = self.b1 & 0xf
        self.n3 = (self.b2 & 0xf0) >> 4
        self.n4 = self.b2 & 0xf
        self.ad =  self.n2 << 8 | self.b2

    def __str__(self):
        if self.opcode == 0x00E0:
            return "CLS"
        elif self.opcode == 0x00EE:
            return "RET"
        elif self.n1 == 0x1:
            return "JP " + hex(self.ad)
        elif self.n1 == 0x2:
            return "CALL " + hex(self.ad)
        elif self.n1 == 0x3:
            return "SE V" + str(self.n2) + ", " + str(self.b2)
        elif self.n1 == 0x4:
            return "SNE V" + str(self.n2) + ", " + str(self.b2)
        elif self.n1 == 0x5:
            return "SE V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x6:
            return "LD V" + str(self.n2) + ", " + str(self.b2)
        elif self.n1 == 0x7:
            return "ADD V" + str(self.n2) + ", " + str(self.b2)
        elif self.n1 == 0x8 and self.n4 == 0x0:
            return "LD V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0x1:
            return "OR V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0x2:
            return "AND V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0x3:
            return "XOR V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0x4:
            return "ADD V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0x5:
            return "SUB V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0x6:
            return "SHR V" + str(self.n2) + " {, V" + str(self.n3) + "}"
        elif self.n1 == 0x8 and self.n4 == 0x7:
            return "SUBN V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0x8 and self.n4 == 0xE:
            return "SHL V" + str(self.n2) + " {, V" + str(self.n3) + "}"
        elif self.n1 == 0x9:
            return "SNE V" + str(self.n2) + ", V" + str(self.n3)
        elif self.n1 == 0xa:
            return "LD I, " + hex(self.ad)
        elif self.n1 == 0xb:
            return "JP V0, " + hex(self.ad) + ", " + hex(b2)
        elif self.n1 == 0xc:
            return "RND V" + str(self.n2) + ", " + hex(self.b2)
        elif self.n1 == 0xd:
            return "DRW V" + str(self.n2) + ", V" + str(self.n3) + ", " + str(self.n4)
        elif self.n1 == 0xe and self.b2 == 0x9e:
            return "SKP V" + str(self.n2)
        elif self.n1 == 0xe and self.b2 == 0xa1:
            return "SKP V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x07:
            return "LD V" + str(self.n2) + ", DT"
        elif self.n1 == 0xf and self.b2 == 0x0a:
            return "LD V" + str(self.n2) + ", K"
        elif self.n1 == 0xf and self.b2 == 0x15:
            return "LD DT, V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x18:
            return "LD ST, V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x1e:
            return "ADD I, V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x29:
            return "LD F, V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x33:
            return "LD B, V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x55:
            return "LD [I], V" + str(self.n2)
        elif self.n1 == 0xf and self.b2 == 0x65:
            return "LD V" + str(self.n2) + ", [I]"
        else:
            return hex(self.opcode) + " (no decode)"


class Screen:
    def __init__(self):
        self.mem = [[False for i in range(pixely)] for j in range(pixelx)]
        self.surface = pygame.display.set_mode(size)

    def cls(self):
        #self.mem = [[False for i in range(pixely)] for j in range(pixelx)]
        for x in range(pixelx):
            for y in range(pixely):
                self.mem[x][y] = False
        self.surface.fill(black)

    def set(self, x, y, val):
        x = x % pixelx
        y = y % pixely
        pxdeleted = self.mem[x][y]

        self.mem[x][y] = self.mem[x][y] ^ val
        rect = pygame.Rect([x*pixelwidth, y*pixelheight, pixelwidth, pixelheight])

        if self.mem[x][y]:
            self.surface.fill(white, rect)
        else:
            self.surface.fill(black, rect)

        return pxdeleted and not self.mem[x][y]

    def draw(self, vx, vy, size):
        startx = regV[vx]
        starty = regV[vy]
        regV[0xf] = 0x0
        for y in range(size):
            sprite = getSprite(memory[regI + y])
            for x in range(8):
                posx = startx + x
                posy = starty + y
                if self.set(posx, posy, sprite[x]) == True: regV[0xf] = 0x1

def printState():
    global regV, stack, regI, regTimer, regSound, regPC, memory

    for i in range(8):
        print "V" + str(i) + "=" + str(regV[i]),
    print
    for i in range(8, 16):
        print "V" + str(i) + "=" + str(regV[i]),

    print
    print "regI=" + hex(regI) + " (" + hex(memory[regI]) + " " + hex(memory[regI+1]) + ")"
    print "regPC=" + hex(regPC) + " (" + str(Opcode(memory[regPC] << 8 | memory[regPC+1])) + ")"
    print "delay=" + hex(regTimer)
    print "sound=" + hex(regSound)
    print "stack: " + str(stack)

def add(a, b, cb = True):
    global regV
    result = a + b

    if cb == True:
        if result > 255:
            regV[0xf] = 1
        else:
            regV[0xf] = 0

    return result & 0xff

def sub(a, b, cb = True): #a - b
    global regV

    if cb == True:
        if a > b:
            regV[0xf] = 1
        else:
            regV[0xf] = 0

    return (a + ~b + 1) & 0xff

def process():
    global regTimer, regSound, regPC, stack, regI, regV, memory, screen, keys, waitforkey, autorun

    if waitforkey >= 0 and waitforkey <= 0xf: return
    op = Opcode(memory[regPC] << 8 | memory[regPC+1])
    if printops: print hex(regPC) + ": " + str(op)

    regPC = regPC + 2

    if op.opcode == 0x00E0:
        screen.cls()
    elif op.opcode == 0x00EE:
        regPC = stack.pop()
    elif op.n1 == 0x1:
        regPC = op.ad
    elif op.n1 == 0x2:
        stack.append(regPC)
        regPC = op.ad
    elif op.n1 == 0x3:
        if regV[op.n2] == op.b2: regPC = regPC + 2
    elif op.n1 == 0x4:
        if regV[op.n2] != op.b2: regPC = regPC + 2
    elif op.n1 == 0x5:
        if regV[op.n2] == regV[op.n3]: regPC = regPC + 2
    elif op.n1 == 0x6:
        regV[op.n2] = op.b2
    elif op.n1 == 0x7:
        regV[op.n2] = add(regV[op.n2], op.b2, False)
    elif op.n1 == 0x8 and op.n4 == 0x0:
        regV[op.n2] = regV[op.n3]
    elif op.n1 == 0x8 and op.n4 == 0x1:
        regV[op.n2] = regV[op.n2] | regV[op.n3]
    elif op.n1 == 0x8 and op.n4 == 0x2:
        regV[op.n2] = regV[op.n2] & regV[op.n3]
    elif op.n1 == 0x8 and op.n4 == 0x3:
        regV[op.n2] = regV[op.n2] ^ regV[op.n3]
    elif op.n1 == 0x8 and op.n4 == 0x4:
        regV[op.n2] = add(regV[op.n2], regV[op.n3])
    elif op.n1 == 0x8 and op.n4 == 0x5:
        regV[op.n2] = sub(regV[op.n2], regV[op.n3])
    elif op.n1 == 0x8 and op.n4 == 0x6:
        if (regV[op.n2] & 0x1) != 0: regV[0xf] = 1
        else: regV[0xf] = 0
        regV[op.n2] = (regV[op.n2] >> 1) & 0xff
    elif op.n1 == 0x8 and op.n4 == 0xe:
        if (regV[op.n2] & 0x80) != 0: regV[0xf] = 1
        else: regV[0xf] = 0
        regV[op.n2] = (regV[op.n2] << 1) & 0xff
    elif op.n1 == 0x9:
        if regV[op.n2] != regV[op.n3]: regPC = regPC + 2
    elif op.n1 == 0xa:
        regI = op.ad
    elif op.n1 == 0xb:
        regPC = op.ad + regV[0]
    elif op.n1 == 0xc:
        regV[op.n2] = random.randint(0, 255) & op.b2
    elif op.n1 == 0xd:
        screen.draw(op.n2, op.n3, op.n4)
    elif op.n1 == 0xe and op.b2 == 0x9e:
        if keys.isPressed(regV[op.n2]): regPC = regPC + 2
    elif op.n1 == 0xe and op.b2 == 0xa1:
        if not keys.isPressed(regV[op.n2]): regPC = regPC + 2
    elif op.n1 == 0xf and op.b2 == 0x07:
        regV[op.n2] = regTimer
    elif op.n1 == 0xf and op.b2 == 0x0a:
        waitforkey = op.n2
    elif op.n1 == 0xf and op.b2 == 0x15:
        regTimer = regV[op.n2]
    elif op.n1 == 0xf and op.b2 == 0x18:
        regSound = regV[op.n2]
    elif op.n1 == 0xf and op.b2 == 0x1e:
        regI = (regI + regV[op.n2]) & 0xffff
    elif op.n1 == 0xf and op.b2 == 0x29:
        regI = 5 * regV[op.n2]
    elif op.n1 == 0xf and op.b2 == 0x33:
        memory[regI] = regV[op.n2] / 100
        memory[regI+1] = (regV[op.n2] % 100) / 10
        memory[regI+2] = (regV[op.n2] % 10)
    elif op.n1 == 0xf and op.b2 == 0x55:
        for p in range(op.n2+1): memory[regI + p] = regV[p]
    elif op.n1 == 0xf and op.b2 == 0x65:
        for p in range(op.n2+1): regV[p] = memory[regI + p]
    else:
        print hex(op.opcode) + " (not implemented)"
        printState()
        sys.exit(0)

def updateTimers():
    global lastTime, regTimer, regSound

    cycles = (pygame.time.get_ticks() - lastTime) / 17

    if cycles > 0:
        regTimer = regTimer - cycles
        regSound = regSound - cycles
        lastTime = pygame.time.get_ticks()

    if regTimer < 0: regTimer = 0
    if regSound < 0: regSound = 0

reset()
pygame.init()
screen = Screen()
keys = KeyPad()
pygame.key.set_repeat()

lastTime = pygame.time.get_ticks()

def main():
    global autorun, printops, screen
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                process()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                printState()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                autorun = not autorun
                if autorun == True:
                    pygame.key.set_repeat()
                else:
                    pygame.key.set_repeat(500, 10)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                printops = not printops
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                screen.cls()
                reset()
            elif event.type == pygame.KEYDOWN:
                keys.down(event.key)
            elif event.type == pygame.KEYUP:
                keys.up(event.key)
        if autorun: process()
        updateTimers()
        pygame.display.flip()

main()
