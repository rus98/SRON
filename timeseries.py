import pickle
import numpy as np
import matplotlib.pyplot as plt
from sron_toolbox import * 
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import rgb2hex, Normalize
import datetime as dt
import math
from pylab import *
import json
import collections as col
from scipy.optimize import minimize
from Regions import *
import ast
import os
from matplotlib import gridspec
import matplotlib.cm as cm

#from pklload2 import *

####### Functions
#Import data from pkl file
def importdata(start_mjd, end_mjd, region):
    #dictionary
    codata = {'mjd':[], 'co':[], 'samplesize':[], 'lon_con':[], 'lat_con':[]}
    for i in range(start_mjd,end_mjd):
        try:
            #set folder name here
            pklfile = open('test_india/operational_gridded_0.25x0.25_test/'+region.get('name')+'/yearly/'+str(i)+'-'+str(i+1)+'_co.pkl')
            data = pickle.load(pklfile)
            co = data['co_column']*6.022141e19
#            print co
            co = col2vmr(co, data['surface_pressure'],is_profile=False)*1e9
#            print co
            co = np.ma.masked_where(co<0.,co)

            codata['co'].append(co)
            #print np.ma.mean(co[np.where(co>0)])
            #sample size is number of data points in region in a particular day
            codata['samplesize'].append(len(co[~np.isnan(co)]))
            dates = data.get('mjd')[~np.isnan(data.get('mjd'))]
            codata['mjd'].append(floor(np.mean(dates)))
#            #date as day of the year starting from 1
#            codata['date'].append(i+1-start_mjd)
            codata['lon_con'].append(data.get('lon_con'))
            codata['lat_con'].append(data.get('lat_con'))
            co = None
            dates = None
            #codata['date'].append(mjd2utc(int(np.mean(dates[~np.isnan(dates)])))['day'])
        except:
            pass
#    print codata['co']
    return codata

def readgfas(start_mjd, end_mjd, region, polygon):
    y0, m0, d0 = mjd2date(start_mjd).year, mjd2date(start_mjd).month, mjd2date(start_mjd).day
    y1, m1, d1 = mjd2date(end_mjd-1).year, mjd2date(end_mjd-1).month, mjd2date(end_mjd-1).day

    rowmin = (90-region.get('latmax'))*10
    rowmax = (90-region.get('latmin'))*10
    colmin = region.get('longmin')*10
    colmax = region.get('longmax')*10
    mjd = start_mjd
    m = m0
    gfasmonthly = []
    months = []
    monthlystd = []
    while m < m1+1:
        with open('gfas_india2/gfas_'+str(y0)+str(m)+'.json', 'r') as f:
            gfasd = json.load(f)
            gfasmonthly.append(np.array(gfasd['data']))
        f.close()
        months.append((y0,m))
        m+=1
    gfasmonthly[0], gfasmonthly[-1] = gfasmonthly[0][d0-1:], gfasmonthly[-1][:d1]
    for i in range(len(gfasmonthly)):
        print len(gfasmonthly[i])

    lats = np.flipud(np.arange(region.get('latmin'), region.get('latmax'), 0.1))
    lons = np.arange(region.get('longmin'), region.get('longmax'), 0.1)
    mask = np.zeros(np.shape(gfasmonthly[0][0]))
    gfasmonthlymask = []
    gfasmonthlysum = []
    gfasdaily = []
    for i in range(len(lats)):
        for j in range(len(lons)):
            if point_in_poly(lons[j], lats[i], polygon['coordinates']) == False:
                mask[i][j] = 1
#    imshow(mask)
#    show()
    for month in range(len(gfasmonthly)):
        monthly = []
        for day in range(gfasmonthly[month].shape[0]):
            gfasmask = np.ma.masked_array(gfasmonthly[month][day], mask=mask)
            gfasmonthlymask.append(gfasmask)
            gfasdaily.append(np.sum(gfasmask)/10**9)
            monthly.append(np.sum(gfasmask)/10**9)
        monthlystd.append(np.sqrt(np.var(monthly)*len(monthly)))
        gfasmonthlysum.append(sum(monthly))
    mjdlist = range(start_mjd, end_mjd)
    print 'GFAS MJD ', len(mjdlist), len(gfasdaily)
    gfasdates = []
    for i in mjdlist:
        gfasdates.append(dt.date(mjd2utc(i)['year'], mjd2utc(i)['month'], mjd2utc(i)['day']))
    print gfasdates[0], gfasdates[-1]
    return mjdlist, gfasdates, gfasdaily, months, gfasmonthly, monthlystd

def readgfed(start_mjd, end_mjd, region, polygon):
    y0, m0, d0 = mjd2date(start_mjd).year, mjd2date(start_mjd).month, mjd2date(start_mjd).day
    y1, m1, d1 = mjd2date(end_mjd-1).year, mjd2date(end_mjd-1).month, mjd2date(end_mjd-1).day
    mjd = start_mjd
    gfedmonthly = []
    monthlystd = []
    months = []
    m=m0
    while m<m1+1:
        with open('gfed_india2/gfed__'+str(y0)+str(m)+'.json', 'r') as f:
            gfedd = json.load(f)
            gfedmonthly.append(np.array(gfedd['data']))
        f.close()
        months.append((y0,m))
        m+=1
    gfedmonthly[0], gfedmonthly[-1] = gfedmonthly[0][d0-1:], gfedmonthly[-1][:d1]
    lats = np.flipud(np.arange(region.get('latmin'), region.get('latmax'), 0.25))
    lons = np.arange(region.get('longmin'), region.get('longmax'), 0.25)
    mask = np.zeros(np.shape(gfedmonthly[0][0]))
    gfedmonthlymask = []
    gfedmonthlysum = []
    gfeddaily = []
    for i in range(len(lats)):
        for j in range(len(lons)):
            if point_in_poly(lons[j], lats[i], polygon['coordinates']) == False:
                mask[i][j] = 1
