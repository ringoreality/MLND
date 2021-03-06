import random
import sys
import pickle

class ProgressBar:
    """progress bar class to visualise progress in a loop"""
    def __init__(self,width):
		self.width = width
		self.set(0.)
    def show(self):
        sys.stdout.write('\r[%s%s] %d %%'%('-'*int(self.p*self.width),' '*(self.width-int(self.width*self.p)),100*self.p))
        sys.stdout.flush()
        if (self.p>=1):
            sys.stdout.write('\n')
            sys.stdout.flush()
    def set(self,p):
        # p is percentage of loop finished
        self.p = p

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

class Agent:
    """agent class that implements q-learning with a q-table"""
    actions = ['F','B','L','R','U','D','f','b','l','r','u','d']
    def __init__(self,alpha,gamma):
        self.alpha = alpha
        self.gamma = gamma
        self.qtable = {}
        self.cube = Cube()
        self.trainData = []
        self.testData = []
    def qclean(self):
        # clean state-action pairs with all zeros to save memory and avoid useless 0 qvalue propagation
        removeKeys = []
        for s in self.qtable:
            zeroEntry = True
            for a in self.qtable[s]:
                if self.qtable[s][a] != 0:
                    zeroEntry = False
                    break
            if zeroEntry:
                removeKeys.append(s)
        for k in removeKeys:
            self.qtable.pop(k)
        print 'qtable size: %d' % (len(self.qtable))
    def clearTrainData(self):
        self.trainData = []
    def generateTrainData(self,permutationLength,trainSize):
        for n in range(1,permutationLength):
            for i in range(0,trainSize):
                self.trainData.append(''.join([random.choice(self.actions) for x in range(0,n)]))
    def clearTestData(self):
        self.testData = []
    def generateTestData(self,permutationLength,testSize):
        for n in range(1,permutationLength):
            for i in range(0,testSize):
                self.testData.append(''.join([random.choice(self.actions) for x in range(0,n)]))
    def do(self,act):
        self.cube.reset()
        self.cube.do(act)
    def getState(self, act):
        self.do(act)
        return ''.join(self.cube.facelets)
    def checkState(self,state):
        if state not in self.qtable:
            self.qtable[state] = {}
            for a in self.actions:
                self.qtable[state][a] = 0
    def reward(self,act,action):
        self.do(act+action)
        return 100 if self.cube.good() else 0
    def stateGood(self, s):
        return True\
        if s[0]==s[1]==s[2]==s[3] and s[4]==s[5]==s[6]==s[7] and s[8]==s[9]==s[10]==s[11] and\
        s[12]==s[13]==s[14]==s[15] and s[16]==s[17]==s[18]==s[19] and s[20]==s[21]==s[22]==s[23]\
        else False
    def train(self,tmax,permutationLength,trainSize):
        self.clearTrainData()
        self.generateTrainData(permutationLength,trainSize)
        print 'Training...'
        bar = ProgressBar(40)
        for i in range(0,len(self.trainData)):
            bar.set(1.*(i+1)/len(self.trainData))
            bar.show()
            act = self.trainData[i]
            for t in range(0,tmax):
                s = self.getState(act)
                self.checkState(s)
                if self.stateGood(s):
                    break
                prob = random.uniform(0,1)
                if prob <= 0.5 - (0.4/tmax)*(t+1):
                    action = random.choice(self.actions)
                else:
                    action = max(self.qtable[s],key=self.qtable[s].get)
                reward = self.reward(act,action)
                ns = self.getState(act+action)
                self.checkState(ns)
                if self.stateGood(ns):
                    self.qtable[s][action] = (1-self.alpha)*self.qtable[s][action] + self.alpha*reward
                else:
                    self.qtable[s][action] = (1-self.alpha)*self.qtable[s][action] + self.alpha*(reward+self.gamma*self.qtable[ns][max(self.qtable[ns],key=self.qtable[ns].get)])
                act = act + action
        self.qclean()
    def solve(self,s,maxTries):
        moves = s
        for t in range(0,maxTries):
            state = self.getState(moves)
            if self.cube.good():
                return {'solved':True, 'permutation':s, 'moves':moves[len(s):]}
            if state not in self.qtable:
                action = random.choice(self.actions)
            else:
                action = max(self.qtable[state],key=self.qtable[state].get)
            moves = moves + action
        return {'solved':False, 'permutation':s, 'moves':moves[len(s):]}
    def singleTest(self,s,maxTries):
        result = self.solve(s,maxTries)
        print result
    def test(self,permutationLength,testSize,maxTries):
        testCounts = {}
        recoveryCounts = {}
        solveLengths = {}
        for i in range(1,permutationLength):
            testCounts[i] = 0
            recoveryCounts[i] = 0
            solveLengths[i] = 0
        self.clearTestData()
        self.generateTestData(permutationLength,testSize)
        print 'Testing...'
        bar = ProgressBar(40)
        for i in range(0,len(self.testData)):
            bar.set(1.*(i+1)/len(self.testData))
            bar.show()
            a = self.testData[i]
            testCounts[len(a)] = testCounts[len(a)] + 1
            result = self.solve(a,maxTries)
            if result['solved']:
                recoveryCounts[len(a)] = recoveryCounts[len(a)] + 1
            solveLengths[len(a)] = solveLengths[len(a)] + len(result['moves'])
        print 'recovery rates:'
        for i in range(1,permutationLength):
            print '%d\t %d%%\t %.2f' % (i, 100.0*recoveryCounts[i]/testCounts[i], 1.0*solveLengths[i]/testCounts[i])
        return {'tc': testCounts, 'rc': recoveryCounts, 'sl': solveLengths}
            
agent = Agent(1.0,0.5)
testResult = []
qsizes = []
for i in range(0,100):
    testResult.append({})
    qsizes.append(0)
for i in range(0,100):
    header = 'Train-Test Round %d' % (i+1)
    print '%s\n %s \n%s' % ('*'*(len(header)+2), header, '*'*(len(header)+2))
    agent.train(5,21,1000)
    testResult[i] = agent.test(21,100,20)
    qsizes[i] = len(agent.qtable)
    print '\n'
    with open('Q.pickle', 'wb') as f:
        pickle.dump([qsizes, agent.qtable, testResult], f)
agent.test(21,10000,20)



