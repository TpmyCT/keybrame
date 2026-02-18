class KeybrameAdmin {
    constructor() {
        this.keybindings = [];
        this.images = [];
        this.settings = {};
        this.editingId = null;
        this.selectedKeys = [];
        this.saveSettingsTimeout = null; // debounce timer for auto-save
        this.pressedKeys = new Set();
        this.isRecording = false;
        this.recordingKeys = new Set();
        this.recordKeyHandler = null;
        this.serverStopping = false;
        this.serverUpdating = false;

        this.init();
    }

    async init() {
        await this.loadSettings();
        await this.loadImages();
        await this.loadKeybindings();
        this.loadVersionBadge();

        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupImageUpload();
        this.setupImagePicker();
        this.setupSocketIO();

        this.refreshPreviewIframe();
    }

    async loadVersionBadge() {
        try {
            const res = await fetch('/api/version');
            const data = await res.json();
            const badge = document.getElementById('version-badge');
            if (badge) badge.textContent = 'v' + data.version;
        } catch (e) {}
    }

    refreshPreviewIframe() {
        const previewIframe = document.getElementById('preview-iframe');
        if (previewIframe) {
            // Force reload with timestamp to bypass cache
            previewIframe.src = `/?t=${Date.now()}`;
        }
    }

    setupSocketIO() {
        this.socket = io();

        this.socket.on('connect', () => {
            if (this.serverUpdating) {
                window.location.reload();
            }
        });

        this.socket.on('disconnect', () => {
            if (this.serverUpdating) {
                document.getElementById('server-updating-overlay').style.display = 'flex';
            } else if (this.serverStopping) {
                document.getElementById('server-offline-overlay').style.display = 'flex';
            }
        });

        this.socket.on('key_pressed', (data) => {
            this.pressedKeys.add(data.key);
            this.updatePressedKeysDisplay();
        });

        this.socket.on('key_released', (data) => {
            this.pressedKeys.delete(data.key);
            this.updatePressedKeysDisplay();
        });

        this.socket.on('update_available', (data) => this.showUpdateBanner(data));
        this.socket.on('update_progress', (data) => this.onUpdateProgress(data.progress));
        this.socket.on('update_installing', () => {
            this.serverUpdating = true;
            document.getElementById('server-updating-overlay').style.display = 'flex';
        });
        this.socket.on('update_error', (data) => {
            this.showNotification('Error en la actualización: ' + data.error, 'error');
        });
    }

    showUpdateBanner(data) {
        if (document.getElementById('update-banner')) return;

        const banner = document.createElement('div');
        banner.id = 'update-banner';
        banner.className = 'update-banner';
        banner.innerHTML = `
            <div class="update-banner-content">
                <i class="fas fa-arrow-circle-up"></i>
                <span>Nueva versión disponible: <strong>v${data.version}</strong></span>
                <button class="btn btn-primary btn-sm" id="btn-install-update">
                    <i class="fas fa-download"></i> Actualizar ahora
                </button>
                <button class="btn btn-secondary btn-sm" id="btn-dismiss-update">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.querySelector('.header').after(banner);

        document.getElementById('btn-install-update').addEventListener('click', () => this.installUpdate(data));
        document.getElementById('btn-dismiss-update').addEventListener('click', () => banner.remove());
    }

    async installUpdate(data) {
        const confirmed = await this.showConfirm(
            `Se descargará e instalará la versión v${data.version}. El programa se cerrará y se reiniciará automáticamente.`,
            'Actualizar Keybrame'
        );
        if (!confirmed) return;

        const btn = document.getElementById('btn-install-update');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Descargando...';
            btn.disabled = true;
        }

        await fetch('/api/server/update', { method: 'POST' });
    }

    onUpdateProgress(progress) {
        const btn = document.getElementById('btn-install-update');
        if (btn) {
            btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${progress}%`;
        }
    }

    updatePressedKeysDisplay() {
        const container = document.getElementById('pressed-keys-display');

        if (this.pressedKeys.size === 0) {
            container.innerHTML = '<span class="no-keys-message">Ninguna tecla presionada</span>';
            return;
        }

        const keysArray = Array.from(this.pressedKeys);
        container.innerHTML = keysArray.map(key => `
            <span class="pressed-key-chip">
                <i class="fas fa-hand-pointer"></i>
                ${this.formatKeyName(key)}
            </span>
        `).join('');
    }

    // ==================== DATA LOADING ====================

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            this.settings = await response.json();

            document.getElementById('input-port').value = this.settings.port || 5000;
            document.getElementById('input-default-image').value = this.removeImagesPrefix(this.settings.default_image) || '';
            this.updateDefaultImagePreview();

            const port = this.settings.port || 5000;
            document.getElementById('obs-url-display').value = `http://localhost:${port}/`;

        } catch (error) {
            this.showNotification('Error al cargar configuración: ' + error.message, 'error');
        }
    }

    async loadKeybindings() {
        try {
            const response = await fetch('/api/keybindings');
            this.keybindings = await response.json();
            this.renderKeybindings();

        } catch (error) {
            this.showNotification('Error al cargar atajos: ' + error.message, 'error');
        }
    }

    async loadImages() {
        try {
            const response = await fetch('/api/images');
            this.images = await response.json();
            this.renderImageGallery();

        } catch (error) {
            this.showNotification('Error al cargar imágenes: ' + error.message, 'error');
        }
    }

    // ==================== RENDERING ====================

    renderKeybindings() {
        const container = document.getElementById('keybindings-list');
        const emptyState = document.getElementById('empty-state');

        if (this.keybindings.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        container.innerHTML = this.keybindings.map(kb => this.createKeybindingHTML(kb)).join('');
    }

    createKeybindingHTML(kb) {
        const keysHTML = kb.keys.map(key => `<span class="key-chip">${this.formatKeyName(key)}</span>`).join('');

        const typeText = kb.type === 'toggle' ? 'Alternar' : 'Mantener';
        const typeIcon = kb.type === 'toggle' ? '<i class="fas fa-sync-alt"></i>' : '<i class="fas fa-hand-paper"></i>';

        const transitionBadges = [];
        if (kb.transition_in) transitionBadges.push('<span class="keybinding-badge"><i class="fas fa-sign-in-alt"></i> Entrada</span>');
        if (kb.transition_out) transitionBadges.push('<span class="keybinding-badge"><i class="fas fa-sign-out-alt"></i> Salida</span>');

        return `
            <div class="keybinding-item" data-id="${kb.id}" draggable="true">
                <div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>
                <div class="keybinding-content">
                    <div class="keybinding-header">
                        <div class="keybinding-keys">${keysHTML}</div>
                        <div class="keybinding-info">
                            <span class="keybinding-type-badge">${typeIcon} ${typeText}</span>
                            ${transitionBadges.join('')}
                        </div>
                    </div>
                    <div class="keybinding-meta">
                        <span><i class="fas fa-image"></i> ${this.removeImagesPrefix(kb.image)}</span>
                        ${kb.description ? `<span class="keybinding-desc">• ${kb.description}</span>` : ''}
                    </div>
                </div>
                <div class="keybinding-actions">
                    <button class="btn-icon edit" onclick="admin.editKeybinding(${kb.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon delete" onclick="admin.deleteKeybinding(${kb.id})" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    renderModalKeyChips() {
        const container = document.getElementById('modal-key-chips');

        let html = this.selectedKeys.map(key => `
            <span class="key-chip removable" onclick="admin.removeModalKey('${key}')" title="Click para quitar">
                ${this.formatKeyName(key)}
            </span>
        `).join('');

        // Show keys being recorded in a different style
        if (this.isRecording && this.recordingKeys.size > 0) {
            const recordingHtml = Array.from(this.recordingKeys).map(key => `
                <span class="key-chip recording-chip">
                    ${this.formatKeyName(key)}
                </span>
            `).join('');
            html += recordingHtml;
        }

        container.innerHTML = html || '<span style="color: var(--text-muted); font-size: 0.9rem;">Ninguna tecla seleccionada</span>';
    }

    updateDefaultImagePreview() {
        const imagePath = document.getElementById('input-default-image').value;
        const previewImg = document.getElementById('default-image-preview-img');
        const placeholder = document.getElementById('default-image-placeholder');

        if (imagePath) {
            const fullPath = this.addImagesPrefix(imagePath);
            previewImg.src = fullPath;
            previewImg.style.display = 'block';
            placeholder.style.display = 'none';
        } else {
            previewImg.style.display = 'none';
            placeholder.style.display = 'flex';
        }
    }

    populateImageSelects() {
        const selects = [
            'select-default-image',
            'modal-select-image',
            'modal-select-transition-in',
            'modal-select-transition-out'
        ];

        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            const currentValue = select.value;

            const emptyOption = select.querySelector('option[value=""]');
            select.innerHTML = '';
            if (emptyOption) {
                select.appendChild(emptyOption);
            }

            this.images.forEach(img => {
                const option = document.createElement('option');
                option.value = img.path;
                option.textContent = `${this.removeImagesPrefix(img.filename)} ${img.duration ? `(${img.duration}ms)` : ''}`;
                select.appendChild(option);
            });

            if (currentValue) {
                select.value = currentValue;
            }
        });
    }

    formatKeyName(key) {
        const keyMap = {
            'mouse_left': 'Mouse L',
            'mouse_right': 'Mouse R',
            'mouse_middle': 'Mouse M',
            'scroll_up': 'Scroll ↑',
            'scroll_down': 'Scroll ↓',
            'space': 'Space',
            'enter': 'Enter',
            'backspace': 'Backspace',
            'ctrl': 'Ctrl',
            'shift': 'Shift',
            'alt': 'Alt',
            'cmd': 'Cmd'
        };

        return keyMap[key] || key.toUpperCase();
    }

    removeImagesPrefix(path) {
        if (!path) return '';
        return path.replace(/^assets\//, '');
    }

    addImagesPrefix(path) {
        if (!path) return '';
        if (path.startsWith('assets/')) return path;
        return 'assets/' + path;
    }

    renderImageGallery() {
        const grid = document.getElementById('images-grid');

        if (this.images.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No hay imágenes subidas aún</p>';
            return;
        }

        grid.innerHTML = this.images.map(img => `
            <div class="image-item" data-filename="${img.filename}">
                <img src="/${img.path}" alt="${this.removeImagesPrefix(img.filename)}" loading="lazy">
                <div class="image-overlay">
                    <div class="image-filename">${this.removeImagesPrefix(img.filename)}</div>
                    <div class="image-actions">
                        <button class="btn-icon delete" onclick="admin.deleteImage('${img.filename}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    async uploadImages(files) {
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/images/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || 'Upload failed');
                }

                this.showNotification(`Subido: ${this.removeImagesPrefix(result.filename)}`, 'success');

            } catch (error) {
                this.showNotification(`Error al subir ${file.name}: ${error.message}`, 'error');
            }
        }

        await this.loadImages();

        // If image picker is open, refresh it
        const imagePickerModal = document.getElementById('image-picker-modal');
        if (imagePickerModal && imagePickerModal.style.display === 'flex') {
            this.renderImagePicker();
        }
    }

    async deleteImage(filename) {
        const confirmed = await this.showConfirm(
            `¿Estás seguro de que quieres eliminar "${filename}"?`,
            'Eliminar imagen'
        );

        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch(`/api/images/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.error || 'Delete failed');
            }

            this.showNotification(`Eliminado: ${this.removeImagesPrefix(filename)}`, 'success');
            await this.loadImages();

        } catch (error) {
            this.showNotification(`Error al eliminar imagen: ${error.message}`, 'error');
        }
    }

    setupImageUpload() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('upload-file-input');

        uploadArea.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadImages(Array.from(e.target.files));
                fileInput.value = '';
            }
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');

            const files = Array.from(e.dataTransfer.files).filter(file =>
                file.type.startsWith('image/')
            );

            if (files.length > 0) {
                this.uploadImages(files);
            }
        });
    }

    setupImagePicker() {
        this.imagePickerTarget = null; // 'main', 'transition-in', 'transition-out'
    }

    openImagePicker(target) {
        this.imagePickerTarget = target;
        this.renderImagePicker();
        document.getElementById('image-picker-modal').style.display = 'flex';
    }

    closeImagePicker() {
        document.getElementById('image-picker-modal').style.display = 'none';
        this.imagePickerTarget = null;
    }

    renderImagePicker() {
        const grid = document.getElementById('image-picker-grid');

        if (this.images.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No hay imágenes disponibles. ¡Sube algunas primero!</p>';
            return;
        }

        let currentValue = '';
        if (this.imagePickerTarget === 'main') {
            currentValue = document.getElementById('modal-input-image').value;
        } else if (this.imagePickerTarget === 'transition-in') {
            currentValue = document.getElementById('modal-input-transition-in').value;
        } else if (this.imagePickerTarget === 'transition-out') {
            currentValue = document.getElementById('modal-input-transition-out').value;
        } else if (this.imagePickerTarget === 'default') {
            currentValue = document.getElementById('input-default-image').value;
        }

        grid.innerHTML = this.images.map(img => {
            const displayName = this.removeImagesPrefix(img.filename);
            const isSelected = this.removeImagesPrefix(img.path) === currentValue;
            return `
                <div class="image-picker-item ${isSelected ? 'selected' : ''}"
                     onclick="admin.selectImage('${img.path}')"
                     title="${displayName}">
                    <img src="/${img.path}" alt="${displayName}" loading="lazy">
                </div>
            `;
        }).join('');
    }

    selectImage(imagePath) {
        let inputId, previewId;

        if (this.imagePickerTarget === 'main') {
            inputId = 'modal-input-image';
            previewId = 'modal-image-preview';
        } else if (this.imagePickerTarget === 'transition-in') {
            inputId = 'modal-input-transition-in';
            previewId = 'modal-transition-in-preview';
        } else if (this.imagePickerTarget === 'transition-out') {
            inputId = 'modal-input-transition-out';
            previewId = 'modal-transition-out-preview';
        } else if (this.imagePickerTarget === 'default') {
            inputId = 'input-default-image';
            previewId = null;
        }

        if (inputId) {
            const displayPath = this.removeImagesPrefix(imagePath);
            document.getElementById(inputId).value = displayPath;
            if (previewId) {
                this.showImagePreview(imagePath, previewId);
            }
            if (this.imagePickerTarget === 'default') {
                this.updateDefaultImagePreview();
                this.saveSettings();
            }
        }

        this.closeImagePicker();
    }

    // ==================== EVENT LISTENERS ====================

    setupEventListeners() {
        document.getElementById('btn-reload').addEventListener('click', () => this.reloadConfig());
        document.getElementById('btn-export').addEventListener('click', () => this.exportConfig());

        document.getElementById('btn-import').addEventListener('click', () => {
            document.getElementById('import-file-input').click();
        });
        document.getElementById('import-file-input').addEventListener('change', (e) => {
            if (e.target.files[0]) {
                this.importConfig(e.target.files[0]);
            }
        });

        document.getElementById('btn-restart').addEventListener('click', () => this.restartServer());
        document.getElementById('btn-shutdown').addEventListener('click', () => this.shutdownServer());
        document.getElementById('btn-copy-obs-url').addEventListener('click', () => this.copyObsUrl());

        document.getElementById('btn-select-default-image').addEventListener('click', () => {
            this.openImagePicker('default');
        });
        document.getElementById('input-default-image').addEventListener('click', () => {
            this.openImagePicker('default');
        });

        // Auto-save port with 2s debounce
        document.getElementById('input-port').addEventListener('input', () => {
            clearTimeout(this.saveSettingsTimeout);
            this.saveSettingsTimeout = setTimeout(() => this.saveSettings(), 2000);
        });

        document.getElementById('btn-save-settings').addEventListener('click', () => this.saveSettings(false));
        document.getElementById('btn-add-keybinding').addEventListener('click', () => this.openModal());

        document.getElementById('modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('modal-cancel').addEventListener('click', () => this.closeModal());
        document.getElementById('keybinding-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveKeybinding();
        });

        document.getElementById('btn-record-keys').addEventListener('click', () => this.toggleRecording());
        document.getElementById('btn-clear-keys').addEventListener('click', () => this.clearSelectedKeys());

        document.querySelectorAll('.type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const button = e.currentTarget;
                const type = button.dataset.type;
                document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
                button.classList.add('active');
                document.getElementById('modal-input-type').value = type;
            });
        });

        document.getElementById('modal-checkbox-transition-in').addEventListener('change', (e) => {
            document.getElementById('modal-transition-in-fields').style.display = e.target.checked ? 'block' : 'none';
        });
        document.getElementById('modal-checkbox-transition-out').addEventListener('change', (e) => {
            document.getElementById('modal-transition-out-fields').style.display = e.target.checked ? 'block' : 'none';
        });

        document.getElementById('btn-select-image').addEventListener('click', () => this.openImagePicker('main'));
        document.getElementById('modal-input-image').addEventListener('click', () => this.openImagePicker('main'));
        document.getElementById('btn-select-transition-in').addEventListener('click', () => this.openImagePicker('transition-in'));
        document.getElementById('modal-input-transition-in').addEventListener('click', () => this.openImagePicker('transition-in'));
        document.getElementById('btn-select-transition-out').addEventListener('click', () => this.openImagePicker('transition-out'));
        document.getElementById('modal-input-transition-out').addEventListener('click', () => this.openImagePicker('transition-out'));

        document.getElementById('image-picker-close').addEventListener('click', () => this.closeImagePicker());
        document.getElementById('btn-upload-from-picker').addEventListener('click', () => {
            document.getElementById('upload-file-input').click();
        });

        // Close modals on backdrop click
        const mainBackdrop = document.getElementById('modal')?.querySelector('.modal-backdrop');
        if (mainBackdrop) mainBackdrop.addEventListener('click', () => this.closeModal());

        const imagePickerBackdrop = document.getElementById('image-picker-modal')?.querySelector('.modal-backdrop');
        if (imagePickerBackdrop) imagePickerBackdrop.addEventListener('click', () => this.closeImagePicker());
    }

    // ==================== DRAG & DROP ====================

    setupDragAndDrop() {
        const container = document.getElementById('keybindings-list');

        container.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('keybinding-item')) {
                e.target.classList.add('dragging');
            }
        });

        container.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('keybinding-item')) {
                e.target.classList.remove('dragging');
                this.saveOrder();
            }
        });

        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = this.getDragAfterElement(container, e.clientY);
            const dragging = document.querySelector('.dragging');

            if (afterElement == null) {
                container.appendChild(dragging);
            } else {
                container.insertBefore(dragging, afterElement);
            }
        });
    }

    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.keybinding-item:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    async saveOrder() {
        const items = document.querySelectorAll('.keybinding-item');
        const order = Array.from(items).map(item => parseInt(item.dataset.id));

        try {
            const response = await fetch('/api/keybindings/reorder', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order })
            });

            if (!response.ok) throw new Error('Failed to save order');

            this.showNotification('Orden guardado exitosamente', 'success');

        } catch (error) {
            this.showNotification('Error al guardar orden: ' + error.message, 'error');
        }
    }

    // ==================== CRUD OPERATIONS ====================

    async saveSettings(silent = true) {
        try {
            const portValue = parseInt(document.getElementById('input-port').value);

            if (isNaN(portValue) || portValue < 1 || portValue > 65535) {
                this.showNotification('Puerto inválido. Debe ser un número entre 1 y 65535.', 'error');
                return;
            }

            const data = {
                port: portValue,
                default_image: this.addImagesPrefix(document.getElementById('input-default-image').value)
            };

            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const result = await response.json().catch(() => ({ error: 'Error desconocido' }));
                throw new Error(result.error || 'Failed to save settings');
            }

            const result = await response.json();

            if (!silent) {
                this.showNotification('Configuración guardada exitosamente', 'success');
            }

            await this.reloadConfig();
            this.updateDefaultImagePreview();

            const previewIframe = document.getElementById('preview-iframe');
            if (previewIframe) {
                previewIframe.src = previewIframe.src;
            }

            if (result.reloadRequired) {
                await this.restartAndRedirect(data.port);
            }

        } catch (error) {
            this.showNotification('Error al guardar configuración: ' + error.message, 'error');
        }
    }

    async restartAndRedirect(newPort) {
        this.showNotification('Reiniciando servidor con nuevo puerto...', 'info');

        try {
            await fetch('/api/server/restart', { method: 'POST' });
            await new Promise(resolve => setTimeout(resolve, 4000));
            window.location.href = `http://localhost:${newPort}/admin?t=${Date.now()}`;
        } catch (error) {
            // Server is probably already restarting, wait and redirect anyway
            await new Promise(resolve => setTimeout(resolve, 4000));
            window.location.href = `http://localhost:${newPort}/admin?t=${Date.now()}`;
        }
    }

    openModal(keybinding = null) {
        this.editingId = keybinding ? keybinding.id : null;
        this.selectedKeys = keybinding ? [...keybinding.keys] : [];

        document.getElementById('keybinding-form').reset();
        this.renderModalKeyChips();

        document.getElementById('modal-title').textContent = keybinding ? 'Editar Atajo' : 'Agregar Atajo';

        if (keybinding) {
            const bindingType = keybinding.type || 'toggle';
            document.getElementById('modal-input-type').value = bindingType;

            document.querySelectorAll('.type-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.type === bindingType);
            });

            document.getElementById('modal-input-image').value = this.removeImagesPrefix(keybinding.image);
            document.getElementById('modal-input-description').value = keybinding.description || '';

            this.showImagePreview(keybinding.image, 'modal-image-preview');

            if (keybinding.transition_in) {
                document.getElementById('modal-checkbox-transition-in').checked = true;
                document.getElementById('modal-transition-in-fields').style.display = 'block';
                document.getElementById('modal-input-transition-in').value = this.removeImagesPrefix(keybinding.transition_in.image);
                document.getElementById('modal-input-duration-in').value = keybinding.transition_in.duration || '';
                this.showImagePreview(keybinding.transition_in.image, 'modal-transition-in-preview');
            } else {
                document.getElementById('modal-checkbox-transition-in').checked = false;
                document.getElementById('modal-transition-in-fields').style.display = 'none';
            }

            if (keybinding.transition_out) {
                document.getElementById('modal-checkbox-transition-out').checked = true;
                document.getElementById('modal-transition-out-fields').style.display = 'block';
                document.getElementById('modal-input-transition-out').value = this.removeImagesPrefix(keybinding.transition_out.image);
                document.getElementById('modal-input-duration-out').value = keybinding.transition_out.duration || '';
                this.showImagePreview(keybinding.transition_out.image, 'modal-transition-out-preview');
            } else {
                document.getElementById('modal-checkbox-transition-out').checked = false;
                document.getElementById('modal-transition-out-fields').style.display = 'none';
            }
        } else {
            document.getElementById('modal-image-preview').classList.remove('show');
            document.getElementById('modal-transition-in-preview').classList.remove('show');
            document.getElementById('modal-transition-out-preview').classList.remove('show');

            document.getElementById('modal-input-type').value = 'toggle';
            document.querySelectorAll('.type-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.type === 'toggle');
            });
        }

        document.getElementById('modal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('modal').style.display = 'none';
        this.editingId = null;
        this.selectedKeys = [];
    }

    async saveKeybinding() {
        if (this.selectedKeys.length === 0) {
            this.showNotification('Por favor selecciona al menos una tecla', 'error');
            return;
        }

        const data = {
            keys: this.selectedKeys,
            type: document.getElementById('modal-input-type').value,
            image: this.addImagesPrefix(document.getElementById('modal-input-image').value),
            description: document.getElementById('modal-input-description').value
        };

        if (document.getElementById('modal-checkbox-transition-in').checked) {
            const transImage = document.getElementById('modal-input-transition-in').value;
            const duration = document.getElementById('modal-input-duration-in').value;
            if (transImage) {
                data.transition_in = { image: this.addImagesPrefix(transImage) };
                if (duration) data.transition_in.duration = parseInt(duration);
            }
        } else {
            data.transition_in = null;
        }

        if (document.getElementById('modal-checkbox-transition-out').checked) {
            const transImage = document.getElementById('modal-input-transition-out').value;
            const duration = document.getElementById('modal-input-duration-out').value;
            if (transImage) {
                data.transition_out = { image: this.addImagesPrefix(transImage) };
                if (duration) data.transition_out.duration = parseInt(duration);
            }
        } else {
            data.transition_out = null;
        }

        try {
            const url = this.editingId ? `/api/keybindings/${this.editingId}` : '/api/keybindings';
            const method = this.editingId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                const errorMsg = result.details ? result.details.join(', ') : result.error;
                throw new Error(errorMsg);
            }

            this.showNotification(
                this.editingId ? 'Keybinding updated successfully' : 'Keybinding created successfully',
                'success'
            );

            this.closeModal();
            await this.loadKeybindings();
            await this.reloadConfig();

        } catch (error) {
            this.showNotification('Error al guardar atajo: ' + error.message, 'error');
        }
    }

    editKeybinding(id) {
        const keybinding = this.keybindings.find(kb => kb.id === id);
        if (keybinding) {
            this.openModal(keybinding);
        }
    }

    async deleteKeybinding(id) {
        const confirmed = await this.showConfirm(
            '¿Estás seguro de que quieres eliminar este atajo?',
            'Eliminar atajo'
        );

        if (!confirmed) return;

        try {
            const response = await fetch(`/api/keybindings/${id}`, { method: 'DELETE' });

            if (!response.ok) throw new Error('Failed to delete keybinding');

            this.showNotification('Atajo eliminado exitosamente', 'success');
            await this.loadKeybindings();
            await this.reloadConfig();

        } catch (error) {
            this.showNotification('Error al eliminar atajo: ' + error.message, 'error');
        }
    }

    // ==================== HELPERS ====================

    removeModalKey(key) {
        this.selectedKeys = this.selectedKeys.filter(k => k !== key);
        this.renderModalKeyChips();
    }

    clearSelectedKeys() {
        this.selectedKeys = [];
        this.renderModalKeyChips();
    }

    toggleRecording() {
        const btn = document.getElementById('btn-record-keys');
        const btnText = document.getElementById('record-btn-text');
        const hint = document.getElementById('record-hint');

        if (this.isRecording) {
            this.stopRecording();
            btn.classList.remove('recording');
            btnText.textContent = 'Grabar Teclas';
            hint.style.display = 'none';
        } else {
            this.startRecording();
            btn.classList.add('recording');
            btnText.textContent = 'Detener Grabación';
            hint.style.display = 'block';
        }
    }

    startRecording() {
        this.isRecording = true;
        this.recordingKeys = new Set();

        this.recordKeyHandler = (data) => {
            if (!this.isRecording) return;

            const key = data.key;
            if (['<unknown>', '?', 'unknown'].includes(key)) return;

            this.recordingKeys.add(key);
            this.renderModalKeyChips();
        };

        if (this.socket) {
            this.socket.on('key_pressed', this.recordKeyHandler);
        } else {
            this.showNotification('Error: Recarga la página', 'error');
        }
    }

    stopRecording() {
        this.isRecording = false;

        if (this.socket && this.recordKeyHandler) {
            this.socket.off('key_pressed', this.recordKeyHandler);
            this.recordKeyHandler = null;
        }

        this.recordingKeys.forEach(key => {
            if (!this.selectedKeys.includes(key)) {
                this.selectedKeys.push(key);
            }
        });

        this.recordingKeys.clear();
        this.renderModalKeyChips();
    }

    showImagePreview(imagePath, previewId) {
        const preview = document.getElementById(previewId);
        if (!imagePath) {
            preview.classList.remove('show');
            return;
        }

        preview.innerHTML = `<img src="/${imagePath}" alt="Preview">`;
        preview.classList.add('show');
    }

    async reloadConfig() {
        try {
            const response = await fetch('/api/reload', { method: 'POST' });

            if (!response.ok) {
                const result = await response.json().catch(() => ({ error: 'Error desconocido' }));
                throw new Error(result.error || 'Failed to reload config');
            }

            this.showNotification('Configuración recargada exitosamente', 'success');

        } catch (error) {
            console.error('Error reloading config:', error);
            this.showNotification('Error al recargar configuración: ' + error.message, 'error');
        }
    }

    async exportConfig() {
        try {
            const response = await fetch('/api/export');
            const config = await response.json();

            const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'keybrame-config.json';
            a.click();
            URL.revokeObjectURL(url);

            this.showNotification('Configuración exportada exitosamente', 'success');

        } catch (error) {
            this.showNotification('Error al exportar configuración: ' + error.message, 'error');
        }
    }

    async importConfig(file) {
        try {
            const text = await file.text();
            const config = JSON.parse(text);

            const response = await fetch('/api/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (!response.ok) {
                const errorMsg = result.details ? result.details.join(', ') : result.error;
                throw new Error(errorMsg);
            }

            this.showNotification('Configuración importada exitosamente', 'success');

            await this.loadSettings();
            await this.loadKeybindings();

        } catch (error) {
            this.showNotification('Error al importar configuración: ' + error.message, 'error');
        }
    }

    async restartServer() {
        const confirmed = await this.showConfirm(
            '¿Estás seguro de que quieres reiniciar el servidor?',
            'Reiniciar servidor'
        );

        if (!confirmed) return;

        try {
            const response = await fetch('/api/server/restart', { method: 'POST' });

            if (response.ok) {
                this.showNotification('Servidor reiniciando...', 'success');
                setTimeout(() => window.location.reload(), 2000);
            } else {
                throw new Error('Error al reiniciar servidor');
            }
        } catch (error) {
            this.showNotification('Error al reiniciar servidor: ' + error.message, 'error');
        }
    }

    async shutdownServer() {
        const confirmed = await this.showConfirm(
            '¿Estás seguro de que quieres apagar el servidor?',
            'Apagar servidor'
        );

        if (!confirmed) return;

        try {
            const response = await fetch('/api/server/shutdown', { method: 'POST' });

            if (response.ok) {
                this.serverStopping = true;
                this.showNotification('Servidor apagándose...', 'success');
            } else {
                throw new Error('Error al apagar servidor');
            }
        } catch (error) {
            this.showNotification('Error al apagar servidor: ' + error.message, 'error');
        }
    }

    copyObsUrl() {
        const urlField = document.getElementById('obs-url-display');
        urlField.select();
        urlField.setSelectionRange(0, 99999); // mobile support

        try {
            navigator.clipboard.writeText(urlField.value).then(() => {
                this.showNotification('URL copiada al portapapeles', 'success');
            }).catch(() => {
                // Fallback for older browsers
                document.execCommand('copy');
                this.showNotification('URL copiada al portapapeles', 'success');
            });
        } catch (error) {
            this.showNotification('Error al copiar URL', 'error');
        }
    }

    showConfirm(message, title = 'Confirmar acción') {
        return new Promise((resolve) => {
            const modal = document.getElementById('confirm-modal');
            const titleEl = document.getElementById('confirm-modal-title');
            const messageEl = document.getElementById('confirm-modal-message');
            const confirmBtn = document.getElementById('confirm-modal-confirm');
            const cancelBtn = document.getElementById('confirm-modal-cancel');

            titleEl.textContent = title;
            messageEl.textContent = message;
            modal.style.display = 'flex';

            const handleConfirm = () => { cleanup(); resolve(true); };
            const handleCancel = () => { cleanup(); resolve(false); };
            const handleEscape = (e) => { if (e.key === 'Escape') handleCancel(); };

            const cleanup = () => {
                modal.style.display = 'none';
                confirmBtn.removeEventListener('click', handleConfirm);
                cancelBtn.removeEventListener('click', handleCancel);
                document.removeEventListener('keydown', handleEscape);
            };

            confirmBtn.addEventListener('click', handleConfirm);
            cancelBtn.addEventListener('click', handleCancel);
            document.addEventListener('keydown', handleEscape);

            cancelBtn.focus(); // safer default focus
        });
    }

    showNotification(message, type = 'success') {
        const container = document.getElementById('toast-container');

        // Max 3 toasts at once
        const toasts = container.querySelectorAll('.toast');
        if (toasts.length >= 3) {
            toasts[0].remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-times-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.success}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        const autoClose = setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);

        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(autoClose);
        });
    }

}

const admin = new KeybrameAdmin();
