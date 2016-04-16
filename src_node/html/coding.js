var myCode = editor.getValue();


window.onload = function() {
       //when the document is finished loading, replace everything
       //between the <a ...> </a> tags with the value of splitText
   editor.setValue(myCode);
}


function runCode(){
	var myCode = editor.getValue();
	console.log(myCode);
}