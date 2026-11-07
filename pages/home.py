import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify

dash.register_page(__name__, path='/', order=0)

layout= dmc.Center(
    style={"height": "100%", "width": "100%"},
    children=[
        dmc.Group(
            [
                dmc.Text(
                    "Emo Lab",
                    variant="gradient",
                    gradient={"from": "blue", "to": "yellow", "deg": 45},
                    fz = 150,
                    fw = 1000,
                    opacity=0.5,
                    mt=150
                ),
                #dmc.ActionIcon(DashIconify(icon="mingcute:music-3-fill", color="lime"))
            ],
            align="center",
        )
    ],
)