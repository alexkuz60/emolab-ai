import os
import dash
from dash import dcc, html, callback, Input, Output, State, no_update, Patch, ctx
#import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

import numpy as np
import libs.emocomp as emocomp
import libs.emofunc as emofunc
import libs.extraslib as extraslib

dash.register_page(__name__, opder=3)

audioFile=emofunc.getFileList(False)[0] #TODO: better are get from dcc.Store last value fileSelector
file_path_name = './audio/'+ audioFile
audioPlayer = emofunc.getAudioPlayer("id-extras-player", audioFile, "fromfilelist")

if os.path.exists(f"./extras/{audioFile}.npy"):
    savedPlots = emofunc.getGrafsContainer(audioFile, "extras")
    plotSegmentator = dcc.Graph(id="id-seg-plot", figure=savedPlots[0])
    plotStyle = dcc.Graph(id="id-plot-style", figure=savedPlots[1])
    plotInstrumentMap = dcc.Graph(id="id-plot-instr-map", figure=savedPlots[2])
    plotHit = dcc.Graph(id="id-plot-hit", figure=savedPlots[3])
    plotFor = dcc.Graph(id="id-plot-for", figure=savedPlots[4])
    plotEmo = dcc.Graph(id="id-plot-emo", figure=savedPlots[5])
else:
    plotSegmentator = dcc.Graph(id="id-seg-plot", figure=emofunc.getEmptyPlot(h=400))
    plotStyle = dcc.Graph(id="id-plot-style", figure=emofunc.getEmptyPlot(h=16*31))
    plotInstrumentMap = dcc.Graph(id="id-plot-instr-map", figure=emofunc.getEmptyPlot(h=16*40))
    plotHit = dcc.Graph(id="id-plot-hit", figure=emofunc.getEmptyPlot(h=300))
    plotFor = dcc.Graph(id="id-plot-for", figure=emofunc.getEmptyPlot(h=600))
    plotEmo= dcc.Graph(id="id-plot-emo", figure=emofunc.getEmptyPlot(h=300))
    
#=================================P=======PAGE HEADER==============================================
fileSelector=emocomp.getFileSelector("id-extras-file-selector")
#grafSelector=emocomp.grafSelector

butCalc = dmc.Button(
    'Calc',
    leftSection=DashIconify(icon="ant-design:calculator-outlined", height=24, color="gray"),
    variant="outline",
    color='gray',
    id='id-extras-but-calc',
)

butPlayPause=emocomp.butPlayPause
butStopRewind=emocomp.butStopRewind

zones=[ {"value": 25, "color": "pink", "label": "Segments.."},
        {"value": 25, "color": "grape", "label": "Instruments.."},
        {"value": 25, "color": "violet", "label": "Emotions.."},
        {"value": 25, "color": "violet", "label": "Styles.."}]
progressor=emocomp.getProgressor(zones)

# dmc.Header в Mantine 7 удалён: фиксированная шапка страницы собирается Paper'ом
# (top=45 — прежний mt=45 под фиксированной шапкой приложения).
pageHader=dmc.Paper(
    [
        dmc.Grid(
            #cols=3,
            children=[
                dmc.GridCol(html.Div(dmc.Group([fileSelector, butCalc])), span=4),
                dmc.GridCol(html.Div(dmc.Group([html.Div(audioPlayer, id="id-extras-player-container"), butStopRewind, butPlayPause ])), span=7, offset=1),
            ],
            align='justify',
        ),
        progressor,
    ],
    pos="fixed",
    top=45,
    left=0,
    right=0,
    h=40,
    radius=0,
    style={"zIndex": 100},
)

progressPlay=dmc.Progress(id='id-progress-play', value=0, color="green", ml=25)

#==================================LIBROSA SEGMENTATOR UI==================================
stepSelector=dmc.Select(
    id="id-seg-step-number",
    # Mantine 7+: значения Select — строки, поэтому число сегментов приводится к int в колбэках
    data=[{"label": str(n), "value": str(n)} for n in range(2, 10)],
    value="5",
    leftSection=DashIconify(icon="fluent:text-word-count-24-filled", height=20, color="gray"),
    h=24,
    w=60,
)

butSegRecalc = dmc.Button(
    'Recalc',
    leftSection=DashIconify(icon="ant-design:calculator-outlined", height=24, color="gray"),
    variant="outline",
    color='gray',
    id='id-but-seg-recalc',
)#---------------------------------------------------------------------------------------------

