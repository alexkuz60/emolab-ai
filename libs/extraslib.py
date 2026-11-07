import time

import scipy
import sklearn.cluster  #for K-Means
import librosa

import essentia
import essentia.standard

import numpy as np

#import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as colors
import plotly.io as pio
pio.templates.default = "plotly_dark"

import libs.emofunc as emofunc
import libs.emolist as emolist

# LaplacianSegmentation:
def calcLaplacianSegmentation(file_path_name, nSeg):
    y, sr = librosa.load(file_path_name)
    start_time=time.time()
    # Compute log-power CQT
    BINS_PER_OCTAVE = 12 * 3
    N_OCTAVES = 7
    C = librosa.amplitude_to_db(np.abs(librosa.cqt(y=y, sr=sr, bins_per_octave=BINS_PER_OCTAVE,
                                n_bins=N_OCTAVES * BINS_PER_OCTAVE)), ref=np.max)

    # Reduce dimensionality: beat-synchronous the CQT
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, trim=False)
    Csync = librosa.util.sync(C, beats, aggregate=np.median)

    # Timing of the beats::fix_frames to include non-beat frames 0 and C.shape[1] (final frame) ---For plotting: 
    beat_times = librosa.frames_to_time(librosa.util.fix_frames(beats, x_min=0),sr=sr)

    # Build a weighted recurrence matrix using beat-synchronous CQT (Equation 1)
    # width=3 prevents links within the same bar, mode='affinity' here implements S_rep (after Eq. 8)
    R = librosa.segment.recurrence_matrix(Csync, width=3, mode='affinity', sym=True)

    # Enhance diagonals with a median filter (Equation 2)
    df = librosa.segment.timelag_filter(scipy.ndimage.median_filter)
    Rf = df(R, size=(1, 7))

    # Build the sequence matrix (S_loc) using mfcc-similarity
    # $R_\text{path}[i, i\pm 1] = \exp(-\|C_i - C_{i\pm 1}\|^2 / \sigma^2)$
    # Take $\sigma$ to be the median distance between successive beats.
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    Msync = librosa.util.sync(mfcc, beats)

    path_distance = np.sum(np.diff(Msync, axis=1)**2, axis=0)
    sigma = np.median(path_distance)
    path_sim = np.exp(-path_distance / sigma)

    R_path = np.diag(path_sim, k=1) + np.diag(path_sim, k=-1)

    # Compute the balanced combination (Equations 6, 7, 9)
    deg_path = np.sum(R_path, axis=1)
    deg_rec = np.sum(Rf, axis=1)
    mu = deg_path.dot(deg_path + deg_rec) / np.sum((deg_path + deg_rec)**2)
    A = mu * Rf + (1 - mu) * R_path

    # Compute the normalized Laplacian (Eq. 10)
    L = scipy.sparse.csgraph.laplacian(A, normed=True)
    # spectral decomposition
    evals, evecs = scipy.linalg.eigh(L)
    # clean this up further with a median filter..# This can help smooth over small discontinuities
    evecs = scipy.ndimage.median_filter(evecs, size=(9, 1))
    # cumulative normalization is needed for symmetric normalize laplacian eigenvectors
    Cnorm = np.cumsum(evecs**2, axis=1)**0.5
    # For k clusters: use the first k normalized eigenvectors.
    # Fun exercise: see how the segmentation changes as you vary k
    k = nSeg #default == 5
    X = evecs[:, :k] / Cnorm[:, k-1:k]

    # K-components to cluster beats into segments (Algorithm 1)
    KM = sklearn.cluster.KMeans(n_clusters=k, n_init="auto")
    seg_ids = KM.fit_predict(X)
    # Locate segment boundaries from the label sequence
    bound_beats = 1 + np.flatnonzero(seg_ids[:-1] != seg_ids[1:])
    # Count beat 0 as a boundary
    bound_beats = librosa.util.fix_frames(bound_beats, x_min=0)
    # Compute the segment label for each boundary
    bound_segs = list(seg_ids[bound_beats])
    # Convert beat indices to frames
    bound_frames = beats[bound_beats]
    # Make sure what cover to the end of the track
    bound_frames = librosa.util.fix_frames(bound_frames, x_min=None, x_max=C.shape[1]-1)
    # Plot the final segmentation over original CQT
    bound_times = librosa.frames_to_time(bound_frames)
    freqs = librosa.cqt_frequencies(n_bins=C.shape[0], fmin=librosa.note_to_hz('C1'), bins_per_octave=BINS_PER_OCTAVE)
    #time_seg = "Total time for process: " + str(round((time.time() - start_time), 3)) + " sec."

    x_start = 0
    x_end = 0
    #y_end = max(freqs)
    fill_colors=colors.DEFAULT_PLOTLY_COLORS

    fig = go.Figure()
    fig.add_trace(go.Heatmap(x=beat_times, y=freqs, z=Csync, zauto= True, showscale=False))
    #fig.add_trace(go.Scatter(x=x_rects, y=y_rects, fill="toself", fillcolor=fill_colors[label], opacity=0.35))
    for interval, label in zip(zip(bound_times, bound_times[1:]), bound_segs):
        x_end = x_start + interval[1] - interval[0]
        fig.add_vrect(x0=x_start, x1=x_end, annotation_text=str(label), fillcolor=fill_colors[label], opacity=0.25)
        x_start = x_end
    #fig.layout.template = 'plotly_dark'
    fig.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=400,
        margin={"r":10,"t":40,"l":10,"b":0},
    )
    fig.update_yaxes(range=[0, 2**12])  #, type="log", exponentformat="power", base=2
    fig.update_xaxes(range=[0, x_end]) # %% track_time
    return fig
