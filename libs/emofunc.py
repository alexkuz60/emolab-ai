import os
import base64
import time
#import wave
#import struct

import numpy as np

import essentia
import essentia.standard

import dash
from dash import html#, dcc, callback, Input, Output
#from dash.exceptions import PreventUpdate
#import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
#from dash_iconify import DashIconify
import dash_player as dp

import plotly.express as px
import plotly.graph_objects as go

#import libs.emocomp as emocomp
import libs.emolist as emolist

UPLOAD_DIR = "./audio"
EXTRAS_DIR= "./extras"
DATAS_DIR = "./datas"

def getFileList(fullPathName=True):
    #List the files in the upload directory
    files_list = []
    for filename in os.listdir(UPLOAD_DIR):
        if fullPathName:
            filename = os.path.join(UPLOAD_DIR, filename)
        files_list.append(filename)
    return files_list

def getGrafsContainer(name, folder):
    file_npy = "./" + folder + "/" + name + ".npy"
    arrNpy=np.load(file_npy, allow_pickle=True)
    return arrNpy

def getGrafList(fullPathName=True):
    #List the files in the extras directory
    files_list = os.listdir(EXTRAS_DIR)
    if not os.listdir(EXTRAS_DIR):
        files_list = []
    else:
        for filename in files_list:
            if fullPathName:
                filename = os.path.join(EXTRAS_DIR, filename)
            files_list.append(filename)
    return files_list

def delResultFiles(del_list):
    for file in del_list:
        os.remove(os.path.join(UPLOAD_DIR, file))
        file +='.npy'
        os.remove(os.path.join(DATAS_DIR, file))
        os.remove(os.path.join(EXTRAS_DIR, file))

def saveResult(file, arrNP):
    np.save(os.path.join(DATAS_DIR, file + '.npy'), arrNP, allow_pickle=True)
    return True

def getEmoList(index):
    classificator = [emolist.emo_list7, emolist.emo_list8, emolist.emo_list14, emolist.emo_list16, emolist.emo_list28]
    emo = classificator[index]
    return emo

def getSectionHeader(text):
    hText = html.Div(
        [
            dmc.Space(h=10),
            dmc.Text(text, size=18, fw=700, c="lightgray", ta="right")
        ]
    )
    return hText

def rescaleArray(array, new_min, new_max):
    minimum, maximum = np.min(array), np.max(array)
    m = (new_max - new_min) / (maximum - minimum)
    b = new_min - m * minimum
    return m * array + b
#---------------------------------------------------
def seId(name):
    return name
#---------------------------------------------------
def getEmptyPlot(h):
    fig = go.Figure()
    fig.layout.template = 'plotly_dark'
    fig.update_layout(height=h, margin={"r":0,"t":40,"l":0,"b":0})
    return fig
#---------------------------------------------------
def getEmptyHistPlotPreviw():
    emo_bars = [i for i in range(28)]
    fig=go.Figure()
    fig.add_bar(y=emo_bars, showlegend=False, hovertext=emolist.emo_list28, opacity=0.25)
    fig.update_layout(
        showlegend=False,
        autosize=True,
        height=100,
        margin={"r":5,"t":0,"l":5,"b":0},
        xaxis_visible=False, yaxis_visible=False,
    )
    return fig   #---------------------------------------------------

def getEmptyCloudPlotPreviw():
    bw_sectors=[2*np.pi/8 for i in range(8)]
    r_dom = [(0.15+0.1*i) for i in range(8)]
    th = [2*i*np.pi/8 for i in range(8)]
    m_size =  [4+i for i in range(8)]
    fig=go.Figure()
    fig.add_pie(values=bw_sectors, showlegend=False, labels=emolist.bw_list,
        direction="counterclockwise", rotation=-360/8, hole=0.25, opacity=0.15)#
    fig.add_hline(0, opacity=0.25)
    fig.add_vline(0, opacity=0.25)
    fig.add_trace(go.Scatterpolar(
        r = r_dom,
        theta = th,
        thetaunit = 'radians',
        mode='markers',
        opacity=0.75,
        #name='EmoCloud',
        marker=dict(
            size=m_size,
            colorscale= 'hsv',
            color = th,
            showscale=False,
        )
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1.05])),
        #legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=False,
        autosize=True,
        #width=800,
        height=300,
        margin={"r":5,"t":0,"l":5,"b":0},
        xaxis_visible=False, yaxis_visible=False,
    )
    fig.update_polars(
        #selector="scatterpolar",
        angularaxis=dict(tickvals=emolist.emo_list8, tickmode="array", ticktext=emolist.emo_list8, visible=True),
        radialaxis=dict(tickvals=[0.25,0.5,0.75, 1.0], tickmode="array", ticktext=["", "", "", ""], visible=True)
    )
    return fig #---------------------------------------------------

