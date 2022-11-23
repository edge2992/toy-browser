
label = document.querySelectorAll("label")[0];

console.log(label);

function lengthCheck() {
  var value = this.getAttribute("value");
  if (value.length > 10) {
    label.innerHTML = "Input is too long";
  }
}

input = document.querySelectorAll("input")[0];
input.addEventListener("keydown", lengthCheck);
