label = document.querySelectorAll("label")[0];
allow_submit = true;

function lengthCheck() {
  allow_submit = input.getAttribute("value").length <= 10;
  if (!allow_submit) {
    label.innerHTML = "Input is too long";
  }
}

input = document.querySelectorAll("input")[0];
input.addEventListener("keydown", lengthCheck);

form = document.querySelectorAll("form")[0];
form.addEventListener("submit", function (evt) {
  if (!allow_submit) {
    evt.preventDefault();
    console.log("Prevented submit");
  }
});