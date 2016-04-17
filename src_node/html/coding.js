var myCode = editor.getValue();
var socket = io();
var list = document.getElementById("sketchList");


loaded = false

editor.setReadOnly(true);

socket.on("connect",function(){
  page = window.location.pathname
  page = /\/(\w+)/.exec(page)[1]
  console.log(page)
  socket.emit("page", {name:page})
})

socket.on("page", function(message){
  loaded = true
  editor.setReadOnly(false)
  editor.setValue(message.code);
})

socket.on("sketches", function(sketches){
  // TODO: Stylize sketch list
  console.log(sketches)
  for (i = 0; i < sketches.length; i++) { 
    var node = document.createElement("LI");   
    var link = document.createElement("A");              // Create a <li> node
    var textnode = document.createTextNode(sketches[i]);         // Create a text node
    link.appendChild(textnode);                              // Append the text to <li>
    node.appendChild(link);
    document.getElementById("sketchList").appendChild(node);
    baseURL = "/";
    href = baseURL.concat(sketches[i]);
    link.href = href;
  }

})

setInterval(function(){
  if(loaded){
    socket.emit("save", {code:editor.getValue()})
  }
},1000)

window.onload = function() {
}


function runCode(){
  socket.emit("save_run",{code:editor.getValue()})
}

function newSketch(){
  console.log("you pressed add new sketch");

  newSketch = document.getElementById("newSketchName").value
  console.log(newSketch);
  var baseURL = "/";
  newURL = baseURL.concat(newSketch);
  console.log(newURL);
  document.getElementById("newSketchName").placeholder = newSketch;
  window.location.href = newURL;
}