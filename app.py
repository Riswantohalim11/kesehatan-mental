import os
import re
import datetime
import pickle
import pymysql
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, abort, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

# Dynamic import of DB models and NLP preprocessor
from model.models import db, User, MentalTest, TestResult, ChatHistory, EmotionResult, Category, Article, Service, Booking, Quote, Bookmark, ContactSetting, ContactMessage
from model.nlp import preprocess_text

# 1. Configuration
# Database credentials are read from environment variables in production.
# The defaults keep the application compatible with the existing local setup.
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '12345678')
DB_NAME = os.getenv('DB_NAME', 'kesehatan_mental')

SECRET_KEY = os.getenv('SECRET_KEY', 'mindhaven-secret-key-120481230')

# 2. Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_CERT_PATH = os.path.join(BASE_DIR, 'ca.pem')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{DB_NAME}"
)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'ssl': {
            'ca': CA_CERT_PATH
        }
    },
    'pool_pre_ping': True,
    'pool_recycle': 280
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Recommended production session settings.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'

# Init extensions
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom Jinja Filter for Article & Service Images (URL or Static relative path)
@app.template_filter('image_src')
def image_src_filter(image_url):
    if not image_url:
        return 'https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&q=80&w=800'
    if isinstance(image_url, str) and image_url.startswith(('http://', 'https://', '//', 'data:')):
        return image_url
    return url_for('static', filename=image_url)

# Admin Role Required Decorator
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Akses ditolak. Halaman ini hanya untuk Administrator.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# 3. Dynamic NLP Model Loading / Auto-Training on startup
vectorizer = None
classifier = None

def load_nlp_model():
    global vectorizer, classifier
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vectorizer_path = os.path.join(base_dir, 'model_nlp', 'vectorizer.pkl')
    classifier_path = os.path.join(base_dir, 'model_nlp', 'classifier.pkl')
    
    if not os.path.exists(vectorizer_path) or not os.path.exists(classifier_path):
        print("NLP Model files not found. Auto-training now...")
        try:
            from train_nlp import train_model
            train_model()
        except Exception as ex:
            print(f"Failed to auto-train NLP model: {ex}")
            return
            
    try:
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)
        with open(classifier_path, 'rb') as f:
            classifier = pickle.load(f)
        print("NLP Classifier & Vectorizer loaded successfully.")
    except Exception as ex:
        print(f"Failed to load NLP models: {ex}")

# 4. Standard Seed Data Setup
def seed_database():
    try:
        # A. Seed Admin User
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@mindhaven.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'adminpassword')
        if not User.query.filter_by(username=admin_username).first():
            admin = User(
                name='Administrator',
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                gender='Laki-laki',
                age=30,
                role='admin'
            )
            db.session.add(admin)
            print(f"Admin user seeded (username: {admin_username})")
            
        # B. Seed Quotes & Tips
        if not Quote.query.first():
            quotes = [
                Quote(
                    quote="Kesehatan mental bukan tujuan akhir, melainkan sebuah proses perjalanan tentang bagaimana Anda mengarungi kehidupan.",
                    author="Anonim",
                    tips="Cobalah luangkan waktu 5-10 menit setiap pagi untuk melakukan meditasi pernapasan sederhana guna merilekskan otot batin Anda."
                ),
                Quote(
                    quote="Tidak apa-apa merasa tidak baik-baik saja. Mengakui perasaan Anda adalah langkah awal yang sangat berani menuju pemulihan diri.",
                    author="Dr. Kristin Neff",
                    tips="Batasi paparan media sosial minimal 1 jam sebelum tidur untuk memberikan ketenangan pada gelombang otak Anda."
                ),
                Quote(
                    quote="Anda tidak bisa mengendalikan segalanya, namun Anda bisa mengendalikan bagaimana Anda merespons apa yang terjadi di sekitar Anda.",
                    author="Viktor Frankl",
                    tips="Bila pikiran terasa sangat penuh, ambil selembar kertas dan mulailah menuangkan semua kekhawatiran Anda (jurnalisme emosional)."
                ),
                Quote(
                    quote="Self-care bukanlah bentuk keegoisan, melainkan cara terbaik untuk menjaga agar diri Anda tetap mampu berkarya dan menyayangi sesama.",
                    author="Lalah Delia",
                    tips="Minumlah air putih yang cukup dan berjalanlah di bawah sinar matahari pagi selama 15 menit untuk memicu hormon kebahagiaan."
                )
            ]
            db.session.bulk_save_objects(quotes)
            print("Quotes and mental health tips seeded.")
            
        # C. Seed Categories
        if not Category.query.first():
            categories = [
                Category(name="Manajemen Stres"),
                Category(name="Mengatasi Kecemasan"),
                Category(name="Mengenali Depresi"),
                Category(name="Self-Care"),
                Category(name="Kesehatan Mental Mahasiswa")
            ]
            db.session.bulk_save_objects(categories)
            db.session.commit()
            print("Article categories seeded.")

        # D. Seed Services (Psychologist, Counselors, Hotlines)
        if not Service.query.first():
            services = [
                Service(
                    name="Layanan Kesehatan Jiwa Kemenkes RI",
                    specialty="Hotline Darurat Pencegahan Bunuh Diri & Konsultasi Psikiatri",
                    address="Seluruh Indonesia (Telepon Bebas Pulsa)",
                    contact="119 Ext 9",
                    category="Hotline Darurat"
                ),
                Service(
                    name="Into The Light Indonesia",
                    specialty="Pendampingan Komunitas Pencegahan Bunuh Diri & Krisis Emosional",
                    address="DKI Jakarta (Akses Online Seluruh Indonesia)",
                    contact="intothelight.id",
                    category="Hotline Darurat"
                ),
                Service(
                    name="Risa Amalia, M.Psi., Psikolog",
                    specialty="Psikolog Klinis Dewasa - Terapi Kognitif Perilaku (CBT)",
                    address="Jl. Melati No. 45, Kebayoran Baru, Jakarta Selatan",
                    contact="0812-3456-7890",
                    category="Psikolog"
                ),
                Service(
                    name="Dr. Hendra Gunawan, Sp.KJ",
                    specialty="Psikiater Klinis - Gangguan Mood & Manajemen Kecemasan",
                    address="Klinik Sehat Utama, Bandung",
                    contact="0819-8765-4321",
                    category="Psikolog"
                ),
                Service(
                    name="Andi Saputra",
                    specialty="Konselor Sebaya (Peer Counselor) - Konsultasi Remaja & Mahasiswa",
                    address="Pusat Kesejahteraan Mahasiswa, Yogyakarta",
                    contact="0857-1122-3344",
                    category="Konselor"
                )
            ]
            db.session.bulk_save_objects(services)
            print("Services and emergency hotlines seeded.")

        # E. Seed Articles
        if not Article.query.first():
            # Get category references
            cat_stres = Category.query.filter_by(name="Manajemen Stres").first()
            cat_cemas = Category.query.filter_by(name="Mengatasi Kecemasan").first()
            cat_depresi = Category.query.filter_by(name="Mengenali Depresi").first()
            cat_self = Category.query.filter_by(name="Self-Care").first()
            cat_mhs = Category.query.filter_by(name="Kesehatan Mental Mahasiswa").first()
            
            author = User.query.filter_by(email=admin_email).first()
            
            articles = [
                Article(
                    title="5 Langkah Praktis Manajemen Stres dalam Pekerjaan",
                    content="Stres di tempat kerja adalah tantangan umum yang dihadapi oleh banyak profesional. Untuk mencegah kelelahan mental (burnout), Anda dapat menerapkan lima langkah praktis berikut:\n\n1. Atur Skala Prioritas: Bagi pekerjaan Anda ke dalam kuadran penting dan mendesak. Jangan mencoba menyelesaikan semuanya sekaligus.\n2. Lakukan Istirahat Singkat: Gunakan teknik Pomodoro (25 menit bekerja, 5 menit istirahat) untuk memberi jeda pada otak Anda.\n3. Batasi Distraksi: Matikan notifikasi non-pekerjaan selama waktu fokus.\n4. Belajar Berkata 'Tidak': Jangan ragu menolak beban kerja tambahan jika kapasitas Anda sudah penuh.\n5. Terapkan Batasan Kerja: Hindari memeriksa email kantor setelah jam kerja selesai.\n\nDengan konsisten mempraktikkan hal ini, Anda dapat menjaga stabilitas mental di tengah tekanan karir.",
                    category_id=cat_stres.id if cat_stres else 1,
                    author_id=author.id if author else 1,
                    image_url=None
                ),
                Article(
                    title="Memahami Gangguan Kecemasan (Anxiety Disorder) dan Gejalanya",
                    content="Rasa cemas adalah respons emosional alami saat menghadapi tantangan. Namun, jika kecemasan berlangsung terus menerus tanpa pemicu yang jelas, itu bisa menjadi indikasi Gangguan Kecemasan.\n\nGejala fisik kecemasan meliputi:\n- Jantung berdebar kencang\n- Keringat dingin di telapak tangan\n- Sesak napas atau napas dangkal\n- Otot pundak dan leher tegang\n\nSedangkan gejala psikologis meliputi kekhawatiran berlebih yang tidak rasional tentang masa depan, sulit berkonsentrasi, hingga serangan panik mendadak. Bila Anda mendapati gejala ini mengganggu fungsi harian Anda lebih dari dua minggu, konsultasikan ke psikolog terdekat.",
                    category_id=cat_cemas.id if cat_cemas else 2,
                    author_id=author.id if author else 1,
                    image_url=None
                ),
                Article(
                    title="Pentingnya Mengenali Gejala Depresi Sejak Dini",
                    content="Depresi bukan sekadar rasa sedih biasa yang bisa hilang dalam satu atau dua hari. Depresi adalah gangguan suasana hati (mood) klinis yang mempengaruhi cara seseorang berpikir, merasa, dan bertindak.\n\nBeberapa gejala utama depresi yang perlu diwaspadai:\n1. Kehilangan minat total pada aktivitas yang sebelumnya sangat disukai.\n2. Merasa sangat lelah dan tidak berenergi sepanjang hari.\n3. Perasaan bersalah, merasa tidak berharga, atau putus asa tentang masa depan.\n4. Gangguan tidur (insomnia atau justru hipersomnia).\n5. Pikiran untuk menyakiti diri sendiri atau mengakhiri hidup.\n\nMengenali gejala ini sejak dini sangat penting agar penderita mendapatkan dukungan psikologis yang tepat.",
                    category_id=cat_depresi.id if cat_depresi else 3,
                    author_id=author.id if author else 1,
                    image_url=None
                ),
                Article(
                    title="Panduan Memulai Self-Care Sederhana untuk Pemula",
                    content="Self-care bukanlah bentuk kemewahan atau keegoisan. Self-care adalah aktivitas sadar yang kita lakukan untuk memelihara kesehatan fisik, mental, dan emosional kita.\n\nBerikut panduan memulai self-care gratis:\n- Tidur Cukup: Pastikan tidur berkualitas 7-8 jam per hari.\n- Nutrisi Baik: Konsumsi makanan bergizi dan minum air putih.\n- Hubungan Sosial: Hubungi sahabat dekat untuk mengobrol ringan.\n- Batasan Digital: Kurangi paparan berita buruk dengan melakukan detoks digital.\n- Belas Kasih Diri: Jangan terlalu keras menghakimi diri saat membuat kesalahan.\n\nSelf-care yang konsisten akan membentuk benteng pertahanan mental yang kuat.",
                    category_id=cat_self.id if cat_self else 4,
                    author_id=author.id if author else 1,
                    image_url=None
                ),
                Article(
                    title="Mengatasi Sindrom Impostor di Kalangan Mahasiswa",
                    content="Sindrom Impostor (Impostor Syndrome) adalah kondisi psikologis di mana seseorang merasa tidak pantas mendapatkan kesuksesannya dan takut dianggap sebagai penipu. Sindrom ini sangat sering melanda mahasiswa baru.\n\nGejala utamanya adalah merasa pencapaian akademis hanyalah faktor keberuntungan, membandingkan diri secara berlebihan dengan teman kuliah, serta takut berpartisipasi karena takut salah.\n\nCara mengatasinya:\n- Tulis daftar pencapaian konkret Anda.\n- Pahami bahwa membuat kesalahan adalah bagian dari proses belajar.\n- Bicarakan perasaan Anda dengan konselor kampus atau konselor sebaya.\n- Berhenti membandingkan proses internal Anda dengan tampilan luar orang lain.",
                    category_id=cat_mhs.id if cat_mhs else 5,
                    author_id=author.id if author else 1,
                    image_url=None
                )
            ]
            db.session.bulk_save_objects(articles)
            print("Educational articles seeded.")

        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print(f"Error seeding data: {ex}")

