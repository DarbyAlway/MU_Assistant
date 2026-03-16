document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('historyListContainer');

    try {
        // Fetch from the API endpoint, NOT the page endpoint
        const response = await fetch('/api/history');
        const data = await response.json();

        if (data.status === "success" && data.history.length > 0) {
            container.innerHTML = ""; // Clear the "Loading" text

            data.history.slice().reverse().forEach((item, index) => {

                const sessionCard = document.createElement('div');
                sessionCard.className = "session-card";

                sessionCard.innerHTML = `
        <div class="session-header">
            <strong>Query:</strong> ${item.query}
        </div>

        <div class="session-results">

            <div class="result-card rag">
                <h4>RAG Result</h4>
                <p>${item.answer_RAG}</p>
            </div>

            <div class="result-card sar">
                <h4>SAR Result</h4>
                <p>${item.answer_SAR}</p>
            </div>

        </div>
    `;

                container.appendChild(sessionCard);
            });
        } else {
            container.innerHTML = "<p>No history found yet. Try searching for something!</p>";
        }
    } catch (error) {
        container.innerHTML = "<p>Error loading history. Make sure the server is running.</p>";
    }
});