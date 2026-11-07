#Emo Classificators:
emo_list7 = ["радость","вдохновение", "эйфория", "страх", "печаль", "депрессия","апатия"]

emo_list14=["страх", "трагичность",
            "скорбь", "разочарование",
            "депрессия", "покорность",
            "равнодушие", "интерес",
            "уверенность", "желание",
            "наслаждение", "кураж",
            "вдохновение", "эйфория"
]

emo_list28=["радость", "наслаждение", "энергичность", "кураж",
            "энтузиазм", "вдохновение","восторг", "эйфория",
            "агрессия", "страх", "тревога", "трагичность",
            "отчаяние","скорбь", "печаль", "разочарование",
            "опустошенность", "меланхолия", "уныние", "покорность",
            "апатия","равнодушие", "созерцание", "релакс",
            "спокойствие", "уверенность", "желание", "бодрость",
]

#!!!!!!!Пока можно использовать только как внешнюю Х-разметку проекции в пространство Рассела.
emo_list8 = [
    "аффект", "тревога",
    "печаль", "стресс",
    "апатия", "релакс",
    "радость", "восторг",
]

emo_list16=["радость", "энтузиазм", "вдохновение", "наслаждение", 
            "эйфория", "агрессия", "страх", "драма",
            'печаль',"депрессия", "меланхолия", "скука",
            "равнодушие", "релакс", "спокойствие", "безмятежность"
]

key_list = [
    ['C',0,1,0], ['C#',1,1,1], ['Db',1,1,1], ['D',2,1,2], ['D#',3,1,3], ['Eb', 3,1,3], ['E',4,1,4],
    ['F',5,1,5], ['F#',6,1,6], ['Gb',6,1,6], ['G',7,1,7], ['G#',8,1,8], ['Ab',8,1,8],
    ['A',-3,1,9], ['A#',-2,1,10], ['Bb', -2,1,10], ['B',-1,1,11],
    #minors:
    ['Cm',-3,0,0], ['C#m',-4,0,1], ['Dm',-5,0,2], ['Ebm',-6,0,3], ['Em',-7,0,4], ['Fm',-8,0,5], ['F#m', -9,0,6],
    ['Gm',-10,0,7], ['Abm',-11,0,8], ['Am',0,0,9], ['Bbm',-1,0,10], ['Bm',-2,0,11]
]

gamma_list = [
    ['C/Cm', 0], ['C#/Db', 1], ['D/Dm',2], ['D#/Eb',3], ['E/Em',4],  ['E#/Fb',5],
    ['F/Fm',6], ['F#/Gb',7], ['G/Gm',8], ['A/Am',9], ['A#/Bm',10], ['B/Bm',11]
]

bw_list = ['LD', 'D', 'Th', 'A', 'B', 'LG', 'HG']

plot_list = ['Spectrogram', 'Signal Wave', 'Chords Map', 'Tempo Map', 'Emogram']

instrument_map40 = ["accordion", "acoustic bass", "acoustic guitar", "bass", "beat", "bell", "bongo", "brass", "cello", "clarinet",
    "classical guitar", "computer", "double-bass", "drum-machine", "drums", "electric guitar", "electric piano", "flute", "guitar", "harmonica",
    "harp", "horn", "keyboard", "oboe", "orchestra", "organ", "pad", "percussion", "piano", "pipeorgan", "rhodes", "sampler", "saxophone",
    "strings", "synthesizer", "trombone", "trumpet", "viola", "violin", "voice"
]

jam_style_map31 = ["alternative", "ambient", "atmospheric", "chillout", "classical", "dance", "downtempo", "easy listening", "electronic",#[8]
    "experimental", "folk", "funk", "hip-hop", "house", "indie", "instrumental pop", "jazz", "lounge", "metal", "new age", "orchestral",#[20]
    "pop", "pop-folk", "pop-rock", "reggae", "rock", "soundtrack", "techno", "trance", "trip-hop", "world"
]
#intellectual: 0.3*alternative[0]+classic[4]+0.6*electronic[8]+experimental[9]+funk[11]+0.3*indie[14]+jazz[16]+0.1*metal[18]+orchestral[20]+rock[25]
#mainstream: 0.7*alternative[0]+0.6*dance[5]+0.7*downtempo[6]+folk[10]+0.6*indie[14]+0.9*metal[18]+0.2*new_age[19]+pop[21]+pop_folk[22]+pop_rock[23]
#       +reggie[24]+world[30]
#background: ambient[1]+atmospheric[2]+chillout[3]+0.3*downtempo[6]+easy_listening[7]+0.4*electronic[8]+hip_hop[12]+house[13]
#       +0.1*indie[14]+instrumental_pop[15]+lounge[17]+0.8*new ages[19]+soundtrack[26]+techno[27]+trance[28]+trip_hop[29]

jam_style_inst_map14 = ["acoustic guitar", "bass", "computer", "drum machine", "drums", "electric guitar",
"electric piano", "guitar", "keyboard", "piano", "strings", "synthesizer", "violin", "voice"
]

jam_style_emo_map5 = ["emotional", "energetic", "film", "happy", "relaxing"]

inst_11 = ['mallet', 'string', 'reed', 'guitar', 'synth_lead', 'vocal', 'bass', 'flute', 'keyboard', 'brass', 'organ']