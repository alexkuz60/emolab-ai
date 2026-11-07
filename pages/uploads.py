import dash
from dash import dcc, html, callback, Input, Output, State, ctx, no_update
import dash_ag_grid as dag
import dash_uploader as du
import dash_mantine_components as dmc

from dash_iconify import DashIconify
#import dash_daq as daq
#import essentia
from essentia.standard import MetadataReader
import pandas as pd
import numpy as np
#import os

#import libs.emocomp as emocomp
import libs.emofunc as emofunc
import libs.emolib as emolib

#VALID_USERNAME_PASSWORD_PAIRS = {'hello': 'world'}

#import libs.emolib as emolib

dash.register_page(__name__, order=1)

#auth = dash_auth.BasicAuth(
#    dash.get_app(),
#    VALID_USERNAME_PASSWORD_PAIRS)
du.configure_upload(dash.get_app(), folder="audio")

def loadListCSV():
    df = pd.read_csv("./datas/list.csv", header=0)
    return df
def saveListCSV(out_data):
    df = pd.DataFrame(out_data,
        columns=["Id","Artist","Title","Album","Year","Genre","Size","Time","File", "Bitrate","Samplerate","Channels"])
    df.to_csv("./datas/list.csv", quotechar='"', index = False, encoding='utf-8')
    return True

fileUploader = html.Div(
    [
        du.Upload(
            id="dash-uploader",
            text='Upload new audio file',
            filetypes=['wav', 'mp3'],
            max_files=1,
            upload_id='',
        ),
    ],
)

def get_icon(icon):
    return DashIconify(icon=icon, height=24, color="lightgray")

wait_icon=DashIconify(
    icon="line-md:uploading-loop",
    color=dmc.theme.DEFAULT_THEME["colors"]["blue"][6],
    width=24
)

analyzeStepper=dmc.Stepper(
    id="analyze-stepper",
    active=-1,
    children=[
        dmc.StepperStep(
            label="Prepare",
            description="Analyse audio and meta data",
            icon=get_icon(icon="tabler:music-question"),
            progressIcon=wait_icon,
            completedIcon=DashIconify(icon="icon-park:waves-left", height=24, color='yellow'),  #ph:vinyl-record-bold
            children=[
                dmc.Text("File uploaded. Read audio data. Extract meta-tags...")
            ],
        ),
        dmc.StepperStep(
            label="Processing",
            description="Audio/Music analyzer",
            icon = get_icon(icon="tabler:music-question"),
            progressIcon = wait_icon,
            completedIcon=DashIconify(icon="icon-park:waves-left", height=24, color='lime'),
            children=[dmc.Text("Extract audio & musical futures...", ta="center")],
        ),
        dmc.StepperStep(
            label="Emo analyse",
            description="Emotions analyser",
            icon=get_icon(icon="tabler:music-question"),
            progressIcon = wait_icon,
            completedIcon=DashIconify(icon="fa6-solid:masks-theater", height=24, color='orange'),
            children=[
                dmc.Text("Complex emotion research", ta="center")
            ],
        ),
        dmc.StepperStep(
            label="Results",
            description="Calc and save results graphs",
            icon=get_icon(icon="tabler:music-question"),
            progressIcon = wait_icon,
            completedIcon=DashIconify(icon="fluent:arrow-sort-down-lines-16-filled", height=24, color='white'),
            children=[
                dmc.Text("Pack and store output results..", ta="center")
            ],
        ),
        dmc.StepperCompleted(
            children=[
                dmc.Text(
                    "Analyze process finished. Data saved, Completed OK.",
                    ta="center",
                )
            ]
        ),
    ],
)

accordionUploader = dmc.Accordion(
    children=[
        dmc.AccordionItem(
            [
                dmc.AccordionControl(
                    "Add new audio file",
                    icon=DashIconify(icon='fluent:quiz-new-20-filled', color='yellow', height=32)
                ),
                dmc.AccordionPanel(
                    [
                        dmc.Grid(
                            children=[
                                dmc.GridCol(fileUploader, span=2),
                                dmc.GridCol([dmc.Space(h=20), analyzeStepper],span=10)
                            ],
                        ),
                    ],
                )
            ],
            value="info",
        ),
    ],
)   
    
