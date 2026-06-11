class IngestorsPage {
    constructor() {
        this.runButton = document.getElementById('btn-run-ingestor');
        this.status = document.getElementById('ingestor-status');
        this.log = document.getElementById('ingestor-log');
        if (this.runButton) {
            this.runButton.addEventListener('click', () => this.run());
        }
        this.refresh();
    }

    async run() {
        if (this.runButton) this.runButton.disabled = true;
        try {
            const response = await fetch('/manage/ingestors/run', { method: 'POST' });
            const data = await response.json();
            if (!response.ok || data.success === false) {
                throw new Error(data?.message?.text || data?.error || `HTTP ${response.status}`);
            }
            this.render(data.data || {});
            this.poll();
        } catch (error) {
            this.setStatus(`Error: ${error.message}`);
            if (this.runButton) this.runButton.disabled = false;
        }
    }

    async refresh() {
        try {
            const response = await fetch('/manage/ingestors/status');
            if (!response.ok) return;
            const data = await response.json();
            this.render(data.data || {});
            if (data.data?.running) this.poll();
        } catch (_) {}
    }

    poll() {
        window.setTimeout(() => this.refresh(), 2000);
    }

    render(payload) {
        const running = Boolean(payload.running);
        if (this.runButton) this.runButton.disabled = running;
        if (running) {
            this.setStatus(`Running since ${payload.started_at || 'now'}`);
        } else if (payload.return_code === 0) {
            this.setStatus('Finished successfully.');
        } else if (payload.return_code !== null && payload.return_code !== undefined) {
            this.setStatus(`Finished with return code ${payload.return_code}.`);
        } else {
            this.setStatus('Idle');
        }
        if (this.log) {
            this.log.textContent = payload.log || '';
        }
    }

    setStatus(text) {
        if (this.status) this.status.textContent = text;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.ingestorsPage = new IngestorsPage();
});
