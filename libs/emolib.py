#import os
#import base64
import time

import numpy as np
import pandas as pd

import essentia
import essentia.standard

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
pio.templates.default = "plotly_dark"

#import libs.emocomp as emocomp
#import libs.emofunc as emofunc
import libs.emolist as emolist

UPLOAD_DIR = "./audio"
EXTRAS_DIR= "./extras"
DATAS_DIR = "./datas"

frame_size = 32768
hop_size = 32768#16384
sample_rate = 44100

Pi = np.pi
twoPi = 2 * Pi
halfPi = Pi/2
def Range2Pi(angle):
    if angle >= twoPi:
        angle = angle - twoPi
    elif angle < 0:
        angle = twoPi - angle
    return angle

d_bw = twoPi/7 #tick size of BrainWave sector in rad
d_key = twoPi/12 #tick size for chord's key in rad d_bw/12
bw_start = halfPi + d_bw/2 # delta0 for lowDelta sector #start lowDelta sector
bw_start_sectors = [Range2Pi(bw_start + d_bw * i) for i in range(0,7,1)]
    
emo_sectors_num = 28
emo_list = emolist.emo_list28
emo_histogram = np.zeros(emo_sectors_num)
dgroup_th = twoPi / emo_sectors_num
emo_scale=[i*360/28 for i in range(28)]

def getBitPositionsAndBPM(audio):
    # Compute beat positions and BPM.--------------------------------------------------------------------
    rhythm_data = essentia.standard.RhythmExtractor2013(maxTempo=250, method="degara", minTempo=60)(audio)
    beat_positions = rhythm_data[1]#sec.
    beat_intervals = rhythm_data[4]#sec.
    #print(len(rhythm_data[1]), len(rhythm_data[3]), len(rhythm_data[4]))
    tempo_delta_bpm = 240 * beat_intervals[:] - 120  #for 4/4 in sec.
    return beat_positions, tempo_delta_bpm # Compute beat positions and BPM.---------------------------

def getTonalityKeys(audio):
    #Tonality Keys:---------------------------------------------------------------------
    tonal_data = essentia.standard.TonalExtractor(frameSize=frame_size, hopSize=hop_size)(audio)
    keys_all = tonal_data[4]
    delta_frame_time = hop_size/44100 #frame-hop step (sec)
    #[name, delta_th, min/maj, num_in_octave]
    
    #gamma_list=np.array(emolist.gamma_list, dtype=object)
    pos_start = 0.0
    index = 1
    key_prev = keys_all[0]
    keys_map = [[]]
    for key_i in keys_all[1:]:
        if key_i != key_prev:
            pos_next = round(index * delta_frame_time, 2)
            xlen = round(pos_next - pos_start, 2)
            k_maj = 0
            k_num_oct=1
            for k_type in emolist.key_list:
                if key_i == k_type[0]:
                    k_maj = k_type[2]
                    k_num_oct = k_type[3]
            keys_map.append([key_i, pos_start, xlen, k_maj, k_num_oct])
            pos_start = pos_next
            key_prev = key_i
        index += 1
    keys_map = keys_map[1:]
    #Calc delta keys:[name, typeId, maj]

    #d=np.rad2deg(d_key*11) for star & minor_major to keymap
    delta_keys = []
    for key in keys_all:
        for k_type in emolist.key_list:
            if key == k_type[0]:
                delta_keys.append(d_key * k_type[1])
    #FOR TEST ONLY: Поиск сбойных вычислений аккорда:
    uniq_keys = list(set(keys_all))

    return delta_keys, keys_map #Tonality Keys:---------------------------------------------------------

