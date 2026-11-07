import dash
from dash import dcc, html, callback, Input, Output, State, Patch, ctx, no_update
#import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

#import essentia.standard
#import numpy as np
#import pandas as pd
#import plotly.express as px
#import plotly.graph_objects as go

#import libs.emolist as emolist
import libs.emolib as emolib
import libs.emocomp as emocomp
import libs.emofunc as emofunc

dash.register_page(__name__, name="analyzer", order=2)

#For loading page audio:
audio_file = emofunc.getFileList(fullPathName=False)[0]#''#1zappa.mp3
file_path_name = "./audio/" + audio_file
#audio_url = emolib.getAudioUrl(audio_file, file_path_name)

saved_plots = emofunc.getGrafsContainer(audio_file, "datas")
plotAudio = dcc.Graph(figure=saved_plots[0], id="id-plot-audio")
plotWave = dcc.Graph(figure=saved_plots[1], id='id-plot-wav')
plotChordMap = dcc.Graph(figure=saved_plots[2], id='id-plot-chord-map')
plotBW = dcc.Graph(figure=saved_plots[3], id="id-plot-bw")
plotHistBW = dcc.Graph(figure=saved_plots[4], id="id-plot-hist-bw")
plotTempoMap = dcc.Graph(figure=saved_plots[5], id="id-plot-tempo-map")
plotEmoHist = dcc.Graph(figure=saved_plots[6], id="id-plot-emo-hist")
plotEmogram = dcc.Graph(figure=saved_plots[7], id="id-plot-emogram")
plotNPES = dcc.Graph(figure=saved_plots[8], id="id-plot-npes")
plotCloud = dcc.Graph(figure=saved_plots[9], id="id-plot-cloud")
plotEmoStar = dcc.Graph(id="id-plot-star", figure=saved_plots[10],
    config=dict(displaylogo=False),
    animate=True, animation_options={'frame': {'redraw': True}})
plotDance = dcc.Graph(figure=saved_plots[11], id="id-plot-dance")
plotRMS = dcc.Graph(figure=saved_plots[12], id='id-plot-rms')

#==========================================UI-PAGE-HEADER=======================================================
fileSelector=emocomp.getFileSelector("id-analyzer-file-selector")

audioPlayer = emofunc.getAudioPlayer("id-analyzer-player", audio_file, "fromfilelist")
progressor = dmc.Progress(id='id-play-progress', value=0, color="green")

butRecalc = dmc.Button("Recalc", leftSection=DashIconify(icon="fluent:tag-question-mark-20-filled"),
    id="id-but-recalc", color="gray", variant="outline")

# dmc.Header в Mantine 7 удалён: фиксированная шапка страницы собирается Paper'ом.
# top=50 — прежний mt=50, которым шапка страницы отодвигалась под фиксированную шапку приложения.
pageHeader=dmc.Paper(
    [
        dmc.Divider(size=2, color="indigo", opacity=0.25, top=1),
        dmc.Grid(
            children=[
                dmc.GridCol(html.Div(dmc.Group([fileSelector, emocomp.emoListSelector, butRecalc], align='justify')), span=5),
                dmc.GridCol(html.Div(dmc.Group([html.Div(audioPlayer, id="id_play-container"), emocomp.butStopRewind, emocomp.butPlayPause,])), span=7) #w=span+offset
            ],
            h=55,
        ),
        plotAudio,
        dmc.Space(h=-55),
        progressor,
    ],
    pos="fixed",
    top=50,
    left=0,
    right=0,
    h=200,
    radius=0,
    style={"zIndex": 100},
)

#==========================================UI-PAGE-TABS=======================================================
def setTabEmo():
    tab=dmc.TabsPanel(
        children=[
            dmc.Space(h=10),
            html.H6("Emo Histogram:"),
            plotEmoHist, #fig_emo_hist
            dmc.Space(h=10),
            html.H6("Dynamic Emogram:"),
            plotEmogram, #fig_emogram
            dmc.Space(h=10),
            html.H6("Positive/Negatine & Exaltation/Supression:"),
            plotNPES,   #fig_np & #fig_es 
            dmc.Space(h=10),
            html.H6("Brain Waves Stimuls:"),
            plotBW,   #fig_bw
        ],
        id="id-tab-emo",
        value="tab-emo"
    )
    return tab

tab_emo = setTabEmo()

def setTabMusic():
    tab=dmc.TabsPanel(
        children=[
            # AccordionMultiple в Mantine 7 заменён на Accordion(multiple=True)
            dmc.Accordion(
                multiple=True,
                children=[
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                "Wave Signal:",
                                icon=DashIconify(
                                    icon="mdi:waveform",
                                    color=dmc.theme.DEFAULT_THEME["colors"]["blue"][6],
                                    width=24,
                                ),
                            ),
                            dmc.AccordionPanel([plotWave]),  #
                        ],
                        value="acc-wave-signal",
                    ),
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                "Chords Map:",
                                icon=DashIconify(
                                    icon="cib:apple-music",
                                    color=dmc.theme.DEFAULT_THEME["colors"]["lime"][6],
                                    width=24,
                                ),
                            ),
                            dmc.AccordionPanel([plotChordMap]),  #
                        ],
                        value="acc-chord-map",
                    ),
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                "Tempo Deviation:",
                                icon=DashIconify(
                                    icon="mdi:tempo",
                                    color=dmc.theme.DEFAULT_THEME["colors"]["yellow"][6],
                                    width=24,
                                ),
                            ),
                            dmc.AccordionPanel([plotTempoMap]),   #fig_tempo
                        ],
                        value="acc-tempo",
                    ),
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                "Danceability:",
                                icon=DashIconify(
                                    icon="fluent:brain-circuit-24-filled",
                                    color=dmc.theme.DEFAULT_THEME["colors"]["pink"][6],
                                    width=24,
                                ),
                            ),
                            dmc.AccordionPanel([plotDance]),  #fig_dance
                        ],
                        value="acc-bw_dynamic",
                    ),
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl(
                                "RMS & Loadness:",
                                icon=DashIconify(
                                    icon="material-symbols:mindfulness-rounded",
                                    color="red",
                                    width=24,
                                ),
                            ),
                            dmc.AccordionPanel([plotRMS]), #fig_rms
                        ],
                        value="acc-bw_hist",
                    ),
                ],
            ),
        ],
        id="id-tab-music",
        value="tab-music",
    )
    return tab

