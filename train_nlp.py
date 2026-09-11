import os
import csv
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from model.nlp import preprocess_text

def ensure_dataset():
    dataset_dir = 'dataset'
    dataset_file = os.path.join(dataset_dir, 'dataset_emosi.csv')
    
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
        
    # Force recreation of dataset to include new emotions
    
    # Define the emotions and their Indonesian text patterns
    data = []
    
    # 1. Marah
    data.extend([
        ("Saya sangat marah sekali dengan keadaan ini", "Marah"),
        ("Aku kesal sekali dengan dia yang berbohong", "Marah"),
        ("Rasanya ingin memukul sesuatu karena emosi", "Marah"),
        ("Saya tidak terima diperlakukan tidak adil seperti ini", "Marah"),
        ("Kenapa semua orang membuatku emosi dan naik pitam?", "Marah"),
        ("Aku murka melihat kelakuannya yang kurang ajar", "Marah"),
        ("Jangan ganggu aku, aku sedang marah", "Marah"),
        ("Brengsek sekali orang itu membuatku kesal", "Marah"),
        ("Sialan, kenapa ini harus terjadi padaku", "Marah"),
        ("Aku naik darah mendengar perkataannya yang sombong", "Marah"),
        ("sangat jengkel aku dengan sikapnya", "Marah"),
        ("bikin emosi saja kelakuanmu itu", "Marah"),
        ("anjing bangsat kau membuatku murka", "Marah"),
        ("aku ngamuk tadi di kantor karena dia", "Marah"),
        ("marah banget saya hari ini", "Marah"),
        ("gw kesel banget sama temen gw", "Marah")
    ])
    
    # 2. Kecewa
    data.extend([
        ("Aku kecewa sekali dengan keputusan ini", "Kecewa"),
        ("Harapanku hancur berkeping-keping", "Kecewa"),
        ("Dia tidak menepati janjinya lagi", "Kecewa"),
        ("Sia-sia perjuanganku selama ini karena hasilnya buruk", "Kecewa"),
        ("Aku tidak menyangka dia akan bersikap dingin seperti itu", "Kecewa"),
        ("Ekspektasiku terlalu tinggi dan akhirnya jatuh", "Kecewa"),
        ("Hasil ujianku tidak sesuai keinginan, kecewa sekali", "Kecewa"),
        ("Rasanya sia-sia mempercayainya selama ini", "Kecewa"),
        ("Sangat mengecewakan sekali pelayanan di sini", "Kecewa"),
        ("Kenapa harus gagal lagi setelah semua usaha ini", "Kecewa"),
        ("ekspektasi tidak sesuai realita, kecewa", "Kecewa"),
        ("dia mengecewakan ku berkali-kali", "Kecewa"),
        ("menyesakkan sekali ketika harapan dipatahkan", "Kecewa"),
        ("hancur harapanku padamu", "Kecewa"),
        ("kecewa berat aku dengannya", "Kecewa"),
        ("gw kecewa banget sama hasil skripsi gw", "Kecewa"),
        ("udah usaha tapi hasilnya tetap jelek", "Kecewa")
    ])
    
    # 3. Terlika (Terluka)
    data.extend([
        ("hatiku terluka parah karena pengkhianatan itu", "Terluka"),
        ("dia ngomong di belakang gw", "Terluka"),
        ("gw masih kepikiran omongannya", "Terluka"),
        ("masih kebayang", "Terluka"),
        ("masih inget kata-katanya", "Terluka"),
        ("susah lupa", "Terluka")
    ])
    
    # 4. Dendam
    data.extend([
        ("Aku tidak akan memaafkannya sampai kapanpun", "Dendam"),
        ("Suatu hari nanti dia akan menerima balasannya yang setimpal", "Dendam"),
        ("Aku ingin dia merasakan apa yang kurasakan sekarang", "Dendam"),
        ("Kebencian ini membuatku ingin membalas dendam padanya", "Dendam"),
        ("Aku tidak akan melupakan apa yang dia lakukan padaku", "Dendam"),
        ("Tunggu saja pembalasanku nanti", "Dendam"),
        ("Rasa dendam ini membakar diriku setiap hari", "Dendam"),
        ("Aku harus membalas perbuatannya yang jahat", "Dendam"),
        ("Tidak ada kata maaf baginya, dia harus menderita", "Dendam"),
        ("Dia harus bayar semua kesalahannya padaku", "Dendam"),
        ("aku akan balas dendam padanya", "Dendam"),
        ("rasanya ingin membalas semua perbuatannya", "Dendam"),
        ("dendam ini tidak akan padam sebelum dia jatuh", "Dendam"),
        ("aku menyimpan dendam yang sangat besar", "Dendam"),
        ("ingin kubalas kejahatan orang itu", "Dendam"),
        ("susah maafin", "Dendam"),
        ("gw susah maafin dia", "Dendam"),
        ("pengen dia ngerasain hal yang sama", "Dendam"),
        ("gw pengen dia ngerasain hal yang sama", "Dendam"),
        ("pengen balas", "Dendam"),
        ("pengen dia tau rasanya", "Dendam")
    ])
    # 5. Sakit Hati
    data.extend([
        ("sakit hati banget dihina seperti itu", "Sakit Hati"),
        ("kepikiran omongannya", "Sakit Hati"),
        ("gw sakit hati banget", "Sakit Hati"),
        ("gw masih kepikiran omongannya", "Sakit Hati"),
        ("masih kebayang", "Sakit Hati"),
        ("masih inget kata-katanya", "Sakit Hati"),
        ("susah lupa", "Sakit Hati")
    ])
    
    # 6. Tersinggung
    data.extend([
        ("Saya tersinggung dengan candaannya yang kelewatan", "Tersinggung"),
        ("Ucapannya tidak sopan dan menyinggungku secara pribadi", "Tersinggung"),
        ("Kenapa dia merendahkanku seperti itu, saya tersinggung", "Tersinggung"),
        ("Kata-katanya sangat menyinggung perasaan saya", "Tersinggung"),
        ("Aku merasa diremehkan oleh omongannya yang kasar", "Tersinggung"),
        ("Sindiran tajam itu membuatku tersinggung berat", "Tersinggung"),
        ("Dia tidak menghargaiku dengan bicara sekasar itu", "Tersinggung"),
        ("Sangat tidak pantas dia berbicara seperti itu padaku", "Tersinggung"),
        ("Hatiku terusik karena ucapan kasarnya yang menyinggung", "Tersinggung"),
        ("Perkataannya membuatku tidak nyaman dan tersinggung", "Tersinggung"),
        ("tersinggung sekali saya dengan perbuatannya", "Tersinggung"),
        ("pernyataan dia sangat menyinggung harga diri saya", "Tersinggung"),
        ("jangan menyinggung perasaan orang lain", "Tersinggung"),
        ("saya merasa tersinggung dengan sindirannya", "Tersinggung"),
        ("kata-katanya membuat saya tersinggung", "Tersinggung")
    ])
    
    # 7. Benci
    data.extend([
        ("Aku benci sekali dengannya, tidak mau kenal lagi", "Benci"),
        ("Aku tidak suka melihat mukanya yang munafik", "Benci"),
        ("Rasanya muak dan benci melihat tingkah lakunya", "Benci"),
        ("Aku sangat membenci sifatnya yang egois dan sombong", "Benci"),
        ("Kebencianku padanya sudah memuncak dan tak tertahankan", "Benci"),
        ("Aku tidak mau bertemu dia lagi seumur hidupku", "Benci"),
        ("Aku benci situasi ini yang terus menerus menyiksaku", "Benci"),
        ("Sangat membenci orang-orang palsu di sekitarku", "Benci"),
        ("Aku tidak sudi berteman dengan orang seperti dia", "Benci"),
        ("Benci sekali rasanya jika mengingat masa-masa bersamanya", "Benci"),
        ("aku benci dia selamanya", "Benci"),
        ("benci sekali aku pada pengkhianat", "Benci"),
        ("sungguh ku benci keadaan yang serba sulit ini", "Benci"),
        ("kebencian ini membuatku muak", "Benci"),
        ("saya membenci sikapnya yang sombong itu", "Benci")
    ])
    
    # 8. Menyesal
    data.extend([
        ("Aku menyesal telah melakukan hal buruk itu", "Menyesal"),
        ("Seandainya aku tidak mengambil keputusan bodoh itu", "Menyesal"),
        ("Semua kekacauan ini adalah kesalahanku yang kusesali", "Menyesal"),
        ("Aku merasa bersalah dan sangat menyesal", "Menyesal"),
        ("Kenapa aku sebodoh itu dulu, menyesal sekali", "Menyesal"),
        ("Penyesalan ini selalu menghantuiku setiap malam", "Menyesal"),
        ("Rasanya ingin memutar balik waktu ke masa lalu", "Menyesal"),
        ("Aku meminta maaf atas kebodohanku yang sangat kusesali", "Menyesal"),
        ("Andai saja aku bisa merubah keputusan masa lalu", "Menyesal"),
        ("Aku sangat menyesali perkataan kasarku kepadanya", "Menyesal"),
        ("menyesal saya telah mempercayai dia", "Menyesal"),
        ("aku menyesali semua perbuatan burukku", "Menyesal"),
        ("penyesalan datang terlambat, aku sedih", "Menyesal"),
        ("menyesal rasanya tidak belajar dengan giat", "Menyesal"),
        ("saya sangat menyesali keputusan resign ini", "Menyesal")
    ])
    
    # 9. Frustasi
    data.extend([
        ("Aku frustasi dengan tugas-tugas kuliah yang menumpuk", "Frustasi"),
        ("Semua usahaku selalu gagal dan sia-sia", "Frustasi"),
        ("Rasanya ingin menyerah saja dari keadaan ini", "Frustasi"),
        ("Stres sekali menghadapi masalah yang tak kunjung selesai", "Frustasi"),
        ("Aku bingung harus berbuat apa lagi menghadapi ini", "Frustasi"),
        ("Semuanya terasa buntu dan tidak ada jalan keluar", "Frustasi"),
        ("Kepalaku mau pecah memikirkan jalan keluar yang tidak ada", "Frustasi"),
        ("Frustasi rasanya tidak ada kemajuan dalam hidupku", "Frustasi"),
        ("Semua rencana masa depanku berantakan", "Frustasi"),
        ("Kenapa tidak ada satupun yang berjalan lancar dalam hidupku", "Frustasi"),
        ("frustasi saya dengan pekerjaan yang monoton ini", "Frustasi"),
        ("buntu semua jalan, frustasi sekali", "Frustasi"),
        ("ingin gila rasanya memikirkan masalah ini, frustasi", "Frustasi"),
        ("usaha keras tapi gagal lagi, bikin frustasi", "Frustasi"),
        ("saya sangat frustasi dengan keadaan ekonomi sekarang", "Frustasi"),
        ("udah usaha tapi hasilnya tetap jelek", "Frustasi")
    ])
    
    # 10. Takut
    data.extend([
        ("Aku takut menghadapi ujian besok", "Takut"),
        ("Rasanya sangat cemas dan ketakutan sendirian", "Takut"),
        ("Aku gemetar membayangkan hal buruk akan terjadi", "Takut"),
        ("Aku takut sendirian di dalam kegelapan malam", "Takut"),
        ("Rasanya ada yang mengawasiku dan aku merasa takut", "Takut"),
        ("Ngeri sekali melihat kecelakaan itu, aku takut", "Takut"),
        ("Aku takut gagal lagi dan mengecewakan orang tua", "Takut"),
        ("Jantungku berdebar kencang karena ketakutan yang mendalam", "Takut"),
        ("Aku merasa tidak aman dan takut di lingkungan ini", "Takut"),
        ("Ada rasa ngeri yang membayangi pikiranku saat ini", "Takut"),
        ("takut sekali saya akan hari esok", "Takut"),
        ("saya ketakutan mendengar ancaman itu", "Takut"),
        ("gemetar tubuhku karena takut", "Takut"),
        ("takut kehilangan orang tua saya", "Takut"),
        ("ngeri dan takut membayangkan kegagalan", "Takut")
    ])
    
    # 11. Cemas
    data.extend([
        ("Aku cemas menunggu hasil diagnosis dokter", "Cemas"),
        ("Jantungku berdebar-debar tanpa sebab yang jelas, cemas sekali", "Cemas"),
        ("Pikiranku terus dipenuhi rasa khawatir dan cemas", "Cemas"),
        ("Bagaimana kalau semuanya gagal, aku sangat cemas", "Cemas"),
        ("Aku merasa sangat gelisah dan cemas hari ini", "Cemas"),
        ("Rasa cemas ini membuatku sulit memejamkan mata", "Cemas"),
        ("Aku khawatir tentang apa yang akan terjadi esok hari", "Cemas"),
        ("Perasaanku tidak tenang dan selalu was-was serta cemas", "Cemas"),
        ("Cemas sekali rasanya memikirkan tanggapan orang lain", "Cemas"),
        ("Aku tidak bisa rileks karena rasa cemas melanda", "Cemas"),
        ("cemas sekali pikiran ini tidak bisa tenang", "Cemas"),
        ("gelisah dan cemas memikirkan masa depan", "Cemas"),
        ("kuatir sekali rasanya, cemas luar biasa", "Cemas"),
        ("cemas memikirkan presentasi besok pagi", "Cemas"),
        ("perasaan was-was dan cemas melanda dada", "Cemas")
    ])
    
    # 12. Malu
    data.extend([
        ("Aku malu sekali karena melakukan kesalahan bodoh tadi", "Malu"),
        ("Rasanya ingin menyembunyikan wajahku karena sangat malu", "Malu"),
        ("Aku merasa sangat canggung dan malu di depan umum", "Malu"),
        ("Semua orang menertawakanku, aku merasa malu", "Malu"),
        ("Aku merasa tidak pantas dan minder, malu sekali", "Malu"),
        ("Malu sekali rasanya menjadi pusat perhatian orang-orang", "Malu"),
        ("Mukaku memerah karena menahan rasa malu yang amat sangat", "Malu"),
        ("Aku menyesal bertingkah konyol dan membuat malu diriku", "Malu"),
        ("Rasanya ingin menghilang karena sangat malu atas kejadian itu", "Malu"),
        ("Aku merasa rendah diri dan malu dengan keadaan finansialku", "Malu"),
        ("malu saya tidak bisa lulus tepat waktu", "Malu"),
        ("sangat malu rasanya berbuat kesalahan fatal itu", "Malu"),
        ("minder dan malu berkumpul dengan mereka yang sukses", "Malu"),
        ("rasanya malu ditolak di depan banyak orang", "Malu"),
        ("saya malu dengan kekurangan fisik saya", "Malu")
    ])
    
    # 13. Kesepian
    data.extend([
        ("Aku merasa sangat kesepian akhir-akhir ini", "Kesepian"),
        ("Tidak ada orang yang peduli denganku di dunia ini", "Kesepian"),
        ("Di ruangan yang ramai pun aku tetap merasa sendiri", "Kesepian"),
        ("Aku tidak punya teman dekat untuk berbagi cerita", "Kesepian"),
        ("Hari-hariku terasa sepi, hampa, dan sunyi", "Kesepian"),
        ("Rasanya terisolasi dari dunia luar dan kesepian", "Kesepian"),
        ("Aku butuh seseorang untuk menemaniku saat ini", "Kesepian"),
        ("Kesepian ini perlahan-lahan menyiksa batinku", "Kesepian"),
        ("Tidak ada yang mau mendengarkan keluh kesahku", "Kesepian"),
        ("Aku selalu sendirian menghadapi malam yang dingin", "Kesepian"),
        ("kesepian sekali hidupku tanpa teman", "Kesepian"),
        ("merasa terasing dan kesepian di kota ini", "Kesepian"),
        ("sepi sekali di rumah tidak ada siapa-siapa", "Kesepian"),
        ("sendirian terus, rasanya sangat kesepian", "Kesepian"),
        ("butuh teman ngobrol, sepi banget", "Kesepian")
    ])
    
    # 14. Sedih
    data.extend([
        ("Air mataku menetes memikirkan nasibku yang malang", "Sedih"),
        ("Kesedihan ini sangat mendalam dan menusuk hati", "Sedih"),
        ("Aku ingin menangis sepuasnya mengeluarkan sedih ini", "Sedih"),
        ("Hatiku terasa kelabu, muram, dan sedih sekali", "Sedih"),
        ("Kabar duka ini membuatku sangat sedih dan berduka", "Sedih"),
        ("Aku tidak bisa memaksakan diri untuk tersenyum hari ini", "Sedih"),
        ("Rasanya hampa dan sedih sekali kehilangan dirinya", "Sedih"),
        ("Kenapa kesedihan ini tak kunjung pergi dari hidupku", "Sedih"),
        ("Aku berduka dan sedih atas kehilangan orang tercinta", "Sedih"),
        ("Perasaanku sangat murung dan dipenuhi kesedihan", "Sedih"),
        ("menangis saya karena sedih sekali", "Sedih"),
        ("sedih banget hari ini rasanya ingin merenung saja", "Sedih"),
        ("hati ini pilu dan sedih mendengar kabar itu", "Sedih"),
        ("suasana hatiku sedang sedih dan muram", "Sedih"),
        ("sangat sedih ditinggal oleh sahabat terbaik", "Sedih")
    ])
    # 15. Merasa Tidak Mampu
    data.extend([
        ("aku tidak kompeten, selalu salah kerja", "Merasa Tidak Mampu"),
        ("merasa tidak sanggup memimpin tim ini", "Merasa Tidak Mampu"),
        ("gw ngerasa kemampuan gw kurang", "Merasa Tidak Mampu")
    ])
    
    # 16. Merasa putus asa
    data.extend([
        ("Aku merasa putus asa dengan hidup ini yang hancur", "Merasa putus asa"),
        ("Tidak ada harapan lagi bagiku untuk sukses", "Merasa putus asa"),
        ("Semua jalan keluar seolah sudah tertutup rapat", "Merasa putus asa"),
        ("Rasanya percuma saja terus mencoba kalau selalu gagal", "Merasa putus asa"),
        ("Aku sudah berada di titik terendah dan putus asa", "Merasa putus asa"),
        ("Tidak ada lagi masa depan yang cerah untukku", "Merasa putus asa"),
        ("Semua usahaku sia-sia belaka tanpa hasil", "Merasa putus asa"),
        ("Aku kehilangan semua harapan untuk bisa sembuh", "Merasa putus asa"),
        ("Rasanya tidak ada lagi pertolongan yang bisa kudapat", "Merasa putus asa"),
        ("Semuanya sudah berakhir bagi saya, saya putus asa", "Merasa putus asa"),
        ("putus asa saya menghadapi penyakit ini", "Merasa putus asa"),
        ("tidak ada lagi sinar harapan, putus asa", "Merasa putus asa"),
        ("rasanya ingin menyerah kalah, putus asa sekali", "Merasa putus asa"),
        ("hancur sudah harapan, putus asa total", "Merasa putus asa"),
        ("kehilangan semangat dan putus asa menghadapi kenyataan", "Merasa putus asa")
    ])
    # 17. Merasa tidak berharga
    data.extend([
        ("rasanya saya tidak berharga sama sekali", "Merasa Tidak Berharga"),
        ("tidak ada nilai diri saya di mata mereka", "Merasa Tidak Berharga"),
        ("merasa tidak penting dan tidak berharga bagi pacar", "Merasa Tidak Berharga"),
        ("kayaknya keberadaan gw nggak penting", "Merasa Tidak Berharga")
    ])
    
    # 18. Merasa kecil
    data.extend([
        ("saya merasa kecil tidak punya prestasi apa-apa", "Merasa Kecil"),
        ("rendah diri ini membuat saya merasa kecil", "Merasa Kecil"),
        ("merasa tidak ada apa-apanya dibanding mereka", "Merasa Kecil"),
        ("gw selalu kalah dibanding orang lain", "Merasa Kecil")
    ])
    
    # 19. Merasa tidak di inginkan
    data.extend([
        ("kehadiranku dianggap mengganggu, tidak di inginkan", "Merasa Tidak Diinginkan"),
        ("dijauhi teman-teman seolah aku tidak diinginkan", "Merasa Tidak Diinginkan"),
        ("mereka menolak kehadiranku secara terang-terangan", "Merasa Tidak Diinginkan"),
        ("gw ngerasa nggak dibutuhin siapa-siapa", "Merasa Tidak Diinginkan")
    ])
    
    # 20. Risiko Tinggi (Crisis)
    data.extend([
        ("gw pengen hilang", "Risiko Tinggi"),
        ("hidup gw nggak ada gunanya", "Risiko Tinggi"),
        ("semua orang lebih baik tanpa gw", "Risiko Tinggi"),
        ("kayaknya semua orang lebih baik tanpa gw", "Risiko Tinggi"),
        ("gw pengen mati", "Risiko Tinggi"),
        ("aku mau bunuh diri saja", "Risiko Tinggi"),
        ("tidak ingin hidup lagi rasanya", "Risiko Tinggi"),
        ("aku mau menyakiti diri sendiri", "Risiko Tinggi"),
        ("sudah capek hidup, ingin mati", "Risiko Tinggi"),
        ("tidak ada gunanya aku hidup di dunia ini", "Risiko Tinggi")
    ])

    # 21. Senang
    data.extend([
        ("Aku merasa sangat senang dan bahagia hari ini", "Senang"),
        ("Alhamdulillah akhirnya aku berhasil lulus ujian", "Senang"),
        ("Hari ini sangat menyenangkan, aku tersenyum sepanjang hari", "Senang"),
        ("Aku merasa bersyukur dengan kehidupanku saat ini", "Senang"),
        ("Senang sekali bertemu dengan teman lama yang kusayangi", "Senang"),
        ("Aku merasa puas dan bangga dengan pencapaianku ini", "Senang"),
        ("Hatiku dipenuhi kegembiraan yang luar biasa", "Senang"),
        ("Aku sangat berterima kasih atas kebaikan semua orang", "Senang"),
        ("Perasaanku sangat cerah dan penuh semangat hari ini", "Senang"),
        ("Aku merasa dicintai dan disayangi oleh keluargaku", "Senang"),
        ("gembira sekali rasanya mendapat kabar baik itu", "Senang"),
        ("bahagia banget aku hari ini bisa liburan", "Senang"),
        ("senang hati ini mendapat hadiah dari sahabat", "Senang"),
        ("sukacita memenuhi hatiku setelah lulus sidang", "Senang"),
        ("aku merasa sangat beruntung dan bersyukur hari ini", "Senang")
    ])

    # 21. Netral (Sapaan, pertanyaan umum, kalimat netral tanpa emosi)
    data.extend([
        ("Hai", "Netral"),
        ("Halo", "Netral"),
        ("Halo apa kabar", "Netral"),
        ("Selamat pagi", "Netral"),
        ("Selamat siang", "Netral"),
        ("Selamat sore", "Netral"),
        ("Selamat malam", "Netral"),
        ("Assalamualaikum", "Netral"),
        ("Hey kamu siapa", "Netral"),
        ("Apa kabar hari ini", "Netral"),
        ("Perkenalkan nama saya Budi", "Netral"),
        ("Saya ingin bertanya sesuatu", "Netral"),
        ("Boleh minta tolong bantu saya", "Netral"),
        ("Apa itu kesehatan mental", "Netral"),
        ("Bisa jelaskan tentang stres", "Netral"),
        ("Bagaimana cara menggunakan chatbot ini", "Netral"),
        ("Terima kasih sudah membantu", "Netral"),
        ("Oke baik saya mengerti sekarang", "Netral"),
        ("Saya mau cerita sedikit tentang hari ini", "Netral"),
        ("Hari ini biasa saja tidak ada yang terjadi", "Netral")
    ])

    with open(dataset_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(data)
        
    print(f"Dataset generated at {dataset_file} with {len(data)} rows.")
    return dataset_file

def train_model():
    dataset_file = ensure_dataset()
    
    # Load dataset
    df = pd.read_csv(dataset_file)
    
    # Preprocess text
    print("Preprocessing text...")
    df['clean_text'] = df['text'].apply(preprocess_text)
    
    # Feature extraction using TF-IDF Vectorizer
    print("Extracting features (TF-IDF)...")
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['clean_text'])
    y = df['label']
    
    # Train Naive Bayes Classifier
    print("Training Naive Bayes Classifier...")
    classifier = MultinomialNB()
    classifier.fit(X, y)
    
    # Save the models
    model_dir = 'model_nlp'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    vectorizer_file = os.path.join(model_dir, 'vectorizer.pkl')
    classifier_file = os.path.join(model_dir, 'classifier.pkl')
    
    with open(vectorizer_file, 'wb') as f:
        pickle.dump(vectorizer, f)
        
    with open(classifier_file, 'wb') as f:
        pickle.dump(classifier, f)
        
    print(f"Vectorizer saved to {vectorizer_file}")
    print(f"Classifier saved to {classifier_file}")
    print("NLP Model Training Completed Successfully!")

if __name__ == "__main__":
    train_model()
