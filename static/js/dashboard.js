// Dashboard functionality
function changeMood(mood) {
    // Send mood change to server
    fetch('/api/change-mood/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ mood: mood })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload page to show new mood
                window.location.reload();
            }
        });
}

function syncData() {
    const btn = document.getElementById('sync-btn');
    const text = document.getElementById('sync-text');

    // Disable button and show loading
    btn.disabled = true;
    text.innerHTML = '🔄 Syncing...';
    text.classList.add('spin');

    // Send sync request
    fetch('/api/sync/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
        .then(response => response.json())
        .then(data => {
            setTimeout(() => {
                text.classList.remove('spin');
                btn.disabled = false;
                text.innerHTML = '🔄 Sync My Life';

                // Reload page to show updated data
                window.location.reload();
            }, 2000);
        });
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
