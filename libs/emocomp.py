import os

import numpy as np
import pandas as pd

import essentia
import essentia.standard

import dash
from dash import dcc, html, callback, Input, Output
#import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

import plotly.express as px
import plotly.graph_objects as go

import libs.emolib as emolib
import libs.emolist as emolist
import libs.emofunc as emofunc

#================================COMPONENTS============================================
buttonUploader=dcc.Upload(
    dmc.Button(
        'Upload File',
        leftSection=DashIconify(icon="line-md:uploading-loop", height=32),
        variant="outline",
        n_clicks=0,
        id='but-upload',
    ),
    id='id-tools-uploader'
)

def getFileSelector(name):
    file_selector = dmc.Select(
        id=name,
        placeholder="Select audio file from list...",
        data=emofunc.getFileList(fullPathName=False),
        value=emofunc.getFileList(fullPathName=False)[0],
        leftSection=DashIconify(icon="fa6-solid:file-waveform", height=20, color="lightgray"),
        searchable=True,
        persistence="persisted",
        persistence_type="session",
        h=22,
        w=300
    )
    return file_selector

grafSelector=dmc.Select(
    placeholder="Select back graf...",
    data=emolist.plot_list,
    value=emolist.plot_list[0],
    id="graf-selector",
    leftSection=DashIconify(icon="lucide:file-bar-chart", height=20, color="lightgray"),
    h=22,
    w=150,
)

emoListSelector=dmc.Select(
    placeholder="Select Emo-classificator...",
    data=[" 7 emo categories"," 8 emo categories", "14 emo categories", "16 emo categories", "28 emo categories"],
    value="28 emo categories",
    id="emo-list-selector",
    leftSection=DashIconify(icon="fa6-solid:masks-theater", height=20, color="lightgray"),
    h=22,
    w=200,
)

butPlayPause=dmc.ActionIcon(DashIconify(icon="fluent:play-16-filled"),
    id="but-play-pause",
    color="blue", variant="outline", n_clicks=0, h=22, mt=6
)

butStopRewind=dmc.ActionIcon(DashIconify(icon="fluent:stop-16-filled"),
    id="but-stop-rewind", color="lime", variant="outline", n_clicks=0, h=22, mt=6
)

rangeSlider=dmc.Slider(
    id="id-range-slider",
    min=0, max=100, step=0.5, #minRange=0, , maxRange=100
    #updatemode="drag",
    value=0,
    marks=[
        {"value": 25, "label": "25%"},
        {"value": 50, "label": "50%"},
        {"value": 75, "label": "75%"},
    ],
    mt=10,
)

posZoomSlider = go.layout.xaxis.Rangeslider(
    autorange =False,
    visible=True,
    bgcolor="indigo",
    bordercolor="gray",
    range=[70, 207]
)

def getTemplateFigure2T(datas, labels):
    fig = go.Figure()
    mean0 = ": " + str(round(np.mean(datas[:,0]), 2))
    mean1 = ": " + str(round(np.mean(datas[:,1]), 2))
    fig.add_trace(go.Scatter(y=datas[:,0], line_shape='spline', mode='lines', fill='tozeroy', name=labels[0] + mean0))
    fig.add_trace(go.Scatter(y=datas[:,1], line_shape='spline', mode='lines', fill='tozeroy', name=labels[1] + mean1))
    fig.layout.template = 'plotly_dark'
    fig.layout.xaxis.title = "Time (sec.)"
    fig.update_traces(hoverinfo='text+name', mode='lines')
    fig.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=200,
        margin={"r":0,"t":40,"l":0,"b":0})
    return fig

def getProgressor(zones):
    # Mantine 7+: сегментированный прогресс собирается из ProgressRoot/ProgressSection,
    # прежний Progress(sections=..., value=...) больше не поддерживается (value и так
    # игнорировался, когда заданы sections)
    return dmc.ProgressRoot(
        [
            dmc.ProgressSection(zone["label"], value=zone["value"], color=zone["color"])
            for zone in zones
        ],
        id="id-seg_progress",
        size=16,
    )
