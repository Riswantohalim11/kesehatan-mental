// Chart.js initialization for User and Admin Dashboards

document.addEventListener('DOMContentLoaded', function() {
    
    // Theme Colors mapped from CSS variables
    const colors = {
        teal: '#20969b',
        indigo: '#5e6ad2',
        sage: '#66bb6a',
        coral: '#ffa726',
        rose: '#ef5350',
        grey: '#78909c',
        tealLight: 'rgba(32, 150, 155, 0.2)',
        indigoLight: 'rgba(94, 106, 210, 0.2)',
        sageLight: 'rgba(102, 187, 106, 0.2)'
    };

    // Grab elements containing chart data from DOM
    const chartDataEl = document.getElementById('chart-data');
    if (chartDataEl) {
        // --- 1. USER EMOTION CHART (Doughnut / Distribution) ---
        const userEmotionCanvas = document.getElementById('userEmotionChart');
        if (userEmotionCanvas) {
            const rawEmotions = JSON.parse(chartDataEl.dataset.emotions || '[]');
            
            // Format data
            const labels = rawEmotions.map(item => item.emotion_label);
            const counts = rawEmotions.map(item => item.count);
            
            // Generate palette
            const palette = [
                colors.teal, colors.indigo, colors.sage, colors.coral, colors.rose, colors.grey,
                '#8d6e63', '#ab47bc', '#26a69a', '#78909c', '#d4e157', '#ffd54f', '#ff7043'
            ];
            
            new Chart(userEmotionCanvas, {
                type: 'doughnut',
                data: {
                    labels: labels.length > 0 ? labels : ['Belum Ada Chat'],
                    datasets: [{
                        data: counts.length > 0 ? counts : [1],
                        backgroundColor: counts.length > 0 ? palette.slice(0, labels.length) : ['#e0e0e0'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: { family: 'Poppins', size: 11 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    if (counts.length === 0) return 'Tidak ada data emosi';
                                    const value = context.raw;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = Math.round((value / total) * 100);
                                    return ` ${context.label}: ${value} pesan (${pct}%)`;
                                }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        }

        // --- 2. USER TEST RESULTS CHART (Timeline or Category Scores) ---
        const userTestCanvas = document.getElementById('userTestChart');
        if (userTestCanvas) {
            const rawTests = JSON.parse(chartDataEl.dataset.tests || '[]');
            
            // We want to group by date and show scores for Stres, Kecemasan, Depresi
            const dates = [...new Set(rawTests.map(t => t.date))].sort();
            
            const stresData = dates.map(d => {
                const item = rawTests.find(t => t.date === d && t.category === 'Stres');
                return item ? item.score : null;
            });
            
            const kecemasanData = dates.map(d => {
                const item = rawTests.find(t => t.date === d && t.category === 'Kecemasan');
                return item ? item.score : null;
            });
            
            const depresiData = dates.map(d => {
                const item = rawTests.find(t => t.date === d && t.category === 'Depresi');
                return item ? item.score : null;
            });
            
            new Chart(userTestCanvas, {
                type: 'line',
                data: {
                    labels: dates.length > 0 ? dates : ['Belum Ada Tes'],
                    datasets: [
                        {
                            label: 'Stres (Maks 80)',
                            data: stresData.length > 0 ? stresData : [0],
                            borderColor: colors.coral,
                            backgroundColor: 'transparent',
                            tension: 0.3,
                            spanGaps: true,
                            pointRadius: 4,
                            borderWidth: 3
                        },
                        {
                            label: 'Kecemasan (Maks 80)',
                            data: kecemasanData.length > 0 ? kecemasanData : [0],
                            borderColor: colors.indigo,
                            backgroundColor: 'transparent',
                            tension: 0.3,
                            spanGaps: true,
                            pointRadius: 4,
                            borderWidth: 3
                        },
                        {
                            label: 'Depresi (Maks 80)',
                            data: depresiData.length > 0 ? depresiData : [0],
                            borderColor: colors.rose,
                            backgroundColor: 'transparent',
                            tension: 0.3,
                            spanGaps: true,
                            pointRadius: 4,
                            borderWidth: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 80,
                            grid: { color: 'rgba(0,0,0,0.05)' },
                            title: { display: true, text: 'Skor Tes' }
                        },
                        x: {
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { font: { family: 'Poppins', size: 11 } }
                        }
                    }
                }
            });
        }
    }

    // --- 3. ADMIN ANALYTICS ---
    const adminDataEl = document.getElementById('admin-chart-data');
    if (adminDataEl) {
        const adminEmotionCanvas = document.getElementById('adminEmotionChart');
        if (adminEmotionCanvas) {
            const rawEmotions = JSON.parse(adminDataEl.dataset.emotions || '[]');
            
            const labels = rawEmotions.map(item => item.emotion_label);
            const counts = rawEmotions.map(item => item.count);
            
            new Chart(adminEmotionCanvas, {
                type: 'bar',
                data: {
                    labels: labels.length > 0 ? labels : ['Belum ada data'],
                    datasets: [{
                        label: 'Jumlah Terdeteksi',
                        data: counts.length > 0 ? counts : [0],
                        backgroundColor: colors.indigo,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.05)' }
                        },
                        x: {
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        const adminTestCanvas = document.getElementById('adminTestChart');
        if (adminTestCanvas) {
            const rawTests = JSON.parse(adminDataEl.dataset.tests || '[]');
            
            // Breakdown of Normal, Ringan, Sedang, Berat test results
            const labels = ['Normal', 'Ringan', 'Sedang', 'Berat'];
            const stressCounts = labels.map(l => (rawTests.find(t => t.category === 'Stres' && t.result === l) || {count:0}).count);
            const anxietyCounts = labels.map(l => (rawTests.find(t => t.category === 'Kecemasan' && t.result === l) || {count:0}).count);
            const depressionCounts = labels.map(l => (rawTests.find(t => t.category === 'Depresi' && t.result === l) || {count:0}).count);

            new Chart(adminTestCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Stres',
                            data: stressCounts,
                            backgroundColor: colors.coral
                        },
                        {
                            label: 'Kecemasan',
                            data: anxietyCounts,
                            backgroundColor: colors.indigo
                        },
                        {
                            label: 'Depresi',
                            data: depressionCounts,
                            backgroundColor: colors.rose
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.05)' }
                        },
                        x: {
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }
    }
});
