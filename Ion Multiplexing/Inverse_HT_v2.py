#!/usr/bin/env python
'''
Copyright 2013  Brian Clowers bhclowers <at> gmail.com

Inverse_HT_v2.py is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Inverse_HT_v2.py is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Inverse_HT_v2.py.  If not, see <http://www.gnu.org/licenses/>.
'''
from matplotlib import use
try:
    use("QT4Agg")
except:
    use("TkAgg")
import numpy as N
import PRS_Generator as PRS
import matplotlib.pyplot as P
import os

__author__ = "Brian H. Clowers"
__copyright__ = "Copyright 2013, Brian H. Clowers"
__credits__ = ["Harwitt and Sloane appendix.  Steve Massick for pushing me towards the Hadamard technique."]
__license__ = "GPL 2.0"
__version__ = "1.0"
__maintainer__ = "Brian Clowers"
__email__ = "bhclowers <at> gmail.com"
__status__ = "Beta"


def Generate_Inverse_Sequence(prs):##prs=pseudo random sequence
    ##sl=sequence length of the PRS
    sl=len(prs)
    inv_prs=N.zeros(sl*2, float)
    ##wf=weighting factor for inverse transform
    wf=2/(float(sl)+1)#get reference for this 09/05/2013 BHC
    # print wf
    for i in range(sl):
        if(prs[i]==0):
            inv_prs[i]=-1*wf
            inv_prs[i+sl]=-1*wf
        elif(prs[i]>0):
            inv_prs[i]=1*wf
            inv_prs[i+sl]=1*wf

    return inv_prs



def Sample_OS_Data_Vector(sl,os,os_raw_data):##sl=prs length, os=oversampling
    '''Samples an oversampled data set and places the individual sets in
    the appropriate column for future transformation'''
    parsed_raw_data=N.zeros((os,sl), float)##creates a 20 by 31 array
    for i in range(sl):
        for n in range(os):
            parsed_raw_data[n,i]=os_raw_data[((i*os)+n)]

    return parsed_raw_data


def Inverse_Transform_1D(raw_data, bit_shift, os, fitArray = None):
    scaleOK = False #used to scale the inverting sequencing
    if fitArray != None:
        if len(fitArray) == os:
            scaleOK = True
            print "scaleOK: ", scaleOK
    sl=(2**bit_shift)-1
    HT_result=N.zeros(sl*os, float)
    temp_inv_vector=N.zeros(sl, float)
    parsed_raw_data=Sample_OS_Data_Vector(sl,os,raw_data)
    inv_prs=Generate_Inverse_Sequence(PRS.Sequence_Generator(bit_shift))
    for i in range(os):
        temp_raw_data=parsed_raw_data[i,:]##selects just a single column of the parsed array
        for j in range(sl):
            start_point=sl-j
            for k in range(sl):
                temp_inv_vector[k]=inv_prs[start_point+k]
            if scaleOK:
                scaleFactor = fitArray[i]
                HT_result[((j*os)+i)]=N.dot(temp_inv_vector*scaleFactor,temp_raw_data)
            else:
                HT_result[((j*os)+i)]=N.dot(temp_inv_vector,temp_raw_data)
    return HT_result

def normalize(vector):
    vector/=vector.max()
    vector*=100
    return vector

def quickTransform(fileName, bit, overSampling):
    import scipy.ndimage as im
    
    f = open(fileName, 'r')
    lines = f.readlines()
    f.close()
        
    x = N.array(lines, dtype = float)
    gx = N.arange( -10, 10)

    smoothData = True
    if smoothData:
        '''A median filter appears to work well for removing signal spikes (e.g. gating) in ion mobility spectra acquired with a Faraday plate'''
        x= im.median_filter(x, 15) 

    plotRaw = True

    resultFileName = fileName.split(".")[0]
    resultFileName += '_Transform.csv'
    ans = Inverse_Transform_1D(x,bit,overSampling, None)
    N.savetxt(resultFileName, ans, delimiter = ',', fmt = '%.6f')
    P.plot(normalize(ans)+10, 'ro-', ms = 3, label = "Inverse Transform", alpha = 0.5)

    if plotRaw:
        P.plot(normalize(x)*-1, 'gs-', ms = 3, label = "Untransformed")
        

    ax = P.gca()
    if len(x) >= 3000:
        ax.set_xlim(0, 3000)
    ax.set_title(fileName)
    ax.legend()
    newFile = fileName.split('.')[0]
    newFile += '.png'
    P.savefig(newFile)
    P.show()

if __name__ == "__main__":
    '''
    The quickTransform call takes a 1D vector of raw signal along with the 
    appropriate parameters of the pseudorandom sequence used to modulate the 
    original signal.  
    '''
    quickTransform("LPIMS_8Bit_OS20_10ms_25Aves.txt",8,20)