def calcBrainWaves(audio):
    #BrainWaves:-------------------------------------------------------------------------
    fft_win = essentia.standard.Windowing(size=hop_size, type = 'hann')
    spectrum = essentia.standard.Spectrum(size=frame_size)  # FFT() would return the complex FFT, here we just want the magnitude spectrum
    spectrums = []
    bw_waves = [[]]

    dt = hop_size / sample_rate
    #frame_start_time = dt
    for frame in essentia.standard.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size, startFromZero=True):
        spectr_frame = []
        spectr_frame = spectrum(fft_win(frame))
        spectrums.append(spectr_frame)
        #---------------
        #EMUSE Octaver:
        low = 0 #TODO!!! with bias???
        high = 1
        bw_num = 0
        bw_frame14 = []
        while bw_num < 14:
            sum = 0.0
            bin = low
            while bin < high:
                sum += spectr_frame[bin]          
                bin += 1
            bw_frame14.append(sum)
            bw_num += 1
            low = high;
            high *= 2;
            #print(low, high)
        bw_frame_out = []
        i = 0
        while i < 7:
            bw_frame_out.append(bw_frame14[i] + bw_frame14[i + 7])
            i += 1
        bw_waves.append(bw_frame_out)

    bw_waves = bw_waves[1:]#delete empty items
    #Normalize:
    max_bw = np.max(bw_waves)
    bw_waves = bw_waves / max_bw #[bw/max_bw for bw in bw_waves]
    return bw_waves

def quantizerTempoMap(frames_bw, beat_positions, tempo_delta_bpm, duration):
    frames_bp = len(tempo_delta_bpm)
    frames_tdb = len(tempo_delta_bpm)
    tempo_quantize = np.zeros(frames_bw)
    index_frame = 0
    index_pos = 0
    time_quant = duration/frames_bw
    pos_frame = time_quant
    while index_frame < frames_bw and index_pos < frames_bp:
        beat_next = beat_positions[index_pos]
        while pos_frame < beat_next and index_pos < frames_tdb:
            tempo_quantize[index_frame] = tempo_delta_bpm[index_pos]
            pos_frame += time_quant
            index_frame += 1
        index_pos += 1
    return tempo_quantize

