document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const btn = document.getElementById('loginBtn');

  if (form && btn) {
    form.addEventListener('submit', () => {
      const isSignup = btn.textContent.toLowerCase().includes('sign up');
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span> ${isSignup ? 'Creating account...' : 'Signing in...'}`;
    });
  }
});