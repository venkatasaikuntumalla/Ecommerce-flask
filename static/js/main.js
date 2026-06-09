// Auto-dismiss flash messages after 4 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 4000);
  });

  // Quantity input validation
  document.querySelectorAll('input[type="number"]').forEach(function (input) {
    input.addEventListener('change', function () {
      const min = parseInt(this.min) || 0;
      const max = parseInt(this.max) || Infinity;
      if (parseInt(this.value) < min) this.value = min;
      if (parseInt(this.value) > max) this.value = max;
    });
  });
});
