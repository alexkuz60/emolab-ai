import dash
from dash import Dash, html #, callback, Output, Input, State
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
#import dash_trich_components as dtc

app = Dash(__name__, title='EmoLab',
    # dag.themes.BASE + ALPINE: legacy-тема ag-grid, с dash-ag-grid >= 33 подключается
    # только внешними таблицами стилей (ядро + тема)
    external_stylesheets=[dbc.themes.DARKLY, dag.themes.BASE, dag.themes.ALPINE],
    use_pages=True,
    #url_base_pathname="/"
)# show_undo_redo=True
server = app.server

navTopMenu = dmc.SimpleGrid(cols=6,
    children=[
        dmc.NavLink(
            label="EmoLab",
            leftSection=DashIconify(icon="mingcute:music-3-fill", color="lime", height=32),
            href='/',
        ),
        html.Div(), #empty grid cells
        dmc.NavLink(
            label="Audio Uplouds",
            leftSection=DashIconify(icon="fluent:task-list-square-add-24-regular", color="lime", height=32),
            ml="auto", # tab in right position,
            href='/uploads',
        ),
        dmc.NavLink(
            label="Emo Analyzer",
            leftSection=DashIconify(icon="fa-regular:chart-bar", color="lime", height=32),
            href='/analyze',
        ),
        dmc.NavLink(
            label="Extra Futures",
            leftSection=DashIconify(icon="tabler:photo-ai", color="lime",height=32),
            href='/extras',
        ),
        dmc.NavLink(
            label="Vocal Tools",
            leftSection=DashIconify(icon="mingcute:mic-2-fill", color="lime",height=32), #"icon-park-outline:electric-wave"
            href='/tools',
        ),
    ],
    id="nav-header",
)

"""
burger=dmc.Burger(id="id-burger")
bar_wide=180
bar_narrow=60
navBar = dmc.Drawer(
        [
            burger,
            dmc.Divider(size=4),
            dmc.NavLink(
                label="EmoLab",
                icon=DashIconify(icon="mingcute:music-3-fill", color="lime", height=32),
                href='/',
                w=200,
            ),
            dmc.NavLink(
                label="Audio Uplouds",
                icon=DashIconify(icon="fluent:task-list-square-add-24-regular", color="lime",height=32),
                ml="auto", # tab in right position,
                href='/uploads',
            ),
            dmc.NavLink(
                label="Emo Analyzer",
                icon=DashIconify(icon="fa-regular:chart-bar", color="lime", height=32),
                href='/analyze',
            ),
            dmc.NavLink(
                label="Extra Futures",
                icon=DashIconify(icon="tabler:photo-ai", color="lime",height=32),
                href='/extras',
            ),
            dmc.NavLink(
                label="Audio Tools",
                icon=DashIconify(icon="icon-park-outline:electric-wave", color="lime",height=32),
                href='/tools',
            ),
        ],
        size=bar_narrow,
        zIndex=10000,
        opened=True,
        withOverlay =False,
        withCloseButton=False,
        id="id-nav-bar",
    ),
"""

app.layout = dmc.MantineProvider(
    dmc.AppShell(
    [
        dmc.AppShellHeader(navTopMenu),
        dmc.AppShellMain(
	    dash.page_container,
        ),
    ],
    header={"height": 50},
    padding=0, # как в прежней вёрстке: у контента не было отступов AppShell
    id="app-layout",
    ),
    forceColorScheme="dark",
)

"""
@callback(
Output("id-nav-bar", "size"),
Input("id-burger", "opened"),
prevent_initial_call=True,
)
def resizeNavBar(isCross):
    w=bar_wide
    if isCross==True:
        w=bar_narrow
    return w
"""

if __name__ == '__main__':
    app.run(debug=True)