segmentatorMenu = dmc.Grid(
    justify='center',
    children=[
        dmc.GridCol(dmc.Group(
            [
                stepSelector,
                butSegRecalc,
            ],
                align='justify',
        ),
        span=2),
        dmc.GridCol(html.H6('', id="id-time-seg"), span=2, offset=8),
    ],
)#---------------------------------------------------------------------------------------------------

accItemSegmentator = dmc.AccordionItem(
    [
        dmc.AccordionControl(
            "Composition's Segmentator",
            icon=DashIconify(icon='ph:list-dashes-fill', rotate=1, color='yellow', height=32, width=32)  #123 fluent:text-word-count-24-filled
        ),
        dmc.AccordionPanel(
            [
                segmentatorMenu,
                dmc.Space(h=10),
                plotSegmentator,
                dmc.Space(h=10),
                progressPlay,
            ],
        )
    ],
    value="id-exras-segmentator",
)#---------------------------------------------------------------------------------------------------

#+++++++++++++++++++++++++++++++++++++++++STYLE MAPPER+++++++++++++++++++++++++++++++++++++++++++
styleMenu = dmc.Grid(
    justify='center',
    children=[
        dmc.GridCol(dmc.Group([
            "any comp"],
            align='justify',
            ),
        span=2),
        dmc.GridCol(html.H6('', id="id-style-map"), span=2, offset=8),
    ],
)#-----------------------------------------------------------------------------------------------

accItemStylyMap=dmc.AccordionItem(
    [
        dmc.AccordionControl(
            children=[dmc.Group(
                [
                    "Music Style Mapper",
                ]),
            ],
            icon=DashIconify(icon='fluent-emoji-high-contrast:saxophone', color='yellow', height=32, width=32) #for Mapper
        ),
        dmc.AccordionPanel(
            [
                dmc.Space(h=10),
                styleMenu,
                dmc.Space(h=10),
                plotStyle,
            ],
        )
    ],
    value="style-map"
)

#++++++++++++++++++++++++++++++++++++++++INSTRUMENT MAPPER+++++++++++++++++++++++++++++++++++++++++++
instrumentMenu = dmc.Grid(
    justify='center',
    children=[
        dmc.GridCol(dmc.Group([
            "any comp"],
            align='justify',
            ),
        span=2),
        dmc.GridCol(html.H6('', id="id-time-inst"), span=2, offset=8),
    ],
)#---------------------------------------------------------------------------------------------------

accItemInstrumentMap=dmc.AccordionItem(
    [
        dmc.AccordionControl(
            children=[dmc.Group(
                [
                    "Instrumental Mapper",
                ]),
            ],
            icon=DashIconify(icon='ph:list-dashes-fill', color='lime', height=32, width=32) #for Mapper
        ),
        dmc.AccordionPanel(
            [
                dmc.Space(h=10),
                instrumentMenu,
                dmc.Space(h=10),
                dmc.Space(h=10),
                plotInstrumentMap,
            ],
        )
    ],
    value="instrument-map",
)#-----------------------------------------------------------------------------------------------

#++++++++++++++++++++++++++++++++++++++++HIT-PREDICTOR+++++++++++++++++++++++++++++++++++++++++++
hitMenu = dmc.Grid(
    justify='center',
    children=[
        dmc.GridCol(dmc.Group([
            "any comp"],
            align='justify',
            ),
        span=2),
        dmc.GridCol(html.H6('', id="id-time-hit"), span=2, offset=8),
    ],
)#-----------------------------------------------------------------------------------------------

accItemHitPredictor=dmc.AccordionItem(
    [
        dmc.AccordionControl(
            children=[dmc.Group(
                [
                    "Hit Predictor",
                    dmc.Divider(orientation="vertical", color="lightgray", style={"height": 24}),
                    "Target Auditory Predictor: ",
                    dmc.ThemeIcon(DashIconify(icon="icon-park-solid:brain", width=20), variant="outline", color="pink"), # For Engagment
                    dmc.Divider(orientation="vertical", color="lightgray", style={"height": 24}),
                    dmc.ThemeIcon(DashIconify(icon="vaadin:group", width=20), variant="outline", color="yellow"), # MainStream
                    dmc.Divider(orientation="vertical", color="lightgray", style={"height": 24}),
                    dmc.ThemeIcon(DashIconify(icon="pepicons-pop:coctail-circle-filled", width=20), variant="outline", color="white"), # For Party
                ]),
            ],
            icon=DashIconify(icon="fluent-emoji-high-contrast:top-arrow", color='red', height=32, width=32) #for Hit
        ),
        dmc.AccordionPanel(
            [
                dmc.Space(h=10),
                hitMenu,
                dmc.Space(h=10),
                plotHit,
                dmc.Space(h=10),
                plotFor
            ],
        )
    ],
    value="hit-predictor"
)#-----------------------------------------------------------------------------------------------