def calcEmoStarData(bw_waves, tempo_quantize, delta_keys):
    #EmoStar data in polar:
    emostars_r = [[]]# [7+1 bw rays]
    emostars_th = [[]]
    #stars_xy = [[]]#[7 bw[x= cos,y=sin]]
    emo_dominante = [[]]
    emo_expression = [] # For emogram
    dominante_th = []

    i_frame = 0
    size=len(tempo_quantize)
    for frame in  bw_waves:
        i_bw = 0
        bw_thetas = []
        bw_rays = []
        sum_sin_bw = 0.0
        sum_cos_bw = 0.0
        dom_th = 0.0
        for bw in frame:
            #keyCorrector:
            d_th = Range2Pi(bw_start_sectors[i_bw] + delta_keys[i_frame])
            #TempoCorrector$
            if i_frame < size:#всегда должны быть равны!
                d_tempo = tempo_quantize[i_frame]/120 # %% frombmp=120 TODO!!!!!!!!!!!!!!
                if 0 < d_th < Pi:
                    bw = bw + bw * d_tempo
                elif Pi < d_th < twoPi or d_th < 0:
                    bw = bw - bw * d_tempo
            bw_sin = bw * np.sin(d_th)
            bw_cos = bw * np.cos(d_th)
            bw_r = round((np.hypot(bw_sin, bw_cos)), 2)
            bw_rays.append(bw_r)
            bw_thetas.append(d_th)
            sum_sin_bw += bw_sin
            sum_cos_bw += bw_cos
            i_bw += 1
        bw_rays.append(bw_rays[0])      #for close emostar
        bw_thetas.append(bw_thetas[0])  #close emostar
        emostars_r.append(bw_rays)
        emostars_th.append(bw_thetas)
        dom_r = np.hypot(sum_sin_bw, sum_cos_bw)
        if sum_cos_bw == 0 and sum_sin_bw > 0:
            dom_th = halfPi
        elif sum_cos_bw == 0 and sum_sin_bw < 0:
            dom_th = -halfPi
        else:
            dom_th = np.arctan2(sum_sin_bw, sum_cos_bw)
        dominante_th.append(dom_th)
        emo_expression.append(dom_r)   
        emo_dominante.append([dom_r, dom_th])
        index = int(dom_th // dgroup_th)
        emo_histogram[index] = emo_histogram[index] + dom_r
        i_frame += 1
    #x=Clear empty items:
    emostars_r = emostars_r[1:]
    emostars_th =emostars_th[1:]
    emo_dominante = emo_dominante[1:]
    # normalize expression:
    zoom_ex = 1/max(emo_expression)
    emo_expression = zoom_ex * np.array(emo_expression, dtype=float)
    return emo_expression, dominante_th, emostars_r, emostars_th

#"NEGATIVE/POSITIVE and EXALTACION/SUPRESSION"---------------------------
def calcDataNPES(emo_expression, dominante_th):
    negative = []
    positive = []
    np_plot = []
    exaltation = []
    supression = []
    es_plot =[]
    i=0
    dlen=len(dominante_th)
    while i < dlen:
        th = float(dominante_th[i])
        if  dominante_th[i] > -halfPi and dominante_th[i] < halfPi:
            positive.append(emo_expression[i])
            negative.append(.0)
            np_plot.append(emo_expression[i])
        else:
            positive.append(.0)
            negative.append(emo_expression[i])
            np_plot.append(-emo_expression[i])
            
        if  dominante_th[i] < 0:
            supression.append(emo_expression[i])
            exaltation.append(.0)
            es_plot.append(-emo_expression[i])
        else:
            supression.append(.0)
            exaltation.append(emo_expression[i])
            es_plot.append(emo_expression[i])
        i += 1
    return np_plot, es_plot #"NEGATIVE/POSITIVE and EXALTACION/SUPRESSION"----------

#=====================================GRAFICS=========================================
#[0] Audio for player
def createFigurePlay(plot_signal, x_sec):

    fig_play = go.Figure()
    fig_play.add_trace(go.Bar(x = x_sec, y=plot_signal))
    fig_play.add_trace(go.Bar(x = x_sec, y=-plot_signal))
    #fig_play.layout.xaxis.title = "Track time (sec.)"
    fig_play.update_layout(
        height=160,
        #xaxis=dict(rangeslider=emocomp.posZoomSlider),
        barmode='overlay',
        barnorm='percent',
        margin={"r":10,"t":40,"l":10,"b":0},
        showlegend=False,
        xaxis=dict(nticks= 12, ticksuffix = " sec"), #tickformat = "%M:%S",
        yaxis=dict(ticklen=50, tickwidth=50)
    )
    fig_play.update_traces(marker_color='lime', marker_line_color='lime', marker_line_width=1, opacity=0.5)
    fig_play.add_shape(type="line",
        #xref="paper", yref="paper",
        x0=10, y0=-0.5, x1=10, y1=0.5,
        line=dict(color="DarkOrange", width=2))
    return fig_play

#[1] AudioSignal plot:---------------------------------------------------------------
def createFigureAudio(plot_signal, x_sec):
    fig_audio = go.Figure()
    fig_audio.add_trace(go.Scatter(x=x_sec, y=plot_signal, line_shape='spline')
    )
    #fig_audio.layout.xaxis.title = "Track time (sec.)"
    fig_audio.update_layout(height=250, margin={"r":10,"t":40,"l":10,"b":0},
        xaxis=dict(ticksuffix = " sec"))    #type="date", tickformat = "%M-%S", 
    return fig_audio

#[2]ChordsMap Plot:------------------------------------------------------------------
def createFigureKeyMap(keys_map, duration):
    h_plot = 12*18
    #with open("./assets/piano_keys.png", "rb") as image_file:
    #    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    df=pd.DataFrame(keys_map)
    df.columns=['chord', 'start_pos', 'xlen', 'min_maj', 'gamma']
    gamma_list = np.array(emolist.gamma_list, dtype=object)
    fig_ch = go.Figure()
    #fig_ch.add_image(source=f"data:image/png;base64,{encoded_string}", #xref= "x", yref= "y",
        #dx= 0.05, dy= 12/240, x0= 0, y0=-1/2, opacity= 0.75)#layer= "below")#sizing= "stretch",
    fig_ch.add_trace(go.Scatter(name='Tracer', x=df['start_pos'], y=df['gamma'],
        line_shape='hv', line_width=1, line_color='lightgreen', opacity=0.5))
    fig_ch.add_trace(go.Bar(name='Chords', orientation = 'h', base=df['start_pos'], x=df['xlen'], y=df['gamma'],
        marker_color=df['min_maj'], marker_colorscale=['blue','red'], marker_line_color='green'))
    fig_ch.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, height=h_plot, showlegend=False, 
        yaxis=dict(dtick=1, tickmode="array", ticktext=gamma_list[:,0], tickvals=gamma_list[:,1], showgrid=True, tickfont_size=11),
        xaxis= dict(range=[0, duration], nticks = 12, ticksuffix=" sec")),
    return fig_ch

