class Cube:
    """cube class for a 2*2*2 rubik's cube"""
    def __init__(self):
        self.reset()
    def reset(self):
        self.facelets = []
        self.faces = {}
        [self.facelets.append(['g','b','o','r','w','y'][i/4]) for i in range(0,24)]
        self.faces['F'] = {'in':[0,1,2,3],'out':[19,18,12,15,21,20,10,9]}
        self.faces['B'] = {'in':[4,5,6,7],'out':[17,16,8,11,23,22,14,13]}
        self.faces['L'] = {'in':[8,9,10,11],'out':[16,19,0,3,20,23,6,5]}
        self.faces['R'] = {'in':[12,13,14,15],'out':[18,17,4,7,22,21,2,1]}
        self.faces['U'] = {'in':[16,17,18,19],'out':[5,4,13,12,1,0,9,8]}
        self.faces['D'] = {'in':[20,21,22,23],'out':[3,2,15,14,7,6,11,10]}
    def info(self):
        for i in range(0,24):
            if i % 4 == 0:
                print ['F','B','L','R','U','D'][i/4], ': ',
            print self.facelets[i],
            if i % 4 == 3:
                print ''
    def _lr(self,x,n,d): # d==1 clockwise
        return x[-n:]+x[:-n] if d==1 else x[n:]+x[:n]
    def _fr(self,face,d):
        for k,v in {'in': 1, 'out': 2}.iteritems():
            tmp = []
            indices = self.faces[face.upper()][k]
            [tmp.append(self.facelets[i]) for i in indices]
            tmp = self._lr(tmp, v, d)
            for i in indices:
                self.facelets[i] = tmp.pop(0)
        return self
    def rotate(self,face,d):
        return self._fr(face,d)
    def do(self,s):
        [self.rotate(f,f.isupper()) for f in s]
        return self
    def eq(self,cube):
        return True if self.facelets == cube.facelets else False
    def good(self):
        for i in range(0,24):
            if self.facelets[i] != self.facelets[i-i%4]: return False
        return True
