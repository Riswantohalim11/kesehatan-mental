import pickle
from model.nlp import preprocess_text

v = pickle.load(open('model_nlp/vectorizer.pkl', 'rb'))
c = pickle.load(open('model_nlp/classifier.pkl', 'rb'))

tests = [
    # Greetings (should be Netral)
    'hai',
    'halo',
    'halo apa kabar',
    'selamat pagi',
    'assalamualaikum',
    'terima kasih sudah membantu',
    'biasa saja hari ini',
    'boleh tanya sesuatu?',
    # Emotional (should detect the correct emotion)
    'aku sedih sekali hari ini',
    'saya sangat marah dengan dia',
    'aku merasa tidak berguna',
    'aku sangat senang hari ini',
    'saya cemas menghadapi ujian besok',
    'aku benci sekali dengannya',
    'saya takut gagal lagi',
    'aku kesepian dan tidak ada teman',
    'aku menyesal telah melakukan itu',
    'aku frustasi dengan tugas kuliah',
]

netral_idx = list(c.classes_).index('Netral')

print('=' * 85)
print(f'{"INPUT":<42} {"RAW":<22} {"CONF":>5} {"N_CONF":>6}  {"FINAL"}')
print('=' * 85)

for t in tests:
    clean = preprocess_text(t)
    vec = v.transform([clean])
    raw_pred = c.predict(vec)[0]
    probs = c.predict_proba(vec)[0]
    idx = list(c.classes_).index(raw_pred)
    conf = probs[idx]
    n_conf = probs[netral_idx]
    
    # Smart Netral detection (same as app.py)
    if raw_pred == 'Netral':
        final = 'Netral'
    elif conf > n_conf * 1.5:
        final = raw_pred
    else:
        final = 'Netral'
    
    ok = '✓' if (final == 'Netral') == (t in tests[:8]) else '✗'
    print(f'{ok} {t:<40} {raw_pred:<22} {conf:>5.1%} {n_conf:>5.1%}  {final}')

print('=' * 85)