##[3]Plot BW: title='Dynamic of BrainWaves'------------------------------------------------
def createFigureDynamicBW(bw_waves, duration):
    fig_bw=px.line(bw_waves)#labels={'0': 'LD', '1':'D','2':'Th'}
    fig_bw.update_layout(
        height=250,
        legend=dict(orientation="h", yanchor = "top", y=10, title="BW: "),
        xaxis=dict(range=[0, duration], nticks=12, ticksuffix = " sec"), margin={"r":0,"t":30,"l":0,"b":0}
    )
    return fig_bw

#[4]BrainWaves summary plot:  test_sum_bws = [i for i in range(1,8)]# for test--------------
def createFigureSummaryHistBW(bw_waves):
    bw_colors = ['red', 'orange', 'yellow', 'green', 'lightblue','blue', "darkviolet"]
    sum_bws = np.sum(bw_waves, axis=0)
    fig_bw_hist = px.bar(x=emolist.bw_list, y=sum_bws, color=bw_colors, height=600, opacity=0.5) 
    fig_bw_hist.update_layout(margin={"r":10,"t":30,"l":10,"b":70}, showlegend=False)
    return fig_bw_hist

#[5]TempoMap plot:, title='Quantize Tempo deviation'----------------------------------------
def createFigureTempoMap(tempo_quantize, x_sec):
    fig_tempo = go.Figure()
    fig_tempo.add_trace(go.Scatter(x = x_sec, y = tempo_quantize, mode='lines', fill='tozeroy', name='delta tempo'))  #line_shape='spline',
    fig_tempo.layout.yaxis.title = "dTempo (bpm)"
    fig_tempo.update_layout(height = 200, margin={"r":0,"t":40,"l":0,"b":0})
    fig_tempo.update_xaxes(ticksuffix = " sec")
    return fig_tempo

#[6]Emogram & Expression plots:---------------------------------------------------------------------
def createFigureEmoHistogram(emo_list, emo_histogram):
    fig_emo_hist = px.bar(x = emo_list, y=emo_histogram, height=250, color = emo_histogram, opacity=0.75)
    fig_emo_hist.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    return fig_emo_hist
   
#[7]Dynamic Emogram---------------------------------------------------------------------------------
def createFigureEmoExpression(emo_expression, dominante_th, x_sec, duration):    #, x_sec
    #zoom = twoPi / np.max(emo_expression)
    marker_len = duration*10/len(dominante_th)
    express_for_plot = np.array(emo_expression) * twoPi
    dom_th_for_plot = np.array(dominante_th) + Pi
    fig_emogram = go.Figure()
    fig_emogram.add_trace(go.Bar(x=x_sec, y=express_for_plot, name='Expression'))
    fig_emogram.add_trace(go.Scatter(x=x_sec, y=dom_th_for_plot, mode='lines', name='Emo dynamic',
                                     line_shape='spline', line_width=3, line_color='orange', opacity=0.25))
    fig_emogram.add_trace(go.Scatter(x=x_sec, y=dom_th_for_plot, mode='markers', name='Emotions')
    )
    fig_emogram.update_traces(
        marker=dict(
        size=marker_len,
        colorscale= 'hsv',
        color = dom_th_for_plot,
        symbol="line-ew",
        line=dict(width=3, color=dom_th_for_plot)),
        selector=dict(mode="markers")
    )
    fig_emogram.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=250,
        xaxis=dict(nticks=12, range=[0, duration], ticksuffix=" sec")
    )#, color_discrete_sequence=['#00bbaa'] )
    return fig_emogram
    
