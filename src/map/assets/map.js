/**
 * 全球军事态势地图 - 高德地图 JSAPI 核心逻辑
 * 负责地图初始化、图标管理、图层控制、交互事件
 */

(function() {
    'use strict';

    // 全局地图实例
    let map = null;
    let clusterer = null;

    // 图层管理
    const layers = {
        warship: { visible: false, markers: [], color: '#FF4444' },
        submarine: { visible: false, markers: [], color: '#CC00CC' },
        base: { visible: false, markers: [], color: '#FF8800' },
        airport: { visible: false, markers: [], color: '#4488FF' },
        ammunition: { visible: false, markers: [], color: '#FF5500' },
        antiAircraft: { visible: false, markers: [], color: '#FFCC00' },
        militaryAircraft: { visible: false, markers: [], color: '#00CCFF' },
        oilDepot: { visible: false, markers: [], color: '#884400' }
    };

    // 特殊图层
    let heatmapLayer = null;
    let trackLayer = null;
    let radiusLayer = null;

    // 底图类型
    let currentBasemap = 'amap';
    const basemaps = {
        amap: null,      // 高德默认
        tianditu: null,  // 天地图
        osm: null        // OSM
    };

    // 当前缩放级别
    let currentZoom = 4;

    // 聚合配置
    const CLUSTER_CONFIG = {
        minZoom: 4,
        maxZoom: 12,
        radius: 80,
        gridSize: 60
    };

    /**
     * SVG 图标 data-uri 生成
     */
    function getIconSvgUri(type) {
        const svgPaths = {
            warship: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <path fill="#FF4444" d="M16 2L4 14l3 2 2-1 6 4 6-4 2 1 3-2L16 2z"/>
                <path fill="#FF4444" d="M4 18c0 6 5 10 12 10s12-4 12-10H4z"/>
                <path fill="#CC3333" d="M8 18v4c0 1 1 2 2 2h12c1 0 2-1 2-2v-4H8z"/>
                <rect fill="#FF6666" x="14" y="8" width="4" height="6" rx="1"/>
            </svg>`,
            submarine: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <ellipse fill="#CC00CC" cx="16" cy="18" rx="12" ry="6"/>
                <ellipse fill="#990099" cx="16" cy="18" rx="10" ry="5"/>
                <rect fill="#CC00CC" x="14" y="8" width="4" height="10" rx="2"/>
                <circle fill="#DD44DD" cx="16" cy="8" r="3"/>
                <path fill="#AA00AA" d="M6 18c-2 0-4 1-4 2s2 2 4 2l2-4z"/>
                <path fill="#AA00AA" d="M26 18c2 0 4 1 4 2s-2 2-4 2l-2-4z"/>
            </svg>`,
            base: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <rect fill="#FF8800" x="4" y="14" width="24" height="14" rx="2"/>
                <rect fill="#CC6600" x="8" y="18" width="6" height="6"/>
                <rect fill="#CC6600" x="18" y="18" width="6" height="6"/>
                <polygon fill="#FFAA33" points="16,2 4,14 28,14"/>
                <rect fill="#FFD700" x="14" y="6" width="4" height="8"/>
            </svg>`,
            airport: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <rect fill="#4488FF" x="6" y="12" width="20" height="16" rx="2"/>
                <rect fill="#3366CC" x="10" y="16" width="12" height="8" rx="1"/>
                <rect fill="#66AAFF" x="12" y="6" width="8" height="6"/>
                <polygon fill="#88CCFF" points="16,2 12,6 20,6"/>
                <rect fill="#2255AA" x="4" y="26" width="24" height="2" rx="1"/>
            </svg>`,
            ammunition: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <rect fill="#FF5500" x="8" y="10" width="6" height="14" rx="1"/>
                <rect fill="#FF5500" x="18" y="10" width="6" height="14" rx="1"/>
                <rect fill="#FF7733" x="9" y="6" width="4" height="6" rx="1"/>
                <rect fill="#FF7733" x="19" y="6" width="4" height="6" rx="1"/>
                <polygon fill="#FFCC00" points="11,2 9,6 13,6"/>
                <polygon fill="#FFCC00" points="21,2 19,6 23,6"/>
                <rect fill="#CC4400" x="6" y="24" width="20" height="4" rx="1"/>
            </svg>`,
            antiAircraft: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <rect fill="#FFCC00" x="14" y="16" width="4" height="12"/>
                <polygon fill="#FFCC00" points="16,2 8,16 24,16"/>
                <polygon fill="#FFDD44" points="16,6 12,14 20,14"/>
                <rect fill="#DDAA00" x="6" y="26" width="20" height="3" rx="1"/>
                <circle fill="#FFEE66" cx="16" cy="10" r="2"/>
            </svg>`,
            militaryAircraft: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <ellipse fill="#00CCFF" cx="16" cy="16" rx="12" ry="4"/>
                <polygon fill="#00AADD" points="4,16 8,12 8,20"/>
                <polygon fill="#00AADD" points="28,16 24,12 24,20"/>
                <polygon fill="#00EEFF" points="16,8 14,14 18,14"/>
                <rect fill="#0099BB" x="10" y="14" width="12" height="4" rx="1"/>
                <circle fill="#00FFFF" cx="16" cy="16" r="2"/>
            </svg>`,
            oilDepot: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <ellipse fill="#884400" cx="16" cy="20" rx="10" ry="8"/>
                <ellipse fill="#AA5500" cx="16" cy="14" rx="8" ry="6"/>
                <ellipse fill="#CC6600" cx="16" cy="14" rx="4" ry="3"/>
                <rect fill="#663300" x="14" y="4" width="4" height="8"/>
                <ellipse fill="#885500" cx="16" cy="4" rx="3" ry="1"/>
            </svg>`
        };

        const svg = svgPaths[type] || svgPaths.base;
        return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }

    /**
     * 创建单个图标
     */
    function createMarker(lng, lat, type, data) {
        const icon = new AMap.Icon({
            size: new AMap.Size(32, 32),
            image: getIconSvgUri(type),
            imageSize: new AMap.Size(32, 32),
            anchor: new AMap.Pixel(16, 16)
        });

        const marker = new AMap.Marker({
            position: new AMap.LngLat(lng, lat),
            icon: icon,
            extData: {
                type: type,
                data: data
            }
        });

        // 鼠标悬停事件
        marker.on('mouseover', function(e) {
            showTooltip(e, type, data);
        });

        // 鼠标移出事件
        marker.on('mouseout', function() {
            hideTooltip();
        });

        // 鼠标点击事件
        marker.on('click', function() {
            if (window.mapBridge && window.mapBridge.onIconClick) {
                window.mapBridge.onIconClick(type, data.unit_id || data.id || '');
            }
        });

        return marker;
    }

    /**
     * 显示悬停提示框
     */
    function showTooltip(e, type, data) {
        const tooltip = document.getElementById('tooltip');
        const typeNames = {
            warship: '军舰',
            submarine: '潜艇',
            base: '军事基地',
            airport: '机场',
            ammunition: '弹药库',
            antiAircraft: '防空导弹',
            militaryAircraft: '军用飞机',
            oilDepot: '油库'
        };

        const titleEl = tooltip.querySelector('.tooltip-title');
        const contentEl = tooltip.querySelector('.tooltip-content');

        titleEl.textContent = typeNames[type] || type;

        let contentHtml = `
            <div class="tooltip-row"><span class="tooltip-label">类型</span><span class="tooltip-value">${typeNames[type] || type}</span></div>
            <div class="tooltip-row"><span class="tooltip-label">名称</span><span class="tooltip-value">${data.name || '未知'}</span></div>
            <div class="tooltip-row"><span class="tooltip-label">坐标</span><span class="tooltip-value">${data.lng?.toFixed(4) || '?'}, ${data.lat?.toFixed(4) || '?'}</span></div>
        `;

        if (data.unit_id) {
            contentHtml += `<div class="tooltip-row"><span class="tooltip-label">单位ID</span><span class="tooltip-value">${data.unit_id}</span></div>`;
        }
        if (data.unit_name) {
            contentHtml += `<div class="tooltip-row"><span class="tooltip-label">所属单位</span><span class="tooltip-value">${data.unit_name}</span></div>`;
        }
        if (data.status) {
            contentHtml += `<div class="tooltip-row"><span class="tooltip-label">状态</span><span class="tooltip-value">${data.status}</span></div>`;
        }

        contentEl.innerHTML = contentHtml;

        // 定位tooltip
        const containerPos = document.getElementById('container').getBoundingClientRect();
        tooltip.style.display = 'block';
        tooltip.style.left = (e.domEvent.clientX - containerPos.left + 15) + 'px';
        tooltip.style.top = (e.domEvent.clientY - containerPos.top + 15) + 'px';
    }

    /**
     * 隐藏提示框
     */
    function hideTooltip() {
        document.getElementById('tooltip').style.display = 'none';
    }

    /**
     * 初始化地图
     */
    function initMap() {
        map = new AMap.Map('map', {
            zoom: 4,
            center: [105, 36],
            viewMode: '2D',
            mapStyle: 'amap://styles/darkblue', // 深蓝军事风格
            features: ['bg', 'road', 'building', 'point']
        });

        // 添加比例尺
        const scale = new AMap.Scale({
            position: 'LB',
            offset: new AMap.Pixel(10, 30)
        });
        map.addControl(scale);

        // 初始化特殊图层
        heatmapLayer = new AMap.HeatmapLayer({ zIndex: 100 });
        trackLayer = new AMap.LayerGroup();
        radiusLayer = new AMap.LayerGroup();

        map.on('zoomchange', function() {
            currentZoom = map.getZoom();
            updateCluster();
            updateScaleText();
        });

        map.on('moveend', function() {
            updateScaleText();
        });

        // 初始化聚类
        clusterer = new AMap.MarkerClusterer(map, [], {
            minZoom: CLUSTER_CONFIG.minZoom,
            maxZoom: CLUSTER_CONFIG.maxZoom,
            radius: CLUSTER_CONFIG.radius,
            gridSize: CLUSTER_CONFIG.gridSize,
            renderClusterMarker: function(context) {
                const count = context.count;
                let size = 40;
                if (count > 100) size = 60;
                if (count > 500) size = 80;

                const div = document.createElement('div');
                div.style.width = size + 'px';
                div.style.height = size + 'px';
                div.style.background = 'rgba(68, 136, 255, 0.8)';
                div.style.border = '2px solid #4488ff';
                div.style.borderRadius = '50%';
                div.style.color = '#fff';
                div.style.textAlign = 'center';
                div.style.lineHeight = size + 'px';
                div.style.fontSize = '12px';
                div.style.fontWeight = 'bold';
                div.textContent = count;
                context.marker.setExtData({ type: 'cluster', count: count });
            },
            renderMarker: function(context) {
                // 单个marker由各自的事件处理
            }
        });

        // 绑定控制面板事件
        bindControlEvents();

        console.log('[Map] 地图初始化完成');
    }

    /**
     * 绑定控制面板事件
     */
    function bindControlEvents() {
        // 底图切换
        document.querySelectorAll('.basemap-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const type = this.dataset.type;
                switchBasemap(type);
                document.querySelectorAll('.basemap-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // 军事目标图层开关
        Object.keys(layers).forEach(type => {
            const checkbox = document.getElementById('toggle-' + type);
            if (checkbox) {
                checkbox.addEventListener('change', function() {
                    setLayerVisible(type, this.checked);
                });
            }
        });

        // 热力图开关
        const heatmapCheckbox = document.getElementById('toggle-heatmap');
        if (heatmapCheckbox) {
            heatmapCheckbox.addEventListener('change', function() {
                setHeatmapVisible(this.checked);
            });
        }

        // 航迹线开关
        const tracksCheckbox = document.getElementById('toggle-tracks');
        if (tracksCheckbox) {
            tracksCheckbox.addEventListener('change', function() {
                setTracksVisible(this.checked);
            });
        }

        // 作战半径开关
        const radiusCheckbox = document.getElementById('toggle-radius');
        if (radiusCheckbox) {
            radiusCheckbox.addEventListener('change', function() {
                setRadiusVisible(this.checked);
            });
        }
    }

    /**
     * 切换底图
     */
    function switchBasemap(type) {
        if (!map) return;

        // 移除当前底图（如果有）
        if (currentBasemap && basemaps[currentBasemap]) {
            map.remove(basemaps[currentBasemap]);
        }

        // 加载新底图
        switch (type) {
            case 'amap':
                // 高德默认底图，直接使用
                currentBasemap = 'amap';
                basemaps.amap = null;
                map.setMapStyle('amap://styles/darkblue');
                break;

            case 'tianditu':
                // 天地图
                currentBasemap = 'tianditu';
                map.setMapStyle('amap://styles/normal');
                // 天地图需要单独加载图层
                break;

            case 'osm':
                // OSM
                currentBasemap = 'osm';
                map.setMapStyle('amap://styles/normal');
                // OSM图层
                break;
        }

        console.log('[Map] 底图切换为:', type);
    }

    /**
     * 设置图层可见性
     */
    function setLayerVisible(type, visible) {
        if (!layers[type]) return;

        layers[type].visible = visible;

        if (visible) {
            // 显示图层
            if (layers[type].markers.length > 0) {
                clusterer.addMarkers(layers[type].markers);
            }
        } else {
            // 隐藏图层
            if (layers[type].markers.length > 0) {
                clusterer.removeMarkers(layers[type].markers);
            }
        }

        updateStats();
        console.log('[Map] 图层', type, '可见性:', visible);
    }

    /**
     * 更新聚合（根据缩放级别）
     */
    function updateCluster() {
        if (!clusterer) return;

        // 4-12级自适应聚合
        if (currentZoom >= CLUSTER_CONFIG.minZoom && currentZoom <= CLUSTER_CONFIG.maxZoom) {
            clusterer.setMinZoom(CLUSTER_CONFIG.minZoom);
            clusterer.setMaxZoom(CLUSTER_CONFIG.maxZoom);
        }
    }

    /**
     * 更新比例尺显示
     */
    function updateScaleText() {
        if (!map) return;

        const zoom = map.getZoom();
        // 粗略计算：每级 zoom 约 2 倍距离
        const scaleText = document.getElementById('scale-text');
        if (scaleText) {
            let scale = '';
            if (zoom < 6) scale = '500km';
            else if (zoom < 8) scale = '200km';
            else if (zoom < 10) scale = '50km';
            else if (zoom < 12) scale = '20km';
            else if (zoom < 14) scale = '10km';
            else scale = '5km';
            scaleText.textContent = '比例尺: ' + scale;
        }
    }

    /**
     * 添加单个图标
     */
    function addIcon(type, lng, lat, data) {
        if (!map) return;

        const marker = createMarker(lng, lat, type, data);
        layers[type].markers.push(marker);

        if (layers[type].visible) {
            clusterer.addMarker(marker);
        }

        updateStats();
        return marker;
    }

    /**
     * 批量添加图标
     */
    function addIconsBatch(icons) {
        if (!map || !icons || !Array.isArray(icons)) return;

        const allMarkers = [];

        icons.forEach(icon => {
            if (!icon.type || !layers[icon.type]) return;

            const marker = createMarker(icon.lng, icon.lat, icon.type, icon.data || icon);
            layers[icon.type].markers.push(marker);
            allMarkers.push(marker);
        });

        // 批量添加到聚类
        clusterer.addMarkers(allMarkers);
        updateStats();

        console.log('[Map] 批量添加图标:', allMarkers.length);
    }

    /**
     * 清除所有图标
     */
    function clearAllIcons() {
        if (!clusterer) return;

        Object.keys(layers).forEach(type => {
            if (layers[type].markers.length > 0) {
                clusterer.removeMarkers(layers[type].markers);
                layers[type].markers = [];
            }
        });

        updateStats();
        console.log('[Map] 已清除所有图标');
    }

    /**
     * 添加航迹线
     */
    function addTrack(points, color, unitId) {
        if (!map || !points || points.length < 2) return;

        const polyline = new AMap.Polyline({
            path: points.map(p => new AMap.LngLat(p.lng, p.lat)),
            strokeColor: color || '#00FFFF',
            strokeWeight: 2,
            strokeOpacity: 0.8,
            showDir: true,
            dirColor: color || '#00FFFF'
        });

        // 添加方向箭头
        const start = points[0];
        const end = points[points.length - 1];

        trackLayer.addLayer(polyline);
        console.log('[Map] 添加航迹线，单位:', unitId);

        return polyline;
    }

    /**
     * 添加作战半径
     */
    function addCombatRadius(lng, lat, radiusKm, color) {
        if (!map) return;

        const circle = new AMap.Circle({
            center: new AMap.LngLat(lng, lat),
            radius: radiusKm * 1000, // 转换为米
            strokeColor: color || '#FF4444',
            strokeWeight: 2,
            fillColor: color || '#FF4444',
            fillOpacity: 0.15
        });

        radiusLayer.addLayer(circle);
        console.log('[Map] 添加作战半径:', radiusKm, 'km');

        return circle;
    }

    /**
     * 添加热力图数据
     */
    function addHeatmap(data) {
        if (!map || !heatmapLayer || !data || !Array.isArray(data)) return;

        const heatmapData = data.map(item => ({
            lng: item.lng,
            lat: item.lat,
            count: item.count || 1
        }));

        heatmapLayer.setDataSet({
            data: heatmapData,
            max: 100
        });

        heatmapLayer.set({
            radius: 30,
            opacity: [0, 0.8]
        });

        console.log('[Map] 添加热力图数据:', heatmapData.length);
    }

    /**
     * 设置热力图可见性
     */
    function setHeatmapVisible(visible) {
        if (!map || !heatmapLayer) return;

        if (visible) {
            map.addLayer(heatmapLayer);
        } else {
            map.removeLayer(heatmapLayer);
        }

        console.log('[Map] 热力图可见性:', visible);
    }

    /**
     * 设置航迹线可见性
     */
    function setTracksVisible(visible) {
        if (!map || !trackLayer) return;

        if (visible) {
            map.addLayer(trackLayer);
        } else {
            map.removeLayer(trackLayer);
        }

        console.log('[Map] 航迹线可见性:', visible);
    }

    /**
     * 设置作战半径可见性
     */
    function setRadiusVisible(visible) {
        if (!map || !radiusLayer) return;

        if (visible) {
            map.addLayer(radiusLayer);
        } else {
            map.removeLayer(radiusLayer);
        }

        console.log('[Map] 作战半径可见性:', visible);
    }

    /**
     * 移动到指定位置
     */
    function panTo(lng, lat, zoom) {
        if (!map) return;

        map.panTo(new AMap.LngLat(lng, lat));
        if (zoom) {
            map.setZoom(zoom);
        }

        console.log('[Map] 移动到:', lng, lat, '缩放级别:', zoom || map.getZoom());
    }

    /**
     * 更新统计面板
     */
    function updateStats() {
        let total = 0;

        Object.keys(layers).forEach(type => {
            const count = layers[type].markers.length;
            const statEl = document.getElementById('stat-' + type);
            if (statEl) {
                statEl.textContent = count;
            }
            total += count;
        });

        const totalEl = document.getElementById('stat-total');
        if (totalEl) {
            totalEl.textContent = total;
        }
    }

    /**
     * 获取当前地图实例（供外部调用）
     */
    function getMapInstance() {
        return map;
    }

    /**
     * 从 Python 调用：添加图标
     */
    window.mapAPI = {
        addIcon: addIcon,
        addIconsBatch: addIconsBatch,
        setLayerVisible: setLayerVisible,
        addTrack: addTrack,
        addCombatRadius: addCombatRadius,
        addHeatmap: addHeatmap,
        setHeatmapVisible: setHeatmapVisible,
        clearAllIcons: clearAllIcons,
        panTo: panTo,
        getMapInstance: getMapInstance,
        updateStats: updateStats
    };

    // 页面加载完成后初始化地图
    window.onload = function() {
        if (typeof AMap !== 'undefined') {
            initMap();
        } else {
            console.error('[Map] 高德地图 JSAPI 未加载');
        }
    };

    // 如果已经加载
    if (typeof AMap !== 'undefined') {
        initMap();
    }

})();
