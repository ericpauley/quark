var myCode = editor.getValue();
var socket = io();

socket.on("connect",function(){
  page = window.location.pathname
  page = /\/(\w+)/.exec(page)[1]
  console.log(page)
  socket.emit("page", {name:page})
})

socket.on("page", function(message){
  console.log(message)
  editor.setValue(message.code);
})

window.onload = function() {
}


function runCode(){
	var myCode = editor.getValue();
	console.log(myCode);
}