#++++++++++++++++++++++++++++++++++++++++COMPATIVE EMO-ANALYZER++++++++++++++++++++++++++++++++++
accItemEmoAnalyzer=dmc.AccordionItem(
    [
        dmc.AccordionControl(
            children=[dmc.Group(
                [
                    "Comparative AI EmoAnalyzer",
                ]),
            ],
            icon=DashIconify(icon='eos-icons:ai', color='lightblue', height=32, width=32) #for Mapper
        ),
        dmc.AccordionPanel(
            [
                dmc.Space(h=10),
                instrumentMenu,
                dmc.Space(h=10),
                plotEmo,
            ],
        )
    ],
    value="emo-analyser"
)

#+++++++++++++++++++++++++++++++++++++++++++PAGE LAYOUT++++++++++++++++++++++++++++++++++++++++++++++++++
layout = html.Div(
    children=[
        pageHader,
        dmc.Space(h=50),
        dmc.Accordion(
            children=[
                accItemSegmentator,
                accItemStylyMap,
                accItemInstrumentMap,
                accItemHitPredictor,
                accItemEmoAnalyzer,
            ],
        ),
    ]
)

@callback(
    Output("id-seg-plot", "figure", allow_duplicate=True),
    Output("id-plot-style", "figure"),
    Output("id-plot-instr-map", "figure"),
    Output("id-plot-hit", "figure"),
    Output("id-plot-for", "figure"),
    Output("id-plot-emo", "figure"),
    #Output("id-progressor-extra", "value"),
    Output("id-extras-player-container", "children"),
    Input("id-extras-but-calc", "n_clicks"),
    Input("id-extras-file-selector", "value"),
    State("id-seg-step-number", "value"),
    prevent_initial_call=True
)
def calcAllExtras(nclick, file, n_seg):
    n_seg = int(n_seg) # Select в Mantine 7+ возвращает значение строкой
    if ctx.triggered_id == "id-extras-file-selector":
        if os.path.exists(f"./extras/{file}.npy"):
            figs = emofunc.getGrafsContainer(file, "extras")
        else:
            figs = extraslib.calcExtras(file, n_seg)
            #emofunc.getProgressor(zones, i*10)
    elif ctx.triggered_id == "id-extras-but-calc":
        figs = extraslib.calcExtras(file, n_seg)
        #emofunc.getProgressor(zones, i*10)
    player=emofunc.getAudioPlayer("id-extras-player", file, "fromfilelist")
    return figs[0], figs[1], figs[2], figs[3], figs[4], figs[5], player

#=============================SEGMENTATOR===================================
@callback(
    Output("id-but-seg-recalc", "children"),
    Output("id-extras-file-selector", "value"),
    Input("id-seg-step-number", "value"),
    State("id-extras-file-selector", "value"),
    #prevent_initial_call=True
)
def onChangeNumSegOrRefreshPage(n_seg, val):
    but_label = "Recalc: " + str(n_seg)
    return but_label, val

#------------------------------PlayerProgress-------------------------
@callback(
    Output("id-progress-play", "value"),
    Input("id-extras-player", "currentTime"),
    prevent_initial_call=True
)
def updatePlayerCurrentTime(val):
    return val

#-----------------------------Recalc Segmentator-----------------------
@callback(
    Output("id-seg-plot", "figure", allow_duplicate=True),
    Input("id-but-seg-recalc", "n_clicks"),
    State("id-extras-file-selector", "value"),
    State("id-seg-step-number", "value"),
    prevent_initial_call=True
)
def onButRecalcSeg(click_recalc, file, n_seg):
    file_path_name = "./audio/"+file
    fig_seg = extraslib.calcLaplacianSegmentation(file_path_name, int(n_seg))
    emofunc.rewriteSegmentsAsNpy(fig_seg, file)
    return fig_seg#, time_seg