#    imshow(mask)
#    show()
    for i in range(len(gfedmonthly)):
        monthly = []
        for j in range(gfedmonthly[i].shape[0]):
            gfedmask = np.ma.masked_array(gfedmonthly[i][j], mask=mask)
            gfedmonthlymask.append(gfedmask)
            monthly.append(np.sum(gfedmask)/10**12)
            gfeddaily.append(np.sum(gfedmask)/10**12)#*region.get('area'))
        monthlystd.append(np.sqrt(np.var(monthly)*len(monthly)))
        gfedmonthlysum.append(sum(monthly))
    
    mjdlist = range(start_mjd, end_mjd)
    gfeddates = []
    for i in mjdlist:
        gfeddates.append(dt.date(mjd2utc(i).get('year'), mjd2utc(i).get('month'), mjd2utc(i).get('day')))
    return mjdlist, gfeddates, gfeddaily, months, gfedmonthlysum, monthlystd

def readviirs(start_mjd, end_mjd, polygon):
    with open('viirs.json', 'r') as f:
        viirsd = json.load(f)
    try:
        i0, i1 = viirsd['mjd'].index(start_mjd), viirsd['mjd'].index(end_mjd)
    except:
        i0, i1 = viirsd['mjd'].index(min(viirsd['mjd'])), viirsd['mjd'].index(end_mjd)
    mjdlist = viirsd['mjd'][i0:i1]
    frpdaily = np.array(viirsd['frp'][i0:i1])
    coords = np.array(viirsd['coords'][i0:i1])
#    for j in range(len(coords)):
#        for i in range(len(coords[j])):
#            plt.scatter(coords[j][i][0], coords[j][i][1])
#    plt.show()
    frpmean = []
#    mask = np.copy(frpdaily)
    viirsregion = []
#    print frpdaily
    for i in range(len(frpdaily)):
        frpday = []
        for j in range(len(frpdaily[i])):
            if point_in_poly(coords[i][j][0], coords[i][j][1], polygon['coordinates']) == True:
                frpday.append(frpdaily[i][j])
#                plt.scatter(coords[i][j][0], coords[i][j][1])
        frpmean.append(sum(frpday)/1000000.)
        del frpday
#    plt.show()
    viirsdates = []
    for i in mjdlist:
        viirsdates.append(dt.date(mjd2utc(i).get('year'), mjd2utc(i).get('month'), mjd2utc(i).get('day')))
#    mjdlist = range(start_mjd, end_mjd)
#    frpdailymask = np.ma.MaskedArray(frpdaily, mask=mask)
#    frpmean = []
#    for i in range(len(frpdailymask)):
#        frpmean.append(np.sum(frpdailymask[i]))

    return mjdlist, viirsdates, frpmean

def readsage(start_mjd, end_mjd, region, polygon):
    y0, m0, d0 = mjd2date(start_mjd).year, mjd2date(start_mjd).month, mjd2date(start_mjd).day
    y1, m1, d1 = mjd2date(end_mjd-1).year, mjd2date(end_mjd-1).month, mjd2date(end_mjd-1).day
    mjd = start_mjd
    sagemonthly = []
    sagemonthlysum = []
    monthlystd = []
    mjdlist = range(start_mjd, end_mjd)
    months = []
    m=m0
    while m<m1+1:
        try:
            with open('sage_india2/sage_'+str(y0)+str(m)+'.json', 'r') as f:
                saged = json.load(f)
#                saged = ast.literal_eval(json.dumps(saged))
                sagemonthly.append((saged))
            f.close()
#            mjdlist+=sagemonthly[-1]['mjdlist']
            months.append((y0,m))
            m+=1
#            y, m = mjd2date(mjd).year, mjd2date(mjd).month
        except:
            m+=1
#            y, m = mjd2date(mjd).year, mjd2date(mjd).month
#    print 'SAGE ', mjdlist == range(start_mjd, end_mjd)
    lats = np.array(sagemonthly[0]['lats'])
    lons = np.array(sagemonthly[0]['lons'])
    for i in range(len(sagemonthly)):
        sagemonthly[i] = np.array(sagemonthly[i]['data'])
    sagemonthly[0], sagemonthly[-1] = sagemonthly[0][d0-1:], sagemonthly[-1][:d1]

    mask = np.zeros(np.shape(sagemonthly[0][0]))
    sagemonthlymask = []
    sagedaily = []
    
    for i in range(len(lats)):
        for j in range(len(lons)):
            if point_in_poly(lons[j], lats[i], polygon['coordinates']) == False:
                mask[i][j] = 1

    for month in range(len(sagemonthly)):
        monthly = []
        for day in range(sagemonthly[month].shape[0]):
            sagemask = np.ma.masked_array(sagemonthly[month][day], mask=mask)
            sagemonthlymask.append(sagemask)
            sagedaily.append(np.sum(sagemask)/10**9)
            monthly.append(np.sum(sagemask)/10**9)
        monthlystd.append(np.sqrt(np.var(monthly)*len(monthly)))
        sagemonthlysum.append(sum(monthly))

    sagedates = []
    for i in mjdlist:
        sagedates.append(dt.date(mjd2utc(i)['year'], mjd2utc(i)['month'], mjd2utc(i)['day']))
    print 'SAGE ',len(sagedates), len(sagedaily)
    return mjdlist, sagedates, sagedaily, months, sagemonthlysum, monthlystd

