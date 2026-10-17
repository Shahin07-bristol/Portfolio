document.addEventListener("DOMContentLoaded", function () {
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightbox-img");
  const lightboxDownload = document.getElementById("lightbox-download");
  const closeBtn = document.querySelector(".lightbox-close");

  // Open Lightbox on Click
  document.querySelectorAll(".lightbox-trigger").forEach((img) => {
    img.addEventListener("click", function () {
      lightbox.style.display = "flex";
      lightboxImg.src = this.src;
      lightboxDownload.href = this.src;
    });
  });

  // Close Lightbox on 'X' click
  closeBtn.addEventListener("click", function () {
    lightbox.style.display = "none";
  });

  // Close Lightbox when clicking anywhere on the background outside the image
  lightbox.addEventListener("click", function (e) {
    if (e.target === lightbox) {
      lightbox.style.display = "none";
    }
  });

  // Close Lightbox on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && lightbox.style.display === "flex") {
      lightbox.style.display = "none";
    }
  });
});