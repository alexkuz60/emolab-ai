#import os
#import base64
import array
import wave
import struct
import time

import numpy as np
#import pandas as pd
#import scipy.io.wavfile as wavf
import speech_recognition as speech_r
#import essentia
import essentia.standard

#import dash
#from dash import dcc, html, callback, Input, Output
#from dash.exceptions import PreventUpdate
#import dash_bootstrap_components as dbc
#import dash_mantine_components as dmc
#from dash_iconify import DashIconify
#import dash_player as dp
#from plotly_resampler import FigureResampler
#import plotly.express as px
import plotly.graph_objects as go

import libs.emocomp as emocomp
#import libs.emofunc as emofunc
#import libs.emolist as emolist

#UPLOAD_DIR = "./audio"
#EXTRAS_DIR= "./extras"
#DATAS_DIR = "./datas"

#====================================VOCAL TOOLS LIB=======================================================
def splitSetInput(input_file):
    start_time = time.time()
    # Input should be audio @41kHz.
    audio, sr, _, _, _, _ = essentia.standard.AudioLoader(filename=input_file)()

    pool = essentia.Pool()
    # The input needs to have 4 dimensions so that it is interpreted as an Essentia tensor.
    pool.set("waveform", audio[..., np.newaxis, np.newaxis])
    end_time = time.time() - start_time
    return pool, audio, end_time
#---------------------------------------------------------------------------------------------------------------------
def splitProcess(pool, input_audio, n_split):
    start_time = time.time()
    #pool.set("waveform", input_audio[..., np.newaxis, np.newaxis])
    if n_split == 2:
        model = essentia.standard.TensorflowPredict(
            graphFilename="./models/spleeter-2s-3.pb",
            inputs=["waveform"],
            outputs=["waveform_accompaniment", "waveform_vocals"]
        )   
    elif n_split == 4:
        model = essentia.standard.TensorflowPredict(
            graphFilename="./models/spleeter-4s-3.pb",
            inputs=["waveform"],
            outputs=["waveform_vocals", "waveform_drums", "waveform_bass", "waveform_other"]
        )
    #elif n_split == 5:
    #    model = essentia.standard.TensorflowPredict(
    #        graphFilename="./models/spleeter-5s-3.pb",
    #        inputs=["waveform"],
    #        outputs=["waveform_vocals", "waveform_drums", "waveform_bass", "waveform_piano", "waveform_other"]
    #    )

    out_pool = essentia.Pool()
    out_pool = model(pool)
    end_time = time.time() - start_time
    return out_pool, end_time
#---------------------------------------------------------------------------------------------------------------------
def splitCalcGraph(input_audio, pool, n_split, plot_density):
    #print(n_split)
    start_time = time.time()

    plot_input = input_audio[::plot_density]
    
    vocal = pool["waveform_vocals"].squeeze()
    plot_vocal = vocal[::plot_density]
    #print("vocal data:", plot_vocal)
    section_name="waveform_other"
    if n_split == 2:
        section_name="waveform_accompaniment"
    other = pool[section_name].squeeze()
    plot_other = other[::plot_density]
    if n_split > 2:
        drums = pool["waveform_drums"].squeeze()
        plot_drums = drums[::plot_density]
        bass = pool["waveform_bass"].squeeze()
        plot_bass = bass[::plot_density]
        #if n_split == 5:
        #    piano = pool["waveform_piano"].squeeze()
        #    plot_piano = piano[::plot_density]
        #    print("piano",piano)

    fig_all = go.Figure()
    fig_all.add_trace(go.Scatter(y=plot_input[:,0], mode='lines', fill='tozeroy', name='input audio', opacity=0.25))    #line_shape='spline', 
    fig_all.add_trace(go.Scatter(y=plot_vocal[:,0], mode='lines', fill='tozeroy', name='vocals', opacity=0.25))
    fig_all.add_trace(go.Scatter(y=plot_other[:,0], mode='lines', fill='tozeroy', name='others', opacity=0.52))
    if n_split > 2:
        fig_all.add_trace(go.Scatter(y=plot_bass[:,0], line_shape='spline', mode='lines', fill='tozeroy', name='bass', opacity=0.25))
        fig_all.add_trace(go.Scatter(y=plot_drums[:,0], line_shape='spline', mode='lines', fill='tozeroy', name='drums', opacity=0.25))
        #if n_split == 5:
        #    fig_all.add_trace(go.Scatter(y=plot_piano, line_shape='spline', mode='lines', fill='tozeroy', name='piano'))
    fig_all.layout.template = 'plotly_dark'
    fig_all.layout.xaxis.title = "Time (sec.)"
    fig_all.update_traces(hoverinfo='text+name', mode='lines')
    fig_all.update_layout(
        xaxis=dict(
            rangeslider=emocomp.posZoomSlider,
        ),
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=400,
        margin={"r":0,"t":40,"l":0,"b":0})
    end_time =time.time() - start_time
    return fig_all, end_time
#---------------------------------------------------------------------------------------------------------------------
def arrayToWavPCM16(data, outFile, sampleRate):
    # Convert to (little-endian) 16 bit integers.
    w = ((data * 32767).astype("<h"))
    with wave.open(outFile, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)# 2 bytes per sample.
        f.setframerate(sampleRate)
        f.writeframes(w.tobytes())