def readwrf(start_mjd, end_mjd, region, polygon):
    y0, m0, d0 = mjd2date(start_mjd).year, mjd2date(start_mjd).month, mjd2date(start_mjd).day
    y1, m1, d1 = mjd2date(end_mjd-1).year, mjd2date(end_mjd-1).month, mjd2date(end_mjd-1).day
    mjd = start_mjd
    wrfmonthly = []
    wrfmonthlysum = []
    EGmonthlystd = []
    Gmonthlystd = []
    mjdlist = range(start_mjd, end_mjd)
    months = []
    m=m0
    edgargfed = {'monthly':[], 'daily':np.zeros(len(mjdlist))}
    gfed = {'monthly':[], 'daily':np.zeros(len(mjdlist))}
    edgar = {'monthly':[], 'daily':np.zeros(len(mjdlist))}
    U = {'monthly':[], 'daily':np.zeros(len(mjdlist))}
    V = {'monthly':[], 'daily':np.zeros(len(mjdlist))}

    while m<m1+1:
        try:
            with open('wrf_india2_injectionheight7x2/wrf_'+str(y0)+str(m)+'.json', 'r') as f:
                wrfd = json.load(f)
                wrfmonthly.append((wrfd))
            f.close()
            #mjdlist+=wrfmonthly[-1]['mjdlist']
            months.append((y,m))
#        print m
            m+=1
#            y, m = mjd2date(mjd).year, mjd2date(mjd).month
        except:
            m+=1
#            y, m = mjd2date(mjd).year, mjd2date(mjd).month
#    print np.shape(wrfmonthly[0]['edgargfed'])
    lats = np.array(wrfmonthly[0]['lats'])
    lons = np.array(wrfmonthly[0]['lons'])
#    print wrfmonthly[-1].keys()
    for i in range(len(wrfmonthly)):
        edgargfed['monthly'].append(wrfmonthly[i]['edgargfed'])
        gfed['monthly'].append(wrfmonthly[i]['gfed'])
        edgar['monthly'].append(wrfmonthly[i]['edgar'])
        U['monthly'].append(wrfmonthly[i]['u'])
        V['monthly'].append(wrfmonthly[i]['v'])
#    for i in range(len(U['monthly'][0])):
#        print U['monthly'][0][i][80][60], V['monthly'][0][i][80][60]
        
    for d in [edgargfed, gfed, edgar, U, V]:
        d['monthly'][0],d['monthly'][-1] = d['monthly'][0][d0-1:],d['monthly'][-1][:d1]
        d['monthly'] = np.array(d['monthly'])
#    print np.shape(U['monthly'][2])
        #d['monthly'] = d['monthly'][date:]

    mask = np.zeros(np.shape(edgargfed['monthly'][0][0]))
    #EGmonthlymask = []
    #Gmonthlymask = []
    #Emonthlymask = []
#    print 'len LONS ', len(lons)
#    print 'len LATS ', len(lats)
    for i in range(len(lats)):
        for j in range(len(lons)):
            if point_in_poly(lons[j], lats[i], polygon['coordinates']) == False:
                mask[i][j] = 1
#            else:
#                print j,i
    #imshow(mask)
    count = 0
    for d in [edgargfed, gfed, edgar, U, V]:
        for month in range(len(d['monthly'])):
            #monthly = []
            for day in range(np.shape(d['monthly'][month])[0]):
                datamask = np.ma.masked_array(d['monthly'][month][day], mask=mask)
                d['daily'][count]=np.mean(datamask)

                #monthly.append(np.mean(datamask))
                count+=1
            #d['monthlystd'].append(np.sqrt(np.var(monthly)*len(monthly)))
            #d['monthlysum'].append(np.mean(monthly))
#        print d['daily']
#        d['daily'] = np.ma.masked_where(d['daily']<0.0001, d['daily'])
        count = 0
#    for k in range(len(U['daily'])):
#        print U['daily'][k], V['daily'][k]
#    print gfed['daily']
    wrfdates = []
    for i in mjdlist:
        wrfdates.append(dt.date(mjd2utc(i)['year'], mjd2utc(i)['month'], mjd2utc(i)['day']))
    edgargfed['dates'], gfed['dates'], edgar['dates'] = wrfdates, wrfdates, wrfdates
#    wrfdaily = np.ma.masked_where(wrfdaily<0.1, wrfdaily)
#    print wrfdaily
#    print wrfdaily.mask
#    print np.shape(wrfdaily)
#    print wrfdates
    return mjdlist, months, edgargfed, gfed, edgar, U, V

def daily(codata):   
    comean = []
    cosum = []
    for i in range(len(codata.get('comask'))):
        x = codata.get('comask')[i]
        x = x[~np.isnan(x)]
        comean.append(np.ma.mean(x))
        cosum.append(np.sum(x))
        del x
    return comean, cosum

#Convert day of the year to date
def seq2date(dates, y0):
    datelist = []
    for i in range(len(dates)):
        datelist.append(dt.date(y0,01,01) + dt.timedelta(dates[i]-1))
    return datelist

def mjd2date(mjd):
    return dt.date(mjd2utc(mjd).get('year'), mjd2utc(mjd).get('month'), mjd2utc(mjd).get('day'))
    
#Daily, weekly, monthly average time series
def series(codata, y0, minpoints):
    codaily = []
    codailysum = []
    datelist = []
#    codaily = np.zeros((len(codata.get('co'))))
#    datelist = np.zeros((len(codata.get('co'))))
    mjdlist = []
    #print datelist
    for i in range(len(codata.get('dailymean'))):
        #Set minimum 'sample size' of daily data to 20
        if codata.get('samplesize')[i]>np.size(codata.get('co')[i])*minpoints:
            if type(codata.get('dailymean')[i]) != np.float64:
                pass
            else:
                codaily.append(codata.get('dailymean')[i])
                codailysum.append(codata.get('dailytotal')[i])
                datelist.append(mjd2date(codata.get('mjd')[i]))
                mjdlist.append(codata.get('mjd')[i])
#                print datelist[-1], codaily[-1]
#    print type(codata.get('dailymean')[i])
    weeklist = [dt.date(y0, 01, 01)]