#---------------------AG-GRID------------------------------#, "valueGetter": {"function": "params.node.Id"}  
columnDefs = [
    {'field': "Id", "checkboxSelection": True, "headerCheckboxSelection": True},    #, "sizeToFit": False, "autoSize": True
    {'field': 'Artist', "sortable": True, "editable": True, "resizable": True},
    {'field': 'Title', "editable": True, "resizable": True},
    {'field': 'Album', "editable": True, "resizable": True},
    {'field': 'Year', "sortable": True, "editable": True},
    {'field': 'Genre', "sortable": True, "editable": True},
    #{'field': 'Size'},
    #{'field': 'File'},
    {'field': 'Time'},
    #{'field': 'Bitrate'},
    #{'field': 'Samplerate'},
    #{'field': 'Channels'},
    {
        "headerName": "Track's Info",
        "children": [
            {
                "columnGroupShow": "closed",
                "field": "File",
                "width": 420,
            },
            {"columnGroupShow": "open", "field": "Size", "width": 100},
            {"columnGroupShow": "open", "field": "Bitrate", "width": 100},
            {"columnGroupShow": "open", "field": "Samplerate", "width": 120},
            {"columnGroupShow": "open", "field": "Channels", "width": 100},
        ],
    },
]

#headers_list = ["id","artist","title","album","year","genre","size","file","time","bitrate","samplerate","channels"]

butDelRows=dmc.Button("Del", leftSection=DashIconify(icon="ic:baseline-delete-forever", color='red'), variant="outline", color="white",
    id="id-but-del")

butSave = dmc.Button("Save", leftSection=DashIconify(icon="material-symbols:save-as-sharp", color="lime"), variant="outline", color="white",
    id="id-but-save")

agTable = dag.AgGrid(
    className="ag-theme-alpine-dark",
    id="id-grid-table",
    defaultColDef={"resizable": True},
    columnDefs=columnDefs,
    columnSize="autoSize",
    rowData=loadListCSV().to_dict("records"),
    #persistence=True,
    #persisted_props=['dataRow'],
    #persistence_type="session",
    dashGridOptions={
        # AG Grid 33+: legacy-тема (alpine) включается опцией theme="legacy", её таблица
        # стилей подключена в emo_app.py через dag.themes.ALPINE
        "theme": "legacy",
        # AG Grid 32.2+: строковое rowSelection заменено объектом
        "rowSelection": {"mode": "multiRow"},
        "undoRedoCellEditing": True,
        "undoRedoCellEditingLimit": 5,
        "editType": "fullRow",
        "pagination": True,
        "paginationPageSize": 10,
        "paginationAutoPageSize": True,
        # прежние "height"/"width" здесь не работали: это не опции грида, а стиль
        # компонента (при необходимости — style={"height": 800} у dag.AgGrid)
        #"style": {"height": 1500, "width": "10/12"},
    },
    getRowId="params.data.Id",
    #getRowId="params.data.File",
)

plot_hist_prev = dcc.Graph(figure=emofunc.getEmptyHistPlotPreviw(), id="id-upload-plot-hist", config={'displayModeBar': False})
plot_cloud_prev = dcc.Graph(figure=emofunc.getEmptyCloudPlotPreviw(), id="id-upload-plot-cloud")# 

layout = html.Div(
    [
        accordionUploader,
        dmc.Space(h=10),
        dmc.Group([
            butDelRows,
            butSave,
            #html.Div([dmc.Kbd("⌘", h=20), " / ", dmc.Kbd("shift", h=20), " + ", dmc.Kbd("Z", h=20)]),
            #html.Button("Save", id="button-save", n_clicks=0),
        ]),
        dmc.Space(h=10),
        dmc.Grid(
            [
                dmc.GridCol(agTable, span=10),
                dmc.GridCol(
                    dmc.Stack(
                        [
                            plot_hist_prev,
                            plot_cloud_prev,
                        ],
                        style={"height": 400},
                        gap=10,
                        align="stretch",
                        justify="center",
                     ),
                    span=2
                )
            ],
        ),
        dcc.Store("id-store-memory-new-row", storage_type="memory")
    ],
    style={"margin": 10},
)

