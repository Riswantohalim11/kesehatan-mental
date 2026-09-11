with open('c:/AppServ/www/kesehatan-mental/model/responses.py', 'a', encoding='utf-8') as f:
    f.write('''

ADVICES = {
    "Sedih": [
        "Saran saya, cobalah beri ruang bagi diri Anda untuk menangis jika itu melegakan.",
        "Untuk saat ini, cobalah bersikap lembut pada diri sendiri dan jangan paksakan untuk langsung merasa baik.",
        "Cobalah luangkan waktu sejenak untuk beristirahat tanpa memikirkan apapun."
    ],
    "Marah": [
        "Saran saya, tarik napas yang dalam dan hembuskan perlahan untuk meredakan panas di dada.",
        "Cobalah menjauh sejenak dari sumber masalah sampai emosi Anda sedikit mereda.",
        "Jika memungkinkan, salurkan energi amarah ini ke aktivitas fisik seperti olahraga ringan atau jalan kaki."
    ],
    "Kecewa": [
        "Sebagai saran, cobalah terima perasaan kecewa ini tanpa menyangkalnya terlebih dahulu.",
        "Cobalah untuk tidak mengambil keputusan besar saat perasaan kecewa ini masih sangat kuat.",
        "Mungkin ini saatnya untuk menurunkan standar ekspektasi dan lebih berfokus pada apa yang bisa Anda kendalikan."
    ],
    "Cemas": [
        "Saran saya, cobalah alihkan fokus Anda pada hal-hal di sekitar yang bisa Anda sentuh atau lihat saat ini.",
        "Tarik napas 4 detik, tahan 4 detik, dan hembuskan 4 detik. Ini bisa membantu menenangkan saraf yang tegang.",
        "Cobalah untuk fokus hanya pada apa yang ada di depan mata hari ini, bukan yang akan terjadi esok."
    ],
    "Kesepian": [
        "Saran saya, cobalah keluar sebentar sekadar merasakan udara segar atau melihat keramaian.",
        "Mungkin Anda bisa mencoba menyapa satu orang yang sudah lama tidak Anda hubungi.",
        "Cobalah lakukan satu aktivitas yang Anda senangi untuk mengisi ruang kosong tersebut."
    ],
    "Terluka": [
        "Saran saya, beri diri Anda izin untuk merasakan perih ini. Jangan buru-buru menuntut diri untuk kuat.",
        "Cobalah lindungi diri Anda sementara dari hal-hal yang memicu ingatan akan rasa sakit tersebut."
    ],
    "Dendam": [
        "Saran saya, tuliskan semua kemarahan itu di secarik kertas, lalu buanglah sebagai bentuk pelepasan.",
        "Meskipun sulit, cobalah alihkan pikiran dari membalas dendam ke fokus membahagiakan diri sendiri."
    ],
    "Sakit Hati": [
        "Saran saya, batasi interaksi dengan sumber masalah untuk sementara waktu demi melindungi batin Anda.",
        "Cobalah berdamai dengan kenyataan perlahan-lahan tanpa memaksakan diri."
    ],
    "Tersinggung": [
        "Saran saya, jangan langsung membalas. Diam sejenak biasanya mencegah kita mengatakan hal yang akan kita sesali.",
        "Cobalah refleksikan apakah ucapan mereka benar, jika tidak, abaikan saja karena itu tidak mendefinisikan Anda."
    ],
    "Benci": [
        "Saran saya, akui saja rasa benci itu, tapi jangan biarkan rasa itu mengendalikan seluruh hari Anda.",
        "Cobalah lepaskan beban kebencian perlahan, bukan demi orang tersebut, tapi demi kedamaian Anda sendiri."
    ],
    "Menyesal": [
        "Saran saya, berhentilah menghukum diri sendiri atas hal yang sudah terjadi di masa lalu.",
        "Cobalah lihat pelajaran apa yang bisa dipetik dari penyesalan ini untuk masa depan."
    ],
    "Frustasi": [
        "Saran saya, hentikan sejenak apa yang sedang Anda kerjakan. Terus memaksakan diri saat buntu hanya menambah stres.",
        "Cobalah ganti suasana ruangan atau cari udara segar di luar sebentar."
    ],
    "Takut": [
        "Saran saya, sadari bahwa Anda berada di tempat yang aman saat ini. Tarik napas yang panjang.",
        "Cobalah identifikasi rasa takut itu: apakah ancamannya nyata saat ini atau sekadar proyeksi masa depan?"
    ],
    "Malu": [
        "Saran saya, ingatlah bahwa rasa malu ini hanya sementara dan orang lain mungkin tidak terlalu memperhatikannya.",
        "Cobalah tertawakan kesalahan kecil tersebut dan jadikan sebagai pengalaman manusiawi yang wajar."
    ],
    "Merasa Tidak Mampu": [
        "Saran saya, ingat-ingat kembali satu keberhasilan kecil yang pernah Anda capai sebelumnya.",
        "Cobalah berhenti membandingkan langkah awal Anda dengan bab pertengahan orang lain."
    ],
    "Merasa Tidak Berharga": [
        "Saran saya, temukan satu hal kecil yang Anda sukai dari diri Anda hari ini.",
        "Cobalah ingat orang-orang yang peduli pada Anda, keberadaan Anda penting bagi mereka."
    ],
    "Risiko Tinggi": [
        "Saran saya, jangan ragu untuk berbagi beban ini kepada seseorang. Anda tidak sendirian."
    ],
    "Umum": [
        "Saran saya, cobalah tenangkan pikiran sejenak dengan meminum air putih atau sekadar rebahan santai.",
        "Cobalah dengarkan lagu favorit yang bisa membuat perasaan menjadi lebih nyaman."
    ]
}

SOLUTIONS = {
    "Skripsi": [
        "Sebagai solusi jangka panjang, cobalah pecah target pengerjaan skripsi menjadi bagian kecil (misal: 1 paragraf per hari) agar tidak terasa berat.",
        "Jika buntu, solusinya cobalah berdiskusi dengan kakak tingkat atau teman yang sudah lebih dulu melewati fase ini.",
        "Menetapkan jadwal khusus untuk menyentuh skripsi, misalnya hanya 1 jam setiap pagi, bisa menjadi jalan keluar yang efektif."
    ],
    "Keluarga": [
        "Sebagai solusinya, cobalah mulai mengomunikasikan batasan personal Anda secara perlahan tapi tegas kepada keluarga.",
        "Jika memungkinkan, mencari ruang pribadi atau waktu sendiri (me-time) di luar rumah bisa menjadi cara menjaga kewarasan.",
        "Solusi terbaik kadang adalah berdamai bahwa kita tidak bisa mengubah keluarga kita, tapi kita bisa mengubah respons kita terhadap mereka."
    ],
    "Pertemanan": [
        "Sebagai jalan keluar, Anda mungkin perlu mulai mencari komunitas baru yang sefrekuensi dan lebih menghargai Anda.",
        "Solusinya, utarakan secara langsung apa yang mengganggu Anda kepada teman tersebut. Jika dia teman sejati, dia akan mengerti.",
        "Membatasi interaksi dengan teman yang toksik dan lebih fokus pada pengembangan diri bisa menjadi solusi jangka panjang."
    ],
    "Hubungan/Pasangan": [
        "Sebagai solusinya, cari waktu yang tenang dan bicarakan ekspektasi serta perasaan Anda kepadanya secara terbuka (dari hati ke hati).",
        "Menetapkan batasan yang jelas dalam hubungan bisa menjadi langkah penyelesaian yang baik.",
        "Jika hubungan terus menyakiti, solusi terbaik mungkin adalah mengevaluasi kembali apakah hubungan ini layak dipertahankan demi kesehatan mental Anda."
    ],
    "Pekerjaan": [
        "Sebagai solusi, cobalah bicarakan beban kerja ini dengan atasan atau HRD jika memang sudah di luar batas wajar.",
        "Membuat batasan tegas antara waktu kerja dan waktu istirahat (tidak membuka chat pekerjaan di malam hari) adalah jalan keluar yang baik.",
        "Jika stres terus berlanjut, mempertimbangkan untuk mencari peluang karir di tempat lain bisa menjadi solusi akhir."
    ],
    "Pendidikan": [
        "Solusinya, cobalah ubah cara belajar Anda atau cari teman diskusi agar materi lebih mudah dipahami.",
        "Mengurangi target yang terlalu perfeksionis dan lebih fokus pada proses belajar bisa menjadi solusi yang meringankan beban.",
        "Jika Anda merasa salah jurusan, berdiskusi dengan konselor kampus atau perlahan mencari passion di luar kelas bisa menjadi langkah awal."
    ],
    "Diri Sendiri": [
        "Sebagai solusinya, mulailah rutinitas kecil setiap hari (seperti berjemur atau jalan pagi) untuk membangun kembali kontrol diri.",
        "Menulis jurnal tentang hal-hal yang patut disyukuri setiap hari bisa menjadi terapi mandiri yang menyembuhkan.",
        "Jika rasa sakit ini tidak kunjung hilang, solusi terbaik yang saya rekomendasikan adalah mencari bantuan profesional seperti psikolog."
    ],
    "Umum": [
        "Sebagai solusi, cobalah rutin mempraktikkan teknik pernapasan atau relaksasi setiap kali emosi negatif muncul.",
        "Menulis semua perasaan (journaling) seringkali bisa mengurai benang kusut di kepala dan menjadi solusi mandiri.",
        "Jangan ragu mencoba menu 'Relaksasi' yang ada di aplikasi ini sebagai langkah awal pemulihan."
    ]
}
''')
