document.addEventListener('DOMContentLoaded', () => {
  // Auto-hide flash messages after 4s
  const flashes = document.querySelectorAll('.flash');
  setTimeout(() => flashes.forEach(f => f.remove()), 4000);
});