#    print weeklist
#    print datelist
    coweekly = []
    while weeklist[-1]<datelist[-1]-dt.timedelta(14):
        weeklist.append(weeklist[-1]+dt.timedelta(7))
    for i in range(len(weeklist)):
        co_week = []
        for j in range(len(codaily)):
            if datelist[j]-weeklist[i] > dt.timedelta(0) and datelist[j]-weeklist[i] < dt.timedelta(8):
                co_week.append(codaily[j])
        coweekly.append(mean(co_week))
        co_week = None
    monthlist = [dt.date(y0, 01, 15)]
    while monthlist[-1]<datelist[-1]-dt.timedelta(15):
        monthlist.append(monthlist[-1]+dt.timedelta(30))
    comonthly = []
    for i in range(len(monthlist)):
        co_month = []
        for j in range(len(codaily)):
            if datelist[j].year == monthlist[i].year and datelist[j].month == monthlist[i].month:
                co_month.append(codaily[j])
        comonthly.append(mean(co_month))
        co_month= None
        
    return datelist, codaily, weeklist, coweekly, monthlist, comonthly, codailysum, mjdlist

def normalize(array):
    mi = np.min(array)
    array = array-np.min(array)
    array = array/np.max(array)
    return array

def regionfilter(codata, polygon):
    lats = np.array(codata['lat_con'])
    lons = np.array(codata['lon_con']) 
#    print lats[0].shape
#    print lats[0][1][1]
#    for i in range(len(lats)):
#        for j in range(lats[0].shape[0]):
#            for k in range(lats[0].shape[1]):
#                lats[i][j][k]=np.mean(lats[i][j][k])
#                lons[i][j][k]=np.mean(lons[i][j][k])
    co = np.array(codata['co'])
    mask = np.zeros(np.shape(co))
    for i in range(lats.shape[0]):
        for j in range(lats.shape[1]):
            for k in range(lats.shape[2]):
                if point_in_poly(lons[i][j][k][0], lats[i][j][k][0], polygon['coordinates']) == False:
                    mask[i][j][k] = 1
    comask = np.ma.masked_array(co,mask=mask)
#    imshow(mask[0])
#    show()
    codata['comask']=comask
    return codata

def globarea(im=360,jm=180,silent=True):
    deg2rad = np.pi/180.
    radius  = 6.371e6
    dxx=360.0/im*deg2rad
    dyy=180.0/jm*deg2rad
    lat=np.arange(-90*deg2rad,90*deg2rad,dyy)
    dxy=dxx*(sin(lat+dyy)-sin(lat))*radius**2
    area=np.resize(np.repeat(dxy,im,axis=0) ,[jm,im])
    if not silent:
        print 'total area of field = ',sum(area.flat)
        print 'total earth area    = ',4*pi*radius**2
    return area

def runningmean(x, N):
    avg = np.convolve(x, np.ones((N,))/N, mode='valid')
    return avg 
#    cumsum = np.cumsum(np.insert(x, 0, 0)) 
#    return (cumsum[N:] - cumsum[:-N]) / float(N)

def total(season, data, mjdlist):
    print season
    start_mjd, end_mjd = seasons[season]['start_mjd'], seasons[season]['end_mjd']
#    start_mjd, end_mjd = int(utc2mjd(y0, m0, d0, 0, 0, 0)), int(utc2mjd(y1, m1, d1, 0, 0, 0))
    try:
        i0, i1 = mjdlist.index(start_mjd), mjdlist.index(end_mjd)
    except:
        mjddiff = [abs(mjdlist[i]-start_mjd) for i in range(len(mjdlist))]
        i0 = mjdlist[mjddiff.index(min(mjddiff))]  
        mjddiff = [abs(mjdlist[i]-end_mjd) for i in range(len(mjdlist))]
        i1 = mjdlist[mjddiff.index(min(mjddiff))]
#    print len(data), len(mjdlist)
    try:
        totalco = sum(data[i0:i1])
#        print max(data[i0:i1])
        var = np.var(data[i0:i1])*(i1-i0)
        std = np.sqrt(var)
    except:
        totalco = 0
        std = 0
    return totalco, std

def bargraph(seasons, ylabels, ylist, stdlist):
    n = float(len(ylist))
    x = np.arange(len(seasons))  # the label locations
    width = 0.3  # the width of the bars
    fig, ax = plt.subplots()
    bars = []
    ax.bar(x-width*1.5, ylist[0], width, yerr=stdlist[0], color='r', label=ylabels[0])
    ax.bar(x-width*0.5, ylist[1], width, yerr=stdlist[1], color='b', label=ylabels[1])
    print [len(ylist[i]) for i in range(len(ylist))]
    ax.bar(x+width*0.5, ylist[2], width, yerr=stdlist[2], color='k', label=ylabels[2])
    #ax.bar(x+width, ylist[3], width, yerr=stdlist[3], color='m', label=ylabels[3])
#    for i in range(int(n)):
#        bar = ax.bar(x-width/n, ylist[i], width, label=ylabels[i])
#        bars.append(bar)
    ax.set_ylabel('Fires Emission (GFAS, GFED, SAGE), Tg of CO')
    ax.set_title('Emissions Products, '+str(polygon['name']))
    ax.set_xticks(x)
#    plt.yticks(np.arange(0, 0.7, 0.05))
    ax.set_xticklabels(seasons)
#    ax2 = ax.twinx()
#    ax2.bar(x+width, ylist[3], width, yerr=stdlist[3], color='m', label=ylabels[3])
#    ax2.set_ylabel('Fires Emission (VIIRS), FRP in TW')
    ax.legend(loc='upper right')
#    ax2.legend(loc='upper right')
#    for bar in bars:
#        autolabel(bar)
    fig.tight_layout()
    plt.show()
#    plt.savefig('barplot_'+str(polygon), dpi=150)
#    plt.close()

