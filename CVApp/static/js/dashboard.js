document.addEventListener('DOMContentLoaded', () => {
  // Helper: Retrieve CSRF token
  function getCsrfToken() {
    const inputToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (inputToken) return inputToken;
    const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    return cookieMatch ? cookieMatch[1] : '';
  }

  // 1. Navigation View Toggle
  const navItems = document.querySelectorAll('.nav-item');
  const views = document.querySelectorAll('.view');

  navItems.forEach((nav) => {
    nav.addEventListener('click', () => {
      const targetView = nav.getAttribute('data-view');
      navItems.forEach((n) => n.classList.remove('active'));
      views.forEach((v) => v.classList.remove('active'));

      nav.classList.add('active');
      const activeElem = document.getElementById(`view-${targetView}`);
      if (activeElem) {
        activeElem.classList.add('active');
      }
    });
  });

  // 2. Global Search Filtering
  const searchInput = document.getElementById('globalSearch');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const rows = document.querySelectorAll('#candidatesTable tr, #overviewTable tr');
      rows.forEach((row) => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }

  // 3. Save Job Requirements via AJAX
  const saveJobBtn = document.getElementById('saveJobBtn');
  const jobForm = document.getElementById('jobForm');

  if (saveJobBtn && jobForm) {
    saveJobBtn.addEventListener('click', async () => {
      const formData = new FormData(jobForm);

      saveJobBtn.disabled = true;
      saveJobBtn.innerText = 'Saving...';

      try {
        const response = await fetch(jobForm.action, {
          method: 'POST',
          body: formData,
        });
        const result = await response.json();

        if (result.success) {
          window.location.reload();
        } else {
          alert('Could not save requirements. Please ensure all required fields are filled.');
          saveJobBtn.disabled = false;
          saveJobBtn.innerText = 'Save requirements';
        }
      } catch (err) {
        alert('Server error occurred while saving.');
        saveJobBtn.disabled = false;
        saveJobBtn.innerText = 'Save requirements';
      }
    });
  }

  // 4. Candidate Stage Updates (Only inside candidatesTable)
  const candidateButtons = document.querySelectorAll('#candidatesTable .btn-stage-interview, #candidatesTable .btn-stage-reject');
  candidateButtons.forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();

      const candidateId = btn.getAttribute('data-id');
      const targetStage = btn.getAttribute('data-stage');
      const csrfToken = getCsrfToken();

      btn.disabled = true;
      const originalText = btn.innerText;
      btn.innerText = '…';

      try {
        const formData = new FormData();
        formData.append('stage', targetStage);

        const response = await fetch(`/dashboard/candidate/${candidateId}/stage/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
          },
          body: formData,
        });

        if (!response.ok) {
          alert(`Server returned HTTP ${response.status} while updating candidate stage.`);
          btn.disabled = false;
          btn.innerText = originalText;
          return;
        }

        const data = await response.json();
        if (data.success) {
          window.location.reload();
        } else {
          alert('Could not update stage: ' + (data.error || 'Server error'));
          btn.disabled = false;
          btn.innerText = originalText;
        }
      } catch (err) {
        alert('Network error while updating candidate stage: ' + err.message);
        btn.disabled = false;
        btn.innerText = originalText;
      }
    });
  });

  // 5. User Approvals (Only inside approvals view)
  const userApproveBtns = document.querySelectorAll('.btn-user-approve');
  const userRejectBtns = document.querySelectorAll('.btn-user-reject');

  const handleUserDecision = async (btn, endpoint) => {
    const csrfToken = getCsrfToken();

    btn.disabled = true;
    const originalText = btn.innerText;
    btn.innerText = '…';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
        },
      });

      if (!response.ok) {
        alert(`Server error (${response.status}): Endpoint ${endpoint} failed.`);
        btn.disabled = false;
        btn.innerText = originalText;
        return;
      }

      const data = await response.json();
      if (data.success) {
        window.location.reload();
      } else {
        alert('Action failed: ' + (data.error || data.message || 'Server error'));
        btn.disabled = false;
        btn.innerText = originalText;
      }
    } catch (err) {
      alert('Network error while processing approval: ' + err.message);
      btn.disabled = false;
      btn.innerText = originalText;
    }
  };

  userApproveBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const userId = btn.getAttribute('data-user-id');
      handleUserDecision(btn, `/dashboard/user/${userId}/approve/`);
    });
  });

  userRejectBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Are you sure you want to reject and delete this registration?')) {
        const userId = btn.getAttribute('data-user-id');
        handleUserDecision(btn, `/dashboard/user/${userId}/reject/`);
      }
    });
  });
});