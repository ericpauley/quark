var myCode = editor.getValue();
var socket = io();

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
