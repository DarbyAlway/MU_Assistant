// Ensure we select all necessary elements
const enterToggle = document.getElementById('enterToggle');
const queryInput = document.getElementById('queryInput');
const compareBtn = document.getElementById('compareBtn');
const historyList = document.getElementById('historyList');

let searchHistory = JSON.parse(sessionStorage.getItem('searchHistory')) || [];

const formatText = (text) => {
    if (!text) return "";
    return text.replace(/\n/g, "<br>");
};

const createSourceList = (urls) => {
    if (!urls || urls.length === 0) return "";
    const linksHtml = urls
        .map(url => `<li><a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a></li>`)
        .join("");
    return `<div class="source-section"><hr><strong>References:</strong><ul class="source-list">${linksHtml}</ul></div>`;
};

function updateHistoryUI() {
    if (!historyList) return;
    historyList.innerHTML = ""; 

    searchHistory.forEach((item, index) => {
        const li = document.createElement('li');
        li.className = "history-item";
        // Show query and time
        li.innerHTML = `<strong>${item.query}</strong> <small>${item.timestamp}</small>`;
        li.onclick = () => displayHistoryItem(index);
        historyList.appendChild(li);
    });
}

function displayHistoryItem(index) {
    const data = searchHistory[index];
    document.getElementById('sarResult').innerHTML = data.sar;
    document.getElementById('ragResult').innerHTML = data.rag;
    // Update the input field to show what the query was
    queryInput.value = data.query;
}

// ... (Existing variables and formatText/createSourceList functions) ...

async function runSearch() {
    const query = queryInput.value.trim();
    if (!query) return;

    const sarResult = document.getElementById('sarResult');
    const ragResult = document.getElementById('ragResult');

    sarResult.innerHTML = "<em>Thinking (SAR)...</em>";
    ragResult.innerHTML = "<em>Thinking (RAG)...</em>";

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

        if (data.status === "success") {
            const sarContent = formatText(data.answer_SAR) + createSourceList(data.sources_SAR || []);
            const ragContent = formatText(data.answer_RAG) + createSourceList(data.sources_RAG || []);

            sarResult.innerHTML = sarContent;
            ragResult.innerHTML = ragContent;

            // Save to sessionStorage
            const historyEntry = {
                query: query,
                sar: sarContent,
                rag: ragContent,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            
            let searchHistory = JSON.parse(sessionStorage.getItem('searchHistory')) || [];
            searchHistory.unshift(historyEntry);
            if (searchHistory.length > 20) searchHistory.pop(); // Increased limit
            
            sessionStorage.setItem('searchHistory', JSON.stringify(searchHistory));
        }
    } catch (error) {
        console.error(error);
        sarResult.innerHTML = "Connection failed.";
    }
}

// Logic to load specific history item if redirected from history page
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const historyIndex = urlParams.get('load');
    
    if (historyIndex !== null) {
        const history = JSON.parse(sessionStorage.getItem('searchHistory'));
        if (history && history[historyIndex]) {
            const data = history[historyIndex];
            document.getElementById('sarResult').innerHTML = data.sar;
            document.getElementById('ragResult').innerHTML = data.rag;
            queryInput.value = data.query;
        }
    }
});

// Function to fetch history from the Backend
async function syncHistoryWithServer() {
    try {
        const response = await fetch('/history');
        const data = await response.json();
        
        if (data.status === "success") {
            // Map backend data to the format your frontend expects
            searchHistory = data.history.map(item => ({
                query: item.query,
                sar: formatText(item.answer_SAR) + createSourceList(item.sources_SAR),
                rag: formatText(item.answer_RAG) + createSourceList(item.sources_RAG),
                timestamp: item.timestamp
            })).reverse(); // Reverse so newest is at the top
            
            // Sync it back to sessionStorage for offline/speed
            sessionStorage.setItem('searchHistory', JSON.stringify(searchHistory));
            
            renderHistoryList();
        }
    } catch (error) {
        console.error("Failed to sync history:", error);
        // Fallback to session storage if server is unreachable
        renderHistoryList();
    }
}

// Separate the rendering logic
function renderHistoryList() {
    if (!historyList) return;
    historyList.innerHTML = ""; 

    searchHistory.forEach((item, index) => {
        const li = document.createElement('li');
        li.className = "history-item";
        li.innerHTML = `
            <div class="history-content">
                <strong>${item.query}</strong>
                <span class="history-time">${item.timestamp}</span>
            </div>
        `;
        li.onclick = () => displayHistoryItem(index);
        historyList.appendChild(li);
    });
}
window.addEventListener('load', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const historyIndex = urlParams.get('load');
    
    if (historyIndex !== null) {
        const response = await fetch('/history');
        const data = await response.json();
        
        if (data.history && data.history[historyIndex]) {
            const item = data.history[historyIndex];
            document.getElementById('sarResult').innerHTML = formatText(item.answer_SAR) + createSourceList(item.sources_SAR);
            document.getElementById('ragResult').innerHTML = formatText(item.answer_RAG) + createSourceList(item.sources_RAG);
            document.getElementById('queryInput').value = item.query;
        }
    }
});

compareBtn.addEventListener('click', runSearch);

enterToggle.addEventListener('change', () => {
    // This puts the cursor back in the box so you can type/press Enter immediately
    queryInput.focus(); 
});
queryInput.addEventListener('keydown', (e) => {
    if (e.key === "Enter") {
        if (enterToggle && enterToggle.checked) {
            e.preventDefault(); // Stops the page from refreshing
            runSearch();
        }
    }
});
// Initialize UI on load
updateHistoryUI();