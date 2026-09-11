with open('c:/AppServ/www/kesehatan-mental/static/css/style.css', 'a', encoding='utf-8') as f:
    f.write('''
/* =============================================
   PAGE: EDUKASI & LAYANAN SPECIFIC CSS
   ============================================= */

/* Image Zoom on Article Card */
.article-card {
  overflow: hidden;
  transition: var(--t-smooth);
}
.article-card .img-wrapper {
  overflow: hidden;
  border-top-left-radius: var(--r-lg);
  border-top-right-radius: var(--r-lg);
}
.article-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  transition: transform 0.5s ease;
}
.article-card:hover img {
  transform: scale(1.08);
}
.article-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-300);
}

/* Hero Section Edukasi */
.hero-edukasi {
  background: var(--grad-primary);
  border-radius: var(--r-xl);
  padding: 3rem 2.5rem;
  color: white;
  position: relative;
  overflow: hidden;
  margin-bottom: 2.5rem;
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hero-edukasi::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.hero-edukasi-text {
  position: relative;
  z-index: 2;
  max-width: 600px;
}
.hero-edukasi-icon {
  font-size: 6rem;
  opacity: 0.8;
  position: relative;
  z-index: 2;
  text-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

/* Search Bar Premium */
.search-premium {
  background: white;
  border-radius: var(--r-full);
  padding: 0.4rem;
  display: flex;
  align-items: center;
  box-shadow: var(--shadow-md);
  transition: var(--t-smooth);
  border: 1px solid rgba(255,255,255,0.4);
}
.search-premium:focus-within {
  box-shadow: 0 0 0 4px rgba(0, 181, 181, 0.2);
  transform: translateY(-2px);
}
.search-premium input {
  border: none;
  background: transparent;
  padding: 0.5rem 1rem;
  width: 100%;
}
.search-premium input:focus {
  outline: none;
  box-shadow: none;
}

/* Service Pill Navs */
.service-nav-pills .nav-link {
  border-radius: var(--r-full);
  color: var(--gray-600);
  font-weight: 600;
  padding: 0.6rem 1.5rem;
  border: 1.5px solid var(--gray-200);
  transition: var(--t-smooth);
  background: white;
  margin-bottom: 0.5rem;
}
.service-nav-pills .nav-link:hover {
  background: var(--gray-50);
  transform: translateY(-2px);
  border-color: var(--primary-300);
}
.service-nav-pills .nav-link.active {
  background: var(--grad-primary);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(0, 181, 181, 0.3);
}
.service-nav-pills .nav-link.text-danger.active {
  background: var(--danger);
  border-color: var(--danger);
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
  color: white !important;
}

/* Pulse Animation for Hotline */
@keyframes pulse-danger {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.3); }
  70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
.hotline-card {
  animation: pulse-danger 2s infinite;
  border: 2px solid var(--danger) !important;
  background: linear-gradient(145deg, #fff5f5, #fef2f2) !important;
  position: relative;
  overflow: hidden;
}
.hotline-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px;
  height: 100%;
  background: var(--danger);
}

/* Directory Service Cards */
.service-card {
  transition: var(--t-smooth);
  border-left: 4px solid var(--primary-400) !important;
}
.service-card:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-sm);
  background: var(--primary-50);
}

/* Form Booking Premium */
.booking-form .form-label {
  font-size: 0.9rem;
  color: var(--gray-700);
}
.booking-form .form-control, .booking-form .form-select {
  border-radius: var(--r-md);
  border: 1.5px solid var(--gray-200);
  padding: 0.75rem 1rem;
  background: #f8fafc;
  transition: var(--t-fast);
}
.booking-form .form-control:focus, .booking-form .form-select:focus {
  background: white;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 4px rgba(0, 181, 181, 0.1);
}

/* Fade in up animation */
.fade-in-up {
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
  transform: translateY(20px);
}
@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
''')