def bar_states(polygonlist, seasons, statenames):
    gfassumlist = []
    gfasstdlist = []
    gfedsumlist = []
    gfedstdlist = []
    sagesumlist = []
    sagestdlist = []
    for k in range(len(polygonlist)):
        gfasmjd, gfasdates, gfas = readgfas(start_mjd, end_mjd, region, polygonlist[k])
        gfedmjd, gfeddates, gfed = readgfed(start_mjd, end_mjd, region, polygonlist[k])
        sagemjd, sagedates, sage = readsage(start_mjd, end_mjd, region, polygonlist[k])
        gfassum = []
        gfasstd = []
        gfedsum = []
        gfedstd = []
        sagesum = []
        sagestd = []
        for i in range(5):
            for j in range(len(seasons)):
                if seasons[seasons.keys()[j]]['name']==str(i):
                    gfassum.append(total(seasons.keys()[j], gfas, gfasmjd)[0])
                    gfasstd.append(total(seasons.keys()[j], gfas, gfasmjd)[1])
                    gfedsum.append(total(seasons.keys()[j], gfed, gfedmjd)[0])
                    gfedstd.append(total(seasons.keys()[j], gfed, gfedmjd)[1])
                    sagesum.append(total(seasons.keys()[j], sage, sagemjd)[0])
                    sagestd.append(total(seasons.keys()[j], sage, sagemjd)[1])
        gfassumlist.append(gfassum)
        gfasstdlist.append(gfasstd)
        gfedsumlist.append(gfedsum)
        gfedstdlist.append(gfedstd)
        sagesumlist.append(sagesum)
        sagestdlist.append(sagestd)
    gfassumlist = np.array(gfassumlist)
    gfasstdlist = np.array(gfasstdlist)
    gfedsumlist = np.array(gfedsumlist)
    gfedstdlist = np.array(gfedstdlist)
    sagesumlist = np.array(sagesumlist)
    sagestdlist = np.array(sagestdlist)
    x = np.arange(len(polygonlist))
    width = 0.1  # the width of the bars
    fig, (ax1,ax2,ax3) = plt.subplots(3,1)
    bars = []
    seasonnames = ['2017 SOND', '2018 MAMJ', '2018 SOND', '2019 MAMJ', '2019 SOND']
    colours = ['b', 'g', 'y', 'r', 'm']
    for i in range(5):
        r, g, b = 0.1, 0.1, 0.1
        ax1.bar(x-0.25+width*i, gfassumlist[:,i], width, yerr=gfasstdlist[:,i],ecolor='k', color=(0.1,0.3,0.8,0.15+float(i)/7.), label=seasonnames[i])
        ax2.bar(x-0.25+width*i, gfedsumlist[:,i], width, yerr=gfedstdlist[:,i],ecolor='k',color=(0.3,0.8,0.4,0.15+float(i)/7.), label=seasonnames[i])
        ax3.bar(x-0.25+width*i, sagesumlist[:,i], width, yerr=sagestdlist[:,i],ecolor='k',color=(0.9,0.3,0.2,0.15+float(i)/7.), label=seasonnames[i])

    ax1.set_ylabel('GFAS, Tg of CO')
    ax2.set_ylabel('GFED, Tg of CO')
    ax3.set_ylabel('SAGE, Tg of CO')
    ax1.set_ylim(0,0.7)
    ax2.set_ylim(0,0.7)
    ax3.set_ylim(0,0.7)
    ax1.set_title('Emissions Products')
    ax1.set_xticks(x)
    ax2.set_xticks(x)
    ax3.set_xticks(x)
#    plt.yticks(np.arange(0, 0.7, 0.05))
    ax1.set_xticklabels(statenames)
    ax2.set_xticklabels(statenames)
    ax3.set_xticklabels(statenames)
    ax1.legend(loc='upper right')
    ax2.legend(loc='upper right')
    ax3.legend(loc='upper right')
    plt.show()
    
def bar_months(metric):
    fig, (ax1,ax2) = plt.subplots(2,1)
    sumlist, sumlist2 = [], []
    stdlist, stdlist2 = [], []
    for k in range(len(polygonlist)):
        gfedmjd, gfeddates, gfed, gfedmonths, gfedsum, gfedmonthlystd = readgfed(start_mjd, end_mjd, region, polygonlist[k])
        gfed_dict = {'mjd': gfedmjd, 'dates': gfeddates, 'daily':gfed, 'months':gfedmonths, 'monthly':gfedsum, 'monthlystd':gfedmonthlystd}
        sumlist.append(gfed_dict['monthly'][6:10])
        sumlist2.append(gfed_dict['monthly'][18:22])
        stdlist.append(gfed_dict['monthlystd'][6:10])
        stdlist2.append(gfed_dict['monthlystd'][18:22])

    #months = metric['months']
    #totals = metric['monthly']
    #stdlist = metric['monthlystd']
    x = np.arange(len(sumlist[0]))
    print len(polygon), len(sumlist[0])
    sumlist = np.array(sumlist)
    stdlist = np.array(stdlist)
    labels = ['Punjab(Pak)', 'Punjab(Ind)', 'Haryana', 'Uttar Pradesh', 'Bihar']
    monthlist = ['March','April','May','June']
    bars = []
    colours = ['b', 'g', 'y', 'r', 'm']
    width = 0.1
    for i in range(len(sumlist)):
        ax1.bar(x-0.25+width*i, sumlist[i,:], width, yerr=stdlist[i,:], ecolor='k',color=colours[i], label=labels[i])
    #ax.bar(x-width*0.5, ylist[1], width, yerr=stdlist[1], color='b', label=ylabels[1])
    #print [len(ylist[i]) for i in range(len(ylist))]
    #ax.bar(x+width*0.5, ylist[2], width, yerr=stdlist[2], color='k', label=ylabels[2])
    #ax.bar(x+width, ylist[3], width, yerr=stdlist[3], color='m', label=ylabels[3])
#    for i in range(int(n)):
#        bar = ax.bar(x-width/n, ylist[i], width, label=ylabels[i])
#        bars.append(bar)
    ax1.set_ylabel('Fires Emission (GFED), Tg of CO')
    ax1.set_title('Emission 2018 Pre-Monsoon')
    ax1.set_xticks(x)
#    plt.yticks(np.arange(0, 0.7, 0.05))
    ax1.set_xticklabels(monthlist)
