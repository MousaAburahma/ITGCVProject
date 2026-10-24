document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const fileChipHolder = document.getElementById('fileChipHolder');
  const submitBtn = document.getElementById('submitBtn');
  const fullname = document.getElementById('fullname');
  const email = document.getElementById('email');
  const form = document.getElementById('cvForm');
  const errorBanner = document.getElementById('error-banner');
  const errorText = document.getElementById('error-text');
  const resetBtn = document.getElementById('resetBtn');

  function checkFormValidity() {
    const hasDetails = fullname.value.trim() !== '' && email.value.trim() !== '';
    const hasFile = fileInput.files && fileInput.files.length > 0;
    submitBtn.disabled = !(hasDetails && hasFile);
  }

  fullname.addEventListener('input', checkFormValidity);
  email.addEventListener('input', checkFormValidity);

  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag');
  });

  ['dragleave', 'dragend'].forEach((type) => {
    dropzone.addEventListener(type, () => dropzone.classList.remove('drag'));
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag');
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      renderFile(fileInput.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      renderFile(fileInput.files[0]);
    }
  });

  function renderFile(file) {
    fileChipHolder.innerHTML = `
      <div class="file-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span class="file-chip-name">${file.name}</span>
        <span class="file-chip-size">(${(file.size / (1024 * 1024)).toFixed(2)} MB)</span>
        <button type="button" class="file-chip-remove" id="removeFileBtn">&times;</button>
      </div>
    `;

    document.getElementById('removeFileBtn').addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.value = '';
      fileChipHolder.innerHTML = '';
      checkFormValidity();
    });

    checkFormValidity();
  }

  // AJAX Submission
  submitBtn.addEventListener('click', async () => {
    errorBanner.classList.add('hidden');
    const formData = new FormData(form);

    if (!fileInput.files.length) {
      errorText.innerHTML = '<strong>File required.</strong> Please select a CV to upload.';
      errorBanner.classList.remove('hidden');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Submitting...';

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();

      if (result.success) {
        document.getElementById('view-form').classList.add('hidden');
        document.getElementById('confirmRef').innerText = result.ref;
        document.getElementById('view-confirm').classList.remove('hidden');
        document.querySelectorAll('.rail-step, .rail-line').forEach((s) => s.classList.add('done'));
      } else {
        let msg = '';
        for (let [key, err] of Object.entries(result.errors)) {
          msg += `${err.join(' ')} `;
        }
        errorText.innerHTML = `<strong>Error:</strong> ${msg}`;
        errorBanner.classList.remove('hidden');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit CV';
      }
    } catch (err) {
      errorText.innerHTML = '<strong>Connection error.</strong> Please try again later.';
      errorBanner.classList.remove('hidden');
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Submit CV';
    }
  });

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      window.location.reload();
    });
  }
});