#---------------------------------------------------------------------------------------------------------------------
def writeSplitResultsAsWav(data, typeTrack):
    outfile = "./temps/" + typeTrack + ".wav"
    arrayToWavPCM16(data, outfile, 44100)
    #wavf.write(outfile, 44100, data)#data.astype(np.int16))
    #progressor:
    progressState=[20,30,30,0,0]
    return progressState
#---------------------------------------------------------------------------------------------------------------------
def splitWriteOutTracks(pool, n_split):
    start_time = time.time()
    vocal = pool["waveform_vocals"].squeeze()
    writeSplitResultsAsWav(vocal[:,0], 'vocal')#[:,0]
    section_name="waveform_other"
    if n_split == 2:
        section_name="waveform_accompaniment"
    other = pool[section_name].squeeze()
    writeSplitResultsAsWav(other[:,0], 'other')#MONO!!!!
    if n_split > 2:
        drums = pool["waveform_drums"].squeeze()
        writeSplitResultsAsWav(drums[:,0], 'drums')
        bass = pool["waveform_bass"].squeeze()
        writeSplitResultsAsWav(bass[:,0], 'bass')
        #if n_split == 5:
        #    piano = pool["waveform_piano"].squeeze()
        #    writeSplitResultsAsWav(piano[:,0], 'piano')
    write_time = time.time() - start_time
    
    #speechRecognitor(vocal[:,0])
    return write_time
#---------------------------------------------------------------------------------------------------------------------
splitProgressStatus = [0,0,0,0,0]

def splitVocalMinus(file_path_name, n_split):
    start_time = time.time()
    input_pool, input_audio, prep_time = splitSetInput(file_path_name)
    out_pool, proc_time = splitProcess(input_pool, input_audio, n_split)
    fig_split, plot_time = splitCalcGraph(input_audio, out_pool, n_split, plot_density=4100)
    fig_inst = estimateVocalInstrumental(file_path_name)
    save_time = splitWriteOutTracks(out_pool, n_split)
    fig_rev, fig_pitch = estimateVocalReverbPitch("./temps/vocal.wav")
    total_time = "Vocal Splitter:: total time: " + str(round((time.time() - start_time), 2)) + " sec."
    print(total_time)
    return fig_split, fig_rev, fig_inst, fig_pitch, total_time
    
    #progressor:
    #progress=[20,80,0]
#---------------------------------------------------------------------------------------------------------------------

def estimateVocalReverbPitch(file):
    audio = essentia.standard.MonoLoader(filename=file, sampleRate=16000, resampleQuality=4)()
    embedding_model = essentia.standard.TensorflowPredictEffnetDiscogs(graphFilename="./models/discogs-effnet-bs64-1.pb", output="PartitionedCall:1")
    embeddings = embedding_model(audio)
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/nsynth_reverb-discogs-effnet-1.pb", output="model/Softmax")
    predictions = model(embeddings)
    
    legend=["vocal reverb", "dry mix"]
    fig = emocomp.getTemplateFigure2T(predictions, legend)
    
    fig_pitch=calcMelodyPitch(audio)
    return fig, fig_pitch

def estimateVocalInstrumental(file):
    audio = essentia.standard.MonoLoader(filename=file, sampleRate=16000, resampleQuality=4)()
    embedding_model = essentia.standard.TensorflowPredictEffnetDiscogs(graphFilename="./models/discogs-effnet-bs64-1.pb", output="PartitionedCall:1")
    embeddings = embedding_model(audio)
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/voice_instrumental-discogs-effnet-1.pb", output="model/Softmax")
    predictions = model(embeddings)
    legend = ["instrumental", "vocal"]
    fig = emocomp.getTemplateFigure2T(predictions, legend)
    return fig

def calcMelodyPitch(audio):
    start_time = time.time()
    pitch, _ = essentia.standard.PitchMelodia()(audio)
    dom_pitch, _ = essentia.standard.PredominantPitchMelodia()(audio)
    
    #prepare for graphs:
    pitch_plot = pitch[::16]#xstep==32k
    np.place(pitch_plot, pitch_plot == 0, None)
    dom_pitch_plot = dom_pitch[::16]#xstep==32k
    np.place(dom_pitch_plot, dom_pitch_plot == 0, None)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=dom_pitch_plot, name="melody", mode='markers+lines', marker_size=4))
    fig.add_trace(go.Scatter(y=pitch_plot, name="backup", mode='markers+lines', opacity=0.5, marker_size=3))
    
    #fig.add_trace(go.Scatter(y=pitch_yin, name="Pitch-Yin"))
    fig.layout.template = 'plotly_dark'
    fig.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=200,
        margin={"r":10,"t":40,"l":10,"b":0},
    )
    #print(round((time.time() - start_time), 2))
    return fig

def speechRecognitor(audio, lang="eng"):
    sample = speech_r.WavFile("./temps/vocal.wav")
    r = speech_r.Recognizer()
    with sample as audio:
        r.adjust_for_ambient_noise(audio)
        content = r.record(audio)
    out_text=r.recognize_google(content, language=lang, show_all=True)
    print(out_text)#