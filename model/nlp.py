import re
import string

# Define Indonesian stopwords (suitable for mental health sentiment/emotion classification)
INDONESIAN_STOPWORDS = {
    'yang', 'untuk', 'pada', 'ke', 'para', 'namun', 'menurut', 'antara', 
    'seperti', 'jika', 'sehingga', 'kembali', 'dan', 'ini', 'karena', 
    'kepada', 'oleh', 'saat', 'harus', 'sementara', 'setelah', 'belum', 
    'bahkan', 'bagi', 'serta', 'dengan', 'bahwa', 'sebelum', 'atau', 
    'begitu', 'secara', 'yaitu', 'terhadap', 'agar', 'lain', 'saja', 
    'hanya', 'itu', 'di', 'dari', 'telah', 'sebagai', 'masih', 'hal', 
    'ketika', 'adalah', 'tentang', 'sudah',
    # Additional pronouns
    'aku', 'saya', 'kamu', 'dia', 'mereka', 'kita', 'kami', 'nya', 'mu', 'ku',
    # Intensifiers
    'sangat', 'banget', 'sekali', 'amat', 'terlalu', 'paling', 'sungguh', 'benar',
    # Feeling verbs (neutral)
    'merasa', 'rasa', 'rasanya',
    # Time words
    'hari', 'besok', 'kemarin', 'sekarang', 'tadi', 'nanti',
    # Others
    'bisa', 'ada', 'tidak', 'tak', 'bukan'
}

# Slang and Typo Dictionary
TYPO_DICTIONARY = {
    'stress': 'stres', 'strees': 'stres', 'setres': 'stres', 'stees': 'stres',
    'depresi': 'depresi', 'depres': 'depresi',
    'tidor': 'tidur', 'tdr': 'tidur', 'tdur': 'tidur',
    'gk': 'tidak', 'nggak': 'tidak', 'ngga': 'tidak', 'gak': 'tidak', 'ndak': 'tidak',
    'krn': 'karena', 'karna': 'karena',
    'bgt': 'banget', 'bangat': 'banget',
    'kcewa': 'kecewa', 'keciwa': 'kecewa',
    'mrh': 'marah', 'mara': 'marah',
    'pd': 'pada',
    'yg': 'yang',
    'dgn': 'dengan',
    'klo': 'kalau', 'kalo': 'kalau',
    'capek': 'lelah', 'cape': 'lelah', 'cpe': 'lelah',
    'pusing': 'pusing', 'psing': 'pusing',
    'bosen': 'bosan',
    'nangis': 'menangis', 'nanggis': 'menangis',
    'sedih': 'sedih', 'sdi': 'sedih',
    'sdh': 'sudah', 'udah': 'sudah', 'udh': 'sudah',
    'blum': 'belum', 'blm': 'belum',
    'ortu': 'orang tua',
    'klg': 'keluarga', 'kluarga': 'keluarga',
    'kerjaan': 'pekerjaan', 'krjaan': 'pekerjaan',
    'ancur': 'hancur',
    'anjir': 'sangat', 'anj': 'sangat',
    'bgst': 'marah',
    'gila': 'gila',
    'bodo': 'bodoh', 'bego': 'bodoh', 'goblok': 'bodoh',
    'gt': 'begitu', 'gitu': 'begitu',
    'jd': 'jadi', 'jdi': 'jadi',
    'lg': 'lagi', 'lgi': 'lagi',
    'sm': 'sama',
    'tp': 'tapi',
    'nyesel': 'menyesal', 'nyesal': 'menyesal',
    'batin': 'batin',
    'mental': 'mental',
    'kesehatan': 'kesehatan',
    'kesepian': 'kesepian', 'sepi': 'kesepian',
    'takut': 'takut', 'tkt': 'takut',
    'cemas': 'cemas', 'cmas': 'cemas',
    'frustasi': 'frustasi', 'frustrasi': 'frustasi',
    'putus': 'putus', 'pts': 'putus',
    'selingkuh': 'selingkuh',
    'kuliah': 'kuliah', 'klh': 'kuliah'
}

import difflib