# 5. Questionnaire questions definition (20 questions per category)
SCREENING_QUESTIONS = {
    'Stres': [
        {"id": 1, "text": "Saya merasa mudah marah atau tersinggung oleh hal-hal kecil."},
        {"id": 2, "text": "Saya merasa tidak mampu mengatasi semua tanggung jawab saya."},
        {"id": 3, "text": "Saya merasa tegang dan sulit untuk rileks."},
        {"id": 4, "text": "Saya mengalami gangguan pencernaan atau sakit kepala karena tekanan."},
        {"id": 5, "text": "Saya merasa kewalahan dengan beban pikiran saya."},
        {"id": 6, "text": "Saya merasa sulit berkonsentrasi karena terlalu banyak pikiran."},
        {"id": 7, "text": "Saya merasa tidak memiliki waktu untuk diri sendiri."},
        {"id": 8, "text": "Saya merasa tidur saya tidak nyenyak karena memikirkan masalah."},
        {"id": 9, "text": "Saya merasa detak jantung saya meningkat tanpa aktivitas berat."},
        {"id": 10, "text": "Saya merasa tidak sabar menghadapi orang lain."},
        {"id": 11, "text": "Saya merasa tubuh saya lemas dan tidak berenergi."},
        {"id": 12, "text": "Saya merasa tertekan oleh tuntutan pekerjaan atau studi."},
        {"id": 13, "text": "Saya merasa cemas jika rencana tidak berjalan sesuai keinginan."},
        {"id": 14, "text": "Saya merasa nafsu makan saya terganggu (makan terlalu banyak atau terlalu sedikit)."},
        {"id": 15, "text": "Saya merasa emosi saya tidak stabil akhir-akhir ini."},
        {"id": 16, "text": "Saya merasa ingin menghindari interaksi dengan orang lain."},
        {"id": 17, "text": "Saya merasa sulit membuat keputusan, bahkan untuk hal kecil."},
        {"id": 18, "text": "Saya merasa otot-otot di tubuh saya tegang."},
        {"id": 19, "text": "Saya merasa tidak puas dengan hasil usaha saya."},
        {"id": 20, "text": "Saya merasa beban hidup saya semakin hari semakin berat."}
    ],
    'Kecemasan': [
        {"id": 1, "text": "Saya merasa cemas atau khawatir yang berlebihan tanpa alasan jelas."},
        {"id": 2, "text": "Jantung saya tiba-tiba berdebar kencang secara mendadak."},
        {"id": 3, "text": "Saya merasa gelisah dan tidak bisa diam tenang."},
        {"id": 4, "text": "Tangan atau tubuh saya gemetar saat menghadapi situasi baru."},
        {"id": 5, "text": "Saya merasa takut akan terjadi sesuatu yang buruk."},
        {"id": 6, "text": "Saya merasa sesak napas atau napas terasa dangkal saat panik."},
        {"id": 7, "text": "Saya merasa pusing atau kepala terasa melayang saat cemas."},
        {"id": 8, "text": "Saya mengalami ketegangan otot yang hebat di daerah leher dan bahu."},
        {"id": 9, "text": "Saya merasa berkeringat dingin di telapak tangan atau kaki."},
        {"id": 10, "text": "Saya merasa ketakutan saat berada di tempat yang ramai atau asing."},
        {"id": 11, "text": "Saya merasa tidak tenang saat harus berbicara di depan umum."},
        {"id": 12, "text": "Saya merasa khawatir dengan kesehatan fisik saya secara berlebihan."},
        {"id": 13, "text": "Saya merasa sulit untuk tertidur karena pikiran yang terus berputar."},
        {"id": 14, "text": "Saya merasa takut kehilangan kendali atas diri saya sendiri."},
        {"id": 15, "text": "Saya merasa mulut saya kering saat situasi menegangkan."},
        {"id": 16, "text": "Saya merasa terengah-engah tanpa melakukan aktivitas fisik berat."},
        {"id": 17, "text": "Saya merasa cemas jika berada jauh dari rumah atau zona nyaman."},
        {"id": 18, "text": "Saya merasa tidak berdaya saat serangan cemas datang."},
        {"id": 19, "text": "Saya sering membayangkan skenario terburuk dari suatu kejadian."},
        {"id": 20, "text": "Saya merasa panik secara tiba-tiba tanpa pemicu yang jelas."}
    ],
    'Depresi': [
        {"id": 1, "text": "Saya merasa sedih, hampa, atau murung sepanjang hari."},
        {"id": 2, "text": "Saya kehilangan minat atau kesenangan pada aktivitas yang biasanya saya sukai."},
        {"id": 3, "text": "Saya merasa tidak memiliki energi untuk melakukan aktivitas sehari-hari."},
        {"id": 4, "text": "Saya merasa tidak berharga atau bersalah tanpa alasan yang jelas."},
        {"id": 5, "text": "Saya merasa putus asa tentang masa depan saya."},
        {"id": 6, "text": "Saya merasa tidur saya terlalu banyak atau terlalu sedikit dari biasanya."},
        {"id": 7, "text": "Saya merasa nafsu makan saya menurun drastis atau meningkat tajam."},
        {"id": 8, "text": "Saya merasa sulit berkonsentrasi atau mengambil keputusan sederhana."},
        {"id": 9, "text": "Saya merasa ingin menarik diri sepenuhnya dari lingkungan sosial."},
        {"id": 10, "text": "Saya merasa lambat dalam berpikir, berbicara, atau bergerak."},
        {"id": 11, "text": "Saya merasa gelisah dan tidak tenang secara internal."},
        {"id": 12, "text": "Saya merasa hidup ini hampa dan tidak memiliki tujuan lagi."},
        {"id": 13, "text": "Saya sering menangis tanpa sebab yang jelas."},
        {"id": 14, "text": "Saya merasa tidak ada yang bisa memahami penderitaan saya."},
        {"id": 15, "text": "Saya merasa masa depan saya suram dan tidak menjanjikan."},
        {"id": 16, "text": "Saya merasa gagal sebagai seorang manusia."},
        {"id": 17, "text": "Saya merasa menjadi beban bagi orang-orang di sekitar saya."},
        {"id": 18, "text": "Saya merasa sulit untuk tersenyum atau tertawa dengan tulus."},
        {"id": 19, "text": "Saya merasa tidak ada lagi hal yang patut dinantikan dalam hidup."},
        {"id": 20, "text": "Saya merasa tidak bersemangat untuk memulai hari baru."}
    ]
}

# ==================== CONTROLLER ROUTES ====================

