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
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to update mood');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Reload page to show new mood
                window.location.reload();
            } else {
                alert('Failed to update mood. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error changing mood:', error);
            alert('Network error. Please check your connection and try again.');
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
        .then(response => {
            if (!response.ok) {
                throw new Error('Sync request failed');
            }
            return response.json();
        })
        .then(data => {
            setTimeout(() => {
                text.classList.remove('spin');
                btn.disabled = false;

                if (data.success) {
                    text.innerHTML = '✅ Synced!';
                    // Reload page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    text.innerHTML = '❌ Sync Failed';
                    alert(data.message || 'Failed to sync data. Please check your Google permissions.');
                    setTimeout(() => {
                        text.innerHTML = '🔄 Sync My Life';
                    }, 2000);
                }
            }, 1000);
        })
        .catch(error => {
            console.error('Error syncing data:', error);
            text.classList.remove('spin');
            btn.disabled = false;
            text.innerHTML = '❌ Network Error';
            alert('Network error. Please check your connection and try again.');
            setTimeout(() => {
                text.innerHTML = '🔄 Sync My Life';
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
