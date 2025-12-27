// GearGuard - Main JavaScript

// Auto-hide flash messages after 5 seconds
document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".alert")
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.animation = "slideOut 0.3s ease"
      setTimeout(() => alert.remove(), 300)
    }, 5000)
  })
})

// Add slideOut animation
const style = document.createElement("style")
style.textContent = `
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`
document.head.appendChild(style)

// Confirm before delete
document.querySelectorAll("[data-confirm]").forEach((element) => {
  element.addEventListener("click", function (e) {
    if (!confirm(this.dataset.confirm)) {
      e.preventDefault()
    }
  })
})

// Form validation helper
function validateForm(formId) {
  const form = document.getElementById(formId)
  if (!form) return true

  const requiredFields = form.querySelectorAll("[required]")
  let isValid = true

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      field.style.borderColor = "#dc3545"
      isValid = false
    } else {
      field.style.borderColor = "#dee2e6"
    }
  })

  return isValid
}

// Equipment selector - show team info
const equipmentSelector = document.getElementById("equipment_id")
if (equipmentSelector) {
  equipmentSelector.addEventListener("change", function () {
    // You can add AJAX call here to fetch and display team info
    console.log("Equipment selected:", this.value)
  })
}

// Dynamic form helpers
document.querySelectorAll("input[required], textarea[required], select[required]").forEach((field) => {
  field.addEventListener("invalid", function () {
    this.style.borderColor = "#dc3545"
  })

  field.addEventListener("input", function () {
    if (this.value.trim()) {
      this.style.borderColor = "#dee2e6"
    }
  })
})
