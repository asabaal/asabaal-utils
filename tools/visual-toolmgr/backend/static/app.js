// Visual Tool Manager Frontend JavaScript

class VisualToolManager {
    constructor() {
        this.currentDirectory = null;
        this.foundTools = [];
        this.selectedDirectory = null;
        
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupEventListeners();
        this.loadCommonDirectories();
        this.loadInstalledTools();
    }

    // Tab Management
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update active tab button
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update active tab content
                tabContents.forEach(content => content.classList.remove('active'));
                document.getElementById(tabName).classList.add('active');
                
                // Load content for specific tabs
                if (tabName === 'installed') {
                    this.loadInstalledTools();
                }
            });
        });
    }

    setupEventListeners() {
        // Browse and scan buttons
        document.getElementById('browse-custom').addEventListener('click', () => {
            const path = document.getElementById('custom-path').value || '/home';
            this.browseDirectory(path);
        });

        document.getElementById('scan-custom').addEventListener('click', () => {
            const path = document.getElementById('custom-path').value;
            if (path) {
                this.scanDirectory(path);
            } else {
                this.showOutput('Please enter a directory path', 'error');
            }
        });

        document.getElementById('scan-current').addEventListener('click', () => {
            if (this.currentDirectory) {
                this.scanDirectory(this.currentDirectory);
            }
        });

        // Install actions
        document.getElementById('install-all').addEventListener('click', () => {
            this.installAllTools();
        });

        // Installed tools actions
        document.getElementById('refresh-installed').addEventListener('click', () => {
            this.loadInstalledTools();
        });

        // Health check actions
        document.getElementById('run-health-check').addEventListener('click', () => {
            this.runHealthCheck();
        });

        document.getElementById('setup-toolmgr').addEventListener('click', () => {
            this.setupToolManager();
        });

        // Enter key in custom path input
        document.getElementById('custom-path').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const path = e.target.value;
                if (path) {
                    this.scanDirectory(path);
                }
            }
        });
    }

    // API Calls
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`/api/${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showOutput(`API Error: ${error.message}`, 'error');
            throw error;
        }
    }

    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showOutput(message, type = 'info') {
        const output = document.getElementById('output');
        const timestamp = new Date().toLocaleTimeString();
        const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
        
        output.textContent += `[${timestamp}] ${prefix} ${message}\n`;
        output.scrollTop = output.scrollHeight;
    }

    // Directory Management
    async loadCommonDirectories() {
        try {
            const data = await this.apiCall('directories');
            this.renderCommonDirectories(data.directories);
        } catch (error) {
            this.showOutput('Failed to load common directories', 'error');
        }
    }

    renderCommonDirectories(directories) {
        const container = document.getElementById('common-directories');
        container.innerHTML = '';

        directories.forEach(dir => {
            const dirElement = document.createElement('div');
            dirElement.className = `dir-item ${!dir.exists ? 'not-exists' : ''}`;
            
            dirElement.innerHTML = `
                <div class="dir-name">${dir.name}</div>
                <div class="dir-path">${dir.path}</div>
                <div class="dir-status ${dir.exists ? 'status-exists' : 'status-not-exists'}">
                    ${dir.exists ? '✅ Exists' : '❌ Not Found'}
                </div>
            `;

            if (dir.exists) {
                dirElement.addEventListener('click', () => {
                    this.selectDirectory(dir.path, dirElement);
                });
            }

            container.appendChild(dirElement);
        });
    }

    selectDirectory(path, element) {
        // Remove previous selection
        document.querySelectorAll('.dir-item').forEach(el => el.classList.remove('selected'));
        
        // Select current
        element.classList.add('selected');
        this.selectedDirectory = path;
        
        // Update custom path input
        document.getElementById('custom-path').value = path;
        
        this.showOutput(`Selected directory: ${path}`);
    }

    async browseDirectory(path) {
        try {
            this.showLoading();
            const data = await this.apiCall(`browse?path=${encodeURIComponent(path)}`);
            this.renderDirectoryBrowser(data);
            this.currentDirectory = data.current_path;
        } catch (error) {
            this.showOutput(`Failed to browse directory: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderDirectoryBrowser(data) {
        const section = document.getElementById('browser-section');
        const breadcrumb = document.getElementById('breadcrumb');
        const contents = document.getElementById('directory-contents');

        // Show browser section
        section.style.display = 'block';

        // Render breadcrumb
        breadcrumb.innerHTML = '';
        const pathParts = data.current_path.split('/').filter(part => part);
        let currentPath = '';

        // Root
        const rootSpan = document.createElement('span');
        rootSpan.className = 'breadcrumb-item';
        rootSpan.textContent = '/';
        rootSpan.addEventListener('click', () => this.browseDirectory('/'));
        breadcrumb.appendChild(rootSpan);

        // Path parts
        pathParts.forEach(part => {
            currentPath += '/' + part;
            const span = document.createElement('span');
            span.className = 'breadcrumb-item';
            span.textContent = part;
            const pathToNavigate = currentPath;
            span.addEventListener('click', () => this.browseDirectory(pathToNavigate));
            breadcrumb.appendChild(span);
        });

        // Render directory contents
        contents.innerHTML = '';

        // Parent directory link
        if (data.parent_path) {
            const parentItem = document.createElement('div');
            parentItem.className = 'file-item';
            parentItem.innerHTML = `
                <span class="file-icon">📁</span>
                <span class="file-name">..</span>
            `;
            parentItem.addEventListener('click', () => this.browseDirectory(data.parent_path));
            contents.appendChild(parentItem);
        }

        // Files and directories
        data.items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = `file-item ${item.is_executable ? 'file-executable' : ''}`;
            
            const icon = item.is_directory ? '📁' : (item.is_executable ? '⚡' : '📄');
            
            itemElement.innerHTML = `
                <span class="file-icon">${icon}</span>
                <span class="file-name">${item.name}</span>
            `;

            if (item.is_directory) {
                itemElement.addEventListener('click', () => this.browseDirectory(item.path));
            }

            contents.appendChild(itemElement);
        });

        // Update custom path
        document.getElementById('custom-path').value = data.current_path;
    }

    // Tool Scanning and Installation
    async scanDirectory(directory) {
        try {
            this.showLoading();
            this.showOutput(`Scanning directory: ${directory}`);
            
            const data = await this.apiCall(`scan?directory=${encodeURIComponent(directory)}`);
            this.foundTools = data.tools;
            this.renderFoundTools(data);
            
            this.showOutput(`Found ${data.tools.length} tools in ${directory}`, 'success');
        } catch (error) {
            this.showOutput(`Failed to scan directory: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderFoundTools(data) {
        const section = document.getElementById('tools-found');
        const directorySpan = document.getElementById('scanned-directory');
        const toolsList = document.getElementById('tools-list');

        // Show tools section
        section.style.display = 'block';
        directorySpan.textContent = data.directory;

        // Render tools
        toolsList.innerHTML = '';

        if (data.tools.length === 0) {
            toolsList.innerHTML = '<p>No tools found in this directory.</p>';
            return;
        }

        data.tools.forEach(tool => {
            const toolCard = document.createElement('div');
            toolCard.className = 'tool-card';
            
            toolCard.innerHTML = `
                <div class="tool-name">${tool.name}</div>
                <div class="tool-version">v${tool.version}</div>
                <div class="tool-category">${tool.category}</div>
                <div class="tool-description">${tool.description}</div>
                <div class="tool-actions">
                    <button class="btn btn-primary btn-small" onclick="vtm.installSingleTool('${data.directory}/${tool.name}')">
                        Install
                    </button>
                </div>
            `;

            toolsList.appendChild(toolCard);
        });
    }

    async installAllTools() {
        const directory = document.getElementById('scanned-directory').textContent;
        const force = document.getElementById('force-install').checked;

        if (!directory) {
            this.showOutput('No directory selected for installation', 'error');
            return;
        }

        try {
            this.showLoading();
            this.showOutput(`Installing all tools from ${directory}...`);
            
            const data = await this.apiCall('install', {
                method: 'POST',
                body: JSON.stringify({ directory, force })
            });

            if (data.success) {
                this.showOutput(data.output, 'success');
                this.loadInstalledTools(); // Refresh installed tools
            } else {
                this.showOutput(data.error || 'Installation failed', 'error');
            }
        } catch (error) {
            this.showOutput(`Installation failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async installSingleTool(filePath) {
        const force = document.getElementById('force-install').checked;

        try {
            this.showLoading();
            this.showOutput(`Installing tool: ${filePath}...`);
            
            const data = await this.apiCall('install-single', {
                method: 'POST',
                body: JSON.stringify({ file_path: filePath, force })
            });

            if (data.success) {
                this.showOutput(data.output, 'success');
                this.loadInstalledTools(); // Refresh installed tools
            } else {
                this.showOutput(data.error || 'Installation failed', 'error');
            }
        } catch (error) {
            this.showOutput(`Installation failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Installed Tools Management
    async loadInstalledTools() {
        try {
            const data = await this.apiCall('installed');
            this.renderInstalledTools(data.output);
        } catch (error) {
            this.showOutput('Failed to load installed tools', 'error');
        }
    }

    renderInstalledTools(output) {
        const container = document.getElementById('installed-tools');
        container.innerHTML = `<pre>${output}</pre>`;
    }

    async removeTool(toolName) {
        if (!confirm(`Are you sure you want to remove "${toolName}"?`)) {
            return;
        }

        try {
            this.showLoading();
            this.showOutput(`Removing tool: ${toolName}...`);
            
            const data = await this.apiCall('remove', {
                method: 'POST',
                body: JSON.stringify({ tool_name: toolName })
            });

            if (data.success) {
                this.showOutput(data.output, 'success');
                this.loadInstalledTools(); // Refresh installed tools
            } else {
                this.showOutput(data.error || 'Removal failed', 'error');
            }
        } catch (error) {
            this.showOutput(`Removal failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Health Check
    async runHealthCheck() {
        try {
            this.showLoading();
            this.showOutput('Running health check...');
            
            const data = await this.apiCall('health-check');
            
            const healthResults = document.getElementById('health-results');
            healthResults.textContent = data.output;
            
            if (data.success) {
                this.showOutput('Health check completed', 'success');
            } else {
                this.showOutput('Health check failed', 'error');
            }
        } catch (error) {
            this.showOutput(`Health check failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async setupToolManager() {
        try {
            this.showLoading();
            this.showOutput('Setting up tool manager...');
            
            const data = await this.apiCall('setup', { method: 'POST' });
            this.showOutput(data.message, 'success');
        } catch (error) {
            this.showOutput(`Setup failed: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
}

// Initialize the application
const vtm = new VisualToolManager();

// Global function for inline onclick handlers
window.vtm = vtm;