#----------------------------------------------------------------------------------------------------------------------------

def getStyleMap(embedding_nn):
    #instrument40_map:
    model = essentia.standard.TensorflowPredict2D(
        graphFilename="./models/mtg_jamendo_top50tags-discogs-effnet-1.pb")    #, output="model/Softmax")
    predictions = model(embedding_nn)
    predictions=predictions[:,:31] #only styles
    predictions = predictions**2 / np.max(predictions)
    sum_styles = sum(predictions)
    np.place(predictions, predictions < 0.015, None)
    
    #styles map:
    jam_legend31 = emolist.jam_style_map31
    
    x_sec=np.arange(0, np.shape(predictions)[0])
    fig_style = go.Figure()
    
    fig_style.add_trace(go.Heatmap(x=x_sec, y=jam_legend31, z=predictions, zauto= False, showscale=False))
    fig_style.add_trace(go.Bar(x=sum_styles, y=jam_legend31, orientation='h', opacity= 0.75, name="Styles summary"))
    fig_style.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=31*16,
        margin={"r":10,"t":40,"l":10,"b":0},
    )
    fig_style.update_traces(selector="heatmap", transpose=True, colorscale="Greens", reversescale=True, opacity= 0.95)#, zmin=0.05, zmax=np.max(predictions)
    fig_style.update_yaxes(autorange="reversed", showgrid=True, showline=True)
    
    return fig_style, sum_styles #time_inst
#-------------------------------------------------------------------------------------------------------------------------

def getInstrumentMap(embedding_nn):
    #instrument40_map:
    model = essentia.standard.TensorflowPredict2D(
        graphFilename="./models/mtg_jamendo_instrument-discogs-effnet-1.pb")    #, output="model/Softmax")
    predictions = model(embedding_nn)
    predictions = predictions**2 / np.max(predictions)
    predictions[:,-1]= predictions[:,-1]*2 #accent vocal
    sumData = np.sum(predictions, axis=0)
    np.place(predictions, predictions < 0.015, None)

    legend40 = emolist.instrument_map40
    """
    fig_inst_hist = go.Figure()
    fig_inst_hist.add_trace(go.Bar(x=legend40, y=sumData))
    fig_inst_hist.update_layout(height=250, margin={"r":10,"t":20,"l":10,"b":40})
    """
    x_sec=np.arange(0, np.shape(predictions)[0])
    #x_sec=np.arange(0, len(dataSelected))
    
    fig_map = go.Figure()
    fig_map.add_trace(go.Heatmap(x=x_sec, y=legend40, z=predictions, zauto= False, showscale=False))#
    fig_map.add_trace(go.Bar(x=sumData, y=legend40, orientation='h', opacity= 0.75, name="Instruments summary"))
    fig_map.update_traces(selector="heatmap", transpose=True, colorscale="Greens", reversescale=True, opacity= 0.95)#, zmin=0.05, zmax=np.max(predictions)
    fig_map.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10), showlegend=True,
        height=16*40, margin={"r":10,"t":40,"l":10,"b":0})
    fig_map.update_yaxes(autorange="reversed", showgrid=True, showline=True)
    #fig.update_xaxes(range=[0, np.shape(predictions)[0]]) # %% track_time

    #emofunc.addToNpy(fig, file, "extras")
    #time_inst = str(round((time.time() - start_time), 2))

    return fig_map#, time_inst