#[8.1] Negative/Positive Plot----------#[8.2] Ex/Su plot----------------------------------
def createFigureNPES(np_plot, es_plot, x_sec):
    fig_npes = go.Figure()
    fig_npes.add_trace(go.Scatter(x=x_sec, y=np_plot, mode='lines', line_shape='spline', fill='tozeroy', name='Positive/Negative', opacity=0.25))
    fig_npes.add_trace(go.Scatter(x=x_sec, y=es_plot, mode='lines', line_shape='spline', fill='tozeroy', name='Exaltation/Supression', opacity=0.25))
    fig_npes.update_traces(hoverinfo='text+name', mode='lines')
    fig_npes.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=250,
        xaxis=dict(nticks=12, ticksuffix=" sec"),
        margin={"r":0,"t":40,"l":0,"b":0}
    )
    return fig_npes

#[9]EmoCloud Star plot:--------------------------------------------------------------------
def createFigureEmoCloud(emo_expression, dominante_th):
    bw_sectors=[d_bw for i in range(7)]
    points_size = 4.0 + np.array(emo_expression) * 10
    fig_cloud=go.Figure()
    fig_cloud.add_pie(values=bw_sectors, showlegend=False, labels=emolist.bw_list,
        direction="counterclockwise", rotation=-360/14, hole=0.95, opacity=0.5)#
    fig_cloud.add_hline(0, opacity=0.25)
    fig_cloud.add_vline(0, opacity=0.25)
    fig_cloud.add_trace(go.Scatterpolar(
        r = emo_expression,
        theta = dominante_th,
        thetaunit = 'radians',
        mode='markers',
        opacity=0.75,
        name='EmoCloud',
        marker=dict(
            size=points_size,
            colorscale= 'hsv',
            color = dominante_th,
            showscale=True,
        )
    ))
    fig_cloud.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1.05])),
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        autosize=True,
        #width=800,
        height=600,
        margin={"r":0,"t":30,"l":10,"b":70},
        xaxis_visible=False, yaxis_visible=False,
    )
    fig_cloud.update_polars(
        #selector="scatterpolar",
        angularaxis=dict(tickvals=emo_scale, tickmode="array", ticktext=emolist.emo_list28, visible=True),
    )
    return fig_cloud