tab_music = setTabMusic()

def setTabStar():
    tab=dmc.TabsPanel(
        [
            dmc.Grid(
                children=[
                    dmc.GridCol(plotEmoStar, span=5),
                    dmc.GridCol(plotHistBW, span=2),    #fig_bw_hist
                    dmc.GridCol(plotCloud, span=5),   #fig_cloud
                ],
            )
        ],
        id="id-tab-star",
        value="tab-star"
        #pb="xs",
    )
    return tab

tab_star=setTabStar()

tabsContent=html.Div(id="tabs-content", style={"paddingTop": 10})

tabs_all=dmc.Tabs(
    children=[
        dmc.TabsList(
            [
                dmc.TabsTab("Emograms",
                    leftSection=DashIconify(
                        icon="mdi:tag-emoji",
                        color=dmc.theme.DEFAULT_THEME["colors"]["yellow"][6],
                        width=32),
                    value="tab-emo"
                    ),
                dmc.TabsTab("Musical Extras",
                    leftSection=DashIconify(
                        icon="fluent-emoji-high-contrast:musical-notes",
                        color=dmc.theme.DEFAULT_THEME["colors"]["green"][6],
                        width=32),
                    value="tab-music"),
                dmc.TabsTab("Emo Star",
                    leftSection=DashIconify(
                        icon="mdi:spider-web",
                        color=dmc.theme.DEFAULT_THEME["colors"]["blue"][6],
                        width=32),
                    value="tab-star",
                    ml="auto"),
            ],
        ),
        #dmc.LoadingOverlay(
        #    [
            tab_emo,
            tab_music,
            tab_star,
        #    ],
        #    loaderProps={"variant": "dots", "color": "orange", "size": "xl"},
        #    id="id-loader_overlay"
        #),
    ],
    id="tabs-all",
    value="tab-emo", #active tab
    mt=210,
    persistence="persisted",
    persisted_props=["value"],
    persistence_type="session",
)

#==========================================UI-PAGE-LAYOUT=======================================================

layout=html.Div(
    children=[
        pageHeader,
        tabs_all,
    ],
    id="layout_analize",
)

#---------------------------------------------------------------------------------------------------------------
@callback(
    Output("id-analyzer-player", "url"),
    Output("id-plot-audio", "figure", allow_duplicate=True),
    Output("id-plot-wav", "figure"),
    Output("id-plot-chord-map", "figure"),
    Output("id-plot-bw", "figure"),
    Output("id-plot-hist-bw", "figure"),
    Output("id-plot-tempo-map", "figure"),
    Output("id-plot-emo-hist", "figure"),
    Output("id-plot-emogram", "figure"),
    Output("id-plot-npes", "figure"),
    Output("id-plot-cloud", "figure"),
    Output("id-plot-star", "figure", allow_duplicate=True),
    Output("id-plot-dance", "figure"),
    Output("id-plot-rms", "figure"),
    #Output("id-tab-emo", "children"),
    #Output("id-tab-music", "children"),
    #Output("id-tab-star", "children"),
    Input("id-analyzer-file-selector", "value"),
    Input("id-but-recalc", "n_clicks"),
    State("id-analyzer-file-selector", "value"),
    prevent_initial_call='initial_duplicate'
)
def redrawAllPlots(selected_file, recalc, current_file):
    file_path_name = "./audio/"+current_file
    url = emofunc.getAudioUrl(selected_file, file_path_name)
    if ctx.triggered_id == "id-but-recalc":
        figs = emolib.emoAnalyze(current_file)
        emofunc.saveResult(current_file, figs)
        url = emofunc.getAudioUrl(current_file, file_path_name)
    else:
        figs = emofunc.getGrafsContainer(selected_file, "datas")
    return url, figs[0], figs[1], figs[2], figs[3], figs[4], figs[5], figs[6], figs[7], figs[8], figs[9], figs[10], figs[11], figs[12]         

@callback(
    Output('id-play-progress','value'),
    #Output('id-plot-star', 'figure', allow_duplicate=True),
    Input('id-analyzer-player', 'currentTime'),
    #Input('id-plot-audio', 'clickData'),
    State('id-analyzer-player', 'duration'),
    prevent_initial_call=True
)
def getPlayPosition(cur_time, duration):
    if (duration is not None) and (cur_time is not None):
        pos = cur_time  * 100 / duration
        return pos  #, patched_fig
    else:
        return no_update, no_update