#    ax2 = ax.twinx()
#    ax2.bar(x+width, ylist[3], width, yerr=stdlist[3], color='m', label=ylabels[3])
#    ax2.set_ylabel('Fires Emission (VIIRS), FRP in TW')
    ax1.legend(loc='upper right')

    #months = metric['months']
    #totals = metric['monthly']
    #stdlist = metric['monthlystd']
    x = np.arange(len(sumlist2[0]))
    print len(polygon), len(sumlist2[0])
    sumlist = np.array(sumlist2)
    stdlist = np.array(stdlist2)
    bars = []
    for i in range(len(sumlist)):
        ax2.bar(x-0.25+width*i, sumlist[i,:], width, yerr=stdlist[i,:], ecolor='k',color=colours[i], label=labels[i])
    ax2.set_ylabel('Fires Emission (GFED), Tg of CO')
    ax2.set_title('Emission 2019 Pre-Monsoon')
    ax2.set_xticks(x)
#    plt.yticks(np.arange(0, 0.7, 0.05))
    ax2.set_xticklabels(monthlist)
#    ax2.legend(loc='upper right')
#    for bar in bars:
#        autolabel(bar)
    
    fig.tight_layout()
    plt.show()
#    plt.savefig('barplot_'+str(polygon), dpi=150)
#    plt.close()
    
def seasonfilter(season, data, dates):
    start_mjd = season['start_mjd']
    end_mjd = season['end_mjd']+1
    start, end = mjd2date(start_mjd), mjd2date(end_mjd)
    while start not in dates:
        start_mjd+=1
        start = mjd2date(start_mjd)
    while end not in dates:
        end_mjd+=1
        end = mjd2date(end_mjd)
#    print start, end
    i0, i1 = dates.index(start), dates.index(end)
    data = data[i0:i1]
    dates = dates[i0:i1]
    return data, dates

def lobf(x, y):
    xfit = np.array([np.min(x), np.max(x)])
   ## print len(x), len(y)
    coeffs = np.polyfit(x,y,1)
    yfit = xfit*coeffs[0]+coeffs[1]
    return xfit.tolist(), yfit.tolist()

############ Main
#Set dates, region+polygon, switches
#Set it to either SOND or MAMJ if looking at SAGE or WRF
y0, m0, d0 = 2018, 9, 10
y1, m1, d1 = 2018, 12, 20
corr0, corr1 = 0, -1
region = india2
polygon = haryana #igp3, punjab_pak, punjab_ind, haryana, up, or bihar
#directory to write output within deos/rushilv
dirname = '13June03/'
#Switches
runningmean_key = True
sage_key = True
gfas_key = True
gfed_key = True
#lobf key sets a line of best fit on correlation plot
lobf_key = True
tropomi_key = True
wrf_key = True
period = 3

start_mjd = int(utc2mjd(y0, m0, d0, 0, 0, 0))
end_mjd = int(utc2mjd(y1, m1, d1, 0, 0, 0))+1

polygonlist = [punjab_pak, punjab_ind, haryana, up, bihar]
statenames = ['Punjab (Pak)', 'Punjab (Ind)', 'Haryana', 'Uttar Pradesh', 'Bihar']

area = globarea(3600,1800)
#minimum number of data points in frame (0-->1)
minpoints = 0.0
codata = importdata(start_mjd, end_mjd, region)
codata = regionfilter(codata, polygon)
codata['dailymean'], codata['dailytotal'] = daily(codata)[0], daily(codata)[1]
datelist, codaily, weeklist, coweekly, monthlist, comonthly, codailysum, comjd = series(codata,y0,minpoints)
print 'co series done' 

if m0 < 7 or y0 < 2018:
    sage_key = False

#viirsmjd, viirsdates, viirs = readviirs(start_mjd, end_mjd, polygon)
gfasmjd, gfasdates, gfas, gfasmonths, gfassum, gfasmonthlystd = readgfas(start_mjd, end_mjd, region, polygon)
gfedmjd, gfeddates, gfeddata, gfedmonths, gfedsum, gfedmonthlystd = readgfed(start_mjd, end_mjd, region, polygon)
if sage_key == True:
    sagemjd, sagedates, sage, sagemonths, sagesum, sagemonthlystd = readsage(start_mjd, end_mjd, region, polygon)

wrfmjd, wrfmonths, edgaremis, emission, edgar, U, V = readwrf(start_mjd, end_mjd, region, polygon)
#print edgargfed['daily']

gfas_dict = {'mjd': gfasmjd, 'dates': gfasdates, 'daily':gfas, 'months':gfasmonths, 'monthly':gfassum, 'monthlystd':gfasmonthlystd}
gfed_dict = {'mjd': gfedmjd, 'dates': gfeddates, 'daily':gfeddata, 'months':gfedmonths, 'monthly':gfedsum, 'monthlystd':gfedmonthlystd}
if sage_key:
    sage_dict = {'mjd': sagemjd, 'dates': sagedates, 'daily':sage, 'months':sagemonths, 'monthly':sagesum, 'monthlystd':sagemonthlystd}

#edgargfed['daily'] = edgargfed['daily'].tolist()
datemask = np.zeros(np.shape(edgaremis['daily']))
for d in [edgaremis, emission, edgar, U, V]:
    d['daily']=d['daily'].tolist()

#loop to make sure all daily series have same dates
stop = False
while not stop:
    #for d in [edgargfed, gfed, edgar]:
        #d['daily'] = d['daily'].tolist()
    for date in emission['dates']:
        if date not in datelist:
            print 'wrf ', date
            datemask[emission['dates'].index(date)]=1
            if sage_key:
                for dataset in [edgaremis, edgar, U, V, gfas_dict, gfed_dict, sage_dict]:
                    dataset['daily'].remove(dataset['daily'][emission['dates'].index(date)])
            else:
                for dataset in [edgaremis, edgar, U, V, gfas_dict, gfed_dict]:
                    dataset['daily'].remove(dataset['daily'][emission['dates'].index(date)])
            emission['daily'].remove(emission['daily'][emission['dates'].index(date)])
            emission['dates'].remove(date)
    for date in datelist:
        if date not in emission['dates']:
            print 'codate ', date
            codaily.remove(codaily[datelist.index(date)])
            datelist.remove(date)
    stop = len(datelist)==len(emission['dates'])==len(codaily)==len(gfas_dict['daily'])
    print len(datelist), len(emission['dates']), len(codaily), len(gfas_dict['daily'])