# (Home and Dashboard are merged below)

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        gender   = request.form.get('gender')
        age      = request.form.get('age')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not name or not email or not username or not password or not confirm_password:
            flash("Nama, Email, Username, dan Password wajib diisi.", "danger")
            return render_template('register.html')
            
        if password != confirm_password:
            flash("Konfirmasi password tidak cocok.", "danger")
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash("Alamat email sudah terdaftar. Silakan gunakan email lain atau masuk.", "danger")
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan. Pilih username lain.", "danger")
            return render_template('register.html')
            
        try:
            hashed_pw = generate_password_hash(password)
            new_user = User(
                name=name,
                username=username,
                email=email,
                gender=gender,
                age=int(age) if age else None,
                password_hash=hashed_pw,
                role='user'
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash(f"Akun '{name}' ({email}) berhasil dibuat! Silakan masuk.", "success")
            return redirect(url_for('login'))
        except Exception as ex:
            db.session.rollback()
            flash(f"Terjadi kesalahan saat pendaftaran: {ex}", "danger")
            
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        login_input = request.form.get('username', '').strip().lower()
        password    = request.form.get('password')
        
        # Support login using either Username or Email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        # Robust password verification supporting bcrypt ($2y$) and Werkzeug hashes
        is_valid = False
        if user and user.password_hash:
            try:
                if user.password_hash.startswith('$2y$') or user.password_hash.startswith('$2b$'):
                    # Convert PHP bcrypt format to python bcrypt format
                    hash_to_check = user.password_hash.replace('$2y$', '$2b$').encode('utf-8')
                    is_valid = bcrypt.checkpw(password.encode('utf-8'), hash_to_check)
                else:
                    is_valid = check_password_hash(user.password_hash, password)
            except (ValueError, TypeError):
                is_valid = False

        if is_valid:
            login_user(user)
            flash(f"Selamat datang kembali, {user.name}! 👋", "success")
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("Email/Username atau Password salah. Silakan coba lagi.", "danger")
            
    return render_template('login.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Anda berhasil keluar sistem.", "success")
    return redirect(url_for('home'))

# User Dashboard / Home Landing Page
@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    total_interactions = 0
    last_emotion = None
    dominant_emotion = None
    emotion_stats = []
    streak_count = 0
    recent_activities = []
    timeline_stats = []

    if current_user.is_authenticated:
        # Get summary data
        total_interactions = EmotionResult.query.filter_by(user_id=current_user.id).count()
        
        # Get dominant emotion
        dominant_query = db.session.query(
            EmotionResult.emotion_label, db.func.count(EmotionResult.id).label('count')
        ).filter(EmotionResult.user_id == current_user.id).group_by(EmotionResult.emotion_label).order_by(db.desc('count')).first()
        dominant_emotion = dominant_query[0] if dominant_query else None
        
        # Get statistics for charts
        # 1. Emotion distribution stats
        emotion_query = db.session.query(
            EmotionResult.emotion_label, db.func.count(EmotionResult.id).label('count')
        ).filter(EmotionResult.user_id == current_user.id).group_by(EmotionResult.emotion_label).all()
        
        emotion_stats = [{'emotion_label': eq[0], 'count': eq[1]} for eq in emotion_query]
        
        # 2. Timeline stats (Last 7 days)
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        timeline_query = db.session.query(
            db.func.date(EmotionResult.created_at).label('date'),
            EmotionResult.emotion_label,
            db.func.count(EmotionResult.id).label('count')
        ).filter(
            EmotionResult.user_id == current_user.id,
            EmotionResult.created_at >= seven_days_ago
        ).group_by(
            db.func.date(EmotionResult.created_at),
            EmotionResult.emotion_label
        ).order_by(db.func.date(EmotionResult.created_at).asc()).all()
        timeline_stats = [{'date': str(t[0]), 'emotion': t[1], 'count': t[2]} for t in timeline_query]
        
        # 3. Calculate Streaks
        interaction_dates = db.session.query(
            db.func.date(EmotionResult.created_at)
        ).filter(EmotionResult.user_id == current_user.id)\
         .group_by(db.func.date(EmotionResult.created_at))\
         .order_by(db.func.date(EmotionResult.created_at).desc()).all()
        
        if interaction_dates:
            latest_date = interaction_dates[0][0]
            today = datetime.datetime.now().date()
            if latest_date == today or latest_date == today - datetime.timedelta(days=1):
                streak_count = 1
                current_check_date = latest_date
                for i in range(1, len(interaction_dates)):
                    if interaction_dates[i][0] == current_check_date - datetime.timedelta(days=1):
                        streak_count += 1
                        current_check_date = interaction_dates[i][0]
                    else:
                        break
                        
        # 4. Recent activities
        recent_activities_records = EmotionResult.query.filter_by(user_id=current_user.id)\
            .order_by(EmotionResult.created_at.desc()).limit(5).all()
            
        emotion_emojis = {
            'Marah': '😠', 'Kecewa': '😞', 'Terlika': '😢', 'Dendam': '😡', 'Sakit hati': '💔',
            'Tersinggung': '😑', 'Benci': '🤬', 'Menyesal': '🥺', 'Frustasi': '😩', 'Takut': '😰',
            'Cemas': '😰', 'Malu': '😳', 'Kesepian': '👤', 'Sedih': '😢', 'Merasa tidak mampu': '😔',
            'Merasa putus asa': '😭', 'Merasa tidak berharga': '🥀', 'Merasa kecil': '🥺',
            'Merasa tidak di inginkan': '🖤', 'Senang': '😊', 'Netral': '💬'
        }
            
        recent_activities = [{
            'label': r.emotion_label,
            'emoji': emotion_emojis.get(r.emotion_label, '😐'),
            'date': r.created_at.strftime('%d %b %H:%M')
        } for r in recent_activities_records]
        
        # Get last emotion from db
        last_emotion_record = recent_activities_records[0] if recent_activities_records else None
        if last_emotion_record:
            last_emotion = {
                'label': last_emotion_record.emotion_label,
                'confidence': last_emotion_record.confidence,
                'emoji': emotion_emojis.get(last_emotion_record.emotion_label, '😐')
            }
        
        # Fetch user's consultation bookings
        user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    else:
        user_bookings = []

    # Daily quote
    quote_record = Quote.query.order_by(db.func.rand()).first()
    if not quote_record:
        quote_record = Quote(
            quote="Ambil napas dalam-dalam. Ini hanyalah hari yang buruk, bukan kehidupan yang buruk.",
            author="Anonim",
            tips="Gunakan teknik 4-7-8 untuk menenangkan detak jantung Anda: Tarik napas 4 detik, tahan 7 detik, embuskan perlahan 8 detik."
        )
        
    return render_template(
        'dashboard.html',
        active_page='dashboard',
        total_interactions=total_interactions,
        last_emotion=last_emotion,
        dominant_emotion=dominant_emotion,
        emotion_stats=emotion_stats,
        streak_count=streak_count,
        recent_activities=recent_activities,
        timeline_stats=timeline_stats,
        quote=quote_record,
        user_bookings=user_bookings,
        now=datetime.datetime.now()
    )

# Admin Dashboard
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Overall summary counts
    total_users = User.query.filter_by(role='user').count()
    total_tests = TestResult.query.count()
    total_bookings = Booking.query.count()
    pending_bookings_count = Booking.query.filter_by(status='Pending').count()
    approved_bookings_count = Booking.query.filter_by(status='Approved').count()
    total_articles = Article.query.count()
    total_services = Service.query.count()
    total_messages = ContactMessage.query.count()
    unread_messages_count = ContactMessage.query.filter_by(status='Unread').count()
    total_chats = ChatHistory.query.count()
    
    # Tables previews
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    recent_crisis_chats = ChatHistory.query.filter_by(is_crisis=True).order_by(ChatHistory.created_at.desc()).limit(5).all()
    contact_setting = get_contact_setting()
    
    # Stats charts queries
    # A. Aggregate emotions count
    admin_emotion_query = db.session.query(
        EmotionResult.emotion_label, db.func.count(EmotionResult.id).label('count')
    ).group_by(EmotionResult.emotion_label).all()
    emotion_stats = [{'emotion_label': eq[0], 'count': eq[1]} for eq in admin_emotion_query]
    
    # B. Aggregate test results breakdown
    admin_test_query = db.session.query(
        TestResult.test_category, TestResult.category_result, db.func.count(TestResult.id).label('count')
    ).group_by(TestResult.test_category, TestResult.category_result).all()
    test_stats = [{
        'category': t[0],
        'result': t[1],
        'count': t[2]
    } for t in admin_test_query]
    
    return render_template(
        'admin_dashboard.html',
        active_page='admin_dashboard',
        total_users=total_users,
        total_tests=total_tests,
        total_bookings=total_bookings,
        pending_bookings_count=pending_bookings_count,
        approved_bookings_count=approved_bookings_count,
        total_articles=total_articles,
        total_services=total_services,
        total_messages=total_messages,
        unread_messages_count=unread_messages_count,
        total_chats=total_chats,
        recent_users=recent_users,
        recent_bookings=recent_bookings,
        recent_messages=recent_messages,
        recent_crisis_chats=recent_crisis_chats,
        contact_setting=contact_setting,
        emotion_stats=emotion_stats,
        test_stats=test_stats
    )

# Relaksasi Route
@app.route('/relaksasi')
@login_required
def relaksasi():
    return render_template('relaksasi.html', active_page='relaksasi')


# Skrining Awal (Terintegrasi langsung di dalam Chatbot)
@app.route('/skrining')
@login_required
def skrining_awal():
    return redirect(url_for('chatbot'))

# API Skrining Submit
@app.route('/api/skrining/submit', methods=['POST'])
@login_required
def api_skrining_submit():
    data = request.get_json() or {}
    score = int(data.get('score', 0))
    category_result = data.get('category_result', 'Indikasi Beban Emosional')
    description = data.get('description', '')
    recommendation = data.get('recommendation', '')
    risk_response = data.get('risk_response', 'Tidak pernah')
    is_risk_high = bool(data.get('is_risk_high', False))
    
    risk_level = 'Tinggi' if is_risk_high else 'Rendah'
    
    # Simpan hasil ke database tabel test_results
    test_res = TestResult(
        user_id=current_user.id,
        test_category='Skrining Awal',
        score=score,
        category_result=category_result,
        description=description,
        recommendation=recommendation,
        risk_level=risk_level,
        risk_response=risk_response
    )
    db.session.add(test_res)
    db.session.commit()
    
    # Simpan ke session untuk integrasi langsung ke chatbot
    flask_session['recent_screening'] = {
        'id': test_res.id,
        'score': score,
        'category_result': category_result,
        'risk_response': risk_response,
        'risk_level': risk_level,
        'description': description
    }
    
    return jsonify({
        'status': 'success',
        'result_id': test_res.id,
        'score': score,
        'category_result': category_result
    })

# Detail Laporan Hasil Skrining
@app.route('/test/detail/<int:result_id>')
@login_required
def test_detail(result_id):
    result = TestResult.query.filter_by(id=result_id, user_id=current_user.id).first_or_404()
    return render_template('test_detail.html', result=result, active_page='profil')

# Riwayat Skrining
@app.route('/test/history')
@login_required
def test_history():
    results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.created_at.desc()).all()
    return render_template('test_history.html', results=results, active_page='profil')

# AI Chatbot Interface route
@app.route('/chatbot')
@login_required
def chatbot():
    import uuid
    session_id = request.args.get('session_id')
    new_session = request.args.get('new')
    from_screening = request.args.get('from_screening')
    
    # Jika baru selesai skrining, buka sesi baru dengan flag auto_screening
    if from_screening == '1':
        new_sid = uuid.uuid4().hex
        return redirect(url_for('chatbot', session_id=new_sid, auto_screening='true'))
        
    # Force new session creation if requested
    if new_session == 'true':
        new_sid = uuid.uuid4().hex
        return redirect(url_for('chatbot', session_id=new_sid))
        
    # Get all distinct sessions for sidebar
    sessions_query = db.session.query(
        ChatHistory.session_id,
        db.func.min(ChatHistory.created_at).label('start_time')
    ).filter(
        ChatHistory.user_id == current_user.id
    ).group_by(
        ChatHistory.session_id
    ).order_by(
        db.desc('start_time')
    ).all()
    
    chat_sessions = []
    for s in sessions_query:
        # Get first user message to use as the title
        first_msg = ChatHistory.query.filter_by(
            user_id=current_user.id,
            session_id=s.session_id,
            sender='user'
        ).order_by(ChatHistory.created_at.asc()).first()
        
        title = first_msg.message if first_msg else "Obrolan Tanpa Teks"
        chat_sessions.append({
            'session_id': s.session_id,
            'title': title,
            'created_at': s.start_time
        })
        
    # If no session_id is provided, direct to latest or new
    if not session_id:
        if chat_sessions:
            return redirect(url_for('chatbot', session_id=chat_sessions[0]['session_id']))
        else:
            new_sid = uuid.uuid4().hex
            return redirect(url_for('chatbot', session_id=new_sid))
            
    # Load messages for the selected session_id
    chat_history = ChatHistory.query.filter_by(
        user_id=current_user.id,
        session_id=session_id
    ).order_by(ChatHistory.created_at.asc()).all()
    
    hotlines = Service.query.filter_by(category='Hotline Darurat').all()
    current_time = datetime.datetime.now().strftime('%H:%M')
    recent_screening = flask_session.get('recent_screening')
    auto_screening = request.args.get('auto_screening') == 'true'
    
    return render_template(
        'chatbot.html', 
        active_page='chatbot', 
        chat_history=chat_history,
        chat_sessions=chat_sessions,
        selected_session_id=session_id,
        hotlines=hotlines,
        current_time=current_time,
        recent_screening=recent_screening,
        auto_screening=auto_screening
    )

# AI Chatbot NLP API Post endpoint
@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    global vectorizer, classifier
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message required'}), 400
        
    user_message = data['message']
    session_id = data.get('session_id', 'default')
    
    # Apply typo correction early for robust intent matching
    from model.nlp import correct_typos
    from model.responses import RESPONSES, ADVICES, SOLUTIONS
    import random
    import re
    import datetime
    
    corrected_message = correct_typos(user_message)
    msg_lower = corrected_message.lower()
    
    # 1. Intent & OOD Detection
    mh_keywords = [
        'stres', 'stress', 'tertekan', 'kewalahan', 'burnout', 'depresi', 'cemas', 'takut', 
        'marah', 'kecewa', 'sedih', 'nangis', 'kesepian', 'sendiri', 'benci', 'frustasi', 
        'lelah', 'capek', 'pusing', 'psikolog', 'psikiater', 'mental', 'emosi', 'perasaan', 
        'merasa', 'pikiran', 'overthinking', 'keluarga', 'ortu', 'pacar', 'hubungan', 
        'teman', 'sahabat', 'kerja', 'kuliah', 'sekolah', 'tugas', 'mati', 'bantu', 'curhat',
        'menyesal', 'dendam', 'tersinggung', 'luka', 'sakit', 'bingung', 'hancur', 'batin',
        'gagal', 'bodoh', 'beban', 'menyusahkan', 'tidur', 'insomnia', 'bunuh diri'
    ]
    has_mh_keyword = any(word in msg_lower for word in mh_keywords)
    
    is_greeting = False
    greeting_words = ['halo', 'hai', 'hey', 'hi', 'pagi', 'siang', 'sore', 'malam', 'assalamualaikum']
    words = msg_lower.split()
    if not has_mh_keyword and any(g in msg_lower for g in greeting_words):
        if len(words) <= 4:
            is_greeting = True

    is_ood = False
    ood_keywords = [
        'makan', 'makanan', 'resep', 'kuliner', 'masak', 'goreng', 'rebus', 'bakar', 'minum', 'kopi', 'teh',
        'coding', 'program', 'python', 'java', 'html', 'komputer', 'laptop', 'hp', 'teknologi', 'aplikasi',
        'olahraga', 'bola', 'basket', 'raket', 'lari', 'renang',
        'politik', 'presiden', 'pemilu', 'partai', 'pemerintah', 'menteri',
        'berita', 'koran', 'tv',
        'matematika', 'fisika', 'kimia', 'rumus', 'hitung',
        'sejarah', 'perang', 'kerajaan',
        'agama', 'tuhan', 'doa', 'ibadah', 'sholat', 'gereja',
        'rekomendasi', 'beli', 'harga', 'jual', 'diskon', 'promo',
        'game', 'main', 'ps', 'xbox', 'nintendo', 'mabar'
    ]
    
    if not is_greeting and not has_mh_keyword:
        if any(word in msg_lower for word in ood_keywords):
            is_ood = True

    # 2. Topic Detection
    topic_keywords = {
        'Skripsi': ['skripsi', 'tesis', 'draf', 'bab', 'dosen pembimbing', 'dospem', 'sidang', 'revisi', 'acc'],
        'Keluarga': ['keluarga', 'orang tua', 'ibu', 'ayah', 'mama', 'papa', 'kakak', 'adik', 'rumah', 'saudara', 'ortu'],
        'Pertemanan': ['teman', 'sahabat', 'tongkrongan', 'sirkel', 'circle', 'bestie', 'kawan'],
        'Hubungan/Pasangan': ['pacar', 'pasangan', 'kekasih', 'mantan', 'hubungan', 'cowokku', 'cewekku', 'selingkuh', 'putus'],
        'Pekerjaan': ['kerja', 'kantor', 'bos', 'atasan', 'rekan kerja', 'gaji', 'karir', 'phk', 'resign', 'deadline kerja'],
        'Pendidikan': ['kuliah', 'sekolah', 'kampus', 'tugas', 'ujian', 'ipk', 'nilai', 'jurusan', 'dosen', 'guru', 'belajar'],
        'Diri Sendiri': ['diri sendiri', 'masa depan', 'tujuan hidup', 'overthinking', 'beban', 'gak berguna', 'trauma', 'insecure']
    }
    
    detected_topic = None
    for topic, keywords in topic_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            detected_topic = topic
            break
            
    # Context building (last 3-5 messages)
    previous_messages = ChatHistory.query.filter_by(
        user_id=current_user.id,
        session_id=session_id,
        sender='user'
    ).order_by(ChatHistory.created_at.desc()).offset(0).limit(5).all()
    previous_messages = list(reversed(previous_messages)) # Oldest to newest
    
    # Topic Tracking: fallback to last known topic if not explicitly changed
    if not detected_topic:
        for pm in reversed(previous_messages):
            if pm.topic_label:
                detected_topic = pm.topic_label
                break
    if not detected_topic:
        detected_topic = 'Umum'

    # 3. Special Handler: Skrining Awal MindHaven
    is_screening = '[HASIL SKRINING AWAL MINDHAVEN]' in user_message or 'SKRINING AWAL' in user_message.upper()
    screening_data = {}
    
    if is_screening:
        # Periksa format 20 pertanyaan baru
        score_20_match = re.search(r'Total Skor (?:20 Pertanyaan)?\s*:\s*(\d+)', user_message, re.IGNORECASE)
        ind_match = re.search(r'Indikasi Kondisi[^\:]*:\s*([^\n\r]+)', user_message, re.IGNORECASE)
        risk_match = re.search(r'Pemeriksaan Keselamatan\s*:\s*([^\n\r]+)', user_message, re.IGNORECASE)
        
        if score_20_match:
            total_score = int(score_20_match.group(1))
            indication_text = ind_match.group(1).strip() if ind_match else 'Indikasi Beban Emosional'
            risk_text = risk_match.group(1).strip() if risk_match else 'Tidak pernah'
            
            is_risk_high = any(w in risk_text.lower() for w in ['sering', 'berisiko', 'tinggi']) or total_score >= 65
            is_crisis = is_risk_high
            
            detected_emotion = 'Risiko Tinggi' if is_crisis else ('Cemas' if total_score > 40 else 'Stres' if total_score > 20 else 'Netral')
            confidence = 0.95
            detected_topic = 'Diri Sendiri'
            
            if total_score <= 20:
                score_desc = "rendah dan relatif stabil"
                advice_text = "Pertahankan ritme harian yang seimbang, cukupi istirahat, dan luangkan waktu untuk hal-hal yang menyenangkan diri Anda."
            elif total_score <= 40:
                score_desc = "ringan hingga sedang, menandakan adanya beberapa tekanan atau kelelahan emosional yang mulai mengganjal"
                advice_text = "Cobalah untuk mengambil jeda sejenak dari aktivitas padat, lakukan pernapasan dalam, dan ceritakan apa saja yang sedang Anda pikirkan."
            elif total_score <= 60:
                score_desc = "cukup tinggi, menunjukkan adanya beban pikiran dan tekanan emosi yang cukup berat dalam 2 minggu terakhir"
                advice_text = "Kurangi tuntutan yang bisa ditunda, prioritaskan ketenangan diri, dan manfaatkan ruang ini untuk meluapkan perasaan tanpa ragu."
            else:
                score_desc = "sangat tinggi, menunjukkan bahwa Anda sedang mengalami kepenatan atau beban emosional yang berat dan perlu pendampingan"
                advice_text = "Sangat penting untuk mengutamakan pemulihan diri. Jangan ragu mencari dukungan dari orang terpercaya atau tenaga profesional kesehatan mental."
                
            screening_reply = f"""Halo {current_user.name}, terima kasih telah menyelesaikan check-in skrining awal Anda di MindHaven.

Berdasarkan hasil check-in 2 minggu terakhir, total skor Anda adalah <strong>{total_score} dari 80 poin</strong> dengan <strong>{indication_text}</strong> ({score_desc}).

Perlu kami ingatkan kembali bahwa hasil ini <strong>bukan merupakan diagnosis medis atau psikologis</strong>, melainkan gambaran awal kondisi emosional Anda saat ini.

<strong>Saran Awal:</strong>
{advice_text}

Saya di sini siap menjadi ruang aman untuk mendengarkan. Apa hal yang paling terasa mengganjal atau membebani pikiran Anda hari ini? Ceritakan saja dengan tenang, Anda tidak sendirian."""

            hotlines = []
            if is_crisis:
                hotlines_query = Service.query.filter_by(category='Hotline Darurat').all()
                hotlines = [{'name': h.name, 'contact': h.contact, 'address': h.address} for h in hotlines_query]
                
            reply = screening_reply
        else:
            # Fallback legacy screening parser
            scale_match = re.search(r'Skala beban perasaan\s*:\s*(\d+)', user_message, re.IGNORECASE)
            scale_val = int(scale_match.group(1)) if scale_match else 5
            
            cond_match = re.search(r'Masalah / Kondisi\s*:\s*([^\n\r]+)', user_message, re.IGNORECASE)
            conditions_text = cond_match.group(1).strip() if cond_match else 'Tidak disebutkan'
            
            hist_match = re.search(r'Riwayat penyakit[^\:]*:\s*([^\n\r]+)', user_message, re.IGNORECASE)
            history_text = hist_match.group(1).strip() if hist_match else 'Tidak ada'
            
            treat_match = re.search(r'Status penanganan[^\:]*:\s*([^\n\r]+)', user_message, re.IGNORECASE)
            treatment_text = treat_match.group(1).strip() if treat_match else 'Belum pernah konsultasi profesional'
            
            phys_match = re.search(r'Tanda masalah fisik\s*:\s*([^\n\r]+)', user_message, re.IGNORECASE)
            physical_text = phys_match.group(1).strip() if phys_match else 'Tidak ada keluhan fisik'
            
            severity_label = "ringan" if scale_val <= 3 else "sedang" if scale_val <= 6 else "berat" if scale_val <= 8 else "sangat berat / kritis"
            
            critical_conditions = ['putus asa', 'tidak berharga', 'tidak di inginkan', 'tidak diinginkan', 'bunuh diri', 'mati']
            has_critical_cond = any(c in conditions_text.lower() for c in critical_conditions)
            is_crisis = scale_val >= 9 or (scale_val >= 7 and has_critical_cond)
            
            if is_crisis:
                detected_emotion = 'Risiko Tinggi' if scale_val >= 9 else 'Putus asa'
            elif 'marah' in conditions_text.lower() or 'benci' in conditions_text.lower() or 'dendam' in conditions_text.lower():
                detected_emotion = 'Marah'
            elif 'kecewa' in conditions_text.lower() or 'sakit hati' in conditions_text.lower() or 'terluka' in conditions_text.lower():
                detected_emotion = 'Kecewa'
            elif 'cemas' in conditions_text.lower() or 'takut' in conditions_text.lower():
                detected_emotion = 'Cemas'
            elif 'sedih' in conditions_text.lower() or 'kesepian' in conditions_text.lower() or 'menyesal' in conditions_text.lower():
                detected_emotion = 'Sedih'
            elif 'frustasi' in conditions_text.lower() or 'tidak mampu' in conditions_text.lower():
                detected_emotion = 'Frustasi'
            else:
                detected_emotion = 'Stres' if scale_val >= 5 else 'Netral'
                
            confidence = 0.95
            detected_topic = 'Diri Sendiri'
            
            physical_insights = []
            phys_lower = physical_text.lower()
            if any(w in phys_lower for w in ['jantung', 'debar', 'dada']):
                physical_insights.append("Jantung berdebar atau sesak di dada adalah respons alami sistem saraf simpatik saat tubuh memproses kecemasan.")
            if any(w in phys_lower for w in ['kepala', 'pusing', 'migrain']):
                physical_insights.append("Sakit kepala atau pusing sering timbul akibat ketegangan pembuluh darah dan saraf karena beban pikiran.")
            if any(w in phys_lower for w in ['mual', 'perut', 'maag', 'lambung', 'pencernaan']):
                physical_insights.append("Keluhan lambung berkaitan dengan respons stres tubuh.")
            if any(w in phys_lower for w in ['otot', 'kaku', 'leher', 'bahu', 'tegang']):
                physical_insights.append("Ketegangan otot menandakan tubuh Anda terus menahan rasa waspada tanpa disadari.")
            if any(w in phys_lower for w in ['gemetar', 'tremor', 'keringat']):
                physical_insights.append("Tubuh gemetar atau keringat dingin merupakan pelepasan hormon adrenalin.")
            if any(w in phys_lower for w in ['lelah', 'lemas', 'energi']):
                physical_insights.append("Kelelahan fisik terjadi karena energi terkuras untuk menampung gejolak batin.")
                
            phys_summary = " ".join(physical_insights) if physical_insights else "Jaga kestabilan pikiran agar beban emosi tidak memicu gejala somatik."
            
            treat_lower = treatment_text.lower()
            if 'dokter' in treat_lower or 'psikolog' in treat_lower or 'psikiater' in treat_lower:
                treat_note = "Sangat baik Anda telah/sedang berkonsultasi secara profesional. Jadikan percakapan ini sebagai ruang refleksi tambahan."
            else:
                treat_note = "Anda telah mengambil langkah awal yang baik dengan melakukan check-in dan skrining mandiri di sini."
                
            step_action = "Lakukan teknik pernapasan 4-7-8 untuk merelaksasi sistem saraf Anda." if scale_val >= 7 else "Lakukan teknik Grounding 5-4-3-2-1 untuk memusatkan kembali pikiran Anda."
            
            screening_reply = f"""Halo {current_user.name}, terima kasih telah melakukan skrining awal di MindHaven.
            
Beban perasaan Anda saat ini berada pada <strong>skala {scale_val}/10 ({severity_label.upper()})</strong>.
{phys_summary}

{treat_note}

<strong>Langkah Pertama:</strong> {step_action}

Kapan pun Anda siap, silakan ceritakan hal yang paling membebani Anda saat ini."""

            hotlines = []
            if is_crisis:
                hotlines_query = Service.query.filter_by(category='Hotline Darurat').all()
                hotlines = [{'name': h.name, 'contact': h.contact, 'address': h.address} for h in hotlines_query]
                
            reply = screening_reply
        
    # Save User message to Chat History
    user_chat = ChatHistory(
        user_id=current_user.id,
        sender='user',
        message=user_message,
        session_id=session_id,
        topic_label=detected_topic
    )
    db.session.add(user_chat)
    db.session.commit()
    
    # 3. Emotion Measurement via trained TF-IDF + Naive Bayes Model (for non-screening messages)
    if not is_screening:
        detected_emotion = 'Netral'
        confidence = 1.0
        
        if is_greeting:
            detected_emotion = 'Sapaan'
        elif is_ood:
            detected_emotion = 'Di Luar Konteks'
        elif vectorizer and classifier:
            try:
                # Classification based primarily on current message for accurate emotion progression
                clean_msg = preprocess_text(user_message)
                
                if clean_msg.strip():
                    vector = vectorizer.transform([clean_msg])
                    prediction = classifier.predict(vector)[0]
                    probabilities = classifier.predict_proba(vector)[0]
                    class_index = list(classifier.classes_).index(prediction)
                    confidence = float(probabilities[class_index])
                    detected_emotion = prediction
            except Exception as ex:
                print(f"Error during NLP prediction: {ex}")
                detected_emotion = 'Netral'
                confidence = 0.5
                
        # Check Crisis keywords again just in case model misses it or if we want hard rules for safety
        crisis_keywords = ['bunuh diri', 'ingin mati', 'menyakiti diri', 'tidak ingin hidup', 'mengakhiri hidup']
        is_crisis = False
        if detected_emotion == 'Risiko Tinggi' or any(keyword in msg_lower for keyword in crisis_keywords):
            is_crisis = True
            detected_emotion = 'Risiko Tinggi'
            confidence = 1.0

    # Save detected emotion details to DB
    user_chat.emotion_label = detected_emotion
    user_chat.emotion_confidence = confidence
    user_chat.is_crisis = is_crisis
    
    emotion_log = EmotionResult(
        user_id=current_user.id,
        chat_id=user_chat.id,
        emotion_label=detected_emotion,
        confidence=confidence
    )
    db.session.add(emotion_log)
    db.session.commit()
    
    # 4. Formulate Bot Response (if not already formulated by screening handler)
    if not is_screening:
        reply = ""
        hotlines = []
        
        if is_crisis:
            crisis_responses = [
                f"Saya mendengar betapa beratnya beban yang Anda rasakan saat ini, {current_user.name}. Menghadapi pikiran seperti ini sendirian pasti sangat melelahkan dan menyakitkan, dan saya sangat menghargai keberanian Anda untuk mengungkapkannya di sini.\n\n<strong>Saran</strong>\nSebagai langkah awal, maukah Anda berjanji kepada saya untuk tetap aman hari ini? Cobalah tarik napas yang sangat dalam perlahan-lahan. Apakah ada seseorang di dekat Anda atau teman yang bisa dihubungi sekarang sekadar untuk menemani?\n\n<strong>Solusi</strong>\nSaya ingin memastikan Anda mendapatkan dukungan yang tepat. Jika Anda merasa kewalahan dan tidak tahu harus ke mana, tolong izinkan para profesional di bawah ini untuk mendengarkan cerita Anda lebih lanjut.",
                
                f"{current_user.name}, rasa putus asa yang Anda alami ini sangat nyata dan valid. Tidak apa-apa jika saat ini semuanya terasa runtuh dan gelap. Saya ada di sini mendengarkan Anda tanpa penghakiman sama sekali.\n\n<strong>Saran</strong>\nTolong jangan lakukan apa pun yang menyakiti diri Anda saat ini. Bisakah Anda mencari posisi duduk atau berbaring yang nyaman dan minum segelas air hangat? Bagaimana kondisi fisik Anda saat ini, apakah Anda merasa aman di tempat Anda sekarang?\n\n<strong>Solusi</strong>\nPerasaan segelap ini seringkali terlalu berat untuk dipikul sendirian. Ada orang-orang yang dilatih khusus untuk memegang tangan Anda melewati badai ini. Mohon pertimbangkan untuk menghubungi layanan darurat di bawah ini kapan pun Anda siap.",
                
                f"Hati saya ikut terasa berat mendengar apa yang Anda sampaikan, {current_user.name}. Sungguh tidak adil Anda harus memendam luka sedalam ini sendirian. Saya sangat peduli dengan keselamatan dan keberadaan Anda di dunia ini.\n\n<strong>Saran</strong>\nUntuk saat ini, mari fokus hanya pada bernapas dari menit ke menit. Jangan pikirkan hari esok dulu. Apakah ada satu benda di ruangan Anda yang bisa Anda genggam untuk membantu Anda merasa lebih tenang?\n\n<strong>Solusi</strong>\nAnda tidak harus berjuang memulihkan diri sendirian. Ada bantuan yang selalu terbuka untuk mendengarkan tangisan dan resah Anda kapan saja. Tolong, berikan kesempatan pada diri Anda dengan menghubungi salah satu kontak di bawah ini."
            ]
            reply = random.choice(crisis_responses)
            hotlines_query = Service.query.filter_by(category='Hotline Darurat').all()
            hotlines = [{'name': h.name, 'contact': h.contact, 'address': h.address} for h in hotlines_query]
        elif is_ood:
            ood_responses = [
                "Maaf, saya dirancang khusus untuk membantu percakapan seputar kesehatan mental, emosi, dan self-help. Saya belum dapat memberikan jawaban untuk topik di luar konteks tersebut.",
                "Maaf ya, saya fokus membantu pengguna dalam topik kesehatan mental dan pengelolaan emosi. Pertanyaan yang Anda ajukan berada di luar cakupan layanan saya."
            ]
            reply = random.choice(ood_responses)
        elif is_greeting:
            hour = datetime.datetime.now().hour
            time_greeting = "Selamat pagi" if hour < 11 else "Selamat siang" if hour < 15 else "Selamat sore" if hour < 18 else "Selamat malam"
            greetings = [
                f"{time_greeting}, {current_user.name}! 😊 Saya MindHaven, teman curhat AI Anda. Apa yang sedang Anda rasakan hari ini? Ceritakan saja dengan bebas, saya siap mendengarkan tanpa menghakimi.",
                f"Hai {current_user.name}! {time_greeting}. Senang bisa menemani Anda. Ada yang ingin Anda ceritakan atau ungkapkan hari ini? Saya di sini untuk Anda.",
                f"{time_greeting}, {current_user.name}! Bagaimana kabar Anda hari ini? Apapun yang Anda rasakan — senang, sedih, atau bingung — silakan ceritakan. Saya siap mendengarkan."
            ]
            reply = random.choice(greetings)
        else:
            # Emotion Progression Check
            transition_prefix = ""
            if previous_messages:
                last_user_msg = previous_messages[-1]
                last_emotion = last_user_msg.emotion_label
                # Only add transition if there's a clear change between significant emotions
                ignore_emotions = ['Netral', 'Sapaan', 'Di Luar Konteks']
                if last_emotion not in ignore_emotions and detected_emotion not in ignore_emotions and last_emotion != detected_emotion:
                    transitions = [
                        f"Saya perhatikan perasaan Anda mulai bergeser menjadi lebih {detected_emotion.lower()}... ",
                        f"Terdengar ada perubahan dalam emosi Anda sekarang, sepertinya Anda merasa {detected_emotion.lower()}. ",
                        f"Tadi Anda terdengar {last_emotion.lower()}, tapi sekarang saya menangkap rasa {detected_emotion.lower()} dari cerita Anda. ",
                        f"Menarik bagaimana perasaan Anda beralih dari {last_emotion.lower()} menjadi {detected_emotion.lower()}. "
                    ]
                    transition_prefix = random.choice(transitions)
                    
            # Retrieve mapped response based on Topic and Emotion
            if detected_emotion in RESPONSES:
                topic_responses = RESPONSES[detected_emotion].get(detected_topic, RESPONSES[detected_emotion].get('Umum', []))
                if topic_responses:
                    # Prevent response repetition by checking last bot reply
                    last_bot_reply = ChatHistory.query.filter_by(
                        user_id=current_user.id,
                        session_id=session_id,
                        sender='bot'
                    ).order_by(ChatHistory.created_at.desc()).first()
                    
                    available_responses = topic_responses.copy()
                    if last_bot_reply and len(available_responses) > 1:
                        # Check if the exact message is in available responses (without transition prefix)
                        for r in available_responses:
                            if r in last_bot_reply.message:
                                available_responses.remove(r)
                                break
                                
                    base_reply = random.choice(available_responses)
                    advice = random.choice(ADVICES.get(detected_emotion, ADVICES['Umum']))
                    solution = random.choice(SOLUTIONS.get(detected_topic, SOLUTIONS['Umum']))

                    # Extended deep empathetic validations per emotion
                    EMOTION_VALIDATIONS = {
                        "Sedih": [
                            "Sangat bisa dipahami jika pikiran dan dada Anda terasa hampa serta berat saat ini. Perasaan sedih dan kelelahan mental yang Anda alami adalah reaksi yang sangat manusiawi dan valid, jadi tidak perlu memaksakan diri untuk langsung terlihat kuat.",
                            "Mengalami kesedihan di tengah situasi ini memang sangat menguras energi emosional Anda. Izinkan diri Anda merasakan dan meluapkan rasa lelah ini tanpa harus menghakimi diri sendiri."
                        ],
                        "Marah": [
                            "Rasa amarah dan gejolak emosi di dada Anda saat ini adalah bentuk pertahanan diri yang wajar ketika situasi terasa tidak adil. Anda berhak merasa kesal dan memproses emosi amarah ini secara aman.",
                            "Sangat wajar jika rasa jengkel dan kemarahan ini membuat pikiran Anda tegang. Mengakui bahwa Anda sedang emosi adalah langkah penting agar amarah ini tidak merusak kedamaian batin Anda."
                        ],
                        "Kecewa": [
                            "Kekecewaan terjadi ketika harapan yang kita bangun tidak berjalan sesuai kenyataan. Sangat wajar jika hati Anda terasa perih dan tawar ketika kenyataan tidak seindah yang diharapkan.",
                            "Rasa kecewa ini memang meninggalkan ruang hampa di dada. Berilah waktu bagi batin Anda untuk menerima situasi ini perlahan tanpa harus menyalahkan diri sendiri."
                        ],
                        "Cemas": [
                            "Rasa cemas dan kekhawatiran yang terus berputar di kepala memang sangat menguras ketenangan. Sangat wajar jika jantung atau pikiran Anda terasa tegang menghadapi ketidakpastian ini.",
                            "Kecemasan seringkali membuat kita membayangkan skenario terburuk yang belum tentu terjadi. Sadarilah bahwa perasaan tegang ini valid dan Anda aman untuk bernapas perlahan saat ini."
                        ],
                        "Kesepian": [
                            "Merasa sendiri dan terisolasi di tengah ramainya dunia adalah pengalaman yang sangat menyayat hati. Perasaan hampa dan rindu akan ruang aman ini sangat valid Anda rasakan.",
                            "Kesepian bukan berarti Anda tidak berharga, melainkan batin Anda sedang merindukan koneksi yang jujur dan hangat. Perasaan ini wajar dan Anda tidak sendirian di sini."
                        ],
                        "Frustasi": [
                            "Rasa frustasi dan kebuntuan ketika usaha keras kita seolah tidak membuahkan hasil memang sangat melelahkan. Sangat wajar jika Anda merasa muak dan ingin menyerah sejenak dari tekanan ini.",
                            "Ketika semua jalan terasa tertutup dan tenaga Anda terkuras habis, rasa frustasi adalah bentuk kelelahan mental yang sangat wajar. Anda berhak beristirahat dari tekanan ini."
                        ],
                        "Takut": [
                            "Rasa takut dan ketidakpastian akan masa depan memang bisa membuat langkah kita terasa goyah. Sangat wajar jika Anda merasa terancam atau cemas dengan apa yang akan terjadi.",
                            "Perasaan takut adalah tanda bahwa Anda peduli pada keselamatan dan masa depan Anda. Ingatlah bahwa tidak apa-apa untuk merasa ragu sambil melangkah pelan-pelan."
                        ],
                        "Merasa Tidak Mampu": [
                            "Merasa tidak mampu atau meragukan kapasitas diri saat menghadapi tekanan tinggi adalah hal yang sering dialami banyak orang. Perasaan kecil ini sangat valid dan bukan berarti Anda gagal.",
                            "Ketika tuntutan terasa lebih besar dari energi yang Anda miliki, wajar jika rasa minder itu muncul. Ingatlah bahwa kelelahan saat ini tidak mendefinisikan seluruh potensi Anda."
                        ],
                        "Tidak mampu": [
                            "Merasa tidak mampu atau meragukan kapasitas diri saat menghadapi tekanan tinggi adalah hal yang sering dialami banyak orang. Perasaan kecil ini sangat valid dan bukan berarti Anda gagal.",
                            "Ketika tuntutan terasa lebih besar dari energi yang Anda miliki, wajar jika rasa minder itu muncul. Ingatlah bahwa kelelahan saat ini tidak mendefinisikan seluruh potensi Anda."
                        ],
                        "Merasa Tidak Berharga": [
                            "Merasa tidak berharga atau diabaikan adalah luka batin yang sangat dalam dan menyakitkan. Ingatlah bahwa perasaan ini hadir dari rasa lelah, bukan karena nilai diri Anda yang berkurang.",
                            "Sangat menyedihkan ketika kita merasa tidak dianggap di sekitar kita. Namun ketahuilah bahwa keberadaan dan perasaan Anda di sini sangatlah penting dan berharga."
                        ],
                        "Tidak berharga": [
                            "Merasa tidak berharga atau diabaikan adalah luka batin yang sangat dalam dan menyakitkan. Ingatlah bahwa perasaan ini hadir dari rasa lelah, bukan karena nilai diri Anda yang berkurang.",
                            "Sangat menyedihkan ketika kita merasa tidak dianggap di sekitar kita. Namun ketahuilah bahwa keberadaan dan perasaan Anda di sini sangatlah penting dan berharga."
                        ],
                        "Putus asa": [
                            "Sangat bisa dimengerti jika Anda merasa titik ini begitu gelap dan berat untuk dijalani. Perasaan putus asa ini adalah jeritan batin yang sedang membutuhkan istirahat dan penanganan yang lembut.",
                            "Ketika harapan seolah sirna, rasa putus asa memang bisa menyelimuti seluruh pikiran. Jangan memikul beban ini sendirian, peluk diri Anda dan izinkan kami mendampingi Anda."
                        ],
                        "Merasa putus asa": [
                            "Sangat bisa dimengerti jika Anda merasa titik ini begitu gelap dan berat untuk dijalani. Perasaan putus asa ini adalah jeritan batin yang sedang membutuhkan istirahat dan penanganan yang lembut.",
                            "Ketika harapan seolah sirna, rasa putus asa memang bisa menyelimuti seluruh pikiran. Jangan memikul beban ini sendirian, peluk diri Anda dan izinkan kami mendampingi Anda."
                        ],
                        "Merasa kecil": [
                            "Merasa kecil dan tidak sebanding di antara orang lain memang membuat hati terasa ciut dan lelah. Ingatlah bahwa standar orang lain tidak perlu menjadi pengukur berharganya hidup Anda.",
                            "Perasaan minder atau merasa kecil ini sangat wajar muncul saat kita sedang lelah. Luangkan waktu untuk mengapresiasi setiap langkah kecil yang sudah Anda perjuangkan sejauh ini."
                        ],
                        "Tidak diinginkan": [
                            "Rasa tidak diinginkan atau merasa menjadi beban bagi orang lain adalah perasaan yang sangat menyakitkan. Sadarilah bahwa kehadiran Anda membawa makna dan Anda berhak diterima apa adanya.",
                            "Perasaan terasingkan dan tidak diinginkan ini adalah beban yang berat. Ingatlah bahwa Anda layak mendapatkan ruang aman dan kepedulian tanpa harus berpura-pura."
                        ],
                        "Terluka": [
                            "Rasa perih dari luka emosional yang Anda rasakan saat ini memang membutuhkan waktu dan ruang untuk sembuh. Sangat wajar jika Anda merasa begitu rapuh dan sakit batin.",
                            "Luka batin ini adalah bukti bahwa Anda pernah berjuang dan peduli dengan sungguh-sungguh. Izinkan diri Anda memproses rasa sakit ini dengan penuh kelembutan."
                        ],
                        "Sakit Hati": [
                            "Rasa sakit hati akibat kekecewaan atau ucapan yang menusuk memang meninggalkan bekas yang dalam. Sangat wajar jika dada Anda terasa sesak dan kecewa saat ini.",
                            "Sakit hati adalah tanda bahwa batasan batin Anda telah terluka. Berilah waktu bagi diri Anda untuk memulihkan rasa percaya dan kedamaian diri."
                        ],
                        "Sakit hati": [
                            "Rasa sakit hati akibat kekecewaan atau ucapan yang menusuk memang meninggalkan bekas yang dalam. Sangat wajar jika dada Anda terasa sesak dan kecewa saat ini.",
                            "Sakit hati adalah tanda bahwa batasan batin Anda telah terluka. Berilah waktu bagi diri Anda untuk memulihkan rasa percaya dan kedamaian diri."
                        ]
                    }

                    val_options = EMOTION_VALIDATIONS.get(detected_emotion, [
                        "Sangat bisa dipahami jika perasaan ini membuat pikiran dan dada Anda terasa berat. Izinkan diri Anda memproses emosi ini tanpa harus memaksakan diri untuk langsung merasa baik-baik saja."
                    ])
                    extra_validation = random.choice(val_options)
                    full_intro = f"{transition_prefix}{base_reply} {extra_validation}"

                    # Warm open-ended follow-up questions
                    followups = {
                        'Skripsi': f"Bagaimana progres atau bagian mana dari skripsi yang saat ini paling membuat Anda merasa lelah, {current_user.name}?",
                        'Keluarga': f"Apakah ada kejadian spesifik di rumah yang paling memicu perasaan ini, {current_user.name}?",
                        'Pertemanan': f"Bagaimana tanggapan teman Anda ketika situasi ini terjadi, {current_user.name}?",
                        'Hubungan/Pasangan': f"Apakah Anda sudah sempat mengomunikasikan perasaan Anda ini kepadanya, {current_user.name}?",
                        'Pekerjaan': f"Bagian mana dari pekerjaan atau situasi kantor yang terasa paling membebani Anda saat ini, {current_user.name}?",
                        'Pendidikan': f"Tugas atau tuntutan akademis mana yang terasa paling berat dihadapi sekarang, {current_user.name}?",
                        'Diri Sendiri': f"Maukah Anda menceritakan apa yang paling membuat pikiran Anda terasa berat hari ini, {current_user.name}?",
                        'Umum': f"Bagaimana kondisi Anda sekarang, {current_user.name}? Ceritakan saja lebih banyak, saya di sini siap mendengarkan."
                    }
                    followup_q = followups.get(detected_topic, followups['Umum'])

                    reply = f"{full_intro}\n\n<strong>Saran</strong>\n{advice}\n\n<strong>Solusi</strong>\n{solution}\n\n{followup_q}"
                else:
                    advice = random.choice(ADVICES.get(detected_emotion, ADVICES['Umum']))
                    solution = random.choice(SOLUTIONS.get(detected_topic, SOLUTIONS['Umum']))
                    reply = f"{transition_prefix}Saya merasakan emosi '{detected_emotion}' dari cerita Anda mengenai topik ini.\n\n<strong>Saran</strong>\n{advice}\n\n<strong>Solusi</strong>\n{solution}\n\nBagaimana kondisi Anda saat ini, {current_user.name}? Ceritakan saja lebih lanjut, saya di sini siap mendengarkan."
            else:
                fallback_replies = [
                    f"Terima kasih sudah mau berbagi dengan saya, {current_user.name}. Maukah Anda ceritakan lebih lanjut apa yang sedang Anda alami?",
                    f"Saya mendengarkan Anda, {current_user.name}. Ceritakan lebih banyak tentang apa yang sedang Anda rasakan — saya di sini untuk menemani.",
                    f"Perasaan Anda itu valid. Jangan ragu untuk terus berbagi cerita dengan saya. Apa lagi yang ingin Anda sampaikan?"
                ]
                
                last_bot_reply = ChatHistory.query.filter_by(
                    user_id=current_user.id, session_id=session_id, sender='bot'
                ).order_by(ChatHistory.created_at.desc()).first()
                
                if last_bot_reply and len(fallback_replies) > 1:
                    for r in fallback_replies:
                        if r in last_bot_reply.message:
                            fallback_replies.remove(r)
                            break
                            
                reply = transition_prefix + random.choice(fallback_replies)
                
            # Add a subtle prompt based on topic to keep conversation flowing naturally if it's too short
            if len(reply) < 150:
                topic_prompts = {
                    'Stres': f" Apa hal terkecil yang bisa membantu Anda merasa sedikit lebih rileks saat ini?",
                    'Tidur': f" Apakah pikiran Anda sering dipenuhi kekhawatiran sebelum tidur?",
                    'Hubungan/Pasangan': f" Apakah Anda merasa sudah cukup mengomunikasikan perasaan Anda kepadanya?",
                    'Pekerjaan': f" Bagian mana dari pekerjaan Anda yang terasa paling membebani?",
                    'Pendidikan': f" Bagian mana dari studi Anda yang terasa paling sulit dihadapi sekarang?",
                    'Diri Sendiri': f" Ingatlah bahwa nilai diri Anda tidak ditentukan oleh satu kegagalan atau omongan orang. Anda berharga."
                }
                if detected_topic in topic_prompts:
                    reply += " " + topic_prompts[detected_topic]

    # Save Bot reply to database
    bot_chat = ChatHistory(
        user_id=current_user.id,
        sender='bot',
        message=reply,
        session_id=session_id
    )
    db.session.add(bot_chat)
    db.session.commit()
    
    return jsonify({
        'reply': reply,
        'emotion': detected_emotion,
        'confidence': confidence,
        'is_crisis': is_crisis,
        'hotlines': hotlines
    })

@app.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    try:
        ChatHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/delete/<session_id>', methods=['POST'])
@login_required
def delete_session(session_id):
    try:
        ChatHistory.query.filter_by(user_id=current_user.id, session_id=session_id).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Services List & Consultation Booking
@app.route('/layanan')
@login_required
def layanan():
    services = Service.query.all()
    min_date = datetime.date.today().strftime('%Y-%m-%d')
    return render_template(
        'layanan.html',
        active_page='layanan',
        services=services,
        min_date=min_date
    )

# Booking consultation submission
@app.route('/booking/submit', methods=['POST'])
@login_required
def booking_submit():
    name = request.form.get('name')
    email = request.form.get('email')
    booking_date_str = request.form.get('booking_date')
    booking_time = request.form.get('booking_time', '09:00 WIB')
    complaint = request.form.get('complaint')
    service_id = request.form.get('service_id')
    
    if not name or not email or not booking_date_str or not booking_time or not complaint or not service_id:
        flash("Seluruh kolom formulir wajib diisi.", "danger")
        return redirect(url_for('layanan'))
        
    try:
        booking_date = datetime.datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        new_booking = Booking(
            user_id=current_user.id,
            name=name,
            email=email,
            booking_date=booking_date,
            booking_time=booking_time,
            complaint=complaint,
            service_id=int(service_id),
            status='Pending'
        )
        db.session.add(new_booking)
        db.session.commit()
        
        flash(f"Pengajuan booking konsultasi untuk jam {booking_time} berhasil dikirim! Silakan lihat status persetujuan jadwal Anda di bawah ini.", "success")
        return redirect(url_for('profil'))
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal mengirim pengajuan booking: {ex}", "danger")
        return redirect(url_for('layanan'))

# Crisis Helpline & Emergency First Aid Page
@app.route('/bantuan-krisis')
def bantuan_krisis():
    return render_template('bantuan_krisis.html', active_page='bantuan_krisis')

# About Us Page
@app.route('/tentang-kami')
def tentang_kami():
    return render_template('tentang_kami.html', active_page='tentang_kami')

# Helper to get or create default contact setting
def get_contact_setting():
    setting = ContactSetting.query.first()
    if not setting:
        setting = ContactSetting(
            email_support='support@mindhaven.id',
            whatsapp_number='+62 812-3456-7890',
            office_address='Gedung MindHaven Care Center Lt. 3, Jl. Jend. Sudirman No. 108, Jakarta Selatan',
            google_maps_url='https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3966.27361957262!2d106.8202!3d-6.2146!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69f3e46c764e57%3A0x6b1427f8eb2be289!2sJl.%20Jend.%20Sudirman%2C%20Jakarta%20Selatan!5e0!3m2!1sid!2sid!4v1700000000000!5m2!1sid!2sid',
            operating_hours='Senin – Sabtu: 08.00 – 17.00 WIB'
        )
        db.session.add(setting)
        db.session.commit()
    return setting

# Contact Us Page (GET & POST)
@app.route('/hubungi-kami', methods=['GET', 'POST'])
def hubungi_kami():
    setting = get_contact_setting()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not name or not email or not subject or not message:
            flash("Seluruh kolom formulir kontak wajib diisi.", "danger")
            return redirect(url_for('hubungi_kami'))
            
        try:
            user_id = current_user.id if current_user.is_authenticated else None
            new_msg = ContactMessage(
                user_id=user_id,
                name=name,
                email=email,
                subject=subject,
                message=message,
                status='Unread'
            )
            db.session.add(new_msg)
            db.session.commit()
            flash(f"Terima kasih {name}, pesan Anda mengenai '{subject}' telah berhasil dikirim! Tim MindHaven akan merespons melalui email {email}.", "success")
        except Exception as ex:
            db.session.rollback()
            flash(f"Gagal mengirim pesan: {ex}", "danger")
            
        return redirect(url_for('hubungi_kami'))
        
    return render_template('hubungi_kami.html', active_page='hubungi_kami', contact_setting=setting)


# Educational Articles List Portal
@app.route('/edukasi')
@login_required
def edukasi():
    category_id = request.args.get('category_id', type=int)
    search_query = request.args.get('search', default='')
    
    query = Article.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    if search_query:
        query = query.filter(Article.title.like(f'%{search_query}%'))
        
    articles = query.order_by(Article.created_at.desc()).all()
    categories = Category.query.all()
    
    # Get user's bookmarks list
    bookmarked_ids = []
    if current_user.role != 'admin':
        bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
        bookmarked_ids = [b.article_id for b in bookmarks]
        
    return render_template(
        'edukasi.html',
        active_page='edukasi',
        articles=articles,
        categories=categories,
        selected_category_id=category_id,
        search_query=search_query,
        bookmarked_ids=bookmarked_ids
    )

# Article details
@app.route('/article/<int:article_id>')
@login_required
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    
    # Check if bookmarked
    bookmarked = False
    if current_user.role != 'admin':
        bookmarked = Bookmark.query.filter_by(user_id=current_user.id, article_id=article_id).first() is not None
        
    return render_template('artikel_detail.html', article=article, bookmarked=bookmarked)

# Bookmark API Toggle endpoint
@app.route('/api/bookmark/<int:article_id>', methods=['POST'])
@login_required
def api_bookmark(article_id):
    if current_user.role == 'admin':
        return jsonify({'status': 'error', 'message': 'Admin cannot bookmark'}), 403
        
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'status': 'error', 'message': 'Article not found'}), 404
        
    existing = Bookmark.query.filter_by(user_id=current_user.id, article_id=article_id).first()
    try:
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'status': 'success', 'bookmarked': False})
        else:
            new_bookmark = Bookmark(user_id=current_user.id, article_id=article_id)
            db.session.add(new_bookmark)
            db.session.commit()
            return jsonify({'status': 'success', 'bookmarked': True})
    except Exception as ex:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(ex)}), 500

