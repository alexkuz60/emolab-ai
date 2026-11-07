import os

import dash
from dash import dcc, html, callback, Input, Output, State, no_update, ctx
from dash.exceptions import PreventUpdate
#import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
#from plotly_resampler import FigureResampler

import essentia
import essentia.standard

import numpy as np
import libs.toolslib as toolslib
import libs.emocomp as emocomp
import libs.emofunc as emofunc
#-------------------------------------------------------------------------------------
dash.register_page(__name__, order=4)

audioFile = ''

fileSelector=emocomp.getFileSelector("id-tools-file-selector")

split_list = ["2: Vocal | Minus", "4: Vocal | Bass | Drums | Others"]#, "5: Vocal | Piano | Bass |Drums | Others"]
splitModeSelector=dmc.Select(
    placeholder="Select split mode..",
    data=split_list,
    value=split_list[0],
    id="id-split-mode-selector",
    leftSection=DashIconify(icon="vaadin:list-select", height=20, color="lightgray"),
    persistence="persisted",
    persistence_type="local",
    h=22,
    w=250
)

plotSplitVocal = dcc.Graph(id="id-plot-split-vocal", figure=emofunc.getEmptyPlot(h=300))
plotReverb = dcc.Graph(id="id-plot-reverb-dry", figure=emofunc.getEmptyPlot(h=200))
plotPitch = dcc.Graph(id="id-plot-pitch", figure=emofunc.getEmptyPlot(h=200))
plotVocalInstrument = dcc.Graph(id="id-plot-voc-inst", figure=emofunc.getEmptyPlot(h=200))

audioPlayer = emofunc.getAudioPlayer("id-tools-player", audioFile, "fromfilelist")

#===================================== UI ================================================
butUploader=emocomp.buttonUploader
butPlayPause=emocomp.butPlayPause
butStopRewind=emocomp.butStopRewind

progressProcess=html.Div(
    [
        # Mantine 7+: сегменты прогресса — отдельные ProgressSection внутри ProgressRoot.
        # Прежние striped=False/animate=False — значения по умолчанию, value=27 при
        # заданных sections игнорировался и в Mantine 6.
        dmc.ProgressRoot(
            [
                dmc.ProgressSection("AI model...", value=20, color="pink"),
                dmc.ProgressSection("Process...", value=50, color="grape"),
                dmc.ProgressSection("Graphs...", value=15, color="grape"),
                dmc.ProgressSection("Save results...", value=0, color="violet"), #for correct totaltime's process
                dmc.ProgressSection("OK! Total time:", value=0, color="violet"), #output message
            ],
            size="xl",
        ),
    ]
)

# dmc.Header в Mantine 7 удалён: фиксированная шапка страницы собирается Paper'ом
# (top=45 — прежний mt=45 под фиксированной шапкой приложения).
pageHeader=dmc.Paper(
    [
        dmc.Grid(
            #cols=3,
            children=[
                dmc.GridCol(html.Div(dmc.Group([fileSelector, butUploader], align='justify')), span=4),
                dmc.GridCol(
                    dmc.Group(
                    [
                        html.Div([audioPlayer], id="id-tools-player-container"),
                        butStopRewind, butPlayPause,
                    ],
                    align='justify'),
                span=7, offset=1,
                ),
            ],
        ),
    ],
    pos="fixed",
    top=45,
    left=0,
    right=0,
    h=40,
    radius=0,
    style={"zIndex": 100},
)

butSplit=dmc.Button(
    'Split',
    leftSection=DashIconify(icon="material-symbols:splitscreen-top-outline", height=22, color='gray'),
    variant="outline",
    n_clicks=0,
    id='id-but-split',
    color="gray"
)

butCalcReverb=dmc.Button(
    'Calc Reverb',
    leftSection=DashIconify(icon="ph:cell-signal-x-bold", height=22, color='gray'),
    variant="outline",
    n_clicks=0,
    id='id-but-calc-reverb',
    color="gray"
)

download_list = ["vocal", "drums", "bass", "others"]#"piano",
downloadSelector=dmc.Select(
    id="id-split-download-selector",
    placeholder="Select split track..",
    data=download_list,
    value=download_list[0],
    leftSection=DashIconify(icon="fa:download", height=20, color="lightgray"),
    h=22,
    w=250
)

iconContainer=dmc.Group(
    [
        dmc.ActionIcon(
            DashIconify(icon="fluent:mic-pulse-32-filled", color="red", height=28),
            variant="filled",
            id="id-icon-but-vocal"),
        dmc.ActionIcon(
            DashIconify(icon="game-icons:guitar-bass-head", height=28), #, color="yellow"
            id="id-icon-but-bass", variant="filled", disabled=True),
        dmc.ActionIcon(
            DashIconify(icon="game-icons:drum", height=28), #, color="yellow"
            id="id-icon-but-drums", variant="filled", disabled=True),
        dmc.ActionIcon(DashIconify(icon="entypo:sound-mix", color="lime", height=28),
            id="id-icon-but-other", variant="filled"),
    ],
    justify="center",
)

splitterHeader=html.Div(
     dmc.Grid(
        [
            dmc.GridCol(html.Div(dmc.Group([splitModeSelector, iconContainer, butSplit, butCalcReverb], align="justify")), span=5),
            dmc.GridCol(html.Div(dmc.Group([downloadSelector])), span=1, offset=6)
        ],
        align='justify',
     )
)