edgaremis['dates']=emission['dates']
edgar['dates']=emission['dates']
U['dates']=emission['dates']
V['dates']=emission['dates']
gfas_dict['dates']=emission['dates']
gfed_dict['dates']=emission['dates']
if sage_key:
    sage_dict['dates']=emission['dates']

wrflist = [edgaremis, emission, edgar, U, V, gfas_dict, gfed_dict]
if sage_key:
    wrflist.append(sage_dict)

codaily = np.ma.masked_where(codaily<1, codaily)
for d in wrflist:
    d['daily']=np.array(d['daily'])

#print np.isnan(gfed['daily'])
edgaremis['daily']=np.ma.masked_where(edgaremis['daily']<1, edgaremis['daily'])
edgar['daily']=np.ma.masked_where(edgar['daily']<1, edgar['daily'])
emission['daily']=np.ma.masked_where(emission['daily']<1, emission['daily'])

wrfmask = edgaremis['daily'].mask+edgar['daily'].mask+emission['daily'].mask
if runningmean_key:
    codaily = runningmean(np.ma.masked_array(codaily,mask=wrfmask),period)
    datelist = datelist[int(math.floor(period/2.)):int(-math.floor(period/2.))]
else:
    codaily = np.ma.masked_array(codaily,mask=wrfmask)

windx = [utc2mjd(datelist[i].year, datelist[i].month, datelist[i].day,0,0,0) for i in range(len(datelist))]
m = windx[0]
windx = [windx[i]-m for i in range(len(windx))]

corr0_date = datelist[0]
corr1_date = datelist[-1]

print len(gfas_dict['dates']), len(gfas_dict['daily'])
count = 1
for d in wrflist:
    if runningmean_key:
        d['daily'] = runningmean(np.ma.masked_array(d['daily'],mask=wrfmask), period)
        d['dates'] = d['dates'][int(math.floor(period/2.)):int(-math.floor(period/2.))]

    else:
        d['daily'] = np.ma.masked_array(d['daily'],mask=wrfmask)
    count+=1

edgaremis['r2'] = np.ma.corrcoef(edgaremis['daily'], codaily)[0,1]
emission['r2'] = np.ma.corrcoef(emission['daily'], codaily)[0,1]
edgar['r2'] = np.ma.corrcoef(edgar['daily'], codaily)[0,1]

print 'period = ', period, ', edgar+emission r2 = ', edgaremis['r2']

if m0>7:
    filename = polygon['filename']+'_'+str(y0)+'_sond_'+str(period)+'day'
    if runningmean_key:
        seriestitle = polygon['name']+', SOND '+str(y0)+' ['+str(period)+' day avg]'
        corrtitle=polygon['name']+', '+str(corr0_date)+' to '+str(corr1_date)+' ['+str(period)+' day avg]'
    else:
        seriestitle = polygon['name']+', SOND '+str(y0)
        corrtitle = polygon['name']+', '+str(corr0_date)+' to '+str(corr1_date)
else:
    filename = polygon['filename']+'_'+str(y0)+'_mamj'
    if runningmean_key:
        seriestitle = polygon['name']+', MAMJ '+str(y0)+' ['+str(period)+' day avg]'
        corrtitle=polygon['name']+', '+str(corr0_date)+' to '+str(corr1_date)+' ['+str(period)+' day avg]'
    else:
        seriestitle = polygon['name']+', MAMJ '+str(y0)
        corrtitle = polygon['name']+', '+str(corr0_date)+' to '+str(corr1_date)

if lobf_key:
    x1,y1 = lobf(edgar['daily'], codaily)
    x2,y2 = lobf(emission['daily'], codaily)
    x3,y3 = lobf(edgaremis['daily'], codaily)

fig,ax = plt.subplots(figsize=(10,7))
ax.scatter(edgar['daily'], codaily, color='crimson', label=r'EDGAR, $R^2 = $'+str(round(edgar['r2'],2)))
ax.plot(x1,y1, color='crimson')
ax.scatter(emission['daily'], codaily, color=(0.1,0.1,0.5), label=r'GFED $R^2 = $'+str(round(emission['r2'],2)))
ax.plot(x2,y2, color=(0.1,0.1,0.5))
ax.scatter(edgaremis['daily'], codaily, color='orange', label=r'EDGAR+GFED, $R^2 = $'+str(round(edgaremis['r2'],2)))
ax.plot(x3,y3, color='gold')
ax.set_xlabel('WRF CO [ppb]',fontsize='x-large')
ax.set_ylabel('TROPOMI CO [ppb]',fontsize='x-large')
ax.set_ylim(0,200)
ax.set_xlim(0,200)
ax.legend(loc='upper right',fontsize='x-large')
ax.set_title(corrtitle,fontsize='x-large')
fig.tight_layout()
#CHANGE DIRECTORY NAME
if not os.path.isdir('/deos/rushilv/WRFvTROP/'+dirname):
    os.mkdir('/deos/rushilv/WRFvTROP/'+str(dirname))
    os.mkdir('/deos/rushilv/WRFvTROP/'+str(dirname)+'Correlations/')
    os.mkdir('/deos/rushilv/WRFvTROP/'+str(dirname)+'Series/')
    os.mkdir('/deos/rushilv/WRFvTROP/'+str(dirname)+'Compass/')