# Profil screen
@app.route('/profil')
@login_required
def profil():
    test_results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.created_at.desc()).all()
    emotion_results = EmotionResult.query.filter_by(user_id=current_user.id).order_by(EmotionResult.created_at.desc()).all()
    bookmarked_articles = Bookmark.query.filter_by(user_id=current_user.id).all()
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    
    return render_template(
        'profil.html',
        active_page='profil',
        test_results=test_results,
        emotion_results=emotion_results,
        bookmarked_articles=bookmarked_articles,
        user_bookings=user_bookings
    )

# Dedicated My Bookings Page (Status Booking Saya)
@app.route('/booking-saya')
@login_required
def booking_saya():
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    contact_setting = get_contact_setting()
    return render_template(
        'booking_saya.html',
        active_page='booking_saya',
        user_bookings=user_bookings,
        contact_setting=contact_setting
    )

# Profile Details update
@app.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    name = request.form.get('name')
    gender = request.form.get('gender')
    age = request.form.get('age')
    
    if not name or not gender or not age:
        flash("Nama, jenis kelamin, dan umur wajib diisi.", "danger")
        return redirect(url_for('profil'))
        
    try:
        current_user.name = name
        current_user.gender = gender
        current_user.age = int(age)
        db.session.commit()
        flash("Profil Anda berhasil diperbarui!", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal memperbarui profil: {ex}", "danger")
        
    return redirect(url_for('profil'))

# Password Update
@app.route('/profile/password', methods=['POST'])
@login_required
def password_update():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not old_password or not new_password or not confirm_password:
        flash("Semua kolom kata sandi wajib diisi.", "danger")
        return redirect(url_for('profil'))
        
    # Robust password verification supporting bcrypt ($2y$) and Werkzeug hashes
    is_valid = False
    if current_user and current_user.password_hash:
        try:
            if current_user.password_hash.startswith('$2y$') or current_user.password_hash.startswith('$2b$'):
                hash_to_check = current_user.password_hash.replace('$2y$', '$2b$').encode('utf-8')
                is_valid = bcrypt.checkpw(old_password.encode('utf-8'), hash_to_check)
            else:
                is_valid = check_password_hash(current_user.password_hash, old_password)
        except (ValueError, TypeError):
            is_valid = False

    if not is_valid:
        flash("Password lama Anda salah.", "error")
        return redirect(url_for('profil'))
        
    if new_password != confirm_password:
        flash("Konfirmasi password baru tidak cocok.", "danger")
        return redirect(url_for('profil'))
        
    try:
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("Password Anda berhasil diperbarui!", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal memperbarui password: {ex}", "danger")
        
    return redirect(url_for('profil'))

# User Self Delete Account Permanently
@app.route('/profile/delete-account', methods=['POST'])
@login_required
def profile_delete_account():
    password = request.form.get('password')
    
    if not password:
        flash("Password wajib diisi untuk mengonfirmasi penghapusan akun.", "danger")
        return redirect(url_for('profil'))
        
    # Verify user password
    is_valid = False
    if current_user and current_user.password_hash:
        try:
            if current_user.password_hash.startswith('$2y$') or current_user.password_hash.startswith('$2b$'):
                hash_to_check = current_user.password_hash.replace('$2y$', '$2b$').encode('utf-8')
                is_valid = bcrypt.checkpw(password.encode('utf-8'), hash_to_check)
            else:
                is_valid = check_password_hash(current_user.password_hash, password)
        except (ValueError, TypeError):
            is_valid = False

    if not is_valid:
        flash("Password yang Anda masukkan salah. Penghapusan akun dibatalkan.", "danger")
        return redirect(url_for('profil'))
        
    user_name = current_user.name
    try:
        user_to_delete = User.query.get(current_user.id)
        logout_user()
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"Akun Anda ({user_name}) beserta seluruh data riwayat telah berhasil dihapus secara permanen dari sistem.", "success")
        return redirect(url_for('home'))
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal menghapus akun: {ex}", "danger")
        return redirect(url_for('profil'))

# ==================== ADMIN ACTION ROUTES ====================

# Admin user list
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', active_page='admin_users', users=users)

# Admin delete user
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_users_delete(user_id):
    if user_id == current_user.id:
        flash("Anda tidak dapat menghapus akun Anda sendiri yang sedang aktif.", "danger")
        return redirect(url_for('admin_users'))
        
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"Akun pengguna {user.name} berhasil dihapus dari sistem.", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal menghapus pengguna: {ex}", "danger")
        
    return redirect(url_for('admin_users'))

# Admin articles list
@app.route('/admin/articles')
@login_required
@admin_required
def admin_articles():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin_articles.html', active_page='admin_articles', articles=articles, form_mode=False)

# Admin add article
@app.route('/admin/articles/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_articles_add():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        category_id = request.form.get('category_id')
        image_url = request.form.get('image_url')
        content = request.form.get('content')
        
        if not title or not category_id or not content:
            flash("Judul, kategori, dan konten wajib diisi.", "danger")
            return redirect(url_for('admin_articles_add'))
            
        try:
            new_art = Article(
                title=title,
                category_id=int(category_id),
                content=content,
                author_id=current_user.id,
                image_url=image_url if image_url else None
            )
            db.session.add(new_art)
            db.session.commit()
            flash("Artikel baru berhasil diterbitkan!", "success")
            return redirect(url_for('admin_articles'))
        except Exception as ex:
            db.session.rollback()
            flash(f"Gagal menambahkan artikel: {ex}", "danger")
            
    return render_template('admin_articles.html', active_page='admin_articles', categories=categories, form_mode=True, article=None)

# Admin edit article
@app.route('/admin/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_articles_edit(article_id):
    article = Article.query.get_or_404(article_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        category_id = request.form.get('category_id')
        image_url = request.form.get('image_url')
        content = request.form.get('content')
        
        if not title or not category_id or not content:
            flash("Kolom judul, kategori, dan konten wajib diisi.", "danger")
            return redirect(url_for('admin_articles_edit', article_id=article_id))
            
        try:
            article.title = title
            article.category_id = int(category_id)
            article.content = content
            article.image_url = image_url if image_url else None
            db.session.commit()
            flash("Artikel berhasil diperbarui!", "success")
            return redirect(url_for('admin_articles'))
        except Exception as ex:
            db.session.rollback()
            flash(f"Gagal memperbarui artikel: {ex}", "danger")
            
    return render_template('admin_articles.html', active_page='admin_articles', categories=categories, form_mode=True, article=article)

# Admin delete article
@app.route('/admin/articles/delete/<int:article_id>', methods=['POST'])
@login_required
@admin_required
def admin_articles_delete(article_id):
    article = Article.query.get_or_404(article_id)
    try:
        db.session.delete(article)
        db.session.commit()
        flash("Artikel berhasil dihapus.", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal menghapus artikel: {ex}", "danger")
    return redirect(url_for('admin_articles'))

# Admin services list
@app.route('/admin/services')
@login_required
@admin_required
def admin_services():
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template('admin_services.html', active_page='admin_services', services=services, form_mode=False)

# Admin add service
@app.route('/admin/services/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_services_add():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        specialty = request.form.get('specialty')
        contact = request.form.get('contact')
        address = request.form.get('address')
        
        if not name or not category or not specialty or not contact or not address:
            flash("Seluruh kolom wajib diisi.", "danger")
            return redirect(url_for('admin_services_add'))
            
        try:
            new_service = Service(
                name=name,
                category=category,
                specialty=specialty,
                contact=contact,
                address=address
            )
            db.session.add(new_service)
            db.session.commit()
            flash("Layanan profesional baru berhasil ditambahkan!", "success")
            return redirect(url_for('admin_services'))
        except Exception as ex:
            db.session.rollback()
            flash(f"Gagal menambahkan layanan: {ex}", "danger")
            
    return render_template('admin_services.html', active_page='admin_services', form_mode=True, service=None)

# Admin edit service
@app.route('/admin/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_services_edit(service_id):
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        specialty = request.form.get('specialty')
        contact = request.form.get('contact')
        address = request.form.get('address')
        
        if not name or not category or not specialty or not contact or not address:
            flash("Seluruh kolom wajib diisi.", "danger")
            return redirect(url_for('admin_services_edit', service_id=service_id))
            
        try:
            service.name = name
            service.category = category
            service.specialty = specialty
            service.contact = contact
            service.address = address
            db.session.commit()
            flash("Informasi layanan berhasil diperbarui!", "success")
            return redirect(url_for('admin_services'))
        except Exception as ex:
            db.session.rollback()
            flash(f"Gagal memperbarui layanan: {ex}", "danger")
            
    return render_template('admin_services.html', active_page='admin_services', form_mode=True, service=service)

# Admin delete service
@app.route('/admin/services/delete/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def admin_services_delete(service_id):
    service = Service.query.get_or_404(service_id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash("Layanan berhasil dihapus.", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal menghapus layanan: {ex}", "danger")
    return redirect(url_for('admin_services'))

# Admin bookings list
@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin_bookings.html', active_page='admin_bookings', bookings=bookings)

# Admin booking status approve / cancel
@app.route('/admin/booking/status/<int:booking_id>/<status>', methods=['POST'])
@login_required
@admin_required
def admin_booking_status(booking_id, status):
    if status not in ['Approved', 'Cancelled']:
        flash("Aksi status booking tidak valid.", "danger")
        return redirect(url_for('admin_bookings'))
        
    booking = Booking.query.get_or_404(booking_id)
    try:
        booking.status = status
        db.session.commit()
        flash(f"Status booking klien {booking.name} berhasil diperbarui menjadi: {status}.", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal merubah status booking: {ex}", "danger")
        
    return redirect(url_for('admin_bookings'))

def sanitize_maps_url(input_url):
    if not input_url:
        return 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3966.27361957262!2d106.8202!3d-6.2146!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69f3e46c764e57%3A0x6b1427f8eb2be289!2sJl.%20Jend.%20Sudirman%2C%20Jakarta%20Selatan!5e0!3m2!1sid!2sid!4v1700000000000!5m2!1sid!2sid'
    
    url = input_url.strip()
    
    # 1. Extract src if user pasted full <iframe ... src="..."> tag
    iframe_match = re.search(r'src=["\']([^"\']+)["\']', url, re.IGNORECASE)
    if iframe_match:
        url = iframe_match.group(1)
        
    # 2. Clean quotes or spaces
    url = url.strip('"\' ')
    
    # 3. Handle standard Google Maps links (place or search)
    if 'google.com/maps' in url and '/embed' not in url:
        if '/place/' in url:
            parts = url.split('/place/')
            place_name = parts[1].split('/')[0]
            url = f"https://maps.google.com/maps?q={place_name}&output=embed"
        else:
            url = "https://maps.google.com/maps?output=embed&q=" + url
    elif 'maps.google.com' in url and '/embed' not in url and 'output=embed' not in url:
        url = url + ("&" if "?" in url else "?") + "output=embed"
        
    return url

# Admin Contact Settings & Support Messages Management
@app.route('/admin/contact', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_contact():
    setting = get_contact_setting()
    if request.method == 'POST':
        email_support = request.form.get('email_support')
        whatsapp_number = request.form.get('whatsapp_number')
        office_address = request.form.get('office_address')
        google_maps_url = request.form.get('google_maps_url')
        operating_hours = request.form.get('operating_hours')
        
        if not email_support or not whatsapp_number or not office_address or not operating_hours:
            flash("Seluruh informasi kontak wajib diisi.", "danger")
            return redirect(url_for('admin_contact'))
            
        try:
            setting.email_support = email_support
            setting.whatsapp_number = whatsapp_number
            setting.office_address = office_address
            if google_maps_url:
                setting.google_maps_url = sanitize_maps_url(google_maps_url)
            setting.operating_hours = operating_hours
            db.session.commit()
            flash("Informasi Kontak & Lokasi Hubungi Kami berhasil diperbarui!", "success")
        except Exception as ex:
            db.session.rollback()
            flash(f"Gagal memperbarui informasi kontak: {ex}", "danger")
            
        return redirect(url_for('admin_contact'))

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread_count = ContactMessage.query.filter_by(status='Unread').count()
    return render_template(
        'admin_contact.html',
        active_page='admin_contact',
        contact_setting=setting,
        messages=messages,
        unread_count=unread_count
    )

# Admin mark contact message status or reply
@app.route('/admin/contact/message/<int:msg_id>/<status>', methods=['POST'])
@login_required
@admin_required
def admin_contact_status(msg_id, status):
    msg = ContactMessage.query.get_or_404(msg_id)
    admin_reply = request.form.get('admin_reply')
    try:
        msg.status = status
        if admin_reply:
            msg.admin_reply = admin_reply
        db.session.commit()
        flash(f"Pesan dari {msg.name} berhasil diperbarui (Status: {status}).", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal merubah status pesan: {ex}", "danger")
    return redirect(url_for('admin_contact'))

# Admin delete contact message
@app.route('/admin/contact/message/delete/<int:msg_id>', methods=['POST'])
@login_required
@admin_required
def admin_contact_delete(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    try:
        db.session.delete(msg)
        db.session.commit()
        flash("Pesan berhasil dihapus dari sistem.", "success")
    except Exception as ex:
        db.session.rollback()
        flash(f"Gagal menghapus pesan: {ex}", "danger")
    return redirect(url_for('admin_contact'))

# 6. Database Initialization & Seeding on Startup
with app.app_context():
    try:
        # Create tables
        db.create_all()
        # Seed standard content
        seed_database()
    except Exception as e:
        print(f"Error during db initialization/seeding: {e}")

# Load models on startup
load_nlp_model()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=False, host='0.0.0.0', port=port)