#[10]EmoStar & Dominante frames plot:----------------------------------------------------------------------
def createFigureEmoStar(emostars_r, emostars_th, emo_expression, dominante_th):
    fig_star = go.Figure()
    fig_star.add_hline(0, opacity=0.25)
    fig_star.add_vline(0, opacity=0.25)

    star_index=0
    for star_frame_r in emostars_r:
        star_frame_th = emostars_th[star_index]
        fig_star.add_trace(go.Scatterpolar(
            r=star_frame_r,
            theta=star_frame_th,
            visible=False,
            thetaunit = 'radians',
            fill='toself',
            #name='Emotions',
            marker_color=['#E4FF87', '#AB1BFF', '#709BFF', '#FFAA70', '#FF2270', '#F01FF0', '#B6FFB4'],
            marker_size=8,
            mode= 'lines+markers',
            name= "EmoSpace"
        ))
        #Dominante:
        dom_r = emo_expression[star_index]
        dom_th = dominante_th[star_index]
        fig_star.add_trace(go.Scatterpolar(
            r=[0, dom_r],
            theta=[0, dom_th],
            mode= 'lines+markers',
            thetaunit = 'radians',
            visible=False,
            name="EmoDominante"
        ))
        star_index += 1
    # Make 1st trace visible
    fig_star.data[0].visible = True
    fig_star.data[1].visible = True

    # Create and add slider:
    steps = []
    steps_num = len(fig_star.data) - 2
    for i in range(0, steps_num, 2):
        step = dict(
            method="update",
            args=[{"visible": [False] * steps_num},
                {"title": "frame: " + str(i)}]  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible" star's polygon
        step["args"][0]["visible"][i+1] = True  # Toggle i+1'th trace to "visible" dominante
        steps.append(step)
    sliders = [dict(
        active=0,
        currentvalue={"prefix": "EmoStar frame: "},
        pad={"t": 50},
        steps=steps,
    )]
    fig_star.update_layout(
        sliders=sliders,
        showlegend=True,
        legend=dict(orientation="h", yanchor = "top", y=10),
        autosize=False,
        height=660,
        margin={"r":10,"t":30,"l":0,"b":10},
        xaxis_visible=False, yaxis_visible=False,
        #polar=dict(radialaxis=dict(visible=True, range=[0, 1.05])),
        #plot_bgcolor ="rgba(0,0,0,0)"
    )
    fig_star.update_polars(
        angularaxis=dict(tickvals=emo_scale, tickmode="array", ticktext=emolist.emo_list28, visible=True),
        radialaxis=dict(range=[0, 1], nticks=10, dtick=0.1, tickmode='auto')
    )
    
    return fig_star

#[11]DANCEABILITY-------------------------------------------------------------------------------
def createFigureDanceability(audio, duration):
    danceability, dfa = essentia.standard.Danceability()(audio)
    len_dfa=len(dfa)
    dfa= 100*dfa/3
    dt = duration / len_dfa
    pos = [n*dt for n in range(0, len_dfa, 1)] #duration of audio (sec.)

    fig_dance = px.line(x=pos, y=dfa, height=200, markers=True)#range_y=[0,1.5], 
    fig_dance.update_layout(xaxis=dict(range=[0, duration], nticks=12, ticksuffix=" sec"), margin={"r":0,"t":40,"l":0,"b":60})
    fig_dance.layout.yaxis.title = "Danceability"
    return fig_dance

#[12] LoudnessEBUR128 requires stereo in 44100 Hz sample rate-------------------------------------
def createFigureRMS(file_path_name, duration):
    start=time.time()
    audio_st, _, _, _, _, _ = essentia.standard.AudioLoader(filename=file_path_name)()
    loudMeter = essentia.standard.LoudnessEBUR128(hopSize=4096/44100, startAtZero=True)
    ebu_momentary, ebu_shortterm, ebu_integrated, _ = loudMeter(audio_st)
    density=10
    max_x = len(ebu_momentary)//density
    dx= duration/max_x
    x_sec = [x*dx for x in range(0, max_x, 1)]
    fig_rms = go.Figure()
    fig_rms.add_hline(y=ebu_integrated, line_color="green")#, annotation=dict(annotation_text="%{ebu_integrated}2f dB"), annotation_position=["bottom", "right"])
    fig_rms.add_trace(go.Scatter(x=x_sec, y=ebu_momentary[::density], mode='lines', line_shape='spline', fill='tozerox', name='Momentary', opacity=0.25))
    fig_rms.add_trace(go.Scatter(x=x_sec, y=ebu_shortterm[::density], mode='lines', line_shape='spline', name='Loadness', opacity=0.85))
    fig_rms.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=250,
        xaxis=dict(range=[0, duration], nticks=12, ticksuffix=" sec"),
        margin={"r":0,"t":40,"l":0,"b":0},
    )
    fig_rms.update_yaxes(range=[-100,0])
    print(time.time() - start)
    return fig_rms

#[13] EmoHist Preview------------------------------------------------------------------------------------------------
def createFigureEmoHistPreview(emo_list, emo_histogram):
    fig_emohist_prev=px.bar(x= emo_list, y=emo_histogram)
    fig_emohist_prev.update_layout(
        showlegend=False,
        autosize=True,
        height=100,
        margin={"r":5,"t":0,"l":5,"b":0},
        xaxis_visible=False, yaxis_visible=False,
    )
    return fig_emohist_prev

#[14] EmoCloud Preview------------------------------------------------------------------------------------------------
def createFigureEmoCloudPreview(emo_expression, dominante_th):
    sectors=[2*np.pi/8 for i in range(8)]
    rays=[22.5 + i*45 for i in range(8)]
    ticks=['' for i in range(8)]
    points_size = 2.0 + np.array(emo_expression) * 5
    
    fig_emo_prev=go.Figure()
    fig_emo_prev.add_trace(go.Pie(values=sectors, showlegend=False,
            hoverinfo='label', textinfo='none', labels=emolist.emo_list8,
            direction="counterclockwise", rotation=-22.5, hole=0.9, opacity=0.5))
    fig_emo_prev.add_hline(0, opacity=0.5, line_color='green')
    fig_emo_prev.add_vline(0, opacity=0.5, line_color='green')
    fig_emo_prev.add_trace(go.Scatterpolar(
            r = emo_expression, theta = dominante_th, thetaunit = 'radians', mode='markers',
            opacity=0.75,
            name='EmoCloud',
            marker=dict(
                size=points_size,
                colorscale= 'hsv',
                color = dominante_th,
                showscale=False,
            ),
        ),
    )
    fig_emo_prev.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1.05])),
        showlegend=False,
        autosize=True,
        height=300,
        margin={"r":5,"t":0,"l":5,"b":0},
        xaxis_visible=False, yaxis_visible=False,
    )
    fig_emo_prev.update_polars(
        #selector="scatterpolar",
        angularaxis=dict(tickvals=rays, ticktext=ticks, visible=True),
        radialaxis=dict(tickvals=[0.25,0.5,0.75, 1.0], tickmode="array", ticktext=["", "", "", ""], visible=True)
    )
    return fig_emo_prev