plt.savefig(filename='/deos/rushilv/WRFvTROP/'+dirname+'Correlations/'+filename+'.png')
plt.savefig(filename='/deos/rushilv/WRFvTROP/'+dirname+'Correlations/'+filename+'.pdf')
plt.close()
    
if wrf_key:
    fig,(ax1,ax4) = plt.subplots(2,1,figsize=(13,10),gridspec_kw={'height_ratios':[2.5,1]})
else:
    fig,ax1 = plt.subplots(figsize=(13,7.14))
windx, windy = np.array(windx), np.ones(len(U['daily']))*1.5
windx = windx*13./np.max(windx)
if wrf_key:
    ax4.quiver(windx, windy, U['daily'], V['daily'], scale=7, width=0.003, headwidth=3)
    ax4.axis([0,13,0,3])
    ax4.set_yticklabels([])
    ax4.set_xticklabels([])
    if runningmean_key:
        ax4.set_ylabel('Wind Direction [3 day avg]', fontsize='x-large')
    else:
        ax4.set_ylabel('Wind Direction', fontsize='x-large')

ax1.plot(datelist, codaily, marker='.', color='g', label='TROPOMI')
ax1.set_title(seriestitle,fontsize='x-large')
ax1.set_ylabel('Average CO [ppb]', fontsize='x-large')
#ax1.set_xticks([i.month for i in datelist[::30]])
plt.yticks(fontsize='x-large')
ax1.set_xticks(datelist[::10])
ax1.set_xticklabels([d.strftime('%b')+' '+d.strftime('%d') for d in datelist[::10]],fontsize='x-large')

if gfed_key or gfas_key:
    ax2 = ax1.twinx()
    ax2.set_ylabel('Fires', fontsize='x-large')
    ax2.set_ylim(0,0.1)
    ax2.legend(loc='upper right')

print len(gfas_dict['dates']), len(gfas_dict['daily'])
if wrf_key:
    ax1.plot(edgar['dates'], edgar['daily'], marker='.', color='crimson', label='WRF (EDGAR)')
    if sage_key:
        ax1.plot(emission['dates'], emission['daily'], marker='.', color=(0.1,0.1,0.5), label='WRF (SAGE)')
        ax1.plot(edgaremis['dates'], edgaremis['daily'], marker='.', color='orange', label='WRF (EDGAR+SAGE)')
    else:
        ax1.plot(emission['dates'], emission['daily'], marker='.', color=(0.1,0.1,0.5), label='WRF (GFED)')
        ax1.plot(edgaremis['dates'], edgaremis['daily'], marker='.', color='gold', label='WRF (EDGAR+GFED)')

ax1.set_ylim(0,200)
ax1.legend(loc='upper left')
#ax3 = ax1.twinx()
#ax3.set_ylabel('GFED [Tg of CO]')
#ax2.plot(viirsdates, viirs, color='m', label='VIIRS [FRP in TW]')
if gfas_key:
    ax2.plot(gfas_dict['dates'], gfas_dict['daily'], color='m', label='GFAS [Tg of CO]')
if gfed_key:
    ax2.plot(gfed_dict['dates'], gfed_dict['daily'], color='b', label='GFED [Tg of CO]')
if sage_key:
    ax2.plot(sage_dict['dates'], 2*sage_dict['daily'], color='k', label='SAGE [Tg of CO]')
ax2.legend(loc='upper right')
fig.tight_layout()
#CHANGE DIRECTORY NAME
fig.savefig(filename='/deos/rushilv/WRFvTROP/'+dirname+'Series/'+filename+'_series_wrf.pdf')
fig.savefig(filename='/deos/rushilv/WRFvTROP/'+dirname+'Series/'+filename+'_series_wrf.png')
plt.close()

theta = np.zeros(np.shape(V['daily']))
for i in range(len(V['daily'])):
    if V['daily'][i] > 0 and U['daily'][i] > 0:
        theta[i] = np.arctan(V['daily'][i]/U['daily'][i])*180./np.pi
    elif V['daily'][i] < 0 and U['daily'][i] > 0:
        theta[i] = 360+np.arctan(V['daily'][i]/U['daily'][i])*180./np.pi
    elif V['daily'][i] < 0 and U['daily'][i] < 0:
        theta[i] = 180+np.arctan(V['daily'][i]/U['daily'][i])*180./np.pi
    elif V['daily'][i] > 0 and U['daily'][i] < 0:
        theta[i] = 180+np.arctan(V['daily'][i]/U['daily'][i])*180./np.pi

theta = theta*np.pi/180.

fig = plt.figure(figsize=(10.5,7))
ax = fig.add_subplot(111,projection='polar')
ax.set_xticklabels(['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE'], fontsize='large')
ax.set_ylim(70,170)
ax.set_title('Wind vs TROPOMI CO [ppb] ('+str(period)+' day avg), '+polygon['name']+', '+str(datelist[0])+':'+str(datelist[-1]), fontsize='x-large')
#x0,x1,x2,x3 = datelist[0], sage_dict['dates'][0], datelist[-1], sage_dict['dates'][-1]
if sage_key:
    plt.scatter(theta, codaily,c=sage_dict['daily'],linewidths=0, s=45, cmap='viridis')
else:
    plt.scatter(theta, codaily,c=gfed_dict['daily'],linewidths=0, s=45, cmap='viridis')

cbar = plt.colorbar()
plt.clim(0,0.032)
if sage_key:
    cbar.ax.text(4,0.67,'SAGE emissions [Tg]', rotation = 270,fontsize='x-large')
else:
    cbar.ax.text(4,0.67,'GFED emissions [Tg]', rotation = 270,fontsize='x-large')

#fig.tight_layout()
#ax.legend(loc='upper right')
#CHANGE DIRECTORY NAME
fig.savefig(filename='/deos/rushilv/WRFvTROP/'+dirname+'Compass/'+filename+'_wind.png')
fig.savefig(filename='/deos/rushilv/WRFvTROP/'+dirname+'Compass/'+filename+'_wind.pdf')
plt.close()

