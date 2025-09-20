function initDashboard(data) {
    let selectedDeliverySystems = [], selectedOffices = [], allDeliverySystems = [], allOffices = [];
    const charts = {};

    document.addEventListener('DOMContentLoaded', () => {
        // --- UTILITY FUNCTIONS ---
        const getElement = id => document.getElementById(id);
        const getElements = selector => document.querySelectorAll(selector);
        const createElement = (tag, className, content) => {
            const el = document.createElement(tag);
            if (className) el.className = className;
            if (content) el.innerHTML = content;
            return el;
        };
        const getQualityClass = quality => quality >= 80 ? 'quality-excellent' : quality >= 60 ? 'quality-good' : 'quality-poor';
        const getQualityColors = percentage => ({
            present: percentage >= 80 ? '#4CAF50' : percentage >= 60 ? '#FF9800' : '#F44336',
            missing: percentage >= 80 ? '#E8F5E9' : percentage >= 60 ? '#FFF3E0' : '#FFEBEE',
            text: percentage >= 80 ? '#2E7D32' : percentage >= 60 ? '#E65100' : '#C62828'
        });

        // --- CHART INITIALIZATION ---
        function createDoughnutChart(ctx, label, value, total, wrongFormatPercent = 0) {
            if (!ctx) return null;
            const percentage = total > 0 ? (value / total * 100).toFixed(1) : 0;
            const missingPercentage = total > 0 ? ((total - value) / total * 100).toFixed(1) : 0;
            const colors = getQualityColors(percentage);
            
            return new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [`${label} Present (${percentage}%)`, `${label} Missing (${missingPercentage}%)`],
                    datasets: [{
                        data: [value, total - value],
                        backgroundColor: [colors.present, colors.missing],
                        borderColor: ['#ffffff', '#ffffff'],
                        borderWidth: 3,
                        hoverBorderWidth: 4,
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '50%',
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'bottom',
                            labels: { padding: 15, font: { size: 11, weight: '600' }, color: '#555', usePointStyle: true, pointStyle: 'circle' }
                        },
                        tooltip: { 
                            enabled: true,
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: colors.present,
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: true,
                            callbacks: {
                                label: context => {
                                    const currentValue = context.dataset.data[context.dataIndex];
                                    const percentage = ((currentValue / total) * 100).toFixed(1);
                                    return `${context.label}: ${currentValue} (${percentage}%)`;
                                },
                                footer: () => wrongFormatPercent > 0 ? `⚠️ ${wrongFormatPercent.toFixed(1)}% have wrong format` : ''
                            }
                        }
                    },
                    animation: { animateRotate: true, animateScale: true, duration: 1000, easing: 'easeOutQuart' }
                },
                plugins: [{
                    id: 'centerText',
                    beforeDraw: chart => {
                        const ctx = chart.ctx;
                        const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                        const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;
                        
                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        
                        ctx.font = 'bold 16px Segoe UI';
                        ctx.fillStyle = colors.text;
                        ctx.fillText(`${percentage}%`, centerX, centerY - 4);
                        
                        ctx.font = '600 10px Segoe UI';
                        ctx.fillStyle = '#666';
                        ctx.fillText(label, centerX, centerY + 6);
                        
                        if (missingPercentage > 0 && percentage < 100) {
                            ctx.font = '500 8px Segoe UI';
                            ctx.fillStyle = '#999';
                            ctx.fillText(`${missingPercentage}% missing`, centerX, centerY + 16);
                        }
                        
                        ctx.restore();
                    }
                }]
            });
        }

        // Initialize charts
        if (data.total_pnrs > 0) {
            const chartData = [
                ['phoneChart', 'Phone', data.valid_phone_count, data.phone_wrong_format_pct],
                ['emailChart', 'Email', data.valid_email_count, data.email_wrong_format_pct],
                ['ffChart', 'FF#', data.ff_count, 0],
                ['mealChart', 'Meal', data.meal_count, 0],
                ['seatChart', 'Seat', data.seat_count, 0]
            ];
            
            chartData.forEach(([id, label, value, wrongFormat]) => {
                const ctx = getElement(id)?.getContext('2d');
                if (ctx) charts[id] = createDoughnutChart(ctx, label, value, data.total_pnrs, wrongFormat);
            });
        }

        // --- QUALITY HISTOGRAM ---
        function initializeQualityHistogram() {
            const histogram = getElement('qualityHistogram');
            if (!histogram) return;
            
            const bars = histogram.querySelectorAll('.histogram-bar');
            const counts = Array.from(bars).map(bar => parseInt(bar.dataset.count) || 0);
            const maxCount = Math.max(...counts, 1);
            const totalCount = counts.reduce((a, b) => a + b, 0);
            const categories = ['Critical', 'Poor', 'Fair', 'Good', 'Excellent'];
            
            bars.forEach((bar, index) => {
                if (bar.querySelector('.histogram-tooltip')) return;
                
                const count = counts[index];
                const percentage = (count / maxCount) * 100;
                const totalPercentage = totalCount > 0 ? ((count / totalCount) * 100).toFixed(1) : 0;
                const height = count > 0 ? Math.max(30, (percentage / 100) * 180) : 10;
                
                // Update existing bar-text to show count inside bar
                const barText = bar.querySelector('.bar-text');
                if (barText) barText.innerHTML = `${count} PNRs`;
                
                // Add tooltip only
                const tooltip = createElement('div', 'histogram-tooltip', `${categories[index]}: ${count} PNRs (${totalPercentage}% of total)`);
                bar.appendChild(tooltip);
                
                // Animate bar height
                setTimeout(() => {
                    bar.style.height = height + 'px';
                    bar.style.minHeight = height + 'px';
                }, index * 150);
            });
        }
        
        initializeQualityHistogram();

        // --- QUALITY TREND CHART ---
        window.initializeQualityTrendChart = async () => {
            const days = getElement('trend-days-selector').value;
            const url = new URL(window.location.origin + '/api/trends/');
            url.searchParams.set('days', days);
            
            const currentParams = new URLSearchParams(window.location.search);
            currentParams.forEach((value, key) => {
                if (key !== 'days') url.searchParams.append(key, value);
            });

            try {
                const response = await fetch(url);
                const trendData = await response.json();

                if (charts.qualityTrendChart) charts.qualityTrendChart.destroy();

                charts.qualityTrendChart = new Chart(getElement('qualityTrendChart'), {
                    type: 'line',
                    data: {
                        labels: trendData.trends.map(d => d.date),
                        datasets: [{
                            label: 'Quality Score',
                            data: trendData.trends.map(d => d.quality),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 3,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, max: 100, title: { display: true, text: 'Quality Score (%)' } },
                            x: { title: { display: true, text: 'Date' } }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            } catch (error) {
                console.error('Error fetching quality trend data:', error);
            }
        };
        
        // --- OFFICE PERFORMANCE CHART ---
        function initializeOfficeChart() {
            const ctx = getElement('officePerformanceChart');
            if (!ctx) {
                console.log('Office chart canvas not found');
                return;
            }
            
            if (!data.office_stats || data.office_stats.length === 0) {
                console.log('No office stats data available');
                // Show a message or placeholder
                const container = ctx.parentElement;
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">No office performance data available</div>';
                return;
            }
            
            const topOffices = data.office_stats.slice(0, 15);
            const labels = topOffices.map(office => office.office_name || office.office_id);
            const qualityScores = topOffices.map(office => parseFloat(office.avg_quality) || 0);
            const volumes = topOffices.map(office => parseInt(office.total) || 0);
            
            console.log('Initializing office chart with', topOffices.length, 'offices');
            
            if (charts.officeChart) {
                charts.officeChart.destroy();
            }
            
            charts.officeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Quality Score (%)',
                        data: qualityScores,
                        backgroundColor: qualityScores.map(score => 
                            score >= 80 ? 'rgba(76, 175, 80, 0.8)' : 
                            score >= 60 ? 'rgba(255, 193, 7, 0.8)' : 'rgba(244, 67, 54, 0.8)'
                        ),
                        borderColor: qualityScores.map(score => 
                            score >= 80 ? '#4CAF50' : score >= 60 ? '#FFC107' : '#F44336'
                        ),
                        borderWidth: 2
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { 
                            beginAtZero: true, 
                            max: 100, 
                            title: { display: true, text: 'Quality Score (%)' },
                            grid: { display: true, color: 'rgba(0,0,0,0.1)' }
                        },
                        y: { 
                            title: { display: true, text: 'Offices' },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#667eea',
                            borderWidth: 1,
                            cornerRadius: 8,
                            callbacks: {
                                title: context => `Office: ${context[0].label}`,
                                label: context => `Quality Score: ${context.parsed.x.toFixed(1)}%`,
                                afterLabel: context => {
                                    const index = context.dataIndex;
                                    return `Volume: ${volumes[index].toLocaleString()} PNRs`;
                                }
                            }
                        },
                    },
                    layout: {
                        padding: {
                            top: 10,
                            right: 60,
                            bottom: 10,
                            left: 10
                        }
                    }
                },
                plugins: [{
                    id: 'customLabels',
                    afterDraw: function(chart) {
                        const ctx = chart.ctx;
                        chart.data.datasets.forEach((dataset, i) => {
                            const meta = chart.getDatasetMeta(i);
                            meta.data.forEach((bar, index) => {
                                const score = qualityScores[index];
                                
                                // Quality score at end of bar (dark text)
                                ctx.fillStyle = '#333';
                                ctx.font = 'bold 12px Arial';
                                ctx.textAlign = 'left';
                                ctx.textBaseline = 'middle';
                                ctx.fillText(`${score.toFixed(1)}%`, bar.x + 8, bar.y);
                            });
                        });
                    }
                }]
            });
        }
        
        if (getElement('qualityTrendChart')) initializeQualityTrendChart();
        
        // Initialize office chart after a short delay to ensure DOM is ready
        setTimeout(() => {
            if (getElement('officePerformanceChart')) {
                console.log('Initializing office performance chart...');
                initializeOfficeChart();
            }
        }, 100);

        // --- TAB NAVIGATION & THEME SWITCHER ---
        getElements('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (tab.id === 'upload-btn') return window.location.href = '/upload/';
                
                getElements('.nav-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const sectionId = tab.getAttribute('data-section');
                getElements('.content-section').forEach(section => {
                    section.style.display = section.id === sectionId ? 'block' : 'none';
                    section.classList.toggle('active', section.id === sectionId);
                });
            });
        });

        getElements('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const theme = btn.getAttribute('data-theme');
                document.documentElement.setAttribute('data-theme', theme);
                getElements('.theme-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                localStorage.setItem('dashboardTheme', theme);
            });
        });

        const savedTheme = localStorage.getItem('dashboardTheme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            document.querySelector(`.theme-btn[data-theme="${savedTheme}"]`)?.classList.add('active');
        }

        // --- FILTER SYSTEM ---
        const isManualReload = !sessionStorage.getItem('filterNavigation');
        if (isManualReload) {
            sessionStorage.removeItem('filterState');
        }
        sessionStorage.removeItem('filterNavigation');

        function initializeFilters() {
            const urlParams = new URLSearchParams(window.location.search);
            selectedDeliverySystems = urlParams.getAll('delivery_systems') || [];
            selectedOffices = urlParams.getAll('offices') || [];
            
            selectedDeliverySystems.forEach(dsId => {
                const ds = allDeliverySystems.find(d => d.id === dsId);
                if (ds) {
                    const checkbox = document.getElementById(`ds-${dsId}`);
                    if (checkbox) checkbox.checked = true;
                    if (selectedDeliverySystems.length < allDeliverySystems.length) {
                        addDeliverySystemTag(dsId, ds.label);
                    }
                }
            });
            
            updateDeliverySystemDisplay();
            updateAvailableOffices(false).then(() => {
                selectedOffices.forEach(officeId => {
                    const checkbox = document.getElementById(`office-${officeId}`);
                    if (checkbox) {
                        checkbox.checked = true;
                        const office = allOffices.find(o => o.office_id === officeId);
                        if (office) {
                            addOfficeTag(officeId, office.name);
                        }
                    }
                });
                updateOfficeDisplay();
            });
        }

        async function updateAvailableOffices(clearSelections = true) {
            if (clearSelections) {
                selectedOffices = [];
                document.getElementById('office-tags').innerHTML = '';
            }
            
            if (selectedDeliverySystems.length === 0 || selectedDeliverySystems.length === allDeliverySystems.length) {
                allOffices = data.all_offices || [];
                populateOfficeDropdown();
                updateOfficeDisplay();
                return Promise.resolve();
            }
            
            try {
                const params = new URLSearchParams();
                selectedDeliverySystems.forEach(ds => params.append('delivery_systems', ds));
                
                const response = await fetch(`/api/offices-by-delivery-systems/?${params}`);
                const officeData = await response.json();
                allOffices = officeData.offices || [];
                populateOfficeDropdown();
                updateOfficeDisplay();
                return Promise.resolve();
            } catch (error) {
                console.error('Error loading offices:', error);
                allOffices = data.all_offices || [];
                populateOfficeDropdown();
                updateOfficeDisplay();
                return Promise.resolve();
            }
        }

        function populateDeliverySystemDropdown() {
            const dropdown = document.getElementById('delivery-system-dropdown');
            dropdown.innerHTML = '';
            
            const allOption = document.createElement('div');
            allOption.className = 'delivery-system-option';
            allOption.onclick = () => selectAllDeliverySystems();
            allOption.innerHTML = '<input type="checkbox" id="ds-all"><label for="ds-all">All</label>';
            dropdown.appendChild(allOption);
            
            allDeliverySystems.forEach(ds => {
                const option = document.createElement('div');
                option.className = 'delivery-system-option';
                option.onclick = () => toggleDeliverySystem(ds.id, ds.label);
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `ds-${ds.id}`;
                
                const label = document.createElement('label');
                label.textContent = ds.label;
                label.setAttribute('for', `ds-${ds.id}`);
                
                option.appendChild(checkbox);
                option.appendChild(label);
                dropdown.appendChild(option);
            });
        }

        function populateOfficeDropdown() {
            const dropdown = document.getElementById('office-dropdown-content');
            dropdown.innerHTML = '';
            
            if (allOffices.length === 0) {
                const option = document.createElement('div');
                option.className = 'office-option disabled';
                option.textContent = 'No offices available';
                dropdown.appendChild(option);
                return;
            }
            
            allOffices.forEach(office => {
                const option = document.createElement('div');
                option.className = 'office-option';
                option.onclick = () => toggleOffice(office.office_id, office.name);
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `office-${office.office_id}`;
                
                const label = document.createElement('label');
                label.textContent = office.name;
                label.setAttribute('for', `office-${office.office_id}`);
                
                option.appendChild(checkbox);
                option.appendChild(label);
                dropdown.appendChild(option);
            });
        }

        function toggleDeliverySystem(dsId, dsLabel) {
            const checkbox = document.getElementById(`ds-${dsId}`);
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                if (!selectedDeliverySystems.includes(dsId)) {
                    selectedDeliverySystems.push(dsId);
                    addDeliverySystemTag(dsId, dsLabel);
                }
            } else {
                selectedDeliverySystems = selectedDeliverySystems.filter(id => id !== dsId);
                removeDeliverySystemTag(dsId);
            }
            
            updateDeliverySystemDisplay();
            updateAvailableOffices(false);
        }

        function toggleOffice(officeId, officeName) {
            const checkbox = document.getElementById(`office-${officeId}`);
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                if (!selectedOffices.includes(officeId)) {
                    selectedOffices.push(officeId);
                    addOfficeTag(officeId, officeName);
                }
            } else {
                selectedOffices = selectedOffices.filter(id => id !== officeId);
                removeOfficeTag(officeId);
            }
            
            updateOfficeDisplay();
        }

        // Consolidated tag management
        const addTag = (containerId, tagClass, id, label, removeFunction) => {
            const container = getElement(containerId);
            if (!container) return;
            
            const tag = createElement('div', tagClass);
            tag.id = `${tagClass.split('-')[0]}-tag-${id}`;
            tag.innerHTML = `${label} <span class="close" onclick="${removeFunction}('${id}')">&times;</span>`;
            container.appendChild(tag);
        };
        
        const removeTag = (id, type, selectedArray, updateFunction, extraAction = null) => {
            const tag = getElement(`${type}-tag-${id}`);
            if (tag) tag.remove();
            
            const checkbox = getElement(`${type === 'ds' ? 'ds' : 'office'}-${id}`);
            if (checkbox) checkbox.checked = false;
            
            if (type === 'ds') {
                selectedDeliverySystems = selectedDeliverySystems.filter(item => item !== id);
                updateDeliverySystemDisplay();
                updateAvailableOffices(false);
            } else {
                selectedOffices = selectedOffices.filter(item => item !== id);
                updateOfficeDisplay();
            }
        };
        
        const addDeliverySystemTag = (dsId, dsLabel) => addTag('delivery-system-tags', 'delivery-system-tag', dsId, dsLabel, 'removeDeliverySystemTag');
        const addOfficeTag = (officeId, officeName) => addTag('office-tags', 'office-tag', officeId, officeName, 'removeOfficeTag');
        const removeDeliverySystemTag = dsId => removeTag(dsId, 'ds');
        const removeOfficeTag = officeId => removeTag(officeId, 'office');

        function selectAllDeliverySystems() {
            const allCheckbox = document.getElementById('ds-all');
            allCheckbox.checked = !allCheckbox.checked;
            
            if (allCheckbox.checked) {
                selectedDeliverySystems = [];
                allDeliverySystems.forEach(ds => {
                    selectedDeliverySystems.push(ds.id);
                    const checkbox = document.getElementById(`ds-${ds.id}`);
                    if (checkbox) checkbox.checked = true;
                });
                document.getElementById('delivery-system-tags').innerHTML = '';
                updateDeliverySystemInputDisplay('All');
            } else {
                selectedDeliverySystems = [];
                document.getElementById('delivery-system-tags').innerHTML = '';
                document.querySelectorAll('[id^="ds-"]').forEach(cb => {
                    if (cb.id !== 'ds-all') cb.checked = false;
                });
                updateDeliverySystemInputDisplay('All');
            }
            
            updateAvailableOffices(true);
        }

        // Consolidated display update functions
        const updateDisplay = (inputSelector, selectedItems, allItems, isOffice = false) => {
            const input = document.querySelector(inputSelector);
            if (!input) return;
            
            if (selectedItems.length === 0 || (allItems.length > 0 && selectedItems.length === allItems.length)) {
                input.placeholder = 'All';
            } else {
                input.placeholder = `${selectedItems.length} selected`;
            }
        };
        
        const updateDeliverySystemDisplay = () => updateDisplay('#delivery-system-filter-toggle input', selectedDeliverySystems, allDeliverySystems);
        const updateOfficeDisplay = () => updateDisplay('#office-input', selectedOffices, allOffices, true);
        const updateDeliverySystemInputDisplay = text => {
            const input = document.querySelector('#delivery-system-filter-toggle input');
            if (input) input.placeholder = text;
        };

        window.removeDeliverySystemTag = removeDeliverySystemTag;
        window.removeOfficeTag = removeOfficeTag;

        // --- DATE PICKER ---
        const [bookingDateDisplay, bookingDatePicker, bookingStartDate, bookingEndDate] = 
            ['booking_date_display', 'booking_date_picker', 'booking_start_date', 'booking_end_date'].map(getElement);

        window.updateBookingDateDisplay = () => {
            const start = bookingStartDate?.value;
            const end = bookingEndDate?.value;
            if (bookingDateDisplay) {
                bookingDateDisplay.value = start && end ? `${start} → ${end}` : 
                                         start ? `${start} → ...` : 
                                         end ? `... → ${end}` : 'start-date → end-date';
            }
        };
        updateBookingDateDisplay();

        bookingDateDisplay?.addEventListener('click', () => {
            if (bookingDatePicker) bookingDatePicker.style.display = 'block';
        });

        getElement('done-booking-dates-btn')?.addEventListener('click', () => {
            if (bookingDatePicker) bookingDatePicker.style.display = 'none';
        });

        getElement('clear-booking-dates-btn')?.addEventListener('click', () => {
            if (bookingStartDate) bookingStartDate.value = '';
            if (bookingEndDate) bookingEndDate.value = '';
            updateBookingDateDisplay();
        });

        // --- FILTER LOGIC ---
        getElement('apply-filters-btn')?.addEventListener('click', () => {
            sessionStorage.setItem('filterNavigation', 'true');
            const params = new URLSearchParams();
            const startDate = getElement('booking_start_date')?.value;
            const endDate = getElement('booking_end_date')?.value;

            if (startDate) params.set('start_date', startDate);
            if (endDate) params.set('end_date', endDate);

            selectedDeliverySystems.forEach(ds => params.append('delivery_systems', ds));
            selectedOffices.forEach(office => params.append('offices', office));

            window.location.search = params.toString();
        });

        getElement('clear-filters-btn')?.addEventListener('click', () => {
            selectedDeliverySystems = [];
            selectedOffices = [];
            if (bookingStartDate) bookingStartDate.value = '';
            if (bookingEndDate) bookingEndDate.value = '';
            updateBookingDateDisplay();
            ['delivery-system-tags', 'office-tags'].forEach(id => {
                const el = getElement(id);
                if (el) el.innerHTML = '';
            });
            getElements('input[type="checkbox"]').forEach(cb => cb.checked = false);
            window.location.href = window.location.pathname;
        });

        // Consolidated dropdown toggles
        const toggleDropdown = (toggleId, dropdownId) => {
            getElement(toggleId)?.addEventListener('click', e => {
                e.stopPropagation();
                const dropdown = getElement(dropdownId);
                if (dropdown) dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            });
        };
        
        toggleDropdown('delivery-system-filter-toggle', 'delivery-system-dropdown');
        toggleDropdown('office-filter-toggle', 'office-dropdown');

        document.addEventListener('click', e => {
            const dropdowns = [
                ['#delivery-system-filter-toggle', '#delivery-system-dropdown', 'delivery-system-dropdown'],
                ['#office-filter-toggle', '#office-dropdown', 'office-dropdown']
            ];
            
            dropdowns.forEach(([toggle, dropdown, id]) => {
                if (!e.target.closest(toggle) && !e.target.closest(dropdown)) {
                    const el = getElement(id);
                    if (el) el.style.display = 'none';
                }
            });
        });

        // Load delivery systems and initialize filters
        Promise.all([
            fetch('/api/delivery-systems/').then(res => res.json()),
            fetch('/api/offices-by-delivery-systems/').then(res => res.json())
        ]).then(([dsData, officeData]) => {
            allDeliverySystems = dsData.delivery_systems || [];
            allOffices = officeData.offices || [];
            populateDeliverySystemDropdown();
            populateOfficeDropdown();
            initializeFilters();
        }).catch(error => console.error('Error loading filters:', error));

        // --- EXPORT ---
        getElements('.export-link').forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                const params = new URLSearchParams(window.location.search);
                params.set('type', e.target.dataset.exportType);
                window.location.href = `${data.export_url}?${params.toString()}`;
            });
        });

        // --- DELIVERY SYSTEM PERFORMANCE CARDS ---
        function renderDeliverySystemCards() {
            const grid = getElement('delivery-system-grid');
            if (!grid || !data.delivery_system_stats) return;

            const sortedSystems = data.delivery_system_stats.sort((a, b) => b.total - a.total).slice(0, 10);
            const totalVolume = data.delivery_system_stats.reduce((sum, sys) => sum + sys.total, 0);
            const icons = { '1A': '🌐', '1G': '🌍', 'KQ': '✈️', 'WEB': '💻', 'MOB': '📱', 'ATO': '🤖', 'CTO': '📞', 'CEC': '🏢', 'NDC': '🔗', 'GSA': '🤝' };
            const rankEmojis = ['🥇', '🥈', '🥉'];

            grid.innerHTML = '';
            sortedSystems.forEach((system, index) => {
                const marketShare = totalVolume > 0 ? (system.total / totalVolume * 100).toFixed(1) : 0;
                const qualityClass = getQualityClass(system.avg_quality);
                const icon = icons[system.delivery_system_company?.toUpperCase()] || '🌐';
                const cardClass = system.delivery_system_company?.toLowerCase().replace(/[^a-z0-9]/g, '') || 'default';
                
                const card = createElement('div', `delivery-system-card ${cardClass}`);
                card.style.cssText = `animation: slideInUp 0.6s ease-out ${index * 0.1}s both; transform-origin: bottom;`;
                
                ['mouseenter', 'mouseleave'].forEach((event, i) => {
                    card.addEventListener(event, () => {
                        card.style.transform = i ? 'translateY(0) scale(1)' : 'translateY(-12px) scale(1.05)';
                        card.style.zIndex = i ? '1' : '10';
                    });
                });
                
                const rankBadge = index < 3 ? `<div class="rank-badge rank-${index + 1}" style="animation: bounceIn 0.8s ease-out ${index * 0.2 + 0.5}s both;">${rankEmojis[index]}</div>` : '';
                const performanceIndicator = system.avg_quality >= 80 ? '<div style="position: absolute; top: 8px; left: 8px; font-size: 16px;">✨</div>' : 
                                           system.avg_quality < 50 ? '<div style="position: absolute; top: 8px; left: 8px; font-size: 16px;">⚠️</div>' : '';
                
                card.innerHTML = `${rankBadge}${performanceIndicator}<div class="channel-icon" style="animation: pulse 2s infinite; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">${icon}</div><div class="channel-name" style="background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 12px; margin: 8px 0; backdrop-filter: blur(10px);">${system.delivery_system_company}</div><div class="metrics"><div class="quality-score ${qualityClass}" style="font-size: 22px; background: rgba(255,255,255,0.15); padding: 4px 8px; border-radius: 8px; margin-bottom: 6px; backdrop-filter: blur(5px);">${system.avg_quality.toFixed(1)}%</div><div class="volume" style="background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 6px; margin-bottom: 3px;">📊 ${system.total.toLocaleString()}</div><div class="market-share" style="background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 6px;">🌐 ${marketShare}%</div></div><div class="quality-bar" style="margin-top: 12px; height: 6px; background: rgba(255,255,255,0.2); border-radius: 3px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);"><div class="quality-fill" style="width: 0%; height: 100%; background: linear-gradient(90deg, rgba(255,255,255,0.8), rgba(255,255,255,1)); border-radius: 3px; transition: width 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${index * 0.2 + 0.5}s; box-shadow: 0 0 10px rgba(255,255,255,0.5);" data-width="${system.avg_quality}"></div></div>`;
                
                grid.appendChild(card);
                
                setTimeout(() => {
                    const qualityFill = card.querySelector('.quality-fill');
                    if (qualityFill) qualityFill.style.width = qualityFill.dataset.width + '%';
                }, 100);
            });
            
            if (!getElement('delivery-system-animations')) {
                const style = createElement('style');
                style.id = 'delivery-system-animations';
                style.textContent = '@keyframes slideInUp{from{opacity:0;transform:translateY(30px) scale(0.9)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes bounceIn{0%{opacity:0;transform:scale(0.3)}50%{opacity:1;transform:scale(1.05)}70%{transform:scale(0.9)}100%{opacity:1;transform:scale(1)}}';
                document.head.appendChild(style);
            }
        }

        renderDeliverySystemCards();
        
        // Initialize office chart
        initializeOfficeChart();

        // --- TABLE SORTING ---
        getElements('.data-table th.sortable, .heatmap-table th.sortable').forEach(headerCell => {
            headerCell.addEventListener('click', () => {
                const table = headerCell.closest('table');
                const headerIndex = Array.from(headerCell.parentElement.children).indexOf(headerCell);
                const isAscending = headerCell.classList.contains('sort-asc');
                
                table.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
                headerCell.classList.toggle('sort-asc', !isAscending);
                headerCell.classList.toggle('sort-desc', isAscending);

                const tbody = table.querySelector('tbody');
                Array.from(tbody.querySelectorAll('tr'))
                    .sort((a, b) => {
                        const aVal = parseFloat(a.querySelector(`td:nth-child(${headerIndex + 1})`).textContent.trim().replace('%', ''));
                        const bVal = parseFloat(b.querySelector(`td:nth-child(${headerIndex + 1})`).textContent.trim().replace('%', ''));
                        return (aVal > bVal ? 1 : -1) * (isAscending ? -1 : 1);
                    })
                    .forEach(tr => tbody.appendChild(tr));
            });
        });
    });
}