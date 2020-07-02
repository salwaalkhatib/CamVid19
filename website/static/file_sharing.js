
window.addEventListener("load", function() {
    document.getElementById("file-upload").onchange = function(event) {
      var reader = new FileReader();
      reader.readAsDataURL(event.srcElement.files[0]);
      var me = this;
      reader.onload = function () {
        var fileContent = reader.result;
        document.getElementById('data').value = fileContent;
        filename = document.getElementById('file-upload').value;
        var n = filename.lastIndexOf('\\');
        var result = filename.substring(n + 1);
        document.getElementById('filename').value = result; 
        document.getElementById('data').value = fileContent; 
        console.log(fileContent);
      }
  }});