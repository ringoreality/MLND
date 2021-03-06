import random
import sys
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import SGD
import numpy as np
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
        # facelets are small color blocks, indexed in F,B,L,R,U,D order
        # in each face, the facelets are indexed in a clockwise order if looked from above
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

class QNN:
    """neural network class to approximate Q-table"""
    def __init__(self):
        self.model = Sequential()
        self.model.add(Dense(96, activation='relu', input_dim=144))
        self.model.add(Dense(48, activation='relu'))
        self.model.add(Dense(12, activation='relu'))
        sgd = SGD(lr=0.001, momentum=0.0, decay=0.0, nesterov=False)
        self.model.compile(loss='mean_squared_error',optimizer=sgd)
    def fit(self, x, y):
        self.model.fit(x,y,batch_size=1,epochs=1,verbose=0)
    def predict(self, x):
        return self.model.predict(x)

class Mem:
    """replay memory class to store past experiences"""
    def __init__(self):
        self.size = 0
        self.s = []
        self.a = []
        self.r = []
        self.ns = []
    def store(self,s,a,r,ns):
        stored = False
        if s in self.s and a in self.a:
            if self.s.index(s) == self.a.index(a):
                stored = True
        if not stored:
            self.size = self.size + 1
            self.s.append(s)
            self.a.append(a)
            self.r.append(r)
            self.ns.append(ns)
    def get(self,n):
        result = {'s':[],'a':[],'r':[],'ns':[]}
        for i in range(0,n):
            idx = random.choice(range(0,self.size))
            result['s'].append(self.s[idx])
            result['a'].append(self.a[idx])
            result['r'].append(self.r[idx])
            result['ns'].append(self.ns[idx])
        return result