#For audioPlayer: mp3/wav format of URL input file:
def write_contents_audio(contents, filename):
    data = contents.decode('utf-8')
    rawdata = data.split(',')[1]
    path_name = "./audio/" + filename
    fh = open(path_name, "wb")
    if 'mp3' in filename:
      fh.write(contents.decode('base64'))
    elif 'wav' in filename:
      fh.write(rawdata.decode('base64'))
    fh.close()
    return path_name
#--------------------------------------------------------
def getAudioUrl(file, file_path_name):
    url=None
    audio_data = base64.b64encode(open(file_path_name, 'rb').read())
    if 'mp3' in file:
        url = 'data:audio/mpeg;base64,{}'.format(audio_data.decode())
    elif 'wav' in file:
        #raw_data = audio_data.split(',')[1]
        url = 'data:audio/wav;base64,{}'.format(audio_data.decode())
    return url
#----------------------------------------------------------
def getAudioPlayer(Id, file, base_path):
    player = dp.DashPlayer(id=Id, controls=True, height=40)
    if file !="" and base_path=="fromfilelist":
        file_path_name = "./audio/"+file
        player = dp.DashPlayer(id=Id, controls=True, url=getAudioUrl(file, file_path_name), height=40, intervalCurrentTime=372)    #2**14/44100
    return player
#----------------------------------------------------------------------

def getProgressPlay(pos):
    return dmc.Progress(id='id-progress-play', value=pos, color="green")
#-----------------------------------------------------------------------

def sssaveNpyData(arrFigs, name, path, clearArr = True, rewriteSeg=False):
    # T/F: default, create new file or rewrite all for emo-analyzer, extras, vocal_tools
    # F/F: for extras append fig in [seg. inst, hit,...]
    # F/T: only foe extras - replace seg
    # T/T: not used
    start_time = time.time()
    outfile = "./" + path + "/" + name + ".npy"
    arrNpy=getGrafsContainer(outfile, "extras")
    if clearArr == True:
        arrNpy=np.array()
    arrNpy.append(arrFigs)#=np.array(figs, dtype=object)
    if rewriteSeg == True:
        arrNpy[0]=arrFigs
    np.save(outfile, arrNpy, allow_pickle=True)
    progressState=[20,30,30,0,0]
    nyp_time = time.time() - start_time
    return progressState, nyp_time
#---------------------------------------------------------------------------------------------------------------------

def saveDataAsNpy(fig, name, folder):
    start_time = time.time()
    outfile = "./"+folder+"/"+name+".npy"
    arrNpy=np.array(fig, dtype=object)
    np.save(outfile, arrNpy, allow_pickle=True)
    nyp_time = time.time() - start_time
    return nyp_time
#---------------------------------------------------------------------------------------------------------------------

def rewriteSegmentsAsNpy(fig, file):
    start_time = time.time()
    file_npy = "./extras/" + file + ".npy"
    figs=np.load(file_npy, allow_pickle=True)
    figs[0]=fig
    out_file_npy = "./extras/" + file
    np.save(file_npy, figs, allow_pickle=True)
    nyp_time = time.time() - start_time
    return nyp_time
#---------------------------------------------------------------------------------------------------------------------

def addToNpy(fig, name, folder):
    start_time = time.time()
    file_npy = "./" + folder + "/" + name + ".npy" #os.path.join(folder, name+'.npy')
    arrNpy=np.load(file_npy, allow_pickle=True)
    np.append(arrNpy, fig)
    np.save(file_npy, arrNpy, allow_pickle=True)
    nyp_time = time.time() - start_time
    return nyp_time
#---------------------------------------------------------------------------------------------------------------------
def getClickCoordinates(click_data: dict) -> tuple[int, int]:
        """
        function extracts information from a dictionary
        Parameters:
            click_data: dictionary which is return by the plotly-dash click event on a dcc.Graph
        Returns:
            x, y: coordinates of the click event
        """
        points = click_data.get('points')[0]
        x = points.get('x')
        y = points.get('y')
        return x, y