const imageInput = document.getElementById('image-input');
const previewWrap = document.getElementById('preview-wrap');
const previewImg = document.getElementById('preview-img');
const uploadHint = document.getElementById('upload-hint');
const form = document.getElementById('diagnose-form');
const loading = document.getElementById('loading');
const submitBtn = document.getElementById('submit-btn');

imageInput.addEventListener('change', () => {
  const file = imageInput.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewWrap.style.display = 'block';
      uploadHint.querySelector('strong').textContent = file.name;
    };
    reader.readAsDataURL(file);
  }
});

form.addEventListener('submit', () => {
  loading.style.display = 'block';
  submitBtn.disabled = true;
  submitBtn.textContent = 'Analyzing...';
});