class Agent:
    """agent class that implements q-learning with a Neural Network"""
    actions = ['F','B','L','R','U','D','f','b','l','r','u','d']
    def __init__(self):
        self.q = QNN()
        self.cube = Cube()
        self.trainData = []
        self.testData = []
        self.qinfo()
        self.m = Mem()
    def qinfo(self):
        self.q.model.summary()
    def reverseLast(self,act):
        return act[-1].upper() if act[-1].islower() else act[-1].lower()
    def clearTestData(self):
        self.testData = []
    def generateTestData(self,maxMoves,testSize):
        for n in range(1,maxMoves):
            for i in range(0,testSize):
                self.testData.append(''.join([random.choice(self.actions) for x in range(0,n)]))
    def do(self,act):
        self.cube.reset()
        self.cube.do(act)
    def getState(self, act):
        self.do(act)
        return ''.join(self.cube.facelets)
    def state2x(self, state):
        x = np.zeros([1,144])
        colorDict = {'g':[0,0,0,0,0,1],'b':[0,0,0,0,1,0],'o':[0,0,0,1,0,0],'r':[0,0,1,0,0,0],'w':[0,1,0,0,0,0],'y':[1,0,0,0,0,0]}
        for i in range(0,24):
            x[0,6*i:6*i+6] = colorDict[state[i]]
        return x
    def stateGood(self, s):
        return True\
        if s[0]==s[1]==s[2]==s[3] and s[4]==s[5]==s[6]==s[7] and s[8]==s[9]==s[10]==s[11] and\
        s[12]==s[13]==s[14]==s[15] and s[16]==s[17]==s[18]==s[19] and s[20]==s[21]==s[22]==s[23]\
        else False
    def reward(self,act,action):
        self.do(act+action)
        return 100 if self.cube.good() else 0
    def train(self,tmax,permutationLength,batchSize,gamma,iii):
        #print 'Training...'
        #print 'mem size: %d' % (agent.m.size)
        #bar = ProgressBar(40)
        act = ''
        for i in range(0,permutationLength):
            act = act + random.choice(self.actions)
        for t in range(0,tmax):
            # monitor nn output for a given state
            ######################## UNCOMMENT THIS PART TO MONITOR THE QNN'S OUTPUT ########################
            ################### REMEMBER TO COMMENT THE PRINTS IN THE TRAIN-TEST CODES ######################
            #k = self.q.predict(self.state2x(self.getState('b')))
            #sys.stdout.write('\r%s' % (' '*100))
            #sys.stdout.flush()
            #sys.stdout.write('\r%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%d'\
            # % (k[0,0],k[0,1],k[0,2],k[0,3],k[0,4],k[0,5],k[0,6],k[0,7],k[0,8],k[0,9],k[0,10],k[0,11],tmax*iii+t))
            #sys.stdout.flush()
            #################################################################################################
            # get and store s,a,r,ns
            s = self.getState(act)
            # finished?
            if self.stateGood(s):
                break
            prob = random.uniform(0,1)
            if prob <= 0.5 - (0.4/tmax)*(t+1):
                action = random.choice(self.actions)
            else:
                action = self.actions[np.argmax(self.q.predict(self.state2x(s)))]
            reward = self.reward(act,action)
            ns = self.getState(act+action)
            self.m.store(s,action,reward,ns)
            # get s,a,r,ns batch and use as X,Y
            X = np.zeros([0,144])
            Y = np.zeros([0,12])
            batch = self.m.get(batchSize)
            for i in range(0,batchSize):
                X = np.concatenate((X,self.state2x(batch['s'][i])),axis=0)
                objective = self.q.predict(self.state2x(batch['s'][i]))
                if self.stateGood(batch['ns'][i]):
                    np.put(objective, self.actions.index(batch['a'][i]), batch['r'][i])
                else:
                    np.put(objective, self.actions.index(batch['a'][i]), batch['r'][i]+gamma*max(max(self.q.predict(self.state2x(batch['ns'][i])))))
                Y = np.concatenate((Y,objective),axis=0)
            self.q.fit(X, Y)
            # next state
            act = act + action
            # progress bar
            #bar.set(1.*(t+1)/tmax)
            #bar.show()
    def solve(self,s,maxTries):
        moves = s
        for t in range(0,maxTries):
            state = self.getState(moves)
            if self.cube.good():
                return {'solved':True, 'permutation':s, 'moves':moves[len(s):]}
            action = self.actions[np.argmax(self.q.predict(self.state2x(state)))]
            moves = moves + action
        return {'solved':False, 'permutation':s, 'moves':moves[len(s):]}
    def singleTest(self,s,maxTries):
        result = self.solve(s,maxTries)
        print result
    def test(self,maxMoves,testSize,maxTries):
        testCounts = {}
        recoveryCounts = {}
        solveLengths = {}
        for i in range(1,maxMoves):
            testCounts[i] = 0
            recoveryCounts[i] = 0
            solveLengths[i] = 0
        self.clearTestData()
        self.generateTestData(maxMoves,testSize)
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
        for i in range(1,maxMoves):
            print '%d\t %d%%\t %.2f' % (i, 100.0*recoveryCounts[i]/testCounts[i], 1.0*solveLengths[i]/testCounts[i])
        return {'tc': testCounts, 'rc': recoveryCounts, 'sl': solveLengths}
            

agent = Agent()
testResult = []
for i in range(0,3):
    testResult.append({})
for r in range(0,3):
    header = 'Round-%d' % (r+1)
    print '\n\n%s\n %s \n%s' % ('*'*(len(header)+2), header, '*'*(len(header)+2))
    for permutationLength in range(1,21):
        print '\npermutation length: %d' % (permutationLength)
        for i in range(0,1000):
            agent.train(5,permutationLength,10,0.5,i)
            sys.stdout.write('\r%.2f%%' % ((i+1.)/1000*100))
            sys.stdout.flush()
    testResult[r] = agent.test(21,100,20)
    with open('QNN.pickle', 'wb') as f:
        pickle.dump(testResult, f)
    agent.q.model.save('QNNmodel')
agent.test(21,10000,20)

    
