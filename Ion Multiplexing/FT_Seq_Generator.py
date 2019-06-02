    
#!/usr/bin/env python

'''
Copyright 2018  Brian Clowers bhclowers <at> gmail.com

FT_Seq_Generator.py is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later versionp.

FT_Seq_Generator.py is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with FT_Seq_Generator.py.  If not, see <http://www.gnu.org/licenses/>.
'''

import numpy as np
import matplotlib.pyplot as P
from scipy.signal import chirp


def transformArray2(pulseSeq, lowState = -1, hiState = 1):
    '''
    Transforms the -1 and 1s pulse sequence into a pulse sequence
    that has the pulse width instead of the 1/-1 scheme.
    '''
    countArray = []
    pulseSequence = np.zeros_like(pulseSeq)
    pulseSequence2 = np.zeros_like(pulseSeq)
    pulseSequence2+=hiState
    

    curState = lowState
    curCount = 0
    for i,p in enumerate(pulseSeq[::-1]):
        if p == curState:
            curCount+=1
        else:
            curState = p
            countArray.append(curCount)
            curCount = 0
    countArray = np.array(countArray)
    countArray+=1#not sure this is correct, need to be sure the system is counting properly (e.g. from zero)

    pulseCount = 1
    for i,p in enumerate(pulseSeq):#[::-1]):#reverse PRS to count backwards
        try:
            if p == hiState:
                pulseCount += 1
            elif p == lowState:
                if i>0:#accounting for first element being 0
                    pulseSequence[i-1] = pulseCount
                    # print(pulseCount, np.int(pulseCount/2))
                    pulseSequence2[i-pulseCount:i-np.int(pulseCount/2)] = lowState
                pulseCount = 1#reset count
        except:
            print("Not a sequence of %s and %s's"%(lowState, hiState))
            raise
    # return pulseSequence[::-1], pulseSequence2[::-1], countArray[::-1] #reverse to be in the forward direction (perhaps uncessary)
    return pulseSequence, pulseSequence2, countArray[::-1] #reverse to be in the forward direction (perhaps uncessary)


def transformArray(pulseSeq, lowState = -1, hiState = 1):
    '''
    Transforms the -1 and 1s pulse sequence into a pulse sequence
    that has the pulse width instead of the 1/-1 scheme.
    '''
    countArray = []
    pulseSequence = np.zeros_like(pulseSeq)
    pulseCount = 0

    curState = lowState
    curCount = 0
    for i,p in enumerate(pulseSeq[::-1]):
        if p == curState:
            curCount+=1
        else:
            curState = p
            countArray.append(curCount)
            curCount = 0
    countArray = np.array(countArray)
    countArray+=1#not sure this is correct, need to be sure the system is counting properly (e.g. from zero)


    for i,p in enumerate(pulseSeq[::-1]):#reverse PRS to count backwards
        try:
            if p == 1:
                pulseCount += 1
            elif p == -1:
                if i>0:#accounting for first element being 0
                    pulseSequence[i-1] = pulseCount
                pulseCount = 0#reset count
        except:
            print("Not a sequence of -1 and 1's")
            raise
    return pulseSequence[::-1], countArray[::-1]#reverse to be in the forward direction (perhaps uncessary)

def findTransitions(pulseSeq, plotBool = False):
    zeroCrossings = np.where(np.diff(np.sign(pulseSeq)))[0]
    zcY = np.zeros_like(zeroCrossings)
    zcY+=1
    # print(len(zeroCrossings))
    diffArray = np.ediff1d(zeroCrossings)
    # print(len(diffArray))
    if plotBool:
        P.plot(zeroCrossings, zcY, 'ro')
        P.plot(pulseSeq, 'bs-', drawstyle="steps")
        P.ylim(-2, 2)
        P.show()

if __name__ == '__main__':
    fStart = 5 #frequency in Hz
    
    fStop = 7505 #freqency in Hz
    scanTime = 480#make this a float to retain precision (seconds)
    sampleSpacing = 1.0/10000#500E-6
    
    fStart *=1.0 #make sure it is a float
    fCycles = np.abs((fStart-fStop)/scanTime)
    #Keep in mind the correct length relative to total TOF scan time and actual sweep time
    #e.g. 60 us at 133333 give 8 seconds but sweep time is 7.998 or 133300
    numPoints = np.int(scanTime/sampleSpacing)#80#9600000#of points across your experiment
    stepTime = scanTime/numPoints
    print(stepTime, fCycles, "Num Points: %d"%numPoints)

    t = np.linspace(0, scanTime, numPoints)
    pulseSeq = chirp(t, f0=fStart, f1=fStop, t1 = scanTime, method = 'linear')


    posIndex = np.where(pulseSeq>0)[0]#account to make things into a square wave
    negIndex = np.where(pulseSeq<0)[0]
    pulseSeq[posIndex]=1
    pulseSeq[negIndex]=-1

    # findTransitions(pulseSeq)
    # pwSeq, countArray = transformArray(pulseSeq)
    pwSeq, pwSeq2, countArray = transformArray2(pulseSeq)
    pulseSeq*=-1
    plotBool = False
    if plotBool:
        
        # pulseSeq+=1
        P.plot(pulseSeq, 'go-', drawstyle="steps")
        # P.plot(pwSeq, 'r-', drawstyle="steps")
        P.plot(pwSeq2, 'b-', drawstyle="steps")
        P.show()
    #Convert to 0s and 1s.  Need to scale for your application (e.g IGOR Voltage Outputs)
    pulseSeq += 1
    pulseSeq /= 2
    pwSeq2 += 2
    pwSeq2 /= 2
    print(pulseSeq.dtype, pwSeq2.dtype)
    print("Saving 1st Sequence")
    np.savetxt('FTSeq_%d_%d_%d_Lin.txt'%(fStart,fStop,scanTime),pulseSeq, fmt='%d')
    print("Saving 2nd Sequence")
    np.savetxt('FTSeq_%d_%d_%d_Lin_2ndGate.txt'%(fStart,fStop,scanTime),pwSeq2, fmt='%d')
    print("DONE!")
# 
    # P.plot(pulseSeq[::-1])
    P.plot(pulseSeq)
    P.show()