#--------------------------------------------------------------------------------------------------------------------------------------

def getExtrasHitPredictor(embedding_nn, kstyle):
    #approach:
    model = essentia.standard.TensorflowPredict2D(
        graphFilename="./models/approachability_2c-discogs-effnet-1.pb", output="model/Softmax")
    predict_app = model(embedding_nn)
    
    #engagment:
    model = essentia.standard.TensorflowPredict2D(
        graphFilename="./models/engagement_2c-discogs-effnet-1.pb", output="model/Softmax")
    predict_eng = model(embedding_nn)

    #danceability:
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/danceability-discogs-effnet-1.pb", output="model/Softmax")
    predict_dance = model(embedding_nn)

    #mood_party:
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/mood_party-discogs-effnet-1.pb", output="model/Softmax")
    predict_party = model(embedding_nn)

    #tonal/atonal:
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/tonal_atonal-discogs-effnet-1.pb", output="model/Softmax")
    predict_aton = model(embedding_nn)


    data_app = predict_app[:,1]
    data_eng = predict_eng[:,1]
    data_dance = predict_dance[:,1]
    data_party = predict_party[:,1]
    data_aton = predict_aton[:,1]
    mean_app = ": " + str(round(np.mean(data_app), 2))
    mean_eng = ": " + str(round(np.mean(data_eng), 2))
    mean_dance = ": " + str(round(np.mean(data_dance), 2))
    mean_party = ": " + str(round(np.mean(data_party), 2))
    mean_aton = ": " + str(round(np.mean(data_aton), 2))
    print(len(data_app), len(data_eng), len(data_dance), len(data_party), len(data_aton))
    
    fig_hit = go.Figure()
    fig_hit.add_trace(go.Scatter(y=data_app, line_shape='spline', mode='lines', fill='tozeroy', name="Pop-mass" + mean_app))
    fig_hit.add_trace(go.Scatter(y=data_eng, line_shape='spline', mode='lines', fill='tozeroy', name="Engagment" + mean_eng))
    fig_hit.add_trace(go.Scatter(y=data_dance, line_shape='spline', mode='lines', fill='tozeroy', name="Danceability" + mean_dance))
    fig_hit.add_trace(go.Scatter(y=data_party, line_shape='spline', mode='lines', fill='tozeroy', name="Background" + mean_party))
    fig_hit.add_trace(go.Scatter(y=data_aton, line_shape='spline', mode='lines', fill='tozeroy', name="Atonality" + mean_aton))
    fig_hit.layout.xaxis.title = "Time (sec.)"
    fig_hit.update_traces(hoverinfo='text+name', mode='lines')
    fig_hit.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=300,
        margin={"r":0,"t":40,"l":0,"b":0})
    
    intel = 0.3*kstyle[0]+kstyle[4]+0.6*kstyle[8]+kstyle[9]+kstyle[11]+0.3*kstyle[14]+kstyle[16]+0.1*kstyle[18]+kstyle[20]+kstyle[25]
    pop = 0.7*kstyle[0]+0.6*kstyle[5]+0.7*kstyle[6]+kstyle[10]+0.6*kstyle[14]+0.9*kstyle[18]+0.2*kstyle[19]+kstyle[21]+kstyle[22]+kstyle[23]+kstyle[24]+kstyle[30]
    bground = kstyle[1]+kstyle[2]+kstyle[3]+0.3*kstyle[6]+kstyle[7]+0.4*kstyle[8]+kstyle[12]+kstyle[13]+0.1*kstyle[14]+kstyle[15]+kstyle[17]+0.8*kstyle[19]+kstyle[26]+kstyle[27]+kstyle[28]+kstyle[29]
    print("i-p-b style: ", intel, pop, bground)
    data_intel = data_eng + data_aton
    data_pop = data_app# + data_dance
    data_bgraund = data_party
    print("i-p-b hit: ", sum(data_intel), sum(data_pop), sum(data_bgraund))
    data_zero=np.zeros(len(data_app))
    fig_for = go.Figure()
    fig_for.add_trace(go.Scatterternary(a=data_intel, b=data_pop, c=data_bgraund, mode="markers"))
    fig_for.update_ternaries(
        aaxis_title=dict(text='Intellectual'),
        baxis_title=dict(text='Mainstream'),
        caxis_title=dict(text='Background'),
    )
    fig_for.update_traces(cliponaxis=False, marker_size=8, selector=dict(type='scatterternary')) #marker_color=["lightblue", "lightgreen","yellow"], 
    fig_for.update_layout(height=600)#)marker_= dict(color = ["blue", "green","red"], 
    #time_hit = str(round((time.time() - start_time), 2))
    return fig_hit, fig_for#, time_hit