#=+++++++++++++++=======================EMODATA ANALYZER=========================++++++++++++++++++++++++
def emoAnalyze(fileName):
    #start_time = time.time()
    plotPool = []
    file_path_name="./audio/" + fileName
    audio = essentia.standard.EasyLoader(filename=file_path_name, replayGain=0)()
    
    #Metadata:
    title, artist, album, _, genre, _, date, tagPool, duration, bitrate, sample_rate, channels = essentia.standard.MetadataReader(filename=file_path_name)()#[7]
    
    density= int(2 * duration * 44.1)
    plot_signal = audio[::density]
    max_x = len(plot_signal)
    x_sec = [x*duration/max_x for x in range(0, max_x, 1)]
    plotPool.append(createFigurePlay(plot_signal, x_sec)) #[0]
    plotPool.append(createFigureAudio(plot_signal, x_sec)) #[1]
    
    #Tonality Keys:---------------------------------------------------------------------
    delta_keys, keys_map = getTonalityKeys(audio)
    plotPool.append(createFigureKeyMap(keys_map, duration)) #[2]

    #BrainWaves:
    bw_waves = calcBrainWaves(audio)
    x_sec = [x*duration/len(bw_waves) for x in range(0, len(bw_waves), 1)]
    plotPool.append(createFigureDynamicBW(bw_waves, duration)) #[3]
    plotPool.append(createFigureSummaryHistBW(bw_waves)) #[4]

    # Compute beat positions and BPM.--------------------------------------------------------------------
    beat_positions, tempo_delta_bpm = getBitPositionsAndBPM(audio)
    #Calc Quantizer/Resampler TempoMap:
    tempo_quantize = quantizerTempoMap(len(bw_waves), beat_positions, tempo_delta_bpm, duration)
    plotPool.append(createFigureTempoMap(tempo_quantize, x_sec)) #[5]
    
    #Calc Emogram & Expression:-------------------------EMO DATA:---------------------------
    emo_expression, dominante_th, emostars_r, emostars_th = calcEmoStarData(bw_waves, tempo_quantize, delta_keys)
    plotPool.append(createFigureEmoHistogram(emo_list, emo_histogram)) #[6]
    plotPool.append(createFigureEmoExpression(emo_expression, dominante_th, x_sec, duration)) #[7]

    #"Negative/positive and Exaltation/Supression"------------------------------------------
    np_plot, es_plot = calcDataNPES(emo_expression, dominante_th)
    plotPool.append(createFigureNPES(np_plot, es_plot, x_sec)) #[8]

    #EmoCloud/EmoStar:----------------------------------------------------------------------
    plotPool.append(createFigureEmoCloud(emo_expression, dominante_th)) #[9]
    plotPool.append(createFigureEmoStar(emostars_r, emostars_th, emo_expression, dominante_th)) #[10]

    plotPool.append(createFigureDanceability(audio, duration)) #[11]
    plotPool.append(createFigureRMS(file_path_name, duration)) #[12]

    #Emo Hist/Cloud Preview for Uploads page:----------------------------------------------------------
    plotPool.append(createFigureEmoHistPreview(emo_list, emo_histogram)) #[13]
    plotPool.append(createFigureEmoCloudPreview(emo_expression, dominante_th)) #[14]
    return plotPool
#--------------------------------------------------------------------------------------------

#Заглушка лога TF
#from tensorflow import debugging
#debugging.set_log_device_placement(False)
