function initDashboard(data) {
    let selectedDeliverySystems = [], selectedOffices = [], allDeliverySystems = [], allOffices = [];
    const charts = {};
    
    document.addEventListener('DOMContentLoaded', () => {
        // --- UTILITY FUNCTIONS ---
        const getElement = id => document.getElementById(id);
        const getElements = selector => document.querySelectorAll(selector);

        // --- CACHED DOM ELEMENTS ---
        const elements = { // This should be inside DOMContentLoaded
            qualityTrendChart: getElement('qualityTrendChart'),
            trendDaysSelector: getElement('trend-days-selector'),
            officePerformanceChart: getElement('officePerformanceChart'),
            qualityHistogram: getElement('qualityHistogram'),
            deliverySystemDropdown: getElement('delivery-system-dropdown'),
            officeDropdownContent: getElement('office-dropdown-content'),
            deliverySystemTags: getElement('delivery-system-tags'),
            officeTags: getElement('office-tags'),
            deliverySystemFilterToggle: getElement('delivery-system-filter-toggle'),
            officeFilterToggle: getElement('office-filter-toggle'),
            officeInput: getElement('office-input'),
            bookingDateDisplay: getElement('booking_date_display'),
            bookingDatePicker: getElement('booking_date_picker'),
            bookingStartDate: getElement('booking_start_date'),
            bookingEndDate: getElement('booking_end_date'),
            modal: getElement('data-modal'),
            modalTitle: getElement('modal-title'),
            deliverySystemChart: getElement('deliverySystemChart'),
            modalTableBody: getElement('modal-table-body'),
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
                    cutout: '65%',
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
            if (!elements.qualityHistogram) return;
            
            const bars = elements.qualityHistogram.querySelectorAll('.histogram-bar');
            const fragment = document.createDocumentFragment();

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
                const tooltip = document.createElement('div');
                tooltip.className = 'histogram-tooltip';
                tooltip.textContent = `${categories[index]}: ${count} PNRs (${totalPercentage}% of total)`;
                
                fragment.appendChild(tooltip);
                
                // Animate bar height
                setTimeout(() => {
                    bar.style.height = height + 'px';
                    bar.style.minHeight = height + 'px';
                }, index * 150);
            });
            bars.forEach(bar => bar.appendChild(fragment.cloneNode(true)));
        }
        
        initializeQualityHistogram();

        // --- QUALITY TREND CHART ---
        window.initializeQualityTrendChart = async () => {
            const days = elements.trendDaysSelector.value;
            const url = new URL(window.location.origin + '/api/trends/');
            url.searchParams.set('days', days);
            
            const currentParams = new URLSearchParams(window.location.search); // Re-read params
            currentParams.forEach((value, key) => {
                if (key !== 'days') url.searchParams.append(key, value);
            });

            try {
                const response = await fetch(url);
                const trendData = await response.json();

                if (charts.qualityTrendChart) charts.qualityTrendChart.destroy();

                charts.qualityTrendChart = new Chart(elements.qualityTrendChart, {
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
            if (!elements.officePerformanceChart) {
                return;
            }
            
            if (!data.office_stats || data.office_stats.length === 0) {
                // Show a message or placeholder
                const container = elements.officePerformanceChart.parentElement;
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">No office performance data available</div>';
                return;
            }
            
            const topOffices = data.office_stats.slice(0, 15);
            const labels = topOffices.map(office => office.office_name || office.office_id);
            const qualityScores = topOffices.map(office => parseFloat(office.avg_quality) || 0);
            const volumes = topOffices.map(office => parseInt(office.total) || 0);
                        
            if (charts.officeChart) {
                charts.officeChart.destroy();
            }
            
            charts.officeChart = new Chart(elements.officePerformanceChart, {
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
                        title: {
                            display: true,
                            text: '🏢 Office Performance Spotlight: Top 15 by Volume',
                            align: 'start',
                            font: {
                                size: 18,
                                weight: 'bold',
                            },
                            padding: { top: 10, bottom: 20 }
                        },
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
        
        if (elements.qualityTrendChart) initializeQualityTrendChart();
        
        // Initialize office chart after a short delay to ensure DOM is ready
        setTimeout(() => {
            if (elements.officePerformanceChart) {
                initializeOfficeChart();
            }
        }, 100);

        // --- DELIVERY SYSTEM CHART ---
        function initializeDeliverySystemChart() {
            const ctx = elements.deliverySystemChart;
            if (!ctx || !data.delivery_system_stats) return;

            const sortedSystems = data.delivery_system_stats.sort((a, b) => b.total - a.total);
            const labels = sortedSystems.map(s => s.delivery_system_company);
            const volumes = sortedSystems.map(s => s.total);
            const qualityScores = sortedSystems.map(s => s.avg_quality);

            const backgroundColors = qualityScores.map(q => {
                if (q >= 80) return 'rgba(76, 175, 80, 0.7)';  // Excellent
                if (q >= 60) return 'rgba(255, 152, 0, 0.7)'; // Good
                return 'rgba(244, 67, 54, 0.7)';             // Poor
            });

            const borderColors = qualityScores.map(q => {
                if (q >= 80) return 'rgba(76, 175, 80, 1)';
                if (q >= 60) return 'rgba(255, 152, 0, 1)';
                return 'rgba(244, 67, 54, 1)';
            });

            if (charts.deliverySystemChart) {
                charts.deliverySystemChart.destroy();
            }

            charts.deliverySystemChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Booking Volume',
                        data: volumes,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 1,
                        barPercentage: 0.7,
                        categoryPercentage: 0.8,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false },
                        title: {
                            display: true,
                            text: 'Booking Volume & Quality by Delivery System',
                            align: 'start',
                            font: { size: 18, weight: 'bold' },
                            padding: { bottom: 20 }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => `Volume: ${context.parsed.y.toLocaleString()}`,
                                afterLabel: (context) => `Quality: ${qualityScores[context.dataIndex].toFixed(1)}%`
                            }
                        }
                    },
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: 'PNR Volume' } },
                        x: { title: { display: true, text: 'Delivery System' } }
                    }
                }
            });
        }

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
                if (elements.officeTags) elements.officeTags.innerHTML = '';
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
            if (!elements.deliverySystemDropdown) return;
            
            const fragment = document.createDocumentFragment();
            elements.deliverySystemDropdown.innerHTML = '';
            
            const allOption = document.createElement('div');
            allOption.className = 'delivery-system-option';
            allOption.onclick = () => selectAllDeliverySystems();
            allOption.innerHTML = '<input type="checkbox" id="ds-all"><label for="ds-all">All</label>';
            fragment.appendChild(allOption);
            
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
                fragment.appendChild(option);
            });
            elements.deliverySystemDropdown.appendChild(fragment);
        }

        function populateOfficeDropdown() {
            const dropdown = elements.officeDropdownContent;
            if (!dropdown) return;
            const fragment = document.createDocumentFragment();
            dropdown.innerHTML = ''; // Clear existing
            
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
                fragment.appendChild(option);
            });
            dropdown.appendChild(fragment);
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
            const container = elements[containerId];
            if (!container) return;
            
            const tag = document.createElement('div');
            tag.className = tagClass;
            tag.id = `${tagClass.split('-')[0]}-tag-${id}`;
            tag.dataset.id = id;
            tag.innerHTML = `${label} <span class="close" data-action="remove-tag">&times;</span>`;
            container.appendChild(tag);
        };
        
        const removeTag = (id, type) => {
            const tagId = type === 'ds' ? 'delivery-system-tag' : 'office-tag';
            const tag = getElement(`${tagId}-${id}`);
            if (tag) tag.remove();
            
            const checkboxId = type === 'ds' ? `ds-${id}` : `office-${id}`;
            const checkbox = getElement(checkboxId);
            if (checkbox) checkbox.checked = false;
            
            if (type === 'ds') {
                selectedDeliverySystems = selectedDeliverySystems.filter(item => item !== id);
                updateDeliverySystemDisplay();
                updateAvailableOffices(true); // Re-fetch offices when a system is removed
            } else {
                selectedOffices = selectedOffices.filter(item => item !== id);
                updateOfficeDisplay();
            }
        };
        
        const addDeliverySystemTag = (dsId, dsLabel) => addTag('deliverySystemTags', 'delivery-system-tag', dsId, dsLabel);
        const addOfficeTag = (officeId, officeName) => addTag('officeTags', 'office-tag', officeId, officeName);

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
                if (elements.deliverySystemTags) elements.deliverySystemTags.innerHTML = '';
                updateDeliverySystemInputDisplay('All');
            } else {
                selectedDeliverySystems = [];
                if (elements.deliverySystemTags) elements.deliverySystemTags.innerHTML = '';
                document.querySelectorAll('[id^="ds-"]').forEach(cb => {
                    if (cb.id !== 'ds-all') cb.checked = false;
                });
                updateDeliverySystemInputDisplay('All');
            }
            
            updateAvailableOffices(true);
        }

        // Consolidated display update functions
        const updateDisplay = (input, selectedItems, allItems) => {
            if (!input) return;
            if (selectedItems.length === 0 || (allItems.length > 0 && selectedItems.length === allItems.length)) {
                input.placeholder = 'All';
            } else {
                input.placeholder = `${selectedItems.length} selected`;
            }
        };

        const updateDeliverySystemDisplay = () => updateDisplay(elements.deliverySystemFilterToggle?.querySelector('input'), selectedDeliverySystems, allDeliverySystems);
        const updateOfficeDisplay = () => updateDisplay(elements.officeInput, selectedOffices, allOffices);
        const updateDeliverySystemInputDisplay = text => {
            const input = elements.deliverySystemFilterToggle?.querySelector('input');
            if (input) input.placeholder = text;
        };

        // Event delegation for removing tags
        elements.deliverySystemTags?.addEventListener('click', e => {
            if (e.target.dataset.action === 'remove-tag') {
                removeTag(e.target.parentElement.dataset.id, 'ds');
            }
        });

        elements.officeTags?.addEventListener('click', e => {
            if (e.target.dataset.action === 'remove-tag') {
                removeTag(e.target.parentElement.dataset.id, 'office');
            }
        });

        // --- DATE PICKER ---
        window.updateBookingDateDisplay = () => {
            const start = elements.bookingStartDate?.value;
            const end = elements.bookingEndDate?.value;
            if (elements.bookingDateDisplay) {
                elements.bookingDateDisplay.value = start && end ? `${start} → ${end}` : 
                                         start ? `${start} → ...` : 
                                         end ? `... → ${end}` : 'start-date → end-date';
            }
        };
        updateBookingDateDisplay();

        elements.bookingDateDisplay?.addEventListener('click', () => {
            if (elements.bookingDatePicker) elements.bookingDatePicker.style.display = 'block';
        });

        getElement('done-booking-dates-btn')?.addEventListener('click', () => {
            if (elements.bookingDatePicker) elements.bookingDatePicker.style.display = 'none';
        });

        getElement('clear-booking-dates-btn')?.addEventListener('click', () => {
            if (elements.bookingStartDate) elements.bookingStartDate.value = '';
            if (elements.bookingEndDate) elements.bookingEndDate.value = '';
            updateBookingDateDisplay();
        });

        // --- FILTER LOGIC ---
        getElement('apply-filters-btn')?.addEventListener('click', () => {
            sessionStorage.setItem('filterNavigation', 'true');
            const params = new URLSearchParams();
            const startDate = elements.bookingStartDate?.value;
            const endDate = elements.bookingEndDate?.value;

            if (startDate) params.set('start_date', startDate);
            if (endDate) params.set('end_date', endDate);

            selectedDeliverySystems.forEach(ds => params.append('delivery_systems', ds));
            selectedOffices.forEach(office => params.append('offices', office));

            window.location.search = params.toString();
        });

        getElement('clear-filters-btn')?.addEventListener('click', () => {
            selectedDeliverySystems = [];
            selectedOffices = [];
            if (elements.bookingStartDate) elements.bookingStartDate.value = '';
            if (elements.bookingEndDate) elements.bookingEndDate.value = '';
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

        if (elements.deliverySystemFilterToggle) toggleDropdown('delivery-system-filter-toggle', 'delivery-system-dropdown');
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

        initializeDeliverySystemChart();
        
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

        // Make the entire delivery system chart clickable
        if (elements.deliverySystemChart) {
            elements.deliverySystemChart.addEventListener('click', () => {
                openDataModal('all_delivery_systems', 'Detailed PNRs by Delivery System');
            });
        }

        // --- MODAL FOR DETAILED DATA ---
        const modalTableHead = getElement('modal-table')?.querySelector('thead tr');
        const modalExportBtn = getElement('modal-export-btn');
        let currentModalMetric = ''; // Variable to store the metric for the currently open modal

        // Function to open the modal and fetch data
        async function openDataModal(metric, title) {
            const modal = elements.modal;
            if (!modal || !elements.modalTitle || !elements.modalTableBody || !modalTableHead) return;
            
            const modalSubtitle = getElement('modal-subtitle');
            currentModalMetric = metric; // Store the metric
            const modalDynamicFilters = getElement('modal-dynamic-filters');
            modalDynamicFilters.innerHTML = ''; // Clear previous dynamic filters
            elements.modalTitle.textContent = title;
            modalSubtitle.textContent = 'Use the inputs in the column headers to filter data like in Excel. Click the export button to download the currently visible data.';
            elements.modalTableBody.innerHTML = '<tr><td colspan="6">Loading data...</td></tr>';
            modal.style.display = 'flex'; // Show modal
            try {
                const params = new URLSearchParams(window.location.search);
                params.set('metric', metric);
                const response = await fetch(`/api/detailed-pnrs/?${params.toString()}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const detailedData = await response.json();

                // Populate table
                modalTableHead.innerHTML = `
                    <th>PNR</th>
                    <th class="sortable" data-column-index="1">
                        Office ID
                        <input type="text" class="modal-filter-input" data-column-index="1" placeholder="Filter..." onkeyup="filterModalTable()">
                    </th>
                    <th>
                        Delivery System
                        <input type="text" class="modal-filter-input" data-column-index="2" placeholder="Filter..." onkeyup="filterModalTable()">
                    </th>
                    <th>Agent ID</th>
                    <th>Contact Type</th>
                    <th>Contact Detail</th>
                `;

                elements.modalTableBody.innerHTML = ''; // Clear loading message
                const fragment = document.createDocumentFragment();
                if (detailedData.pnrs && detailedData.pnrs.length > 0) {
                    detailedData.pnrs.forEach(pnr => {
                        const row = document.createElement('tr');
                        // Add a data attribute for filtering
                        row.dataset.filterCol1 = (pnr.office_id || '').toLowerCase();
                        row.dataset.filterCol2 = (pnr.delivery_system || '').toLowerCase();

                        row.innerHTML = `
                            <td>${pnr.control_number || '-'}</td>
                            <td>${pnr.office_id || '-'}</td>
                            <td>${pnr.delivery_system || '-'}</td>
                            <td>${pnr.agent || '-'}</td>
                            <td>${pnr.contact_type || '-'}</td>
                            <td>${pnr.contact_detail || '-'}</td>
                        `;
                        fragment.appendChild(row);
                    });
                    elements.modalTableBody.appendChild(fragment);
                } else {
                    elements.modalTableBody.innerHTML = '<tr><td colspan="6">No data available for this metric.</td></tr>';
                }

                // Add sorting to the new sortable header
                modalTableHead.querySelector('.sortable').addEventListener('click', handleSort);

            } catch (error) {
                elements.modalTableBody.innerHTML = `<tr><td colspan="6">Error loading data.</td></tr>`;
            }
        }

        // Make the filter function globally accessible
        window.filterModalTable = () => {
            const filters = Array.from(modalTableHead.querySelectorAll('.modal-filter-input')).map(input => ({
                index: parseInt(input.dataset.columnIndex),
                value: input.value.toLowerCase()
            }));

            const rows = elements.modalTableBody.querySelectorAll('tr');
            rows.forEach(row => {
                let isVisible = true;
                filters.forEach(filter => {
                    if (filter.value) {
                        const cellValue = row.dataset[`filterCol${filter.index}`];
                        if (!cellValue || !cellValue.includes(filter.value)) {
                            isVisible = false;
                        }
                    }
                });
                row.style.display = isVisible ? '' : 'none';
            });
        };

        // Sorting handler for modal table
        function handleSort(e) {
            const headerCell = e.currentTarget;
            const table = headerCell.closest('table');
            const tbody = table.querySelector('tbody');
            const headerIndex = parseInt(headerCell.dataset.columnIndex);
            const isAscending = headerCell.classList.contains('sort-asc');

            table.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
            headerCell.classList.toggle('sort-asc', !isAscending);
            headerCell.classList.toggle('sort-desc', isAscending);

            Array.from(tbody.querySelectorAll('tr'))
                .sort((a, b) => {
                    const aVal = a.querySelector(`td:nth-child(${headerIndex + 1})`).textContent.trim();
                    const bVal = b.querySelector(`td:nth-child(${headerIndex + 1})`).textContent.trim();
                    return (aVal > bVal ? 1 : -1) * (isAscending ? -1 : 1);
                })
                .forEach(tr => tbody.appendChild(tr));
        }

        // Add click listeners to the overview cards
        getElements('.clickable-card').forEach(card => {
            card.addEventListener('click', () => {
                const metric = card.dataset.metric;
                const title = card.querySelector('.card-title').textContent;
                if (metric) {
                    openDataModal(metric, `Details for: ${title}`);
                }
            });
        });

        // Close modal logic
        getElement('modal-close-btn')?.addEventListener('click', () => elements.modal.style.display = 'none');
        elements.modal?.addEventListener('click', (e) => {
            if (e.target === elements.modal) elements.modal.style.display = 'none';
        });

        // Export button logic
        modalExportBtn?.addEventListener('click', () => {
            const params = new URLSearchParams(window.location.search); // Re-read params
            params.set('type', currentModalMetric); // Use the stored metric
            window.location.href = `${data.export_url}?${params.toString()}`;
        });
    });
}