def correct_typos(text):
    if not text:
        return ""
        
    words = text.lower().split()
    corrected_words = []
    
    # Target keywords for fuzzy matching if not found in typo dict
    target_keywords = [
        'stres', 'tertekan', 'kewalahan', 'burnout',
        'psikolog', 'psikiater', 'konseling', 'konsultasi', 'terapi',
        'tidur', 'insomnia', 'begadang',
        'pacar', 'pasangan', 'hubungan', 'putus', 'selingkuh', 'teman', 'sahabat', 'keluarga',
        'kuliah', 'tugas', 'skripsi', 'ujian', 'nilai', 'kerja', 'kantor', 'bos', 'deadline', 'pekerjaan',
        'berguna', 'berharga', 'beban', 'menyusahkan', 'gagal', 'bodoh',
        'sedih', 'marah', 'kecewa', 'terluka', 'dendam', 'benci', 'menyesal', 'frustasi', 'takut', 'cemas', 'malu', 'kesepian'
    ]
    
    for word in words:
        clean_word = re.sub(r'[^\w\s]', '', word)
        
        # 1. Exact match in manual slang/typo dictionary
        if clean_word in TYPO_DICTIONARY:
            corrected_words.append(TYPO_DICTIONARY[clean_word])
            continue
            
        # 2. Fuzzy matching for slight typos (e.g., 'streesss' -> 'stres')
        if len(clean_word) > 3:
            matches = difflib.get_close_matches(clean_word, target_keywords, n=1, cutoff=0.8)
            if matches:
                corrected_words.append(matches[0])
                continue
                
        # If no typo detected, keep original
        corrected_words.append(word)
        
    return " ".join(corrected_words)

# Rule-based Stemmer for Indonesian (Fallback)
def stem_indonesian_word(word):
    original = word
    # Keep critical emotion terms intact
    if word in ['sedih', 'marah', 'kecewa', 'terluka', 'dendam', 'benci', 'menyesal', 
                'frustasi', 'takut', 'cemas', 'malu', 'kesepian', 'senang', 'cinta']:
        return word
        
    # 1. Remove inflectional suffixes (-lah, -kah, -pun, -ku, -mu, -nya)
    word = re.sub(r'(lah|kah|pun)$', '', word)
    word = re.sub(r'(ku|mu|nya)$', '', word)
    
    # 2. Remove derivational suffixes (-kan, -an, -i)
    word = re.sub(r'(kan|an|i)$', '', word)
    
    # 3. Remove derivational prefixes (di-, ke-, se-, te-, be-, me-, pe-)
    if word.startswith('di'):
        word = word[2:]
    elif word.startswith('ke'):
        word = word[2:]
    elif word.startswith('se') and not word.startswith('sedih') and not word.startswith('senang'):
        word = word[2:]
    elif word.startswith('ter') and not word.startswith('terluka') and not word.startswith('tersinggung'):
        word = word[3:]
    elif word.startswith('ber'):
        word = word[3:]
    elif word.startswith('be') and not word.startswith('benci'):
        word = word[2:]
    elif word.startswith('me'):
        if word.startswith('meng'):
            word = word[4:]
        elif word.startswith('meny'):
            word = 's' + word[4:]
        elif word.startswith('men'):
            word = word[3:]
        elif word.startswith('mem'):
            word = word[3:]
        else:
            word = word[2:]
    elif word.startswith('pe'):
        if word.startswith('peng'):
            word = word[4:]
        elif word.startswith('peny'):
            word = 's' + word[4:]
        elif word.startswith('pen'):
            word = word[3:]
        elif word.startswith('pem'):
            word = word[3:]
        else:
            word = word[2:]
            
    if len(word) < 3:
        return original
    return word

def preprocess_text(text):
    if not text:
        return ""
        
    # Apply typo correction first
    text = correct_typos(text)
    
    # 1. Case Folding
    text = text.lower()
    
    # Remove punctuation & numbers
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    
    # 2. Tokenization
    tokens = text.split()
    
    # 3. Stopword Removal
    tokens = [t for t in tokens if t not in INDONESIAN_STOPWORDS]
    
    # 4. Stemming
    try:
        from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
        factory = StemmerFactory()
        stemmer = factory.create_stemmer()
        stemmed_text = stemmer.stem(" ".join(tokens))
        return stemmed_text
    except Exception:
        # Fallback to custom rule-based stemmer
        stemmed_tokens = [stem_indonesian_word(t) for t in tokens]
        return " ".join(stemmed_tokens)
