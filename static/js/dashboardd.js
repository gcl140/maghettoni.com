document.addEventListener('DOMContentLoaded', function() {
    // Greeting based on time of day
    const hour = new Date().getHours();
    const greetingText = document.getElementById('greetingText');
    if (greetingText) {
        let greeting = 'Habari';
        if (hour < 12) greeting = 'Habari ya Asubuhi';
        else if (hour < 17) greeting = 'Habari ya Mchana';
        else greeting = 'Habari ya Jioni';
        greetingText.textContent = greeting;
    }
    
    // Update current date
    const currentDate = document.getElementById('currentDate');
    if (currentDate) {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        currentDate.textContent = now.toLocaleDateString('sw-TZ', options);
    }
    
    // Revenue Chart
    const revenueChart = document.getElementById('revenueChart');
    if (revenueChart) {
        const labels = JSON.parse(revenueChart.dataset.labels);
        const data = JSON.parse(revenueChart.dataset.values);

        const ctx = revenueChart.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mapato (TZS)',
                    data: data,
                    borderColor: '#603b2b',
                    backgroundColor: 'rgba(96, 59, 43, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'TZS ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'TZS ' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Add hover effects to all cards
    const cards = document.querySelectorAll('.hover-lift');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'transform 0.2s ease, box-shadow 0.2s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Animate stats numbers on load
    const statsNumbers = document.querySelectorAll('.text-xl.font-bold');
    statsNumbers.forEach(number => {
        const originalValue = number.textContent;
        const target = parseInt(originalValue.replace(/,/g, ''));
        
        if (!isNaN(target) && target > 0) {
            number.textContent = '0';
            
            setTimeout(() => {
                let count = 0;
                const duration = 1500; // 1.5 seconds
                const increment = target / (duration / 16); // 60fps
                
                const timer = setInterval(() => {
                    count += increment;
                    if (count >= target) {
                        count = target;
                        clearInterval(timer);
                    }
                    number.textContent = Math.floor(count).toLocaleString();
                }, 16); // ~60fps
            }, 300); // Delay to allow page to load
        }
    });
    
    // Add click event to search bar for demo
    const searchInput = document.querySelector('input[placeholder="Tafuta..."]');
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            this.parentElement.classList.add('ring-2', 'ring-brown-300');
        });
        searchInput.addEventListener('blur', function() {
            this.parentElement.classList.remove('ring-2', 'ring-brown-300');
        });
    }
    
    // Add notification badge animation
    const notificationBtn = document.querySelector('button .fa-bell');
    const maint = document.getElementById('maintenanceStatus');
    if (maint) {
        const emergencyCount = JSON.parse(maint.dataset.values);
    } else { 
        var emergencyCount = 0; }
    if (notificationBtn && emergencyCount > 0) {
        setInterval(() => {
            const badge = notificationBtn.nextElementSibling;
            if (badge && badge.classList.contains('animate-pulse')) {
                badge.classList.toggle('animate-pulse');
                setTimeout(() => {
                    badge.classList.toggle('animate-pulse');
                }, 1000);
            }
        }, 3000);
    }
    
    // Initialize tooltips for chart
    if (revenueChart) {
        const tooltips = revenueChart.parentElement.querySelectorAll('.chart-tooltip');
        tooltips.forEach(tooltip => {
            tooltip.style.opacity = '0';
        });
    }
});