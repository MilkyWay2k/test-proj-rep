// Function to apply styles
function applyStyles() {
    const bgColor = localStorage.getItem("bgColor") || "#f2f2f2"; // Default color if not set
  
    const font = localStorage.getItem("font") || "Arial, sans-serif"; // Default font if not set
    const boxColor = localStorage.getItem("boxColor") || "#e0e0e0"; // Default box color if not set

    document.body.style.backgroundColor = bgColor;
    
    document.body.style.fontFamily = font;

    // Apply the box color to all room boxes
    const roomBoxes = document.querySelectorAll('.room-box');
    roomBoxes.forEach(function(box) {
        box.style.backgroundColor = boxColor;
    });
}

// Apply styles when the page loads
window.addEventListener("load", applyStyles);

// Функция для открытия popup окна
function openPopup() {
    const popup = document.getElementById("popup");
    popup.style.display = "block";
    document.body.classList.add("popup-open"); // Добавить класс при открытии
}

// Функция для закрытия popup окна
function closePopup() {
    const popup = document.getElementById("popup");
    popup.style.display = "none";
    document.body.classList.remove("popup-open"); // Удалить класс при закрытии
}


