document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = 640;
    canvas.height = 480;

    // Access webcam
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => { 
                if (video) {
                    video.srcObject = stream;
                }
            })
            .catch(error => {
                console.error('Error accessing webcam:', error);
                alert('Could not access webcam. Please ensure you have granted camera permissions.');
            });
    } else {
        alert('Your browser does not support webcam access.');
    }
});

function captureAndSend() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    
    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob and send to server
    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');
        
        fetch('/attendance', { 
            method: 'POST', 
            body: formData 
        })
        .then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => {
            console.error('Error:', error);
            alert('Error sending image to server');
        });
    }, 'image/jpeg', 0.8);
}