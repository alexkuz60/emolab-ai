#import dash_auth
from dash import dcc, html, callback, Input, Output, State, ctx, no_update
#import dash_mantine_components as dmc
#from dash_iconify import DashIconify

import essentia
from essentia.standard import MetadataReader
import pandas as pd
import numpy as np
#import os

#import libs.emocomp as emocomp
import libs.emofunc as emofunc
import libs.emolib as emolib

#VALID_USERNAME_PASSWORD_PAIRS = {'hello': 'world'}

#import libs.emolib as emolib

#auth = dash_auth.BasicAuth(
#    dash.get_app(),
#    VALID_USERNAME_PASSWORD_PAIRS)