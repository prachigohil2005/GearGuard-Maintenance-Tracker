// Kanban Board - Drag & Drop Functionality

let draggedCard = null

document.addEventListener("DOMContentLoaded", () => {
  initKanban()
})

function initKanban() {
  const cards = document.querySelectorAll(".kanban-card")
  const columns = document.querySelectorAll(".kanban-column")

  // Setup drag events for cards
  cards.forEach((card) => {
    card.addEventListener("dragstart", handleDragStart)
    card.addEventListener("dragend", handleDragEnd)

    // Prevent navigation on drag
    card.addEventListener("click", function (e) {
      if (e.target === this || e.target.closest(".kanban-card")) {
        // Allow click-through for navigation
      }
    })
  })

  // Setup drop zones
  columns.forEach((column) => {
    const cardsContainer = column.querySelector(".kanban-cards")

    cardsContainer.addEventListener("dragover", handleDragOver)
    cardsContainer.addEventListener("drop", handleDrop)
    cardsContainer.addEventListener("dragleave", handleDragLeave)
  })
}

function handleDragStart(e) {
  draggedCard = this
  this.classList.add("dragging")
  e.dataTransfer.effectAllowed = "move"
  e.dataTransfer.setData("text/html", this.innerHTML)

  // Stop propagation to prevent click event
  e.stopPropagation()
}

function handleDragEnd(e) {
  this.classList.remove("dragging")
}

function handleDragOver(e) {
  if (e.preventDefault) {
    e.preventDefault()
  }

  e.dataTransfer.dropEffect = "move"
  this.classList.add("drag-over")
  return false
}

function handleDragLeave(e) {
  this.classList.remove("drag-over")
}

function handleDrop(e) {
  if (e.stopPropagation) {
    e.stopPropagation()
  }

  this.classList.remove("drag-over")

  const column = this.closest(".kanban-column")
  const newStatus = column.dataset.status
  const cardId = draggedCard.dataset.id

  // Update card status via AJAX
  updateCardStatus(cardId, newStatus).then((success) => {
    if (success) {
      // Move card to new column
      this.appendChild(draggedCard)

      // Update count badges
      updateColumnCounts()

      // Show success message
      showToast("Status updated successfully!", "success")
    } else {
      showToast("Failed to update status", "danger")
    }
  })

  return false
}

async function updateCardStatus(cardId, newStatus) {
  try {
    const response = await fetch(`/requests/api/update-status/${cardId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: newStatus }),
    })

    const data = await response.json()
    return data.success
  } catch (error) {
    console.error("Error updating status:", error)
    return false
  }
}

function updateColumnCounts() {
  document.querySelectorAll(".kanban-column").forEach((column) => {
    const count = column.querySelectorAll(".kanban-card").length
    const badge = column.querySelector(".kanban-count")
    if (badge) {
      badge.textContent = count
    }
  })
}

function showToast(message, type) {
  const toast = document.createElement("div")
  toast.className = `alert alert-${type}`
  toast.textContent = message
  toast.style.position = "fixed"
  toast.style.top = "2rem"
  toast.style.right = "2rem"
  toast.style.zIndex = "9999"

  document.body.appendChild(toast)

  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease"
    setTimeout(() => toast.remove(), 300)
  }, 3000)
}
