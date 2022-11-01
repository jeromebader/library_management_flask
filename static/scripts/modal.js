// Get the modal
var modal = document.getElementById("contact-modal");

// Get the button that opens the modal
var btn = document.getElementById("contact");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

var submit = document.getElementById("submit_modal");

// When the user clicks on the button, open the modal
btn.onclick = function() {
  modal.style.display = "block";
}

submit.onclick= function()
{
 modal.title("Hello! I am an alert box!!");
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}