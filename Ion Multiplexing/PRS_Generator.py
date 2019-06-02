#!/usr/bin/env python

'''
Copyright 2013  Brian Clowers bhclowers <at> gmail.com

PRS_Generator.py is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PRS_Generator.py is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PRS_Generator.py.  If not, see <http://www.gnu.org/licenses/>.

####################################

PRS_Generator.py

Maximal Length Psuedo Random Sequence Generator

Description:  This script returns an array consisting of 0's and 1's in a
pseudo random sequence (prs) as defined by Harwitt and Sloane.
Each sequence is determined by using a primitive binary polynomial.
For additional detail see their book entitled: Hadamard Transform Optics,
Academic Press, NY, 1979.  The appendix contains an in depth discussion
of the topic.

'''

from matplotlib import use
try:
    use("QT4Agg")
except:
    # raise
    use("TkAgg")

from numpy import *
import operator

__author__ = "Brian H. Clowers"
__copyright__ = "Copyright 2013, Brian H. Clowers"
__credits__ = ["Harwitt and Sloane appendix.  Steve Massick for pushing me towards the Hadamard technique."]
__license__ = "GPL >=2.0"
__version__ = "1.0"
__maintainer__ = "Brian Clowers"
__email__ = "bhclowers <at> gmail.com"
__status__ = "Beta"

def Sequence_Generator(bit_shift):
    sequence_length=2**bit_shift - 1
    prs_1D=zeros(sequence_length, dtype=int)
    prs_1D[bit_shift-1]=1 ## initialize the correct element
    if bit_shift < 3 or bit_shift > 20:
        print "Desired bit shift is out of range.\nTry again!"
        return False
    for i in range(bit_shift, sequence_length,1):

        prs_1D[i]= {
            
            3:  lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 1]),
            
            4:  lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 1]),
            
            5:  lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 2]),
            
            6:  lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 1]),
            
            7:  lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 1]),
            
            8:  lambda: operator.xor(prs_1D[i-bit_shift],operator.xor(prs_1D[i - bit_shift + 1],
                       operator.xor(prs_1D[i - bit_shift + 5],prs_1D[i - bit_shift + 6]))),
            
            9:  lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 4]),
            
            10: lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 3]),
            
            11: lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 2]),
            
            12: lambda: operator.xor(prs_1D[i-bit_shift],operator.xor(prs_1D[i - bit_shift + 3],
                        operator.xor(prs_1D[i - bit_shift + 4],prs_1D[i - bit_shift + 7]))),
            
            13: lambda: operator.xor(prs_1D[i - bit_shift], operator.xor(prs_1D[i - bit_shift + 1],
                        operator.xor(prs_1D[i - bit_shift + 3],prs_1D[i - bit_shift + 4]))),
            
            14: lambda: operator.xor(prs_1D[i - bit_shift], operator.xor(prs_1D[i - bit_shift +1],
                        operator.xor(prs_1D[i - bit_shift + 11], prs_1D[i - bit_shift + 12]))),
            
            15: lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 1]),
            
            16: lambda: operator.xor(prs_1D[i - bit_shift], operator.xor(prs_1D[i - bit_shift + 2],
                        operator.xor(prs_1D[i - bit_shift + 3], prs_1D[i - bit_shift + 5]))),
            
            17: lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 3]),
            
            18: lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 7]),
            
            19: lambda: operator.xor(prs_1D[i - bit_shift], operator.xor(prs_1D[i - bit_shift + 1],
                        operator.xor(prs_1D[i - bit_shift + 5], prs_1D[i - bit_shift + 6]))),
            
            20: lambda: operator.xor(prs_1D[i-bit_shift],prs_1D[i - bit_shift + 3]),

        } [bit_shift]()

    return prs_1D


def Generate_Oversampled_PRS_v2(bit_shift, oversampling, IFT = False, savePRS = False, invert = False, pulseLength = 1):
    '''
    Generates and oversampled data prs according to the method described by
    Clowers and Belov -- designed for the ion funnel trap.

    Not quite right for a single pulse sequence.  Fails when the minimum pulse sequence
    does not exceed the oversampling of the system.
    '''
    sl=2**bit_shift-1 ##sl=sequence length
    osl=sl*oversampling ##osl=oversampling length
    prs_os=zeros(osl, dtype=int)
    prs=Sequence_Generator(bit_shift)
    n=0
    notes = ''
    if IFT:
        notes += '_IFT'
        if pulseLength>=oversampling:
            print "Pulse Length is >= Oversampling which doesn't jive."
            return False
        else:
            notes+='_PW%s'%pulseLength
            for i,j in enumerate(prs):
                if j == 1:
                    startInd = i*oversampling
                    prs_os[startInd:startInd+pulseLength] = 1


    else:        
        for i in xrange(0,osl-1,1):
            if(i%oversampling==0):
                prs_os[i:(i+oversampling)]=prs[n]
                n+=1

    if savePRS:
        if invert:
            prs_os = invertPRS(prs_os)
            notes+= "_%s"%(len(prs_os))
            notes += '_INV'
        else:
            notes+= "_%s"%(len(prs_os))
        savetxt("PRS_B%s_O%s%s.txt"%(bit_shift, oversampling, notes), prs_os, delimiter = ',', fmt = "%d,")

    return prs_os

def transformPRS(prs):
    '''
    Transforms the 0 and 1s hadamard sequence into a pulse sequence
    that has the pulse width instead of the 1/0 scheme.
    '''
    pulseSequence = zeros_like(prs)
    pulseCount = 0
    for i,p in enumerate(prs[::-1]):#reverse PRS to count backwards
        try:
            if p == 1:
                pulseCount += 1
            elif p == 0:
                if i>0:#accounting for first element being 0
                    pulseSequence[i-1] = pulseCount
                pulseCount = 0#reset count
        except:
            print "Not a pseudorandom sequence of 0 and 1's"
            raise
    return pulseSequence[::-1]#reverse to be in the forward direction (perhaps uncessary)

def invertPRS(prs):
    '''
    IRS signal is generated by doubling the PRBS and toggling every other digit of the doubled sequence.
    Srinvivasan Ind. Eg. Chem. Res 1999, 38, 3420-3429
    '''
    newSeq = zeros(len(prs)*2)
    newSeq[0:len(prs)]=prs
    for i,j in enumerate(prs):
        if i%2 == 0:
            if j == 0:
                newSeq[i] = 1
            elif j == 1:
                newSeq[i] = 0
            else:
                print "%s not 0 or 1"%j
    for m,n in enumerate(prs):
        val = newSeq[m]
        if val > 0:
            newSeq[m+len(prs)] = 0
        else:
            newSeq[m+len(prs)] = 1

    # return prs
    return newSeq

if __name__ == "__main__":
    import matplotlib.pyplot as P

    bit = 10
    overSampling = 1
    IFT = False
    pulseLength = 1
    newPRS = Generate_Oversampled_PRS_v2(bit, overSampling, savePRS = True, invert = False, IFT = IFT, pulseLength = pulseLength)
    prs = Generate_Oversampled_PRS_v2(bit, overSampling, savePRS = False, invert = False, IFT = False, pulseLength = pulseLength)
    note = 'Pulse B%s O%s PW%s'%(bit, overSampling, pulseLength)
    if IFT:
        note += " IFT"
    print "Number of 1s per pulse sequence: %d"%newPRS.sum()
    P.plot(newPRS, '-or', ms = 5,  label = note)
    P.plot(prs+1.25, '-og', ms = 5, label = 'Raw OS PRS')
    ax = P.gca()
    ax.legend()
    ax.set_ylim(-0.5, 2.5)
    P.show()





