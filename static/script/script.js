let dropArea = document.getElementById('drop-area');
let fileInput = document.getElementById('fileElem');
let fileName = document.getElementById('file-name');
let preview = document.getElementById('preview');

// Click anywhere on box
dropArea.addEventListener('click', () => {
    fileInput.click();
});

// Drag over
dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('dragover');
});

// Drag leave
dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('dragover');
});

// Drop
dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('dragover');

    let files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        showPreview(files[0]);
    }
});

// Manual selection
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        showPreview(fileInput.files[0]);
    }
});

function showPreview(file) {
    fileName.innerText = file.name;

    let reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
}