#===================================================CALLBACKS=============================================
###STEP1:
@du.callback(
    output = [
        Output("id-store-memory-new-row", "data"),
        Output("analyze-stepper", "active", allow_duplicate=True)
    ],
    id="dash-uploader"
)
def onUpload(status: du.UploadStatus): # <------- NEW: du.UploadStatus
    if status.is_completed:
        file_name = status.latest_file.name
        file_path_name = "./audio/" + file_name
        title, artist, album, _, genre, _, date, tagPool, duration, bitrate, sampleRate, channels = MetadataReader(filename=file_path_name)()#[7]
        rng = np.random.default_rng()
        new_row = {
            "Id": rng.integers(1000),
            "Artist": artist,
            "Title": title,
            "Album": album,
            "Year": date,
            "Genre": genre,
            "Size": str(round(float(status.uploaded_size_mb), 2)) + " mb",
            "File": file_name,
            "Time": str(duration) + " sec.",
            "Channels": channels,
            "Bitrate": bitrate,
            "Samplerate": sampleRate,
        }    
        stored_data = {"saved_row": new_row, "new_file_name": file_name}
        active_step=1
        print("0:", active_step)
        #succeful file uploaded:
        return [stored_data, active_step]
    #File no was uploaded:
    return no_update, no_update
#---------------------------------------------------------------------------------------------------------------
###STEP2:
@callback(
    Output("id-grid-table", "rowTransaction"),
    Output("analyze-stepper", "active", allow_duplicate=True),
    Input("id-store-memory-new-row", "data"),
    State("analyze-stepper", "active"),
    prevent_initial_call=True
)
def gridAddRow(stored_data, state_active): #, csv_data):
    #------------------Add new row to table:
    if state_active == 1:
        row = stored_data.get('saved_row')
        active_step=2
        print("1:", active_step)
        return {"add": [row],"async": False}, active_step
#-------------------------------------------------------------
###STEP3:
@callback(
    Output("analyze-stepper", "active", allow_duplicate=True),
    Input("id-grid-table", "rowData"),
    State("analyze-stepper", "active"),
    State("id-store-memory-new-row", "data"),
    prevent_initial_call=True
)
def startEmoAnalyzer(row_data, state_active, stored_data):
    if state_active == 2:
        file_name = stored_data.get("new_file_name")
        result_arr = emolib.emoAnalyze(file_name)
        emofunc.saveResult(file_name, result_arr)
        active_step = 3
        print("2b:", active_step)
        return active_step
    return no_update
#---------------------------------------------------------------
###STEP4:
@callback(
    Output("analyze-stepper", "active", allow_duplicate=True),
    Input("analyze-stepper", "active"),
    State("id-grid-table", "rowData"),
    prevent_initial_call=True
)
def finishProcess(active, csv_data):
    if active == 3:
        saveListCSV(csv_data)
        active_step = 4
        print("4:", active_step)
        return active_step
    return no_update
#-----------------------------------------------------------------------------

@callback(
    Output("id-grid-table", "rowTransaction", allow_duplicate=True),
    Input("id-but-del", "n_clicks"),
    State("id-grid-table", "selectedRows"),
    prevent_initial_call=True
)
def onDelRowsButton(click_del, selected):
    #--------------Delete rows from table:
    if selected is None:
        return no_update, no_update
    del_list = [s["File"] for s in selected]
    emofunc.delResultFiles(del_list)
    return {"remove": selected}
#-------------------------------------------

@callback(
    Output("analyze-stepper", "active", allow_duplicate=True),
    Input("id-but-save", "n_clicks"),
    Input("id-grid-table", "rowData"),
    prevent_initial_call=True
)
def saveTableData(save_click, csv_data):
#---------------Save updated row data:
    saveListCSV(csv_data)
    if ctx.triggered_id == "id-but-save":
        active = 0
        return active
    return no_update
#---------------------------------------------

@callback(
    Output("id-upload-plot-hist", "figure"),
    Output("id-upload-plot-cloud", "figure"),
    Input("id-grid-table", "cellClicked"),
    prevent_initial_call=True
)
def onClickCellFile(cell):
    if cell['colId'] == "File":
        file_name = cell['value']
        if file_name is not None:
            fig_hist_prev = emofunc.getGrafsContainer(file_name, "datas")[13]
            fig_cloud_prev = emofunc.getGrafsContainer(file_name, "datas")[14]
            return fig_hist_prev, fig_cloud_prev
    return no_update
#-------------------------------------------------------------