#--------------------------------------------------------------------------------------------------------------------------------------

def getExtrasMoodEmo(embedding_nn):
    #aggressive:
    model = essentia.standard.TensorflowPredict2D(
        graphFilename="./models/mood_aggressive-discogs-effnet-1.pb", output="model/Softmax")
    predict_agg = model(embedding_nn)
    
    #happy:
    model = essentia.standard.TensorflowPredict2D(
        graphFilename="./models/mood_happy-discogs-effnet-1.pb", output="model/Softmax")
    predict_happy = model(embedding_nn)

    #relax:
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/mood_relaxed-discogs-effnet-1.pb", output="model/Softmax")
    predict_relax = model(embedding_nn)

    #sad:
    model = essentia.standard.TensorflowPredict2D(graphFilename="./models/mood_sad-discogs-effnet-1.pb", output="model/Softmax")
    predict_sad = model(embedding_nn)

    data_agg = predict_agg[:,0]
    data_happy = predict_happy[:,0]
    data_relax = predict_relax[:,0]
    data_sad = predict_sad[:,0]

    mean_agg = ": " + str(round(np.mean(data_agg), 2))
    mean_happy = ": " + str(round(np.mean(data_happy), 2))
    mean_relax = ": " + str(round(np.mean(data_relax), 2))
    mean_sad = ": " + str(round(np.mean(data_sad), 2))
  
    print(len(data_agg), len(data_happy), len(data_relax), len(data_sad))
    
    fig_emo = go.Figure()
    fig_emo.add_trace(go.Scatter(y=data_agg, line_shape='spline', mode='lines', fill='tozeroy', name="Aggressive" + mean_agg))
    fig_emo.add_trace(go.Scatter(y=data_happy, line_shape='spline', mode='lines', fill='tozeroy', name="Happyness" + mean_happy))
    fig_emo.add_trace(go.Scatter(y=data_relax, line_shape='spline', mode='lines', fill='tozeroy', name="Relaxed" + mean_relax))
    fig_emo.add_trace(go.Scatter(y=data_sad, line_shape='spline', mode='lines', fill='tozeroy', name="Sadness" + mean_sad))
    fig_emo.layout.xaxis.title = "Time (sec.)"
    fig_emo.update_traces(hoverinfo='text+name', mode='lines')
    fig_emo.update_layout(
        legend=dict(orientation="h", yanchor = "top", y=10),
        showlegend=True,
        height=300,
        margin={"r":0,"t":40,"l":0,"b":0})
    
    #time_hit = str(round((time.time() - start_time), 2))
    return fig_emo#, time_hit
#--------------------------------------------------------------------------------------------------------------------------------------
def calcExtras(audiofile, nSeg):
    figs = []
    start_time = time.time()
    file_path_name = "./audio/"+audiofile
    fig_seg = calcLaplacianSegmentation(file_path_name, nSeg)
    figs.append(fig_seg)
    #yield 10
    
    audio = essentia.standard.MonoLoader(filename=file_path_name, sampleRate=16000, resampleQuality=4)()
    embedding_model = essentia.standard.TensorflowPredictEffnetDiscogs(
        graphFilename="./models/discogs-effnet-bs64-1.pb", output="PartitionedCall:1")
    embeddings = embedding_model(audio)
    
    fig_style, sum_styles = getStyleMap(embeddings)
    figs.append(fig_style)
    #yield 20
    fig_inst = getInstrumentMap(embeddings)
    figs.append(fig_inst)
    #yield 30
    
    fig_hit, fig_for = getExtrasHitPredictor(embeddings, sum_styles)
    figs.append(fig_hit)
    #yield 40
    figs.append(fig_for)
    #yield 50
    fig_emo = getExtrasMoodEmo(embeddings)
    figs.append(fig_emo)
    #yield 70
    outfile = "./extras/"+audiofile
    np.save(outfile, figs, allow_pickle=True)
    
    total_time = round((time.time() - start_time), 2)
    print(total_time)

    return figs