progressPlay=dmc.Progress(id='id-split-progress-play', value=0, color="green", ml=25)

accordionTools= dmc.Accordion(
    children=[
        dmc.AccordionItem(
            [
                dmc.AccordionControl(
                    children=[
                        dmc.Group(
                            [
                                "Splitter: Vocal | Accompaniment: drums | bass | other",
                                dmc.Space(h=20),
                                dmc.Divider(orientation="vertical", style={"height": 24}, size=2),
                                dmc.Space(h=20),
                                dmc.ActionIcon(DashIconify(icon="ph:cell-signal-x-bold", flip="horizontal",width=32), variant="subtle", color="gray"), # For rever
                                "Reverb | Dry ",
                                dmc.Space(h=20),
                                dmc.Divider(orientation="vertical", style={"height": 24}, size=2),
                                dmc.Space(h=20),
                                dmc.ActionIcon(DashIconify(icon="mingcute:mic-2-fill", width=32), variant="subtle", color="red"), # For voc
                                "Instrumental | Vocal",
                                dmc.ActionIcon(DashIconify(icon="openmoji:musical-keyboard", width=32), variant="subtle"),   # For instr
                                dmc.Space(h=20),
                                dmc.Divider(orientation="vertical", style={"height": 24}, size=2),
                                dmc.Space(h=20),
                                dmc.Text("Total time for process:", c="green", ta="right", id="id-acc-info"),
                            ],
                        ),
                    ],
                    icon=DashIconify(icon='material-symbols:splitscreen-top-outline', color='yellow', height=32, width=64)# For Splitter
                ),
                dmc.AccordionPanel(
                    [
                        splitterHeader,
                        dmc.Space(h=10),
                        progressProcess,
                        plotSplitVocal,
                        progressPlay,
                        emofunc.getSectionHeader("Vocal: Melody Pitch"),
                        plotPitch,
                        emofunc.getSectionHeader("Reverb | Dry in vocal track"),
                        plotReverb,
                        emofunc.getSectionHeader("Vocal | Instrumental in input track"),
                        plotVocalInstrument,         
                    ],
                ),
            ],
            value="val-split-vocal",
        ),
    ],
    id="id-acc-vocal-cplitter"
)

layout=html.Div(
    children=[
        pageHeader,
        dmc.Space(h=50),
        dcc.Download(id="id-split-download"),
        accordionTools,
    ],
    id="layout_tools",
)

@callback(
    Output("id-tools-player-container", "children"),
    #Input("id-uploader", "n_clicks"),
    Input("id-tools-file-selector", "value"),
    State("id-icon-but-vocal", "n_clicks"),
    State("id-icon-but-bass", "n_clicks"),
    State("id-icon-but-drums", "n_clicks"),
    State("id-icon-but-other", "n_clicks"),
)
def onSelectFileOrClickUpload(file, v, b, d, o):
    who_is = ctx.triggered_id
    if who_is == "id-tools-file-selector":
        return emofunc.getAudioPlayer("id-tools-player", file, "fromfilelist")
    else:
        if who_is == "id-icon-but-vocal":
            file = "vocal.wav"
        elif who_is == "id-icon-but-bass":
            file = "bass.wav"
        elif who_is == "id-icon-but-drums":
            file = "drums.wav"
        elif who_is == "id-icon-but-other":
            file = "other.wav"
        else:
            return emofunc.getAudioPlayer("id-tools-player", file,"fromfilelist")
#--------------------------------------------------

@callback(
    Output("id-icon-but-bass", "disabled"),
    Output("id-icon-but-drums", "disabled"),
    Input("id-split-mode-selector", "value")
)
def onSelectSplitModel(mode_split):
    n_split = int(mode_split[0])
    if n_split == 4:
        return False, False
    return True, True

@callback(
    Output("id-plot-split-vocal", "figure"),
    Output("id-plot-reverb-dry", "figure"),
    Output("id-plot-voc-inst", "figure"),
    Output("id-plot-pitch", "figure"),
    Output("id-acc-info", "children"),
    Input("id-but-split", "n_clicks"),
    State("id-tools-file-selector", "value"),
    State("id-split-mode-selector", "value"),
    #prevent_initial_call=True
)
def onOrClickButSplit(nclick, file, mode_split ):
    file_path_name = "./audio/"+file
    n_split = int(mode_split[0])
    fig_split, fig_rev, fig_inst, fig_pitch, total_time = toolslib.splitVocalMinus(file_path_name, n_split)
    return fig_split, fig_rev, fig_inst, fig_pitch, total_time
#--------------------------------------------------

@callback(
    Output("id-split-progress-play", "value"),
    Input("id-tools-player", "currentTime"),
    prevent_initial_call=True
)
def updateCurrentTime(val):
    return val
#--------------------------------------------------

@callback(
    Output("id-split-download", "data"),
    Input("id-split-download-selector", "value"),
    prevent_initial_call=True
)
def downloadSplitFile(fType):
    selected_file = "./temps/" + fType + ".wav"
    return dcc.send_file(selected_file)
#--------------------------------------------------
